"""Optional Tk desktop for the existing measured RC design use case."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import os
from pathlib import Path
import subprocess
import sys
try:
    import tkinter as tk
    from tkinter import filedialog, ttk
except ImportError:
    tk = None

from pydantic import ValidationError

from circuforge import __version__
from circuforge.desktop.model import FormValues, MODES, TOPOLOGIES, RunController, build_request

BG, INK, MUTED, TEAL = "#f1f5f9", "#172b42", "#586b80", "#087f79"


class DesktopApp:
    def __init__(self, root: tk.Tk, *, output_root: Path, executable: str | None = None):
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from matplotlib.figure import Figure

        self.root, self.controller = root, RunController()
        self.closing, self.output, self.result = False, None, None
        self.variables = {name: tk.StringVar(root, value=value) for name, value in asdict(FormValues()).items()}
        self.output_root = tk.StringVar(root, value=str(output_root.expanduser().resolve()))
        self.executable = tk.StringVar(root, value=executable or "")
        self.controls = []
        self.status = tk.StringVar(root, value="Ready to design")
        self.details = tk.StringVar(root, value="Choose a target and component bounds, then run a measured design.")
        self.saved = tk.StringVar(root, value="Results will be saved as JSON, CSV, PNG and ZIP.")
        self.root.title("CircuForge — Local RC Studio")
        self.root.configure(bg=BG)
        self.root.geometry(f"{min(1280, root.winfo_screenwidth() - 80)}x{min(900, root.winfo_screenheight() - 100)}")
        self.root.minsize(1040, 760)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self._styles()
        header = tk.Frame(root, bg=INK, height=78)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="CircuForge", bg=INK, fg="white", font=("Segoe UI", 23, "bold")).pack(side="left", padx=(25, 14))
        tk.Label(header, text="LOCAL RC STUDIO", bg=INK, fg="#b8d5e7", font=("Segoe UI", 10)).pack(side="left")
        tk.Label(header, text=f"Research edition  ·  {__version__}", bg=INK, fg="#b8d5e7", font=("Segoe UI", 10)).pack(side="right", padx=25)
        body = tk.Frame(root, bg=BG)
        body.pack(fill="both", expand=True, padx=20, pady=18)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)
        left = tk.Frame(body, bg="white", padx=18, pady=15, width=330)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        left.columnconfigure(0, weight=1)
        right = tk.Frame(body, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(3, weight=1)
        self._form(left)
        self.badge = tk.Label(right, textvariable=self.status, bg="#e1edf5", fg=INK,
                              font=("Segoe UI", 12, "bold"), anchor="w", padx=14, pady=10)
        self.badge.grid(row=0, column=0, sticky="ew")
        tk.Label(right, textvariable=self.details, bg=BG, fg=MUTED, justify="left", anchor="w",
                 wraplength=740, font=("Segoe UI", 10)).grid(row=1, column=0, sticky="ew", pady=(8, 12))
        metrics = tk.Frame(right, bg=BG)
        metrics.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        self.metrics = {}
        for index, (key, title) in enumerate((("cutoff", "MEASURED CUTOFF"), ("error", "ERROR VS TARGET"), ("calls", "SIMULATOR CALLS"))):
            metrics.columnconfigure(index, weight=1)
            card = tk.Frame(metrics, bg="white", padx=13, pady=10)
            card.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 8, 0))
            tk.Label(card, text=title, bg="white", fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w")
            value = tk.StringVar(root, value="—")
            tk.Label(card, textvariable=value, bg="white", fg=INK, font=("Segoe UI", 19, "bold")).pack(anchor="w", pady=(3, 0))
            self.metrics[key] = value
        chart = tk.Frame(right, bg="white")
        chart.grid(row=3, column=0, sticky="nsew")
        self.figure = Figure(figsize=(7.2, 5), dpi=100, facecolor="white", layout="constrained")
        self.axes = self.figure.subplots(2, 1, sharex=True)
        self.canvas = FigureCanvasTkAgg(self.figure, master=chart)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self._empty_plot()
        foot = tk.Frame(right, bg=BG)
        foot.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        foot.columnconfigure(0, weight=1)
        tk.Label(foot, textvariable=self.saved, bg=BG, fg=MUTED, font=("Segoe UI", 9),
                 anchor="w", justify="left", wraplength=590).grid(row=0, column=0, sticky="ew")
        self.open_button = ttk.Button(foot, text="Open results folder", command=self.open_results, state="disabled")
        self.open_button.grid(row=0, column=1, padx=(10, 0))
        for variable in (*self.variables.values(), self.output_root, self.executable):
            variable.trace_add("write", self._changed)
        self.root.after(80, self._poll)

    def _styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TLabel", background="white", foreground=INK, font=("Segoe UI", 10))
        style.configure("TEntry", padding=5, font=("Segoe UI", 10))
        style.configure("TCombobox", padding=4, font=("Segoe UI", 10))
        style.configure("TButton", padding=(10, 7), font=("Segoe UI", 10))
        style.configure("Run.TButton", background=TEAL, foreground="white", font=("Segoe UI", 11, "bold"), padding=(12, 11))
        style.map("Run.TButton", background=[("disabled", "#96b7b5"), ("active", "#056d68")])

    def _entry(self, frame, key, label, row, column=0):
        ttk.Label(frame, text=label).grid(row=row, column=column, sticky="w", pady=(5, 3))
        entry = ttk.Entry(frame, textvariable=self.variables[key], width=13)
        entry.grid(row=row + 1, column=column, sticky="ew", padx=(0, 7) if column == 0 else (0, 0))
        self.controls.append((entry, "normal"))
        return entry

    def _form(self, left):
        ttk.Label(left, text="Design a filter", font=("Segoe UI", 16, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 8))
        choices = tk.Frame(left, bg="white")
        choices.grid(row=1, column=0, sticky="ew")
        choices.columnconfigure((0, 1), weight=1)
        for column, (key, title, values) in enumerate((("topology", "Filter", tuple(TOPOLOGIES)), ("mode", "Mode", MODES))):
            ttk.Label(choices, text=title).grid(row=0, column=column, sticky="w")
            control = ttk.Combobox(choices, textvariable=self.variables[key], values=values, state="readonly", width=17)
            control.grid(row=1, column=column, sticky="ew", pady=(3, 0), padx=(0, 7) if column == 0 else (0, 0))
            self.controls.append((control, "readonly"))
        target = tk.Frame(left, bg="white")
        target.grid(row=2, column=0, sticky="ew", pady=8)
        target.columnconfigure((0, 1), weight=1)
        self._entry(target, "target_hz", "Target cutoff · Hz", 0)
        self._entry(target, "tolerance_pct", "Allowed error · %", 0, 1)
        self.ranges = tk.Frame(left, bg="white")
        self.ranges.grid(row=3, column=0, sticky="ew")
        self.ranges.columnconfigure((0, 1), weight=1)
        self._entry(self.ranges, "r_min_ohm", "R min · Ω", 0)
        self._entry(self.ranges, "r_max_ohm", "R max · Ω", 0, 1)
        self._entry(self.ranges, "c_min_nf", "C min · nF", 2)
        self._entry(self.ranges, "c_max_nf", "C max · nF", 2, 1)
        self.components = tk.Frame(left, bg="white")
        self.components.columnconfigure((0, 1), weight=1)
        self._entry(self.components, "resistance_ohm", "Resistance · Ω", 0)
        self._entry(self.components, "capacitance_nf", "Capacitance · nF", 0, 1)
        tk.Label(left, text="Ideal zero-ohm source · infinite load\nContinuous, ideal R/C values", bg="white", fg=MUTED,
                 justify="left", font=("Segoe UI", 9)).grid(row=4, column=0, sticky="w", pady=(12, 6))
        self.diagram = tk.Canvas(left, width=295, height=125, bg="#f4f8fb", highlightthickness=0)
        self.diagram.grid(row=5, column=0, sticky="ew", pady=(5, 10))
        self._diagram()
        storage = tk.Frame(left, bg="white")
        storage.grid(row=6, column=0, sticky="ew")
        storage.columnconfigure(0, weight=1)
        ttk.Label(storage, text="Save results in").grid(row=0, column=0, sticky="w")
        entry = ttk.Entry(storage, textvariable=self.output_root, width=26)
        entry.grid(row=1, column=0, sticky="ew", pady=3)
        browse = ttk.Button(storage, text="Browse…", command=self._browse_output)
        browse.grid(row=1, column=1, padx=(5, 0))
        self.controls.extend(((entry, "normal"), (browse, "normal")))
        ttk.Label(storage, text="ngspice executable · optional").grid(row=2, column=0, columnspan=2, sticky="w", pady=(7, 0))
        spice = ttk.Entry(storage, textvariable=self.executable, width=26)
        spice.grid(row=3, column=0, sticky="ew", pady=3)
        choose = ttk.Button(storage, text="Choose…", command=self._browse_executable)
        choose.grid(row=3, column=1, padx=(5, 0))
        self.controls.extend(((spice, "normal"), (choose, "normal")))
        tk.Label(storage, text="Blank uses CIRCUFORGE_NGSPICE / PATH", bg="white", fg=MUTED,
                 font=("Segoe UI", 8)).grid(row=4, column=0, columnspan=2, sticky="w")
        self.run_button = ttk.Button(left, text="Run measured design", style="Run.TButton", command=self.run)
        self.run_button.grid(row=7, column=0, sticky="ew", pady=(14, 5))
        self.progress = ttk.Progressbar(left, mode="indeterminate")
        self.progress.grid(row=8, column=0, sticky="ew", pady=(3, 0))
        left.rowconfigure(9, weight=1)

    def _diagram(self, candidate=None):
        canvas = self.diagram
        canvas.delete("all")
        color = INK
        low = self.variables["topology"].get() == "Low-pass"
        if candidate is not None:
            low = candidate.topology == "rc_lowpass"
        canvas.create_text(17, 26, text="IN", fill=MUTED, anchor="w", font=("Segoe UI", 8, "bold"))
        canvas.create_text(254, 26, text="OUT", fill=MUTED, anchor="w", font=("Segoe UI", 8, "bold"))
        canvas.create_line(20, 51, 78, 51, fill=color, width=2)
        if low:
            canvas.create_line(78, 51, 84, 43, 94, 59, 104, 43, 114, 59, 124, 43, 134, 59, 140, 51, fill=color, width=2)
        else:
            canvas.create_line(78, 51, 104, 51, fill=color, width=2)
            canvas.create_line(104, 38, 104, 64, fill=color, width=2)
            canvas.create_line(114, 38, 114, 64, fill=color, width=2)
            canvas.create_line(114, 51, 140, 51, fill=color, width=2)
        canvas.create_line(140, 51, 275, 51, fill=color, width=2)
        canvas.create_oval(216, 48, 222, 54, fill=TEAL, outline=TEAL)
        if low:
            canvas.create_line(219, 51, 219, 74, fill=color, width=2)
            canvas.create_line(206, 74, 232, 74, fill=color, width=2)
            canvas.create_line(206, 82, 232, 82, fill=color, width=2)
            canvas.create_line(219, 82, 219, 104, fill=color, width=2)
        else:
            canvas.create_line(219, 51, 219, 64, 212, 69, 226, 75, 212, 81, 226, 87, 219, 92, 219, 104, fill=color, width=2)
        for y, span in ((104, 14), (109, 9), (114, 4)):
            canvas.create_line(219 - span, y, 219 + span, y, fill=color, width=2)
        r = f"{candidate.resistance_ohm:.5g} Ω" if candidate else "R"
        c = f"{candidate.capacitance_f * 1e9:.5g} nF" if candidate else "C"
        canvas.create_text(109, 25, text=r if low else c, fill=TEAL, font=("Segoe UI", 9, "bold"))
        canvas.create_text(150, 84, text=c if low else r, fill=TEAL, font=("Segoe UI", 9, "bold"))

    def _empty_plot(self):
        for axis, label in zip(self.axes, ("Gain · dB", "Phase · degrees")):
            axis.clear()
            axis.set_xscale("log")
            axis.set_xlim(10, 1e5)
            axis.set_ylabel(label, color=MUTED)
            axis.grid(True, which="both", alpha=.12)
            axis.spines[["top", "right"]].set_visible(False)
        self.axes[0].text(.5, .5, "Your measured frequency response appears here", transform=self.axes[0].transAxes,
                          ha="center", va="center", color=MUTED, fontsize=11)
        self.axes[1].set_xlabel("Frequency · Hz", color=MUTED)
        self.canvas.draw_idle()

    def _changed(self, *args):
        manual = self.variables["mode"].get() == "Simulate R/C"
        (self.ranges if manual else self.components).grid_remove()
        (self.components if manual else self.ranges).grid(row=3, column=0, sticky="ew")
        if not self.controller.busy:
            self._diagram()
            if self.result is not None:
                self.status.set("Settings changed — run to update")
                self.badge.configure(bg="#fff1d6", fg="#885400")
                self.details.set("The chart and metrics below belong to the last saved run, not the edited settings.")
                self._diagram(self.result.best.candidate if self.result.best else None)

    def _browse_output(self):
        value = filedialog.askdirectory(parent=self.root, title="Choose a results directory")
        if value:
            self.output_root.set(value)

    def _browse_executable(self):
        value = filedialog.askopenfilename(parent=self.root, title="Choose the ngspice console executable",
                                            filetypes=(("Executable", "*.exe"), ("All files", "*")))
        if value:
            self.executable.set(value)

    def _enable(self, enabled):
        for widget, normal in self.controls:
            widget.configure(state=normal if enabled else "disabled")
        self.run_button.configure(state="normal" if enabled else "disabled")

    def run(self):
        if self.controller.busy:
            return
        try:
            request = build_request(FormValues(**{key: variable.get() for key, variable in self.variables.items()}))
            if not self.output_root.get().strip():
                raise ValueError("Choose a directory in which to save results")
            output = self.controller.start(request, Path(self.output_root.get()), self.executable.get().strip() or None)
        except (ValueError, OSError, RuntimeError) as exc:
            if isinstance(exc, ValidationError):
                message = "; ".join(error["msg"].removeprefix("Value error, ") for error in exc.errors(include_url=False))
            else:
                message = str(exc)
            if self.result is not None:
                message += "\nChart and metrics belong to the last saved run."
            self.status.set("Check your inputs")
            self.details.set(message)
            self.badge.configure(bg="#fff1d6", fg="#885400")
            return
        self.result, self.output = None, output
        self.open_button.configure(state="disabled")
        for variable in self.metrics.values():
            variable.set("—")
        self._empty_plot()
        self._diagram()
        self.status.set("Running ngspice…")
        self.badge.configure(bg="#e1edf5", fg=INK)
        self.details.set("Measuring the AC response and checking the cutoff against the target and ideal RC reference.")
        self.saved.set(f"Saving a new run in {output}")
        self._enable(False)
        self.progress.start(12)

    def _poll(self):
        event = self.controller.poll()
        if event is not None:
            self.progress.stop()
            if self.closing:
                self.root.destroy()
                return
            self._enable(True)
            self.output, self.result = event.output, event.result
            if event.error:
                self.status.set("Run could not complete")
                self.details.set(event.error)
                self.badge.configure(bg="#fee8e7", fg="#a83229")
                self.saved.set(f"Partial output: {event.output}" if event.output.exists() else "No result was produced. Check ngspice and the output directory.")
            else:
                self._show_result(event.result)
                self.saved.set(f"Saved JSON / CSV / PNG / ZIP\n{event.output}")
            self.open_button.configure(state="normal" if event.output.is_dir() else "disabled")
        self.root.after(80, self._poll)

    def _show_result(self, result):
        labels = {"passed": ("PASSED — measured target met", "#ddf3ec", "#08705c"),
                  "target_missed": ("TARGET MISSED — measurement completed", "#fff1d6", "#885400"),
                  "simulation_failed": ("SIMULATION FAILED — no accepted result", "#fee8e7", "#a83229")}
        title, background, foreground = labels[result.status]
        self.status.set(title)
        self.badge.configure(bg=background, fg=foreground)
        self.metrics["calls"].set(str(result.simulator_calls))
        best = result.best
        if best is None:
            reasons = [entry.reason or entry.status for entry in result.history if not entry.verified]
            self.details.set("; ".join(reasons) or "No verified measurement is available.")
            return
        self.metrics["cutoff"].set(f"{best.measured_cutoff_hz:,.5g} Hz")
        self.metrics["error"].set(f"{best.relative_error * 100:.5g}%")
        spec = result.request.spec
        self.details.set(f"Target {spec.cutoff_hz:g} Hz  ·  Allowed error {spec.relative_error_tolerance * 100:g}%  ·  "
                         f"Independent RC reference checked: {'yes' if best.verified else 'no'}")
        self._diagram(best.candidate)
        waveform = result.waveform
        if waveform is None:
            return
        for axis, samples, label in zip(self.axes, (waveform.gain_db, waveform.phase_deg), ("Gain · dB", "Phase · degrees")):
            axis.clear()
            axis.semilogx(waveform.frequency_hz, samples, color=TEAL, linewidth=1.8, label="Measured ngspice")
            axis.axvline(spec.cutoff_hz, color="#64748b", linestyle=":", label="Target cutoff")
            axis.axvline(best.measured_cutoff_hz, color="#d28b22", linestyle="--", label="Measured cutoff")
            axis.set_ylabel(label, color=MUTED)
            axis.grid(True, which="both", alpha=.15)
            axis.spines[["top", "right"]].set_visible(False)
        self.axes[0].legend(fontsize=8, loc="best", frameon=False)
        self.axes[1].set_xlabel("Frequency · Hz", color=MUTED)
        self.canvas.draw_idle()

    def open_results(self):
        if self.output and self.output.is_dir():
            try:
                if os.name == "nt":
                    os.startfile(self.output)
                else:
                    subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", str(self.output)])
            except OSError as exc:
                self.details.set(f"Could not open the folder: {exc}. Saved results remain at {self.output}")

    def close(self):
        if self.controller.busy:
            self.closing = True
            self._enable(False)
            self.status.set("Finishing the current run before closing…")
        else:
            self.root.destroy()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ngspice", help="trusted ngspice console executable; otherwise environment/PATH")
    parser.add_argument("--output-root", type=Path, default=Path.home() / "CircuForge-Runs")
    args = parser.parse_args(argv)
    if tk is None:
        print("Desktop unavailable: install Python Tk support. The CLI remains usable.", file=sys.stderr)
        return 2
    root = None
    try:
        root = tk.Tk()
        DesktopApp(root, output_root=args.output_root, executable=args.ngspice)
    except (tk.TclError, ImportError) as exc:
        if root is not None:
            root.destroy()
        print(f"Desktop unavailable: {exc}. Install the gui extra and Python Tk support; the CLI remains usable.", file=sys.stderr)
        return 2
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
