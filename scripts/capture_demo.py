"""Capture installed CLI results and render an explicitly labeled 75-second replay."""
from __future__ import annotations

import argparse
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess

from circuforge.application import load_request
from circuforge.contracts import DesignResult
from circuforge.evaluation.acceptance import require
from circuforge.evaluation.design_acceptance import audit_design
from circuforge.evaluation.records import environment

POLICY = "p7-captured-cli-demo-v1"
CASES = (("design-lowpass", "passed", 1), ("design-optimization", "passed", 4),
         ("design-target-miss", "target_missed", 4))
CAPTION = "Captured installed CLI output - annotated replay, not a live screen recording"
CLAIMS = ("Draft wording, not owner approval or a publication:\n\n"
          "Implemented a local Python RC filter simulation and optimization pipeline with typed specifications, "
          "allowlisted ngspice netlists, bounded numerical search and reproducible exports. "
          "Validated installed CLI behavior with raw physics checks while preserving target misses. "
          "Simulation validation is not hardware verification; no general LLM-performance claim is made.\n")


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frames(results: list[DesignResult], roots: list[Path]):
    from PIL import Image, ImageDraw, ImageFont
    from matplotlib.font_manager import findfont

    font_path = findfont("DejaVu Sans Mono")
    title_font = ImageFont.truetype(font_path, 31)
    body_font = ImageFont.truetype(font_path, 22)
    small_font = ImageFont.truetype(font_path, 17)

    def canvas(title):
        image = Image.new("RGB", (1280, 800), "#101820")
        draw = ImageDraw.Draw(image)
        draw.text((35, 25), title, font=title_font, fill="#ffffff")
        draw.text((35, 76), CAPTION, font=small_font, fill="#a8c9df")
        return image, draw

    first, draw = canvas("CircuForge: installed local CLI walkthrough")
    draw.multiline_text((45, 170), "Typed RC specifications\nTrusted templates -> real ngspice AC sweeps\nMeasured cutoff -> independent analytic check\nBounded grid search and explicit target misses\n\nNo model inference or cloud is used in this demo.\nFull commands, transcripts and raw data accompany it.\n\nPresentation timing: 15 seconds per slide; 75 seconds per loop.",
                        font=body_font, fill="white", spacing=18)
    output = [first]
    for (name, _, _), result, root in zip(CASES, results, roots):
        image, draw = canvas(name)
        best = result.best
        text = (f"status: {result.status}\nmethod: {result.request.method}\n"
                f"target: {result.request.spec.cutoff_hz:.6f} Hz\n"
                f"measured: {best.measured_cutoff_hz:.6f} Hz\n"
                f"target error: {100 * best.relative_error:.6f}%\n"
                f"R: {best.candidate.resistance_ohm:.6g} ohm\nC: {best.candidate.capacitance_f:.6g} F\n"
                f"SPICE attempts: {result.simulator_calls}\n"
                f"physics verified: {str(best.verified).lower()}")
        draw.multiline_text((35, 155), text, font=body_font, fill="white", spacing=13)
        with Image.open(root / "response.png") as source:
            chart = source.convert("RGB")
            chart.thumbnail((650, 515), Image.Resampling.LANCZOS)
            image.paste(chart, (610, 155))
        draw.text((35, 730), f"Transcript: {name}/stdout.json; raw evidence: {name}/cli/", font=small_font, fill="#a8c9df")
        output.append(image)
    last, draw = canvas("What these observed results support")
    calls = sum(result.simulator_calls for result in results)
    passes = sum(result.status == "passed" for result in results)
    misses = sum(result.status == "target_missed" for result in results)
    draw.multiline_text((45, 165), f"{passes} passing examples; {misses} preserved target miss\n{calls} actual simulator calls, independently raw-audited\n\nRun from an installed package with Python -I.\nSchemas, JSON stdout and raw traces must agree.\nCLI exit 1 for a target miss is intentional.\n\nIdeal source/load and continuous R/C only.\nNo hardware, optimizer-superiority or live-recording claim.\nDraft portfolio wording accompanies the evidence.",
                        font=body_font, fill="white", spacing=17)
    output.append(last)
    return output


def gif_bytes(images) -> bytes:
    stream = BytesIO()
    images[0].save(stream, format="GIF", save_all=True, append_images=images[1:],
                   duration=15000, loop=0, disposal=2, optimize=False)
    return stream.getvalue()


def capture(python: Path, source: Path, output: Path, ngspice: str) -> dict:
    requests = [load_request(source / (name + ".json")) for name, _, _ in CASES]
    require(all(r.spec.max_evaluations == 4 and r.spec.timeout_s <= 2 and
                r.spec.sweep.expected_points <= 1001 for r in requests), "demo examples exceed frozen compute caps")
    require([r.method for r in requests] == ["simulate", "grid", "grid"], "unexpected demo method")
    output.mkdir(parents=True, exist_ok=False)
    env = {**os.environ}
    env.pop("PYTHONPATH", None)
    probe_command = [str(python), "-I", "-c", "import json,sys,circuforge; from circuforge.evaluation.records import environment; print(json.dumps({'prefix':sys.prefix,'module':circuforge.__file__,'environment':environment()}))"]
    probe = subprocess.run(probe_command, cwd=output, env=env, capture_output=True, check=True, timeout=15)
    identity = json.loads(probe.stdout)
    module = Path(identity["module"]).resolve()
    require(module.is_relative_to(Path(identity["prefix"]).resolve()) and "site-packages" in module.parts and
            identity["environment"] == environment(), "demo must use a matching isolated installed package")
    results, roots, records = [], [], []
    for (name, expected, calls), request in zip(CASES, requests):
        root = output / name
        root.mkdir()
        destination = root / "cli"
        command = [str(python), "-I", "-m", "circuforge", "--ngspice", ngspice, "design",
                   "--request", str((source / (name + ".json")).resolve()), "--output", str(destination.resolve())]
        with (root / "stdout.json").open("wb") as stdout, (root / "stderr.log").open("wb") as stderr:
            completed = subprocess.run(command, cwd=output, env=env, stdout=stdout, stderr=stderr,
                                       stdin=subprocess.DEVNULL, shell=False, timeout=45)
        result = audit_design(destination, request)
        require(result == DesignResult.model_validate_json((root / "stdout.json").read_bytes()), "CLI stdout differs from artifacts")
        require(result.status == expected and result.simulator_calls == calls and
                completed.returncode == (0 if expected == "passed" else 1), "demo outcome differs from frozen expectation")
        results.append(result)
        roots.append(destination)
        records.append(dict(case=name, command=command, exit=completed.returncode, status=result.status,
                            calls=result.simulator_calls, input_sha256=sha256(source / (name + ".json")),
                            stdout_sha256=sha256(root / "stdout.json")))
    images = frames(results, roots)
    for index, image in enumerate(images):
        image.save(output / f"frame-{index:02d}.png")
    (output / "demo.gif").write_bytes(gif_bytes(images))
    (output / "claims.md").write_text(CLAIMS, encoding="utf-8")
    report = dict(policy=POLICY, capture_kind="annotated replay of captured installed CLI output; not live screen recording",
                  exporter_sha256=sha256(Path(__file__)),
                  new_model_requests=0, actual_spice_calls=sum(row["calls"] for row in records),
                  duration_ms=75000, frames=5, loops=True, installed_identity=identity, probe_command=probe_command,
                  cases=records, gif_sha256=sha256(output / "demo.gif"), claims_sha256=sha256(output / "claims.md"),
                  owner_cv_approved=False, remote_published=False)
    (output / "demo.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", type=Path, required=True, help="trusted isolated installed-package interpreter")
    parser.add_argument("--source", type=Path, required=True, help="versioned example directory")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ngspice", required=True)
    args = parser.parse_args(argv)
    try:
        report = capture(args.python, args.source, args.output.resolve(), args.ngspice)
        print(f"Captured {len(report['cases'])} installed CLI examples/{report['actual_spice_calls']} real calls; 75-second annotated replay exported.")
        return 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"Demo capture blocked: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
