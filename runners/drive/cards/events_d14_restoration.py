"""D14's single conditional accept-then-edit topic-restoration extension.

DESIGN CHECK: LESSONS 3-5. Unchanged/orthogonal edits give zero restoration;
movement toward/away from the pre-suggestion paragraph gives positive/negative
signs. Select the first touch before reading its effect; ambiguous first touch
excludes the acceptance rather than selecting a later favorable edit. Zero
embedding changes stay. P5's content/housekeeping threshold never selects this
sample. Hash-verified preserved D14/P5/raw/P2 sources bind the paired readout;
neural values are reused, not freshly validated by this numerical verifier.
"""
import gzip
import hashlib
import json
import math
import time
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from .events_p5 import read, write, filehash, model_identity
from .events_d4 import save, read_sealed, sealed, assert_close
from .events_d4_sources import bind_completed
from .events_d4_stats import interval, stable_seed
from .events_d14_features import paragraph

CONFIG = dict(threads=2, bootstrap=2000, seed=20261017)
SHARED = {'sessions', 'content_records', 'content_vectors', 'content_model', 'content_complete',
          'p8_rows', 'p8_summary', 'p8_verified'}
INPUTS = SHARED | {'d14_summary', 'd14_inputs', 'd14_index', 'd14_completion',
    'p5_index', 'p5_inputs', 'p5_summary', 'p5_source_pins', 'p5_completion', 'p2_index', 'source_roster', 'source_root'}
FORECAST = 900


def input_pins(inputs):
    pins = {str(Path(p)): filehash(p) for k, p in inputs.items() if k != 'source_root'}
    identity = read(inputs['content_model']); model_identity(inputs['content_model'])
    pins.update({str(Path(identity['path']) / rel): digest for rel, digest in identity['files'].items()})
    # The exact completed primary input capsule also pins P4/P8, spaCy and the
    # retained failed/pilot provenance. Authenticate all of it without refitting.
    for path, expected in read(inputs['d14_inputs'])['pins'].items():
        if path in pins and pins[path] != expected or filehash(path) != expected:
            raise ValueError('D14 preserved primary source changed')
        pins[path] = expected
    return pins


def source(inputs):
    for key in ('d14_summary', 'd14_inputs', 'd14_index'):
        bind_completed(inputs['d14_completion'], inputs[key])
    for key in ('p5_index', 'p5_inputs', 'p5_summary', 'p5_source_pins'):
        bind_completed(inputs['p5_completion'], inputs[key])
    summary, d14, p5 = read(inputs['d14_summary']), read(inputs['d14_inputs']), read(inputs['p5_inputs'])
    if (summary['card'] != 'D14' or summary['phase'] != 'main' or summary.get('execution_only')
            or summary['primary']['state'] not in ('positive', 'marginal') or summary.get('extension_run')):
        raise ValueError('D14 main does not open restoration')
    if d14['config'] != dict(phase='main',threads=2,batch_size=16,bootstrap=2000,seed=20261017,pca_dimensions=16):
        raise ValueError('D14 original config differs')
    for key in SHARED:
        if Path(d14['paths'][key]).resolve() != Path(inputs[key]).resolve() or d14['pins'][str(Path(inputs[key]))] != filehash(inputs[key]):
            raise ValueError('D14 shared source differs')
    for key in ('sessions', 'content_model', 'p2_index', 'source_roster', 'source_root'):
        if Path(p5['paths'][key]).resolve() != Path(inputs[key]).resolve():
            raise ValueError('P5 raw/session/model source differs')
        if key != 'source_root' and p5['sha256'][key] != filehash(inputs[key]):
            raise ValueError('P5 source hash differs')
    content = read(inputs['content_complete'])
    if content.get('status') != 'COMPLETE':
        raise ValueError('CONTENT incomplete')
    for key in ('content_records', 'content_vectors', 'content_model'):
        if [v for k, v in content['outputs'].items() if Path(k).name == Path(inputs[key]).name] != [filehash(inputs[key])]:
            raise ValueError('CONTENT completion differs')
    p8 = read(inputs['p8_summary'])
    if p8.get('status') != 'complete' or p8['table_sha256'] != filehash(inputs['p8_rows']) or not read(inputs['p8_verified']).get('verified'):
        raise ValueError('preserved P8 evidence differs')
    sessions, records = read(inputs['sessions']), read(inputs['content_records'])
    session_map = {s['session']: s for s in sessions}; record_map = {r['key']: r for r in records}
    menu_keys = [r['key'] for s in sessions for r in s['rows']]
    p5_rows, p2_rows, roster_rows, d14_rows = (read(inputs[k]) for k in ('p5_index', 'p2_index', 'source_roster', 'd14_index'))
    maps = [{r['session']: r for r in rows} for rows in (p5_rows, p2_rows, roster_rows)]
    if (len(session_map) != len(sessions) or len(record_map) != len(records) or len(set(menu_keys)) != len(menu_keys)
            or set(menu_keys) != set(record_map) or any(len(m) != len(r) for m, r in zip(maps, (p5_rows,p2_rows,roster_rows)))
            or set(session_map) != set(maps[0]) or set(session_map) != set(maps[1]) or not set(session_map) <= set(maps[2])
            or read(inputs['p5_summary'])['sessions'] != len(sessions)):
        raise ValueError('D14 restoration source coverage differs')
    d14_map = {r['writer']: r for r in d14_rows}; writers = sorted({s['writer'] for s in sessions})
    if len(d14_map) != len(d14_rows) or sorted(d14_map) != writers or summary['selected_writers'] != writers:
        raise ValueError('D14 full writer coverage differs')
    vectors = np.load(inputs['content_vectors'], mmap_mode='r', allow_pickle=False)
    if vectors.ndim != 2 or vectors.shape[1] != 384:
        raise ValueError('CONTENT shape differs')
    for session in sessions:
        if not math.isfinite(session['timestamp']) or len({m['ordinal'] for m in session['rows']}) != len(session['rows']):
            raise ValueError('session chronology/menu ordinal differs')
        for menu in session['rows']:
            record = record_map[menu['key']]
            if (any(menu[k] != session[k] or record[k] != session[k] for k in ('session','writer'))
                    or len(record['options']) != len(menu['menu'])
                    or any(type(i) is not int or not 0 <= i < len(vectors) for i in record['options'])):
                raise ValueError('CONTENT menu identity/index differs')
    return dict(sessions=sessions, records=record_map, vectors=vectors, p5=maps[0], p2=maps[1],
        roster=maps[2], d14=d14_map, raw_pins=read(inputs['p5_source_pins']))


def vector(value):
    a = np.asarray(value, float)
    if a.shape != (384,) or not np.isfinite(a).all() or not np.isclose(np.linalg.norm(a), 1., atol=1e-5, rtol=0):
        raise ValueError('invalid restoration embedding')
    return a


def first_touch_rows(session, saved, vectors, eligible, paragraphs):
    vectors = np.asarray(vectors)
    if (vectors.ndim != 2 or vectors.shape[1] != 384 or len(vectors) != len(saved['visibility'])
            or len({e['ordinal'] for e in saved['edits']}) != len(saved['edits'])):
        raise ValueError('P5 edit/vector coverage differs')
    first = {}
    for edit in sorted(saved['edits'], key=lambda e: e['ordinal']):
        for owner in edit['accepted_owners_touched']:
            first.setdefault(owner, edit)
    rows, excluded = [], []
    for menu in sorted(session['rows'], key=lambda r: (r['ordinal'], r['key'])):
        if menu['key'] not in eligible:
            continue
        edit = first.get(menu['ordinal'])
        reason = None
        if edit is None:
            reason = 'accepted-then-edited menu has no recovered first touch'
        elif menu['ordinal'] >= edit['ordinal']:
            raise ValueError('correction does not follow acceptance')
        elif edit['origin'] != 'model' or edit['accepted_owners_touched'] != [menu['ordinal']]:
            reason = 'first touch lacks one exclusive accepted owner'
        elif any(count > 0 for origin, count in edit['deleted_origin_counts'].items() if origin != 'accepted'):
            reason = 'first touch has mixed changed-span provenance'
        elif not edit['before'].strip() or not edit['after'].strip():
            reason = 'empty before or after sentence window'
        if reason:
            excluded.append(dict(key=menu['key'], session=session['session'], ordinal=edit['ordinal'] if edit else None, reason=reason)); continue
        for side in ('before','after'):
            index = edit[side+'_vector']
            if type(index) is not int or not 0 <= index < len(vectors):
                raise ValueError('P5 sentence vector index differs')
            scope = saved['visibility'][index]
            if (scope['full_tokens'] < 0 or scope['used_tokens'] != min(scope['full_tokens'],254)
                    or scope['truncated'] != (scope['full_tokens']>254)
                    or not 0 <= scope['codepoint_end'] <= len(edit[side])):
                raise ValueError('P5 sentence token scope differs')
        before, after, anchor = vector(vectors[edit['before_vector']]), vector(vectors[edit['after_vector']]), vector(paragraphs[menu['key']]['vector'])
        before_fit, after_fit = (float(np.clip(a @ anchor, -1, 1)) for a in (before, after))
        rows.append(dict(key=menu['key'], writer=session['writer'], session=session['session'],
            accepted_ordinal=menu['ordinal'], correction_ordinal=edit['ordinal'],
            before_vector=before.tolist(), after_vector=after.tolist(), anchor=anchor.tolist(),
            before_text_sha256=hashlib.sha256(edit['before'].encode()).hexdigest(), after_text_sha256=hashlib.sha256(edit['after'].encode()).hexdigest(),
            before_scope=saved['visibility'][edit['before_vector']], after_scope=saved['visibility'][edit['after_vector']],
            paragraph_scope=paragraphs[menu['key']]['scope'], original_offer_drift=eligible[menu['key']]['topic_drift'],
            before_drift=1-before_fit, after_drift=1-after_fit, restoration=after_fit-before_fit,
            deterministic_split=edit['split'], zero_embedding_change=bool(np.array_equal(before, after))))
    return rows, excluded


def extract_writer(writer, data, inputs):
    d14_root = Path(inputs['d14_index']).resolve().parent
    entry = data['d14'][writer]; d14_path = (d14_root / entry['file']).resolve(); d14_path.relative_to(d14_root)
    bind_completed(inputs['d14_completion'], d14_path)
    if filehash(d14_path) != entry['sha256']:
        raise ValueError('D14 writer extraction changed')
    old = read_sealed(d14_path); own = sorted((s for s in data['sessions'] if s['writer'] == writer), key=lambda s:(s['timestamp'],s['session']))
    if any(row['writer'] != writer for row in old['rows']):
        raise ValueError('D14 preserved writer identity differs')
    menus = {m['key']: m for s in own for m in s['rows']}; paragraphs = {r['key']: r for r in old['paragraphs']}
    if set(paragraphs) != set(menus) or len(paragraphs) != len(old['paragraphs']):
        raise ValueError('D14 paragraph coverage differs')
    for key, context in paragraphs.items():
        text, start, end = paragraph(menus[key]['document']); vector(context['vector'])
        if [start, end] != [context['start_codepoint'], context['end_codepoint']]:
            raise ValueError('preserved D14 paragraph source bounds differ')
        scope = context['scope']
        if (scope['used_tokens'] != min(scope['full_tokens'],254) or scope['first_native_token'] != max(0,scope['full_tokens']-254)
                or scope['truncated'] != (scope['full_tokens']>254) or not 0 <= scope['codepoint_start'] <= scope['codepoint_end'] <= len(text)):
            raise ValueError('D14 paragraph token scope differs')
    eligible = {}
    for row in old['rows']:
        if row['handling'] != 'edit':
            continue
        menu = menus[row['key']]; record = data['records'][row['key']]
        chosen = [i for i,t in enumerate(menu['menu']) if t == menu['inserted']]
        if (row['writer'] != writer or row['session'] != menu['session'] or menu['handling'] != 'edit'
                or chosen != [row['position']] or row['key'] in eligible or not paragraph(menu['document'])[0].strip()):
            raise ValueError('original D14 accepted-edit scope differs')
        expected = 1-float(vector(paragraphs[row['key']]['vector']) @ vector(data['vectors'][record['options'][row['position']]]))
        if not np.isclose(expected,row['topic_drift'],rtol=0,atol=1e-6):
            raise ValueError('preserved D14 topic drift differs')
        eligible[row['key']] = row
    rows, excluded, pins = [], [], {str(d14_path): entry['sha256']}
    root, p2_root, raw_root = Path(inputs['p5_index']).resolve().parent, Path(inputs['p2_index']).resolve().parent, Path(inputs['source_root']).resolve()
    for session in own:
        if not any(m['key'] in eligible for m in session['rows']):
            continue
        sid = session['session']; p5 = data['p5'][sid]; p2 = data['p2'][sid]; raw = data['roster'][sid]
        if p2['writer'] != writer or raw['writer'] != writer:
            raise ValueError('P5/P2/raw writer differs')
        raw_path = (raw_root / raw['path']).resolve(); raw_path.relative_to(raw_root)
        p2_path = (p2_root / p2['file']).resolve(); p2_path.relative_to(p2_root)
        for path, expected in ((raw_path, raw['source_sha256']), (p2_path,p2['sha256'])):
            if data['raw_pins'].get(str(path)) != expected or filehash(path) != expected:
                raise ValueError('preserved P5 raw/P2 source changed')
            pins[str(path)] = expected
        for field, digest in (('file','sha256'),('vectors','vectors_sha256')):
            path = (root / p5[field]).resolve(); path.relative_to(root)
            if filehash(path) != p5[digest]:
                raise ValueError('P5 sentence checkpoint changed')
            pins[str(path)] = p5[digest]
        with gzip.open(root / p5['file'],'rt',encoding='utf8') as f:
            saved = json.load(f)
        if any(saved[k] != session[k] for k in ('writer','session','timestamp','end_at')) or saved['source_sha256'] != raw['source_sha256'] or saved['p2_sha256'] != p2['sha256']:
            raise ValueError('P5 saved source identity differs')
        rr, ee = first_touch_rows(session, saved, np.load(root / p5['vectors'],allow_pickle=False), eligible, paragraphs)
        rows.extend(rr); excluded.extend(ee)
    return dict(writer=writer, rows=rows, exclusions=excluded, source_pins=pins,
        original_edit_menus=len(eligible), original_d14_rows=len(old['rows']),
        original_noneligible_menus=len(menus)-len(eligible))


def summarize(units, config):
    values = {k: [] for k in ('restoration','anchor_shuffle','direction_swap')}; per_writer = []; control_support=Counter()
    for unit in sorted(units,key=lambda u:u['writer']):
        rows = sorted(unit['rows'],key=lambda r:(r['session'],r['accepted_ordinal'],r['key']))
        if not rows:
            per_writer.append(dict(writer=unit['writer'],eligible=False,reason='no eligible first-touch correction')); continue
        rng = np.random.default_rng(stable_seed(config['seed'],unit['writer']))
        permuted = rng.permutation(len(rows)); signs = rng.choice([-1,1],size=len(rows)); grouped = {k:defaultdict(list) for k in values}
        control_support['writers_with_one_correction'] += len(rows)==1
        for i,row in enumerate(rows):
            before,after,anchor=vector(row['before_vector']),vector(row['after_vector']),vector(row['anchor'])
            effect=float(np.clip(after@anchor,-1,1)-np.clip(before@anchor,-1,1))
            if not np.isclose(effect,row['restoration'],rtol=0,atol=1e-12):
                raise ValueError('saved restoration arithmetic differs')
            other=vector(rows[int(permuted[i])]['anchor'])
            control_support['anchor_assignments_changed'] += int(permuted[i])!=i
            control_support['anchor_vectors_changed'] += not np.array_equal(anchor,other)
            control_support['direction_labels_swapped'] += int(signs[i]==-1)
            grouped['restoration'][row['session']].append(effect)
            grouped['anchor_shuffle'][row['session']].append(float(np.clip(after@other,-1,1)-np.clip(before@other,-1,1)))
            grouped['direction_swap'][row['session']].append(effect*int(signs[i]))
        result=dict(writer=unit['writer'],eligible=True,menus=len(rows),sessions=len(grouped['restoration']))
        for arm in values:
            result[arm]=float(np.mean([np.mean(v) for _,v in sorted(grouped[arm].items())]));values[arm].append(result[arm])
        per_writer.append(result)
    return dict(card='D14-restoration',primary=interval(values['restoration'],config['bootstrap'],config['seed']),
        paragraph_anchor_shuffle=interval(values['anchor_shuffle'],config['bootstrap'],config['seed']),
        before_after_direction_swap=interval(values['direction_swap'],config['bootstrap'],config['seed']),
        writer_contrasts=per_writer,rows=sum(len(u['rows']) for u in units),writers=len(units),
        control_support=dict(control_support),
        original_edit_menus=sum(u['original_edit_menus'] for u in units),original_d14_rows=sum(u['original_d14_rows'] for u in units),
        original_noneligible_menus=sum(u['original_noneligible_menus'] for u in units),
        exclusions=[dict(writer=u['writer'],**e) for u in units for e in u['exclusions']],
        splits=dict(Counter(r['deterministic_split'] for u in units for r in u['rows'])),
        zero_embedding_changes=sum(r['zero_embedding_change'] for u in units for r in u['rows']),
        truncated_sentence_windows=sum(r[k]['truncated'] for u in units for r in u['rows'] for k in ('before_scope','after_scope')),
        truncated_paragraphs=sum(r['paragraph_scope']['truncated'] for u in units for r in u['rows']),
        method='Before-minus-after topic drift of first exact accepted-span correction toward frozen pre-suggestion paragraph; equal accepted menus within session, sessions within writer and writers',
        correction_scope='First user edit touching original accepted owner; P5 exact common before/after sentence windows. Mixed or multiple-owner first touch excludes the acceptance, no later rescue. All split labels and zero changes retained.',
        source_scope='Original D14 accepted-then-edited menu eligibility, same CONTENT/P5 model and preserved P4/P8 source capsule. Paired restoration does not refit the protection model.',
        encoding_scope='Preserved D14 full-paragraph native tail254 anchor and P5 before/after sentence native first254 embeddings; exact truncation scopes retained',
        controls='Within-writer paragraph-anchor permutation and independent before/after sign swap, fixed seed; same rows/weights',
        verification_scope='Original raw/P2/P5/D14 input hashes and all numerical/source joins verified; no fresh neural extraction or raw event replay',
        limitations=['Conditional exploratory interval not adjusted for primary-based selection','Sentence-window drift change is not a whole accepted-span reconstruction',
            'No causal set-point or private-goal inference','Sentiment/formality/restoration of other variables unmeasured','P5 and D14 neural values reused from completed sources'],
        extension_run=True,further_extension=None,scientific_admission=False)


def execute(output:Path,inputs:dict,config:dict)->dict:
    if config != CONFIG or set(inputs) != INPUTS:
        raise ValueError('frozen D14 restoration inputs/config differ')
    output=Path(output);output.mkdir(parents=True,exist_ok=True);started=time.monotonic()
    binding=dict(paths=inputs,config=config,pins=input_pins(inputs))
    if (output/'BINDING.json').exists():
        if read(output/'BINDING.json') != binding:raise ValueError('D14 restoration resume binding differs')
        if (output/'SUMMARY.json').exists():raise ValueError('D14 restoration completed output is never rerun')
    elif any(output.iterdir()):raise ValueError('D14 restoration unbound output')
    else:write(output/'BINDING.json',binding)
    data=source(inputs);roster=sorted(data['d14']);units=[];index=[];elapsed=0.
    for writer in roster:
        name='writers/'+hashlib.sha256(writer.encode()).hexdigest()[:24]+'.json';path=output/name
        if sealed(path):
            unit=read_sealed(path)
            if unit['writer'] != writer:raise ValueError('D14 restoration checkpoint writer differs')
            for source_path,expected in unit['source_pins'].items():
                if filehash(source_path) != expected:raise ValueError('D14 restoration checkpoint source changed')
        else:
            clock=time.monotonic();unit=extract_writer(writer,data,inputs);unit['elapsed_seconds']=time.monotonic()-clock;save(path,unit)
        units.append(unit);elapsed+=unit['elapsed_seconds'];index.append(dict(writer=writer,file=name,sha256=filehash(path)))
        if len(index)==max(1,math.ceil(.1*len(roster))) and not (output/'FIRST_TENTH.json').exists():
            write(output/'FIRST_TENTH.json',dict(writers=len(index),total_writers=len(roster),projected_cpu_seconds=2*elapsed*len(roster)/len(index),forecast_cpu_seconds=FORECAST))
        if (output/'YIELD_REQUEST.json').exists():return dict(status='yielded',writers_saved=len(index),writers_total=len(roster))
    save(output/'WRITER_INDEX.json',index);result=summarize(units,config)
    result.update(elapsed_seconds=time.monotonic()-started,saved_extraction_seconds=elapsed,forecast_cpu_seconds=FORECAST)
    write(output/'SUMMARY.json',result)
    write(output/'OUTPUT_HASHES.json',{p.relative_to(output).as_posix():filehash(p) for p in output.rglob('*')
        if p.is_file() and p.name not in ('OUTPUT_HASHES.json','YIELD_REQUEST.json')})
    return result


def verify(output:Path,inputs:dict,config:dict)->dict:
    output=Path(output);binding=read(output/'BINDING.json')
    if binding['paths']!=inputs or binding['config']!=config or config!=CONFIG or set(inputs)!=INPUTS:
        raise ValueError('D14 restoration verification binding differs')
    for path,expected in binding['pins'].items():
        if filehash(path)!=expected:raise ValueError('D14 restoration input changed')
    for relative,expected in read(output/'OUTPUT_HASHES.json').items():
        if filehash(output/relative)!=expected:raise ValueError('D14 restoration output changed')
    data=source(inputs);index=read_sealed(output/'WRITER_INDEX.json');units=[]
    if [e['writer'] for e in index]!=sorted(data['d14']):raise ValueError('D14 restoration writer coverage differs')
    for entry in index:
        unit=read_sealed(output/entry['file'])
        if filehash(output/entry['file'])!=entry['sha256']:raise ValueError('D14 restoration index differs')
        rebuilt=extract_writer(entry['writer'],data,inputs);assert_close(rebuilt,{k:unit[k] for k in rebuilt});units.append(unit)
    result=summarize(units,config);saved=read(output/'SUMMARY.json');assert_close(result,{k:saved[k] for k in result})
    return dict(verified=True,primary_recomputed=result['primary'],summary_sha256=filehash(output/'SUMMARY.json'),
        verification_scope=result['verification_scope'],scientific_admission=False)
