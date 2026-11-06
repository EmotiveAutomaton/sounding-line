"""CA1.s1 whole-annotator inputs, including every approved CA3 recipient.

DESIGN CHECK: LESSONS 3-5 reread 2026-11-04. NULL and ALTERNATIVE keep
the same source-membership sample and original prompt/conversation splits.
No choice, explanation value, fitted direction or cost outcome selects a person.
Missing mandatory members, changed producers, duplicate comparisons or altered
texts refuse. Original row indices and the full prompt-cluster vocabulary stay.
"""
from collections import Counter
import gzip
import json
from pathlib import Path
import numpy as np
from runners.stage14.common import read, filehash, digest
from .week3_alignment_inputs import Lines, hashed
from .week3_alignment_features import source
from .timing_pmap_source import completed
from .timing_p6 import write_equal
from .batch_runtime import check_files


def configuration(mode):
    if mode not in ('constructed','full'):
        raise ValueError('Unknown input mode')
    return dict(card='CA1.s1-inputs',mode=mode,seed=20261102,mandatory=836,additional=200)


def select(population, mandatory, additional):
    population, mandatory = sorted(population), sorted(mandatory)
    if len(set(population))!=len(population) or len(set(mandatory))!=len(mandatory):
        raise ValueError('Duplicate identity')
    if not set(mandatory)<=set(population):
        raise ValueError('Mandatory recipient absent from original source')
    others=sorted(set(population)-set(mandatory))
    if type(additional) is not int or additional<=0 or additional>len(others):
        raise ValueError('Invalid additional sample size')
    random=sorted(np.random.default_rng(20261102).permutation(others).tolist()[:additional])
    return dict(mandatory=mandatory,random=random,selected=sorted(mandatory+random),seed=20261102)


def subset(rows, splits, membership):
    chosen=set(membership['selected']); keep=[]; original_indices=[]
    for i,row in enumerate(rows):
        if row['writer'] in chosen:
            keep.append(dict(row,original_comparison_index=i));original_indices.append(i)
    if {r['writer'] for r in keep}!=chosen:
        raise ValueError('Selected person lost all comparisons')
    keys=[(r['writer'],r['conversation'],r['turn']) for r in keep]
    if len(set(keys))!=len(keys):
        raise ValueError('Duplicate comparison key')
    ids={i for r in keep for i in r['candidates']}
    # The original fallback clustering sees every original prompt, so a sample
    # must not quietly redefine its fifty-cluster reference population.
    ids.update(splits['prompt_text_indices'].values())
    small=dict(writer_splits={w:splits['writer_splits'][w] for w in sorted(chosen)},
               prompt_text_indices=splits['prompt_text_indices'])
    return keep,small,sorted(ids),original_indices


def known_answers():
    rows=[dict(writer=f'w{w}',conversation=f'c{w}-{j}',turn=1,choice=j%4,
               candidates=[2*w,2*w+1],prompt='p',half=j%2) for w in range(10) for j in range(4)]
    splits=dict(writer_splits={f'w{w}':{'fixture':True} for w in range(10)},prompt_text_indices={'p':99})
    selected=select(list(splits['writer_splits']),['w2','w4','w7'],2)
    kept,small,ids,indices=subset(rows,splits,selected)
    if len(kept)!=20 or 99 not in ids or len(small['writer_splits'])!=5:
        raise ValueError('Known complete-unit selection failed')
    if any({k:v for k,v in row.items() if k!='original_comparison_index'}!=rows[i] for row,i in zip(kept,indices)):
        raise ValueError('Original split or choice changed')
    if select(list(reversed(list(splits['writer_splits']))),['w7','w4','w2'],2)!=selected:
        raise ValueError('Sample depends on ordering')
    return dict(verified=True,mandatory_preserved=True,whole_units=True,original_indices_preserved=True,
                global_prompt_reference_preserved=True)


def load(inputs):
    if set(inputs)!={'prepared_summary','prepared_complete','supported_summary','supported_complete'}:
        raise ValueError('Exact completed input bundle required')
    prepared,root,rows,splits=source(inputs)
    for name in ('prepared_complete','supported_complete'):
        plan=read(Path(inputs[name]).resolve().parent/'PLAN.json');check_files(plan['pins'])
    summary=Path(inputs['supported_summary']).resolve()
    completed(inputs['supported_complete'],summary);support=read(summary)
    if support['card']!='CA3.supported-inputs' or support['supported_annotators']!=836:
        raise ValueError('Approved supported population differs')
    for name,h in support['output_hashes'].items():
        if filehash(summary.parent/name)!=h:raise ValueError('Supported membership changed')
    mandatory=[r['writer'] for r in read(summary.parent/'PRIVATE_SUPPORTED_REFIT_TARGETS.json')]
    if len(mandatory)!=836:raise ValueError('Mandatory count differs')
    membership=select(list(splits['writer_splits']),mandatory,200)
    return prepared,root,rows,splits,membership


def calculate(output,inputs,config,saving):
    if config!=configuration(config.get('mode')):raise ValueError('Frozen sample configuration required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    if config['mode']=='constructed':
        if inputs:raise ValueError('No human data in constructed input checks')
        return known_answers()
    prior,root,rows,splits,membership=load(inputs)
    kept,small,ids,indices=subset(rows,splits,membership)
    manifest=dict(membership,original_comparison_indices=indices,source_text_indices=ids,
                  original_population=len(splits['writer_splits']),sample_population=len(membership['selected']))
    for name,value in [('SPLITS.json',small),('PRIVATE_SAMPLE.json',manifest)]:
        if saving:write_equal(output/name,value)
        elif read(output/name)!=value:raise ValueError('Sample source manifest differs')
    out=Lines(output/'COMPARISONS.jsonl.gz',saving)
    try:
        for row in kept:out.append(row)
    finally:comparison_receipt=out.close()
    texts=Lines(output/'TEXTS.jsonl.gz',saving);wanted=set(ids);seen=set()
    try:
        with gzip.open(root/'TEXTS.jsonl.gz','rt',encoding='utf8') as stream:
            for line in stream:
                row=json.loads(line)
                if row['index'] not in wanted:continue
                if row['index'] in seen or hashed(row['text'])!=row['sha256']:
                    raise ValueError('Original text changed or duplicated')
                seen.add(row['index']);texts.append(row)
    finally:text_receipt=texts.close()
    if seen!=wanted:raise ValueError('Required source text missing')
    # Recompute uncompressed receipts from the actual saved streams too.
    for name,expected in [('COMPARISONS.jsonl.gz',comparison_receipt),('TEXTS.jsonl.gz',text_receipt)]:
        verify=Lines(output/'unused',False)
        with gzip.open(output/name,'rt',encoding='utf8') as stream:
            for line in stream:verify.append(json.loads(line))
        if verify.close()!=expected:raise ValueError('Saved stream differs from complete source reconstruction')
    return dict(card='CA1-inputs',variant='CA1.s1',state='inputs_ready',
        input_hashes={k:filehash(v) for k,v in inputs.items()},config=config,
        original_annotators=2979,sample_annotators=len(membership['selected']),mandatory_annotators=836,random_annotators=200,
        split_supported_annotators=len(membership['selected']),comparisons=comparison_receipt,texts=text_receipt,
        original_texts=prior['texts']['records'],all_original_prompts=len(splits['prompt_text_indices']),
        permutation_route=prior['permutation_route'],sample_scope=True,scientific_admission=False,
        output_hashes={n:filehash(output/n) for n in ['COMPARISONS.jsonl.gz','TEXTS.jsonl.gz','SPLITS.json','PRIVATE_SAMPLE.json']},
        scope='Whole annotators; mandatory support-selected group and separate seeded random group; original splits and global prompt reference unchanged')


def execute(output,inputs,config):
    value=calculate(output,inputs,config,True);write_equal(Path(output)/'SUMMARY.json',value);return value


def verify(output,inputs,config):
    value=calculate(output,inputs,config,False)
    if read(Path(output)/'SUMMARY.json')!=value:raise ValueError('Complete sample source replay differs')
    return dict(verified=True,full_fresh_source_replay=True,whole_annotators=True)
