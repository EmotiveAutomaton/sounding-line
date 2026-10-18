"""Canonical choice, rank invariance and independent fake-graph known answers."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from runners.drive.cards import menus_d12_rank as m
from runners.drive.cards import menus_d12_rank_stats as s
from runners.drive.cards.menus_io import read,write,sha256


def fixture(root,mode="positive"):
    root=Path(root).resolve();root.mkdir(parents=True,exist_ok=False)
    base=root/"results/phase_2_4_stage_15/raw";audit=root/"audit";p8=root/"p8"
    sessions=[];proofs=[];producer=[];sourcepins={};inputpins={}
    for w in range(40):
        for h in range(4):
            sid=f"w{w:02}s{h}";rows=[];events=[]
            rawsha=hashlib.sha256(sid.encode()).hexdigest()
            for i in range(8):
                key=f"{sid}i{i}";menu=["a","bb","ccc","dddd","eeeee"]
                chosen=min(4,(w+i%3)//9)
                if mode=="reverse" and h%2:chosen=4-chosen
                if mode=="constant":chosen=2
                wrong=(chosen+1)%5;ids=[7,11,17,21,28]
                handling="accept" if i<w%9 else "edit"
                row=dict(key=key,writer=f"w{w:02}",session=sid,ordinal=i,open_at=h*100+i,
                    handling=handling,menu=menu,inserted=menu[wrong])
                rows.append(row)
                events.append(dict(ordinal=i,decision=handling,usable=True,verified_insertion=True,
                    options=[dict(index=oid,original=text) for oid,text in zip(ids,menu)],matched_option_indices=[ids[chosen]],
                    selected_index=wrong,logged_index_agrees=False))
                proofs.append(dict(key=key,writer=row["writer"],session=sid,ordinal=i,open_at=row["open_at"],
                    canonical_handling=handling,prepared_handling=handling,canonical_positions=[chosen],prepared_positions=[wrong],
                    canonical_option_ids=ids,verified_insertion=True,canonical_usable=True,logged_selected_index=wrong,
                    logged_index_agrees=False,index_status="proven_disjoint_choice",raw_source_sha256=rawsha))
                for j,score in enumerate([-10.,-1.,0.,2.,77.54]):
                    producer.append(dict(key=key,writer=row["writer"],session=sid,ordinal=i,
                        position=j,suggestion_index=ids[j],logged_score=score,source_sha256=rawsha))
            canonical=root/"canonical"/(sid+".json");write(canonical,dict(usable=True,reconstructed=True,events=events))
            digest=sha256(canonical);sourcepins[canonical.relative_to(root).as_posix()]=digest;inputpins[str(canonical)]=digest
            for proof in proofs[-len(rows):]:proof.update(canonical_path=str(canonical),canonical_sha256=digest)
            sessions.append(dict(writer=f"w{w:02}",session=sid,timestamp=h,rows=rows))
    session_path=base/"phase0-v1/prepared/SESSIONS.json";source_path=base/"phase0-v1/prepared/SOURCE_PINS.json"
    write(session_path,sessions);write(source_path,sourcepins)
    foundation=base/"drive-foundation-v1";plan=foundation/"PLAN.json";complete=foundation/"COMPLETE.json"
    write(plan,dict(pins={p.relative_to(root).as_posix():sha256(p) for p in (session_path,source_path)},synthetic_fixture_only=True))
    write(complete,dict(status="COMPLETE",plan_sha256=sha256(plan),synthetic_fixture_only=True))
    for path in (session_path,source_path,plan,complete):inputpins[str(path)]=sha256(path)
    write(audit/"ROWS.json",proofs);write(audit/"INPUT_PINS.json",inputpins)
    origin=root/"audit_source.py";origin.write_text("# Explicit synthetic canonical audit fixture.\n",encoding="utf8")
    write(audit/"COMPLETE.json",dict(status="COMPLETE",schema_version=1,source_path=str(origin),source_sha256=sha256(origin),
        outputs={name:sha256(audit/name) for name in ("ROWS.json","INPUT_PINS.json")},no_fits=True,no_raw_replay=True,
        no_inference=True,no_repaired_scores=True,synthetic_fixture_only=True))
    p8.mkdir();(p8/"SUGGESTIONS.jsonl").write_text("".join(json.dumps(p)+"\n" for p in producer),encoding="utf8")
    write(p8/"PLAN.json",dict(pins={str(session_path):sha256(session_path)},synthetic_fixture_only=True))
    write(p8/"COMPLETE.json",dict(status="COMPLETE",synthetic_fixture_only=True,outputs={name:sha256(p8/name) for name in ("PLAN.json","SUGGESTIONS.jsonl")}))
    helper=Path(__file__).resolve().parents[1]/".agent-state/drive-20261017/builder3/selected_source_audit_reader.py"
    return dict(sessions=str(session_path),p8=str(p8/"SUGGESTIONS.jsonl"),p8_complete=str(p8/"COMPLETE.json"),
                selection_reader=str(helper),selection_complete=str(audit/"COMPLETE.json"))


def units(inputs):
    audit,writers,by_key=m.load(inputs,m.CONFIG)
    return [m.writer_rows(w,group,by_key,audit,m.CONFIG["seed"]) for w,group in writers.items()]


def test_source_identity_rank_direction_ties_and_monotone_invariance(tmp_path):
    inputs=fixture(tmp_path/"source");audit,writers,by_key=m.load(inputs,m.CONFIG)
    original=m.writer_rows("w00",writers["w00"],by_key,audit,m.CONFIG["seed"])
    r=original["rows"][0]
    assert r["chosen"]==0 and r["option_id"]==7 and r["prepared_positions"]==[1]
    assert r["centered_rank"]==-.5 and r["canonical_choice_changed"]
    for options in by_key.values():
        for p in options:p["logged_score"]=p["logged_score"]**3+100
    transformed=m.writer_rows("w00",writers["w00"],by_key,audit,m.CONFIG["seed"])
    assert [r["centered_rank"] for r in transformed["rows"]]==[r["centered_rank"] for r in original["rows"]]
    key=r["key"]
    for p,value in zip(by_key[key],[0.,0.,1.,2.,3.]):p["logged_score"]=value
    tied=m.writer_rows("w00",writers["w00"],by_key,audit,m.CONFIG["seed"])["rows"][0]
    assert tied["centered_rank"]==-.375 and tied["least_tied"]
    for p in by_key[key]:p["logged_score"]=7
    assert m.writer_rows("w00",writers["w00"],by_key,audit,m.CONFIG["seed"])["exclusions"]["all_tied_score_menu"]==1
    by_key[key][0]["logged_score"]=None
    assert m.writer_rows("w00",writers["w00"],by_key,audit,m.CONFIG["seed"])["exclusions"]["menu_has_missing_score"]==1
    by_key[key][0]["suggestion_index"]=8
    with pytest.raises(ValueError,match="option identity"):
        m.writer_rows("w00",writers["w00"],by_key,audit,m.CONFIG["seed"])


def test_fake_graph_bootstrap_matches_explicit_node_copies():
    x=np.array([-.5,-.2,.1,.5]);y=np.array([.4,-.1,.2,-.3]);permutation=np.array([2,1,3,0])
    counts=np.array([[2,1,1,0],[1,0,2,1],[1,1,1,1]])
    weights=s.fake_weights(counts,permutation)
    for b,count in enumerate(counts):
        pairs=[]
        for i,j in enumerate(permutation):
            copies=count[i] if i==j else count[i]*count[j]
            pairs.extend([(x[i],y[j])]*copies)
        pair=np.asarray(pairs);expected=np.corrcoef(pair.T)[0,1]
        assert s.correlation(x,y[permutation],weights[b:b+1])[0]==pytest.approx(expected)
    assert weights[0,1]==1  # fixed point counts once, not a second endpoint copy.


def test_positive_reverse_and_constant_known_answers(tmp_path):
    data=units(fixture(tmp_path/"source"));report=s.summarize(data,m.CONFIG)
    assert report["primary"]["effect"]==pytest.approx(1) and report["state"]=="positive"
    assert report["own_minus_fake"]["state"]=="positive"
    assert report["writer_label_permutation"]["p_one_sided"]<=.05
    for unit in data:
        for row in unit["rows"]:
            if row["half"]:row["centered_rank"]*=-1
    assert s.summarize(data,m.CONFIG)["state"]=="negative"
    for unit in data:
        for row in unit["rows"]:row["centered_rank"]=0.
    assert s.summarize(data,m.CONFIG)["state"]=="invalid"
    assert s.interval(0.,[-.1,0,.1]*10,m.CONFIG)["state"]=="null"
    assert s.interval(.2,[float("nan")]*6+[.1]*94,m.CONFIG)["state"]=="invalid"
    assert s.controls(1.,[.3]*200)["biased_pipeline_flag"]


def test_serialized_handler_resume_fresh_process_and_canonical_tamper(tmp_path):
    inputs=fixture(tmp_path/"source");output=tmp_path/"output";output.mkdir()
    write(output/"YIELD_REQUEST.json",dict(reason="fixture"))
    assert m.execute(output,inputs,m.CONFIG)["status"]=="yielded"
    (output/"YIELD_REQUEST.json").unlink()
    result=m.execute(output,inputs,m.CONFIG)
    assert result["source_census"]["proven_disjoint_choice"]==1280
    assert result["primary"]["effect"]==pytest.approx(1.)
    assert m.execute(output,inputs,m.CONFIG)==result
    request=tmp_path/"REQUEST.json";write(request,dict(output=str(output),inputs=inputs,config=m.CONFIG))
    code="import json,sys;from pathlib import Path;from runners.drive.cards.menus_d12_rank import verify;a=json.load(open(sys.argv[1]));print(verify(Path(a['output']),a['inputs'],a['config']))"
    run=subprocess.run([sys.executable,"-B","-c",code,str(request)],capture_output=True,text=True,
        env={**os.environ,"PYTHONHASHSEED":"719"},timeout=40)
    assert run.returncode==0,run.stderr
    proof=read(Path(inputs["selection_complete"]).parent/"ROWS.json")[0]
    path=Path(proof["canonical_path"]);path.write_text(path.read_text()+" ",encoding="utf8")
    with pytest.raises(ValueError,match="hash"):
        m.verify(output,inputs,m.CONFIG)


def test_raw_source_mismatch_and_prepared_mutation_refused(tmp_path):
    inputs=fixture(tmp_path/"source");audit,writers,by_key=m.load(inputs,m.CONFIG)
    row=writers["w00"][0]["rows"][0];changed=copy.deepcopy(row);changed["inserted"]="tampered"
    with pytest.raises(ValueError,match="consumer prepared row"):
        m.canonical.join(audit,changed,by_key[row["key"]])
    by_key[row["key"]][0]["source_sha256"]="0"*64
    with pytest.raises(ValueError,match="raw-source"):
        m.canonical.join(audit,row,by_key[row["key"]])
