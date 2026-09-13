"""Finite manifest-driven cloud block; inference only, no evaluator access.

DESIGN CHECK: LESSONS3-5, Round 1 sections2-6. Both null and alternative run
identical complete model/method blocks. Repeated/changed tasks, incomplete
counterparts, profile drift, corrupt replay and unknown interrupted attempts
refuse. Completed attempts are reused; invalid forecasts remain charged rows.
"""
from __future__ import annotations
from collections import defaultdict
from dataclasses import asdict
import hashlib
from pathlib import Path
import time
from . import ollama, deliberation, human_routes, human_memory, human_memory_routes, human_programs
from . import structured, reading_routes
from .contracts import canonical, digest
from .reader import from_record
from .ghost import task_from
from .gear3_io import inventory
from .queue import read

SCHEMA = "stage10.gear3.block.1"
PINS = {"9b": "6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7",
        "27b": "7653528ba5cba4dd8e19da24aaddc7f4d0b5ecd93571c0825dfd4137958ec06e"}
METHODS = {"P": {"R0", "R2", "R3", "R1-memory", "R4-opaque", "R4-grounded"},
           "A": {"R0", "R2", "R3"}, "B": {"R0", "R3"},
           "C": {"R1-memory", "R4-opaque", "R4-grounded"}, "D": {"R0", "R2", "R3"}}


def validate(manifest):
    if set(manifest) != {"schema", "block_id", "node", "profiles", "tasks", "training", "units", "source_hashes", "scope"} or manifest["schema"] != SCHEMA:
        raise ValueError("unexpected cloud block fields")
    if manifest["node"] not in METHODS or not manifest["units"] or not manifest["tasks"]:
        raise ValueError("empty or unsupported block")
    if not isinstance(manifest['block_id'],str) or not manifest['block_id'] or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in manifest['block_id']):
        raise ValueError('unsafe block identifier')
    if set(manifest["profiles"]) != set(PINS): raise ValueError("both frozen model counterparts required")
    profiles = {k: ollama.ReaderProfile(**v) for k,v in manifest["profiles"].items()}
    for k,p in profiles.items():
        if p.model != "qwen3.5:"+k or p.model_digest != PINS[k]: raise ValueError("cloud model pin changed")
    if len({p.server_version for p in profiles.values()}) != 1: raise ValueError("unmatched serving versions")
    tasks={}
    for row in manifest["tasks"]:
        if set(row) != {"record", "envelope", "group"}: raise ValueError("unexpected target data")
        if not isinstance(row["group"], str) or not row["group"]: raise ValueError("missing source group")
        task=from_record(row["record"])
        if task.task_id in tasks: raise ValueError("duplicate target record")
        if task.family == "coauthor-handling":
            human_programs.features(task)
            if row["envelope"] is not None: raise ValueError("human record has foreign envelope")
        elif task.family.startswith("ghost-"):
            if task != task_from(row["envelope"]): raise ValueError("Ghost envelope does not reconstruct public task")
            if task.family not in {"ghost-opportunity", "ghost-reading"}: raise ValueError("source adapter not admitted")
        else: raise ValueError("source adapter not admitted")
        tasks[task.task_id]=(task,row)
    if set(manifest["training"]) - {"coauthor-handling", "ghost-reading"}: raise ValueError("unsupported training source")
    training_ids=set()
    for family, data in manifest["training"].items():
        if set(data) != {"public", "answers"}: raise ValueError("unexpected training input")
        public={from_record(r).task_id:from_record(r) for r in data["public"]}
        truth={r["task_id"]:r["correct_choice"] for r in data["answers"]}
        if len(public)!=len(data["public"]) or len(truth)!=len(data["answers"]) or set(public)!=set(truth):
            raise ValueError("training join is not one to one")
        for tid,t in public.items():
            if t.family!=family or truth[tid] not in dict(t.choices): raise ValueError("training target/support mismatch")
            if family == "coauthor-handling": human_programs.features(t)
        for answer in data['answers']:
            required={'task_id','correct_choice','writer_component','source_event'} if family=='coauthor-handling' else {'task_id','correct_choice','case_id'}
            allowed=required|({'prompt_component'} if family=='coauthor-handling' else set())
            if not required<=set(answer)<=allowed or any(not isinstance(answer[k],str) or not answer[k] for k in required):
                raise ValueError('training answer has missing metadata or unpermitted fields')
        training_ids.update(public)
    if training_ids & set(tasks): raise ValueError("training overlaps target task IDs")
    if manifest['node'] != 'P':
        for family,data in manifest['training'].items():
            field='writer_component' if family=='coauthor-handling' else 'case_id'
            train_groups={r[field] for r in data['answers']}
            if any(row['group'] in train_groups for task,row in tasks.values() if task.family==family):
                raise ValueError('scientific target overlaps a training source group')
    pairs=defaultdict(set); by_task=defaultdict(set); ids=[]
    for unit in manifest["units"]:
        if set(unit)!={"task_id", "model", "arm"} or unit["task_id"] not in tasks or unit["model"] not in profiles or unit["arm"] not in METHODS[manifest["node"]]:
            raise ValueError("undeclared cloud unit")
        task=tasks[unit["task_id"]][0]
        if task.family=="ghost-opportunity" and unit["arm"] not in {"R0","R2","R3"}: raise ValueError("opportunity memory is not implemented")
        if unit["arm"] in METHODS["C"] and task.family not in manifest["training"]: raise ValueError("memory needs its permitted training pool")
        # The actual nested builder rechecks feedback/representation bounds.
        ollama.request_for(task, generated_tokens=768, profile=profiles[unit["model"]])
        key=digest(unit);ids.append(key)
        pairs[(unit["task_id"],unit["arm"])].add(unit["model"])
        by_task[unit["task_id"]].add(unit["arm"])
    if len(set(ids))!=len(ids) or set(by_task)!=set(tasks) or any(x!=set(PINS) for x in pairs.values()):
        raise ValueError("duplicate, missing or unmatched model counterparts")
    if manifest["node"] != "P" and any(x!=METHODS[manifest["node"]] for x in by_task.values()):
        raise ValueError("incomplete scientific method comparison")
    families={t.family for t,r in tasks.values()}
    if len(families)!=1: raise ValueError("a block must belong to one source family")
    if len({(t.evidence_view,t.question) for t,r in tasks.values()})!=1:
        raise ValueError("a block must have one target and evidence condition")
    if manifest["node"] != "P" and len(tasks) > (8 if families=={"coauthor-handling"} else 4):
        raise ValueError("comparison block exceeds prescribed size")
    return tasks,profiles


def code_matches(source_hashes):
    root=Path(__file__).resolve().parents[2]
    for name,expected in source_hashes.items():
        p=root/name
        if not name.endswith(".py") or not p.resolve().is_relative_to(root) or hashlib.sha256(p.read_bytes()).hexdigest()!=expected:
            raise ValueError("cloud source/configuration changed")
    required={"runners/stage10/gear3_batch.py", "runners/stage10/ollama.py", "runners/stage10/gear3_io.py"}
    if not required.issubset(source_hashes): raise ValueError("cloud source closure is incomplete")


def dispatch(task, row, arm, profile, output, training, ghost_root):
    kwargs={"profile":profile}
    if arm=="R0": return ollama.call(task, output, **kwargs)
    if arm=="R2": return deliberation.route(task, output, **kwargs)
    if task.family=="coauthor-handling":
        if arm=="R3": return human_routes.route(task, output, **kwargs)
        data=training[task.family]
        learned=human_memory.induce(data["public"],data["answers"])
        return human_memory_routes.route(task,output,arm,data["public"],data["answers"],learned,**kwargs)
    if ghost_root is None: raise ValueError("actual public Ghost executor is required")
    if task.family=="ghost-opportunity": return structured.route(ghost_root,row["envelope"],output,**kwargs)
    data=training.get("ghost-reading", {"public":[], "answers":[]})
    return reading_routes.route(ghost_root,row["envelope"],output,data["public"],data["answers"],
                                "R1" if arm=="R1-memory" else arm,row["group"],**kwargs)


def run_block(manifest, output: Path, *, ghost_root=None, before_model=None, stop_after=None):
    tasks,profiles=validate(manifest);code_matches(manifest["source_hashes"])
    binding=digest(manifest)
    complete=output/"COMPLETE.json"
    if complete.exists():
        receipt=read(complete)
        if receipt["binding"]!=binding: raise ValueError("completed block changed")
        observed=inventory(output);observed.pop("COMPLETE.json")
        if observed!=receipt["files"]: raise ValueError("completed block evidence changed")
        # Reconstruct every completed native route, including its literal parse.
        # No callback/model load occurs, and network access is forbidden.
        from unittest.mock import patch
        def forbidden(*args, **kwargs): raise ValueError("completed replay attempted inference")
        with patch.object(ollama, "api", forbidden):
            for unit in manifest["units"]:
                folder=output/"units"/digest(unit)[:32]
                saved=read(folder/"UNIT.json")
                task,row=tasks[unit["task_id"]]
                result=dispatch(task,row,unit["arm"],profiles[unit["model"]],folder/"route",manifest["training"],ghost_root)
                if result!=saved["result"]: raise ValueError("completed native route does not reproduce")
        return receipt
    output.mkdir(parents=True,exist_ok=True)
    if (output/"BLOCK.json").exists():
        if digest(read(output/"BLOCK.json"))!=binding: raise ValueError("interrupted block changed")
    else: ollama.write_new(output/"BLOCK.json",manifest)
    rows=[];active=None
    # Manifest order is frozen model-major within a complete paired block.
    for unit in manifest["units"]:
        key=digest(unit)[:32];folder=output/"units"/key;receipt_path=folder/"UNIT.json"
        expected=digest({"block":binding,"unit":unit})
        if receipt_path.exists():
            saved=read(receipt_path)
            if (saved["binding"]!=expected or saved["files"]!=inventory(folder/"route")
                    or saved['unit']!=unit or saved['profile']!=asdict(profiles[unit['model']])):
                raise ValueError("saved unit changed")
            from unittest.mock import patch
            def forbidden(*a, **kw): raise ValueError('saved unit replay attempted inference')
            task,row=tasks[unit['task_id']]
            with patch.object(ollama, 'api', forbidden):
                reproduced=dispatch(task,row,unit['arm'],profiles[unit['model']],folder/'route',manifest['training'],ghost_root)
            if reproduced!=saved['result']:
                raise ValueError('saved unit native result does not reproduce')
            rows.append(saved);continue
        if unit["model"]!=active:
            if before_model is not None: before_model(profiles[unit["model"]])
            active=unit["model"]
        task,row=tasks[unit["task_id"]]
        # Existing incomplete attempt directories refuse; never repeat an uncertain request.
        started=time.monotonic()
        result=dispatch(task,row,unit["arm"],profiles[unit["model"]],folder/"route",manifest["training"],ghost_root)
        saved={"binding":expected,"unit":unit,"profile":asdict(profiles[unit["model"]]),
               "result":result,"files":inventory(folder/"route"),"at":ollama.now(),
               "unit_wall_seconds":time.monotonic()-started}
        ollama.write_new(receipt_path,saved);rows.append(saved)
        if stop_after is not None and len(rows)==stop_after:
            raise InterruptedError("constructed interruption between complete units")
    result={"schema":SCHEMA,"at":ollama.now(),"binding":binding,"block_id":manifest["block_id"],
            "node":manifest["node"],"units":len(rows),"status":"COMPLETE",
            "files":inventory(output),"scope":"complete producer; scientific comparison remains unscored"}
    ollama.write_new(complete,result)
    return result
