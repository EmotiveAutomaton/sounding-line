import csv,io,tarfile
import numpy as np
from runners.theory_days.moral import prepare,contrast,COLUMNS

def test_pairing_orphans_and_duplicates(tmp_path):
    s=io.StringIO();w=csv.writer(s);w.writerow(COLUMNS)
    w.writerow(['a','s','u','0','1','Hoomans','Species','Species'])
    w.writerow(['b','s','u','0','1','Fit','Fitness','Fitness'])
    w.writerow(['a','s','u','1','0','Pets','Species','Species'])
    for _ in range(3):w.writerow(['c','s','u','0','1','Females','Gender','Gender'])
    data=s.getvalue().encode();p=tmp_path/'x.tar.gz'
    with tarfile.open(p,'w:gz') as t:
        x=tarfile.TarInfo('data.csv');x.size=len(data);t.addfile(x,io.BytesIO(data))
    result=prepare(p,tmp_path/'x.sqlite',tmp_path/'out.gz')
    assert result['complete_valid_pairs']==1 and result['orphans']==1 and result['duplicated_responses']==1
    assert result['common_returning_fingerprints']==0

def test_signed_and_null_comparison():
    for index,expected in [(3,'supports'),(12,'against'),(0,'against')]:
        h=np.zeros(16,dtype=int);h[index]=10000
        result=contrast(h,10000);assert result['verdict']==expected and result['interval'][0]<result['interval'][1]
    assert contrast(np.ones(16,dtype=int)*1000,16000)['verdict']=='against'

def test_complete_literal_handler_replays(tmp_path):
    from runners.theory_days.validate_moral import execute,verify
    output=tmp_path/'new-output';execute(output,{},{});assert verify(output,{}, {})['verified']
