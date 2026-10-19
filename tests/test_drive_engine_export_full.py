import json
from pathlib import Path

import pytest

from runners.drive.cards import engine_export_full as card
from runners.drive.cards import engine_input_full, engine_export_pilot as pilot, engine_export_support_pilot as support
from runners.drive.cards.timing_p6 import gzread
from runners.stage14.common import read, filehash
from tests.test_drive_engine_input_full import fixture as source_fixture, CONFIG as SOURCE_CONFIG
from tests.test_drive_engine_sources import save


def finish(root, module, inputs, config, pins):
    save(root/'PLAN.json', dict(module=module, inputs=inputs, config=config, pins=pins))
    save(root/'COMPLETE.json', dict(status='COMPLETE', fresh_process_verified=True,
        outputs={p.relative_to(root).as_posix():filehash(p) for p in root.rglob('*') if p.is_file()}))


def source_inputs(root):
    inputs = source_fixture(root/'source-fixture')
    full = root/'full-source'
    engine_input_full.execute(full/'output', inputs, SOURCE_CONFIG)
    assert engine_input_full.verify(full/'output', inputs, SOURCE_CONFIG)['verified']
    finish(full, 'runners.drive.cards.engine_input_full', inputs, SOURCE_CONFIG,
           {str(Path(inputs['source_completion'])):filehash(inputs['source_completion'])})
    rows = [dict(writer='w', session=sid, index=i, length=3, personal_surprise=.25,
        donor_surprise=-.3, population_surprisal=2., log_pause=-.7, log_frequency=-4.,
        sentence_start=0, after_punctuation=1) for sid in ['s','t'] for i in (0,1)]
    rows.append(dict(rows[0],session='outside'))
    save(root/'ROWS.json', rows)
    return dict(inputs, rows_fixture=str((root/'ROWS.json').resolve())), full


def fake_export(output, documents, inputs, config, operation, check):
    check(); folder=output/operation; folder.mkdir(exist_ok=False)
    files={'constructed-test-engine':'0'*64}
    manifest=dict(format='tompathy-ev-features-1', exporterSha256=pilot.EXPORTER_SHA,
        engine=dict(commit='5f3ad0a304727fff5e1a6beca592e786ee71b181',files=files,sourceSha256=pilot.ENGINE_SHA),
        slotLeaseSha256='fixture-lease',scientificAdmission=False,constructed=True,
        reader={'id':'constructed-byte-losses-v1'},readerFiles={})
    values=[]
    for i,d in enumerate(documents,1):
        values.append(dict(status='unsupported',keys=d['keys'],textSha256=d['textSha256'],
            inputRecordSha256=card.digest(d),provenance=d['provenance'],provenanceSha256=card.digest(d['provenance']),
            words=[],variant=d['variant'],productionMappingValidated=False,fragmentConstruction=None,
            regions=[dict(id='r',start=0,end=len(d['text']))],
            reason='No scorable content words after names/numbers/code holdouts',line=i,manifestSha256=card.digest(manifest)))
    path=folder/'FEATURES.jsonl'
    path.write_bytes((''.join(json.dumps(v)+'\n' for v in values)).encode('utf8'))
    save(str(path)+'.manifest.json',manifest)
    save(str(path)+'.receipt.json',dict(format=manifest['format'],counts=dict(complete=0,unsupported=len(values),error=0),
        manifestSha256=card.digest(manifest),outputSha256=filehash(path),scientificAdmission=False))
    save(path.with_suffix('.environment.json'),dict(versions=pilot.ENVIRONMENT,mode='constructed'))
    return values,manifest


def fixture(root, monkeypatch):
    inputs, full = source_inputs(root)
    save(root/'exporter.py', {'fixture':True}); save(root/'reader.json',{'fixture':True})
    inputs.update(exporter=str((root/'exporter.py').resolve()),export_python=str((root/'exporter.py').resolve()),
                  reader_manifest=str((root/'reader.json').resolve()))
    monkeypatch.setattr(pilot,'EXPORTER_SHA',filehash(inputs['exporter']))
    monkeypatch.setattr(pilot,'READER_SHA',card.digest(read(inputs['reader_manifest'])))
    monkeypatch.setattr(pilot,'ENGINE_SHA',card.digest({'constructed-test-engine':'0'*64}))
    monkeypatch.setattr(pilot,'export',fake_export); monkeypatch.setattr(support,'export',fake_export)
    parent=root/'support'
    support.execute(parent/'output', inputs, support.CONSTRUCTED)
    assert support.verify(parent/'output', inputs, support.CONSTRUCTED)['verified']
    finish(parent,'runners.drive.cards.engine_export_support_pilot',inputs,support.CONSTRUCTED,
           {str(Path(inputs['source_completion'])):filehash(inputs['source_completion'])})
    return dict(inputs,full_source_completion=str((full/'COMPLETE.json').resolve()),
                support_completion=str((parent/'COMPLETE.json').resolve()))


def test_complete_known_answer_reuse_replay_and_reentry(tmp_path,monkeypatch):
    inputs=fixture(tmp_path,monkeypatch);output=tmp_path/'reader'
    actual=card.execute(output,inputs,card.CONSTRUCTED)
    assert actual['documents']==2 and actual['reused_documents']==1
    assert actual['support']['original_rows']==5
    assert actual['support']['dispositions']=={'engine-unsupported-document':2,'not-intact-final-word':2,'outside-input-cohort':1}
    assert not actual['scientific_admission'] and not actual['real_reader_executed']
    assert card.verify(output,inputs,card.CONSTRUCTED)['summary']==actual
    parent=Path(inputs['support_completion']).parent/'output/execute/FEATURES.jsonl'
    assert (output/'reuse/FEATURES.jsonl').read_bytes()==parent.read_bytes()
    hashes=read(output/'TIMING_BINDINGS.json')['outputs']
    monkeypatch.setattr(pilot,'export',lambda *a:pytest.fail('completed batches must not run again'))
    assert card.execute(output,inputs,card.CONSTRUCTED)==actual
    assert hashes=={k:filehash(output/k) for k in hashes}


def test_sealed_batch_resume_before_aggregate(tmp_path,monkeypatch):
    inputs=fixture(tmp_path,monkeypatch);output=tmp_path/'reader';join=card.join_exports
    monkeypatch.setattr(card,'join_exports',lambda *a:(_ for _ in ()).throw(RuntimeError('fixture boundary')))
    with pytest.raises(RuntimeError,match='fixture boundary'):card.execute(output,inputs,card.CONSTRUCTED)
    sealed=(output/'execute/batch-000/FEATURES.jsonl').read_bytes()
    monkeypatch.setattr(card,'join_exports',join)
    monkeypatch.setattr(pilot,'export',lambda *a:pytest.fail('sealed batch must be reused'))
    assert card.execute(output,inputs,card.CONSTRUCTED)['status']=='complete'
    assert (output/'execute/batch-000/FEATURES.jsonl').read_bytes()==sealed


@pytest.mark.parametrize('kind',['source-terminal','support-terminal','raw','reused-export','checkpoint','summary','scope'])
def test_refuses_changed_or_incomplete_evidence(tmp_path,monkeypatch,kind):
    inputs=fixture(tmp_path,monkeypatch);output=tmp_path/'reader'
    card.execute(output,inputs,card.CONSTRUCTED)
    if kind.endswith('terminal'):
        key='full_source_completion' if kind=='source-terminal' else 'support_completion'
        value=read(inputs[key]);value['fresh_process_verified']=False;save(inputs[key],value)
    elif kind=='raw':
        p=tmp_path/'source-fixture/source/raw/t.jsonl';p.write_bytes(p.read_bytes()+b' ')
    elif kind=='reused-export': (output/'reuse/FEATURES.jsonl').write_bytes(b'{}\n')
    elif kind=='checkpoint': (output/'execute/batch-000/FEATURES.jsonl').write_bytes(b'{}\n')
    elif kind=='summary': save(output/'SUMMARY.json',{})
    else:
        with pytest.raises(ValueError):card.validate(inputs,dict(card.CONSTRUCTED,expected_sessions=1))
        return
    with pytest.raises(ValueError):card.verify(output,inputs,card.CONSTRUCTED)


def test_partial_batch_refused_without_overwrite(tmp_path,monkeypatch):
    inputs=fixture(tmp_path,monkeypatch);output=tmp_path/'reader'
    folder=output/'execute/batch-000';folder.mkdir(parents=True);(folder/'FEATURES.jsonl').write_bytes(b'partial')
    with pytest.raises(FileNotFoundError):card.execute(output,inputs,card.CONSTRUCTED)
    assert (folder/'FEATURES.jsonl').read_bytes()==b'partial'


def test_fresh_replay_refuses_changed_values(tmp_path,monkeypatch):
    inputs=fixture(tmp_path,monkeypatch);output=tmp_path/'reader';card.execute(output,inputs,card.CONSTRUCTED)
    base=pilot.export
    def changed(*args):
        result=base(*args)
        folder=args[0]/args[4];p=folder/'FEATURES.jsonl'
        values=[json.loads(line) for line in p.read_text().splitlines()];values[0]['extra']='changed'
        p.write_bytes((''.join(json.dumps(v)+'\n' for v in values)).encode('utf8'))
        receipt=read(str(p)+'.receipt.json');receipt['outputSha256']=filehash(p);save(str(p)+'.receipt.json',receipt)
        return result
    monkeypatch.setattr(pilot,'export',changed)
    with pytest.raises(ValueError,match='does not reproduce'):card.verify(output,inputs,card.CONSTRUCTED)


def test_combined_cost_not_reset_and_forecast_admission():
    result=card.remaining_cost(2464.068555400004,11000,949.8856067999732)
    assert result['max_wall_seconds']==15335
    assert result['prior_wall_seconds_charged']+result['max_wall_seconds']<=28800
    with pytest.raises(ValueError):card.remaining_cost(2464.068555400004,16000,949.8856067999732)
    for invalid in [float('nan'),float('inf'),0,-1,True]:
        with pytest.raises(ValueError):card.remaining_cost(invalid,11000,949.8856067999732)
