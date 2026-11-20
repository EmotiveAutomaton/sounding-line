from pathlib import Path
import csv
import pytest

def load():
    p=Path(__file__).resolve().parents[1]/'runners/drive/sealed/week6-sm0/run.py'
    namespace={'__name__':'sealed_fixture'}
    exec(compile(p.read_text('utf8'),str(p),'exec'),namespace)
    return namespace

def test_self_contained_package_on_csv(tmp_path):
    mod=load();root=tmp_path/'data';root.mkdir();out=tmp_path/'out';out.mkdir()
    with (root/'dummy.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['M2ID','C1SNEURO','C1SEXTRA','C1SAGREE'])
        for i in range(11):w.writerow([i,1,2,3])
    mod['run'](root,out)
    row=list(csv.DictReader((out/'structure.csv').open()))[0]
    assert row['n']=='11' and row['wave3_traits']=='1'

@pytest.mark.parametrize('extension',['sav','dta'])
def test_self_contained_package_on_statistical_formats(tmp_path,extension):
    import pandas as pd
    import pyreadstat
    mod=load();root=tmp_path/'data';root.mkdir();out=tmp_path/'out';out.mkdir()
    frame=pd.DataFrame({'M2ID':[float(i) for i in range(11)]*3,'B2DDAY':[1.]*33,
        'B2DWEEKD':[2.]*33,'B2DC17':[1.]*33,'B2DC19':[2.]*33})
    getattr(pyreadstat,'write_'+extension)(frame,str(root/('data.'+extension)))
    mod['run'](root,out)
    row=list(csv.DictReader((out/'structure.csv').open()))[0]
    assert row['n']=='11' and row['wave2_daily']=='1'
