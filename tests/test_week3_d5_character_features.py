from pathlib import Path

import pytest

from runners.drive.cards import week3_d5_character_features as card
from runners.drive.cards import week3_d5_features as words
from runners.stage14.common import freeze, read, filehash
from tests.test_week3_d5_features import fixture


def test_exact_counts_and_no_invented_cross_gap_sequence():
    r=card.counts(['ababa','cc'])
    assert r['counts']['2']=={'ab':2,'ba':2,'cc':1}
    assert r['counts']['3']=={'aba':2,'bab':1}
    assert r['counts']['4']=={'abab':1,'baba':1}
    assert r['opportunities']=={'2':5,'3':3,'4':2}
    assert 'ac' not in r['counts']['2']


def test_unicode_case_and_whitespace_are_exact_codepoints():
    s='A\U0001f600\u00e9\nA'
    r=card.counts([s])
    assert r['codepoints']==5 and r['counts']['2']=={'A\U0001f600':1,'\U0001f600\u00e9':1,'\u00e9\n':1,'\nA':1}
    assert card.counts(['AA'])['counts']['2']!=card.counts(['aa'])['counts']['2']


def test_prefix_keeps_raw_spans_and_excludes_trailing_punctuation():
    groups=['  Can','not, go! trailing']
    assert card.prefix_groups(groups,1)==['  Can']
    assert card.prefix_groups(groups,2)==['  Can','not']
    assert card.prefix_groups(groups,3)==['  Can','not, go']
    assert card.prefix_groups(groups,5) is None
    assert card.prefix_groups(['!','a'],1)==['!','a']
    with pytest.raises(ValueError):card.prefix_groups(groups,0)


def test_empty_short_and_prefix_word_parity():
    f=fixture();u=f['units'][0];r=card.prepare(u);w=words.prepare(u,f['dictionary'])
    assert r['human']['words']==w['human']['words']
    for n in words.LENGTHS:
        p=r['human_prefixes'][str(n)];q=w['human_prefixes'][str(n)]
        assert p['supported']==q['supported']
        if p['supported']:assert p['words']==q['words']==n
    assert card.counts([])['opportunities']=={'2':0,'3':0,'4':0}
    assert card.counts(['a','b'])['counts']['2']=={}


def test_complete_handler_immutable_reentry_replay_and_tamper(tmp_path):
    path=tmp_path/'fixture.json';freeze(path,fixture());out=tmp_path/'output';inputs={'fixture':str(path)}
    card.execute(out,inputs,card.CONSTRUCTED)
    hashes={str(p):filehash(p) for p in out.rglob('*') if p.is_file()}
    card.execute(out,inputs,card.CONSTRUCTED)
    assert hashes=={str(p):filehash(p) for p in out.rglob('*') if p.is_file()}
    assert card.verify(out,inputs,card.CONSTRUCTED)['full_fresh_character_replay']
    (out/'SUMMARY.json').write_text('{}',encoding='utf-8')
    with pytest.raises(ValueError,match='replay'):card.verify(out,inputs,card.CONSTRUCTED)


def test_duplicate_population_and_yield(tmp_path):
    f=fixture();f['units'][1]['session']=f['units'][0]['session'];bad=tmp_path/'bad.json';freeze(bad,f)
    with pytest.raises(ValueError,match='census'):card.execute(tmp_path/'bad',{'fixture':str(bad)},card.CONSTRUCTED)
    path=tmp_path/'fixture.json';freeze(path,fixture());out=tmp_path/'out';out.mkdir();freeze(out/'YIELD_REQUEST.json',{})
    assert card.execute(out,{'fixture':str(path)},card.CONSTRUCTED)['status']=='yielded'
    assert not (out/'SUMMARY.json').exists()


def test_actual_complete_producer_and_word_prefix_agreement(tmp_path):
    root=Path(__file__).resolve().parents[1]
    inputs=dict(source_complete=str(root/'results/phase_2_4_stage_15/raw/drive-week3-20261025/D5-inputs-h1-v2/COMPLETE.json'),
                pmap_complete=str(root/'results/phase_2_4_stage_15/raw/drive-wave-20261017-w1/PMAP-recovery/COMPLETE.json'))
    if not Path(inputs['source_complete']).exists():pytest.skip('private completed producer unavailable')
    units,bindings=card.load(inputs,card.CONFIG)
    assert len(units)==1399 and len({u['writer'] for u in units})==61
    u=units[0];r=card.prepare(u)
    assert r['final']['words']==card.word_count([u['final_document']])
    for n,p in r['human_prefixes'].items():
        if p['supported']:assert p['words']==int(n)
    bad=tmp_path/'COMPLETE.json';c=read(inputs['source_complete']);c['outputs']['PLAN.json']='0'*64;freeze(bad,c)
    (tmp_path/'PLAN.json').write_bytes((Path(inputs['source_complete']).parent/'PLAN.json').read_bytes())
    with pytest.raises(ValueError):card.load(dict(inputs,source_complete=str(bad)),card.CONFIG)
