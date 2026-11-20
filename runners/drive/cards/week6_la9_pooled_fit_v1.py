"""Pooled dialogue-act odds on the original LA6 paired utterances.

DESIGN CHECK (LESSONS 3–5). Reusing a control cannot create a fiftieth
utterance. Empty nuisance levels never erase an otherwise identifiable class
contrast. If the fixed reference or the target is absent in a draw, its
contrast has no interval. The original paired labels and both model arms stay
fixed. A constructed fit is compared to the original solver before release.
"""
from pathlib import Path
import time
import warnings
from zipfile import ZipFile

import numpy as np
from sklearn.base import clone
from sklearn.exceptions import ConvergenceWarning
from threadpoolctl import threadpool_limits

from . import timing_p6
from . import week5_engine_export_io as seal
from . import week5_qualification_io as io
from . import week5_rr3_v1 as compare
from . import week6_la6_runner_v2 as parent
from . import week6_la6_source_v1 as source
from . import week6_la6_v2 as model
from . import week6_la9_classes_v1 as classes
from .week6_laughter_followup_fit_v1 import fixed_folds, stored

MODULE = "runners.drive.cards.week6_la9_pooled_fit_v1"


def load(inputs):
    if set(inputs) != {"original_preparation", "original_complete_sha256", "registration", "proof", "icsi_map"}:
        raise ValueError("The original paired table and prospective dictionaries are required")
    root = Path(inputs["original_preparation"])
    if io.sha(root / "COMPLETE.json") != inputs["original_complete_sha256"]:
        raise ValueError("Original LA6 source completion differs")
    _, plan, finished = seal.complete(root, source.MODULE)
    registration, proof = seal.read(inputs["registration"]), seal.read(inputs["proof"])
    if proof["registration_sha256"] != io.sha(inputs["registration"]) or proof["heldout_data_opened"] is not False:
        raise ValueError("Prospective dictionary proof differs")
    upstream = Path(plan["inputs"]["source_root"])
    origin_plan = seal.read(upstream / "PLAN.json")
    archive = Path(origin_plan["inputs"]["archive_root"]) / "AMI.zip"
    if io.sha(archive) != origin_plan["pins"][str(archive)]:
        raise ValueError("Original AMI archive differs")
    member = registration["ami"]["archive_member"]
    with ZipFile(archive) as z:
        if z.namelist().count(member) != 1:
            raise ValueError("AMI ontology not uniquely identified")
        maps = classes.dictionaries(registration, z.read(member), inputs["icsi_map"])
    if len(maps["AMI"]) != proof["ami_labels"] or len(maps["ICSI"]) != proof["icsi_labels"]:
        raise ValueError("Prospective dictionary coverage differs")
    metadata = upstream / "output/METADATA.json.gz"
    if io.sha(metadata) != seal.read(upstream / "COMPLETE.json")["outputs"]["output/METADATA.json.gz"]:
        raise ValueError("Meeting to corpus binding differs")
    corpus = {meeting: row["corpus"] for meeting, row in timing_p6.gzread(metadata).items()}
    table = root / "output/TABLE.json"
    if io.sha(table) != finished["outputs"]["output/TABLE.json"] or not seal.read(root/"RESULT.json")["complete_preparation"]:
        raise ValueError("Original complete table differs")
    rows = seal.read(table)["rows"]
    threshold = registration["minimum_distinct_heldout_utterances"]
    if threshold != 50:
        raise ValueError("Published class support floor differs")
    relabelled, support, unscored = classes.relabel(rows, corpus, maps, threshold)
    identity = dict(parent_complete=inputs["original_complete_sha256"], table=io.sha(table),
                    registration=proof["registration_sha256"], dictionary_proof=io.sha(inputs["proof"]),
                    metadata=io.sha(metadata))
    return relabelled, support, unscored, identity


def state_for_fit(rows, support):
    """Both design matrices use the parent's complete-table coding and original labels."""
    meetings = sorted({r["meeting"] for r in rows})
    if not meetings:
        return None
    meeting_number = {key: i for i, key in enumerate(meetings)}
    group = np.asarray([meeting_number[r["meeting"]] for r in rows])
    y = np.asarray([r["label"] for r in rows])
    folds = fixed_folds(meetings)
    if set(y) != {0, 1}:
        raise ValueError("Original paired comparison requires cases and controls")
    arms = {}
    for inc in (True, False):
        fitted, template = model.fitted(rows, inc)
        matrix, _ = model.encoding(rows, inc, template)
        arms[str(inc)] = (fitted, matrix, 9 if inc else 8)
    categories = template[0]
    names = {name: i for i, name in enumerate(categories)}
    return dict(group=group, meetings=len(meetings), fold_counts=[sum(v == k for v in folds.values())
                for k in sorted(set(folds.values()))], y=y, arms=arms, categories=categories,
                term=np.asarray([names[r["act_type"]] for r in rows]),
                eligible={name: names[name] for name in sorted(support) if support[name]["eligible"]})


def coefficients(state, ordinal=None):
    ref = state["categories"][0]
    if ordinal is None:
        w = None
        present = set(state["term"])
    else:
        n = state["meetings"]
        rng = np.random.default_rng(np.random.SeedSequence([model.SEED, ordinal, 6]))
        w = np.bincount(rng.integers(n, size=n), minlength=n)[state["group"]]
        present = set(np.unique(state["term"][w > 0]))
    result = {}
    for name, (base, x, offset) in state["arms"].items():
        values = {}
        if ref in state["eligible"] and 0 in present:
            fit = base
            if w is not None:
                with threadpool_limits(limits=2), warnings.catch_warnings():
                    warnings.simplefilter("error", ConvergenceWarning)
                    fit = clone(base).fit(x, state["y"], sample_weight=w)
            for tag, index in state["eligible"].items():
                if index in present:
                    values[tag] = 0. if index == 0 else float(fit.coef_[0][offset + index - 1])
        result[name] = {tag: values.get(tag) for tag in state["eligible"]}
    return result


def assemble(state, support, unscored, point, bank):
    if state is None:
        return dict(status="below floor, descriptive", classes=support, unassigned_distinct=unscored, draws=0)
    if len(bank) != 2000:
        raise ValueError("Every registered draw is required")
    result = {}
    for history, arm in point.items():
        findings = {}
        for tag, count in support.items():
            row = dict(count, reference=(tag == state["categories"][0]))
            if not count["eligible"]:
                row["status"] = "below class floor"
            elif arm[tag] is None:
                row["status"] = "reference below class floor"
            else:
                values = [entry[history][tag] for entry in bank]
                missing = [i for i, v in enumerate(values) if v is None]
                row.update(odds_ratio=float(np.exp(arm[tag])), absent_draws=missing)
                if missing:
                    row["status"] = "interval unavailable"
                elif row["reference"]:
                    row["status"] = "reference"
                else:
                    row.update(status="descriptive" if state["meetings"] < 20 else "estimated",
                               interval=np.exp(np.quantile(values, [.025, .975])).tolist(),
                               log_odds_standard_error=float(np.std(values, ddof=1)))
            findings[tag] = row
        result[history] = findings
    return dict(arms=result, reference=state["categories"][0], unassigned_distinct=unscored,
                meetings=state["meetings"], heldout_meetings_by_fold=state["fold_counts"], draws=len(bank))


def operation(output, inputs, config):
    if config.get("phase") != "LA9" or config.get("draws") != 2000:
        raise ValueError("Original pooled-act table and 2,000 draws required")
    limit, seconds = parent.settings(dict(config, phase="LA6"))
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    rows, support, unscored, identity = load(inputs)
    binding = source.digest(dict(source=identity, math=io.sha(model.__file__), runner=io.sha(__file__)))
    cursor = seal.state(output/"STATE.json", binding, {"completed": 0})["completed"]
    if type(cursor) is not int or not 0 <= cursor <= 2000:
        raise ValueError("Invalid pooled-table draw cursor")
    state = state_for_fit(rows, support)
    bank = []
    if state is not None:
        point = coefficients(state)
        for i in range(2000):
            path = output/"draws"/f"{i:04d}.json"
            if i >= cursor:
                if i-cursor >= limit or source.requested(output, started, seconds):
                    return dict(status="yielded", verified=False, completed=i, total=2000)
                row = dict(binding=binding, index=i, value=coefficients(state, i))
                if path.exists() and path.with_suffix(".seal.json").exists():
                    compare.compare_record(stored(path), row)
                else:
                    seal.checkpoint(path, row)
                seal.checkpoint(output/"STATE.json", dict(binding=binding, completed=i+1))
            saved = stored(path)
            if saved["binding"] != binding or saved["index"] != i:
                raise ValueError("Pooled table checkpoint identity differs")
            bank.append(saved["value"])
    else:
        point = None
    result = assemble(state, support, unscored, point, bank)
    result.update(card="LA9", source_identity=identity, matched_rows=len(rows), complete_computation=True,
                  record_kind="claim", theory_tags=["H18-S5"], by_construction=False, activation=[])
    io.write_json(output/"RESULT.json", result)
    return result


def execute(output, inputs, config):
    return operation(output, inputs, config)


def verify(output, inputs, config):
    output = Path(output)
    replay = output/"independent-replay"
    result = operation(replay, inputs, config)
    if result.get("status") == "yielded":
        return result
    compare.compare_record(seal.read(output/"RESULT.json"), result)
    for i in range(result["draws"]):
        name = Path("draws")/f"{i:04d}.json"
        compare.compare_record(stored(output/name), stored(replay/name))
    return dict(verified=True, original_pairs_retained=True, pooled_class_draws_replayed=True)
