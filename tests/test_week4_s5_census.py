from runners.drive.cards.week4_s5_census import summarize
from runners.drive.cards.week4_s5_h1 import extract
from tests.test_week4_s5_h1 import row
def test_unsupported_keeps_all_gap_classes_without_fitting_primary():
    rows,_=extract([row(0,'IMPLEMENTATION','Text Production'),row(1000,'PLANNING','Idea Generation'),
        row(2000,'PLANNING','Idea Generation'),row(1900000,'IMPLEMENTATION','Text Production')])
    summary,private=summarize(rows)
    assert summary['distributions']['category']['PLANNING']['run_starts']['n']==1
    assert summary['distributions']['category']['PLANNING']['inside_runs']['n']==1
    assert summary['distributions']['category']['IMPLEMENTATION']['long_breaks']['n']==1
    assert summary['mixture_states']=={'unsupported':1} and 'estimate' not in summary
