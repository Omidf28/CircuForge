"""Render the planning documents. This does not build or deploy the product."""
from pathlib import Path
import argparse
import csv
import json

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output-dir', type=Path, help='generated project root; defaults to source project root')
args = parser.parse_args()
OUTPUT = args.output_dir.resolve() if args.output_dir else ROOT.parent
PLAN_OUTPUT = OUTPUT / 'planning'
data = json.loads((ROOT / 'context.json').read_text(encoding='utf-8-sig'))
data.update(json.loads((ROOT / 'phase-tasks.json').read_text(encoding='utf-8-sig')))
data['assembledDate'] = data['date']
tasks = [task for phase in data['phases'] for task in phase['tasks']]
ids = {task['id'] for task in tasks}
assert len(ids) == len(tasks), 'Duplicate task ID'
assert all(dep in ids for task in tasks for dep in task['dependsOn']), 'Unknown task dependency'
assert all(task['status'] in {'todo', 'doing', 'blocked', 'review', 'done', 'deferred'} for task in tasks), 'Invalid task status'
assert all(task.get('evidence') for task in tasks if task['status'] == 'done'), 'Completed tasks require evidence'
assert all(p.get('gateStatus', 'pending') in {'pending', 'blocked', 'passed'} for p in data['phases']), 'Invalid phase gate status'
assert all(p.get('gateEvidence') for p in data['phases'] if p.get('gateStatus') == 'passed'), 'Passed gates require evidence'
seen, visiting = set(), set()
by_id = {task['id']: task for task in tasks}
def visit(task_id):
    assert task_id not in visiting, f'Dependency cycle: {task_id}'
    if task_id in seen:
        return
    visiting.add(task_id)
    for dep in by_id[task_id]['dependsOn']:
        visit(dep)
    visiting.remove(task_id)
    seen.add(task_id)
for task_id in ids:
    visit(task_id)

plan_json = json.dumps(data, indent=2, ensure_ascii=False)
PLAN_OUTPUT.mkdir(parents=True, exist_ok=True)
(PLAN_OUTPUT / 'roadmap.json').write_text(plan_json + '\n', encoding='utf-8')
template = (ROOT / 'roadmap.template.html').read_text(encoding='utf-8')
html = template.replace('__PLAN_DATA__', plan_json.replace('<', '\\u003c'))
(OUTPUT / 'CircuForge-Roadmap.html').write_text(html, encoding='utf-8')

sources = {s['id']: s for s in data['sources']}
def refs(items):
    return ' '.join(f"[{sources[s]['title']}]({sources[s]['url']})" for s in items)
lines = [f"# {data['title']}", '',
    f"Version {data['version']} · assembled {data['date']} · architecture assumptions to verify in current environment", '',
    data['purpose'], '', '**Unconfirmed premise:** ' + data['premise'], '',
    '## Destination and scope', '', data['vision'], '', data['target'], '', data['schedule'], '',
    'The estimates are active-work planning assumptions, not model runtime or billing estimates. Current task statuses and evidence follow. Phase dates are relative to kickoff.', '',
    '### Launch scope', '']
lines += ['- ' + item for item in data['scope']['now']]
lines += ['', '### Deferred scope', ''] + ['- ' + item for item in data['scope']['later']]
lines += ['', '## First 48 hours', '']
for item in data['first48']:
    lines += [f"### {item['owner']}: {item['title']}", '', item['body'], '']
lines += ['## Intended user journey', '']
for item in data['journey']:
    lines += [f"### {item['step']}. {item['title']}", '', item['body'], '']
lines += ['## Phase workflow', '',
    'Critical path: P0 → P1 → P2 → P3 → P4 → P5 → P6 → P7. P8 is optional after validated research MVP.', '',
    'Technical phase gates use tested automatic acceptance under the owner delegation recorded in AGENTS.md. A status change alone does not prove completion. Explicit owner approvals for spending, remote publishing and other restricted operations remain separate. Deferred work needs a recorded reason; critical correctness, isolation and data-loss failures must be resolved.', '']
for phase in data['phases']:
    lines += [f"### {phase['id']}: {phase['title']}", '',
              f"**Window:** {phase['window']} · {'Optional after launch' if phase['optional'] else 'Launch path'}", '',
              '**Outcome:** ' + phase['outcome'], '',
              '**Phase dependencies:** ' + (', '.join(phase['dependsOn']) or 'None'), '',
              '**Exit gate:** ' + phase['gate'], '',
              '**Gate status:** ' + phase.get('gateStatus', 'pending'), '',
              '**Gate evidence:** ' + phase.get('gateEvidence', 'Not recorded'), '']
    for task in phase['tasks']:
        lines += [f"#### {task['id']} · {task['owner']} · {task['title']}", '',
                  f"Status: {task['status']} · Estimate: {task['effort']} active hours" + (' · Optional' if task.get('optional') else ''), '',
                  '**Action:** ' + task['action'], '',
                  '**Deliverable:** ' + task['deliverable'], '',
                  '**Acceptance:** ' + task['acceptance'], '',
                  '**Depends on:** ' + (', '.join(task['dependsOn']) or 'None'), '',
                  '**Evidence:** ' + task.get('evidence', 'Not recorded'), '']
for heading, key in [('Proposed architecture', 'architecture'), ('Intelligence and fine-tuning decisions', 'intelligence'), ('Distinctive techniques', 'techniques')]:
    lines += ['## ' + heading, '']
    for item in data[key]:
        lines += ['### ' + item['title'], '']
        if item.get('verdict') or item.get('timing'):
            lines += [item.get('verdict', item.get('timing')), '']
        lines += [item['body'] + (' ' + refs(item['sources']) if item.get('sources') else ''), '']
lines += ['## Provider choices and constraints', '']
for item in data['providers']:
    lines += ['### ' + item['name'], '', item['recommendation'], '', item['detail'] + ' ' + refs(item['sources']), '']
lines += ['## Capacity and budget assumptions', '']
c = data['capacity']
lines += ['- '+data['target'], '- '+c['budget'], '', '## Validation gates', '', 'All targets below are proposed. Only tested artifacts count as evidence.', '']
for item in data['launchGates']:
    lines += ['### ' + item['name'], '', item['target'], '']
lines += ['## Human / Codex working agreement', '']
for item in data['workflow']:
    lines += ['### ' + item['title'], '', item['body'], '']
lines += ['## Where the plan should live', '', data['planningHome'] + ' ' + refs(['githubprojects']), '',
          'Use task IDs as issue titles. Fields: phase, owner, status, dependency IDs, estimate, deliverable, acceptance and evidence link. The issues.csv is an exchange table; GitHub Projects does not provide a guaranteed native one-click CSV import.', '',
          'The HTML stores progress only in the browser. Export JSON to share statuses and evidence. Export an HTML snapshot for a self-contained visual copy. Git commits or a shared issue tracker reconcile changes; this file is not a multi-user database.', '',
          '## Agent handoff prompt', '', '```text', data['handoff'], '```', '',
          '## Sources', '', 'Reference links aid implementation; verify current versions and local environment before making claims. Goals are engineering assumptions, not validated results.', '']
lines += [f"- [{s['title']}]({s['url']})" for s in data['sources']]
(PLAN_OUTPUT / 'roadmap.md').write_text('\n'.join(line.rstrip() for line in lines) + '\n', encoding='utf-8')
with (PLAN_OUTPUT / 'issues.csv').open('w', encoding='utf-8-sig', newline='') as handle:
    fields = ['id','phase','owner','title','status','estimate_hours','depends_on','deliverable','acceptance','action','optional','evidence']
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    for phase in data['phases']:
        for t in phase['tasks']:
            writer.writerow(dict(id=t['id'],phase=phase['id'],owner=t['owner'],title=t['title'],status=t['status'],estimate_hours=t['effort'],depends_on='; '.join(t['dependsOn']),deliverable=t['deliverable'],acceptance=t['acceptance'],action=t['action'],optional=phase['optional'] or t.get('optional',False),evidence=t.get('evidence', '')))
print(f'Rendered roadmap HTML, Markdown, JSON and CSV: {len(data["phases"])} phases, {len(tasks)} tasks. Dependencies validated.')
