from runners.drive.cards.week5_la_followup import analyze


def test_next_act_branch_refuses_absent_matches():
    rows=[dict(id='a',meeting='m',speaker='s',act_type='x',start=0,end=1,word_count=3,surprise=2,laughed_after=True)]
    result=analyze(rows,20)
    assert result['state']=='unsupported' and result['missing_next']==1
