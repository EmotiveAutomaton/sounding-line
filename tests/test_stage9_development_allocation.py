import copy
from collections import Counter
import pytest
from runners.stage9.development_allocation import declaration,support_inventory,validate


@pytest.mark.parametrize('original',[2,12,24,72])
def test_exact_empty_sets_and_preserved_marginals(original):
    spec=declaration(original);counts=validate(spec,'development',original);support=support_inventory()
    assert len(counts)==96 and sum(counts)==96*original
    assert sum(n==0 for n in counts)==8
    assert all((n>0)==(s['parameter_counts']['development']>0) for n,s in zip(counts,support))
    for dimensions in ((0,3),(0,3,1),(0,3,2)):
        actual=Counter();expected=Counter()
        for row in spec['counts']:
            group=tuple(row['cohort'][i] for i in dimensions)
            actual[group]+=row['count'];expected[group]+=original
        assert actual==expected
    assert all(s['parameter_counts'][role]>0 for s in support for role in ('training','discovery','reserve'))


@pytest.mark.parametrize('role',['training','discovery','reserve','pilot'])
def test_repair_cannot_change_another_source_role(role):
    with pytest.raises(ValueError,match='confined to development'):validate(declaration(2),role,2)


@pytest.mark.parametrize('fault',['empty','omission','reorder','count','support'])
def test_modified_support_or_allocation_refuses(fault):
    spec=copy.deepcopy(declaration(2))
    if fault=='empty':next(row for row in spec['counts'] if row['count']==0)['count']=1
    elif fault=='omission':spec['counts'].pop()
    elif fault=='reorder':spec['counts'].reverse()
    elif fault=='count':spec['counts'][0]['count']+=1
    else:spec['finite_support_sha256']='0'*64
    with pytest.raises(ValueError,match='exact reviewed support'):validate(spec,'development',2)


@pytest.mark.parametrize('number',[0,1,3,True,2.0])
def test_unreviewed_fractional_or_insufficient_quotas_refuse(number):
    with pytest.raises(ValueError,match='positive even'):declaration(number)
