import copy
import json
from pathlib import Path

import pytest

from runners.drive.cards import engine_export_pilot as card
from runners.drive.engine_export_join import digest
from runners.stage14.common import filehash


def save(path,value):
    Path(path).write_bytes((json.dumps(value,ensure_ascii=False,allow_nan=False)+'\n').encode('utf8'))


def fixture(tmp_path,monkeypatch):
    cases=json.loads((Path(__file__).parent/'fixtures/ev_export_join.json').read_text(encoding='utf8'))['cases']
    files={'constructed-fixture-only':'0'*64};monkeypatch.setattr(card,'ENGINE_SHA',digest(files))
    manifest=dict(format='tompathy-ev-features-1',exporterSha256=card.EXPORTER_SHA,
        engine=dict(commit='5f3ad0a304727fff5e1a6beca592e786ee71b181',files=files,sourceSha256=digest(files)),
        slotLeaseSha256='lease',scientificAdmission=False,constructed=True,
        reader={'id':'constructed-byte-losses-v1'},readerFiles={})
    records=[c['record']['document'] for c in cases]
    values=[c['export']|dict(line=i,manifestSha256=digest(manifest)) for i,c in enumerate(cases,1)]
    path=tmp_path/'FEATURES.jsonl'
    save(str(path)+'.manifest.json',manifest)
    path.write_bytes((''.join(json.dumps(v,ensure_ascii=False)+'\n' for v in values)).encode('utf8'))
    counts={k:sum(v['status']==k for v in values) for k in ('complete','unsupported','error')}
    save(str(path)+'.receipt.json',dict(format=manifest['format'],counts=counts,manifestSha256=digest(manifest),
        outputSha256=filehash(path),scientificAdmission=False))
    save(path.with_suffix('.environment.json'),dict(versions=card.ENVIRONMENT,mode='constructed',executable='fixture'))
    return path,records,values,manifest


def test_exact_serialized_export_receipts_and_unsupported_units(tmp_path,monkeypatch):
    path,records,values,manifest=fixture(tmp_path,monkeypatch)
    actual=card.authenticated_export(path,records,{},'constructed','lease')
    assert actual==(values,manifest)


@pytest.mark.parametrize('fault',['missing-receipt','truncated','reordered','foreign-input','foreign-engine',
    'false-counts','false-manifest','false-output','wrong-environment','wrong-lease','fake-as-real','admission'])
def test_authentication_refusals(tmp_path,monkeypatch,fault):
    path,records,values,manifest=fixture(tmp_path,monkeypatch)
    receipt=Path(str(path)+'.receipt.json');meta=Path(str(path)+'.manifest.json')
    if fault=='missing-receipt':receipt.unlink()
    elif fault=='truncated':path.write_bytes(path.read_bytes().splitlines(keepends=True)[0])
    elif fault=='reordered':records.reverse()
    elif fault=='foreign-input':records[0]['text']+='changed'
    elif fault=='foreign-engine':manifest['engine']['commit']='other';save(meta,manifest)
    elif fault in ('false-counts','false-manifest','false-output'):
        r=json.loads(receipt.read_text());key={'false-counts':'counts','false-manifest':'manifestSha256','false-output':'outputSha256'}[fault]
        r[key]={} if key=='counts' else 'wrong';save(receipt,r)
    elif fault=='wrong-environment':save(path.with_suffix('.environment.json'),dict(versions={},mode='constructed'))
    elif fault=='wrong-lease':manifest['slotLeaseSha256']='other';save(meta,manifest)
    elif fault=='admission':manifest['scientificAdmission']=True;save(meta,manifest)
    else:manifest['reader']={'id':'real-model'};save(meta,manifest)
    with pytest.raises((ValueError,FileNotFoundError)):
        card.authenticated_export(path,records,{},'constructed','lease')


def test_scope_refuses_unadmitted_population():
    with pytest.raises(ValueError,match='first-ten'):
        card.validate({},dict(card.PILOT,session_limit=100))
