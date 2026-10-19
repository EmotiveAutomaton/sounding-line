"""Required fixed first-100 engine export/support pilot; no full admission.

DESIGN CHECK (2026-10-18)
Lessons read: LESSONS sections 3-5. Under null and alternative, exact source,
cohort and uncached replay must agree. Changed source, unsupported substitutions,
or cap overrun refuse completion. The same authenticated exporter and join are
used as in the completed first-ten pilot. This separately frozen scope preserves
that pilot's bytes, costs and outputs. Operational bands: COMPLETE or FAILED.
EV2 support is evaluated only after the whole first-100 export is verified;
no sample-selected projection, full-corpus admission or scientific verdict.
"""
from collections import Counter
import os
from pathlib import Path
import time
from threadpoolctl import threadpool_limits
from runners.stage14.common import atomic,read,filehash
from runners.drive.engine_export_join import digest,join_exports,typed_fragments
from . import engine_export_pilot as original, engine_d33_consumer as consumer
from .engine_export_pilot import authenticated_export,export
from .timing_p6 import write_equal,gzip_equal,gzread
from .timing_stats import bind,check_binding

CONSTRUCTED=original.CONSTRUCTED
CONFIG=dict(mode='reader-pilot',session_limit=100,cumulative_wall_seconds=3600)


def validate(inputs,config):
    if config not in (CONSTRUCTED,CONFIG):
        raise ValueError('Only constructed or fixed first-100 support pilot admitted')
    # Reuse unchanged identity/input gates; scope is separately validated above.
    original.validate(inputs,CONSTRUCTED if config==CONSTRUCTED else original.PILOT)


def run(output,inputs,config,operation):
    validate(inputs,config);os.environ['PYTHONSAFEPATH']='1';output=Path(output);output.mkdir(parents=True,exist_ok=True)
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
            summary=dict(card='EV-export-support-pilot',status='complete',mode=config['mode'],
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
