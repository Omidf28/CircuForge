"""Offline fixture tests, not LLM traffic, tokenization or billing measurements."""
import json

import pytest
from pydantic import ValidationError

from circuforge.domain.specs import CircuitCandidate, DesignSpec
from circuforge.proposals import (MAX_CANDIDATE_BYTES, ProposalBlocked, ProposalLimits,
                                 ProposalSession, ProviderReply, TokenPrices,
                                 TokenReservation, TokenUsage)


def payload(**changes):
    return json.dumps({**CircuitCandidate().model_dump(), **changes})


def reply(candidate=None, **usage):
    return ProviderReply(payload() if candidate is None else candidate,
                         TokenUsage(input_tokens=usage.get("input_tokens", 2),
                                    output_tokens=usage.get("output_tokens", 3)))


class FixtureProvider:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.requests = []

    def propose(self, request):
        self.requests.append(request)
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


def test_explicit_candidate_and_context_are_typed_and_immutable():
    provider = FixtureProvider(reply())
    session = ProposalSession(DesignSpec(), provider, seed=73)
    result = session.propose()
    assert result.status == "accepted" and result.candidate == CircuitCandidate()
    assert result.accounting == "reported" and result.cost_microusd == 0
    request = provider.requests[0]
    assert request.seed == 73 and request.request_number == 1 and request.spec == DesignSpec()
    with pytest.raises(ValidationError):
        request.spec.cutoff_hz = 42.0
    assert session.history == (result,) and session.usage.requests == 1
    assert session.usage.input_tokens + session.usage.output_tokens == 5


@pytest.mark.parametrize("text", [
    "{}", "[]", "null", "not JSON", "```json\n{}\n```", b"\xff",
    '{"topology":"rc_lowpass","resistance_ohm":1000,"resistance_ohm":2000,"capacitance_f":1e-7}',
    '{"topology":"rc_lowpass","resistance_ohm":NaN,"capacitance_f":1e-7}',
    payload(topology="opamp"), payload(topology="rc_highpass"),
    payload(resistance_ohm=1.0), payload(capacitance_f=1.0),
    payload(resistance_ohm=True), payload(capacitance_f="1e-7"),
    payload(netlist=".control\nshell arbitrary\n.endc"), payload(output_path="C:/untrusted"),
    " " * (MAX_CANDIDATE_BYTES + 1), payload(extra="é" * MAX_CANDIDATE_BYTES),
])
def test_untrusted_candidates_are_rejected_and_usage_still_counted(text):
    provider = FixtureProvider(reply(text))
    session = ProposalSession(DesignSpec(), provider)
    result = session.propose()
    assert result.status == "invalid_candidate" and result.candidate is None
    assert result.accounting == "reported"
    assert session.usage.input_tokens + session.usage.output_tokens == 5
    assert len(provider.requests) == 1
    assert "untrusted" not in result.model_dump_json()


@pytest.mark.parametrize("limits,prices,message", [
    (ProposalLimits(max_total_tokens=9), TokenPrices(), "token"),
    (ProposalLimits(max_cost_microusd=0), TokenPrices(input_microusd=1), "cost"),
])
def test_pre_call_reservations_block_without_invocation(limits, prices, message):
    provider = FixtureProvider(reply())
    session = ProposalSession(DesignSpec(), provider, limits=limits, prices=prices)
    with pytest.raises(ProposalBlocked, match=message):
        session.propose(TokenReservation(input_tokens=5, output_tokens=5))
    assert provider.requests == [] and session.history == () and session.usage.requests == 0


def test_exact_token_cost_and_request_caps_allow_boundary_then_block():
    provider = FixtureProvider(reply(input_tokens=5, output_tokens=5), reply())
    session = ProposalSession(DesignSpec(), provider,
                              limits=ProposalLimits(max_requests=1, max_total_tokens=10, max_cost_microusd=25),
                              prices=TokenPrices(input_microusd=2, output_microusd=3))
    assert session.propose(TokenReservation(input_tokens=5, output_tokens=5)).status == "accepted"
    assert session.usage.cost_microusd == 25
    with pytest.raises(ProposalBlocked, match="request"):
        session.propose(TokenReservation(input_tokens=1, output_tokens=1))
    assert len(provider.requests) == 1


def test_valid_usage_refunds_only_unused_reservations():
    provider = FixtureProvider(reply(), reply())
    session = ProposalSession(DesignSpec(), provider, limits=ProposalLimits(max_total_tokens=15))
    reservation = TokenReservation(input_tokens=5, output_tokens=5)
    session.propose(reservation)
    session.propose(reservation)
    assert session.usage.input_tokens + session.usage.output_tokens == 10
    with pytest.raises(ProposalBlocked, match="token"):
        session.propose(reservation)
    assert len(provider.requests) == 2


@pytest.mark.parametrize("response,status", [
    (RuntimeError("sensitive adapter failure"), "provider_error"),
    (None, "invalid_response"),
    (ProviderReply(payload(), TokenUsage.model_construct(input_tokens=-1, output_tokens=0)), "invalid_response"),
])
def test_unknown_or_bad_usage_conservatively_keeps_full_reservation(response, status):
    session = ProposalSession(DesignSpec(), FixtureProvider(response),
                              limits=ProposalLimits(max_total_tokens=10, max_cost_microusd=25),
                              prices=TokenPrices(input_microusd=2, output_microusd=3))
    result = session.propose(TokenReservation(input_tokens=5, output_tokens=5))
    assert result.status == status and result.accounting == "reserved"
    assert session.usage.input_tokens + session.usage.output_tokens == 10
    assert session.usage.cost_microusd == 25
    assert "sensitive" not in result.model_dump_json()
    with pytest.raises(ProposalBlocked):
        session.propose(TokenReservation(input_tokens=1, output_tokens=1))


def test_usage_overrun_records_excess_and_blocks_even_when_budget_remains():
    provider = FixtureProvider(reply(input_tokens=11, output_tokens=2), reply())
    session = ProposalSession(DesignSpec(), provider)
    result = session.propose(TokenReservation(input_tokens=10, output_tokens=5))
    assert result.status == "usage_overrun" and result.candidate is None
    assert session.usage.input_tokens == 11 and session.usage.blocked
    with pytest.raises(ProposalBlocked, match="overrun"):
        session.propose()
    assert len(provider.requests) == 1


def test_rate_boundary_has_no_sleep_or_automatic_retry():
    times = iter((10.0, 10.5, 11.0))
    provider = FixtureProvider(reply(), reply())
    session = ProposalSession(DesignSpec(), provider, limits=ProposalLimits(min_interval_s=1.0),
                              clock=lambda: next(times))
    session.propose()
    with pytest.raises(ProposalBlocked, match="rate"):
        session.propose()
    assert session.usage.requests == 1
    assert session.propose().request_number == 2 and len(provider.requests) == 2


def test_reentrant_provider_cannot_escape_request_accounting():
    class Reentrant:
        def propose(self, request):
            with pytest.raises(ProposalBlocked, match="active"):
                session.propose()
            assert session.history[0].status == "pending" and session.usage.requests == 1
            return reply()

    session = ProposalSession(DesignSpec(), Reentrant())
    assert session.propose().status == "accepted" and session.usage.requests == 1


def test_interruption_is_charged_and_re_raised():
    session = ProposalSession(DesignSpec(), FixtureProvider(KeyboardInterrupt()))
    with pytest.raises(KeyboardInterrupt):
        session.propose()
    assert session.history[0].status == "provider_error"
    assert session.history[0].accounting == "reserved" and session.usage.requests == 1


@pytest.mark.parametrize("kwargs", [{"seed": True}, {"seed": -1}, {"seed": 2**32},
                                    {"limits": ProposalLimits.model_construct(max_requests=0)}])
def test_invalid_configuration_is_rejected_before_provider(kwargs):
    provider = FixtureProvider(reply())
    with pytest.raises(ValidationError):
        ProposalSession(DesignSpec(), provider, **kwargs)
    assert provider.requests == []


def test_unsupported_unsafe_constructed_spec_is_revalidated():
    provider = FixtureProvider(reply())
    with pytest.raises(ValidationError):
        ProposalSession(DesignSpec().model_copy(update={"filter_type": "unrestricted"}), provider)
    assert provider.requests == []
