"""Bounded, single-worker loopback HTTP access to the shared design use case."""
import argparse
from pathlib import Path
import tempfile
from threading import BoundedSemaphore

import anyio
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, Response
from starlette.middleware.trustedhost import TrustedHostMiddleware

from circuforge.application import run_design
from circuforge.contracts import MAX_REQUEST_BYTES, DesignRequest, DesignResult, ServiceError
from circuforge.simulation.ngspice import Ngspice, SimulationError

API_CALL_LIMIT = 8
API_SWEEP_LIMIT = 1001
API_TIMEOUT_LIMIT = 2.


class LocalRequestGuard:
    """Bound streamed bodies before JSON parsing, and reject browser/remote callers."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = {k.lower(): v for k, v in scope["headers"]}
        client = scope.get("client")

        async def reject(code, message):
            response = JSONResponse({"code": "request_rejected", "message": message}, status_code=code)
            await response(scope, receive, send)

        if not client or client[0] not in {"127.0.0.1", "::1"} or b"origin" in headers:
            return await reject(403, "local non-browser clients only")
        if scope["method"] != "POST":
            return await self.app(scope, receive, send)
        if headers.get(b"content-type", b"").split(b";", 1)[0].strip().lower() != b"application/json":
            return await reject(415, "application/json required")
        try:
            declared = int(headers.get(b"content-length", b"0"))
        except ValueError:
            return await reject(400, "invalid content length")
        if declared < 0:
            return await reject(400, "invalid content length")
        if declared > MAX_REQUEST_BYTES:
            return await reject(413, "request exceeds 16 KiB")
        data = bytearray()
        try:
            with anyio.fail_after(5):
                while True:
                    event = await receive()
                    if event["type"] == "http.disconnect":
                        return
                    data.extend(event.get("body", b""))
                    if len(data) > MAX_REQUEST_BYTES:
                        return await reject(413, "request exceeds 16 KiB")
                    if not event.get("more_body", False):
                        break
        except TimeoutError:
            return await reject(408, "request body timeout")
        delivered = False

        async def replay_receive():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(data), "more_body": False}
            return await receive()

        await self.app(scope, replay_receive, send)


def check_api_limits(request: DesignRequest) -> None:
    if (request.spec.max_evaluations > API_CALL_LIMIT or request.spec.timeout_s > API_TIMEOUT_LIMIT or
            request.spec.sweep.expected_points > API_SWEEP_LIMIT):
        raise HTTPException(422, detail="API limits: <=8 calls, <=2 seconds/call, <=1001 AC samples")


def create_app(*, ngspice: str | None = None, temporary_root: Path | None = None) -> FastAPI:
    app = FastAPI(title="CircuForge local research API", version="0.1.0", docs_url=None, redoc_url=None)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "[::1]"], www_redirect=False)
    app.add_middleware(LocalRequestGuard)
    gate = BoundedSemaphore(1)
    app.state.design_gate = gate

    @app.get("/health")
    def health():
        return {"service": "circuforge", "status": "ready", "simulator": "not_checked", "max_calls": API_CALL_LIMIT,
                "max_call_timeout_s": API_TIMEOUT_LIMIT, "max_sweep_samples": API_SWEEP_LIMIT,
                "max_body_bytes": MAX_REQUEST_BYTES, "active_design_limit": 1}

    def execute(request: DesignRequest, archive: bool):
        check_api_limits(request)
        if not gate.acquire(blocking=False):
            raise HTTPException(429, detail="a design is already running; retry after it finishes")
        try:
            simulator = Ngspice(ngspice)
            with tempfile.TemporaryDirectory(prefix="circuforge-api-", dir=temporary_root) as directory:
                output = Path(directory) / "design"
                result = run_design(request, simulator, output)
                code = 502 if result.status == "simulation_failed" else 200
                if archive:
                    return Response((output / "bundle.zip").read_bytes(), status_code=code, media_type="application/zip",
                                    headers={"Content-Disposition": 'attachment; filename="circuforge-design.zip"',
                                             "X-CircuForge-Status": result.status})
                if code != 200:
                    return JSONResponse(result.model_dump(mode="json"), status_code=code)
                return result
        except SimulationError as exc:
            return JSONResponse(ServiceError(code=exc.status, message=str(exc)).model_dump(), status_code=503)
        except (OSError, ValueError, ImportError):
            return JSONResponse(ServiceError(code="artifact_error", message="local export failed; check dependencies and writable temporary storage").model_dump(), status_code=500)
        finally:
            gate.release()

    errors = {502: {"model": DesignResult}, 503: {"model": ServiceError}, 500: {"model": ServiceError}}

    @app.post("/v1/designs", response_model=DesignResult, responses=errors)
    def design(request: DesignRequest):
        return execute(request, False)

    @app.post("/v1/designs/export", response_class=Response,
              responses={200: {"content": {"application/zip": {"schema": {"type": "string", "format": "binary"}}}},
                         502: {"content": {"application/zip": {"schema": {"type": "string", "format": "binary"}}}},
                         503: {"model": ServiceError}, 500: {"model": ServiceError}})
    def design_export(request: DesignRequest):
        return execute(request, True)

    return app


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--ngspice", help="trusted server-side executable override")
    parser.add_argument("--temporary-root", type=Path, help="trusted server-side existing temporary directory")
    args = parser.parse_args(argv)
    if not 1024 <= args.port <= 65535:
        parser.error("port must be in [1024,65535]")
    import uvicorn

    if args.temporary_root is not None and not args.temporary_root.is_dir():
        parser.error("temporary-root must be an existing directory")
    uvicorn.run(create_app(ngspice=args.ngspice, temporary_root=args.temporary_root), host="127.0.0.1", port=args.port,
                workers=1, proxy_headers=False, limit_concurrency=8, timeout_keep_alive=5)


if __name__ == "__main__":
    main()
