import json,sqlite3
from pathlib import Path
import pytest
from runners.drive.cards import week5_id_source_checkpointed as s


def test_source_row_ordinal_and_snapshot_are_same_transaction(tmp_path):
    binding={'source':'constructed'};db,state=s.open_state(tmp_path,binding)
    state['rows']=123;s.state_write(db,state);db.commit();db.close();s.seal(tmp_path,state)
    db,reloaded=s.open_state(tmp_path,binding);assert reloaded['rows']==123;db.close()
    db=sqlite3.connect(tmp_path/'pairs.sqlite');db.execute('UPDATE checkpoint SET value=?',(json.dumps(dict(state,rows=124)),));db.commit();db.close()
    with pytest.raises(ValueError,match='snapshot changed'):s.open_state(tmp_path,binding)


def test_archive_census_and_exact_five_percent_are_frozen():
    import math
    assert s.SOURCE_ROWS==70332355
    assert s.PILOT_ROWS==math.ceil(s.SOURCE_ROWS*.05)==3516618
