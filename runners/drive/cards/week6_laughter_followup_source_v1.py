"""Qualify both strict-onset windows and the length-held pairs on the original meetings.

DESIGN CHECK. Keep every source utterance in linguistic history. Count the
candidate population, timing exclusions and control reuse before fitting. A
fresh replay reconstructs each window separately and compares every kept
numeric feature and pair. Meeting identifiers and utterance features stay
in the private source bundle.
"""
from collections import defaultdict
from pathlib import Path
import time

from . import week5_engine_export_io as seal
from . import week5_qualification_io as io
from . import week6_la6_followups_v1 as follow
from . import week6_la6_source_v1 as source
from . import week6_la6_v2 as parent

MODULE = "runners.drive.cards.week6_laughter_followup_source_v1"
WINDOWS = (1, 2)


def projection(acts, laughs, replay=False):
    """Pack windows and actual pairing audits with one copy of each feature vector."""
    matched_features, windows = {}, {}
    shared = None
    for seconds in WINDOWS:
        rows, eligible, vocal = follow.strict_labels(acts, laughs, seconds)
        if shared is None or replay:
            shared = parent.feature_rows(rows, vocal)
        if len(shared) != len(acts):
            raise ValueError("Incomplete original utterance history")
        variants = {}
        for name, matcher in (("strict", parent.match), ("length_held", follow.match_length)):
            pairs, audit = matcher(eligible)
            for pair in pairs:
                for role in ("case", "control"):
                    row = shared[pair["meeting"], pair[role]]
                    feature = {"act_type": row["act_type"], "numeric": row["numeric"]}
                    if matched_features.setdefault(row["id"], feature) != feature:
                        raise ValueError("Meeting feature differs between windows")
            variants[name] = {"pairs": [[p["case"], p["control"]] for p in pairs], "audit": audit}
        windows[str(seconds)] = dict(variants, excluded_preexisting=len(rows) - len(eligible))
    return {"source_utterances": len(acts), "features": matched_features, "windows": windows}



def rows_for_window(block, seconds, variant):
    """Expand exactly the matched case/control rows required by the parent fit."""
    if seconds not in WINDOWS or variant not in ("strict", "length_held"):
        raise ValueError("Unknown registered window or match rule")
    rows = []
    for case, control in block["windows"][str(seconds)][variant]["pairs"]:
        for role, key, label in (("case", case, 1), ("control", control, 0)):
            rows.append(dict(block["features"][key], meeting=block["meeting"], id=key,
                             pair=case, role=role, label=label))
    return rows

def source_binding(inputs):
    if set(inputs) != {"original_preparation", "original_preparation_sha256"}:
        raise ValueError("The frozen original LA6 source preparation is required")
    original = Path(inputs["original_preparation"])
    if io.sha(original / "COMPLETE.json") != inputs["original_preparation_sha256"]:
        raise ValueError("Source preparation completion differs")
    root, plan, _ = seal.complete(original, source.MODULE)
    earlier = seal.read(root / "output/RESULT.json")
    if not earlier.get("complete_preparation"):
        raise ValueError("Parent did not reconcile all source utterances")
    acts, laughs, metadata, identity = source.load_source(plan["inputs"])
    if len(acts) != earlier["all_original_utterances"]:
        raise ValueError("Original utterance count differs")
    identity.update(parent_preparation=inputs["original_preparation_sha256"],
                    strict_windows_sha256=io.sha(follow.__file__),
                    feature_math_sha256=io.sha(parent.__file__), preparation_sha256=io.sha(__file__))
    return acts, laughs, metadata, source.digest(identity)


def operation(output, inputs, config, replay=False):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    if config.get("phase") != "LA6-followup-source" or set(config) - {"phase", "max_new_meetings", "max_wall_seconds"}:
        raise ValueError("Exact registered LA6 follow-up source phase required")
    limit = config.get("max_new_meetings", 8)
    seconds = config.get("max_wall_seconds", 600)
    if type(limit) is not int or limit < 1 or not 0 < seconds <= 1200:
        raise ValueError("Invalid source preparation bounds")
    began = time.monotonic()
    acts, laughs, meta, binding = source_binding(inputs)
    groups, events = defaultdict(list), defaultdict(list)
    for act in acts:
        meeting = act["meeting"]
        if meta[meeting]["corpus"] not in ("AMI", "ICSI"):
            raise ValueError("Unregistered meeting corpus")
        groups[meeting].append(act)
    for event in laughs:
        events[event["meeting"]].append(event)
    meetings = sorted(groups)
    state = seal.state(output / "STATE.json", binding, {"parts": []})
    cursor = len(state["parts"])
    if cursor > len(meetings):
        raise ValueError("Impossible source cursor")
    total = 0
    for i, meeting in enumerate(meetings):
        path = output / "meetings" / f"{i:04d}.json"
        if i < cursor:
            record = state["parts"][i]
            if record["meeting"] != meeting or io.sha(path) != record["sha256"]:
                raise ValueError("A preserved meeting part differs")
        else:
            if i - cursor >= limit or source.requested(output, began, seconds):
                return {"status": "yielded", "verified": False, "completed": i, "total": len(meetings)}
            block = projection(groups[meeting], events[meeting], replay)
            block.update(binding=binding, meeting=meeting, corpus=meta[meeting]["corpus"])
            seal.checkpoint(path, block)
            record = {"meeting": meeting, "corpus": block["corpus"], "utterances": block["source_utterances"],
                      "sha256": io.sha(path), "relative": path.relative_to(output).as_posix()}
            state["parts"].append(record)
            seal.checkpoint(output / "STATE.json", state)
        total += record["utterances"]
    if total != len(acts):
        raise ValueError("Source population does not reconcile")
    result = {"card": "LA6-followup-source", "record_kind": "run", "complete_preparation": True,
              "scientific_admission": False, "by_construction": False, "theory_tags": [], "activation": [],
              "binding": binding, "meetings": len(meetings), "source_utterances": total,
              "manifest_sha256": io.sha(output / "STATE.json")}
    io.write_json(output / "RESULT.json", result)
    return result


def execute(output, inputs, config):
    return operation(output, inputs, config)


def verify(output, inputs, config):
    output = Path(output)
    replay = output / "independent-replay"
    result = operation(replay, inputs, config, replay=True)
    if result.get("status") == "yielded":
        return result
    if result != seal.read(output / "RESULT.json") or seal.read(replay / "STATE.json") != seal.read(output / "STATE.json"):
        raise ValueError("Independent meeting source manifests differ")
    return {"verified": True, "both_windows_replayed": True, "every_meeting_part_replayed": True}
