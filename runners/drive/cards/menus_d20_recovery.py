"""D20's single lossless storage repair; original attempt and analysis immutable.

DESIGN CHECK: LESSONS 3-5 read October18. Under every scientific world this
adapter preserves all original checkpoint JSON bytes and calls the original
analysis unchanged. Changed sources, missing seals, changed configuration or
compressed-byte damage must fail, never become a scientific null. Both null
and planted serialized fixtures require original/recovery parity. The owner
charges the prior attempt against the original wall cap; no cap is enlarged.
"""
from collections import Counter
from datetime import datetime
from pathlib import Path
import gzip
import hashlib
import json
import math
import time
import numpy as np
from . import menus_d20 as original
from .menus_io import read, write, sha256, input_hashes, assert_equal, canonical

EXTRA_INPUTS = frozenset(('original_plan', 'original_failure', 'original_inventory'))


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def context(output, inputs, config):
    plan_path = Path(inputs['original_plan']).resolve()
    failure_path = Path(inputs['original_failure']).resolve()
    if failure_path != plan_path.parent / 'FAILED.json':
        raise ValueError('D20 failure does not belong to original plan')
    plan = read(plan_path); failure = read(failure_path)
    if plan.get('module') != 'runners.drive.cards.menus_d20' or plan.get('card') != 'D20':
        raise ValueError('D20 original module/card differs')
    if failure.get('status') != 'FAILED' or failure.get('error') != "RuntimeError('Frozen output byte cap exceeded')":
        raise ValueError('D20 recovery requires the retained byte-cap failure')
    if not failure.get('engineering_retry_available') or (plan_path.parent / 'COMPLETE.json').exists():
        raise ValueError('D20 original attempt is not eligible for recovery')
    scientific_inputs = {k:v for k,v in inputs.items() if k not in EXTRA_INPUTS}
    assert_equal(scientific_inputs, plan['inputs']); assert_equal(config, plan['config'])
    for name, expected in plan['pins'].items():
        if sha256(name) != expected:
            raise ValueError('D20 original source pin changed: '+name)
    for name in scientific_inputs.values():
        if plan['pins'].get(str(name)) != sha256(name):
            raise ValueError('D20 original input was not pinned')
    for module in (original,original.source):
        path=str(Path(module.__file__).resolve())
        if plan['pins'].get(path)!=sha256(path):raise ValueError('D20 original analysis/extractor not pinned')
    binding = dict(inputs=input_hashes(scientific_inputs), config=config)
    old_output = plan_path.parent / 'output'
    assert_equal(read(old_output/'BINDING.json'), binding)
    inventory = read(inputs['original_inventory'])
    assert_equal(inventory['original_plan_sha256'],sha256(plan_path))
    assert_equal(inventory['original_failure_sha256'],sha256(failure_path))
    if set(inventory['sessions'])!={s['session'] for s in read(scientific_inputs['sessions'])}:
        raise ValueError('D20 original inventory roster differs')
    charged = (datetime.fromisoformat(failure['at'])-datetime.fromisoformat(plan['at'])).total_seconds()
    if not 0 < charged < plan['max_wall_seconds']:
        raise ValueError('D20 prior elapsed charge is invalid or exhausted')
    outer = Path(output).parent/'PLAN.json'
    if outer.exists():
        retry = read(outer)
        if retry.get('module') == __name__:
            if retry['max_output_bytes'] != plan['max_output_bytes']:
                raise ValueError('D20 retry changed original byte cap')
            if retry['max_wall_seconds']+charged > plan['max_wall_seconds']+1e-9:
                raise ValueError('D20 retry does not charge prior elapsed time')
    return scientific_inputs, binding, old_output, dict(original_plan_sha256=sha256(plan_path),
        original_failure_sha256=sha256(failure_path), prior_elapsed_charged_seconds=charged,
        original_inventory_sha256=sha256(inputs['original_inventory']),
        original_max_wall_seconds=plan['max_wall_seconds'], max_output_bytes=plan['max_output_bytes'])


def compressed(path, raw):
    """Exclusive deterministic gzip write, then prove exact raw-byte recovery."""
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = gzip.compress(raw, compresslevel=6, mtime=0)
    with path.open('xb') as stream:
        stream.write(encoded)
    if gzip.decompress(path.read_bytes()) != raw:
        raise ValueError('D20 compressed JSON byte parity failed')
    return dict(sha256=sha256(path), raw_sha256=digest(raw), raw_bytes=len(raw), compressed_bytes=len(encoded))


def sealed_bytes(path):
    receipt = read(path.with_suffix('.seal.json'))
    if sha256(path) != receipt['sha256']:
        raise ValueError('changed D20 compressed checkpoint')
    raw = gzip.decompress(path.read_bytes())
    if digest(raw) != receipt['raw_sha256'] or len(raw) != receipt['raw_bytes']:
        raise ValueError('changed D20 decompressed checkpoint')
    return raw, receipt


def legacy_bytes(old_output, sid, binding, inventory):
    path = old_output/'sessions'/(sid+'.json'); seal = path.with_suffix('.seal.json')
    raw = path.read_bytes(); expected = read(seal)['sha256']
    if digest(raw) != expected:
        raise ValueError('changed original D20 session checkpoint')
    assert_equal(inventory['sessions'][sid],dict(sha256=expected,seal_sha256=sha256(seal),bytes=len(raw)))
    saved = json.loads(raw); assert_equal(saved['binding'], binding)
    return raw, dict(original_path=str(path), original_sha256=expected, original_seal_sha256=sha256(seal))


def validate_rows(data, sid, saved):
    expected, support, pins = original.source.session_rows(data, sid)
    actual = [{k:v for k,v in row.items() if k not in ('window_vector','visibility')} for row in saved['rows']]
    assert_equal(actual, expected); assert_equal(support, saved['support']); assert_equal(pins, saved['source_pins'])
    for row in saved['rows']:
        if row['handling']=='dismiss' and row['window'] is not None:
            vector = np.asarray(row['window_vector'])
            if vector.shape!=(384,) or not np.isfinite(vector).all() or not np.isclose(np.linalg.norm(vector),1,atol=1e-5):
                raise ValueError('invalid saved D20 window vector')


def execute(output, inputs, config):
    output=Path(output); output.mkdir(parents=True,exist_ok=True); started=time.perf_counter()
    scientific, binding, old, recovery = context(output, inputs, config)
    retry_binding=dict(inputs=input_hashes(inputs), config=config, recovery=recovery)
    if (output/'BINDING.json').exists(): assert_equal(read(output/'BINDING.json'),retry_binding)
    else: write(output/'BINDING.json',retry_binding)
    if (output/'SUMMARY.json').exists():
        verify(output,inputs,config); return read(output/'SUMMARY.json')
    data=original.source.load(scientific); rows=[]; counts=Counter(); hashes={}; parity={}
    inventory=read(inputs['original_inventory'])
    expected_names={sid+'.json' for sid in data['sessions']}
    actual_names={p.name for p in (old/'sessions').glob('*.json') if not p.name.endswith('.seal.json')}
    if actual_names != expected_names: raise ValueError('D20 original checkpoint roster is incomplete or extra')
    total=len(expected_names)
    for i,sid in enumerate(sorted(data['sessions'])):
        if (output/'YIELD_REQUEST.json').exists(): return dict(status='yielded',saved_sessions=i)
        raw, provenance=legacy_bytes(old,sid,binding,inventory)
        path=output/'sessions'/(sid+'.json.gz')
        if path.exists():
            retained,receipt=sealed_bytes(path)
            if retained!=raw: raise ValueError('D20 reuse differs from original JSON bytes')
            assert_equal(receipt['provenance'],provenance)
        else:
            receipt=compressed(path,raw)|dict(provenance=provenance)
            write(path.with_suffix('.seal.json'),receipt)
        saved=json.loads(raw); rows.extend(saved['rows']); counts.update(saved['support'])
        name=path.relative_to(output).as_posix(); hashes[name]=sha256(path); parity[name]=receipt
        if i+1>=math.ceil(.1*total) and not (output/'FIRST_TENTH.json').exists():
            elapsed=time.perf_counter()-started
            write(output/'FIRST_TENTH.json',dict(completed_sessions=i+1,total_sessions=total,
                elapsed_seconds=elapsed,projected_seconds=elapsed*total/(i+1),
                scope='Storage reuse only; original frozen whole-card forecast covers unchanged analysis/replay.'))
    if (output/'YIELD_REQUEST.json').exists(): return dict(status='yielded',saved_sessions=total)
    arms,comparisons=original.analyze(rows,config)
    raw=(canonical(comparisons)+'\n').encode('utf8'); path=output/'COMPARISONS.json.gz'
    if path.exists():
        retained,receipt=sealed_bytes(path)
        if retained!=raw: raise ValueError('changed D20 saved comparisons')
    else:
        receipt=compressed(path,raw);write(path.with_suffix('.seal.json'),receipt)
    primary=arms['lexical_observed']['primary']
    report=dict(card='D20',descriptive=True,scientific_admission=False,primary=primary,state=primary['state'],arms=arms,
        input_hashes=binding['inputs'],config=config,session_hashes=hashes,counts=dict(counts),comparisons_hash=sha256(path),
        estimand='Equal writers, equal sessions within writer, equal dismissed menus within session. Lexical suggestion-content-word recall primary; MiniLM cosine secondary. Next50 completed newly typed words, including later revisions.',
        baseline='Exact permutation expectation: uniform other session with same prompt and completed-typed-word progress decile, then uniform menu and supported option. Recipient session excluded in full. Bootstrap resamples writers and recomputes donor weights.',
        uncertainty='Writer-node bootstrap of target and donor roles together; lexical primary and embedding secondary fixed before outcomes.',
        extension='Separate split-half reliability only if lexical primary positive or marginal; not computed by this primary runner.',
        recovery=recovery|dict(reused_sessions=total,all_decompressed_bytes_identical=True,
            original_session_bytes=sum(v['raw_bytes'] for v in parity.values()),
            compressed_session_bytes=sum(v['compressed_bytes'] for v in parity.values())),
        comparison_storage=receipt)
    write(output/'SUMMARY.json',report);return report


def verify(output, inputs, config):
    output=Path(output); report=read(output/'SUMMARY.json')
    scientific,binding,old,recovery=context(output,inputs,config)
    assert_equal(report['input_hashes'],binding['inputs']);assert_equal(report['config'],config)
    for key,value in recovery.items():assert_equal(report['recovery'][key],value)
    assert_equal(read(output/'BINDING.json'),dict(inputs=input_hashes(inputs),config=config,recovery=recovery))
    data=original.source.load(scientific);rows=[];counts=Counter();raw_total=packed_total=0
    inventory=read(inputs['original_inventory'])
    names={f'sessions/{sid}.json.gz' for sid in data['sessions']}
    if set(report['session_hashes'])!=names:raise ValueError('D20 recovery roster differs')
    for sid in sorted(data['sessions']):
        name=f'sessions/{sid}.json.gz';path=output/name
        if sha256(path)!=report['session_hashes'][name]:raise ValueError('changed D20 compressed session')
        raw,receipt=sealed_bytes(path);old_raw,provenance=legacy_bytes(old,sid,binding,inventory)
        if raw!=old_raw:raise ValueError('D20 recovery lost exact original bytes')
        assert_equal(receipt['provenance'],provenance)
        saved=json.loads(raw);validate_rows(data,sid,saved);rows.extend(saved['rows']);counts.update(saved['support'])
        raw_total+=len(raw);packed_total+=path.stat().st_size
    assert_equal(report['recovery'],recovery|dict(reused_sessions=len(data['sessions']),all_decompressed_bytes_identical=True,
        original_session_bytes=raw_total,compressed_session_bytes=packed_total))
    assert_equal(report['counts'],dict(counts));arms,comparisons=original.analyze(rows,config)
    path=output/'COMPARISONS.json.gz'
    if sha256(path)!=report['comparisons_hash']:raise ValueError('changed D20 compressed comparisons')
    raw,receipt=sealed_bytes(path);assert_equal(receipt,report['comparison_storage'])
    if raw!=(canonical(comparisons)+'\n').encode('utf8'):raise ValueError('D20 comparison byte replay differs')
    assert_equal(arms,report['arms']);assert_equal(report['primary'],arms['lexical_observed']['primary'])
    assert_equal(report['state'],report['primary']['state'])
    return dict(verified=True,primary_recomputed=report['primary'],state=report['state'],
        source_windows_replayed=True,original_json_bytes_preserved=True,reused_sessions=len(data['sessions']))
