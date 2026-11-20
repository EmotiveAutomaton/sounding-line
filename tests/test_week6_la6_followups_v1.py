from runners.drive.cards import week6_la6_followups_v1 as follow


def act(name, start, end, n=4, speaker="a"):
    return dict(meeting="m",id=name,speaker=speaker,act_type="statement",
                start=start,end=end,words=[{"text":"word","kind":"word"} for _ in range(n)])


def event(start,end,label="vocal"):
    return dict(meeting="m",speaker="b",label=label,start=start,end=end)


def test_onset_edges_and_preexisting_vocal_overlap():
    a=act("target",10,11)
    for begin,end,eligible,one,two in [(11.,11.,False,False,False),
         (12.,12.1,True,True,True),(13.,13.2,True,False,True),
         (13.001,14.,True,False,False),(5.,9.,False,False,False),
         (6.,8.999,True,False,False)]:
        for window, label in [(1,one),(2,two)]:
            rows, allowed, _=follow.strict_labels([a],[event(begin,end)],window)
            assert bool(allowed)==eligible and rows[0]["laughed_after"]==label


def test_only_vocal_events_count():
    _, allowed, _=follow.strict_labels([act("x",1,2)],[event(1,3,"breath")],1)
    assert len(allowed)==1 and not allowed[0]["laughed_after"]


def test_length_search_considers_more_distant_eligible_controls_and_reuse():
    def r(name,t,n,out):
        return dict(meeting="m",id=name,speaker="a",act_type="question",start=t,end=t+1,
                    text="fixture",word_count=n,laughed_after=out)
    rows=[r("z",10,20,False),r("a",10,20,False),r("close",45,26,False),
          r("case1",80,20,True),r("case2",81,21,True),r("far",151,23,False)]
    pairs, audit=follow.match_length(rows)
    assert [p["control"] for p in pairs]==["a","far"]
    # Identical distances choose the earlier start, then the earlier source id.
    pairs, audit=follow.match_length(rows[:-1])
    assert [p["control"] for p in pairs]==["a","a"]
    assert audit["reused_control_copies"]==1


def test_half_threshold_and_covariate_omission_preserve_every_other_feature():
    assert follow.retained_route(10,5)=="matched"
    assert follow.retained_route(10,4)=="covariate"
    assert follow.retained_route(0,0)=="unsupported"
    x={"numeric":[12,3,4,7],"role":"case"}
    assert follow.omit_length([x])==[{"numeric":[0,3,4,7],"role":"case"}]
    assert x["numeric"][0]==12


def test_excluded_utterance_still_supplies_preceding_context():
    acts=[act("c",0,1),act("previous",40,41),act("target",46,47)]
    acts[0]["words"]=[{"text":"different","kind":"word"}]
    x=follow.project_meeting(acts,[event(40.2,40.5),event(48,48.1)],1)
    assert x["excluded_preexisting_vocal_laugh"]==1
    positive,= (r for r in x["strict"]["table"] if r["role"]=="case")
    assert positive["id"]=="target" and positive["numeric"][0]==4
    assert positive["numeric"][2]==1


def test_both_source_windows_match_independent_reference_and_reused_controls():
    from runners.drive.cards import week6_laughter_followup_source_v1 as source

    acts = [act("control", 0, 1), act("quick", 40, 41), act("later", 80, 81),
            act("excluded", 95, 98)]
    laughs = [event(41.5, 42), event(82.5, 83), event(96, 97)]
    stored = dict(source.projection(acts, laughs), meeting="m")
    assert stored == dict(source.projection(acts, laughs, True), meeting="m")
    for seconds in (1, 2):
        reference = follow.project_meeting(acts, laughs, seconds)
        for name in ("strict", "length_held"):
            rows = source.rows_for_window(stored, seconds, name)
            assert rows == reference[name]["table"]
            assert stored["windows"][str(seconds)][name]["audit"] == reference[name]["audit"]
            assert all("text" not in row and "words" not in row for row in rows)
    assert len(stored["windows"]["2"]["strict"]["pairs"]) > len(stored["windows"]["1"]["strict"]["pairs"])


def test_source_resume_and_fresh_replay_validate_each_meeting(tmp_path, monkeypatch):
    from runners.drive.cards import week6_laughter_followup_source_v1 as source
    import pytest

    meetings = ["a", "b"]
    acts = [dict(row, meeting=m) for m in meetings for row in [act("one", 0, 1), act("two", 42, 43)]]
    laughs = [dict(event(43.5, 44), meeting=m) for m in meetings]
    meta = {"a": {"corpus": "AMI"}, "b": {"corpus": "ICSI"}}
    monkeypatch.setattr(source, "source_binding", lambda inputs: (acts, laughs, meta, "made-up-identity"))
    config = {"phase": "LA6-followup-source", "max_new_meetings": 1, "max_wall_seconds": 600}
    assert source.execute(tmp_path, {}, config)["status"] == "yielded"
    done = source.execute(tmp_path, {}, config)
    assert done["source_utterances"] == 4 and done["meetings"] == 2
    assert source.verify(tmp_path, {}, config)["status"] == "yielded"
    assert source.verify(tmp_path, {}, config)["every_meeting_part_replayed"]
    part = tmp_path / "meetings/0000.json"
    part.write_bytes(part.read_bytes() + b" ")
    with pytest.raises(ValueError, match="preserved meeting part differs"):
        source.execute(tmp_path, {}, config)
