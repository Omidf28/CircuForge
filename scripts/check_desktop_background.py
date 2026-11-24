"""Exercise our own withdrawn Tk widgets without OS input or a visible window.

Plots are measured scientific figures, never presented as window screenshots.
The existing independent raw-design auditor checks every simulator result.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

from circuforge.desktop.model import FormValues
from circuforge.evaluation.design_acceptance import audit_design
from circuforge.evaluation.records import environment

CASES = (("lowpass", FormValues(), "passed"),
         ("highpass", FormValues(topology="High-pass"), "passed"),
         ("target-miss", FormValues(topology="High-pass", mode="Simulate R/C"), "target_missed"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hidden(root):
    if root.state() != "withdrawn" or root.winfo_ismapped():
        raise RuntimeError("Test window must remain withdrawn for the entire check")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ngspice", required=True)
    parser.add_argument("--only-lowpass", action="store_true")
    parser.add_argument("--require-installed", action="store_true")
    args = parser.parse_args(argv)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    decision = dict(status="blocked", policy="desktop-withdrawn-controls-v1", os_input_used=False,
                    window_mapped=False, screenshots_created=False, visual_qa=False, model_requests=0)
    root = None
    try:
        import tkinter as tk
        import circuforge.desktop.app as desktop

        module = Path(desktop.__file__).resolve()
        prefix = Path(sys.prefix).resolve()
        if args.require_installed and not module.is_relative_to(prefix):
            raise RuntimeError("Installed check imported the source checkout")
        root = tk.Tk()
        root.withdraw()  # Before any update/event loop; never deiconify or send OS input.
        app = desktop.DesktopApp(root, output_root=output / "runs", executable=args.ngspice)
        hidden(root)
        rows = []
        selected = CASES[:1] if args.only_lowpass else CASES
        for index, (name, values, expected) in enumerate(selected):
            for field in values.__dataclass_fields__:
                app.variables[field].set(getattr(values, field))
            stale_notice = index == 0 or app.status.get().startswith("Settings changed")
            if not stale_notice:
                raise RuntimeError("Edited inputs lost the previous-result notice")
            app.run_button.invoke()
            if not app.controller.busy or str(app.run_button.cget("state")) != "disabled":
                raise RuntimeError("Background work did not disable duplicate submissions")
            if any(str(widget.cget("state")) != "disabled" for widget, _ in app.controls):
                raise RuntimeError("Inputs remained editable during a run")
            app.run_button.invoke()  # Disabled: must not allocate another run.
            deadline = time.monotonic() + 30
            while app.controller.busy and time.monotonic() < deadline:
                root.update()
                hidden(root)
                time.sleep(.01)
            if app.controller.busy or app.result is None:
                raise RuntimeError("Background UI run failed or did not finish: " + app.details.get())
            result = audit_design(app.output, app.result.request)
            if result != app.result or result.status != expected or result.simulator_calls != 1:
                raise RuntimeError("Displayed result differs from independently audited physics")
            expected_title = "TARGET MISSED" if expected == "target_missed" else "PASSED"
            if not app.status.get().startswith(expected_title):
                raise RuntimeError("UI status differs from the saved measured result")
            metrics = {key: variable.get() for key, variable in app.metrics.items()}
            if (metrics["cutoff"] != f"{result.best.measured_cutoff_hz:,.5g} Hz" or
                    metrics["error"] != f"{result.best.relative_error * 100:.5g}%" or metrics["calls"] != "1"):
                raise RuntimeError("Displayed numeric values differ from raw-audited results")
            hidden(root)
            figure = output / f"{name}-response.png"
            app.figure.savefig(figure, dpi=120)
            rows.append(dict(name=name, run=app.output.relative_to(output).as_posix(),
                             topology=result.request.spec.filter_type, method=result.request.method,
                             status=app.status.get(), result_status=result.status, metrics=metrics,
                             busy_inputs_disabled=True, stale_notice=stale_notice,
                             open_folder_enabled=str(app.open_button.cget("state")) == "normal",
                             window_state=root.state(), mapped=bool(root.winfo_ismapped()),
                             report_sha256=digest(app.output / "report.json"),
                             plot=figure.name, plot_sha256=digest(figure)))
            print(f"{name}: {result.status}, one actual raw-audited call; window withdrawn", flush=True)
        count = len(list((output / "runs").iterdir()))
        app.variables["target_hz"].set("invalid")
        app.run_button.invoke()
        root.update()
        hidden(root)
        if (app.controller.busy or app.status.get() != "Check your inputs" or
                len(list((output / "runs").iterdir())) != count or "last saved run" not in app.details.get()):
            raise RuntimeError("Invalid input started a job or lost the previous-result label")
        decision.update(status="passed", environment=environment(), installed_module=str(module), prefix=str(prefix),
                        require_installed=args.require_installed, cases=rows, actual_calls=len(rows),
                        invalid_input_rejected=True, invalid_input_run_count=count,
                        ui_state_verification="withdrawn Tk widgets and independently audited saved results; no native input/pixel inspection")
    except Exception as exc:
        decision["error"] = str(exc)
        print("Withdrawn desktop check blocked: " + str(exc), flush=True)
    finally:
        if root is not None:
            root.destroy()
    (output / "background.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    return 0 if decision["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
