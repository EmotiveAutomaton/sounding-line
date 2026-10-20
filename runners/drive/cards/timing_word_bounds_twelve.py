"""Twelve-prefix capacity refinement on the same four fixed P7 pilot words.

Separate immutable successor: only the work cap changes from eight to twelve.
Original numerical functions, precision, events, inputs and context remain.
All earlier costs count toward the unchanged diagnostic ceiling.

DESIGN CHECK: LESSONS 3-5 reread 2026-10-19. NULL/ALTERNATIVE outcomes cannot
select examples, context, nodes or precision. Changed source, tokenizer bytes,
nonpositive native weights, missing oracle rows or fresh replay disagreement
refuse. Wide intervals remain unresolved; they neither admit scores nor imply
an impossible algorithm. This is the existing P7 common-event engineering rung,
not a new scientific comparison. Original completed instrumentation is immutable.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import time

from . import timing_word_event_native as original
from .timing_p7_batched import prepare
from .timing_p7_admitted import load_model
from .timing_p6 import write_equal, gzip_equal, gzread, progress
from .timing_census import read
from .timing_stats import bind, check_binding
from .timing_text import TOKEN
from .timing_word_bounds import next_word_bounds

CONFIG = dict(phase='bounded_native_word_events',targets=4,max_nodes_per_event=12,tolerance_nats=1e-4)


def source(inputs, config):
    if config != CONFIG:
        raise ValueError('exact bounded diagnostic configuration required')
    binding, rows, manifest, pieces = original.source(inputs, original.CONFIG)
    binding = dict(binding, bounds_config=config)
    return binding, rows, manifest, pieces


def design(row, tokenizer, pieces):
    text = row['prefix'] + row['target']
    matches = list(TOKEN.finditer(text))
    if not matches or matches[-1].span() != (len(row['prefix']), len(text)):
        raise ValueError('original target is not one exact terminal TOKEN')
    item = prepare(tokenizer, row['prefix'], row['target'])
    positions = item['positions']
    if positions != list(range(positions[0], len(item['ids']))):
        raise ValueError('target is not a terminal native suffix')
    payload = b''.join(pieces[i] for i in item['ids'][positions[0]:])
    target = row['target'].encode('utf8')
    if not payload.endswith(target):
        raise ValueError('native bytes do not contain exact target suffix')
    return dict(prefix_ids=item['ids'][:positions[0]], required_hex=payload[:-len(target)].hex(),
                target_folded=row['target'].casefold(), dropped=item['dropped'],
                context_rule='Original fixed canonical token prefix; no alternative-history marginal or extra crop')


def evaluate(output, model, tokenizer, torch, pieces, rows, verify=False):
    results = []
    for number, index in enumerate(original.native_selection(rows)):
        fixed = design(rows[index], tokenizer, pieces)
        cache = {}
        def oracle(path):
            if path in cache:
                return cache[path]
            ids = fixed['prefix_ids'] + list(path)
            if not ids or len(ids) > 1024:
                raise ValueError('native context exceeded, without permission to crop')
            key = hashlib.sha256(json.dumps(list(path)).encode('ascii')).hexdigest()
            dest = output/'oracle'/str(number)/(key+'.json.gz')
            tensor = torch.tensor([ids],dtype=torch.long,device='cpu')
            with torch.inference_mode():
                logits = model(input_ids=tensor,use_cache=False).logits[0,-1].double()
                weights = torch.exp(logits-logits.max())
            if not bool(torch.isfinite(weights).all()) or not bool((weights>0).all()) or len(weights)!=len(pieces)+1:
                raise ValueError('invalid or underflowed complete native oracle')
            values = weights.tolist()
            evidence = dict(path=list(path),weights=values)
            if verify:
                if evidence != gzread(dest):
                    raise ValueError('complete fresh native oracle replay differs')
            else:
                gzip_equal(dest,evidence)
            cache[path] = dict(enumerate(values))
            return cache[path]
        value = next_word_bounds(oracle,pieces,tokenizer.eos_token_id,
            bytes.fromhex(fixed['required_hex']),fixed['target_folded'],
            max_nodes=CONFIG['max_nodes_per_event'],max_depth=1025-len(fixed['prefix_ids']),
            tolerance_nats=CONFIG['tolerance_nats'])
        result = dict(row_index=index,design=fixed,bounds=value,unique_native_forwards=len(cache))
        dest = output/'targets'/(str(number)+'.json')
        if verify:
            if result != read(dest):
                raise ValueError('event reconstruction differs')
        else:
            write_equal(dest,result)
            progress(output/'PROGRESS.json',dict(completed=number+1,total=4,phase='bounded_event_validation'))
        results.append(result)
        if not verify and (output/'YIELD_REQUEST.json').exists():
            return dict(status='yielded',phase='bounded_event_validation',completed=number+1,total=4)
    return dict(instrument_only=True,scientific_admission=False,main_admitted=False,
                targets=len(results),native_forwards=sum(r['unique_native_forwards'] for r in results),
                tight_targets=sum(r['bounds']['conditional']['point_score_admitted'] for r in results),
                precision_nats=CONFIG['tolerance_nats'],
                target_intervals_retained=True,
                scope='Next casefolded original TOKEN after observed overlap bytes, conditional on original canonical history; complete numerical native-token oracle, residual frontier/context mass retained',
                corpus_admission='Not tested; no D33/P7 scientific score or full-corpus forecast')


def execute(output,inputs,config):
    started=time.monotonic();output=Path(output);output.mkdir(parents=True,exist_ok=True)
    binding,rows,manifest,pieces=source(inputs,config)
    write_equal(output/'SOURCE.json',binding)
    model,tokenizer,torch=load_model(manifest)
    original.validate_decoder(tokenizer,pieces)
    result=evaluate(output,model,tokenizer,torch,pieces,rows)
    if result.get('status')=='yielded':
        progress(output/'ACTIVE_TIME.json',dict(seconds=time.monotonic()-started))
        return result
    write_equal(output/'PRIMARY.json',result)
    artifacts=['SOURCE.json','PRIMARY.json']+[p.relative_to(output).as_posix() for folder in ('oracle','targets') for p in sorted((output/folder).rglob('*')) if p.is_file()]
    if (output/'TIMING_BINDINGS.json').exists():
        check_binding(output,inputs,config)
    else:
        bind(output,inputs,config,artifacts)
    progress(output/'ACTIVE_TIME.json',dict(seconds=time.monotonic()-started))
    return result


def verify(output,inputs,config):
    started=time.monotonic();output=Path(output);check_binding(output,inputs,config)
    binding,rows,manifest,pieces=source(inputs,config)
    if binding!=read(output/'SOURCE.json'):
        raise ValueError('original source binding changed')
    model,tokenizer,torch=load_model(manifest)
    original.validate_decoder(tokenizer,pieces)
    result=evaluate(output,model,tokenizer,torch,pieces,rows,verify=True)
    if result!=read(output/'PRIMARY.json'):
        raise ValueError('complete bounded-event report differs')
    return dict(verified=True,full_oracle_and_event_replay=True,
                cumulative_seconds=read(output/'ACTIVE_TIME.json')['seconds']+time.monotonic()-started,
                scientific_admission=False,main_admitted=False)
