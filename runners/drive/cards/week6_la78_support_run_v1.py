"""Count and verify BG target support before either meeting outcome is opened."""
from collections import Counter
from itertools import combinations
from pathlib import Path

from .batch_runtime import filehash, read
from .week6_la78_source_v1 import checked_table, support_first
from .week6_la78_support_v1 import group_by


def independent_support(utterances, laughs, metadata):
    """Literal interval comparisons, independent of the indexed speaker-floor implementation."""
    acts = group_by(utterances, "meeting")
    events = group_by(laughs, "meeting")
    totals={"LA7":Counter(),"LA8":Counter()}
    pairs={"LA7":Counter(),"LA8":Counter()}
    for meeting, meta in metadata.items():
        roles={s:r.get("role") or "unreported" for s,r in meta["speakers"].items()}
        cards=["LA8"]
        if meta.get("scenario") and meta["corpus"]=="AMI" and "unreported" not in roles.values():
            cards.append("LA7")
        else:
            totals["LA7"]["meetings_without_qualified_roles"]+=1
        for card in cards:
            totals[card]["eligible_meetings"]+=1
        rows=acts[meeting]
        for laugh in events[meeting]:
            if laugh["label"]!="vocal":
                continue
            onset=laugh["start"]
            targets={a["speaker"] for a in rows if a["speaker"]!=laugh["speaker"]
                     and a["start"]<=onset and onset-2<=a["end"]}
            kind="multiple" if len(targets)>1 else "single" if targets else "self_laughter"
            distinct={tuple(sorted((roles[a],roles[b]))) for a,b in combinations(targets,2)}
            for card in cards:
                totals[card]["total"]+=1
                totals[card][kind]+=1
                totals[card]["candidate"]+=bool(targets)
                pairs[card].update(distinct)
    return totals,pairs


def execute(output,inputs,config):
    if config!={"phase":"BG-support","window_seconds":2.0}:
        raise ValueError("BG support has a frozen two-second attribution rule")
    path=Path(output)
    _,_,_,record=support_first(path,inputs)
    return dict(status="computed",scientific_verdict=None,populations=record["populations"],
                support_sha256=filehash(path/"BG_SUPPORT.json"),outcome_table_opened=False)


def verify(output,inputs,config):
    path=Path(output)
    repeated=execute(path/"independent-replay",inputs,config)
    if read(path/"BG_SUPPORT.json")!=read(path/"independent-replay/BG_SUPPORT.json"):
        raise ValueError("Original and reconstructed BG support differ")
    counts,pairs=independent_support(*(checked_table(inputs,key) for key in ("acts","laughs","metadata")))
    for card,row in repeated["populations"].items():
        for name in ("total","candidate","single","multiple","self_laughter","eligible_meetings","meetings_without_qualified_roles"):
            if counts[card][name]!=row.get(name,0):
                raise ValueError("Independent event inventory differs")
        if dict(pairs[card])!={(p["first"],p["second"]):p["count"] for p in row["candidate_role_pairs"]}:
            raise ValueError("Independent role-pair inventory differs")
    return dict(verified=True,outcome_table_opened=False,support_sha256=repeated["support_sha256"])
