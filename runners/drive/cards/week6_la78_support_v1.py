"""Support-first meeting census for amendment BG. No next-minute outcomes here."""
from collections import Counter, defaultdict
from math import isclose

from .week6_la78_targets_v1 import SpeakerFloor, attribute, rate_credits


def group_by(rows, field):
    result = defaultdict(list)
    for row in rows:
        result[row[field]].append(row)
    return result


def meeting_support(utterances, laughs, metadata):
    roster = metadata["speakers"]
    roles = {speaker: row.get("role") or "unreported" for speaker, row in roster.items()}
    groups = group_by(utterances, "speaker")
    if any(s not in roster for s in groups):
        raise ValueError("Utterance speaker is outside the source roster")
    floors = {s: SpeakerFloor(groups[s]) for s in roster}
    counts, pairs, events = attribute(laughs, floors, roles)
    candidate = counts["single"] + counts["multiple"]
    all_laughs = candidate + counts["self"]
    fraction = counts["single"] / candidate if candidate else None
    qualified_roles = bool(metadata.get("scenario") and metadata["corpus"] == "AMI"
                           and all(role != "unreported" for role in roles.values()))
    support = dict(total=all_laughs, self_laughter=counts["self"], single=counts["single"],
                   multiple=counts["multiple"], candidate=candidate, scenario_roles=qualified_roles)
    support["pair_counts"] = [[a,b,count] for (a,b),count in sorted(pairs.items())]
    credits = rate_credits(events, roles)
    if any(not isclose(sum(credits[name].values()),expected,abs_tol=1e-8) for name,expected in
           (("single",counts["single"]),("latest",candidate),("fractional",candidate))):
        raise ValueError("Laughter target mass does not reconcile")
    return support, events


def census(utterances, laughs, metadata):
    utterance_groups = group_by(utterances, "meeting")
    laugh_groups = group_by(laughs, "meeting")
    if (set(utterance_groups)|set(laugh_groups))-set(metadata):
        raise ValueError("Meeting metadata missing")
    counts = {key:Counter() for key in ("LA7","LA8")}
    role_pairs = {key:Counter() for key in counts}
    for meeting in sorted(metadata):
        support,_ = meeting_support(utterance_groups[meeting],laugh_groups[meeting],metadata[meeting])
        for card in counts:
            if card=="LA7" and not support["scenario_roles"]:
                counts[card]["meetings_without_qualified_roles"]+=1
                continue
            counts[card]["eligible_meetings"]+=1
            counts[card].update({k:support[k] for k in ("total","self_laughter","single","multiple","candidate")})
            for a,b,n in support["pair_counts"]:
                role_pairs[card][a,b]+=n
    result={}
    for card,v in counts.items():
        def share(count,denominator):
            return count/v[denominator] if v[denominator] else None
        result[card]={**v,"single_share_among_candidate":share(v["single"],"candidate"),
                      "multiple_share_all":share(v["multiple"],"total"),
                      "multiple_share_among_candidate":share(v["multiple"],"candidate"),
                      "single_under_half":2*v["single"]<v["candidate"] if v["candidate"] else None,
                      "candidate_role_pairs":[dict(first=a,second=b,count=n,share_all=share(n,"total"),
                       share_with_candidate=share(n,"candidate"),share_ambiguous=share(n,"multiple"))
                       for (a,b),n in sorted(role_pairs[card].items())]}
    return result
