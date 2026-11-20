"""Constructed analytic, roster, read-order and Windows Access checks for R1.i."""
from math import sqrt
from pathlib import Path
import subprocess

import numpy as np
import pytest

from runners.drive.cards import week6_r1_isear_v1 as study
from runners.drive.cards import week6_r1_runner_v1 as runner


def reports():
    rows=[]
    for agency in range(1,5):
        for pleasant in range(1,4):
            for x in range(1,4):
                key = len(rows)//2+1
                shift = int(agency%2==0)
                for feeling, intensity in ((3,x+shift),(4,pleasant+shift)):
                    rows.append(dict(COUN=1,CITY=1,SUBJ=key,EMOT=feeling,INTS=intensity,
                                     EXPC=4-x,PLEA=pleasant,CAUS=agency))
    return rows


def samples(rows):
    roster, structural=study.source_roster(rows)
    return study.prepare(rows,roster,structural)


@pytest.mark.parametrize("replay",[False,True])
def test_planted_slope_and_authorized_adjustment(replay):
    paired,count=samples(reports())
    point=study.scores(paired,np.ones(count["complete_union"],dtype=int),replay)
    assert point==pytest.approx([sqrt(8/11),0.,sqrt(8/11)],abs=1e-10)


def test_original_and_independent_slopes_agree_in_whole_person_draws():
    paired,counts=samples(reports())
    for index in range(47):
        weights=study.draw_weights(counts["complete_union"],index)
        np.testing.assert_array_equal(weights,study.draw_weights(36,index))
        assert weights.sum()==36 and paired[0].indices.tolist()==paired[1].indices.tolist()
        assert runner.agrees(study.scores(paired,weights), study.scores(paired,weights,True))


def test_invalid_items_are_excluded_only_from_the_affected_feeling():
    rows=reports()
    rows[0].update(INTS="",CAUS=7)
    paired,counts=samples(rows)
    assert counts["complete"]==[35,36] and counts["complete_both"]==35 and counts["complete_union"]==36
    assert counts["invalid_items"][0]==dict(INTS=1,EXPC=0,PLEA=0,CAUS=1)
    assert 0 not in paired[0].indices and 0 in paired[1].indices


def test_site_and_country_are_both_part_of_the_person_key():
    rows=[dict(COUN=c,CITY=s,SUBJ="02",EMOT=f) for c,s in ((1,1),(2,1),(1,2)) for f in study.FEELINGS]
    _,support=study.source_roster(rows+[dict(COUN="",CITY=1,SUBJ=2,EMOT=3)])
    assert support["people_union"]==support["people_both"]==3 and support["missing_identity"]==[1,0]


def test_duplicate_refuses_before_items_are_requested(tmp_path,monkeypatch):
    data=tmp_path/"db";data.write_bytes(b"constructed")
    script=tmp_path/"reader";script.write_bytes(b"synthetic")
    note=tmp_path/"design";note.write_bytes(b"plan")
    rows=[{k:r[k] for k in runner.BASE_COLUMNS} for r in reports()]
    rows.append(rows[0])
    def projection(database,adapter,mode):
        assert mode=="Roster"
        return rows
    monkeypatch.setattr(runner,"EDITION",runner.filehash(data))
    monkeypatch.setattr(runner,"project",projection)
    inputs=dict(database=data,adapter=script,adapter_sha256=runner.filehash(script),
                design=note,design_sha256=runner.filehash(note))
    config=dict(draws=study.DRAWS,seed=study.SEED,max_wall_seconds=60)
    runner.execute(tmp_path/"out",inputs,config)
    assert runner.verify(tmp_path/"out",inputs,config)["verified"]
    assert runner.read(tmp_path/"out/verify/ENGINE_RESULT.json")["outcomes_read"] is False


def test_changed_membership_refuses_before_a_fit():
    rows=reports()
    roster,support=study.source_roster(rows)
    with pytest.raises(ValueError,match="rosters"):
        study.prepare(rows[:-1],roster,support)


@pytest.mark.parametrize("replay",[False,True])
def test_target_aliased_with_pleasantness_preserves_sibling(replay):
    rows=reports()
    for row in rows:
        if row["EMOT"]==3:
            row["EXPC"]=4-row["PLEA"]
    paired,counts=samples(rows)
    point=study.scores(paired,np.ones(counts["complete_union"],dtype=int),replay)
    assert point[0] is None and point[2] is None and point[1]==pytest.approx(0.,abs=1e-10)


def test_draw_bank_and_support_gate():
    counts={"complete":[19,45]}
    point=[.15,.03,.12]
    result=study.summarize(point,[point]*study.DRAWS,counts)
    assert result["anger"]["interval"] is None and result["sadness"]["interval"]==[.03,.03]
    assert result["joint_reading"]=="could not say"
    cuts=[[.15,None,None]]+[point]*(study.DRAWS-1)
    result=study.summarize(point,cuts,{"complete":[40,40]})
    assert result["anger"]["interval"]==[.15,.15] and result["sadness"]["defined_draws"]==1999
    assert result["anger_minus_sadness"]["interval"] is None


def test_true_access_projection_and_complete_independent_replay(tmp_path,monkeypatch):
    # A synthetic Access database exercises the installed provider and the production projection.
    rows=reports()
    database=tmp_path/"invented.mdb"
    setup=tmp_path/"create.ps1"
    statements=["CREATE TABLE [DATA] ("+",".join("["+k+"] INTEGER" for k in rows[0])+")"]
    statements.extend("INSERT INTO [DATA] VALUES ("+",".join(str(v) for v in row.values())+")" for row in rows)
    setup.write_text("""param([string]$Destination)
$ErrorActionPreference='Stop'
$catalog=New-Object -ComObject ADOX.Catalog
$catalog.Create(('Provider=Microsoft.ACE.OLEDB.12.0;Data Source='+$Destination+';Jet OLEDB:Engine Type=5'))
$db=$catalog.ActiveConnection
try {
"""+ "\n".join("$null=$db.Execute('"+s+"')" for s in statements)+"\n} finally { $db.Close() }\n",encoding="utf8")
    subprocess.run(["pwsh.exe","-NoLogo","-NoProfile","-NonInteractive","-File",str(setup),str(database)],
                   capture_output=True,check=True,timeout=60)
    adapter=Path(runner.__file__).with_name("week6_r1_projection.ps1")
    monkeypatch.setattr(runner,"EDITION",runner.filehash(database))
    seen=[]
    actual=runner.project
    def projection(file,script,mode):
        if mode=="Items":
            location="execute" if seen==["Roster"] else "verify"
            assert runner.read(tmp_path/"out"/location/"STRUCTURE.json")["people_both"]==36
        seen.append(mode)
        return actual(file,script,mode)
    monkeypatch.setattr(runner,"project",projection)
    inputs=dict(database=database,adapter=adapter,adapter_sha256=runner.filehash(adapter),
                design=setup,design_sha256=runner.filehash(setup))
    config=dict(draws=study.DRAWS,seed=study.SEED,max_wall_seconds=120)
    assert runner.execute(tmp_path/"out",inputs,config)["status"]=="computed"
    assert runner.verify(tmp_path/"out",inputs,config)["verified"] is True
    assert seen==["Roster","Items","Roster","Items"]
    engine=runner.read(tmp_path/"out/verify/ENGINE_RESULT.json")
    assert engine["point"]==pytest.approx([sqrt(8/11),0.,sqrt(8/11)],abs=1e-10)
    assert engine["estimates"]["joint_reading"]=="both registered bars met"
    assert len(list((tmp_path/"out/verify").glob("draws-*.json")))==40
