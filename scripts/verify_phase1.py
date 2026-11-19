"""Run bounded Phase 1 reference fixtures; produce evidence for human review."""
import argparse
from contextlib import redirect_stderr, redirect_stdout
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import sys

import numpy as np
from pydantic import Field, TypeAdapter

from circuforge.cli import main as run_cli
from circuforge.domain.specs import CircuitCandidate, DesignSpec, Model, Positive

ROOT = Path(__file__).resolve().parents[1]


class Fixture(Model):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,59}$")
    topology: str
    resistance_ohm: Positive
    capacitance_f: Positive
    expected_cutoff_hz: Positive

    def candidate(self) -> CircuitCandidate:
        return CircuitCandidate(topology=self.topology, resistance_ohm=self.resistance_ohm,
                                capacitance_f=self.capacitance_f)


def source_fingerprint() -> str:
    digest = hashlib.sha256()
    for path in sorted((ROOT / "src").rglob("*.py")):
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=ROOT / "examples/phase1-fixtures.json")
    parser.add_argument("--output", type=Path, required=True, help="new output directory")
    parser.add_argument("--ngspice", help="trusted executable path override")
    args = parser.parse_args(argv)
    try:
        fixtures = TypeAdapter(list[Fixture]).validate_json(args.fixtures.read_text(encoding="utf-8"))
        if not 1 <= len(fixtures) <= 16 or len({f.id for f in fixtures}) != len(fixtures):
            raise ValueError("provide 1–16 reference fixtures with unique IDs")
        # Validate the entire input before allocating output or making SPICE calls.
        prepared = []
        for fixture in fixtures:
            candidate = fixture.candidate()
            expected = 1 / (2 * math.pi * candidate.resistance_ohm * candidate.capacitance_f)
            if not math.isclose(fixture.expected_cutoff_hz, expected, rel_tol=1e-10):
                raise ValueError(f"{fixture.id}: tabulated cutoff does not match the stated R/C")
            spec = DesignSpec(filter_type=candidate.topology, cutoff_hz=fixture.expected_cutoff_hz)
            spec.validate_candidate(candidate)
            prepared.append((fixture, candidate, spec))
        args.output.mkdir(parents=True, exist_ok=False)
        inputs = args.output / "specs"
        inputs.mkdir()
        records = []
        for fixture, candidate, spec in prepared:
            spec_path = inputs / f"{fixture.id}.json"
            spec_path.write_text(spec.model_dump_json(indent=2), encoding="utf-8")
            destination = args.output / fixture.id
            cli_args = (["--ngspice", args.ngspice] if args.ngspice else []) + [
                "simulate", "--spec", str(spec_path), "--output", str(destination),
                "--resistance-ohm", str(candidate.resistance_ohm),
                "--capacitance-f", str(candidate.capacitance_f),
            ]
            stdout, stderr = io.StringIO(), io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = run_cli(cli_args)
            record = {"id": fixture.id, "fixture": fixture.model_dump(), "cli_exit_code": code,
                      "command": [sys.executable, "-m", "circuforge", *cli_args], "passed": False}
            report_path = destination / "report.json"
            if report_path.is_file():
                report = json.loads(report_path.read_text(encoding="utf-8"))
                with (destination / "response.csv").open(encoding="utf-8", newline="") as stream:
                    rows = list(csv.DictReader(stream))
                freq = np.array([float(row["frequency_hz"]) for row in rows])
                transfer = np.array([complex(float(row["transfer_real"]), float(row["transfer_imag"])) for row in rows])
                normalized = 2j * math.pi * freq * candidate.resistance_ohm * candidate.capacitance_f
                expected_h = (1 if candidate.topology == "rc_lowpass" else normalized) / (1 + normalized)
                fc = fixture.expected_cutoff_hz
                gain = float(np.interp(math.log(fc), np.log(freq), 20 * np.log10(np.abs(transfer))))
                phase = float(np.interp(math.log(fc), np.log(freq), np.rad2deg(np.unwrap(np.angle(transfer)))))
                expected_phase = -45. if candidate.topology == "rc_lowpass" else 45.
                record.update(measured_cutoff_hz=report["measured_cutoff_hz"],
                              cutoff_relative_error=abs(report["measured_cutoff_hz"] / fc - 1),
                              gain_at_reference_cutoff_db=gain, phase_at_reference_cutoff_deg=phase,
                              response_matches_analytic=bool(np.allclose(transfer, expected_h, rtol=2e-5, atol=1e-8)),
                              ngspice_version=report["ngspice_version"])
                record["passed"] = bool(code == 0 and record["cutoff_relative_error"] <= .001
                                         and abs(gain + 10 * math.log10(2)) <= .001
                                         and abs(phase - expected_phase) <= .02
                                         and record["response_matches_analytic"])
            else:
                record["error"] = stderr.getvalue().strip()
            records.append(record)
            print(f"{fixture.id}: {'PASS' if record['passed'] else 'FAIL'}")
            # Preserve progress if a later case is interrupted.
            summary = {"purpose": "Phase 1 electrical fixtures; not an optimizer benchmark",
                       "acceptance_mode": "automated_reference_checks", "manual_review_required": False,
                       "source_sha256": source_fingerprint(),
                       "passed": all(r["passed"] for r in records) and len(records) == len(prepared),
                       "completed_cases": len(records), "planned_cases": len(prepared), "cases": records}
            (args.output / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        return 0 if summary["passed"] else 1
    except (OSError, ValueError) as exc:
        print(f"Phase 1 verification error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
