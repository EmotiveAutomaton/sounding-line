"""Disjoint menu units, independent rival selection and failed-row retention."""
import copy
import pytest
from runners.stage9.commit_cases import menus,wording,partition
from runners.stage9.commit_jobs import ARMS,select,evaluate
from runners.stage9.split_guard import Separation


def source(i):
    return {'key':str(i),'unit':str(i),'message':'change value '+str(i),'languages':['py'],
        'diff':f'diff --git a/f.py b/f.py\n--- a/f.py\n+++ b/f.py\n@@ -1 +1 @@\n-old = 1\n+value = {i}\n'}


def row(i,prob=.6,rival=.8,language='py'):
    distribution=lambda p:{'0':p,'1':(1-p)/3,'2':(1-p)/3,'3':(1-p)/3}
    return {'key':str(i),'unit':str(i),'candidate_units':[str(i)+'-'+str(n) for n in range(4)],'language':language,
        'truth':'0','valid':True,'probabilities':{k:distribution(prob if k=='all' else rival if k=='surface' else .25) for k in ARMS}}


def test_menu_repositories_and_content_order():
    rows=[source(i) for i in range(12)];a,ledger=menus(rows);b,other=menus(list(reversed(rows)))
    assert a==b and ledger==other and len(a)==3
    assert len({g for r in a for g in r['candidate_units']})==12
    assert sum(r['role']=='target' for r in ledger)==3 and sum(r['role']=='distractor' for r in ledger)==9
    for r in a:
        target=next(s for s in rows if s['key']==r['source_key'])
        assert r['evidence']['candidate_descriptions'][int(r['truth'])]==target['message']


def test_wording_and_reserve_fingerprints_without_source_payload():
    rows=[source(i) for i in range(9)];allocation={str(i):('train' if i<3 else 'development' if i<6 else 'evaluation') for i in range(9)}
    rows[0]['message']=rows[7]['message'];rows[3]['message']='reserved text'
    groups={'commitbench:'+str(i):{'split':'development'} for i in range(9)};groups['commitbench:reserved']={'split':'reserve'}
    cross=Separation(groups,{'long_overlap_edges':[]})
    split,excluded=partition(rows,allocation,cross,[{'group':'commitbench:reserved','roles':['candidate'],'text_sha256':wording('reserved text')}])
    assert {r['key'] for r in excluded}=={'0','3'}
    assert len(split['train'])==len(split['development'])==2 and len(split['evaluation'])==3


def test_strong_rival_invalid_zero_and_selection_overlap():
    selection=select([row('dev1'),row('dev2')]);assert selection['selected']=='surface'
    rows=[row('eval1'),row('eval2',language='js')];profile=evaluate(rows,selection,'pilot',draws=100)
    assert profile['contrasts']['selected_rival']['estimate']['mean']<0
    assert profile['source_repositories']==8 and profile['assigned']==2
    broken=copy.deepcopy(rows);broken[1]['valid']=False;broken[1]['probabilities']=None
    failed=evaluate(broken,selection,'pilot',draws=100)
    assert failed['disposition']=='IMPLEMENTATION INVALID' and failed['assigned']==2 and failed['excluded']==0 and failed['scored']==0
    zeros=[row('zero',prob=0,rival=0)];zero=evaluate(zeros,selection,'pilot',draws=100)
    assert zero['contrasts']['selected_rival']['estimate']['finite_estimate'] is False
    with pytest.raises(ValueError):evaluate(rows+[rows[0]],selection,'pilot',draws=100)
    reused=copy.deepcopy(rows);reused[0]['candidate_units'][0]='dev1-0'
    with pytest.raises(ValueError):evaluate(reused,selection,'pilot',draws=100)
