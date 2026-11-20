import csv
from pathlib import Path
from unittest.mock import patch
import pytest
from runners.drive.cards import week6_sm0_probe_v2 as probe


def setup(tmp_path):
    root=tmp_path/'data';root.mkdir();out=tmp_path/'out';out.mkdir()
    mapping=dict(schema_version=1,source_alias='midus-m2-joined',tables=[dict(path='daily.csv',person_column='M2ID',role='daily')])
    return root,out,mapping


def table(root,name='daily.csv',people=20,header=('M2ID','B2DDAY','B2DWEEKD','B2DC17','B2DC19')):
    path=root/name;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf8',newline='') as stream:
        writer=csv.writer(stream);writer.writerow(header)
        for i in range(people):
            for repeat in range(3):writer.writerow([i]+[2]*(len(header)-1))
    return path


def status(out):
    with (out/'status.csv').open() as stream:return list(csv.DictReader(stream))[0]


def test_empty_source_still_writes_status(tmp_path):
    root,out,m=setup(tmp_path);r=probe.run(root,out,m)
    assert status(out)['disposition']=='none_loaded' and r['status']['missing_files']==1
    assert not (out/'structure.csv').exists() and not r['source_admitted']


def test_archive_only_listing_is_retained(tmp_path):
    root,out,m=setup(tmp_path);(root/'release.zip').write_bytes(b'constructed')
    r=probe.run(root,out,m)['status']
    assert (r['listed_files'],r['archive_files'],r['loaded_tables'])==(1,1,0)


def test_no_people_denominator_is_invented(tmp_path):
    root,out,m=setup(tmp_path);probe.run(root,out,m)
    row=status(out);assert 'n' not in row and row['record_kind']=='source_layout'


def test_duplicate_people_are_still_counted_once(tmp_path):
    root,out,m=setup(tmp_path);table(root);r=probe.run(root,out,m)
    with (out/'structure.csv').open() as stream:row=list(csv.DictReader(stream))[0]
    assert row['n']=='20' and r['status']['disposition']=='mapped_tables_loaded'


def test_small_cohort_keeps_metadata_only(tmp_path):
    root,out,m=setup(tmp_path);table(root,people=8);r=probe.run(root,out,m)['status']
    assert r['loaded_tables']==r['suppressed_tables']==1 and r['exported_tables']==0
    assert not (out/'structure.csv').exists()


def test_missing_person_does_not_erase_listing(tmp_path):
    root,out,m=setup(tmp_path);table(root,header=('record','value'));r=probe.run(root,out,m)['status']
    assert (r['listed_files'],r['failed_tables'],r['loaded_tables'])==(1,1,0)


def test_one_failed_table_does_not_hide_other_table(tmp_path):
    root,out,m=setup(tmp_path);table(root);table(root,'survey.csv',header=('wrong','value'))
    m['tables'].append(dict(path='survey.csv',person_column='M2ID',role='survey'))
    r=probe.run(root,out,m)['status'];assert r['disposition']=='partial' and r['loaded_tables']==r['failed_tables']==1


def test_read_ceiling_retains_status_without_population(tmp_path):
    root,out,m=setup(tmp_path);table(root);r=probe.run(root,out,m,max_read_bytes=1)['status']
    assert r['failed_tables']==1 and r['reserved_read_bytes']==r['loaded_tables']==0


def test_legacy_alias_is_not_retried(tmp_path):
    root,out,m=setup(tmp_path);table(root);m['source_alias']='midus'
    with patch.object(probe,'inspect_table',side_effect=AssertionError('no data read')) as loader:
        r=probe.run(root,out,m)['status']
        loader.assert_not_called()
    assert not r['mapping_valid'] and r['listed_files']==1


def test_second_joined_alias_is_accepted(tmp_path):
    root,out,m=setup(tmp_path);table(root);m['source_alias']='midus-m3-joined'
    assert probe.run(root,out,m)['status']['mapping_valid']==1


def test_escaping_path_is_rejected(tmp_path):
    root,out,m=setup(tmp_path);m['tables'][0]['path']='../outside.csv'
    assert probe.run(root,out,m)['status']['disposition']=='mapping_invalid'


def test_absolute_path_is_rejected(tmp_path):
    root,out,m=setup(tmp_path);m['tables'][0]['path']='/data/daily.csv'
    assert probe.run(root,out,m)['status']['mapping_valid']==0


def test_ambiguous_duplicate_mapping_is_rejected(tmp_path):
    root,out,m=setup(tmp_path);m['tables'].append(dict(path='DAILY.csv',person_column='M2ID',role='survey'))
    assert probe.run(root,out,m)['status']['mapping_valid']==0


def test_unreviewed_person_key_is_not_guessed(tmp_path):
    root,out,m=setup(tmp_path);m['tables'][0]['person_column']='row_number'
    assert probe.run(root,out,m)['status']['mapping_valid']==0


def test_listing_failure_is_not_empty_complete_source(tmp_path):
    root,out,m=setup(tmp_path)
    real=probe.os.scandir
    def scan(path):
        if Path(path)==root:raise PermissionError('constructed refusal')
        return real(path)
    with patch.object(probe.os,'scandir',side_effect=scan):r=probe.run(root,out,m)['status']
    assert r['disposition']=='layout_incomplete' and r['listing_errors']==1 and r['listing_complete']==0


def test_listing_bound_refuses_data_reads(tmp_path):
    root,out,m=setup(tmp_path);table(root);(root/'other.txt').write_text('constructed')
    with patch.object(probe,'inspect_table',side_effect=AssertionError('no data read')) as loader:
        r=probe.run(root,out,m,max_entries=1)['status']
        loader.assert_not_called()
    assert r['scan_limited']==1 and r['listing_complete']==0


def test_nonempty_destination_is_preserved(tmp_path):
    root,out,m=setup(tmp_path);p=out/'keep';p.write_text('retained')
    with pytest.raises(ValueError,match='Fresh'):probe.run(root,out,m)
    assert p.read_text()=='retained'


def test_source_cannot_be_output_destination(tmp_path):
    root,out,m=setup(tmp_path);inside=root/'out';inside.mkdir()
    with pytest.raises(ValueError,match='outside'):probe.run(root,inside,m)


def test_unknown_metadata_field_is_rejected(tmp_path):
    root,out,m=setup(tmp_path);s=probe.run(root,out,m)['status'];s['raw_name']='private'
    with pytest.raises(ValueError,match='schema'):probe.status_payload(s)


def test_boolean_counter_is_rejected(tmp_path):
    root,out,m=setup(tmp_path);s=probe.run(root,out,m)['status'];s['listed_files']=True
    with pytest.raises(ValueError,match='integer'):probe.status_payload(s)


def test_filenames_and_errors_never_leave(tmp_path):
    root,out,m=setup(tmp_path);(root/'sensitive_filename.zip').write_bytes(b'constructed')
    probe.run(root,out,m);text=(out/'status.csv').read_text()
    assert 'sensitive_filename' not in text and 'constructed' not in text


def test_unclassified_reader_failure_still_has_status(tmp_path):
    root,out,m=setup(tmp_path);table(root)
    with patch.object(probe,'inspect_table',side_effect=RuntimeError('private failure detail')):
        r=probe.run(root,out,m)['status']
    assert r['failed_tables']==r['unclassified_load_failures']==1
    assert 'private failure detail' not in (out/'status.csv').read_text()


def test_unbounded_metadata_counter_is_rejected(tmp_path):
    root,out,m=setup(tmp_path);s=probe.run(root,out,m)['status'];s['listed_files']=probe.MAX_ENTRIES+1
    with pytest.raises(ValueError,match='bound'):probe.status_payload(s)
