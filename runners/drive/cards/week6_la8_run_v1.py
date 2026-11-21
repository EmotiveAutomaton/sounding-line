"""Build the single-target next-minute comparison after support and the measure are frozen."""
from collections import Counter
from pathlib import Path

import numpy as np

from .batch_runtime import filehash, freeze, read
from .week6_la78_models_v1 import speaking_share, talk_crossproducts, talk_fit
from .week6_la78_source_v1 import checked_table, outcome_speech
from .week6_la78_support_v1 import group_by, meeting_support
from .week6_la78_targets_v1 import next_minute, SpeakerFloor

SEED = 202611208
DRAWS = 2000


def meeting_block(acts, laughs, words, meta, denominator):
    support, events = meeting_support(acts, laughs, meta)
    roster = meta["speakers"]
    tracks = group_by(words, "speaker")
    if set(tracks) - set(roster):
        raise ValueError("Speech speaker is outside meeting roster")
    floors = {speaker: SpeakerFloor(tracks[speaker]) for speaker in roster}
    onsets = {speaker: [row["start"] for row in rows if row["label"] == "vocal"]
              for speaker, rows in group_by(laughs, "speaker").items()}
    rows, excluded = next_minute(events, onsets, floors, 0., meta["duration"])
    if len(rows)+excluded["incomplete paired minutes"] != support["single"]:
        raise ValueError("Single-target window census does not reconcile")
    counts = Counter(single=support["single"], truncated=excluded["incomplete paired minutes"])
    used = []
    for row in rows:
        time, target = row["onset"], row["target"]
        before = speaking_share(target, floors, time-60, time, denominator)
        after = speaking_share(target, floors, time, time+60, denominator)
        if before is None or after is None:
            counts["undefined_share"] += 1
        else:
            counts["joined" if row["joined"] else "unjoined"] += 1
            used.append(dict(joined=row["joined"],phase=row["phase"],before=before,after=after))
    return talk_crossproducts(used), counts


def fit_meetings(blocks):
    sizes = len(blocks)
    if not sizes:
        return dict(effect_points=None, interval=None, undefined_draws=DRAWS, status="could not say")
    point = talk_fit(blocks, np.ones(sizes, dtype=int))
    bank = []
    gram = np.asarray([item[0] for item in blocks])
    rhs = np.asarray([item[1] for item in blocks])
    for ordinal in range(DRAWS):
        rng = np.random.default_rng(np.random.SeedSequence([SEED, ordinal]))
        weights = np.bincount(rng.integers(sizes, size=sizes), minlength=sizes)
        cross = np.tensordot(weights, gram, axes=1)
        product = weights @ rhs
        if np.linalg.matrix_rank(cross) == 4:
            bank.append(100.*float(np.linalg.solve(cross, product)[1]))
    interval = np.quantile(bank, [.025, .975]).tolist() if len(bank) == DRAWS else None
    status = "could not say" if point is None or interval is None else (
             "registered bar met" if point <= -2 and interval[1] < 0 else "registered bar not met")
    return dict(effect_points=point, interval=interval, undefined_draws=DRAWS-len(bank), status=status)


def execute(output, inputs, config):
    output = Path(output)
    decision = Path(inputs["measure_decision"])
    if filehash(decision) != inputs["measure_decision_sha256"]:
        raise ValueError("Prospective speaking-share decision changed")
    spec = read(decision)
    denominator = spec["primary_denominator"]
    if (denominator not in ("voiced","elapsed") or spec.get("owner_approved") is not True
            or spec.get("card") != "LA8" or config != dict(denominator=denominator, draws=DRAWS)):
        raise ValueError("Approved prospective LA8 denominator required")
    support = Path(inputs["support"])
    receipt = Path(inputs["support_receipt"])
    if (filehash(receipt) != inputs["support_receipt_sha256"] or filehash(support) != inputs["support_sha256"]
            or read(receipt)["full_write_through"] is not True or read(receipt)["support_sha256"] != filehash(support)):
        raise ValueError("Filed support census required before speech access")
    inventory = read(support)["populations"]["LA8"]
    meta = checked_table(inputs, "metadata")
    acts = group_by(checked_table(inputs, "acts"), "meeting")
    laughs = group_by(checked_table(inputs, "laughs"), "meeting")
    speech = group_by(outcome_speech(inputs,support), "meeting")
    counts = Counter()
    blocks = []
    for meeting, info in sorted(meta.items()):
        block, rows = meeting_block(acts[meeting], laughs[meeting], speech[meeting], info, denominator)
        blocks.append(block)
        counts.update(rows)
    if (counts["single"] != inventory["single"] or len(blocks) != inventory["eligible_meetings"]
            or counts["single"] != sum(counts[k] for k in ("truncated","undefined_share","joined","unjoined"))):
        raise ValueError("Filed population differs from fit roster")
    result = dict(card="LA8", denominator=denominator, counts=dict(counts), meetings=len(blocks),
                  support=inventory, limit_single_under_half=inventory["single_under_half"],
                  draws=DRAWS, model=fit_meetings(blocks))
    path = output/"NEXT_MINUTE.json"
    output.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if read(path) != result:
            raise ValueError("Prior next-minute result differs")
    else:
        freeze(path,result)
    return result


def verify(output, inputs, config):
    output = Path(output)
    if execute(output/"independent-replay", inputs, config) != read(output/"NEXT_MINUTE.json"):
        raise ValueError("Fresh next-minute original-source replay differs")
    return dict(verified=True, checked_draws=DRAWS)
