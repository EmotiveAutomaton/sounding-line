import csv
import pytest
from runners.drive.cards.week6_sm0_probe_v1 import run, inspect_table, column_map
from runners.drive.cards.week6_sealed_support_v1 import ReadBudget, SealedFailure

def table(tmp_path,ids,header=('M2ID','B2DDAY','B2DWEEKD','B2DC17','B2DC19')):
    root=tmp_path/'data';root.mkdir()
    p=root/'private_name.csv'
    with p.open('w',encoding='utf8',newline='') as f:
        w=csv.writer(f);w.writerow(header)
        for i in ids:w.writerow([i]+[2]*(len(header)-1))
    out=tmp_path/'out';out.mkdir()
    return root,p,out

def test_duplicate_people_count_once_and_only_aggregate_leaves(tmp_path):
    root,p,out=table(tmp_path,list(range(20))*5)
    run(root,out)
    text=(out/'structure.csv').read_text()
    row=list(csv.DictReader(text.splitlines()))[0]
    assert {k:row[k] for k in ('table','n','wave2_daily','wave3_daily','wave2_traits','wave3_traits')}==dict(table='table_001',n='20',wave2_daily='1',wave3_daily='0',wave2_traits='0',wave3_traits='0')
    assert 'private_name' not in text
    assert row['present_M2ID']=='1' and row['present_C1SNEURO']=='0'

def test_small_group_leaves_no_file(tmp_path):
    root,p,out=table(tmp_path,range(8))
    with pytest.raises(SealedFailure,match='No publishable'):run(root,out)
    assert not list(out.iterdir())

def test_missing_person_never_uses_rows(tmp_path):
    root,p,out=table(tmp_path,range(20),('record','value'))
    with pytest.raises(SealedFailure,match='person field'):run(root,out)
    assert not list(out.iterdir())

def test_cap_refuses_before_opening_table(tmp_path):
    root,p,out=table(tmp_path,range(20))
    with pytest.raises(SealedFailure,match='allowance'):run(root,out,max_bytes=1)
    assert not list(out.iterdir())

def test_casefold_ambiguity_refused():
    with pytest.raises(SealedFailure,match='Ambiguous'):column_map(['M2ID','m2id'])

def test_unknown_archive_not_treated_as_empty_population(tmp_path):
    root=tmp_path/'data';root.mkdir();(root/'file.zip').write_bytes(b'archive')
    out=tmp_path/'out';out.mkdir()
    with pytest.raises(SealedFailure,match='archives'):run(root,out)

def test_outside_root_refused(tmp_path):
    root,p,out=table(tmp_path,range(20))
    with pytest.raises(SealedFailure,match='outside'):inspect_table(p,ReadBudget(out))

def test_blank_identifiers_not_counted(tmp_path):
    root,p,out=table(tmp_path,['']*100+list(range(11)))
    assert inspect_table(p,ReadBudget(root))['n']==11

def test_ragged_input_fails_without_output(tmp_path):
    root,p,out=table(tmp_path,range(20))
    with p.open('a') as f:f.write('1,2\n')
    with pytest.raises(SealedFailure,match='Malformed'):run(root,out)
    assert not list(out.iterdir())
