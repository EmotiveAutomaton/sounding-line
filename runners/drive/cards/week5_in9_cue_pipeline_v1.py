"""IN9 private literal-cue projection, semantic gate and directed odds.

DESIGN CHECK: complete original retained rows; no raw-text output. Contextual
precision is reviewed separately before any odds. Whole-writer resampling keeps
all failed draws. The items-primary implementation remains immutable.
"""
from pathlib import Path
import hashlib
import json
import math as scalar
import os
import time
import zipfile
for _key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_key] = '2'
import numpy as np
import pandas as pd
from . import week5_in as original
from . import week5_in9_cues_v1 as literal
from . import week5_in9_cue_math_v1 as math
from . import week5_engine_export_io as seal
from . import week5_qualification_io as io

MODULE = 'runners.drive.cards.week5_in9_cue_pipeline_v1'
TABLE_PIN = '196fe2a4f72b36ae91516ee5caf762cb3ba04f7d69b6da4e53958587d44c1638'
SOURCE_COLUMNS = ['text_id', 'prolific_id', 'emotion', 'generated_text']
REASONS = ('context_supports', 'negated', 'quoted_other', 'other_referent', 'literal_only', 'unclear')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def dependencies():
    return {Path(m.__file__).as_posix(): io.sha(m.__file__) for m in (original, literal, math, seal, io)} | {Path(__file__).as_posix(): io.sha(__file__)}


def settings(config):
    if set(config)-{'phase', 'draws', 'max_new_draws', 'max_wall_seconds'} or config.get('phase') not in ('IN9-cues-prepare', 'IN9-cues'):
        raise ValueError('Exact declared cue phases only')
    if config.get('draws', 2000) != 2000 or type(config.get('max_new_draws', 100)) is not int or config.get('max_new_draws', 100) < 1:
        raise ValueError('Complete2000 draws and positive whole-unit quantum required')
    if not np.isfinite(config.get('max_wall_seconds', 900)) or config.get('max_wall_seconds', 900) <= 0:
        raise ValueError('Finite positive wall bound required')
    return {'phase':config['phase'], 'draws':2000, 'literal_lists':literal.LEXICONS,
            'exposure':'binary literal presence; counts also retained', 'prevalence_floor':.05,
            'audit':'all hits if fewer than100; otherwise first100 fixed hash ranks; at least80% contextual precision',
            'contrast':'unadjusted odds of shame versus guilt when cue present versus absent; no added bar'}


def load_source(inputs):
    if set(inputs) != {'source_run'}:
        raise ValueError('Qualified original IN source required')
    root, plan, _ = seal.complete(inputs['source_run'], 'runners.drive.cards.week5_in')
    if plan['config'].get('phase') != 'prepare':
        raise ValueError('Original source preparation required')
    archive_path, salt_path = Path(plan['inputs']['source']), Path(plan['inputs']['salt'])
    if io.sha(archive_path) != original.SOURCE_SHA or io.sha(salt_path) != plan['pins'].get(str(salt_path)):
        raise ValueError('Pinned archive or private salt changed')
    if io.sha(root/'output/generation.parquet') != TABLE_PIN:
        raise ValueError('Qualified numeric generation table changed')
    salt = salt_path.read_bytes()
    if len(salt) != 32:
        raise ValueError('Private salt length differs')
    base = pd.read_parquet(root/'output/generation.parquet', columns=['text_id', 'prolific_id', 'emotion'])
    base = base.loc[base.emotion.isin(['shame', 'guilt'])].copy()
    with zipfile.ZipFile(archive_path) as archive:
        with archive.open('corpus/crowd-enVent_generation.tsv') as stream:
            extra = pd.read_csv(stream, sep='\t', usecols=SOURCE_COLUMNS, dtype=str, keep_default_na=False)
    if len(extra) != 6600 or extra.text_id.duplicated().any():
        raise ValueError('Source row cardinality or uniqueness differs')
    for column, namespace in [('text_id', 'crowd-text'), ('prolific_id', 'crowd-person')]:
        extra[column] = extra[column].map(lambda v: original.salted(v, salt, namespace))
    identity = {'source_complete':io.sha(root/'COMPLETE.json'), 'source_plan':io.sha(root/'PLAN.json'),
                'archive':original.SOURCE_SHA, 'salt_sha256':io.sha(salt_path), 'qualified_table':TABLE_PIN,
                'read_columns':SOURCE_COLUMNS, 'raw_text_written':False, 'demographics_loaded':False}
    return base, extra, identity


def project(base, extra, independent=False):
    lookup = extra.set_index('text_id'); rows = []
    count = literal.independent_count if independent else literal.count
    for row in base.sort_values('text_id').to_dict('records'):
        item = lookup.loc[row['text_id']]
        if item.prolific_id != row['prolific_id'] or item.emotion != row['emotion']:
            raise ValueError('Private original writer/text/prompt join changed')
        rows.append({**row, **count(item.generated_text)})
    return rows


def sample(rows):
    by_family = {}
    for name in math.FAMILIES:
        hits = [r['text_id'] for r in rows if r[name] > 0]
        rank = lambda key: hashlib.sha256(f'IN9-cue-audit|20261113|{name}|{key}'.encode()).hexdigest()
        chosen = sorted(hits, key=lambda key:(rank(key), key))[:100]
        by_family[name] = {'hits':len(hits), 'prevalence':len(hits)/len(rows) if rows else 0,
            'method':'census' if len(hits) < 100 else 'fixed100-hit sample',
            'required_reviews':len(chosen), 'private_text_ids':chosen, 'rank_sha256':[rank(key) for key in chosen]}
    return {'families':by_family, 'total_texts':len(rows), 'lexicons_sha256':io.sha(literal.__file__),
            'no_text_or_prompt_labels_in_review_sample':True}


def should_yield(output, start, config, added):
    root = Path(output).parent if Path(output).name == 'independent-replay' else Path(output)
    return (added >= config.get('max_new_draws', 100) or time.monotonic()-start >= config.get('max_wall_seconds', 900)
            or any((root/name).exists() for name in ('YIELD_REQUEST.json', 'STOP_REQUEST.json')))


def prepare(output, inputs, config, independent=False):
    output = Path(output); output.mkdir(parents=True, exist_ok=True); semantic = settings(config)
    base, extra, identity = load_source(inputs)
    if base.text_id.duplicated().any() or not set(base.text_id).issubset(set(extra.text_id)):
        raise ValueError('Complete unique retained source join required')
    binding = digest({'source':identity, 'semantic':semantic, 'modules':dependencies(), 'independent':independent})
    groups = dict(tuple(base.groupby('prolific_id', sort=True))); keys = sorted(groups)
    extra_people = dict(tuple(extra.groupby('prolific_id', sort=True)))
    rows = []; started = time.monotonic(); added = 0
    for index, key in enumerate(keys):
        path = output/'writers'/f'{index:06}.json'
        if path.exists():
            block = seal.state(path, binding, {})
            if block['ordinal'] != index or block['person'] != key:
                raise ValueError('Checkpoint writer ordering differs')
        else:
            if should_yield(output, started, config, added):
                return {'status':'yielded', 'verified':False, 'phase':'IN9_cue_source_writers', 'completed':index, 'total':len(keys)}
            block = {'binding':binding, 'ordinal':index, 'person':key,
                     'rows':project(groups[key], extra_people[key], independent)}
            seal.checkpoint(path, block); added += 1
        rows.extend(block['rows'])
    rows.sort(key=lambda row:row['text_id']); audit_sample = sample(rows)
    seal.checkpoint(output/'TABLE.json', {'rows':rows, 'source_identity':identity})
    io.write_json(output/'AUDIT_SAMPLE.json', audit_sample)
    result = {'card':'IN9-cues-source', 'record_kind':'run', 'theory_tags':[], 'by_construction':False, 'activation':[],
        'complete_preparation':True, 'source_identity':identity, 'rows':len(rows), 'writers':len(keys),
        'prompt_counts':{name:sum(r['emotion']==name for r in rows) for name in ('shame','guilt')},
        'literal_counts':{name:{'hits':audit_sample['families'][name]['hits'],
                              'occurrences':sum(r[name] for r in rows)} for name in math.FAMILIES},
        'semantic_precision_unreviewed':True, 'no_text_exported':True}
    io.write_json(output/'RESULT.json', result); return result


def load_prepared(inputs):
    if set(inputs) != {'prepared_run','audit'}:
        raise ValueError('Complete cue preparation and explicit audit path or null required')
    root, plan, _ = seal.complete(inputs['prepared_run'], MODULE)
    if plan['config'].get('phase') != 'IN9-cues-prepare' or seal.read(root/'output/RESULT.json').get('complete_preparation') is not True:
        raise ValueError('Complete exact cue source phase required')
    table, audit_sample = seal.read(root/'output/TABLE.json'), seal.read(root/'output/AUDIT_SAMPLE.json')
    identity = {'prepared_complete_sha256':io.sha(root/'COMPLETE.json'), 'table_sha256':io.sha(root/'output/TABLE.json'),
                'sample_sha256':io.sha(root/'output/AUDIT_SAMPLE.json'), 'source_identity':table['source_identity']}
    audit = None if inputs['audit'] is None else seal.read(inputs['audit'])
    identity['audit_sha256'] = None if inputs['audit'] is None else io.sha(inputs['audit'])
    return pd.DataFrame(table['rows']), audit_sample, audit, identity


def audit_gate(audit_sample, audit, identity):
    if audit is not None:
        if set(audit) != {'prepared_complete_sha256','table_sha256','sample_sha256','reviewer_role','method','families'}:
            raise ValueError('Exact private semantic-review schema required')
        if any(audit[k] != identity[k] for k in ('prepared_complete_sha256','table_sha256','sample_sha256')):
            raise ValueError('Semantic audit source/sample changed')
        if audit['method'] != 'local blinded context review; no text exported' or not audit['reviewer_role']:
            raise ValueError('Explicit local semantic-review method and reviewer role required')
        if set(audit['families'])-set(math.FAMILIES):
            raise ValueError('Undeclared audit family')
    gates = {}
    for name, specimen in audit_sample['families'].items():
        basic = {k:specimen[k] for k in ('hits','prevalence','method','required_reviews')}
        if specimen['prevalence'] < .05:
            gates[name] = {**basic, 'status':'unsupported: under5% of the two prompts'}; continue
        if audit is None or name not in audit['families']:
            gates[name] = {**basic, 'status':'held: missing semantic audit', 'reviewed':0}; continue
        reviews = audit['families'][name]
        if not isinstance(reviews,list) or len(reviews) != specimen['required_reviews']:
            raise ValueError('Complete census or exact100-hit audit required')
        found = {}
        for item in reviews:
            if set(item) != {'text_id','correct','reason'} or type(item['correct']) is not bool or item['reason'] not in REASONS:
                raise ValueError('Audit uses only private key, Boolean and fixed reason code; never source text')
            if item['text_id'] in found or item['correct'] != (item['reason']=='context_supports'):
                raise ValueError('Duplicate or inconsistent semantic judgment')
            found[item['text_id']] = item
        if set(found) != set(specimen['private_text_ids']) or not found:
            raise ValueError('Audit reviewed a different hit selection')
        correct = sum(item['correct'] for item in found.values())
        failed = [i for i,key in enumerate(specimen['private_text_ids']) if not found[key]['correct']]
        gates[name] = {**basic, 'status':'qualified literal cue' if 5*correct >= 4*len(found) else 'instrument failed',
            'reviewed':len(found), 'correct':correct, 'precision':correct/len(found), 'failed_sample_ordinals':failed}
    return gates


def calculate(frame, audit_sample, audit, identity, output, config, independent=False):
    output=Path(output); output.mkdir(parents=True,exist_ok=True); semantic=settings(config)
    prepared=math.prepare(frame); counts={n:int(frame.emotion.eq(n).sum()) for n in ('shame','guilt')}
    if sample(frame.to_dict('records')) != audit_sample:
        raise ValueError('Full private cue sample does not match the prepared table')
    gates=audit_gate(audit_sample,audit,identity)
    common={'card':'IN9-cues','record_kind':'claim','theory_tags':['H15-T5'],'by_construction':False,
        'activation':[{'channel':'SHAME','observation':'self-labelled shame prompt and qualified literal context'},
                      {'channel':'CARE','observation':'guilt-as-CARE is the attributed proposal, not established tissue'}],
        'scope':'prompted recollections and frozen literal phrases; not two feelings or a causal sender test',
        'source_gap':'R13-R15 supporting handoffs absent; explicit packet governs',
        'source_identity':identity,'semantic':semantic,'prompt_counts':counts,'writers':len(prepared['keys']),
        'instrument_gates':gates,'no_text_exported':True,'complete_card':True}
    if min(counts.values())<200:
        return {**common,'status':'unsupported','reason':'fewer than200 texts in either original prompt'}
    families=[name for name in math.FAMILIES if gates[name]['status']=='qualified literal cue']
    if not families:
        return {**common,'record_kind':'run','status':'count-only: no qualified cue family','activation':[]}
    binding=digest({'source':identity,'semantic':semantic,'modules':dependencies(),'families':families,
                    'frame':frame.to_json(orient='split'),'independent':independent})
    saved=seal.state(output/'DRAWS.json',binding,{'point':None,'draws':[]})
    if saved['point'] is None:
        saved['point']=math.evaluate(prepared,np.ones(len(frame),dtype=int),families,independent)
        seal.checkpoint(output/'DRAWS.json',saved)
    start=time.monotonic(); added=0; cpu=time.process_time()
    while len(saved['draws'])<2000 and len(prepared['keys'])>=2:
        if should_yield(output,start,config,added):
            seal.checkpoint(output/'DRAWS.json',saved)
            return {'status':'yielded','verified':False,'phase':'IN9_cue_writer_draws','completed':len(saved['draws']),'total':2000}
        weights=math.draw_weights(prepared['codes'],len(prepared['keys']),len(saved['draws']))
        saved['draws'].append(math.evaluate(prepared,weights,families,independent)); added+=1
        if added==1 and not (output/'COST_PREFIX.json').exists():
            io.write_json(output/'COST_PREFIX.json',{'first_draw_CPU_seconds':time.process_time()-cpu,
                                                   'excludes_source_audit_and_complete_replay':True})
        if len(saved['draws'])%10==0:
            seal.checkpoint(output/'DRAWS.json',saved)
            io.write_json(output/'PROGRESS.json',{'phase':'IN9_cue_writer_draws','completed':len(saved['draws']),'total':2000})
    seal.checkpoint(output/'DRAWS.json',saved)
    return {**common,'status':'complete directed secondaries','all_failed_draws_retained':True,
        'cues':{name:math.summarize(saved['point'][name],[d[name] for d in saved['draws']],len(prepared['keys']),independent)
                for name in families}}


def equivalent(left,right):
    if isinstance(left,dict):
        return isinstance(right,dict) and set(left)==set(right) and all(equivalent(v,right[k]) for k,v in left.items())
    if isinstance(left,list):
        return isinstance(right,list) and len(left)==len(right) and all(equivalent(a,b) for a,b in zip(left,right))
    if isinstance(left,float):
        return isinstance(right,(float,int)) and scalar.isclose(left,right,rel_tol=1e-9,abs_tol=1e-10)
    return left==right


def execute(output,inputs,config):
    settings(config)
    if config['phase']=='IN9-cues-prepare': return prepare(output,inputs,config)
    result=calculate(*load_prepared(inputs),output,config)
    if result.get('status')!='yielded': io.write_json(Path(output)/'RESULT.json',result)
    return result


def verify(output,inputs,config):
    output=Path(output); settings(config)
    if config['phase']=='IN9-cues-prepare':
        result=prepare(output/'independent-replay',inputs,config,True)
        if result.get('status')!='yielded':
            for name in ('TABLE.json','AUDIT_SAMPLE.json'):
                if seal.read(output/name)!=seal.read(output/'independent-replay'/name):
                    raise ValueError('Complete independent cue count/source projection differs')
    else:
        result=calculate(*load_prepared(inputs),output/'independent-replay',config,True)
    if result.get('status')=='yielded': return {**result,'verified':False}
    if not equivalent(result,seal.read(output/'RESULT.json')):
        raise ValueError('Complete independent cue source, semantic gate or odds replay differs')
    return {'verified':True,'complete_independent_source_and_formula_replay':True,'no_text_exported':True}
