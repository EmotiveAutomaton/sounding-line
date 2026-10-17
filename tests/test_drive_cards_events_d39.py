import json
import os
import subprocess
import sys
import math

import pytest

from runners.drive.cards.events_d39 import extract_failures,match_failures,paired_primary,statistics,execute,verify
from runners.drive.cards.events_p5 import write,filehash
from runners.drive.timeline import rebuild


def event(i,name="text-delete",source="user",**kw):
    return dict(eventNum=i,eventTimestamp=1000+i*100,eventName=name,eventSource=source,**kw)


def model_source():
    events=[event(0,"system-initialize","api",currentDoc="\n"),event(1,"suggestion-get"),
            event(2,"suggestion-open"),event(3,"suggestion-select"),
            event(4,"text-insert","api",textDelta={"ops":[{"insert":"😀ABCD"}]}),
            event(5,textDelta={"ops":[{"retain":2},{"delete":4}]}),
            event(6,textDelta={"ops":[{"delete":2}]}),event(7,"suggestion-open"),
            event(8,"suggestion-hover"),event(9,"suggestion-hover"),event(10,"suggestion-close")]
    rows=[dict(key="a",ordinal=2,end_ordinal=7,handling="edit",menu=["😀ABCD"]),
          dict(key="b",ordinal=7,end_ordinal=11,handling="dismiss",menu=["x"])]
    return events,rebuild(events,rows)


def own_source():
    events=[event(0,"system-initialize","api",currentDoc="\n"),event(1,"suggestion-get"),
            event(2,"text-insert",textDelta={"ops":[{"insert":"😀ABCD"}]}),
            event(3,textDelta={"ops":[{"retain":4},{"delete":2}]}),
            event(4,textDelta={"ops":[{"retain":2},{"delete":2}]}),
            event(5,textDelta={"ops":[{"delete":2}]}),event(6,"suggestion-open"),event(7,"suggestion-close")]
    rows=[dict(key="b",ordinal=6,end_ordinal=8,handling="dismiss",menu=["x"])]
    return events,rebuild(events,rows)


def test_exact_eighty_percent_codepoints_and_single_crossing():
    failures=extract_failures(*model_source())
    assert len(failures)==1
    f=failures[0]
    assert f["kind"]=="model" and f["ordinal"]==5
    assert f["deleted_codepoints"]==4 and f["original_codepoints"]==5
    assert f["next_menus"][0]["ordinal"]==7
    assert f["next_menus"][0]["hovers"]==2


def test_own_backspace_run_reconstructs_text_and_endpoint():
    failures=extract_failures(*own_source())
    assert len(failures)==1
    f=failures[0]
    assert f["kind"]=="own" and f["ordinal"]==5
    assert f["deleted_codepoints"]==5 and f["deleted_text"]=="😀ABCD"
    assert f["deletion_deltas"]==3
    assert f["next_menus"][0]["hovers"]==0


def test_cursor_event_breaks_run_without_timing_assumptions():
    events,timeline=own_source()
    events.insert(4,event(4,"cursor-backward"))
    for i,e in enumerate(events):
        e.update(eventNum=i,eventTimestamp=1000+i*100)
    failures=extract_failures(events,dict(final_document="\n",decisions=[]))
    assert [r["deleted_codepoints"] for r in failures]==[2,3]
    assert all(r["next_menus"]==[] for r in failures)


def test_changed_final_source_and_half_surrogate_refuse():
    events,timeline=model_source();timeline["final_document"]="changed"
    with pytest.raises(ValueError,match="P2 final"):
        extract_failures(events,timeline)
    events[5]["textDelta"]={"ops":[{"delete":1}]}
    with pytest.raises(UnicodeError):
        extract_failures(events,timeline)


def failure(w,kind,hovers,length=10,i=1):
    return dict(writer=w,session=w+str(i),session_index=i,ordinal=i,kind=kind,
                request_gap_seconds=1.,deleted_codepoints=length,next_menus=[dict(hovers=hovers)])


def test_matched_effect_preserves_sign_and_equal_writer_weight():
    fs=[r for w,effect in (("a",1),("b",3)) for r in (failure(w,"model",effect),failure(w,"own",0))]
    matched,_=match_failures(fs)
    assert paired_primary(matched,bootstrap=50)["effect"]==2


def test_matching_caliper_and_missing_input_exclusions():
    fs=[failure("a","model",4),failure("a","own",1,12),failure("b","model",3),failure("b","own",0,13)]
    absent=failure("a","model",1);absent["next_menus"]=[];fs.append(absent)
    matched,excluded=match_failures(fs)
    assert len(matched)==1 and matched[0]["hover_difference"]==3
    assert excluded=={"missing_next_menu_or_request":1,"no_length_matched_own_deletion":1}


def test_null_positive_negative_and_insufficient_writers():
    for value,state in [(0,"null"),(2,"positive"),(-2,"negative")]:
        rows=[dict(writer=w,hover_difference=value) for w in ("a","b","c")]
        result=paired_primary(rows,bootstrap=50)
        assert result["effect"]==value and result["state"]==state
    assert paired_primary([dict(writer="a",hover_difference=2)])["state"]=="invalid"


def test_equal_writer_weights_survive_unbalanced_pair_counts():
    rows=[dict(writer="a",hover_difference=1)]*20+[dict(writer="b",hover_difference=3)]
    result=paired_primary(rows,bootstrap=50)
    assert result["effect"]==2 and result["standard_error"]>0
    assert result["p_approx"]==pytest.approx(math.erfc(abs(result["z"])/math.sqrt(2)))
    zero=paired_primary([dict(writer=w,hover_difference=0) for w in ("a","b")],bootstrap=50)
    assert zero["standard_error"]==0 and zero["z"] is None and zero["p_approx"] is None


def test_execute_and_fresh_process_recompute(tmp_path,monkeypatch):
    index=[];roster=[];sessions=[]
    for w in ("a","b","c"):
        for i,constructor in enumerate((model_source,own_source)):
            stem=w+str(i); events,timeline=constructor()
            source=tmp_path/f"{stem}.jsonl"
            source.write_text("\n".join(json.dumps(e) for e in events),encoding="utf8")
            write(tmp_path/f"{stem}_p2.json",timeline)
            roster.append(dict(session=stem,path=source.name,source_sha256=filehash(source)))
            index.append(dict(session=stem,writer=w,file=f"{stem}_p2.json",sha256=filehash(tmp_path/f"{stem}_p2.json")))
            sessions.append(dict(session=stem,writer=w,timestamp=i))
    for name,value in (("index",index),("roster",roster),("sessions",sessions)):
        write(tmp_path/f"{name}.json",value)
    inputs=dict(p2_index=str(tmp_path/"index.json"),source_roster=str(tmp_path/"roster.json"),
                source_root=str(tmp_path),sessions=str(tmp_path/"sessions.json"))
    config=dict(length_ratio=1.25,bootstrap=2000,seed=20261017)
    result=execute(tmp_path/"out",inputs,config)
    assert result["primary"]["effect"]==2
    write(tmp_path/"call.json",dict(inputs=inputs,config=config))
    code="import ctypes,json,sys; from pathlib import Path; ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(),0x4000); from runners.drive.cards.events_d39 import verify; p=Path(sys.argv[1]); a=json.loads((p/'call.json').read_text()); assert verify(p/'out',a['inputs'],a['config'])['verified']"
    child=subprocess.run([sys.executable,"-B","-c",code,str(tmp_path)],capture_output=True,text=True,
                         env=dict(os.environ,PYTHONHASHSEED="431"),timeout=60)
    assert child.returncode==0,child.stderr
    import runners.drive.cards.events_d39 as module
    original=module.extract_failures;calls=[]
    def yielding(*args,**kwargs):
        if not calls:
            (tmp_path/"yielded"/"YIELD_REQUEST.json").write_text("{}",encoding="utf8")
        calls.append(1)
        return original(*args,**kwargs)
    monkeypatch.setattr(module,"extract_failures",yielding)
    pause=execute(tmp_path/"yielded",inputs,config)
    assert pause["status"]=="yielded" and pause["sessions_saved"]==1
    assert not (tmp_path/"yielded"/"SUMMARY.json").exists()
    (tmp_path/"yielded"/"YIELD_REQUEST.json").unlink()
    resumed=execute(tmp_path/"yielded",inputs,config)
    assert resumed["primary"]==result["primary"] and len(calls)==len(index)
    assert verify(tmp_path/"yielded",inputs,config)["verified"]
    (tmp_path/"out"/"MATCHES.json").write_text("[]",encoding="utf8")
    with pytest.raises(ValueError,match="output changed"):
        verify(tmp_path/"out",inputs,config)
