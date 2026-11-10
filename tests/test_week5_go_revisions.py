from pathlib import Path
import xml.etree.ElementTree as ET
import pandas as pd
import py7zr
from runners.drive.cards import week5_go_revisions as source


def test_constructed_archive_whole_projection_drops_comment_and_ids(tmp_path,monkeypatch):
    posts=ET.Element('posts');ET.SubElement(posts,'row',Id='123',OwnerUserId='456')
    history=ET.Element('posthistory')
    ET.SubElement(history,'row',Id='1',PostId='123',PostHistoryTypeId='2',UserId='456',CreationDate='2020-01-01T00:00:00',Text='a speling mistake')
    ET.SubElement(history,'row',Id='2',PostId='123',PostHistoryTypeId='5',UserId='456',CreationDate='2020-01-01T00:01:00',Text='a spelling mistake',Comment='fix spelling')
    ET.SubElement(history,'row',Id='3',PostId='123',PostHistoryTypeId='5',UserId='789',CreationDate='2020-01-01T00:02:00',Text='a spelling mistake explained',Comment='add explanation')
    for name,root in [('Posts.xml',posts),('PostHistory.xml',history)]:ET.ElementTree(root).write(tmp_path/name,encoding='utf-8',xml_declaration=True)
    archive=tmp_path/'fixture.7z'
    with py7zr.SevenZipFile(archive,'w') as stream:
        for name in ['Posts.xml','PostHistory.xml']:stream.write(tmp_path/name,arcname=name)
    monkeypatch.setitem(source.ARCHIVES,'writers',source.core.sha(archive))
    a=source.project_site(archive,b'x'*32,'writers',tmp_path/'run')
    b=source.project_site(archive,b'x'*32,'writers',tmp_path/'replay')
    assert a==b and a['retained_edits']==2
    data=pd.read_parquet(tmp_path/'run/edits.parquet')
    assert data.reason.tolist()==['typo_spelling','added_content']
    assert data.self_edit.tolist()==[True,False]
    assert 'comment' not in data.columns and data.editor.str.len().eq(64).all()


def test_actual_revision_feature_and_baseline_fixture():
    assert source.fixture()['passed']
