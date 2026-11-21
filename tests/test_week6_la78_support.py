from runners.drive.cards.week6_la78_support_v1 import census


def test_roster_separation_and_ambiguous_pair_denominators():
    roster = {"A":{"role":"chair"},"B":{"role":"design"},"C":{"role":"sales"}}
    metadata = {"s":{"scenario":True,"corpus":"AMI","speakers":roster},
                "n":{"scenario":False,"corpus":"ICSI","speakers":roster}}
    acts = [dict(meeting="s",speaker="B",start=12,end=15),dict(meeting="s",speaker="C",start=10,end=12)]
    laughs = [dict(meeting="s",speaker="A",label="vocal",start=t) for t in (8,13,17)]
    laughs.append(dict(meeting="n",speaker="A",label="vocal",start=8))
    result=census(acts,laughs,metadata)
    role=result["LA7"]
    assert role["total"]==3 and role["single"]==1 and role["multiple"]==1 and role["self_laughter"]==1
    assert role["multiple_share_all"]==1/3 and role["single_share_among_candidate"]==.5
    assert role["single_under_half"] is False
    assert role["candidate_role_pairs"]==[dict(first="design",second="sales",count=1,share_all=1/3,
                                              share_with_candidate=.5,share_ambiguous=1.)]
    assert result["LA8"]["eligible_meetings"]==2 and result["LA8"]["self_laughter"]==2


def test_zero_support_keeps_undefined_share():
    result=census([],[],{"s":{"corpus":"AMI","scenario":True,"speakers":{"a":{"role":"designer"}}}})
    assert result["LA7"]["single_under_half"] is None
    assert result["LA8"]["multiple_share_among_candidate"] is None
