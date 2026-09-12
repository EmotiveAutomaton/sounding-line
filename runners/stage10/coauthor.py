"""Stage 10 wrapper for the reviewed source-defined CoAuthor handling task.

DESIGN CHECK: LESSONS 2-5 and CONTROLS 6. NULL and ALTERNATIVE both preserve
writer/prompt separation, actual predecision evidence and four-way support.
Future handling must never enter public target evidence. Repeated writer events
remain dependent and a small development writer count is a limitation, not n.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from pathlib import Path

from runners.stage9.coauthor_cases import inputs
from .contracts import PublicTask, choices_for, digest
from .ollama import now, write_new

DESCRIPTIONS = {
    "accept": "Accept an offered model suggestion and leave that insertion unedited before the next new menu.",
    "edit": "Accept an offered model suggestion, then edit its inserted text before the next new menu.",
    "dismiss": "Explicitly dismiss the displayed suggestion menu without a verified selection.",
    "ignore": "Leave this displayed menu without a recorded selection or explicit dismissal.",
}


def task_from(row: dict, view: str) -> PublicTask:
    if view not in {"artifact", "process-record"}:
        raise ValueError("this initial adapter exposes artifact or reviewed prior handling")
    native = row["views"]["artifact" if view == "artifact" else "record"]
    expected = {"document", "suggestions"} | ({"earlier_handling"} if view == "process-record" else set())
    if set(native) != expected or any(ordinal >= row["ordinal"] for ordinal in row["prior_source_ordinals"]):
        raise ValueError("public evidence or chronology differs from the reviewed projection")
    if not isinstance(native["document"], str) or not native["suggestions"] or not all(isinstance(item, str) for item in native["suggestions"]):
        raise ValueError("invalid draft or shown suggestion menu")
    if view == "process-record" and any(item not in DESCRIPTIONS for item in native["earlier_handling"]):
        raise ValueError("unrecognized earlier handling event")
    evidence = {key: native[key] for key in expected}
    return PublicTask(digest(["s10-coauthor", row["key"], view])[:32], "coauthor-handling", view,
                      evidence, "Predict how the human will handle this displayed model-suggestion menu.",
                      choices_for(list(DESCRIPTIONS.values()), row["key"]),
                      "after this menu is displayed, before the next new menu; only predecision evidence is visible",
                      "human selection and subsequent handling of model-authored suggestions",
                      "historically exposed corpus; descriptive prediction")


def prepare(output: Path):
    rows, metadata = inputs("scientific")
    output.mkdir(parents=True, exist_ok=False)
    public = {lane: [] for lane in rows}
    targets = {lane: [] for lane in rows}
    counts = {}
    for lane, limit in (("train", 40), ("development", 48), ("evaluation", 96)):
        per_writer = Counter()
        selected = []
        for row in sorted(rows[lane], key=lambda item: digest(["s10-coauthor-screen-v1", item["key"]])):
            if per_writer[row["unit"]] >= 8:
                continue
            if len(selected) >= limit:
                break
            selected.append(row)
            per_writer[row["unit"]] += 1
        for row in selected:
            for view in ("artifact", "process-record"):
                task = task_from(row, view)
                public[lane].append(asdict(task))
                targets[lane].append({"task_id": task.task_id, "source_event": row["key"],
                                      "writer_component": row["unit"], "prompt_component": row["stimulus"],
                                      "session": row["session"], "ordinal": row["ordinal"],
                                      "correct_choice": next(key for key, description in task.choices if description == DESCRIPTIONS[row["truth"]])})
        counts[lane] = {"distinct_events": len(selected), "writer_components": len(per_writer),
                        "prompt_components": len({row["stimulus"] for row in selected}), "public_tasks": len(public[lane]),
                        "maximum_events_per_writer": max(per_writer.values(), default=0)}
    for left, right in (("train", "development"), ("train", "evaluation"), ("development", "evaluation")):
        for key in ("writer_component", "prompt_component", "source_event"):
            if {row[key] for row in targets[left]} & {row[key] for row in targets[right]}:
                raise ValueError("source dependencies cross a stage partition")
    write_new(output / "SOURCE.json", metadata)
    for lane in rows:
        write_new(output / (lane + "-public.json"), {"tasks": public[lane]})
        write_new(output / (lane + "-evaluator.json"), {"targets": targets[lane]})
    summary = {"prepared_at": now(), "status": "FROZEN", "counts": counts,
               "public_sha256": {lane: digest({"tasks": public[lane]}) for lane in rows},
               "evaluator_sha256": {lane: digest({"targets": targets[lane]}) for lane in rows},
               "source_sha256": digest(metadata), "source_exposure": "historically exposed; descriptive",
               "development_limitation": "strict inherited writer/prompt separation leaves one development writer; routing generalization is not validated",
               "scope": "initial common cohort, two reviewed views; earlier-artifact view remains an explicit implementation obligation"}
    write_new(output / "FROZEN.json", summary)
    return summary
