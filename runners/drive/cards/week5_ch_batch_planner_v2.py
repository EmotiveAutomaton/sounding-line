"""CH1 planner adapter admitting exact original and cooperative engine batches.

DESIGN CHECK: LESSONS 3-5. A terminal marker without complete native replay is
not usable. No missing/gapped/overlapping interval may reach whole-roster use.
"""
from pathlib import Path
import json
from . import week5_ch_batch_planner as original
from .week5_ch_collection import verified_spec
from .week5_ch_source import digest, write_json

segments = original.segments
node_texture_roster = original.node_texture_roster
MODULE = 'runners.drive.cards.week5_ch_engine_bounded'


def authenticated_batch(completion):
    file = verified_spec(completion)
    root = file.parent
    receipt = json.loads(file.read_text(encoding='utf8'))
    if receipt.get('status') != 'COMPLETE' or not receipt.get('fresh_process_verified'):
        raise ValueError('Batch lacks complete native replay')
    outputs = receipt['outputs']
    if outputs.get('PLAN.json') != digest(root/'PLAN.json'):
        raise ValueError('Completed plan binding changed')
    plan = json.loads((root/'PLAN.json').read_text(encoding='utf8'))
    if plan['module'] != MODULE:
        return original.authenticated_batch(completion)
    names = sorted(n for n in outputs if n.startswith('output/PRIVATE_SCORES/') and n.endswith('.json'))
    needed = ['output/BATCH.json', 'output/VERIFY.json', 'output/BINDING.json']
    for name in needed + names:
        if name not in outputs or digest(root/name) != outputs[name]:
            raise ValueError('Completed batch binding changed')
    report = json.loads((root/'output/BATCH.json').read_text(encoding='utf8'))
    proof = json.loads((root/'output/VERIFY.json').read_text(encoding='utf8'))
    binding = json.loads((root/'output/BINDING.json').read_text(encoding='utf8'))
    semantic = {k:v for k,v in plan['config'].items() if k != 'max_new_draws'}
    if binding['inputs'] != plan['inputs'] or binding['config'] != semantic:
        raise ValueError('Batch binding does not match plan')
    if not proof.get('all_scores_equal') or not proof.get('fresh_from_ordinal_zero') or proof['verified_positions'] != len(names):
        raise ValueError('Replay denominator mismatch')
    offset = plan['config'].get('offset', 0)
    if (report['visited_positions'] != len(names) or not names or
            report['next_offset'] != offset + len(names) or
            len(names) > plan['config'].get('max_positions', 1024)):
        raise ValueError('Batch interval mismatch')
    actual = {p.name for p in (root/'output/PRIVATE_SCORES').iterdir() if p.is_file()}
    if actual != {Path(n).name for n in names}:
        raise ValueError('Unbound score file')
    return root, plan, report, {Path(n).name:outputs[n] for n in names}


def continuation(segment, completions):
    intervals = []
    for complete in completions:
        _, plan, report, _ = authenticated_batch(complete)
        if plan['inputs']['positions'] != segment['roster'] or report['node_limit'] != segment['node_limit']:
            raise ValueError('Batch belongs to different roster or node limit')
        begin = plan['config'].get('offset', 0)
        end = report['next_offset']
        if begin < segment['begin'] or end > segment['end'] or end <= begin:
            raise ValueError('Batch outside segment or made no progress')
        intervals.append((begin, end))
    offset = segment['begin']
    for begin, end in sorted(intervals):
        if begin != offset:
            raise ValueError('Overlapping or gapped batch continuation')
        offset = end
    if offset == segment['end']:
        return dict(segment_complete=True, next_offset=offset)
    return dict(segment_complete=False, next_offset=offset,
                config=dict(offset=offset, max_positions=segment['end']-offset,
                            nodes=segment['node_limit'], wall_seconds=600))


def collection_manifest(completions, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    batches = []
    for i, complete in enumerate(completions):
        root, _, _, bindings = authenticated_batch(complete)
        path = output/f'SCORE_BINDINGS_{i:06}.json'
        write_json(path, bindings)
        def spec(p): return dict(path=str(p), sha256=digest(p))
        batches.append(dict(path=str(root/'output/PRIVATE_SCORES'),
                            verify=spec(root/'output/VERIFY.json'), report=spec(root/'output/BATCH.json'),
                            score_bindings=spec(path), native_complete=complete))
    write_json(output/'BATCHES.json', dict(batches=batches, population_complete=False))
    return len(batches)
