import io,tarfile
import pyarrow as pa
from runners.theory_days.backlog_intake import moral_header,chess_prefix

def test_literal_tar_schema_and_zstd(tmp_path):
    p=tmp_path/'source.tar.gz'
    text=b'ResponseID,ExtendedSessionID,UserID,Intervention,Saved,AttributeLevel,ScenarioType,ScenarioTypeStrict\n'
    with tarfile.open(p,'w:gz') as t:
        x=tarfile.TarInfo('SharedResponses.csv');x.size=len(text);t.addfile(x,io.BytesIO(text))
    assert moral_header(p)['expanded_bytes']==len(text)
    z=tmp_path/'source.zst'
    with pa.CompressedOutputStream(str(z),'zstd') as f:f.write(b'[Event "constructed"]\n1. e4 {[%eval 0.1] [%clk 0:05:00]} *\n')
    probe=chess_prefix(z);assert probe['events']==probe['clocks']==probe['evaluations']==1
