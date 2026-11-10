import pytest
from runners.drive.cards import week5_go2_single_author as cell


@pytest.mark.parametrize('flag',[None,0,'false'])
def test_historical_authorship_unknown_refuses(tmp_path,flag):
    path=tmp_path/'anchors.json';cell.core.write(path,dict(anchors=[dict(historical_multi_author=flag)]))
    with pytest.raises(ValueError,match='Historical multi-author'):
        cell.execute(tmp_path/'output',dict(anchors=str(path)),dict(draws=200))


def test_all_multi_author_is_explicit_unsupported(tmp_path):
    path=tmp_path/'anchors.json';cell.core.write(path,dict(anchors=[dict(historical_multi_author=True)]))
    value=cell.execute(tmp_path/'output',dict(anchors=str(path)),dict(draws=200))
    assert value['status']=='unsupported' and value['multi_author_history_anchors_excluded']==1
    assert cell.verify(tmp_path/'output',dict(anchors=str(path)),dict(draws=200))['verified']
