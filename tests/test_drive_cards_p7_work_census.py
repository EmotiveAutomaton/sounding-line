import json
from pathlib import Path
import subprocess
import sys
import time

import pytest

from runners.drive.cards import timing_p7_work_census as card
from runners.drive.cards.timing_census import read, write, filehash
from runners.drive.cards.timing_p7 import CachedScorer
from runners.drive.cards.timing_p7_batched import prepare, groups
from tests.test_drive_cards_p7_admission import tiny_model


def fixture(tmp_path):
    rows = [dict(index=i,is_word=True,prefix=p,target=t) for i,(p,t) in enumerate(
        [("", "a"), ("a ", "b"), ("a b ", "c"), ("a ", "x"),
         ("word "*220, "y"), ("word "*220+"y ", "z")])]
    units = [dict(domain=d,identity=str(i),source=rows) for i,d in enumerate(("typed","jester"))]
    path=tmp_path/"fixture.json";write(path,units)
    return dict(fixture=str(path),sha256=filehash(path))


def fixture_reference(inputs, config):
    assert config == card.CONFIG
    if filehash(inputs["fixture"]) != inputs["sha256"]:
        raise ValueError("fixture changed")
    units=read(inputs["fixture"])
    return dict(fixture=inputs["sha256"]),units,{},None,{}


def fixture_tokenizer(_):
    return tiny_model(None)[1]


def fixture_locations(unit,*unused):
    return unit["source"]


def execute(output,inputs,config):
    card.reference=fixture_reference;card.tokenizer_only=fixture_tokenizer;card.old.locations=fixture_locations
    return card.execute(output,inputs,config)


def verify(output,inputs,config):
    card.reference=fixture_reference;card.tokenizer_only=fixture_tokenizer;card.old.locations=fixture_locations
    return card.verify(output,inputs,config)


def test_independent_known_work_counts():
    def r(ids,drop=0):return dict(ids=ids,positions=[len(ids)-1],dropped=drop)
    got=card.work([r([0,1]),r([0,1,2]),r([0,3]),r([8,9,10],2),r([8,9],1)])
    # First two share one causal forward of 3; edit reuses no cache (2);
    # shifted window is fresh (3); its shorter member adds no forward.
    assert got["groups"]==got["forwards"]==3
    assert got["forward_tokens"]==8 and got["cropped_targets"]==2
    assert sum(s["count"] for s in got["context_lengths"])==5
    assert got["native_target_tokens"]==5 and got["max_dropped_tokens"]==2


def test_work_simulation_matches_real_cache_with_revisions_and_overflow(tmp_path):
    inputs=fixture(tmp_path); rows=read(inputs["fixture"])[0]["source"]
    model,tokenizer,torch=tiny_model(None)
    prepared=[prepare(tokenizer,r["prefix"],r["target"]) for r in rows]
    scorer=CachedScorer(model,tokenizer,torch)
    actual_shapes=[]
    def observe(module,args,kwargs):
        cache=kwargs.get("past_key_values")
        old=cache.get_seq_length() if cache is not None else 0
        new=kwargs["input_ids"].shape[1]
        actual_shapes.append((old+new,new))
    hook=model.register_forward_pre_hook(observe,with_kwargs=True)
    try:
        for group in groups(prepared):
            i=next(i for i in group["members"] if prepared[i]["ids"]==group["ids"])
            scorer.score(rows[i]["prefix"],rows[i]["target"])
    finally:hook.remove()
    census=card.work(prepared)
    from collections import Counter
    assert Counter(actual_shapes)==Counter({(s["context"],s["new_tokens"]):s["count"] for s in census["shapes"]})
    assert census["forward_tokens"]==scorer.forward_tokens
    assert census["cropped_targets"]==2


def test_resume_fresh_replay_reentry_and_mutation_refusal(tmp_path,monkeypatch):
    inputs=fixture(tmp_path);output=tmp_path/"output"
    monkeypatch.setattr(card,"reference",fixture_reference)
    monkeypatch.setattr(card,"tokenizer_only",fixture_tokenizer)
    monkeypatch.setattr(card.old,"locations",fixture_locations)
    write(output/"YIELD_REQUEST.json",{})
    assert card.execute(output,inputs,card.CONFIG)["status"]=="yielded"
    first=(output/"units/00000.json").read_bytes()
    (output/"YIELD_REQUEST.json").unlink()
    primary=card.execute(output,inputs,card.CONFIG)
    assert primary["units"]==2 and primary["targets"]==12 and not primary["main_admitted"]
    assert first==(output/"units/00000.json").read_bytes()
    hashes={str(p):filehash(p) for p in output.rglob("*") if p.is_file()}
    assert card.execute(output,inputs,card.CONFIG)==primary
    assert hashes=={str(p):filehash(p) for p in output.rglob("*") if p.is_file()}
    args=tmp_path/"args.json";write(args,dict(output=str(output),inputs=inputs))
    code="from tests.test_drive_cards_p7_work_census import verify;import json,sys;x=json.load(open(sys.argv[1]));assert verify(x['output'],x['inputs'],{'phase':'native_work_census'})['verified']"
    result=subprocess.run([sys.executable,"-X","utf8","-B","-c",code,str(args)],capture_output=True,text=True,timeout=60)
    assert result.returncode==0,result.stderr
    # Rehash a forged intermediate and its index: source reconstruction must
    # still refuse, rather than treating mutually consistent hashes as validity.
    path=output/"units/00000.json";data=read(path);data["census"]["forward_tokens"]+=1
    path.write_text(json.dumps(data),encoding="utf8")
    path.with_suffix(".receipt.json").write_text(json.dumps(dict(sha256=filehash(path))),encoding="utf8")
    index=read(output/"INDEX.json");index[0]["sha256"]=filehash(path)
    (output/"INDEX.json").write_text(json.dumps(index),encoding="utf8")
    with pytest.raises(ValueError,match="fresh source reconstruction"):card.verify(output,inputs,card.CONFIG)


def test_wrong_scope_and_changed_source_refuse(tmp_path):
    with pytest.raises(ValueError,match="fixed P7"):card.reference({},dict(phase="main"))
    inputs=fixture(tmp_path)
    Path(inputs["fixture"]).write_text("[]",encoding="utf8")
    with pytest.raises(ValueError,match="fixture changed"):fixture_reference(inputs,card.CONFIG)


def test_actual_counted_runtime(tmp_path):
    inputs=fixture(tmp_path);root=tmp_path/"runtime"
    write(root/"PLAN.json",dict(card="P7-census-fixture",module="tests.test_drive_cards_p7_work_census",
        inputs=inputs,config=card.CONFIG,pins={inputs["fixture"]:inputs["sha256"]},
        forecast_cpu_seconds=600,max_wall_seconds=180,max_output_bytes=16*1024**2,smoke=True))
    with (root/"runtime.log").open("w") as stream:
        proc=subprocess.Popen([sys.executable,"-X","utf8","-B","-m","runners.drive.cards.batch_runtime_v2","run",str(root)],stdout=stream,stderr=stream)
        try:
            deadline=time.monotonic()+40
            while not (root/"OWNER.json").exists():
                if proc.poll() is not None or time.monotonic()>deadline:raise RuntimeError("Census runtime handshake failed")
                time.sleep(.1)
            write(root/"MONITOR_READY.json",dict(owner_sha256=filehash(root/"OWNER.json")))
            assert proc.wait(timeout=180)==0,(root/"runtime.log").read_text()
            assert read(root/"COMPLETE.json")["fresh_process_verified"]
            assert read(root/"VERIFIED.json")["verified"]
            assert not Path(read(root/"ADMISSION.json")["lease"]).exists()
        finally:
            if proc.poll() is None:proc.terminate();proc.wait(timeout=30)
