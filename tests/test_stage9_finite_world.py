from runners.stage9.finite_world import case
from runners.stage9.automata import accepts,evaluate


def test_existing_constructor_realizes_long_distinction_and_commuting_compression():
    for domain in ('essay','workshop_doc'):
        c=case(0,domain)
        for name in ('distinction','compression'):
            pair=c[name];a,b=pair['left'],pair['right']
            left=lambda s:accepts(a,a['initial'],s)
            right=lambda s:accepts(b,b['initial'],s)
            result=evaluate(left,right,left,right,a['alphabet'],4)
            assert result['precision']==1
            if name=='distinction':
                assert pair['one_step_support_identical']
                assert len(pair['separator']['suffix'])>=2
                assert result['recall']==1
            else:
                assert result['true_boundary_size']==0
                assert result['recall'] is None
