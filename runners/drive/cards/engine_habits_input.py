"""EV3 authenticated final/typed habit input; no identification statistic.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 6-7 read 2026-10-19. Under both
null and alternative, final habit values must match the completed exporter;
typed fragments retain every source boundary and require fresh exact replay.
No typed support is missing data, never zero habits. Source/output corruption,
unsupported config or failed native children refuse completion. Construction,
complete input and failed extraction are distinct from a scientific result.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import time
from threadpoolctl import threadpool_limits
from runners.stage14.common import REPO,read,atomic,filehash
from runners.stage9.process_identity import native_identity
from runners.drive.native_job import ContainedProcess
from runners.drive.engine_export_join import digest,typed_fragments
from runners.drive.engine_habits_child import EXPORTER_SHA,ENGINE_SHA
from . import engine_export_full as reader
from .timing_p6 import gzread,gzip_equal,write_equal
from .timing_stats import bind,check_binding
from .engine_signatures_guarded import boundary

CONFIG=dict(mode='full-habit-input',expected_sessions=1399)
CONSTRUCTED=dict(mode='constructed-habit-input',expected_sessions=2)


def validate(inputs,config):
    expected={'reader_completion','exporter','export_python'} if config==CONFIG else {'fixture','exporter','export_python'} if config==CONSTRUCTED else None
    if expected is None or set(inputs)!=expected:raise ValueError('fixed habit input/config required')
    if filehash(inputs['exporter'])!=EXPORTER_SHA:raise ValueError('pinned exporter changed')


def load(inputs,config):
    validate(inputs,config)
    if config==CONSTRUCTED:
        value=read(inputs['fixture'])
        if set(value)!={'records'} or len(value['records'])!=2:raise ValueError('known-answer population required')
        return value['records'],None
    root,plan=reader.authenticate(inputs['reader_completion'],'runners.drive.cards.engine_export_full')
    if plan['config']['mode']!='full-reader':raise ValueError('full-reader completion required')
    for key in ('exporter','export_python'):
        if Path(inputs[key]).resolve()!=Path(plan['inputs'][key]).resolve():raise ValueError('completed engine environment differs')
    records,_,_,_=reader.load(plan['inputs'],plan['config'])
    # Read the completed JSONL exports one document at a time, retaining only
    # habit values. No whole-corpus reader-word matrix is materialized again.
    values={}
    paths=[root/'output/reuse/FEATURES.jsonl']+sorted((root/'output/execute').glob('batch-*/FEATURES.jsonl'))
    for path in paths:
        with path.open(encoding='utf8') as stream:
            for line in stream:
                value=json.loads(line);sid=value['keys']['session']
                if sid in values:raise ValueError('duplicate completed export session')
                values[sid]=dict(keys=value['keys'],textSha256=value['textSha256'],inputRecordSha256=value['inputRecordSha256'],habits=value['habits'])
    if len(records)!=1399 or len(values)!=1399:raise ValueError('incomplete full habit population')
    return records,values


def documents(records):
    result=[];fragments=[]
    for record in records:
        doc=record['document'];fragment=typed_fragments(record)
        result.append(doc);fragments.append(fragment)
        if fragment['document'] is not None:result.append(fragment['document'])
    return result,fragments


def combine(records,fragments,values,reference):
    indexed={}
    for value in values:
        key=(value['keys']['session'],value['variant'])
        if key in indexed:raise ValueError('duplicate variant')
        indexed[key]=value
    result=[];used=set()
    for record,fragment in zip(records,fragments,strict=True):
        doc=record['document'];sid=doc['keys']['session']
        construction=fragment['document']['fragmentConstruction'] if fragment['document'] is not None else fragment['construction']
        row=dict(keys=doc['keys'],typed_support=fragment['support'],fragment_construction_sha256=digest(construction))
        for name,source in [('final',doc),('typed',fragment['document'])]:
            if source is None:row[name]=None;continue
            key=(sid,source.get('variant','final-document'));value=indexed[key];used.add(key)
            if value['keys']!=source['keys'] or value['inputRecordSha256']!=digest(source) or value['textSha256']!=source['textSha256']:
                raise ValueError('habit export source binding differs')
            if name=='final' and reference is not None:
                expected=reference[sid]
                if any(value[k]!=expected[k] for k in expected):raise ValueError('fresh final habits differ from completed reader export')
            row[name]=value['habits']
        result.append(row)
    if used!=set(indexed):raise ValueError('unexpected exported document')
    return result


def extract(output,docs,inputs,operation):
    owner=read(output.parent/'OWNER.json')['native'];admission=read(output.parent/'ADMISSION.json');lease=Path(admission['lease'])
    if native_identity(owner['pid'])!=owner or read(lease)['native']!=owner:raise ValueError('live counted lease required')
    folder=output/operation;folder.mkdir(exist_ok=False)
    data=folder/'INPUT.jsonl';data.write_bytes(''.join(json.dumps(d,ensure_ascii=False,allow_nan=False)+'\n' for d in docs).encode('utf8'))
    dest=folder/'HABITS.jsonl'
    request=dict(exporter=inputs['exporter'],input=str(data),output=str(dest),slot_lease=str(lease),stop=str(output.parent/'STOP'),**{'yield':str(output/'YIELD_REQUEST.json')})
    write_equal(folder/'REQUEST.json',request)
    env=os.environ.copy();env['PYTHONSAFEPATH']='1'
    started=time.monotonic()
    with ContainedProcess([inputs['export_python'],'-X','utf8','-B',REPO/'runners/drive/engine_habits_child.py',folder/'REQUEST.json'],REPO,folder/'stdout.log',folder/'stderr.log',env=env) as child:
        atomic(folder/'NATIVE.json',dict(native=native_identity(child.pid),contained=True))
        while child.poll() is None:
            boundary(output)
            if time.monotonic()-started>1200:raise TimeoutError('habit extraction exceeded contained child cap')
            time.sleep(.2)
        if child.poll()!=0:raise RuntimeError('habit child failed; retained native stderr')
    receipt=read(dest.with_suffix('.receipt.json'))
    if (receipt['engine']['sourceSha256']!=ENGINE_SHA or receipt['exporterSha256']!=EXPORTER_SHA or receipt['documents']!=len(docs)
        or receipt['readerExecuted'] or receipt['modelFrameworkImported'] or receipt['slotLeaseSha256']!=filehash(lease) or receipt['outputSha256']!=filehash(dest)):
        raise ValueError('habit-only native receipt differs')
    return [json.loads(line) for line in dest.read_text(encoding='utf8').splitlines()]


def run(output,inputs,config,operation):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);boundary(output)
    if operation=='verify' or (output/'TIMING_BINDINGS.json').exists():check_binding(output,inputs,config)
    phase=operation
    with threadpool_limits(limits=1):
        records,reference=load(inputs,config);boundary(output)
        if operation=='execute' and (output/'TIMING_BINDINGS.json').exists():
            return read(output/'SUMMARY.json')
        if (output/phase).exists():raise ValueError('explicit fresh attempt required; preserve existing child receipts')
        docs,fragments=documents(records);values=extract(output,docs,inputs,phase)
        rows=combine(records,fragments,values,reference);boundary(output)
    summary=dict(card='EV3-habit-input',status='complete',documents=len(records),
        final_habits=len(rows),typed_habits=sum(r['typed'] is not None for r in rows),
        unsupported_typed=sum(r['typed'] is None for r in rows),
        final_export_parity=reference is not None,reader_executed=False,
        typed_variant='Surviving typed runs; non-typed gaps are synthetic paragraph boundaries, not original prose',
        scientific_admission=False,identification_not_run=True)
    if operation=='execute':
        write_equal(output/'SUMMARY.json',summary);gzip_equal(output/'HABITS.json.gz',rows)
        bind(output,inputs,config,['SUMMARY.json','HABITS.json.gz']);return summary
    if summary!=read(output/'SUMMARY.json') or rows!=gzread(output/'HABITS.json.gz'):raise ValueError('fresh habit extraction differs')
    return dict(verified=True,summary=summary,fresh_source_authentication=True,fresh_native_habits_replay=True)


def execute(output,inputs,config):return run(output,inputs,config,'execute')
def verify(output,inputs,config):return run(output,inputs,config,'verify')
