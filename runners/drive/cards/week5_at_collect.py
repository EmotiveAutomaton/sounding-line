"""AT complete-model bank assembler; no selection from unfinished models.

DESIGN CHECK: LESSONS3--5, 2026-11-07. Complete source roster, all declared
batches and verified model identities must agree under every scientific state.
Missing batches refuse; unsupported timings are counted before common-row fits.
"""
from pathlib import Path
from collections import Counter
import math
from .week5_at_source import authenticate
from .timing_census import read,filehash
from .timing_p6 import gzread,gzip_equal,write_equal


def produce(output,inputs,config,verifying=False):
    if set(inputs) not in ({'source_root','bank_manifest'},{'source_root','bank_manifest','covariates_root'}) or config.get('context','final') not in ('final','at_typing'):
        raise ValueError('Exact collection source and context required')
    source=authenticate(inputs['source_root'])/'output';context=config.get('context','final')
    bank=read(inputs['bank_manifest']);expected=[r for r in read(source/'BATCHES.json') if r['context']==context]
    allrows=[]
    for entry in read(source/'INDEX.json'):
        path=source/entry['file']
        if filehash(path)!=entry['sha256']:raise ValueError('Source word bank changed')
        allrows.extend(gzread(path)['rows'])
    roster={r['row_key']:r for r in allrows};scored={}
    if len(roster)!=len(allrows):raise ValueError('Duplicate row identity')
    for model,paths in sorted(bank.items()):
        if set(paths)!=set(r['file'] for r in expected):raise ValueError('Model bank is incomplete')
        values={}
        for chunk in expected:
            root=authenticate(paths[chunk['file']]);data=root/'output'
            summary=read(data/'SUMMARY.json')
            if summary['context']!=context or summary['model']!=model:raise ValueError('Model/context identity differs')
            sourcechunk=source/chunk['file']
            if filehash(sourcechunk)!=chunk['sha256']:raise ValueError('Source chunk changed')
            wanted=[r['row_key'] for r in gzread(sourcechunk)]
            index=read(data/'INDEX.json')
            if [r['row_key'] for r in index]!=wanted:raise ValueError('Model chunk row coverage differs')
            for item in index:
                p=data/item['file']
                if filehash(p)!=item['sha256']:raise ValueError('Word score changed')
                value=read(p)
                if 'slot' in item:value=value['values'][item['slot']]
                if item['row_key'] in values:raise ValueError('Duplicated scored row')
                values[item['row_key']]=value['score']
        scored[model]=values
    if not scored:raise ValueError('No complete model bank')
    keys=set(next(iter(scored.values())))
    if any(set(v)!=keys for v in scored.values()):raise ValueError('Model support differs')
    covariates={}
    if 'covariates_root' in inputs:
        covroot=authenticate(inputs['covariates_root'])/'output'
        for item in read(covroot/'INDEX.json'):
            path=covroot/item['file']
            if filehash(path)!=item['sha256']:raise ValueError('Raw timing controls changed')
            covariates.update(gzread(path))
    out=[];counts=Counter()
    for key in sorted(keys):
        row=roster[key];counts['scored_words']+=1
        if not row['timing_supported']:
            counts['unsupported_timing']+=1;continue
        if any(row.get(k) is None or not math.isfinite(row[k]) for k in ('population_surprisal','log_frequency','pause_seconds','fast')):
            counts['unsupported_covariate']+=1;continue
        publicless={k:v for k,v in row.items() if k not in ('target','final_prefix','at_typing_prefix')}
        if covariates:
            if key not in covariates:counts['unsupported_timing_control']+=1;continue
            publicless.update(covariates[key])
        out.append(dict(publicless,scores={m:v[key] for m,v in scored.items()}))
    summary=dict(context=context,models=sorted(bank),counts=dict(counts),supported_words=len(out),
                 supported_writers=len({r['writer'] for r in out}),scientific_admission=False)
    root=Path(output)
    if verifying:
        if gzread(root/'ROWS.json.gz')!=out or read(root/'SUMMARY.json')!=summary:
            raise ValueError('Complete collection replay differs')
        return dict(verified=True,complete_collection_replay=True)
    gzip_equal(root/'ROWS.json.gz',out);write_equal(root/'SUMMARY.json',summary)
    return dict(status='complete',models=len(bank))


def execute(output,inputs,config):return produce(output,inputs,config)
def verify(output,inputs,config):return produce(output,inputs,config,True)
