"""Pinned engine habit extraction only; no reader imports or model scoring.

DESIGN CHECK: LESSONS 3-5 read 2026-10-19. Under null and alternative,
source hashes, exact text/provenance and lease identity must agree. Changed
inputs or stops refuse extraction; unsupported denominators stay explicit.
Known counts and parity with completed real exporter habits precede inference.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile

for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key]='1'
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',CUDA_VISIBLE_DEVICES='')
EXPORTER_SHA='a5dd4bc6447524968e75d1d4ae5f7d6c058529b41bbf2143ed44d4b7261273aa'
ENGINE_SHA='8aeee563b8f23202a042c7b4385df0669e1fd78c2d5f7f8455fd85ee6cb32bc7'


def project(raw,connectives):
    denominator=raw['words'];total=denominator+raw['quotedWords']
    rates={name:raw['connectives'].get(name,0)*1000/denominator if denominator else None for name in connectives}
    rates.update({name:raw['punctuation'].get(name,0)*1000/denominator if denominator else None for name in (',',';',':','\u2014','?','!')})
    return dict(raw=raw,ratesPer1000UnquotedWords=rates,
        rateStatus='supported' if denominator else 'unsupported-empty-denominator',
        sentenceMean=raw['sentenceMean'] if raw['sentenceCount'] else None,
        sentenceSpread=raw['sentenceSpread'] if raw['sentenceCount'] else None,
        quotedWordShare=raw['quotedWords']/total if total else None)


def main():
    cfg=json.loads(Path(sys.argv[1]).read_text(encoding='utf8'));source=Path(cfg['exporter'])
    if hashlib.sha256(source.read_bytes()).hexdigest()!=EXPORTER_SHA:raise ValueError('exporter source changed')
    lease=Path(cfg['slot_lease']);lease_bytes=lease.read_bytes()
    def check():
        if Path(cfg['stop']).exists() or Path(cfg['yield']).exists() or lease.read_bytes()!=lease_bytes:
            raise RuntimeError('Owner/resource stop or changed lease')
    check()
    spec=importlib.util.spec_from_file_location('pinned_ev_exporter',source)
    exporter=importlib.util.module_from_spec(spec);spec.loader.exec_module(exporter)
    destination=Path(cfg['output'])
    with tempfile.TemporaryDirectory(prefix='sl-ev-habits-') as directory:
        engine=exporter.frozen_engine(source.parents[1],Path(directory))
        if engine['sourceSha256']!=ENGINE_SHA:raise ValueError('pinned engine changed')
        from tompathy_engine.preview import habits
        count=0
        with Path(cfg['input']).open(encoding='utf8') as records,destination.open('x',encoding='utf8',newline='\n') as stream:
            for line in records:
                check();record=json.loads(line)
                _,_,capture=exporter.prepare(record)
                value=dict(keys=record['keys'],variant=record.get('variant','final-document'),
                    inputRecordSha256=exporter.sha(exporter.canonical(record)),textSha256=record['textSha256'],
                    habits=project(habits.describe(capture,check),habits.CONNECTIVES))
                stream.write(json.dumps(value,ensure_ascii=False,allow_nan=False)+'\n');stream.flush();count+=1
        forbidden=[name for name in sys.modules if name=='torch' or name.startswith('transformers')]
        if forbidden:raise RuntimeError('Habit-only child unexpectedly imported a model framework')
        receipt=dict(engine=engine,exporterSha256=EXPORTER_SHA,documents=count,
            outputSha256=exporter.sha(destination.read_bytes()),readerExecuted=False,
            modelFrameworkImported=False,slotLeaseSha256=exporter.sha(lease_bytes))
        destination.with_suffix('.receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,sort_keys=True),encoding='utf8',newline='\n')


if __name__=='__main__':main()
