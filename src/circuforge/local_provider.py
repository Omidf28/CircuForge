"""Opt-in pinned local Ollama adapter; never imported by the basic design engine."""
import asyncio
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import time

from circuforge.proposals import ProposalRequest, ProviderReply, TokenUsage

MODEL = "llama3:latest"
DIGEST = "365c0bd3c000a25d28ddbf732fe1c6add414de7275464c4e4d1c3b5fcb5d8ad1"
BASE_URL = "http://127.0.0.1:11434"
MAX_RESPONSE_BYTES = 64 * 1024
RESERVED_INPUT = 2048
MAX_OUTPUT = 256


class LocalTrialLimit(RuntimeError):
    """A shared approved experiment limit has been reached."""


class LocalModelError(RuntimeError):
    """Pinned local service could not provide a complete bounded response."""


def write_json(path: Path, value) -> None:
    """Evidence writer: caller chooses a trusted directory, never the model."""
    staging = path.with_suffix(path.suffix + ".tmp")
    with staging.open("w", encoding="utf-8") as stream:
        stream.write(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(staging, path)


class TrialBudget:
    """One persistent experiment ledger; reserve before any generation request.

    A preexisting ledger cannot be reopened/reset. There are no automatic retries
    or resumptions. HTTP failures retain their request/token reservations.
    """
    def __init__(self, output: Path, *, clock=time.monotonic):
        self.output = output
        self._clock = clock
        self.started = clock()
        self.last_request = None
        self.requests = self.spice_calls = 0
        self.blocked = False
        self.records = []
        if (output / "budget.json").exists():
            raise LocalTrialLimit("existing experiment ledger cannot be reset")
        self.save()

    def remaining(self) -> float:
        remaining = 600.0 - (self._clock() - self.started)
        if not math.isfinite(remaining) or not 0 < remaining <= 600:
            raise LocalTrialLimit("experiment deadline reached or clock invalid")
        if self.blocked:
            raise LocalTrialLimit("experiment blocked after reported usage overrun")
        return remaining

    @classmethod
    def continue_rejected_pilot(cls, output: Path):
        """One explicit continuation, retaining counters and the original deadline.

        The initial ledger predates persisted start clocks. Its final file mtime
        plus saved elapsed time reconstructs that start conservatively (five
        seconds earlier). Unknown/malformed/changed histories cannot continue.
        This is not a new allowance, an automatic retry or a quota reset.
        """
        path = output / "budget.json"
        saved = json.loads(path.read_text(encoding="utf-8"))
        if (saved["model_requests"] != 1 or saved["spice_attempts"] != 0 or saved["blocked"] or
                len(saved["records"]) != 1 or saved["records"][0]["status"] != "reported"):
            raise LocalTrialLimit("only the single recorded rejected pilot can continue")
        age = time.time() - path.stat().st_mtime
        elapsed = saved["elapsed_s"] + age + 5.0
        if age < 0 or not math.isfinite(elapsed) or not 0 < elapsed < 600:
            raise LocalTrialLimit("original experiment deadline cannot be extended")
        instance = cls.__new__(cls)
        instance.output, instance._clock = output, time.monotonic
        instance.started = time.monotonic() - elapsed
        # Reconstruct the prior request start too; do not waive the rate limit
        # if an unusually fast rejected pilot is continued immediately.
        duration = float(saved["records"][0].get("client_elapsed_s", 0.0))
        if not math.isfinite(duration) or duration < 0:
            raise LocalTrialLimit("invalid recorded request duration")
        instance.last_request = time.monotonic() - max(0.0, age + duration)
        instance.requests, instance.spice_calls = 1, 0
        instance.blocked, instance.records = False, saved["records"]
        write_json(output / "initial-budget-before-continuation.json", saved)
        instance.save()
        return instance

    def save(self):
        write_json(self.output / "budget.json", dict(
            model_requests=self.requests, reserved_tokens=self.requests * (RESERVED_INPUT + MAX_OUTPUT),
            spice_attempts=self.spice_calls, blocked=self.blocked,
            elapsed_s=max(0.0, self._clock() - self.started),
            started_monotonic=self.started,
            cost_microusd=0, records=self.records))

    def reserve_model(self) -> int:
        self.remaining()
        if self.requests >= 32:
            raise LocalTrialLimit("32-request experiment ceiling reached")
        now = self._clock()
        if self.last_request is not None and now - self.last_request < 1.0:
            raise LocalTrialLimit("one-second global request interval not satisfied")
        self.last_request = now
        self.requests += 1
        self.records.append(dict(request=self.requests, status="reserved", reserved_tokens=2304))
        self.save()  # If durable reservation fails, no request is sent.
        return self.requests

    def settle(self, index: int, *, status: str, usage: TokenUsage | None = None):
        record = self.records[index - 1]
        record["status"] = status
        if usage is not None:
            record["reported_usage"] = usage.model_dump()
            if usage.input_tokens > RESERVED_INPUT or usage.output_tokens > MAX_OUTPUT:
                self.blocked = True
        self.save()

    def reserve_spice(self):
        self.remaining()
        if self.spice_calls >= 80:
            raise LocalTrialLimit("80-attempt experiment SPICE ceiling reached")
        self.spice_calls += 1
        self.save()


class OllamaProvider:
    """Trusted synchronous adapter with fixed loopback identity and total deadline.

    HTTPX is an optional local-model dependency. The injected transport is only
    for controlled tests. This adapter is not an untrusted-code sandbox.
    """
    def __init__(self, budget: TrialBudget, *, transport=None):
        self.budget = budget
        self._transport = transport
        self.info = None

    async def _request(self, method: str, endpoint: str, *, payload=None, timeout_s: float):
        import httpx

        if endpoint not in {"/api/tags", "/api/show", "/api/version", "/api/generate"}:
            raise LocalModelError("unsupported local endpoint")
        async with asyncio.timeout(timeout_s):
            async with httpx.AsyncClient(trust_env=False, follow_redirects=False,
                                         transport=self._transport, timeout=timeout_s) as client:
                async with client.stream(method, BASE_URL + endpoint, json=payload) as response:
                    if response.status_code != 200:
                        raise LocalModelError(f"local service returned HTTP {response.status_code}")
                    if int(response.headers.get("content-length", "0")) > MAX_RESPONSE_BYTES:
                        raise LocalModelError("local response exceeds byte limit")
                    body = bytearray()
                    async for chunk in response.aiter_bytes(chunk_size=4096):
                        if len(body) + len(chunk) > MAX_RESPONSE_BYTES:
                            raise LocalModelError("local response exceeds byte limit")
                        body.extend(chunk)
        result = json.loads(body)
        if not isinstance(result, dict):
            raise LocalModelError("local service returned a non-object envelope")
        return result

    def preflight(self):
        async def inspect():
            tags = await self._request("GET", "/api/tags", timeout_s=5.0)
            matches = [m for m in tags.get("models", []) if m.get("name") == MODEL]
            if len(matches) != 1 or matches[0].get("digest") != DIGEST:
                raise LocalModelError("approved model digest is not installed; no download permitted")
            show = await self._request("POST", "/api/show", payload={"model": MODEL}, timeout_s=5.0)
            if "completion" not in show.get("capabilities", []):
                raise LocalModelError("approved model has no completion capability")
            version = await self._request("GET", "/api/version", timeout_s=5.0)
            return dict(model=MODEL, digest=DIGEST, ollama_version=version.get("version"),
                        endpoint=BASE_URL, capabilities=show["capabilities"])

        try:
            self.info = asyncio.run(inspect())
        except Exception as exc:
            raise LocalModelError("local model preflight failed: " + type(exc).__name__) from exc
        write_json(self.budget.output / "local-model.json", self.info)
        return self.info

    def propose(self, request: ProposalRequest) -> ProviderReply:
        if self.info is None:
            raise LocalModelError("local model preflight must pass before inference")
        if request.token_limits.input_tokens != RESERVED_INPUT or request.token_limits.output_tokens != MAX_OUTPUT:
            raise LocalModelError("request does not match approved token reservation")
        spec = request.spec
        prompt = (
            f"Propose one ideal unloaded {spec.filter_type} circuit for cutoff {spec.cutoff_hz:g} Hz. "
            f"Resistance range [{spec.resistance_ohm.minimum:g}, {spec.resistance_ohm.maximum:g}] ohm. "
            f"Capacitance range [{spec.capacitance_f.minimum:g}, {spec.capacitance_f.maximum:g}] F. "
            f"Trial seed {request.seed}; proposal {request.request_number}. Choose a distinct pair for this proposal. "
            "Return only JSON with topology, resistance_ohm and capacitance_f as SI numeric values."
        )
        schema = dict(type="object", additionalProperties=False,
                      required=["topology", "resistance_ohm", "capacitance_f"], properties={
                          "topology": {"type": "string", "enum": [spec.filter_type]},
                          "resistance_ohm": {"type": "number"}, "capacitance_f": {"type": "number"}})
        payload = dict(model=MODEL, prompt=prompt, format=schema, stream=False, keep_alive=0,
                       options=dict(seed=(request.seed + request.request_number - 1) % 2**32,
                                    num_ctx=2048, num_predict=MAX_OUTPUT, num_gpu=0, num_thread=2,
                                    temperature=0.7))
        index = self.budget.reserve_model()
        write_json(self.budget.output / f"model-{index:03d}-request.json", payload)
        started = time.monotonic()
        try:
            async def generate():
                # Recheck the tag on every call; do not silently use a replaced model.
                tags = await self._request("GET", "/api/tags", timeout_s=min(5.0, self.budget.remaining()))
                if not any(m.get("name") == MODEL and m.get("digest") == DIGEST for m in tags.get("models", [])):
                    raise LocalModelError("approved local model identity changed")
                return await self._request("POST", "/api/generate", payload=payload,
                                           timeout_s=min(60.0 - (time.monotonic() - started), self.budget.remaining()))

            data = asyncio.run(generate())
            write_json(self.budget.output / f"model-{index:03d}-response.json", data)
            if data.get("done") is not True or data.get("model") != MODEL or not isinstance(data.get("response"), str):
                raise LocalModelError("incomplete or mismatched local model response")
            usage = TokenUsage(input_tokens=data.get("prompt_eval_count"), output_tokens=data.get("eval_count"))
            self.budget.settle(index, status="reported", usage=usage)
            return ProviderReply(data["response"], usage)
        except BaseException as exc:
            self.budget.settle(index, status=type(exc).__name__)
            raise
        finally:
            self.budget.records[index - 1]["client_elapsed_s"] = time.monotonic() - started
            self.budget.records[index - 1]["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
            self.budget.save()
