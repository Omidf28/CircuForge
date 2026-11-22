import csv
import hashlib
import platform
from pathlib import Path

import numpy as np
import pydantic

from circuforge import __version__
from circuforge.simulation.ngspice import SimulationResult


def environment() -> dict:
    import scipy

    root = Path(__file__).resolve().parents[1]
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*.py")):
        digest.update(path.relative_to(root).as_posix().encode() + b"\0" + path.read_bytes())
    return {"python": platform.python_version(), "platform": platform.platform(),
            "circuforge": __version__, "numpy": np.__version__, "pydantic": pydantic.__version__,
            "scipy": scipy.__version__, "source_sha256": digest.hexdigest()}


def write_response(directory: Path, result: SimulationResult) -> None:
    """Write genuine response data into an existing per-call directory."""
    (directory / "circuit.cir").write_text(result.netlist, encoding="ascii")
    (directory / "stdout.log").write_text(result.stdout, encoding="utf-8")
    (directory / "stderr.log").write_text(result.stderr, encoding="utf-8")
    response = result.response
    with (directory / "response.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["frequency_hz", "transfer_real", "transfer_imag", "gain_db", "phase_deg"])
        writer.writerows(zip(response.frequency_hz, response.transfer.real, response.transfer.imag,
                              response.gain_db, response.phase_deg))
