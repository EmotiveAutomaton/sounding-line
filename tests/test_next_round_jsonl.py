import pytest
from runners.next_round import intake_jsonl as intake


def test_schema_census_preserves_all_fields_and_refuses_invalid(tmp_path):
    p = tmp_path/'rows.jsonl'
    p.write_text('{"human":1}\n{"model":2}\n', encoding='utf8')
    assert intake.census(p)['fields'] == ['human','model']
    assert intake.census(p)['rows'] == 2
    for value in ('', 'null\n', '{bad}\n'):
        p.write_text(value, encoding='utf8')
        with pytest.raises(ValueError):
            intake.census(p)


@pytest.mark.parametrize('length,encoding,ceiling,valid', [(3,'identity',4,True),(4,'identity',4,False),(0,'identity',2,False),(3,'gzip',4,False)])
def test_transfer_integrity(tmp_path, monkeypatch, length, encoding, ceiling, valid):
    class Response:
        headers = {'Content-Length':str(length), 'Content-Encoding':encoding}
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def raise_for_status(self): pass
        def iter_content(self,*args): yield b'abc'
    class Session:
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def get(self,*args,**kwargs):
            assert kwargs['headers']['Accept-Encoding']=='identity'
            return Response()
    monkeypatch.setattr(intake.requests,'Session',Session)
    p=tmp_path/'data'
    if valid:
        assert intake.fetch('https://example.invalid',p,ceiling,lambda _:None)['bytes']==3
    else:
        with pytest.raises(ValueError):
            intake.fetch('https://example.invalid',p,ceiling,lambda _:None)
