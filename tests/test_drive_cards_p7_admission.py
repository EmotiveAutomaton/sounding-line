import json
from pathlib import Path
import subprocess
import sys
import time

import pytest

from runners.drive.cards import timing_p7_admitted as card
from runners.drive.cards.timing_census import read, write, filehash
from runners.drive.cards.timing_p6 import gzwrite, gzread
from runners.drive.cards.timing_text import replay_words


def fixture_source(root):
    root = Path(root).resolve()
    events = [dict(eventName="system-initialize", eventTimestamp=0, currentDoc=""),
              dict(eventName="text-insert", eventTimestamp=100, eventSource="user",
                   textDelta={"ops":[{"insert":"red red cat "}]}),
              dict(eventName="text-insert", eventTimestamp=200, eventSource="user",
                   textDelta={"ops":[{"retain":8},{"delete":3},{"insert":"dog"}]})]
    raw = root / "raw.jsonl"; raw.parent.mkdir(parents=True, exist_ok=True)
    raw.write_text("\n".join(json.dumps(e) for e in events),encoding="utf8")
    roster = root / "ROSTER.json"
    write(roster, [dict(session="fixture", path="raw.jsonl", source_sha256=filehash(raw))])
    p6 = root / "p6"; words = replay_words(events)["words"]
    gzwrite(p6/"output/scores/fixture.json.gz", dict(words=words))
    write(p6/"output/P6_INDEX.json", [dict(session="fixture", file="scores/fixture.json.gz",
          sha256=filehash(p6/"output/scores/fixture.json.gz"), word_count=len(words))])
    write(p6/"output/P6_BINDINGS.json", dict(repo_root=str(root),inputs=dict(raw_roster=filehash(roster)),
          index_sha256=filehash(p6/"output/P6_INDEX.json")))
    original = root / "original.json"
    write(original,dict(inputs=dict(raw_roster=str(roster))))
    write(p6/"PLAN.json", dict(module="runners.drive.cards.timing_p6_recovery",config={},
          inputs=dict(original_plan=str(original)),pins={str(original):filehash(original)}))
    write(p6/"output/RECOVERY_BINDING.json",dict(fixture=True)); write(p6/"VERIFIED.json",dict(verified=True))
    write(p6/"COMPLETE.json",dict(card="P6-recovery",status="COMPLETE",fresh_process_verified=True,
          outputs={p.relative_to(p6).as_posix():filehash(p) for p in p6.rglob("*") if p.is_file()}))
    jokes = root / "jokes.json"
    write(jokes,[dict(joke_id=i,text="red "*(60 if i==150 else 1)) for i in range(1,151)])
    jm = root/"jester-manifest.json"; jv=root/"jester-verified.json"
    write(jm,dict(source_revision=card.JESTER_REVISION,jokes=150,texts_sha256=filehash(jokes)))
    write(jv,dict(jokes=150,all_exact_strings_match_independent_xml_parser=True,
          source_bytes_and_zip_crc_verified=True,text_manifest_sha256=filehash(jm)))
    model = root/"model"; model.mkdir()
    for name in ("config.json","tokenizer_config.json","tokenizer.json","vocab.json","merges.txt","model.safetensors"):
        (model/name).write_text("fixture-only",encoding="utf8")
    mm = root/"model-manifest.json"
    write(mm,dict(model="openai-community/gpt2-medium", revision=card.MODEL_REVISION,
          files={str(p):filehash(p) for p in model.iterdir()}, packages={},model_path=str(model),tokenizer_path=str(model)))
    return dict(repo_root=str(root),raw_roster=str(roster),p6_completion=str(p6/"COMPLETE.json"),
                jester_texts=str(jokes),jester_manifest=str(jm),jester_verified=str(jv),model_manifest=str(mm))


def tiny_model(_):
    import torch
    from transformers import GPT2Config,GPT2LMHeadModel
    torch.set_num_threads(2); torch.manual_seed(44)
    model=GPT2LMHeadModel(GPT2Config(vocab_size=128,n_positions=1024,n_embd=8,n_layer=1,n_head=1)).eval()
    class Tokenizer:
        eos_token_id=0
        def __call__(self,text,**kwargs):
            return dict(input_ids=[ord(c)%127 for c in text],offset_mapping=[(i,i+1) for i in range(len(text))])
    return model,Tokenizer(),torch


def test_serialized_resume_and_fresh_process_replay(tmp_path,monkeypatch):
    inputs=fixture_source(tmp_path/"sources"); output=tmp_path/"output"
    monkeypatch.setattr(card,"load_model",tiny_model)
    write(output/"YIELD_REQUEST.json",dict(reason="fixture"))
    assert card.execute(output,inputs,card.CONFIG)["status"]=="yielded"
    parts=list((output/"parts").rglob("*.json.gz")); assert len(parts)==1
    before=parts[0].read_bytes()
    (output/"YIELD_REQUEST.json").unlink()
    result=card.execute(output,inputs,card.CONFIG)
    assert parts[0].read_bytes()==before
    assert card.verify(output,inputs,card.CONFIG)["verified"]
    hashes={str(p):filehash(p) for p in output.rglob("*") if p.is_file()}
    assert card.execute(output,inputs,card.CONFIG)==result
    assert hashes=={str(p):filehash(p) for p in output.rglob("*") if p.is_file()}
    args=tmp_path/"arguments.json"; write(args,dict(inputs=inputs,output=str(output)))
    script="""import importlib.util,json,sys
spec=importlib.util.spec_from_file_location('p7_fixture',sys.argv[1]); f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
from runners.drive.cards import timing_p7_admitted as card
card.load_model=f.tiny_model
d=json.load(open(sys.argv[2]));assert card.verify(d['output'],d['inputs'],card.CONFIG)['verified']
"""
    child=subprocess.run([sys.executable,"-X","utf8","-B","-c",script,__file__,str(args)],capture_output=True,text=True,timeout=60)
    assert child.returncode==0,child.stderr


@pytest.mark.parametrize("change",["completion","roster","model","jester","main"])
def test_source_and_main_refusals(tmp_path,change):
    inputs=fixture_source(tmp_path)
    if change=="main":
        with pytest.raises(ValueError,match="pilot"):
            card.source(inputs,dict(phase="main"))
        return
    key={"completion":"p6_completion","roster":"raw_roster","model":"model_manifest","jester":"jester_texts"}[change]
    path=Path(inputs[key]); data=read(path)
    if change=="completion": data["fresh_process_verified"]=False
    elif change=="roster": data[0]["source_sha256"]="bad"
    elif change=="model": data["revision"]="bad"
    else: data.pop()
    path.write_text(json.dumps(data),encoding="utf8")
    with pytest.raises(ValueError): card.source(inputs,card.CONFIG)


def test_checkpoint_tamper_refused_before_model_load(tmp_path,monkeypatch):
    inputs=fixture_source(tmp_path/"sources"); output=tmp_path/"output"
    monkeypatch.setattr(card,"load_model",tiny_model)
    write(output/"YIELD_REQUEST.json",dict(reason="fixture"))
    card.execute(output,inputs,card.CONFIG)
    path=next((output/"parts").rglob("*.json.gz"));path.write_bytes(path.read_bytes()+b"damage")
    def forbidden(_): raise AssertionError("must refuse before model load")
    monkeypatch.setattr(card,"load_model",forbidden)
    with pytest.raises(ValueError,match="checkpoint hash"):card.execute(output,inputs,card.CONFIG)


def test_native_numerical_control_rejects_nan_and_wrong_ids():
    from runners.drive.cards.timing_p7 import CachedScorer
    model,tok,torch=tiny_model(None); scorer=CachedScorer(model,tok,torch)
    actual=scorer.score("red ","cat")
    bad=dict(actual,native_token_nll=[float("nan")]*len(actual["native_token_nll"]))
    with pytest.raises(ValueError,match="finite-loss"):scorer.direct_check("red ","cat",bad)
    bad=dict(actual,native_token_ids=[0]*len(actual["native_token_ids"]))
    with pytest.raises(ValueError,match="identity"):scorer.direct_check("red ","cat",bad)


# Only the smoke plan imports this TEST module. Production imports the admitted
# module directly and cannot select this replacement through its fixed inputs.
def execute(output,inputs,config):
    card.load_model=tiny_model
    return card.execute(output,inputs,config)


def verify(output,inputs,config):
    card.load_model=tiny_model
    return card.verify(output,inputs,config)


def test_actual_counted_runtime(tmp_path):
    inputs=fixture_source(tmp_path/"sources"); root=tmp_path/"runtime"
    write(root/"PLAN.json",dict(card="P7-fixture",module="tests.test_drive_cards_p7_admission",
          inputs=inputs,config=card.CONFIG,pins={v:filehash(v) for k,v in inputs.items() if k!="repo_root"},
          forecast_cpu_seconds=600,max_wall_seconds=180,max_output_bytes=16*1024**2,smoke=True))
    with (root/"runtime.log").open("w") as stream:
        proc=subprocess.Popen([sys.executable,"-X","utf8","-B","-m","runners.drive.cards.batch_runtime_v2","run",str(root)],stdout=stream,stderr=stream)
        try:
            deadline=time.monotonic()+40
            while not (root/"OWNER.json").exists():
                if proc.poll() is not None or time.monotonic()>deadline:
                    raise RuntimeError("P7 smoke owner handshake failed: "+(root/"runtime.log").read_text())
                time.sleep(.1)
            write(root/"MONITOR_READY.json",dict(owner_sha256=filehash(root/"OWNER.json")))
            assert proc.wait(timeout=180)==0,(root/"runtime.log").read_text()
            assert read(root/"COMPLETE.json")["fresh_process_verified"]
            assert read(root/"VERIFIED.json")["verified"]
            assert not Path(read(root/"ADMISSION.json")["lease"]).exists()
        finally:
            if proc.poll() is None:
                proc.terminate();proc.wait(timeout=30)
