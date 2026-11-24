"""Exercise desktop failure and recovery with a window that stays withdrawn."""

import tkinter as tk
from types import SimpleNamespace
import time

from circuforge.desktop import model
from circuforge.desktop.app import DesktopApp
from circuforge.evaluation.design_acceptance import audit_design
from circuforge.simulation.ngspice import SimulationError


def wait_for_run(root, app):
    deadline = time.monotonic() + 20
    while app.controller.busy and time.monotonic() < deadline:
        root.update()
        assert root.state() == "withdrawn" and not root.winfo_ismapped()
        time.sleep(.01)
    assert not app.controller.busy and app.result is not None


def test_failed_sweep_reports_only_diagnostics_then_allows_retry(tmp_path, monkeypatch):
    class FailingSimulator:
        info = SimpleNamespace(version="controlled failure fixture", executable="fixture")

        def simulate(self, spec, candidate):
            raise SimulationError("nonzero_exit", "controlled sweep failure")

    root = tk.Tk()
    root.withdraw()
    try:
        app = DesktopApp(root, output_root=tmp_path)
        with monkeypatch.context() as fixture:
            fixture.setattr(model, "Ngspice", lambda _: FailingSimulator())
            app.run_button.invoke()
            wait_for_run(root, app)

        failed = app.output
        assert app.result.status == "simulation_failed" and app.result.waveform is None
        assert (failed / "report.json").is_file() and (failed / "bundle.zip").is_file()
        assert not (failed / "response.csv").exists() and not (failed / "response.png").exists()
        assert "diagnostic JSON / ZIP" in app.saved.get()
        assert "CSV" not in app.saved.get() and "PNG" not in app.saved.get()
        assert str(app.open_button.cget("state")) == "normal"
        assert str(app.run_button.cget("state")) == "normal"

        app.run_button.invoke()
        wait_for_run(root, app)
        assert app.output != failed and (failed / "report.json").is_file()
        assert app.result.status == "passed" and app.result.simulator_calls == 1
        assert audit_design(app.output, app.result.request) == app.result
        assert "JSON / CSV / PNG / ZIP" in app.saved.get()
    finally:
        root.destroy()
