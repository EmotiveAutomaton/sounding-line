"""Bounded native P7 event/path diagnostic; never admits a scientific event.

All612 original pilot targets stay represented. Exact byte-path/Unicode alias
counts are distinct from word probabilities. Four fixed original word targets
measure at most16 native paths each in their unchanged token contexts. This
cannot establish infeasibility of a different algorithm or admit scoped P7.

DESIGN CHECK: LESSONS 3-5 read for this admission on 2026-10-19. NULL and
ALTERNATIVE scientific effects do not select targets or change these checks.
Changed source, decoder disagreement, canonical loss error above 1e-4, missing
coverage or nonfinite losses refuse. Incomplete alias/path enumeration and
context overflow remain explicit; neither is assigned zero omitted mass.
Complete fresh native replay is required. Passing admits only this diagnostic,
not a shared word probability, scientific effect, or full P7 execution.
"""
from __future__ import annotations
from pathlib import Path
import math
import time
import unicodedata

from .timing_census import read,filehash
from .timing_p6 import write_equal,gzip_equal,gzread,progress
from .timing_stats import bind,check_binding
from .timing_p7_hybrid_pilot import reference,CONFIG as REFERENCE_CONFIG
from .timing_p7_batched import prepare
from .timing_p7_admitted import load_model
from .timing_word_paths import byte_vocabulary,inverse_casefold,BytePaths,describe_word,native_path_cost

CONFIG=dict(phase='native_word_event_diagnostic',alias_limit=256,native_targets=4,native_paths_per_target=16)
FORECAST_SECONDS=300
CAP_SECONDS=900


def source(inputs,config):
    if config!=CONFIG or set(inputs)!={'original_pilot_complete'}:raise ValueError('exact native diagnostic inputs/config required')
    complete=Path(inputs['original_pilot_complete']).resolve()
    if complete.name!='COMPLETE.json':raise ValueError('original pilot completion path required')
    binding,units,manifest,_=reference(dict(original_pilot=str(complete.parent)),REFERENCE_CONFIG)
    rows=[dict(domain=unit['domain'],**row,expected=expected) for unit in units for row,expected in zip(unit['rows'],unit['expected'])]
    if len(rows)!=612:raise ValueError('original612target population differs')
    binding.update(config=config,complete_sha256=filehash(complete),unicode_version=unicodedata.unidata_version)
    vocabulary=read(Path(manifest['model_path'])/'vocab.json')
    return binding,rows,manifest,byte_vocabulary(vocabulary)


def native_selection(rows):
    # First and last word in each original domain: no performance/answer selection.
    selected=[]
    for domain in sorted({r['domain'] for r in rows}):
        candidates=[i for i,r in enumerate(rows) if r['domain']==domain and r['is_word']]
        if not candidates:raise ValueError('pilot domain has no word targets')
        selected.extend([candidates[0],candidates[-1]])
    if len(set(selected))!=4:raise ValueError('native diagnostic four-target coverage differs')
    return selected


def validate_decoder(tokenizer,pieces):
    """Independent native tokenizer agreement for every nonspecial token."""
    for index,piece in pieces.items():
        if tokenizer.decode([index],skip_special_tokens=False,clean_up_tokenization_spaces=False)!=piece.decode('utf8',errors='replace'):
            raise ValueError('native byte decoder differs from tokenizer')
    return len(pieces)


def structure(row,paths,inverse,config):
    identity=dict(domain=row['domain'],index=row['index'],is_word=row['is_word'])
    if not row['is_word']:
        return dict(identity,status='retained_nonword',reason='Punctuation has a different TOKEN event; no word-probability substitution')
    return dict(identity,status='byte_path_diagnostic',**describe_word(row['target'],paths,inverse,config['alias_limit']))


def cost_design(row,tokenizer,paths,pieces,config):
    item=prepare(tokenizer,row['prefix'],row['target'])
    positions=item['positions'];canonical=[item['ids'][p] for p in positions]
    if positions!=list(range(positions[0],len(item['ids']))):raise ValueError('pilot target token range is not a terminal suffix')
    payload=b''.join(pieces[t] for t in canonical)
    if not payload.endswith(row['target'].encode('utf8')):raise ValueError('canonical token bytes do not end in exact target spelling')
    # Every sampled segmentation spells the EXACT ORIGINAL native token bytes,
    # including any native token overlap into the supplied visible prefix.
    descriptions=paths.describe(payload,limit=config['native_paths_per_target'])
    choices=[canonical]+[p for p in descriptions['paths'] if p!=canonical]
    choices=choices[:config['native_paths_per_target']]
    prefix=item['ids'][:positions[0]];valid=[];overflow=[]
    for p in choices:
        (valid if len(prefix)+len(p)<=1024 else overflow).append(p)
    return dict(prefix_ids=prefix,paths=valid,overflow_paths=overflow,
        total_exact_spelling_paths=descriptions['path_count'],sample_complete=len(choices)==descriptions['path_count'],
        original_prefix_tokens_dropped=item['dropped'],canonical_tokens=canonical,
        canonical_expected_nll=row['expected']['native_token_nll'])


def check_cost(cost,design):
    values=cost['paths']
    if [r['tokens'] for r in values]!=design['paths']:raise ValueError('native cost path identities differ')
    if any(not r['native_token_nll'] or len(r['native_token_nll'])!=len(r['tokens']) or
           any(not math.isfinite(v) or v<0 for v in r['native_token_nll']) for r in values):raise ValueError('invalid native diagnostic loss')
    actual=next(r['native_token_nll'] for r in values if r['tokens']==design['canonical_tokens'])
    expected=design['canonical_expected_nll']
    if len(actual)!=len(expected) or max(abs(a-b) for a,b in zip(actual,expected))>1e-4:
        raise ValueError('original canonical native loss changed')


def result(structures,costs):
    words=[r for r in structures if r['is_word']]
    return dict(instrument_only=True,scientific_admission=False,common_event_admitted=False,main_admitted=False,
        pilot_targets=len(structures),word_targets=len(words),retained_nonwords=len(structures)-len(words),
        casefold_alias_enumerations_incomplete=sum(not r['alias_enumeration_complete'] for r in words),
        native_paths_measured=sum(len(c['cost']['paths']) for c in costs),
        context_overflow_paths_retained=sum(len(c['design']['overflow_paths']) for c in costs),
        cost_scope='Direct native teacher-forced path samples only; no projection to full common-event inference or impossibility claim',
        unresolved=['Casefold-equivalence event versus writer-specific P6 unknown event requires owner review',
            'Regex TOKEN ignores whitespace/underscore and handles punctuation/internal apostrophes; token space markers alone do not match it',
            'Boundary-crossing tokens and alternate tokenizations require complete marginalization plus start normalization',
            'No unbounded omitted-prefix/alias/path mass has been set to zero'])


def execute(output:Path,inputs:dict,config:dict)->dict:
    started=time.monotonic();output=Path(output);output.mkdir(parents=True,exist_ok=True)
    binding,rows,manifest,pieces=source(inputs,config);write_equal(output/'SOURCE.json',binding)
    timing=output/'ACTIVE_TIME.json';previous=float(read(timing)['seconds']) if timing.exists() else 0.
    elapsed=lambda:previous+time.monotonic()-started
    paths=BytePaths(pieces);inverse=inverse_casefold();structures=[]
    for i,row in enumerate(rows):
        value=structure(row,paths,inverse,config);gzip_equal(output/'structure'/(str(i).zfill(3)+'.json.gz'),value);structures.append(value)
        progress(timing,dict(seconds=elapsed()))
        if elapsed()>CAP_SECONDS:raise RuntimeError('native diagnostic cumulative cap exceeded')
        if (output/'YIELD_REQUEST.json').exists():return dict(status='yielded',phase='structure',completed=i+1,total=612)
    model,tokenizer,torch=load_model(manifest);validate_decoder(tokenizer,pieces);costs=[]
    for number,index in enumerate(native_selection(rows)):
        design=cost_design(rows[index],tokenizer,paths,pieces,config);dest=output/'cost'/(str(number)+'.json.gz')
        if dest.exists():value=gzread(dest)
        else:
            cost=native_path_cost(model,torch,design['prefix_ids'],design['paths']);check_cost(cost,design)
            value=dict(row_index=index,design=design,cost=cost);gzip_equal(dest,value)
        if value['row_index']!=index or value['design']!=design:raise ValueError('native diagnostic checkpoint changed')
        check_cost(value['cost'],design);costs.append(value)
        progress(timing,dict(seconds=elapsed()))
        if elapsed()>CAP_SECONDS:raise RuntimeError('native diagnostic cumulative cap exceeded')
        if number==0 and not (output/'FIRST_TENTH.json').exists():
            write_equal(output/'FIRST_TENTH.json',dict(completed_native_targets=1,total_native_targets=4,
                projected_cpu_seconds=2*(elapsed()+3*value['cost']['seconds']),forecast_cpu_seconds=FORECAST_SECONDS,
                method='All source/structure/model-load time plus three more first-target path samples; doubled for complete fresh verification; diagnostic-only projection'))
        if (output/'YIELD_REQUEST.json').exists():return dict(status='yielded',phase='native_paths',completed=number+1,total=4)
    report=result(structures,costs);write_equal(output/'PRIMARY.json',report)
    artifacts=['SOURCE.json','PRIMARY.json']+[p.relative_to(output).as_posix() for folder in ('structure','cost') for p in sorted((output/folder).glob('*.gz'))]
    if (output/'TIMING_BINDINGS.json').exists():check_binding(output,inputs,config)
    else:bind(output,inputs,config,artifacts)
    return report


def verify(output:Path,inputs:dict,config:dict)->dict:
    started=time.monotonic();output=Path(output);check_binding(output,inputs,config)
    binding,rows,manifest,pieces=source(inputs,config)
    if binding!=read(output/'SOURCE.json'):raise ValueError('native diagnostic source changed')
    paths=BytePaths(pieces);inverse=inverse_casefold();structures=[]
    for i,row in enumerate(rows):
        value=structure(row,paths,inverse,config)
        if value!=gzread(output/'structure'/(str(i).zfill(3)+'.json.gz')):raise ValueError('native structure failed source reconstruction')
        structures.append(value)
    model,tokenizer,torch=load_model(manifest);validate_decoder(tokenizer,pieces);saved=[];maximum=0.
    for number,index in enumerate(native_selection(rows)):
        value=gzread(output/'cost'/(str(number)+'.json.gz'));design=cost_design(rows[index],tokenizer,paths,pieces,config)
        if design!=value['design']:raise ValueError('native path design changed')
        fresh=native_path_cost(model,torch,design['prefix_ids'],design['paths']);check_cost(fresh,design);check_cost(value['cost'],design)
        for a,b in zip(fresh['paths'],value['cost']['paths']):
            maximum=max(maximum,max(abs(x-y) for x,y in zip(a['native_token_nll'],b['native_token_nll'])))
        saved.append(value)
    if maximum>1e-4 or result(structures,saved)!=read(output/'PRIMARY.json'):raise ValueError('native diagnostic replay differs')
    total=float(read(output/'ACTIVE_TIME.json')['seconds'])+time.monotonic()-started
    if total>CAP_SECONDS:raise RuntimeError('native diagnostic cumulative verification cap exceeded')
    return dict(verified=True,max_native_loss_error=maximum,cumulative_seconds=total,scientific_admission=False,common_event_admitted=False)
