from runners.drive.cards.week6_la78_support_run_v1 import independent_support
from runners.drive.cards.week6_la78_support_v1 import census


def test_direct_replay_and_indexed_census_agree_on_both_populations():
    import random
    rng=random.Random(2501)
    roles={s:{"role":r} for s,r in zip("ABCDE",("manager","design","sales","sales","design"))}
    metadata={m:{"speakers":roles,"corpus":c,"scenario":m=="one"} for m,c in (("one","AMI"),("two","ICSI"))}
    acts=[];laughs=[]
    for meeting in metadata:
        for _ in range(120):
            onset=rng.randrange(240)
            acts.append(dict(speaker=rng.choice("ABCDE"),start=onset,end=onset+rng.randrange(10),meeting=meeting))
            laughs.append(dict(speaker=rng.choice("ABCDE"),start=rng.randrange(260),meeting=meeting,label="vocal"))
    indexed=census(acts,laughs,metadata);counts,pairs=independent_support(acts,laughs,metadata)
    for card,row in indexed.items():
        assert all(row.get(key,0)==value for key,value in counts[card].items())
        assert pairs[card]=={(item["first"],item["second"]):item["count"] for item in row["candidate_role_pairs"]}
