"""Installed-package CLI and real loopback HTTP walkthrough; no source imports."""
import argparse
import json
from pathlib import Path
import socket
import subprocess
import sys
from threading import Thread
import time

import circuforge
import httpx
import uvicorn

from circuforge.api import create_app
from circuforge.application import load_request
from circuforge.contracts import DesignResult
from circuforge.evaluation.design_acceptance import audit_design, compare_interfaces, extract_bundle
from circuforge.evaluation.records import environment

CASES = ("design-lowpass", "design-optimization", "design-target-miss")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="example data directory, not a Python import path")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ngspice", required=True)
    args = parser.parse_args(argv)
    args.output = args.output.resolve()
    args.source = args.source.resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    scratch = args.output / "server-temp"
    scratch.mkdir()
    module = Path(circuforge.__file__).resolve()
    if not module.is_relative_to(Path(sys.prefix).resolve()) or "site-packages" not in module.parts:
        raise ValueError("walkthrough must run the freshly installed package with Python -I")
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(create_app(ngspice=args.ngspice, temporary_root=scratch),
                                         host="127.0.0.1", port=port, workers=1, proxy_headers=False,
                                         limit_concurrency=8, log_level="warning", timeout_keep_alive=5,
                                         timeout_graceful_shutdown=30))
    worker = Thread(target=server.run, name="circuforge-local-walkthrough", daemon=True)
    worker.start()
    commands, rows, rejected = [], [], {}
    try:
        with httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=45, trust_env=False) as client:
            deadline = time.monotonic() + 15
            health = None
            while time.monotonic() < deadline:
                try:
                    response = client.get("/health")
                    if response.status_code == 200:
                        health = response.json()
                        break
                except httpx.TransportError:
                    pass
                time.sleep(.05)
            if not health or health.get("service") != "circuforge":
                raise ValueError("local API failed startup/identity check")
            payload = json.loads((args.source / "design-lowpass.json").read_text(encoding="utf-8"))
            for name, body, headers, expected in (
                ("unsupported_netlist", {**payload, "netlist": ".control"}, {}, 422),
                ("browser_origin", payload, {"Origin": "https://untrusted.example"}, 403),
            ):
                response = client.post("/v1/designs", json=body, headers=headers)
                if response.status_code != expected:
                    raise ValueError(f"guard failed: {name}")
                rejected[name] = response.status_code
            oversized = client.post("/v1/designs", content=b"x" * 16385, headers={"Content-Type": "application/json"})
            if oversized.status_code != 413 or list(scratch.iterdir()):
                raise ValueError("body guard or rejected-request cleanup failed")
            rejected["oversized_body"] = oversized.status_code
            for name in CASES:
                source = args.source / (name + ".json")
                request = load_request(source)
                root = args.output / name
                root.mkdir()
                command = [sys.executable, "-I", "-m", "circuforge", "--ngspice", args.ngspice,
                           "design", "--request", str(source), "--output", str(root / "cli")]
                commands.append(command)
                with (root / "cli.stdout.json").open("wb") as stdout, (root / "cli.stderr.log").open("wb") as stderr:
                    result = subprocess.run(command, cwd=args.output, stdout=stdout, stderr=stderr,
                                            stdin=subprocess.DEVNULL, timeout=60, shell=False)
                expected_exit = 1 if name == "design-target-miss" else 0
                if result.returncode != expected_exit:
                    raise ValueError(f"CLI example {name} exited {result.returncode}")
                payload = json.loads(source.read_text(encoding="utf-8"))
                response = client.post("/v1/designs", json=payload)
                if response.status_code != 200 or list(scratch.iterdir()):
                    raise ValueError(f"JSON response/cleanup failed for {name}")
                (root / "api.json").write_bytes(response.content)
                downloaded = client.post("/v1/designs/export", json=payload)
                if downloaded.status_code != 200 or downloaded.headers.get("content-type") != "application/zip" or list(scratch.iterdir()):
                    raise ValueError(f"ZIP response/cleanup failed for {name}")
                (root / "api.zip").write_bytes(downloaded.content)
                extract_bundle(root / "api.zip", root / "api")
                cli = audit_design(root / "cli", request)
                zipped = audit_design(root / "api", request)
                api = DesignResult.model_validate_json(response.content)
                compare_interfaces(cli, api, zipped)
                row = {"case": name, "status": cli.status, "calls_per_interface": cli.simulator_calls,
                       "cli_exit": result.returncode, "json_http": response.status_code, "zip_http": downloaded.status_code,
                       "zip_status": downloaded.headers.get("x-circuforge-status"),
                       "temporary_storage_empty": True}
                rows.append(row)
                print(json.dumps(row), flush=True)
    finally:
        server.should_exit = True
        worker.join(timeout=40)
        if worker.is_alive():
            raise RuntimeError("local server did not stop within its bounded shutdown period")
    summary = {"status": "passed", "installed_module": str(module), "prefix": sys.prefix,
               "environment": environment(), "commands": commands, "health": health, "rejected": rejected,
               "server_stopped": not worker.is_alive(), "temporary_storage_empty": not list(scratch.iterdir()),
               "actual_simulator_calls": sum(r["calls_per_interface"] * 3 for r in rows),
               "raw_calls_audited": sum(r["calls_per_interface"] * 2 for r in rows), "cases": rows}
    (args.output / "walkthrough.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
