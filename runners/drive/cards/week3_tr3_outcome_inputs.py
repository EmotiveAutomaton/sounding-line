"""TR3 complete selected-feature counts and canonical offer attribution.

DESIGN CHECK: LESSONS 2-5 and CONTROLS read 2026-10-27. NULL and ALTERNATIVE
must retain the complete split and count only actual selected alternatives as
accepted. Reopens, empty menus, mixed sources and wrong logged indices cannot
invent production. Source or replay disagreement refuses. Exhaustive states:
complete count preparation or failure; no carryover inference is performed.
"""
from collections import Counter, defaultdict
import hashlib
from pathlib import Path
import time

from .timing_census import read, filehash
from .timing_pmap_source import completed
from .timing_p6 import gzread, gzip_equal, write_equal, progress
from .week3_tr3_candidates import features, discovery_roster
from .week3_tr3_human_counts import production_counts
from .week3_tr3_selection import checked_counts


def offer_counts(exposure, canonical, selected):
    if not canonical['usable'] or not canonical['reconstructed'] or canonical['errors']:
        raise ValueError('invalid canonical source')
    menus = {r['ordinal']: r for r in canonical['events']}
    if len(menus) != len(canonical['events']):
        raise ValueError('duplicate canonical menu')
    counts = defaultdict(Counter); seen = set(); stats = Counter()
    for display in exposure['displays']:
        if display['reopened']:
            stats['reopens'] += 1
            continue
        origin = display['origin']
        if origin != display['ordinal'] or origin in seen or origin not in menus:
            raise ValueError('original menu coverage differs')
        seen.add(origin); row = menus[origin]
        if (display['options'] != row['options'] or
                display['handling_usable'] != row['usable'] or
                display['handling'] != (row['decision'] if row['usable'] else None)):
            raise ValueError('canonical offer or handling differs')
        options = row['options']; indices = [o['index'] for o in options]
        if len(indices) != len(set(indices)) or any(type(i) is not int for i in indices):
            raise ValueError('invalid canonical option identities')
        accepted = set()
        if row['usable'] and row['decision'] in ('accept', 'edit'):
            accepted = set(row['matched_option_indices'])
            if not row['verified_insertion'] or len(accepted) != 1 or not accepted <= set(indices):
                raise ValueError('accepted identity not uniquely reconstructed')
        for option in options:
            if not row['usable']:
                handling = 'unknown'
            elif option['index'] in accepted:
                handling = 'accepted'
            elif row['decision'] == 'dismiss':
                handling = 'dismissed'
            else:
                handling = 'other'
            stats['alternatives'] += 1
            for feature in set(features(option['original'])) & selected:
                counts[feature]['shown'] += 1
                counts[feature][handling] += 1
        stats['menus'] += 1; stats['empty_menus'] += not bool(options)
    if seen != set(menus):
        raise ValueError('canonical menus missing from exposure')
    return dict(counts={f: dict(sorted(c.items())) for f,c in sorted(counts.items())},
                support=dict(stats))


def prepare(roster, exposure, human, canonical, selected):
    if any(any(row[k] != roster[k] for k in ('session','writer','prompt')) for row in (exposure,human)):
        raise ValueError('selected-count identity differs')
    if (exposure['start'], exposure['end']) != (roster['start'], roster['end']):
        raise ValueError('selected-count chronology differs')
    if human['typed_characters'] != roster['typed_inserted_characters']:
        raise ValueError('selected-count denominator differs')
    checked_counts(human['feature_counts'])
    offers = offer_counts(exposure, canonical, selected)
    return dict(session=roster['session'], writer=roster['writer'], prompt=roster['prompt'],
        half=roster['half'], typed_characters=human['typed_characters'],
        human_counts={f:n for f,n in sorted(human['feature_counts'].items()) if f in selected},
        offers=offers['counts'], offer_support=offers['support'])


def canonical_index(typing_root):
    completed(typing_root/'COMPLETE.json', typing_root/'PLAN.json')
    completed(typing_root/'COMPLETE.json', typing_root/'output/BINDING.json')
    candidates = defaultdict(list)
    for path, digest in read(typing_root/'PLAN.json')['pins'].items():
        path = Path(path)
        if '/coauthor-v2/sessions/' in path.as_posix():
            candidates[digest].append(path)
    result = {}
    for row in read(typing_root/'output/BINDING.json')['units']:
        sid = row['session']; digest = row['source_hashes']['canonical']
        if sid in result or digest not in candidates:
            raise ValueError('canonical binding missing or duplicate')
        # Multiple paths with identical bytes are the same authenticated record.
        path = sorted(candidates[digest])[0]
        if filehash(path) != digest:
            raise ValueError('canonical binding changed')
        result[sid] = (path, digest)
    return result


def run(output, inputs, config, verification=False):
    mode = config.get('mode')
    if config != dict(mode=mode, seed=20261026) or mode not in ('constructed','full'):
        raise ValueError('frozen outcome-input configuration required')
    output = Path(output); output.mkdir(parents=True, exist_ok=True); started = time.process_time()
    if mode == 'constructed':
        if set(inputs) != {'fixture'}:
            raise ValueError('fixture required')
        fixture = read(inputs['fixture']); census = fixture['census']; split = fixture['split']
        selection = fixture['selection']; parents = None
    else:
        keys = ('exposure','typing','human','selection')
        if set(inputs) != {k+'_completion' for k in keys}:
            raise ValueError('exact completed sources required')
        parents = {k:Path(inputs[k+'_completion']).parent for k in keys}
        for key, name in [('exposure','CENSUS.json'),('exposure','WB1_WRITER_SPLIT.json'),('selection','SELECTION.json')]:
            completed(inputs[key+'_completion'], parents[key]/'output'/name)
        census = read(parents['exposure']/'output/CENSUS.json'); split = read(parents['exposure']/'output/WB1_WRITER_SPLIT.json')
        selection = read(parents['selection']/'output/SELECTION.json')
        canonicals = canonical_index(parents['typing'])
        if set(canonicals) != {r['session'] for r in census['roster']}:
            raise ValueError('canonical census population differs')
    discovery_roster(census, split, mode == 'full')
    selected = {r['feature'] for r in selection['features']}
    if len(selected) != len(selection['features']):
        raise ValueError('duplicate selected feature')
    checked_counts({f:1 for f in selected})
    stats = Counter(); bindings = []; roster = sorted(census['roster'], key=lambda r:r['session'])
    for i,r in enumerate(roster):
        sid = r['session']; name = hashlib.sha256(sid.encode()).hexdigest()+'.json.gz'; hashes = {}
        if parents is None:
            unit = fixture['units'][sid]; exposure = unit['exposure']; canonical = unit['canonical']
            human = unit['human'] if r['half']=='discovery' else production_counts(unit['typing'])
        else:
            path = parents['exposure']/'output/sessions'/name
            completed(inputs['exposure_completion'], path); hashes['exposure'] = filehash(path); exposure = gzread(path)
            path, digest = canonicals[sid]; canonical = read(path); hashes['canonical'] = digest
            if r['half'] == 'discovery':
                path = parents['human']/'output/sessions'/name
                completed(inputs['human_completion'], path); hashes['human'] = filehash(path); human = gzread(path)
            else:
                path = parents['typing']/'output/sessions'/name
                completed(inputs['typing_completion'], path); hashes['typing'] = filehash(path); human = production_counts(gzread(path))
        row = prepare(r, exposure, human, canonical, selected)
        path = output/'sessions'/name
        if verification:
            if gzread(path) != row:
                raise ValueError('outcome-input session replay differs')
        else:
            gzip_equal(path, row)
        stats.update(sessions=1, typed_characters=row['typed_characters'],
                     discovery_counts_reused=int(r['half']=='discovery'), test_counts_computed=int(r['half']=='test'))
        stats.update(row['offer_support']); bindings.append(dict(session=sid, sources=hashes))
        progress(output/'PROGRESS.json', dict(phase='verify-selected-inputs' if verification else 'selected-inputs',done=i+1,total=len(roster)))
        if (output.parent/'STOP').exists() or (output/'YIELD_REQUEST.json').exists():
            raise InterruptedError('selected-input yield at complete session boundary')
    summary = dict(stats, writers=len(split['writers']), selected_features=len(selected),
        constructed=mode=='constructed', scientific_admission=False,
        scope='Complete selected-feature typing counts and canonical display attribution; no matched contrast or carryover inference')
    values = {'CENSUS.json':census,'SELECTION.json':selection,'SUMMARY.json':summary,
        'BINDING.json':dict(config=config,inputs={k:filehash(v) for k,v in inputs.items()},units=bindings)}
    for name,value in values.items():
        if verification:
            if read(output/name) != value:
                raise ValueError('outcome-input aggregate replay differs')
        else:
            write_equal(output/name,value)
    if verification:
        return dict(verified=True,complete_outcome_input_replay=True,scientific_admission=False)
    if not (output/'TIMING.json').exists():
        write_equal(output/'TIMING.json',dict(cpu_seconds=time.process_time()-started))
    return dict(status='complete',summary=summary,scientific_admission=False)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
