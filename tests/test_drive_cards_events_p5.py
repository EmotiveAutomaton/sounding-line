"""Known-answer extraction, classification and saved-statistic replay controls."""
import gzip
import json
import types
from pathlib import Path

import numpy as np
import pytest

from runners.drive.cards import events_p5 as p
from runners.drive.timeline import rebuild


def event(i,name="text-insert",source="user",**kw):
    return dict(eventNum=i,eventName=name,eventSource=source,eventTimestamp=1000+i*100,**kw)


def source(text="",edits=()):
    events=[event(0,"system-initialize","api",currentDoc="\n"),
            event(1,textDelta={"ops":[{"insert":text}]})]
    for ops in edits:
        events.append(event(len(events),textDelta={"ops":ops}))
    return events


def test_exact_typed_sentence_and_emoji_replay():
    events=source("Hello 😀 there. Next sentence.",[[{"retain":9},{"delete":5},{"insert":"friend"}]])
    timeline=rebuild(events,[])
    r=p.extract_session(events,timeline)
    assert len(r["edits"])==1
    assert r["edits"][0]["changed_before"]=="there"
    assert r["edits"][0]["changed_after"]=="friend"
    assert r["edits"][0]["origin"]=="own"
    assert all(s["writer_typed"] for s in r["sentences"])
    assert r["sentences"][0]["correction_ordinals"]==[2]
    assert r["sentences"][1]["correction_ordinals"]==[]


def test_boundary_change_keeps_same_surrounding_words():
    events=source("Hello world",[[{"retain":5},{"insert":"."},{"delete":1},{"insert":" "}]])
    r=p.extract_session(events,rebuild(events,[]))
    assert r["edits"][0]["before"].strip()=="Hello world"
    assert r["edits"][0]["after"].strip()=="Hello. world"


def test_prompt_and_model_text_are_not_writer_typed():
    events=[event(0,"system-initialize","api",currentDoc="Prompt.\n"),
            event(1,"suggestion-open"),event(2,"suggestion-select"),
            event(3,source="api",textDelta={"ops":[{"retain":7},{"insert":"Model sentence."}]}),
            event(4,textDelta={"ops":[{"retain":13},{"delete":8},{"insert":"passage"}]})]
    r=p.extract_session(events,rebuild(events,[]))
    assert r["edits"][0]["origin"]=="model"
    assert not any(s["writer_typed"] for s in r["sentences"])


def test_changed_source_fails_p2_conservation():
    events=source("One sentence.",[[{"retain":0},{"delete":3},{"insert":"New"}]])
    timeline=rebuild(events,[])
    timeline["edits"][0]["after"]="changed"
    with pytest.raises(ValueError,match="P2 edit window"):
        p.extract_session(events,timeline)


def test_half_surrogate_delta_refused():
    events=source("😀",[[{"delete":1}]])
    with pytest.raises(UnicodeError):
        p.extract_session(events,dict(edits=[],final_document=""))


@pytest.mark.parametrize("before,after,expected",[
    ("A typo here.","A type here.",True),
    ("One word.","One word!",True),
    ("One word.","One new word.",False),
    ("A word.","A word.",False),
    ("One word.","Two words.",False),
    ("One word.","One word. ",False),
])
def test_housekeeping_known_answers(before,after,expected):
    assert p.housekeeping(before,after) is expected


def test_d4_disjoint_threshold_boundary_and_noop():
    unit=np.array([1.,0.])
    distant=np.array([.8,.6])
    r=p.classify("The dog waits.","The owl waits.",unit,distant,1,1)
    assert r["split"]=="housekeeping" and r["overlap"]
    r=p.classify("He waits here.","She travels abroad.",unit,distant,1,1)
    assert r["split"]=="content"
    r=p.classify("He waits here.","He waited here and slept.",unit,unit,1,2)
    assert r["split"]=="content"
    assert p.classify("unchanged","unchanged",unit,distant,1,2)["split"]=="excluded"
    assert p.classify("He waits here.","They wait here.",unit,unit,1,1)["split"]=="excluded"


def test_nonfinite_and_unnormalized_refuse():
    for bad in ([float("nan"),0],[2,0]):
        with pytest.raises(ValueError):
            p.classify("a","b",bad,[1,0],0,0)


def test_saved_primary_recomputed_and_tamper_refused(tmp_path):
    vectors=np.zeros((2,384),np.float32); vectors[0,0]=1; vectors[1,1]=1
    entry=dict(ordinal=2,before="The cat sleeps.",after="Someone came home.",origin="own",before_vector=0,after_vector=1)
    entry.update(p.classify(entry["before"],entry["after"],vectors[0],vectors[1],1,1))
    value=dict(edits=[entry],sentences=[dict(writer_typed=True,correction_ordinals=[2],content_correction_touched=True)],visibility=[])
    path=tmp_path/"session.json.gz"
    with gzip.open(path,"wt",encoding="utf8") as f:
        json.dump(value,f)
    np.save(tmp_path/"vectors.npy",vectors,allow_pickle=False)
    p.write(tmp_path/"SESSION_INDEX.json",[dict(session="fixture",file=path.name,sha256=p.filehash(path),vectors="vectors.npy",vectors_sha256=p.filehash(tmp_path/"vectors.npy"))])
    summary=p.summary_from_saved(tmp_path)
    assert summary["split_counts"]=={"content":1}
    assert summary["typed_sentences_touched_by_content"]==1
    path.write_bytes(b"changed")
    with pytest.raises(ValueError,match="saved session changed"):
        p.summary_from_saved(tmp_path)


def test_execute_verify_actual_serialized_handler(tmp_path,monkeypatch):
    """Expensive encoder/parser stubbed; every extraction/binding/write path runs."""
    import spacy
    import runners.drive.cards
    monkeypatch.setattr(runners.drive.cards,"states",types.SimpleNamespace(),raising=False)
    class FakeEncoder:
        def __init__(self,*a): pass
        def encode(self,texts):
            v=np.zeros((len(texts),384),np.float32); v[:,0]=1
            return v,[dict(truncated=False) for _ in texts]
    class FakeParser:
        def pipe(self,texts,**kw):
            return [[] for _ in texts]
    monkeypatch.setattr(p,"Encoder",FakeEncoder)
    monkeypatch.setattr(p,"model_identity",lambda path:None)
    monkeypatch.setattr(spacy,"load",lambda *a,**kw:FakeParser())
    events=source("One sentence.",[[{"delete":3},{"insert":"Two"}]])
    p.write(tmp_path/"p2.json",rebuild(events,[]))
    raw=tmp_path/"source.jsonl"
    raw.write_text("\n".join(json.dumps(e) for e in events),encoding="utf8")
    p.write(tmp_path/"index.json",[dict(session="s",writer="w",file="p2.json",sha256=p.filehash(tmp_path/"p2.json"))])
    p.write(tmp_path/"roster.json",[dict(session="s",path=raw.name,source_sha256=p.filehash(raw))])
    p.write(tmp_path/"sessions.json",[dict(session="s",writer="w",prompt="p",timestamp=1,end_at=2)])
    p.write(tmp_path/"model.json",{})
    (tmp_path/"spacy").mkdir(); (tmp_path/"spacy"/"config.cfg").write_text("fixture",encoding="utf8")
    inputs=dict(p2_index=str(tmp_path/"index.json"),source_roster=str(tmp_path/"roster.json"),
                source_root=str(tmp_path),sessions=str(tmp_path/"sessions.json"),
                content_model=str(tmp_path/"model.json"),spacy_model=str(tmp_path/"spacy"))
    config=dict(threads=2,batch_size=16,expected_sessions=1,expected_edits=1)
    result=p.execute(tmp_path/"out",inputs,config)
    assert result["split_counts"]=={"housekeeping":1}
    assert p.verify(tmp_path/"out",inputs,config)["verified"]
    with pytest.raises(ValueError,match="completed output"):
        p.execute(tmp_path/"out",inputs,config)
    calls=[]
    class YieldEncoder(FakeEncoder):
        def encode(self,texts):
            calls.append(1)
            (tmp_path/"yielded"/"YIELD_REQUEST.json").write_text("{}",encoding="utf8")
            return super().encode(texts)
    monkeypatch.setattr(p,"Encoder",YieldEncoder)
    yielded=p.execute(tmp_path/"yielded",inputs,config)
    assert yielded["status"]=="yielded"
    assert not (tmp_path/"yielded"/"SUMMARY.json").exists()
    assert p.read(tmp_path/"yielded"/"FIRST_TENTH.json")["forecast_cpu_seconds"]==3600
    (tmp_path/"yielded"/"YIELD_REQUEST.json").unlink()
    resumed=p.execute(tmp_path/"yielded",inputs,config)
    assert resumed==result and len(calls)==1
    assert p.verify(tmp_path/"yielded",inputs,config)["verified"]
    raw.write_text("changed",encoding="utf8")
    with pytest.raises(ValueError,match="frozen source"):
        p.verify(tmp_path/"out",inputs,config)
