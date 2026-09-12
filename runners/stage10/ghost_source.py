"""Join only frozen training cases to original Ghost recorded outcomes.

DESIGN CHECK: LESSONS2-5. Under NULL/ALTERNATIVE, source hashes, task joins,
case allocations and actual-outcome types must validate. Expected reference
predictions are never training truth. Development/evaluation files stay unopened.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from .contracts import digest
from .ghost import envelopes, task_from
from .reader import from_record, build
from .ollama import now, write_new
from .queue import read


def prepare(public_root, export, output):
    allocation = read(output/"ALLOCATION.json")
    manifest = read(public_root/"PUBLIC_MANIFEST.json")
    if digest(manifest) != allocation["source_public_manifest_sha256"]:
        raise ValueError("public manifest differs from allocation")
    training = set(allocation["train_cases"])
    development = set(allocation["development_cases"])
    if training & development or (training | development) & set(allocation["excluded_pilot_cases"]):
        raise ValueError("case allocation leak")
    members = {c["case_id"]:set(c["tasks_in_recorded_order"]) for c in manifest["cases"]}
    train = read(output/"train-public.json")
    dev = read(output/"development-public.json")
    task_by_id = {r["task_id"]:from_record(r) for r in train["tasks"]}
    raw_manifest = read(export/"RAW_MANIFEST.json")
    index = raw_manifest["files"]
    labels = []; sources = {}
    for case in sorted(training):
        relative = "private/"+case+"-evaluation.json"
        p = export/relative
        payload = p.read_bytes()
        actual = hashlib.sha256(payload).hexdigest()
        if actual != index[relative]:
            raise ValueError("training evaluator changed")
        data = json.loads(payload)
        if data["case_id"] != case or set(data["task_ids"]) != members[case]:
            raise ValueError("training task/case join differs")
        outcome = data["hidden_continuations"]
        if type(outcome["artifact"]) is not int or outcome["artifact"] not in (0,1) or type(outcome["legal"]) is not bool or outcome["attempted_option"] not in (0,1):
            raise ValueError("training target is not a recorded binary enacted artifact")
        sources[case] = {"sha256": actual, "source": data["source"], "target_field": "hidden_continuations.artifact"}
        for row in allocation["tasks"]:
            if row["case_id"] != case:
                continue
            if row["lane"] != "train" or row["task_id"] not in task_by_id:
                raise ValueError("allocation/training source differs")
            task = task_by_id[row["task_id"]]
            labels.append({"task_id":task.task_id, "correct_choice":next(k for k,v in task.choices if v==str(outcome["artifact"])),
                           "case_id":case,"target_source":"actual recorded execution; not reference forecast"})
    answers={"targets":labels}
    for row in dev["tasks"]:
        build(from_record(row),"R1",train["tasks"],labels)
    source={"at":now(),"training_evaluators":sources,"raw_manifest_sha256":hashlib.sha256((export/"RAW_MANIFEST.json").read_bytes()).hexdigest(),
            "development_answers_opened":False,"scope":allocation["scope"],"preparation_source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    frozen={"at":now(),"scope":allocation["scope"],"public_sha256":{"train":digest(train),"development":digest(dev)},
            "evaluator_sha256":{"train":digest(answers)},"allocation_sha256":digest(allocation),
            "counts":{"train_cases":len(training),"development_cases":len(development),"train_tasks":len(train["tasks"]),"development_tasks":len(dev["tasks"])} }
    write_new(output/"train-evaluator.json",answers)
    write_new(output/"SOURCE.json",source)
    write_new(output/"FROZEN.json",frozen)
    return frozen


if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--public-root",type=Path,required=True)
    p.add_argument("--export",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();r=prepare(a.public_root,a.export,a.output);print(json.dumps(r["counts"]))
