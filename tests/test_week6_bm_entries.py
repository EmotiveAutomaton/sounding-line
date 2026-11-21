"""Local synthetic SPSS integration with the actual package and gate."""
from pathlib import Path
import csv
import json
import os
import subprocess
import sys
import pytest

R=Path(__file__).resolve().parents[1]
SOURCE=R/'runners/drive/sealed/week6-sm-science'
SYN=R/'.agent-state/drive-20261115/lattice-20261120/spark-family-constructed-v2'
GATE=R/'.agent-state/drive-20261115/lattice-20261119/intake/unpacked/PREFLIGHT_2026-11-19/spark/sealed_gate.py'


@pytest.fixture(scope='module')
def mounted(tmp_path_factory):
    sys.path.insert(0,str(SOURCE))
    import build_bm
    code=tmp_path_factory.mktemp('code')
    for name,src in build_bm.bm_sources().items():
        (code/(name+'.py')).write_text(src,'utf8')
    sys.path.insert(0,str(code))
    # The preserved reader is code for synthetic SPSS fixtures as well as the sealed image.
    reader=R/'.agent-state/drive-20261115/lattice-20261119/fixture-reader-native'
    sys.path.insert(0,str(reader))
    import pyreadstat
    assert callable(pyreadstat.read_sav) and issubclass(pyreadstat.ReadstatError,Exception)
    import bm_entry,bm_numeric,daily_bank,argument_bank
    manifest=json.loads((SYN/'MANIFEST.json').read_text('utf8'))
    assert manifest['constructed_only'] and manifest['private_source_reads']==0
    # Exercise the same point, roster and independent-draw paths on this local fixture.
    # Scientific packages retain the original two thousand draws per study.
    bm_numeric.DRAW_COUNT=daily_bank.DRAWS=argument_bank.DRAWS=2
    yield bm_entry,manifest
    sys.path.remove(str(reader));sys.path.remove(str(code));sys.path.remove(str(SOURCE))


@pytest.mark.parametrize('job',['main','nt1','d5'])
def test_individual_joined_job(mounted,tmp_path,job):
    entry,manifest=mounted
    out=tmp_path/'out';out.mkdir()
    entry.run_layout(SYN,manifest['sources'],job,out)
    passed=subprocess.run([sys.executable,'-B',str(GATE),str(out)],capture_output=True,text=True)
    assert passed.returncode==0 and 'gate passed' in passed.stdout
    with (out/'table_status.csv').open() as f:status=list(csv.DictReader(f))
    assert status and all(int(row['n'])==manifest['people'] for row in status)
    if job!='main':assert len(status)==1
    else:
        with (out/'counts.csv').open() as f:counts=list(csv.DictReader(f))
        assert counts and all(int(row['n'])>=11 for row in counts)

