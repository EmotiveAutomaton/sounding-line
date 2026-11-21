"""File-level synthetic rehearsal of the three fixed disclosure outcomes."""
import csv,importlib.util,subprocess,sys
from pathlib import Path
import pytest
from runners.drive.cards import week6_sealed_support_v1 as support
BASE=Path(__file__).resolve().parents[1]
SRC=BASE/'runners/drive/sealed/week6-sm-science/independent_release.py'
sys.modules.setdefault('week6_sealed_support_v1',support)
spec=importlib.util.spec_from_file_location('independent_release',SRC)
bm=importlib.util.module_from_spec(spec);sys.modules[spec.name]=bm;spec.loader.exec_module(bm)
GATE=BASE/'.agent-state/drive-20261115/lattice-20261119/intake/unpacked/PREFLIGHT_2026-11-19/spark/sealed_gate.py'


def from_file(path):
    with path.open(newline='') as stream:
        records=list(csv.DictReader(stream))
    people=frozenset(int(row['person']) for row in records)
    table=[]
    for ix,name in enumerate(('main','daily','argument'),1):
        rows=[]
        for level in (1,2,3):
            group=frozenset(int(row['person']) for row in records if int(row[name])>=level)
            rows.append(bm.Entry(dict(n=len(group),parameter=level),group))
        table.append((ix,name,rows))
    return people,table


@pytest.mark.parametrize('case',['small','complement','sound'])
def test_three_file_cases(tmp_path,case):
    path=tmp_path/'constructed.csv'
    with path.open('w',newline='') as stream:
        w=csv.writer(stream);w.writerow(('person','main','daily','argument'))
        for p in range(100):
            normal=3 if p<30 else 2 if p<50 else 1 if p<70 else 0
            daily=(3 if p<7 else 0) if case=='small' else (3 if p<46 else 2 if p<50 else 1 if p<70 else 0) if case=='complement' else normal
            w.writerow((p,normal,daily,normal))
    people,tables=from_file(path)
    for ix in (1,2,3):
        folder=tmp_path/str(ix);folder.mkdir()
        bm.write_job(folder,tables,people,{ix})
        check=subprocess.run([sys.executable,'-B',str(GATE),str(folder)],capture_output=True,text=True)
        assert check.returncode==0 and 'gate passed' in check.stdout
        with (folder/'table_status.csv').open() as stream:s,=csv.DictReader(stream)
        assert int(s['n'])==100
        if ix==2 and case=='small':
            assert s['reason']==str(bm.BELOW) and not (folder/'daily.csv').exists()
        else:
            name=tables[ix-1][1]
            with (folder/(name+'.csv')).open() as stream:rows=list(csv.DictReader(stream))
            assert len(rows)==(2 if ix==2 and case=='complement' else 3)
            assert all(int(row['n'])>=11 for row in rows)


def test_true_file_floor_only():
    with pytest.raises(support.SealedFailure) as exc:bm.decide([],range(10))
    assert exc.value.code==12
    _,status=bm.decide([(1,'main',None)],range(11))
    assert status==[dict(table=1,kept=0,reason=bm.MISSING,n=11)]


def test_disclosure_across_outputs():
    # Two overlapping published rosters can reveal a one-person difference.
    universe=frozenset(range(60));a=frozenset(range(30));b=frozenset(range(29))
    table=[(1,'main',[bm.Entry(dict(n=30),a)]),(2,'daily',[bm.Entry(dict(n=29),b)])]
    rows,status=bm.decide(table,universe)
    assert set(rows)=={'main'} and status[1]['reason']==bm.COMPLEMENT


def test_known_survey_and_diary_are_checked_together():
    diary=frozenset(range(50))
    survey=frozenset(range(20,85))
    subgroup=frozenset(range(21,50))
    tables=[(1,'counts',[bm.Entry(dict(n=65),survey)]),
            (2,'daily',[bm.Entry(dict(n=29),subgroup)])]
    rows,status=bm.decide(tables,diary,[survey])
    assert set(rows)=={'counts'} and status[1]['reason']==bm.COMPLEMENT


def test_small_existing_overlap_cannot_acquire_new_subgroups():
    diary=frozenset(range(40))
    survey=frozenset(range(39,80))
    subgroup=frozenset(range(20))
    tables=[(1,'main',[bm.Entry(dict(n=40),diary)]),
            (2,'daily',[bm.Entry(dict(n=20),subgroup)])]
    rows,status=bm.decide(tables,diary,[survey])
    assert set(rows)=={'main'} and status[1]['reason']==bm.COMPLEMENT

