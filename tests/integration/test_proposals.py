"""Offline fixture proposals through actual ngspice; not an LLM ablation."""
import json

import pytest

from circuforge.domain.specs import DesignSpec
from circuforge.optimization.base import Evaluator
from circuforge.proposals import ProposalSession, ProviderReply, TokenUsage
from circuforge.simulation.ngspice import Ngspice, SimulationError, executable_path


@pytest.mark.integration
@pytest.mark.parametrize("topology", ["rc_lowpass", "rc_highpass"])
def test_offline_proposal_validation_precedes_real_measurement(topology, tmp_path):
    try:
        executable_path()
    except SimulationError as exc:
        pytest.skip(str(exc))

    class OfflineFixture:
        def propose(self, request):
            number = request.request_number
            candidate = dict(topology="unsupported" if number == 1 else topology,
                             resistance_ohm=2000.0 if number == 4 else 1000.0,
                             capacitance_f=1e-7)
            return ProviderReply(json.dumps(candidate), TokenUsage(input_tokens=2, output_tokens=3))

    spec = DesignSpec(filter_type=topology, max_evaluations=2)
    session = ProposalSession(spec, OfflineFixture())
    evaluator = Evaluator(spec, Ngspice(), tmp_path / "raw")
    invalid = session.propose()
    assert invalid.status == "invalid_candidate" and invalid.candidate is None and evaluator.calls == 0
    first = evaluator.evaluate(session.propose().candidate)
    duplicate = evaluator.evaluate(session.propose().candidate)
    missed = evaluator.evaluate(session.propose().candidate)
    assert first.verified and first.target_passed and duplicate is first
    assert missed.verified and not missed.target_passed
    assert evaluator.calls == 2 and evaluator.cache_hits == 1
    assert session.usage.requests == 4 and session.usage.cost_microusd == 0
    for index in (1, 2):
        assert (tmp_path / "raw" / f"call-{index:04d}" / "response.csv").is_file()
