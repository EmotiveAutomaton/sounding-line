"""GO1 fixed public task: identifiers and source section offsets, never text.

DESIGN CHECK: EX3/T and original GO1 source/allocation. Exact verified task,
source bytes, author hashing and subtree removal are mandatory; a later model
or support mask cannot alter the export's roster.
"""
from pathlib import Path
import hashlib
import json
import math
import re
import time
from . import week5_engine_export_io as common
from . import week5_go1_two_reader as go1
from . import week5_go1_pipeline_v2 as pipeline
from . import week5_go as core

MODULE='runners.drive.cards.week5_ex3'
GO1_MODULE='runners.drive.cards.week5_go1_two_reader'


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def spans(text,repository,salt,expected):
    row,reason=core.parse_document(text,repository,salt)
    if row is None or any(row[key]!=expected[key] for key in row):
        raise ValueError('Pinned source no longer reproduces exact GO1 document')
    header,parts=core.sections(text);lines=text.splitlines();ends=text.splitlines(keepends=True)
    offsets=[0]
    for line in ends:offsets.append(offsets[-1]+len(line))
    if len(offsets)!=len(lines)+1:raise ValueError('Source line/code-point map differs')
    blocks=[]
    excluded=[(p['start'],p['subtree_end']) for p in parts if p['normalized'] in
        ('motivation','copyright','copyright and license','copyright and licence')]
    for part in parts:
        start=part['start'];markdown=bool(re.match(r'^(#{1,6})\s+(.+?)\s*#*$',lines[start]))
        body=start+(1 if markdown else 2)
        blocks.append(dict(start_line=start,body_start_line=body,end_line=part['end'],
            subtree_end_line=part['subtree_end'],start_codepoint=offsets[start],
            body_start_codepoint=offsets[body],end_codepoint=offsets[part['end']],
            subtree_end_codepoint=offsets[part['subtree_end']],level=part['level'],
            role='motivation' if part['normalized']=='motivation' else
                 'copyright' if part['normalized'] in ('copyright','copyright and license','copyright and licence')
                 else 'rest',
            retained_in_query=not any(a<=start<b for a,b in excluded)))
    return dict(document_id=expected['document'],repository=repository,
        relative_path=expected['relative_path'],commit=expected.get('commit',expected['head']),
        source_sha256=expected['source_sha256'],decoded_lf_sha256=hashlib.sha256(text.encode()).hexdigest(),
        hashed_first_author=expected['author'],license=expected['license'],sections=blocks)


def task_rows(rows,allocation):
    identities=[row['document'] for row in rows]
    if len(set(identities))!=len(identities):raise ValueError('Repeated public document identifier')
    result=[]
    for query in allocation:
        candidates=query['candidates'];truth=query['truth_position'];i=query['query']
        if len(candidates)!=50 or len(set(candidates))!=50 or candidates[truth]!=i:
            raise ValueError('Exact original 49-distractor roster required')
        if any(j<0 or j>=len(rows) for j in candidates):raise ValueError('Candidate index out of range')
        result.append(dict(document_id=identities[i],candidate_ids=[identities[j] for j in candidates],
            distractor_ids=[identities[j] for j in candidates if j!=i],truth_position=truth,
            hashed_first_author=rows[i]['author'],other_stratum=query['other_stratum']))
    return result


def run(output,inputs,config):
    if set(inputs)!={'go1_prepare'} or set(config)-{'max_new_documents','max_wall_seconds'}:
        raise ValueError('Exact GO1 preparation and operational limits required')
    maximum=config.get('max_new_documents',100000);wall=config.get('max_wall_seconds',900)
    if type(maximum) is not int or maximum<=0 or not isinstance(wall,(int,float)) or not math.isfinite(wall) or wall<=0:
        raise ValueError('Invalid export quantum')
    root,plan,_=common.complete(inputs['go1_prepare'],GO1_MODULE)
    if plan['config']!={'phase':'GO1-prepare','distractors':49}:
        raise ValueError('Only original primary GO1 preparation may supply EX3')
    prepared=common.read(root/'output/PREPARED.json')
    if prepared.get('source_only') is not True or prepared.get('module_sha256')!=common.io.sha(go1.__file__):
        raise ValueError('GO1 source preparation identity differs')
    documents=Path(plan['inputs']['documents']);source_root=documents.parent.parent
    if documents.resolve()!=(source_root/'output/documents.json').resolve():
        raise ValueError('Exact original GO source document projection required')
    _,source_plan,_=common.complete(source_root,'runners.drive.cards.week5_go')
    if source_plan['config']!={'phase':'prepare'}:raise ValueError('Original full GO source required')
    rows,allocation=pipeline.prepared_rows(plan['inputs'],plan['config'])
    if (digest(rows),digest(allocation))!=(prepared['rows_binding'],prepared['allocation_binding']):
        raise ValueError('Verified GO1 task identity differs')
    salt=Path(source_plan['inputs']['salt']).read_bytes()
    if len(salt)!=32:raise ValueError('Original source identity salt required')
    binding=dict(module_sha256=common.io.sha(__file__),go1_complete=common.io.sha(root/'COMPLETE.json'),
        source_complete=common.io.sha(source_root/'COMPLETE.json'),rows_binding=digest(rows),
        allocation_binding=digest(allocation),salt_sha256=hashlib.sha256(salt).hexdigest())
    output=Path(output);output.mkdir(parents=True,exist_ok=True);state_path=output/'STATE.json'
    state=common.state(state_path,binding,dict(completed=0,files={}))
    if set(state['files'])!={f'documents/{n:05d}.json' for n in range(state['completed'])}:
        raise ValueError('EX3 contiguous source checkpoint is incomplete')
    for name,sha in state['files'].items():
        if common.io.sha(output/name)!=sha:raise ValueError('Saved EX3 document changed')
    for name in {row['repository'] for row in rows}:
        repo=Path(source_plan['inputs'][name])
        if core.git(repo,'rev-parse','HEAD').strip()!=core.PINS[name] or core.git(repo,'status','--porcelain').strip():
            raise ValueError('Public source checkout changed')
    began=time.monotonic();new=0
    for n in range(state['completed'],len(rows)):
        row=rows[n];repo=Path(source_plan['inputs'][row['repository']]);path=repo/row['relative_path']
        path.resolve().relative_to(repo.resolve())
        if path.is_symlink() or common.io.sha(path)!=row['source_sha256']:raise ValueError('Public source file changed')
        text=path.read_text(encoding='utf8');value=spans(text,row['repository'],salt,row)
        name=f'documents/{n:05d}.json';common.io.write_json(output/name,value)
        state['files'][name]=common.io.sha(output/name);state['completed']=n+1;new+=1
        common.checkpoint(state_path,state)
        common.io.write_json(output/'PROGRESS.json',dict(phase='EX3_source',completed=n+1,total=len(rows)))
        if n+1<len(rows) and (new>=maximum or time.monotonic()-began>=wall or (output/'YIELD_REQUEST.json').exists()):
            return dict(status='yielded',verified=False,completed=n+1,total=len(rows))
    bundle=output/'bundle';bundle.mkdir(exist_ok=True)
    task=dict(schema='EX3-1',documents=[common.read(output/f'documents/{n:05d}.json') for n in range(len(rows))],
        queries=task_rows(rows,allocation),source_binding=binding)
    common.io.write_json(bundle/'TASK.json',task)
    text=('# EX3: frozen public goal task\n\nNo proposal text or author names are included. '
        'TASK.json contains exact public repository-relative paths, pinned commits, original byte hashes, '
        'hashed first-listed authors, all section spans and the same ordered 49 distractors as GO1. '
        'Offsets are zero-based, half-open lines and Unicode code points after UTF-8 decoding with '
        'CRLF/CR normalized to LF, as in Python read_text. Motivation subtrees, headers and copyright '
        'are excluded exactly by the pinned GO1 parser; nested sections inherit query exclusion. '
        'The source parser SHA is '+common.io.sha(core.__file__)+'. Reconstruct target and query '
        'with that original parser, including its heading rendering, subtree joins and stripping.\n\n'
        'Licences remain the original per-document public-domain/CC0 PEP statement or CC0 EIP/ERC '
        'repository notice. Document IDs are local task keys; paths and commits identify public sources. '
        'This task exports no model result and applies no later model support filter. '
        'Source ledger record: OPS-S15-W5-GO-BK-SOURCES-20261107.\n\n'
        f'Documents: {len(rows)}. Queries: {len(allocation)}. Distractors per query: 49.\n')
    (bundle/'README.md').write_text(text,encoding='utf8',newline='\n')
    manifest=dict(card='EX3',complete_export=True,source_binding=binding,
        files={name:common.io.sha(bundle/name) for name in ('TASK.json','README.md')})
    common.io.write_json(bundle/'MANIFEST.json',manifest)
    result=dict(card='EX3',record_kind='run',theory_tags=[],by_construction=False,
        complete_export=True,documents=len(rows),queries=len(allocation),text_exported=False)
    common.io.write_json(output/'RESULT.json',result);return result


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):
    output=Path(output);result=run(output/'independent-replay',inputs,config)
    if result.get('status')=='yielded':return result|{'verified':False}
    if result!=common.read(output/'RESULT.json'):raise ValueError('EX3 aggregate replay differs')
    common.replay_bundle(output/'bundle',output/'independent-replay/bundle')
    return dict(verified=True,all_document_spans_and_candidates_replayed=True)
def export_local(root,destination):return common.materialize(root,destination,card='EX3',module=MODULE,producer_sha256=common.io.sha(__file__))
