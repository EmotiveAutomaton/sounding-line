"""Constructed integrated Gear 3 checks; no model or cloud calls."""
from copy import deepcopy
from dataclasses import asdict, replace
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import time
import zipfile
import pytest
from runners import gear3_campaign as cost
from runners.stage10 import ollama, gear3_batch as batch, gear3_io as storage
from runners.stage10 import human_memory_checks as fixtures
from runners.stage10.contracts import canonical, digest

SPEC=Path("docs/archive/study-specs/GEAR_3_ROUND_1_2026-09-13.md")


def profile(key="9b"):
    return ollama.ReaderProfile("qwen3.5:"+key,batch.PINS[key],"0.32.14")


def manifest(node="A", kind="signal"):
    task=fixtures.task(100,2)
    public,answers=fixtures.rows(kind)
    names=[p for p in Path("runners/stage10").glob("*.py")]
    return {"schema":batch.SCHEMA,"block_id":"constructed-"+node,"node":node,
            "profiles":{k:asdict(profile(k)) for k in batch.PINS},
            "tasks":[{"record":asdict(task),"envelope":None,"group":"fixture"}],
            "training":{"coauthor-handling":{"public":public,"answers":answers}},
            "units":[{"task_id":task.task_id,"model":k,"arm":arm} for k in batch.PINS for arm in sorted(batch.METHODS[node])],
            "source_hashes":{p.as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in names},
            "scope":"constructed apparatus only; no scientific target answers"}


def transport(monkeypatch):
    requests=[]
    def urlopen(req, timeout):
        path=req.full_url.split("11434")[-1];payload=None if req.data is None else json.loads(req.data)
        if path=="/api/tags": response={"models":[{"name":"qwen3.5:"+k,"digest":v} for k,v in batch.PINS.items()]}
        elif path=="/api/version": response={"version":"0.32.14"}
        elif path=="/api/show": response={"details":{"quantization_level":"Q4_K_M"}}
        else:
            assert path=="/api/chat"
            body=json.loads(payload["messages"][1]["content"]);choices=body["task"]["choices"]
            choice=choices[0]["id"]
            if "hypotheses" in payload["format"]["properties"]:
                content={"hypotheses":{"0":[],"1":[0,1]},"choice":choice,"insufficient_support":True}
            elif "candidate_support" in body:
                domain=body["candidate_support"]
                content={"candidates":[{"cause":domain["cause"][0],"cost":0.5,"lapse":0.08}],"choice":choice,"insufficient_support":True}
            elif "candidates" in payload["format"]["properties"]:
                content={"candidates":[{"goal_hypothesis":"constructed only","program":{"feature":"draft_words","threshold":6.5,"below":"accept","otherwise":"edit"}}],"choice":choice,"insufficient_support":False}
            else:
                content={"choice":choice,"probabilities":{r["id"]:1/len(choices) for r in choices},"insufficient_evidence":True,"explanation":"constructed null forecast"}
            requests.append(payload)
            response={"fixture":True,"done":True,"done_reason":"stop","message":{"content":canonical(content)},
                      "eval_count":100,"prompt_eval_count":1000,"total_duration":1,"load_duration":0,"prompt_eval_duration":0,"eval_duration":1}
        return io.BytesIO(canonical(response).encode())
    monkeypatch.setattr(ollama.urllib.request,"urlopen",urlopen)
    return requests


def test_legacy_direct_request_and_binding_unchanged():
    original=subprocess.check_output(["git","show","e93ecef8f:runners/stage10/ollama.py"],text=True,encoding="utf8")
    ns={"__name__":"runners.stage10.legacy_test","__package__":"runners.stage10"}
    exec(compile(original,"legacy", "exec"),ns)
    t=fixtures.task(100,2)
    assert ns["request_for"](t)==ollama.request_for(t)
    assert ollama.bind_request(ollama.request_for(t))==digest({"request":ns["request_for"](t),"model_digest":ollama.MODEL_DIGEST})


def test_profile_identity_and_context_fail_closed(monkeypatch,tmp_path):
    transport(monkeypatch)
    t=fixtures.task(100,2);p=profile("27b")
    assert ollama.identity(profile=p)["reader_profile"]==asdict(p)
    with pytest.raises(RuntimeError):ollama.identity(profile=replace(p,model_digest="a"*64))
    with pytest.raises(RuntimeError):ollama.identity(profile=replace(p,server_version="wrong"))
    with pytest.raises(ValueError):ollama.request_for(t,profile=p,context_tokens=8192)
    with pytest.raises(ValueError):ollama.ReaderProfile(p.model,"7653528ba5cb",p.server_version)
    ollama.call(t,tmp_path/"attempt",profile=p)
    with pytest.raises(ValueError):ollama.call(t,tmp_path/"attempt",profile=profile())


def test_interrupted_block_complete_archive_and_no_call_replay(monkeypatch,tmp_path):
    requests=transport(monkeypatch);m=manifest();out=tmp_path/"original"
    reservation={"invocation_id":"fixture","reserved_cents":150,"expires_at":time.time()+1800}
    commits=[]
    with storage.durable_attempts(out,reservation,lambda:commits.append(1)):
        with pytest.raises(InterruptedError):batch.run_block(m,out,stop_after=2)
        assert not (out/"COMPLETE.json").exists()
        saved=batch.run_block(m,out)
    assert saved["units"]==6 and len(requests)==10
    assert {r["model"] for r in requests}=={"qwen3.5:9b","qwen3.5:27b"}
    assert all(r["options"]["num_ctx"]==16384 and r["options"]["num_thread"]==2 and r["think"] is False for r in requests)
    assert len(commits)>len(requests)*3
    for path in out.rglob("REQUEST.json"):
        assert json.loads(path.read_text())["cloud_reservation"]==reservation
    assert list(out.rglob("EXECUTION.json"))  # actual human rule executor
    archive=tmp_path/"full.zip";receipt=storage.make_archive(out,archive)
    restored=tmp_path/"restored";assert storage.verify_archive(archive,restored)==receipt
    def forbidden(*args,**kwargs):raise AssertionError("replay attempted model access")
    monkeypatch.setattr(ollama.urllib.request,"urlopen",forbidden)
    assert batch.run_block(m,restored)==saved
    raw=next(restored.rglob("RAW.json"));raw.write_text("{}")
    with pytest.raises(ValueError):batch.run_block(m,restored)


@pytest.mark.parametrize("kind",["null","signal"])
def test_all_human_memory_paths_forward_profile(monkeypatch,tmp_path,kind):
    requests=transport(monkeypatch);m=manifest("P",kind)
    batch.run_block(m,tmp_path/"block")
    assert len(requests)==20
    assert all(r["options"]["num_ctx"]==16384 and r["options"]["num_thread"]==2 for r in requests)
    assert {r["model"] for r in requests}=={"qwen3.5:9b","qwen3.5:27b"}


def test_incomplete_and_private_manifest_refuse():
    m=manifest();m["units"].pop()
    with pytest.raises(ValueError):batch.validate(m)
    m=manifest();m["evaluation_answers"]=[]
    with pytest.raises(ValueError):batch.validate(m)
    m=manifest();m["tasks"][0]["record"]["evidence"]["future_document"]="hidden"
    with pytest.raises(ValueError):batch.validate(m)


def test_request_requires_durable_reservation_and_original_deadline(tmp_path):
    reservation={"invocation_id":"fixture","reserved_cents":100,"expires_at":time.time()+120}
    commits=[];payload=ollama.request_for(fixtures.task(100,2),profile=profile())
    with storage.durable_attempts(tmp_path,reservation,lambda:commits.append(1)):
        active=storage.journal()
        with pytest.raises(ValueError):active.before_api("/api/chat",payload,600)
        ollama.write_new(tmp_path/"REQUEST.json",{"request":payload,"binding":ollama.bind_request(payload,profile())})
        assert len(commits)==1 and 1<=active.before_api("/api/chat",payload,600)<120
        with pytest.raises(ValueError):active.before_api("/api/chat",payload,600)
    reservation["expires_at"]=time.time()-1
    with storage.durable_attempts(tmp_path,reservation,lambda:None):
        with pytest.raises(TimeoutError):ollama.write_new(tmp_path/"later"/"REQUEST.json",{"request":payload})


def test_archive_missing_members_or_traversal_refuse(tmp_path):
    for name in ("../escape","member"):
        path=tmp_path/("bad-"+str(len(name))+".zip")
        with zipfile.ZipFile(path,"w") as z:
            z.writestr(storage.ARCHIVE_MANIFEST,canonical({"schema":"gear3.archive.1","files":{name:{"bytes":1,"sha256":"0"*64}}}))
            if name.startswith(".."):z.writestr(name,"x")
        with pytest.raises(ValueError):storage.verify_archive(path,tmp_path/"extract")
    assert not (tmp_path/"escape").exists()


@pytest.mark.parametrize("operation",["opportunity","reading"])
def test_actual_exported_ghost_paths_and_restored_replay(monkeypatch,tmp_path,operation):
    from runners.stage10 import ghost,reading_source
    if not os.environ.get("G3_GHOST_ROOT"):
        pytest.skip("requires reviewed local public Ghost export; mandatory before cloud admission")
    root=Path(os.environ["G3_GHOST_ROOT"]).resolve()
    rows,_=ghost.envelopes(root)
    eligible=[r for r in rows if r["envelope"]["declared_context"]["operation"]==operation]
    if operation=="reading": eligible=[r for r in eligible if r["case_id"]==reading_source.PILOT_CASE]
    else:eligible=[r for r in eligible if r['case_id']=='318c3dff39044fb78a1be45b83db3777']
    row=eligible[0];task=ghost.task_from(row["envelope"])
    m=manifest("P");m["block_id"]="constructed-native-"+operation
    m["tasks"]=[{"record":asdict(task),"envelope":row["envelope"],"group":row["case_id"]}]
    m["training"]={} if operation=="opportunity" else {"ghost-reading":{"public":[],"answers":[]}}
    if operation=="reading":
        if not os.environ.get("G3_READING_PREPARED"):
            pytest.fail("native memory check needs the source-separated permitted training records")
        prepared=Path(os.environ["G3_READING_PREPARED"])
        m["training"]["ghost-reading"]={"public":json.loads((prepared/"train-public.json").read_text())["tasks"],
            "answers":[{k:r[k] for k in ('task_id','correct_choice','case_id')} for r in json.loads((prepared/"train-evaluator.json").read_text())["targets"]]}
    arms=("R0","R2","R3") if operation=="opportunity" else sorted(batch.METHODS["P"])
    m["units"]=[{"task_id":task.task_id,"model":model,"arm":arm} for model in batch.PINS for arm in arms]
    requests=transport(monkeypatch);out=tmp_path/"native"
    reservation={"invocation_id":"native-fixture","reserved_cents":100,"expires_at":time.time()+600}
    with storage.durable_attempts(out,reservation,lambda:None): saved=batch.run_block(m,out,ghost_root=root)
    assert {r["model"] for r in requests}=={"qwen3.5:9b","qwen3.5:27b"}
    executions=list(out.rglob("execution/RAW.json"));assert executions
    for p in executions:
        raw=json.loads(p.read_text());assert raw["returncode"]==0 and json.loads(raw["stdout"].splitlines()[0])["ready"] is True
    archive=tmp_path/"native.zip";storage.make_archive(out,archive)
    restored=tmp_path/"restored";storage.verify_archive(archive,restored)
    def forbidden(*a,**k):raise AssertionError("replay attempted external computation")
    monkeypatch.setattr(ollama.urllib.request,"urlopen",forbidden)
    native_run=subprocess.run;executed=[]
    def checked_native(cmd,**kwargs):
        assert Path(cmd[4]).name=='executor_worker.py'
        executed.append(cmd)
        return native_run(cmd,**kwargs)
    monkeypatch.setattr(subprocess,'run',checked_native)
    assert batch.run_block(m,restored,ghost_root=root)==saved
    assert executed  # semantic replay executes original native candidates again


def ledger(tmp_path):
    p=tmp_path/"ledger.json"
    p.write_text(json.dumps({"runs":[{"ts":1,"status":"COMPLETE","est_actual_dollars":1.2}],"cap_approvals":[]}))
    l=cost.CampaignLedger(p);l.enroll("specific bounded package, 2026-09-13",SPEC)
    return l


def test_budget_caps_and_historical_entries_survive(tmp_path):
    l=ledger(tmp_path);prior=l.path.read_bytes()
    with pytest.raises(ValueError):l.reserve("too-big","P",["batch"],{},5000,0,approval="pilot")
    assert l.path.read_bytes()==prior
    first=l.reserve("first","P",["batch"],{},1200,10,approval="pilot",now=1000)
    again=l.reserve("first","P",["batch"],{},1200,10,approval="pilot",now=9999)
    assert again["expires_at"]==2200 and again["booked_cents"]==first["booked_cents"]
    assert again["existing_reservation"] is True
    with pytest.raises(ValueError):l.reserve("second","A",["batch"],{},1200,10,approval="A")
    l.transition("first","SUBMITTED",call_id="fc-fixture")
    l.transition("first","UNKNOWN",evidence="lost client")
    with pytest.raises(ValueError):l.reserve("second","A",["batch"],{},1200,10,approval="A")
    data=json.loads(l.path.read_text());assert data["runs"][0]["est_actual_dollars"]==1.2
    assert data["runs"][-1]["booked_cents"]==first["reserved_cents"]
    l.transition("first","CANCELLED",owner_ended=True,evidence="provider confirms cancelled")
    l.reserve("second","A",["batch"],{},1200,10,approval="A")
    with pytest.raises(ValueError):l.enroll("new approval cannot reset budget",SPEC)


def test_ordinary_total_and_one_recovery_enforced(tmp_path):
    l=ledger(tmp_path)
    for node in ("P","A","B","C","D"):
        overhead=cost.NODE_CENTS[node]-1
        l.reserve(node,node,["batch"],{},1,overhead,approval=node,now=1000)
        l.transition(node,"SUBMITTED",call_id="fc-"+node)
        l.transition(node,"COMPLETE",owner_ended=True,evidence="constructed finish")
    with pytest.raises(ValueError):l.reserve("more","A",["batch"],{},1,0,approval="more")
    recovery=l.reserve("repair","Reserve",["batch"],{},1,999,approval="one repair",recovery_of="P",now=1000.5)
    assert recovery['expires_at']==1001
    l.transition("repair","SUBMITTED",call_id="fc-repair")
    l.transition("repair","FAILED",owner_ended=True,evidence="constructed failure")
    with pytest.raises(ValueError):l.reserve("repair2","Reserve",["batch"],{},1,0,approval="repeat",recovery_of="P")
    assert sum(l.totals(json.loads(l.path.read_text())).values())==5000
