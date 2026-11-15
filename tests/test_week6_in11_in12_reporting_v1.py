"""Reporting-only successor checks; old statistics and completed fixtures retained."""
import ast
from pathlib import Path
import pytest
from runners.drive.cards import week5_in11_v1 as old11
from runners.drive.cards import week5_in12_v1 as old12
from runners.drive.cards import week6_in11_reporting_v1 as new11
from runners.drive.cards import week6_in12_reporting_v1 as new12

CASES=[((-.2,-.01),'against'),((-.2,0.),'inconclusive'),((-.1,.1),'against'),
       ((0.,.1),'against'),((.1,.1),'against'),((.1,.2),'inconclusive'),
       ((.1+1e-12,.2),'supports'),((-.1-1e-12,.1),'inconclusive'),
       ((-.1,.1+1e-12),'inconclusive'),((-.1,-.1),'against'),
       ((0.,0.),'against'),((0.,.2),'inconclusive')]


def without_labels(value):
    if isinstance(value,dict):return {k:without_labels(v) for k,v in value.items() if k!='outcome'}
    if isinstance(value,list):return [without_labels(v) for v in value]
    return value


def summaries(card,interval,writers=30,independent=False):
    lo,hi=interval;values=[lo]*1000+[hi]*1000
    if card=='IN11':
        point={'value':[(lo+hi)/2,.2,.3,.4,.5]}
        draws=[{'value':[v,v/2,2*v,.1+v,v-.1]} for v in values]
        return old11.summarize(point,draws,writers,independent),new11.summarize(point,draws,writers,independent)
    point={'value':{'pooled':(lo+hi)/2},'failures':{}}
    draws=[{'value':{'pooled':v}} for v in values]
    return old12.summarize('pooled',point,draws,writers,independent),new12.summarize('pooled',point,draws,writers,independent)


@pytest.mark.parametrize('card',['IN11','IN12'])
@pytest.mark.parametrize('interval,expected',CASES)
def test_signed_boundary_and_identical_known_summary(card,interval,expected):
    before,after=summaries(card,interval)
    assert without_labels(before)==without_labels(after)
    primary=after['primary'] if card=='IN11' else after
    assert primary['interval']==list(interval)
    assert primary['outcome']==expected


@pytest.mark.parametrize('card',['IN11','IN12'])
def test_reference_arithmetic_and_descriptive_scope_unchanged(card):
    before,after=summaries(card,(-.05,.05),independent=True)
    assert without_labels(before)==without_labels(after)
    before,after=summaries(card,(.2,.3),writers=19)
    assert before==after
    primary=after['primary'] if card=='IN11' else after
    assert 'outcome' not in primary
    if card=='IN12':
        point={'value':{'joy':.2},'failures':{}};draws=[{'value':{'joy':.2}}]*2000
        assert old12.summarize('joy',point,draws,30)==new12.summarize('joy',point,draws,30)


@pytest.mark.parametrize('old,new',[(old11,new11),(old12,new12)])
def test_only_namespace_and_outcome_expression_changed(old,new):
    class Normalize(ast.NodeTransformer):
        def visit_Assign(self,node):
            if len(node.targets)==1:
                target=node.targets[0]
                if isinstance(target,ast.Name) and target.id=='MODULE':node.value=ast.Constant('NAMESPACE')
                elif isinstance(target,ast.Subscript) and isinstance(target.slice,ast.Constant) and target.slice.value=='outcome':node.value=ast.Constant('LABEL')
            return self.generic_visit(node)
    a=Path(old.__file__).read_text();b=Path(new.__file__).read_text()
    assert ast.dump(Normalize().visit(ast.parse(a)),include_attributes=False)==ast.dump(Normalize().visit(ast.parse(b)),include_attributes=False)
    assert old.math is new.math and old.original is new.original
    assert old.MODULE!=new.MODULE
    for phase in (old.MODULE.split('.')[-1].split('_')[1].upper(),):
        assert old.settings({'phase':phase})==new.settings({'phase':phase})
