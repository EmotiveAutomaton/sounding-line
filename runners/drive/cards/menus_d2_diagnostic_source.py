"""Canonical targets and exact original D2 split/visibility authentication.

DESIGN CHECK: LESSONS3-5. A source discrepancy invalidates this successor;
it cannot be an exclusion selected after outcomes. Canonical offer identities,
text visibility, original partition counts/cutoffs/heldout keys all must agree.
Only selected targets change; no old coefficient or probability is reused.
"""
from collections import Counter,defaultdict
import copy
import hashlib
import json
from pathlib import Path
import numpy as np

from . import menus_d2 as original
from . import menus_p4 as partitions
from . import menus_canonical_selection as canonical
from .menus_io import read,sha256,assert_equal,input_hashes
from runners.stage14.common import digest

INPUTS={'sessions','records','vectors','content_complete','p8','p8_complete',
        'visibility','selection_reader','selection_complete','original_complete'}


def output_receipt(path,names):
    path=Path(path);receipt=read(path)
    if receipt.get('status')!='COMPLETE':raise ValueError('incomplete source')
    for name in names:
        if receipt['outputs'].get(name)!=sha256(path.parent/name):
            raise ValueError('completed source identity differs')
    return receipt


def visibility(row,feature,ledger):
    scopes=[]
    for index,text,role in [(feature['context'],row['document'],'context')]+[
            (index,text,'suggestion') for index,text in zip(feature['options'],row['menu'])]:
        if not isinstance(index,int) or not 0<=index<len(ledger):raise ValueError('visibility index invalid')
        scope=ledger[index]
        if scope['role']!=role or scope['text_sha256']!=digest(text):
            raise ValueError('visibility text/role differs')
        full,used=scope['full_tokens'],scope['used_tokens']
        if (not isinstance(full,int) or isinstance(full,bool) or full<0 or used!=min(full,254)
                or scope['truncated']!=(full>254)
                or scope['first_native_token']!=(max(0,full-254) if role=='context' else 0)):
            raise ValueError('visibility truncation contract differs')
        scopes.append(scope)
    return dict(option_truncated=sum(s['truncated'] for s in scopes[1:]),
                context_truncated=bool(scopes[0]['truncated']))


def load(inputs):
    if set(inputs)!=INPUTS:raise ValueError('D2 diagnostic input roster differs')
    original.authenticated(inputs);audit=canonical.load(inputs)
    content=Path(inputs['content_complete']);relative=Path(inputs['visibility']).resolve().relative_to(content.parent.resolve()).as_posix()
    output_receipt(content,[relative])
    sessions=read(inputs['sessions']);corrected=copy.deepcopy(sessions)
    records=read(inputs['records']);features={r['key']:r for r in records};ledger=read(inputs['visibility'])
    vectors=np.load(inputs['vectors'],allow_pickle=False)
    if len(ledger)!=len(vectors):raise ValueError('visibility/vector coverage differs')
    with Path(inputs['p8']).open(encoding='utf8') as stream:producer=[json.loads(line) for line in stream]
    by_key=defaultdict(list)
    for item in producer:by_key[item['key']].append(item)
    rows=[];census=Counter();prepared_eligible=set();canonical_eligible=set()
    for session in corrected:
        for row in session['rows']:
            proof,chosen=canonical.join(audit,row,by_key[row['key']])
            feature=features[row['key']]
            if len(feature['options'])!=len(row['menu']):raise ValueError('filtered content option')
            scope=visibility(row,feature,ledger);size=len(row['menu'])
            oldmatches=[i for i,text in enumerate(row['menu']) if text==row['inserted']]
            oldeligible=row['handling'] in ('accept','edit') and size>=2 and len(oldmatches)==1
            if oldeligible:prepared_eligible.add(row['key'])
            if chosen is not None:
                row['inserted']=row['menu'][chosen]
                if size>=2:canonical_eligible.add(row['key'])
            auditrow=dict(key=row['key'],writer=row['writer'],session=row['session'],options=size,
                canonical_choice=chosen,prepared_positions=proof['prepared_positions'],
                choice_changed=proof['index_status']=='proven_disjoint_choice',eligible=row['key'] in canonical_eligible,
                original_option_ids=proof['canonical_option_ids'],raw_source_sha256=proof['raw_source_sha256'],
                canonical_sha256=proof['canonical_sha256'],**scope)
            rows.append(auditrow);census['menus']+=1;census['options']+=size
            census['menus_with_truncated_option']+=scope['option_truncated']>0
            census['truncated_options']+=scope['option_truncated'];census['truncated_contexts']+=scope['context_truncated']
            census['canonical_choice_changed']+=auditrow['choice_changed']
    if prepared_eligible!=canonical_eligible:raise ValueError('canonical labels change original eligible population')
    cases,excluded=original.assemble(corrected,records,vectors,producer)
    if set(cases)!=canonical_eligible:raise ValueError('canonical unique text extraction differs')
    splits,unsupported=original.chronological_partitions(sessions)
    oldroot=Path(inputs['original_complete']).parent
    receipt=output_receipt(inputs['original_complete'],['PLAN.json','output/SUMMARY.json'])
    plan=read(oldroot/'PLAN.json');summary=read(oldroot/'output/SUMMARY.json')
    if not receipt.get('fresh_process_verified'):raise ValueError('original D2 lacks completed fresh verification')
    for key in ('sessions','records','vectors','p8','p8_complete','content_complete'):
        if Path(plan['inputs'][key]).resolve()!=Path(inputs[key]).resolve() or plan['pins'].get(str(Path(inputs[key]).resolve()))!=sha256(inputs[key]):
            raise ValueError('original D2 input binding differs')
    assert_equal(plan['config'],original.CONFIG)
    for module in (original,partitions):
        path=str(Path(module.__file__).resolve())
        if plan['pins'].get(path)!=sha256(path):raise ValueError('original model/partition source differs')
    eligible={};partition_rows=[];expected_names=set()
    for writer in sorted(splits):
        split=original.recipient_split(writer,splits)
        if split['reason']:continue
        groups=[[r['key'] for s in split[name] for r in s['rows'] if r['key'] in cases]
                for name in ('train','calibration','test')]
        name='recipients/'+hashlib.sha256(writer.encode()).hexdigest()[:24]+'.json'
        expected_names.add(name);path=oldroot/'output'/name
        if summary['recipient_hashes'].get(name)!=sha256(path) or receipt['outputs'].get('output/'+name)!=sha256(path):
            raise ValueError('original recipient identity differs')
        old=read(path)['result']
        if any(not group for group in groups):
            if old is not None:raise ValueError('original nonempty choice support differs')
            continue
        if old is None:raise ValueError('original completed choice support differs')
        for key,actual in zip(('train_count','calibration_count','test_count'),map(len,groups)):
            if old[key]!=actual:raise ValueError('original partition count differs')
        for key in ('cutoff','test_cutoff'):
            if old[key]!=split[key]:raise ValueError('original partition cutoff differs')
        if [r['key'] for r in old['arms']['primary']['predictions']]!=groups[2]:
            raise ValueError('original heldout membership differs')
        edges=np.quantile([cases[k]['dissimilarity'] for k in groups[0]],[.2,.4,.6,.8]).tolist()
        assert_equal(old['edges'],edges)
        eligible[writer]=split
        partition_rows.append(dict(writer=writer,cutoff=split['cutoff'],test_cutoff=split['test_cutoff'],
            groups={name:group for name,group in zip(('train','calibration','test'),groups)},
            sessions={name:[s['session'] for s in split[name]] for name in ('train','calibration','test')}))
    if expected_names!=set(summary['recipient_hashes']):raise ValueError('original recipient roster differs')
    selected=[r for r in rows if r['eligible']]
    census.update(eligible_menus=len(selected),eligible_menus_with_truncated_option=sum(r['option_truncated']>0 for r in selected),
        eligible_truncated_options=sum(r['option_truncated'] for r in selected),
        eligible_choice_changed=sum(r['choice_changed'] for r in selected),filtered_options=0,menus_with_filtered_options=0)
    return dict(cases=cases,splits=eligible,rows=rows,partitions=partition_rows,
        census=dict(census),exclusions=dict(menu=excluded,session=unsupported),identity=input_hashes(inputs),
        scope='Complete canonical offers preserved. Embeddings retain original first254 suggestion tokens/last254 context tokens; lexical/length covariates retain original text. Counts do not describe hidden producer-internal candidate filtering.')
