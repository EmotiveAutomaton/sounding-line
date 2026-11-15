"""Week 6 predecessor and cumulative-card accounting boundaries.

DESIGN CHECK: LESSONS 3-5, read 2026-11-15. Under both scientific directions,
time alone never proves drain and a new campaign never resets a carried card.
Missing/changed evidence, an unexplained owner, duplicate budget revision or a
reduced cumulative preparation charge refuses admission. No automatic recovery.
"""
from pathlib import Path
from datetime import datetime, timezone
import math
import re
from .batch_runtime import REPO, read, filehash, check_files

PREDECESSOR = REPO/'results/phase_2_4_stage_15/raw/drive-week5-20261107'
DRAIN_REVIEW = REPO/'.agent-state/drive-20261115/PREDECESSOR_DRAIN_REVIEW.json'
EARLIEST = datetime.fromisoformat('2026-11-16T06:00:00+00:00')
EXPLICIT_CAPS = {'IN13': ('IN', 20000), 'IN14': ('IN', 20000),
                 'IN15': ('IN', 20000), 'IN16': ('IN', 20000),
                 'RW1': ('RW', 20000), 'TR2': ('MD', 60000), 'DC1': ('MD', 10000)}


def finite(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError('Invalid cumulative card accounting')
    return float(value)


def budgets(root):
    """Immutable revisions; preparation is cumulative, never summed twice."""
    directory = Path(root)/'_budgets'
    try:
        paths = list(directory.iterdir())
    except FileNotFoundError:
        return {}
    groups = {}
    for path in paths:
        if not path.is_file() or path.suffix != '.json' or path.is_symlink():
            raise ValueError('Unexpected budget registry member')
        row = read(path)
        key = row['key']
        if not re.fullmatch(r'[A-Za-z0-9_.-]+', key) or not row.get('owner_reviewed'):
            raise ValueError('Reviewed stable card budget identity required')
        if row.get('campaign') != 'S15-WEEK6':
            raise ValueError('Budget campaign differs')
        for field in ('ceiling_cpu_seconds', 'prior_campaign_cpu_seconds', 'preparation_cpu_seconds'):
            finite(row[field])
        if row['ceiling_cpu_seconds'] <= 0 or not row.get('evidence_pins'):
            raise ValueError('Positive original ceiling and accounting evidence required')
        if key in EXPLICIT_CAPS and (row['family'], row['ceiling_cpu_seconds']) != EXPLICIT_CAPS[key]:
            raise ValueError('Approved card ceiling/family differs')
        revision = row['revision']
        if type(revision) is not int or revision < 1:
            raise ValueError('Positive integer budget revision required')
        if path.name != f'{key}-r{revision:04d}.json':
            raise ValueError('Budget filename/identity differs')
        groups.setdefault(key, []).append((revision, path, row))
    result = {}
    for key, versions in groups.items():
        versions.sort(key=lambda value: value[0])
        previous = None
        for expected, (revision, path, row) in enumerate(versions, 1):
            if revision != expected:
                raise ValueError('Missing or repeated budget revision')
            if previous is None:
                if row.get('previous_sha256') is not None:
                    raise ValueError('First budget revision has a predecessor')
            else:
                prior_path, prior = previous
                if row.get('previous_sha256') != filehash(prior_path):
                    raise ValueError('Budget ancestry differs')
                for field in ('key', 'family', 'ceiling_cpu_seconds', 'prior_campaign_cpu_seconds'):
                    if row[field] != prior[field]:
                        raise ValueError('Original budget boundary changed: '+field)
                if row['preparation_cpu_seconds'] < prior['preparation_cpu_seconds']:
                    raise ValueError('Preparation charges cannot decrease')
                if any(row['evidence_pins'].get(p) != h for p, h in prior['evidence_pins'].items()):
                    raise ValueError('Prior accounting evidence dropped')
            check_files(row['evidence_pins'])
            previous = path, row
        result[key] = dict(versions[-1][2], receipt=str(versions[-1][1]), receipt_sha256=filehash(versions[-1][1]))
    return result


def plan_budget(plan, root):
    key = plan['budget_key']
    latest = budgets(root)[key]
    path = Path(plan['budget_receipt']).resolve()
    path.relative_to((Path(root)/'_budgets').resolve())
    if filehash(path) != plan['budget_receipt_sha256'] or plan['pins'].get(str(path)) != filehash(path):
        raise ValueError('Plan accounting receipt not pinned')
    bound = read(path)
    for field in ('key', 'family', 'ceiling_cpu_seconds', 'prior_campaign_cpu_seconds'):
        if bound[field] != latest[field]:
            raise ValueError('Plan and cumulative budget identity differ')
    if latest['family'] != plan['family']:
        raise ValueError('Card budget family differs')
    return latest


def predecessor_inventory(root=PREDECESSOR):
    """Only terminal evidence, never progress or an artifact's scientific scores."""
    inventory = {}
    for directory in Path(root).iterdir():
        if not directory.is_dir():
            continue
        if directory.is_symlink():
            raise ValueError('Unexpected predecessor directory link')
        path = directory/'PLAN.json'
        if not path.exists():
            continue
        plan = read(path)
        if plan.get('campaign') != 'S15-WEEK5':
            continue
        if not (directory/'ATTEMPT.claim').exists() and not (directory/'OWNER.json').exists():
            continue
        terminals = [n for n in ('COMPLETE.json', 'FAILED.json', 'PAUSED.json') if (directory/n).exists()]
        if len(terminals) != 1:
            raise RuntimeError('Predecessor attempt lacks one reconciled terminal: '+directory.name)
        owner = read(directory/'OWNER.json')
        if owner.get('plan_sha256') != filehash(path):
            raise ValueError('Predecessor owner binding differs')
        terminal = read(directory/terminals[0])
        finite(terminal['cpu_seconds'])
        inventory[directory.name] = {
            'pins': {n: filehash(directory/n) for n in ('PLAN.json', 'OWNER.json', terminals[0])},
            'native': owner['native'],
        }
    return inventory


def require_predecessor_drain(plan, at, lease_paths=()):
    if at.tzinfo is None or at < EARLIEST:
        raise RuntimeError('Before approved predecessor drain time')
    path = DRAIN_REVIEW.resolve()
    if plan['pins'].get(str(path)) != filehash(path):
        raise ValueError('Predecessor drain review must be pinned')
    proof = read(path)
    stamp = datetime.fromisoformat(proof['at'])
    if stamp.tzinfo is None or not EARLIEST <= stamp <= at:
        raise ValueError('Invalid actual drain inspection clock')
    if not (proof.get('owner_reviewed') and proof.get('all_native_exits_verified') and proof.get('full_write_through')):
        raise RuntimeError('Actual predecessor drain inspection and full filing required')
    if Path(proof['predecessor_root']).resolve() != PREDECESSOR.resolve():
        raise ValueError('Wrong predecessor campaign')
    actual = predecessor_inventory(PREDECESSOR)
    if not actual or proof['terminal_inventory'] != actual:
        raise ValueError('Predecessor terminal inventory changed or empty')
    if proof['exited_native_identities'] != {k: v['native'] for k, v in actual.items()}:
        raise ValueError('Every exact predecessor identity needs exit reconciliation')
    report = Path(proof['final_drain_receipt']).resolve()
    if filehash(report) != proof['final_drain_receipt_sha256'] or plan['pins'].get(str(report)) != filehash(report):
        raise ValueError('Filed drain receipt differs or is unpinned')
    filed = read(report)
    if not filed.get('full_write_through') or not filed.get('id', '').startswith('OPS-S15-W5-') or 'DRAIN' not in filed['id']:
        raise ValueError('A calendar notification is not a fully filed drain')
    for lease in lease_paths:
        value = read(lease)
        if value.get('attempt_root') and Path(value['attempt_root']).resolve().is_relative_to(PREDECESSOR.resolve()):
            raise RuntimeError('Predecessor still holds a counted lease')
    return proof
