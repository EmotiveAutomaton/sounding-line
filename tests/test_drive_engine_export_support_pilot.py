import pytest
from runners.drive.cards import engine_export_support_pilot as card
from runners.drive.cards.timing_p6 import gzread
from tests.test_drive_engine_d33_consumer import fixture


@pytest.mark.parametrize('size',[0,10,99,101,1399])
def test_scope_refuses_other_populations(size):
    with pytest.raises(ValueError,match='first-100'):
        card.validate({},dict(card.CONFIG,session_limit=size))


def test_scope_reuses_original_identity_gates(monkeypatch):
    calls=[]
    monkeypatch.setattr(card.original,'validate',lambda i,c:calls.append((i,c)))
    card.validate({'identity':'retained'},card.CONFIG)
    assert calls==[({'identity':'retained'},card.original.PILOT)]
    with pytest.raises(ValueError):card.validate({},dict(card.CONFIG,cumulative_wall_seconds=7200))


def test_constructed_full_handler_replay_and_refusal(tmp_path,monkeypatch):
    inputs=fixture(tmp_path/'source');output=tmp_path/'output'
    monkeypatch.setattr(card,'validate',lambda i,c:None)
    # This fixture exercises unsupported-document propagation. The actual
    # exporter and environment are exercised by separate native admission.
    seen=[];saved=[]
    def fake_export(out,documents,provided,config,operation,check):
        seen.append(operation)
        values=[]
        for document in documents:
            values.append(dict(status='unsupported',keys=document['keys'],
                textSha256=document['textSha256'],inputRecordSha256=card.digest(document),
                provenance=document.get('provenance',[]),
                provenanceSha256=card.digest(document.get('provenance',[])),words=[],
                variant=document['variant'],productionMappingValidated=False,
                fragmentConstruction=None,regions=[dict(id='r',start=0,end=len(document['text']))],
                reason='No scorable content words after names/numbers/code holdouts'))
        folder=out/operation;folder.mkdir()
        (folder/'FEATURES.jsonl').write_bytes(b'fixture\n')
        answer=values,dict(slotLeaseSha256='fixture')
        saved.append(answer)
        return answer
    monkeypatch.setattr(card,'export',fake_export)
    first=card.execute(output,inputs,card.CONSTRUCTED)
    monkeypatch.setattr(card,'authenticated_export',lambda *a:saved[0])
    # The complete row-support check is independent of partial per-document logs.
    assert first['support']['original_rows']==3
    assert first['documents']==1 and not first['scientific_admission']
    assert not first['full_corpus_admitted'] and not first['ev2_support_pilot_complete']
    rows=gzread(output/'JOINED.json.gz')['rows']
    assert len(rows)==3 and all(r['engine'] is None for r in rows)
    assert first['support']['dispositions']['engine-unsupported-document']==1
    assert seen==['execute']
    assert card.verify(output,inputs,card.CONSTRUCTED)['summary']==first
    assert seen==['execute','verify']
    (output/'SUMMARY.json').write_bytes(b'{}\n')
    with pytest.raises(ValueError):card.verify(output,inputs,card.CONSTRUCTED)
