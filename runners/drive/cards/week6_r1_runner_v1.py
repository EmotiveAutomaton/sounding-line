"""Run and independently replay the prospective R1.i ISEAR study in a counted slot.

DESIGN CHECK (LESSONS 2–5). Freeze structural support before reading questionnaire
items. Both a true and a null association need the same source, whole-person
allocations and independent fits. Preserve unidentified slopes and incomplete
banks; partial work carries no registered verdict.
"""
from pathlib import Path
import hashlib
import shutil
import subprocess
import time

import numpy as np

from runners.stage14.common import atomic, filehash, freeze, now, read
from . import week6_r1_isear_v1 as study

EDITION = "04ffbc24950f4effd85ede4b735f2a16bbec5a3a21262e5d7879e6556ead902e"
BASE_COLUMNS = ("COUN","CITY","SUBJ","EMOT")
BLOCK = 50


def project(database, adapter, mode):
    shell = shutil.which("pwsh.exe")
    if not shell:
        raise RuntimeError("Required read-only Windows projection is unavailable")
    call = subprocess.run([shell,"-NoLogo","-NoProfile","-NonInteractive","-File",str(adapter),
                           "-Database",str(database),"-Projection",mode],capture_output=True,timeout=90)
    if call.returncode:
        # Database-engine diagnostics can name private files. Retain only a fixed error.
        raise RuntimeError(f"Read-only questionnaire {mode} projection failed")
    columns = BASE_COLUMNS if mode=="Roster" else BASE_COLUMNS+tuple(study.DOMAINS)
    values = []
    for line in call.stdout.decode("utf-8-sig").splitlines():
        cells = line.split("\t")
        if len(cells) != len(columns):
            raise ValueError("Unexpected questionnaire projection layout")
        values.append(dict(zip(columns,cells)))
    return values


def preserve(path, value):
    if path.is_file():
        if read(path)!=value:
            raise ValueError("Immutable R1.i record changed")
    else:
        freeze(path,value)


def agrees(left,right):
    if len(left)!=len(right):
        return False
    for a,b in zip(left,right):
        if a is None or b is None:
            if a is not b:
                return False
        elif not np.isclose(a,b,rtol=2e-8,atol=1e-10):
            return False
    return True


def equivalent_block(original, fresh):
    return (original["start"]==fresh["start"] and original["stop"]==fresh["stop"]
            and original["weights_sha256"]==fresh["weights_sha256"]
            and len(original["draws"])==len(fresh["draws"])
            and all(agrees(a,b) for a,b in zip(original["draws"],fresh["draws"])))


def run(output, inputs, config, replay):
    if (set(inputs)!={"database","adapter","adapter_sha256","design","design_sha256"}
            or set(config)!={"draws","seed","max_wall_seconds"}
            or config["draws"]!=study.DRAWS or config["seed"]!=study.SEED
            or not 0<config["max_wall_seconds"]<=21600):
        raise ValueError("Unreviewed R1.i source or draw configuration")
    database, adapter, design = (Path(inputs[k]).resolve() for k in ("database","adapter","design"))
    if filehash(database)!=EDITION or filehash(adapter)!=inputs["adapter_sha256"] or filehash(design)!=inputs["design_sha256"]:
        raise ValueError("R1.i source, read-only projection or prospective design changed")
    base=Path(output)
    original=base/"execute"
    folder=base/("verify" if replay else "execute")
    folder.mkdir(parents=True,exist_ok=True)
    if replay and not (original/"ENGINE_RESULT.json").exists():
        raise ValueError("Complete original result required before replay")
    started=time.monotonic()
    roster,support=study.source_roster(project(database,adapter,"Roster"))
    preserve(folder/"STRUCTURE.json",support)
    if replay and support!=read(original/"STRUCTURE.json"):
        raise ValueError("Structural support differs on fresh projection")
    if support["ambiguous_person_feelings"] or not support["people_union"]:
        status="ambiguous original person key" if support["ambiguous_person_feelings"] else "no identified eligible person"
        result=dict(disposition=status, structural=support, outcomes_read=False)
    else:
        samples, counts=study.prepare(project(database,adapter,"Items"),roster,support)
        preserve(folder/"ANALYTIC_SUPPORT.json",counts)
        if replay and counts!=read(original/"ANALYTIC_SUPPORT.json"):
            raise ValueError("Complete-case support differs on fresh projection")
        people=counts["complete_union"]
        if not people:
            result=dict(disposition="no complete outcome roster",structural=support,analytic=counts)
        else:
            point=study.scores(samples,np.ones(people,dtype=int),replay)
            if replay and not agrees(point,read(original/"ENGINE_RESULT.json")["point"]):
                raise ValueError("Independent point does not reproduce the reported contrasts")
            bank=[]
            for start in range(0,study.DRAWS,BLOCK):
                if time.monotonic()-started>=config["max_wall_seconds"] or any(
                        (base/x).is_file() for x in ("STOP_REQUEST.json","YIELD_REQUEST.json")):
                    return dict(status="yielded", verified=False, completed_draws=len(bank), scientific_result_complete=False)
                target=folder/f"draws-{start:04d}.json"
                if target.is_file():
                    part=read(target)
                else:
                    weights_hash=hashlib.sha256()
                    rows=[]
                    for i in range(start,start+BLOCK):
                        w=study.draw_weights(people,i)
                        weights_hash.update(w.astype("<i8").tobytes())
                        rows.append(study.scores(samples,w,replay))
                    part=dict(start=start,stop=start+BLOCK,weights_sha256=weights_hash.hexdigest(),draws=rows)
                    freeze(target,part)
                if part["start"]!=start or part["stop"]!=start+BLOCK or len(part["draws"])!=BLOCK:
                    raise ValueError("Incomplete saved draw block")
                if replay and not equivalent_block(read(original/target.name),part):
                    raise ValueError("Original and independent R1.i draw banks disagree")
                bank.extend(part["draws"])
                atomic(folder/"DRAW_PROGRESS.json",dict(at=now(),phase=folder.name,completed=len(bank),target=study.DRAWS))
            result=dict(structural=support,analytic=counts,point=point,draws=len(bank),
                        estimates=study.summarize(point,bank,counts),seed=study.SEED,source_sha256=EDITION)
    if filehash(database)!=EDITION or filehash(adapter)!=inputs["adapter_sha256"]:
        raise ValueError("R1.i source changed during projection")
    if replay:
        previous=read(original/"ENGINE_RESULT.json")
        if result.get("disposition")!=previous.get("disposition"):
            raise ValueError("Scientific disposition changed on replay")
        if "estimates" in result:
            for term in study.TERMS:
                a,b=result["estimates"][term],previous["estimates"][term]
                if (a["defined_draws"]!=b["defined_draws"] or not agrees(
                        a["interval"] or [None], b["interval"] or [None])):
                    raise ValueError("Independent uncertainty differs")
            if result["estimates"]["joint_reading"]!=previous["estimates"]["joint_reading"]:
                raise ValueError("Independent decision differs")
    preserve(folder/"ENGINE_RESULT.json",result)
    return dict(status="verified" if replay else "computed",verified=replay,scientific_result_complete=replay,
                output_sha256=filehash(folder/"ENGINE_RESULT.json"))


def execute(output,inputs,config):
    return run(output,inputs,config,False)


def verify(output,inputs,config):
    return run(output,inputs,config,True)
