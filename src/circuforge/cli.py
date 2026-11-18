"""Executable Phase 1 demo with traceable JSON/CSV artifacts."""

import argparse
import csv
from dataclasses import asdict
import json
from pathlib import Path
import platform
import sys

import numpy as np
import pydantic

from circuforge import __version__
from circuforge.domain.specs import CircuitCandidate, DesignSpec
from circuforge.optimization.search import SearchFailure, search
from circuforge.simulation.metrics import analytic_cutoff, cutoff_hz
from circuforge.simulation.ngspice import Ngspice, SimulationError, preflight
from circuforge.synthesis.rc import netlist


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ngspice", help="trusted local executable path (also CIRCUFORGE_NGSPICE)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("preflight", help="check actual simulator availability and version")
    sim = sub.add_parser("simulate", help="run an ideal unloaded RC sweep")
    sim.add_argument("--search", action="store_true", help="bounded deterministic R/C search for the spec target")
    sim.add_argument("--spec", type=Path, default=Path("examples/lowpass.json"))
    sim.add_argument("--resistance-ohm", type=float, default=1000.0)
    sim.add_argument("--capacitance-f", type=float, default=100e-9)
    sim.add_argument("--output", type=Path, required=True, help="new artifact directory")
    args = parser.parse_args(argv)
    try:
        if args.command == "preflight":
            print(json.dumps({"status": "available", **asdict(preflight(args.ngspice))}, indent=2))
            return 0
        spec = DesignSpec.model_validate_json(args.spec.read_text(encoding="utf-8"))
        candidate = CircuitCandidate(topology=spec.filter_type, resistance_ohm=args.resistance_ohm, capacitance_f=args.capacitance_f)
        if not args.search:
            spec.validate_candidate(candidate)
        args.output.mkdir(parents=True, exist_ok=False)
        simulator = Ngspice(args.ngspice)
        searched = search(spec, simulator) if args.search else None
        if searched:
            candidate, result = searched.candidate, searched.simulation
        else:
            result = simulator.simulate(spec, candidate)
        # Save genuine raw evidence before metric extraction, including on metric failure.
        (args.output / "circuit.cir").write_text(result.netlist, encoding="ascii")
        (args.output / "stdout.log").write_text(result.stdout, encoding="utf-8")
        (args.output / "stderr.log").write_text(result.stderr, encoding="utf-8")
        try:
            measured = cutoff_hz(result.response, candidate.topology)
        except ValueError as exc:
            raise SimulationError("metric_error", str(exc), stdout=result.stdout,
                                  stderr=result.stderr, returncode=result.returncode) from exc
        analytic = analytic_cutoff(candidate)
        analytic_error = abs(measured / analytic - 1)
        target_error = abs(measured / spec.cutoff_hz - 1)
        report = {
            "status": "success", "spec": spec.model_dump(), "candidate": candidate.model_dump(),
            "measured_cutoff_hz": measured, "analytic_cutoff_hz": analytic,
            "analytic_relative_error": analytic_error, "target_relative_error": target_error,
            "analytic_check_passed": analytic_error <= 0.001,
            "target_passed": target_error <= spec.relative_error_tolerance,
            "simulator_calls": searched.simulator_calls if searched else 1,
            "search_history": searched.history if searched else [],
            "search_method": "log-bounds bisection" if searched else None,
            "elapsed_s": sum(x["elapsed_s"] for x in searched.history) if searched else result.elapsed_s,
            "command": result.command, "returncode": result.returncode,
            "ngspice_version": result.version,
            "environment": {"python": platform.python_version(), "platform": platform.platform(),
                            "circuforge": __version__, "numpy": np.__version__, "pydantic": pydantic.__version__},
            "assumptions": ["ideal zero-ohm source", "infinite load", "ideal continuous R/C values"],
            "cutoff_method": "linear dB interpolation in log-frequency at -10*log10(2), unity DC gain",
        }
        (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        response = result.response
        with (args.output / "response.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(["frequency_hz", "transfer_real", "transfer_imag", "gain_db", "phase_deg"])
            writer.writerows(zip(response.frequency_hz, response.transfer.real, response.transfer.imag,
                                  response.gain_db, response.phase_deg))
        print(json.dumps(report, indent=2))
        return 0 if report["analytic_check_passed"] and report["target_passed"] else 1
    except SimulationError as exc:
        error = {"status": exc.status, "error": str(exc), "returncode": exc.returncode,
                 "stdout": exc.stdout, "stderr": exc.stderr}
        if isinstance(exc, SearchFailure):
            error.update(exc.context())
        if getattr(args, "output", None) and args.output.is_dir():
            if isinstance(exc, SearchFailure):
                (args.output / "circuit.cir").write_text(netlist(exc.spec, exc.candidate), encoding="ascii")
                (args.output / "stdout.log").write_text(exc.stdout, encoding="utf-8")
                (args.output / "stderr.log").write_text(exc.stderr, encoding="utf-8")
            (args.output / "failure.json").write_text(json.dumps(error, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(error, indent=2), file=sys.stderr)
        return 2
    except (ValueError, OSError) as exc:
        print(json.dumps({"status": "invalid_input_or_artifact", "error": str(exc)}), file=sys.stderr)
        return 2
