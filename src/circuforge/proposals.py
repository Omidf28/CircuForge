"""Offline proposal contract and conservative accounting, isolated from simulation.

Providers are trusted, synchronous Python adapters, not a network or code sandbox.
This module includes no provider SDK, credentials, network transport or agent loop.
Token reports and integer micro-USD prices are supplied by the trusted adapter;
the ledger is accounting evidence, not independent billing verification.
"""
from dataclasses import dataclass
import json
import math
from threading import Lock
import time
from typing import Annotated, Callable, Literal, Protocol

from pydantic import Field, ValidationError

from circuforge.domain.specs import CircuitCandidate, DesignSpec, Model

MAX_CANDIDATE_BYTES = 4096
Count = Annotated[int, Field(strict=True, ge=0, le=2**31 - 1)]
Money = Annotated[int, Field(strict=True, ge=0, le=10**12)]


class ProposalLimits(Model):
    max_requests: Annotated[int, Field(strict=True, ge=1, le=128)] = 16
    max_total_tokens: Annotated[int, Field(strict=True, ge=1, le=1_000_000)] = 65536
    max_cost_microusd: Money = 0
    min_interval_s: Annotated[float, Field(strict=True, ge=0, le=3600, allow_inf_nan=False)] = 0.0


class TokenReservation(Model):
    input_tokens: Annotated[int, Field(strict=True, ge=1, le=131072)] = 2048
    output_tokens: Annotated[int, Field(strict=True, ge=1, le=8192)] = 512


class TokenUsage(Model):
    input_tokens: Count
    output_tokens: Count


class TokenPrices(Model):
    """Declared integer micro-USD per token; defaults model a free offline fixture."""
    input_microusd: Money = 0
    output_microusd: Money = 0

    def cost(self, usage: TokenUsage | TokenReservation) -> int:
        return usage.input_tokens * self.input_microusd + usage.output_tokens * self.output_microusd


class ProposalRequest(Model):
    spec: DesignSpec
    seed: Annotated[int, Field(strict=True, ge=0, le=2**32 - 1)]
    request_number: Annotated[int, Field(strict=True, ge=1, le=128)]
    token_limits: TokenReservation


@dataclass(frozen=True)
class ProviderReply:
    """Only candidate JSON is untrusted model content; usage comes from the adapter."""
    candidate_json: str | bytes
    usage: TokenUsage


class ProposalProvider(Protocol):
    def propose(self, request: ProposalRequest) -> ProviderReply:
        """Return one response. Real transport/deadlines require a separate adapter."""
        ...


class ProposalAttempt(Model):
    request_number: int
    status: Literal["pending", "accepted", "invalid_candidate", "invalid_response", "provider_error", "usage_overrun"]
    candidate: CircuitCandidate | None = None
    accounting: Literal["reserved", "reported"] = "reserved"
    input_tokens: Count
    output_tokens: Count
    cost_microusd: int


class SessionUsage(Model):
    requests: int
    input_tokens: int
    output_tokens: int
    cost_microusd: int
    blocked: bool


class ProposalBlocked(RuntimeError):
    """Pre-call rejection: the provider was not invoked or charged."""


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError("nonfinite JSON number")


def _candidate(payload: str | bytes, spec: DesignSpec) -> CircuitCandidate:
    if not isinstance(payload, (str, bytes)):
        raise ValueError("candidate must be JSON text")
    if len(payload) > MAX_CANDIDATE_BYTES:
        raise ValueError("candidate JSON exceeds byte limit")
    raw = payload.encode("utf-8") if isinstance(payload, str) else payload
    if len(raw) > MAX_CANDIDATE_BYTES:
        raise ValueError("candidate JSON exceeds byte limit")
    obj = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object, parse_constant=_reject_constant)
    # CircuitCandidate has defaults for local convenience; a proposal must be explicit.
    required = {"topology", "resistance_ohm", "capacitance_f"}
    if not isinstance(obj, dict) or not required.issubset(obj):
        raise ValueError("proposal requires all candidate fields")
    candidate = CircuitCandidate.model_validate(obj)
    spec.validate_candidate(candidate)
    return candidate


class ProposalSession:
    """Bound one local proposal session without changing the SPICE call budget.

    Reserve worst-case tokens/cost before invoking the adapter. Settle only valid
    usage reports; exceptions or malformed usage retain the entire reservation.
    A report above its reservation is recorded honestly and blocks future calls.
    There are no automatic retries, waits, network calls or simulator invocations.
    """
    def __init__(self, spec: DesignSpec, provider: ProposalProvider, *, seed: int = 42,
                 limits: ProposalLimits = ProposalLimits(), prices: TokenPrices = TokenPrices(),
                 clock: Callable[[], float] = time.monotonic):
        # Revalidate even model_copy/model_construct objects at this boundary.
        self.spec = DesignSpec.model_validate(spec.model_dump())
        self.limits = ProposalLimits.model_validate(limits.model_dump())
        self.prices = TokenPrices.model_validate(prices.model_dump())
        self.seed = ProposalRequest(spec=self.spec, seed=seed, request_number=1,
                                    token_limits=TokenReservation()).seed
        self._provider, self._clock = provider, clock
        self._lock = Lock()
        self._history: list[ProposalAttempt] = []
        self._requests = self._input = self._output = self._cost = 0
        self._last_start: float | None = None
        self._blocked = False

    @property
    def history(self) -> tuple[ProposalAttempt, ...]:
        return tuple(self._history)

    @property
    def usage(self) -> SessionUsage:
        return SessionUsage(requests=self._requests, input_tokens=self._input,
                            output_tokens=self._output, cost_microusd=self._cost, blocked=self._blocked)

    def propose(self, reservation: TokenReservation = TokenReservation()) -> ProposalAttempt:
        if not self._lock.acquire(blocking=False):
            raise ProposalBlocked("session already has an active proposal")
        try:
            return self._propose(TokenReservation.model_validate(reservation.model_dump()))
        finally:
            self._lock.release()

    def _propose(self, reservation: TokenReservation) -> ProposalAttempt:
        if self._blocked:
            raise ProposalBlocked("session blocked after adapter usage overrun")
        if self._requests >= self.limits.max_requests:
            raise ProposalBlocked("request budget exhausted")
        if self._input + self._output + reservation.input_tokens + reservation.output_tokens > self.limits.max_total_tokens:
            raise ProposalBlocked("token reservation exceeds remaining budget")
        reserved_cost = self.prices.cost(reservation)
        if self._cost + reserved_cost > self.limits.max_cost_microusd:
            raise ProposalBlocked("cost reservation exceeds remaining budget")
        now = self._clock()
        if not math.isfinite(now) or (self._last_start is not None and now - self._last_start < self.limits.min_interval_s):
            raise ProposalBlocked("proposal rate limit or invalid monotonic clock")
        self._last_start = now
        self._requests += 1
        self._input += reservation.input_tokens
        self._output += reservation.output_tokens
        self._cost += reserved_cost
        pending = ProposalAttempt(request_number=self._requests, status="pending",
                                  input_tokens=reservation.input_tokens, output_tokens=reservation.output_tokens,
                                  cost_microusd=reserved_cost)
        self._history.append(pending)
        request = ProposalRequest(spec=self.spec, seed=self.seed, request_number=self._requests, token_limits=reservation)
        try:
            reply = self._provider.propose(request)
        except BaseException as exc:
            result = pending.model_copy(update={"status": "provider_error"})
            self._history[-1] = result
            if not isinstance(exc, Exception):
                raise
            return result
        try:
            if not isinstance(reply, ProviderReply) or not isinstance(reply.usage, TokenUsage):
                raise ValueError("adapter returned an invalid response envelope")
            usage = TokenUsage.model_validate(reply.usage.model_dump())
        except (ValueError, TypeError, AttributeError):
            result = pending.model_copy(update={"status": "invalid_response"})
        else:
            cost = self.prices.cost(usage)
            self._input += usage.input_tokens - reservation.input_tokens
            self._output += usage.output_tokens - reservation.output_tokens
            self._cost += cost - reserved_cost
            overrun = usage.input_tokens > reservation.input_tokens or usage.output_tokens > reservation.output_tokens
            result = ProposalAttempt(request_number=self._requests, status="usage_overrun" if overrun else "invalid_candidate",
                                     accounting="reported", input_tokens=usage.input_tokens,
                                     output_tokens=usage.output_tokens, cost_microusd=cost)
            if overrun:
                self._blocked = True
            else:
                try:
                    candidate = _candidate(reply.candidate_json, self.spec)
                except (ValueError, TypeError, UnicodeError, RecursionError, ValidationError):
                    pass  # Never persist untrusted text or exception strings in the ledger.
                else:
                    result = result.model_copy(update={"status": "accepted", "candidate": candidate})
        self._history[-1] = result
        return result
