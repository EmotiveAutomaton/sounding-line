import csv
import pytest
from runners.drive.cards.week7_crv1_timing import summarize


@pytest.mark.parametrize('measure,expected',[('vowel_ms',5.),('syllables_per_phonation_second',-1.)])
def test_pairs_weight_sessions_then_parents(tmp_path, measure, expected):
    path=tmp_path/'fixture.csv'
    with path.open('w',newline='') as f:
        w=csv.writer(f)
        w.writerow(['id_parent','session','register','vowel_dur','phonation_time_ms','n_syllables'])
        for i in range(20):
            for session,gap in [('s1',0),('s2',10)]:
                w.writerow([i,session,'ADS',100,500,3])
                for _ in range(1 if session=='s1' else 3):
                    w.writerow([i,session,'IDS',100+gap,500,3-gap//10])
        w.writerow([0,'s3','IDS',999,100,30])
        w.writerow([0,'s1','ADS','NA','NA',4])
    row=summarize(path,measure)
    assert row['people']==20 and row['paired_sessions']==40 and row['unpaired_sessions']==1
    assert row['mean']==expected and row['interval']==[expected,expected]
    assert row['excluded']=={'missing_measure':1}


def test_register_is_bound(tmp_path):
    f=tmp_path/'unknown.csv'
    f.write_text('id_parent,session,register,vowel_dur\na,1,unknown,300\n')
    with pytest.raises(ValueError,match='register'):
        summarize(f,'vowel_ms')
