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
