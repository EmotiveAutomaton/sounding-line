"""Authenticated, contained exporter pilot; no full-corpus or science admission.

DESIGN CHECK (2026-10-18)
Lessons read: LESSONS sections 3-5. Under null and alternative, producer identity,
exact population, spans, manifests and fresh uncached replay must agree. Failure
direction is refusal of changed, missing or substituted evidence. Operational
bands exhaustive: complete input/export validation, unsupported word, or failure.
The fixed first ten documents measure execution cost; EV2's 100-document support
pilot and all statistical consumers remain separate. No result-selected sample.
"""
from __future__ import annotations
from collections import Counter
import json
from pathlib import Path
import time

import psutil
from threadpoolctl import threadpool_limits

from runners.drive.engine_export_child import EXPORTER_SHA,ENGINE_SHA,ENVIRONMENT
from runners.drive.engine_export_join import digest,join_exports,typed_fragments,word_index
from runners.drive.native_job import ContainedProcess
from runners.stage9.process_identity import native_identity
from runners.stage14.common import REPO,read,atomic,filehash
from . import engine_d33_consumer as consumer
from .timing_p6 import write_equal,gzip_equal,gzread
from .timing_stats import bind,check_binding

CONSTRUCTED=dict(mode='constructed',session_limit=1,cumulative_wall_seconds=180)
PILOT=dict(mode='reader-pilot',session_limit=10,cumulative_wall_seconds=1800)
EXTRA={'exporter','export_python','reader_manifest'}
READER_SHA='7612cbcd48959ed57557d659d6aa3961a8c9e210fd9e4c76f7a8923c1b6a2e8f'


def validate(inputs,config):
    if config not in (CONSTRUCTED,PILOT):raise ValueError('Only constructed or fixed first-ten timing pilot admitted')
    underlying={k:v for k,v in inputs.items() if k not in EXTRA}
    consumer.validate(underlying,dict(mode='constructed',cumulative_wall_seconds=120)
        if config['mode']=='constructed' else consumer.CONFIG)
    if set(inputs)!=set(underlying)|EXTRA:raise ValueError('Exact exporter identities required')
    if filehash(inputs['exporter'])!=EXPORTER_SHA:raise ValueError('Pinned exporter changed')
    if digest(read(inputs['reader_manifest']))!=READER_SHA:raise ValueError('Pinned reader manifest changed')


def authenticated_export(path,documents,inputs,mode,lease_sha):
    path=Path(path);manifest=read(str(path)+'.manifest.json');receipt=read(str(path)+'.receipt.json')
    if (manifest['format']!='tompathy-ev-features-1' or manifest['exporterSha256']!=EXPORTER_SHA
            or manifest['engine']['commit']!='5f3ad0a304727fff5e1a6beca592e786ee71b181'
            or manifest['engine']['sourceSha256']!=ENGINE_SHA
            or digest(manifest['engine']['files'])!=ENGINE_SHA
            or manifest['slotLeaseSha256']!=lease_sha or manifest['scientificAdmission'] is not False):
        raise ValueError('Exporter source/lease manifest differs')
    if mode=='constructed':
        if manifest.get('constructed') is not True or manifest['reader']!={'id':'constructed-byte-losses-v1'} or manifest['readerFiles']:
            raise ValueError('Constructed reader identity differs')
    else:
        reader=read(inputs['reader_manifest'])
        expected=dict(id=reader['model'],revision=reader['revision'],sha256=READER_SHA,
            backend='torch 2.9.1+cpu; transformers 4.57.6; CPU dynamic-int8 linear, float32 embeddings, 1 thread')
        if manifest.get('constructed') or manifest['reader']!=expected or manifest['readerFiles']!=reader['files']:
            raise ValueError('Actual reader identity differs')
    values=[json.loads(line) for line in path.read_text(encoding='utf8').splitlines()]
    counts=dict(complete=0,unsupported=0,error=0)
    if len(values)!=len(documents):raise ValueError('Exporter document cohort differs')
    for number,(document,value) in enumerate(zip(documents,values),1):
        if value['line']!=number or value['manifestSha256']!=digest(manifest):
            raise ValueError('Exporter order or manifest binding differs')
        word_index(document,value)
        counts[value['status']]+=1
    if receipt!=dict(format=manifest['format'],counts=counts,manifestSha256=digest(manifest),
                     outputSha256=filehash(path),scientificAdmission=False):
        raise ValueError('Exporter final receipt differs')
    environment=read(path.with_suffix('.environment.json'))
    if environment['versions']!=ENVIRONMENT or environment['mode']!=mode:
        raise ValueError('Exporter environment differs')
    return values,manifest


def export(output,documents,inputs,config,operation,check):
    root=output.parent;admission=read(root/'ADMISSION.json');owner=read(root/'OWNER.json')
    lease=Path(admission['lease']);lease_value=read(lease)
    if lease_value['native']!=owner['native'] or native_identity(owner['native']['pid'])!=owner['native']:
        raise ValueError('Live counted owner lease required')
    folder=output/operation;folder.mkdir(exist_ok=False)
    data=folder/'INPUT.jsonl'
    data.write_bytes((''.join(json.dumps(d,ensure_ascii=False,allow_nan=False)+'\n' for d in documents)).encode('utf8'))
    destination=folder/'FEATURES.jsonl'
    request=dict(mode=config['mode'],exporter=inputs['exporter'],input=str(data),output=str(destination),
        reader=str(Path(inputs['reader_manifest']).parent),slot_lease=str(lease),stop=str(root/'STOP'))
    write_equal(folder/'REQUEST.json',request)
    started=time.monotonic();peak=0.;cpu=0.
    with ContainedProcess([inputs['export_python'],'-X','utf8','-B',REPO/'runners/drive/engine_export_child.py',folder/'REQUEST.json'],
                         REPO,folder/'stdout.log',folder/'stderr.log') as worker:
        atomic(folder/'NATIVE.json',dict(native=native_identity(worker.pid),contained=True))
        while worker.poll() is None:
            check()
            try:
                parent=psutil.Process(worker.pid);processes=[parent]+parent.children(recursive=True)
                peak=max(peak,sum(p.memory_info().rss for p in processes)/2**30)
                cpu=max(cpu,sum(sum(p.cpu_times()[:2]) for p in processes))
            except psutil.NoSuchProcess:pass
            time.sleep(.2)
        if worker.poll()!=0:raise RuntimeError('Exporter child failed; retained stderr and partial output')
    check()
    atomic(folder/'MEASURED.json',dict(wall_seconds=time.monotonic()-started,peak_ram_GiB=peak,
        sampled_cpu_seconds=cpu,uncached=True,documents=len(documents)))
    return authenticated_export(destination,documents,inputs,config['mode'],filehash(lease))


def run(output,inputs,config,operation):
    validate(inputs,config);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    timing=output/'ACTIVE_TIME.json';previous=read(timing)['seconds'] if timing.exists() else 0.
    started=time.monotonic()
    def check():
        if previous+time.monotonic()-started>config['cumulative_wall_seconds']:
            raise TimeoutError('Combined exporter execution/replay cap exceeded')
        if (output.parent/'STOP').exists():raise RuntimeError('Owner stop requested')
    try:
        with threadpool_limits(limits=1):
            if operation=='verify' or (output/'TIMING_BINDINGS.json').exists():check_binding(output,inputs,config)
            mode='constructed' if config['mode']=='constructed' else consumer.CONFIG['mode']
            sources,selected,records=consumer.input_records(inputs['source_completion'],mode)
            selected=selected[:config['session_limit']];records=records[:config['session_limit']]
            if len(records)!=config['session_limit']:raise ValueError('Timing-pilot source support differs')
            original=consumer.original_rows(inputs,{'mode':'constructed'} if mode=='constructed' else consumer.CONFIG)
            if operation=='verify':
                for sid,record in zip(selected,records):
                    if sources.session(sid)!=record:raise ValueError('Fresh source document differs')
                    check()
            documents=[r['document'] for r in records];fragments=[typed_fragments(r) for r in records]
            folder=output/operation
            if operation=='execute' and (output/'TIMING_BINDINGS.json').exists():
                # Byte-stable second entry never starts another model process.
                values,manifest=authenticated_export(folder/'FEATURES.jsonl',documents,inputs,config['mode'],
                    read(output/'IDENTITY.json')['lease_sha256'])
            else:values,manifest=export(output,documents,inputs,config,operation,check)
            joined=join_exports(original,records,values)
            summary=dict(card='EV-export-timing-pilot',status='complete',mode=config['mode'],
                documents=len(documents),support=joined['support'],
                fragment_dispositions=dict(Counter(x['status'] for x in fragments)),
                real_reader_executed=config['mode']=='reader-pilot',scientific_admission=False,
                full_corpus_admitted=False,ev2_support_pilot_complete=False)
            identity=dict(selected_sessions=selected,manifest_sha256=digest(manifest),
                lease_sha256=manifest['slotLeaseSha256'],input_hashes={k:filehash(v) for k,v in sorted(inputs.items())})
            if operation=='execute':
                write_equal(output/'IDENTITY.json',identity);gzip_equal(output/'JOINED.json.gz',joined)
                gzip_equal(output/'FRAGMENTS.json.gz',fragments);write_equal(output/'SUMMARY.json',summary)
                if not (output/'TIMING_BINDINGS.json').exists():
                    artifacts=['IDENTITY.json','JOINED.json.gz','FRAGMENTS.json.gz','SUMMARY.json']
                    artifacts += [p.relative_to(output).as_posix() for p in sorted(folder.glob('*')) if p.suffix in ('.json','.jsonl')]
                    bind(output,inputs,config,artifacts)
            else:
                original_values,original_manifest=authenticated_export(output/'execute/FEATURES.jsonl',documents,inputs,config['mode'],manifest['slotLeaseSha256'])
                if (values!=original_values or manifest!=original_manifest or identity!=read(output/'IDENTITY.json')
                        or joined!=gzread(output/'JOINED.json.gz') or fragments!=gzread(output/'FRAGMENTS.json.gz')
                        or summary!=read(output/'SUMMARY.json')):
                    raise ValueError('Fresh uncached export or exact source join does not reproduce')
            check()
            return summary if operation=='execute' else dict(verified=True,summary=summary,
                fresh_input_reconstruction=True,fresh_uncached_export=True)
    finally:atomic(timing,dict(seconds=previous+time.monotonic()-started))


def execute(output,inputs,config):return run(output,inputs,config,'execute')
def verify(output,inputs,config):return run(output,inputs,config,'verify')
