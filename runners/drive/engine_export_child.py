"""Fresh ToMpathy-interpreter adapter; constructed mode never loads weights.

DESIGN CHECK (2026-10-18)
Lessons read: LESSONS sections 3-5. Under null and alternative, exact source,
environment and lease identities are required. Failure direction is refusal
on any mismatch. Exhaustive operational bands: complete, unsupported or failed;
none licenses a scientific claim. The actual exporter owns real-reader scoring.
"""
from __future__ import annotations
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile

for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key]='1'
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',CUDA_VISIBLE_DEVICES='')
EXPORTER_SHA='a5dd4bc6447524968e75d1d4ae5f7d6c058529b41bbf2143ed44d4b7261273aa'
ENGINE_SHA='8aeee563b8f23202a042c7b4385df0669e1fd78c2d5f7f8455fd85ee6cb32bc7'
ENVIRONMENT={'torch':'2.9.1+cpu','transformers':'4.57.6','numpy':'2.5.4',
             'tokenizers':'0.22.2','safetensors':'0.7.0'}


class ConstructedLosses:
    def score(self,text,context,check):
        check()
        return [dict(start=i,end=i+1,nats=float(i%11+1)) for i in range(len(text))]


def main():
    cfg=json.loads(Path(sys.argv[1]).read_text(encoding='utf8'))
    source=Path(cfg['exporter'])
    if hashlib.sha256(source.read_bytes()).hexdigest()!=EXPORTER_SHA:
        raise ValueError('pinned exporter source changed')
    environment={k:importlib.metadata.version(k) for k in ENVIRONMENT}
    if environment!=ENVIRONMENT:raise ValueError('ToMpathy reader environment changed')
    output=Path(cfg['output'])
    with output.with_suffix('.environment.json').open('x',encoding='utf8',newline='\n') as stream:
        json.dump(dict(versions=environment,executable=sys.executable,mode=cfg['mode']),stream)
    spec=importlib.util.spec_from_file_location('pinned_ev_exporter',source)
    exporter=importlib.util.module_from_spec(spec);spec.loader.exec_module(exporter)
    if cfg['mode']=='reader-pilot':
        sys.argv=[str(source),'--input',cfg['input'],'--output',str(output),
                  '--reader',cfg['reader'],'--slot-lease',cfg['slot_lease'],'--stop-file',cfg['stop']]
        # No cache in either execution or verification: replay recomputes losses.
        exporter.main()
        return
    if cfg['mode']!='constructed':raise ValueError('unadmitted exporter mode')
    lease=Path(cfg['slot_lease']).read_bytes()
    def check():
        if Path(cfg['stop']).exists() or Path(cfg['slot_lease']).read_bytes()!=lease:
            raise RuntimeError('lease changed or stop requested')
    check()
    with tempfile.TemporaryDirectory(prefix='sl-ev-constructed-') as directory:
        engine=exporter.frozen_engine(source.parents[1],Path(directory))
        if engine['sourceSha256']!=ENGINE_SHA:raise ValueError('engine archive changed')
        from tompathy_engine.preview import surface, habits
        manifest=dict(format=exporter.FORMAT,engine=engine,exporterSha256=EXPORTER_SHA,
            reader={'id':'constructed-byte-losses-v1'},readerFiles={},
            slotLeaseSha256=exporter.sha(lease),scientificAdmission=False,constructed=True)
        manifest_sha=exporter.sha(exporter.canonical(manifest))
        with output.with_suffix(output.suffix+'.manifest.json').open('x',encoding='utf8',newline='\n') as stream:
            json.dump(manifest,stream,ensure_ascii=False,indent=2)
        counts=dict(complete=0,unsupported=0,error=0)
        with Path(cfg['input']).open(encoding='utf8') as inputs, output.open('x',encoding='utf8',newline='\n') as stream:
            for number,line in enumerate(inputs,1):
                result=exporter.export_record(json.loads(line),ConstructedLosses(),surface,habits,check)
                counts[result['status']]+=1
                stream.write(json.dumps(result|dict(line=number,manifestSha256=manifest_sha),ensure_ascii=False,allow_nan=False)+'\n')
                stream.flush()
        receipt=dict(format=exporter.FORMAT,counts=counts,manifestSha256=manifest_sha,
                     outputSha256=exporter.sha(output.read_bytes()),scientificAdmission=False)
        with output.with_suffix(output.suffix+'.receipt.json').open('x',encoding='utf8',newline='\n') as stream:
            json.dump(receipt,stream,indent=2)


if __name__=='__main__':main()
