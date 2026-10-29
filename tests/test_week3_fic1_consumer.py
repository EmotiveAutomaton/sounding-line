import copy
import pytest
from threadpoolctl import threadpool_limits
from runners.drive.cards import week3_fic1_consumer as m


@pytest.fixture(scope='module')
def prepared():
    with threadpool_limits(limits=1):
        return m.context.prepare(m.world('writer_plant'),m.CONFIG)


def test_world_has_explicit_known_raw_words_and_timing():
    data=m.world('writer_plant')
    assert len(data['units'])==72 and len(data['rows'])==72
    for u,r in zip(data['units'],data['rows']):
        i=int(u['writer'][1:])
        assert u['whole']['word_counts']=={m.WORDS[i]:12}
        assert u['whole']['within_intervals']==pytest.approx([(10+7*i)/1000]*len(u['whole']['within_intervals']))
        assert r['final_counts']['word_counts']==u['whole']['word_counts']


def test_strong_observed_and_independent_context_routing(prepared):
    for spec in m.variants(prepared):
        assert set(m.joined(prepared,spec,'observed').values())=={1.}
        assert list(m.joined(prepared,spec,'context').values())==pytest.approx([1/6]*9)


def test_prompt_only_arms_equal():
    with threadpool_limits(limits=1):
        p=m.context.prepare(m.world('prompt_only'),m.CONFIG)
    for spec in m.variants(p):
        assert m.joined(p,spec,'observed')==m.joined(p,spec,'context')


def test_missing_fixed_matrix_is_unsupported(prepared):
    p=copy.deepcopy(prepared);spec=m.variants(p)[0];name,genre,_=spec
    p['rotations'][0]['observed'][name][genre]['state']='unsupported'
    assert m.joined(p,spec,'observed') is None
    assert m.joined(p,spec,'context') is not None


@pytest.mark.parametrize('damage',['gallery','duplicate_probe','donor_overlap','missing_probe'])
def test_rotation_corruption_refused(prepared,damage):
    p=copy.deepcopy(prepared);spec=m.variants(p)[0];name,genre,_=spec
    if damage=='gallery':p['rotations'][0]['observed'][name][genre]['writers'].reverse()
    elif damage=='duplicate_probe':p['rotations'][1]['probes'][name]+=p['rotations'][0]['probes'][name][:1]
    elif damage=='donor_overlap':p['rotations'][0]['donors']+=p['rotations'][0]['galleries'][name][:1]
    else:p['rotations'][0]['probes'][name].pop()
    with pytest.raises(ValueError):m.joined(p,spec,'observed')


def test_short_reference_has_no_inference_and_is_order_invariant():
    d=m.world('writer_plant')
    with threadpool_limits(limits=1):
        a=m.evaluate(d,draws=2)
        d['units'].reverse();d['rows'].reverse();b=m.evaluate(d,draws=2)
    assert a==b and not a['comparisons'] and all(len(x)==2 for x in a['banks'].values())
    with pytest.raises(ValueError,match='full reference'):m.known_answer('writer_plant',a)


def test_draw_reconstruction_cannot_change_topology(monkeypatch,prepared):
    original=m.context.prepare
    def wrong(data,config,labels=None):
        p=original(data,config,labels)
        if labels is not None:p['rosters']['style.full'].pop()
        return p
    monkeypatch.setattr(m.context,'prepare',wrong)
    with threadpool_limits(limits=1),pytest.raises(ValueError,match='topology'):
        m.evaluate(m.world('writer_plant'),draws=1)


def test_human_handler_and_foreign_fixture_refused(tmp_path):
    p=tmp_path/'fixture.json';m.freeze(p,m.FIXTURE)
    with pytest.raises(ValueError,match='constructed-only'):
        m.execute(tmp_path/'out',dict(fixture=str(p)),dict(m.CONFIG,mode='human'))
    p2=tmp_path/'bad.json';m.freeze(p2,dict(constructed=True,worlds=['writer_plant']))
    with pytest.raises(ValueError,match='constructed-only'):
        m.execute(tmp_path/'out',dict(fixture=str(p2)),m.CONFIG)
