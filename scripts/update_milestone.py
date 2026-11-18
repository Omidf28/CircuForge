"""Record the verified 2026-11-18 milestone in canonical plan inputs."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / "planning/phase-tasks.json"
data = json.loads(path.read_text(encoding="utf-8"))
evidence = {
    "P0-C1": "Installable package built and installed locally; pytest unit tests pass; missing simulator preflight tested. See docs/DEVELOPMENT.md.",
    "P0-C2": "ngspice-47 console exit 0; 601 real AC rows; evidence/lowpass-2026-11-18/{stdout.log,response.csv,report.json}.",
    "P1-C1": "Pydantic SI schemas, low/high-pass types, continuous-value policy, explicit ideal source/load, bounds/infeasibility/injection tests; examples/*.json.",
    "P1-C2": "Real ngspice integration plus timeout, output-limit, absent binary, launch and nonzero-exit tests; no arbitrary-netlist interface; startup files disabled.",
    "P1-C3": "Eight real R/C/topology/amplitude fixtures compare complex response and phase to independent formula; cutoff error <0.1%; evidence low/high-pass reports.",
}
for phase in data["phases"]:
    for task in phase["tasks"]:
        if task["id"] in evidence:
            task.update(status="done", evidence=evidence[task["id"]])
path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
path = root / "planning/context.json"
context = json.loads(path.read_text(encoding="utf-8"))
context["purpose"] = "Phase 1 local numerical implementation verified on Windows with ngspice-47. Canonical task statuses carry evidence; human reviews and later phases remain open. See planning/HANDOFF.md."
context["handoff"] = "Read AGENTS.md and planning/HANDOFF.md. P0-C1/C2 and P1-C1/C2/C3 have verified evidence. Reproduce tests and complete human P0-H1/H2 and P1-H1 reviews before Phase 2 baseline comparisons. First-slice bounded measured bisection is implemented; random/grid/SciPy remain Phase 2. Do not start PCB or LLM work."
path.write_text(json.dumps(context, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
# Seed browser status from canonical tasks, while preserving browser overrides.
path = root / "planning/roadmap.template.html"
text = path.read_text(encoding="utf-8")
old = "const saved=()=>"
seed = "for(const t of tasks){S.tasks[t.id]={status:t.status,note:t.evidence||'',...(S.tasks[t.id]||{})}};"
if seed not in text:
    text = text.replace(old, seed + old)
path.write_text(text, encoding="utf-8")
