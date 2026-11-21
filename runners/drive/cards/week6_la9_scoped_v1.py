"""LA9's registered cost fallback, retaining complete meetings and the original solver."""
from collections import Counter
from pathlib import Path
import warnings

import numpy as np
from sklearn.base import clone
from sklearn.exceptions import ConvergenceWarning
from threadpoolctl import threadpool_limits

from . import week6_la9_pooled_fit_v1 as original
from .batch_runtime import filehash, freeze, read
from .week5_at_scope import select


def roster(metadata):
    size = len(metadata)//4
    if size < 1:
        raise ValueError("Too few source meetings for the frozen scope")
    return select({meeting: {meeting: row["corpus"]} for meeting, row in metadata.items()}, size)


def subset_fit(rows, support, selected):
    """Retain parent scales, category order, column coding and fold assignments."""
    population = original.state_for_fit(rows, support)
    if population is None:
        raise ValueError("Original matched population empty")
    mask = np.array([row["meeting"] in selected for row in rows])
    subset = [row for row, keep in zip(rows, mask) if keep]
    by_id = {(r["meeting"],r["id"]):r["act_type"] for r in subset}
    counts = Counter(by_id.values())
    scoped_support = {tag:dict(distinct_utterances=counts[tag],eligible=counts[tag]>=50) for tag in support}
    unassigned = sum(n for key,n in counts.items() if key.startswith("unmapped/"))
    if not subset:
        return None,scoped_support,unassigned
    keys = sorted({row["meeting"] for row in subset})
    number = {meeting:i for i,meeting in enumerate(keys)}
    folds = original.fixed_folds(r["meeting"] for r in rows)
    y = population["y"][mask]
    if set(y) != {0,1}:
        raise ValueError("Unauthenticated paired rows")
    arms = {}
    for arm,(base, matrix, offset) in population["arms"].items():
        x = matrix[mask]
        with threadpool_limits(limits=2), warnings.catch_warnings():
            warnings.simplefilter("error",ConvergenceWarning)
            fitted = clone(base).fit(x,y)
        arms[arm] = fitted,x,offset
    state = dict(population, group=np.array([number[row["meeting"]] for row in subset]),meetings=len(keys),
                 fold_counts=[sum(folds[meeting]==i for meeting in keys) for i in sorted(set(folds.values()))],
                 y=y,arms=arms,term=population["term"][mask],
                 eligible={tag:population["categories"].index(tag) for tag, value in scoped_support.items() if value["eligible"]})
    return state,scoped_support,unassigned


def operation(output, inputs, config):
    if config.get("phase")!="LA9" or config.get("draws")!=2000 or config.get("max_new_draws") not in (100,2000):
        raise ValueError("Unregistered pooled meeting scope")
    output = Path(output)
    output.mkdir(parents=True,exist_ok=True)
    proof = Path(inputs["scope_decision"])
    if filehash(proof)!=inputs["scope_sha256"] or not read(proof)["full_write_through"]:
        raise ValueError("Filed cost and equivalence dispositions required")
    src = inputs["original"]
    root = Path(src["original_preparation"])
    if filehash(root/"COMPLETE.json")!=src["original_complete_sha256"]:
        raise ValueError("Original paired source changed")
    raw = Path(read(root/"PLAN.json")["inputs"]["source_root"])
    meta = raw/"output/METADATA.json.gz"
    if filehash(meta)!=read(raw/"COMPLETE.json")["outputs"]["output/METADATA.json.gz"]:
        raise ValueError("Original metadata changed")
    metadata = original.timing_p6.gzread(meta)
    selected, allocation = roster(metadata)
    scope=dict(population=len(metadata),selected=len(selected),seed=20261102,allocation=allocation,
               roster_sha256=original.source.digest(sorted(selected)),metadata_sha256=filehash(meta))
    scope_path=output/"SCOPE.json"
    if scope_path.exists():
        if read(scope_path)!=scope:raise ValueError("Scope record differs")
    else:
        freeze(scope_path,scope)
    rows,support,_,identity=original.load(src)
    selected_set = set(selected)
    state, support, unassigned = subset_fit(rows,support,selected_set)
    binding = original.source.digest(dict(scope=scope,source=identity,worker=filehash(__file__),
                                          original_fit=filehash(original.__file__)))
    point=original.coefficients(state) if state is not None else None
    bank=[]
    new=0
    if state is not None:
        for index in range(2000):
            path=output/"draws"/f"{index:04d}.json"
            if path.exists() and path.with_suffix(".seal.json").exists():
                data=original.stored(path)
            else:
                if new>=config["max_new_draws"] or (output/"YIELD_REQUEST.json").exists() or (output.parent/"YIELD_REQUEST.json").exists():
                    return dict(status="yielded",completed=index,total=2000)
                data=dict(binding=binding,index=index,value=original.coefficients(state,index))
                original.seal.checkpoint(path,data)
                new+=1
            if data["binding"]!=binding or data["index"]!=index:raise ValueError("Scoped draw identity differs")
            bank.append(data["value"])
    result=original.assemble(state,support,unassigned,point,bank)
    result.update(card="LA9",scope=scope,source_identity=identity,complete_computation=True,
                  matched_rows=sum(row["meeting"] in selected_set for row in rows))
    original.io.write_json(output/"RESULT.json",result)
    return result


def execute(output,inputs,config):
    return operation(output,inputs,config)


def verify(output,inputs,config):
    output=Path(output)
    replay=output/"independent-replay"
    result=operation(replay,inputs,config)
    if result.get("status")=="yielded":
        return result
    original.compare.compare_record(read(output/"RESULT.json"),result)
    for i in range(result["draws"]):
        name=Path("draws")/f"{i:04d}.json"
        original.compare.compare_record(original.stored(output/name),original.stored(replay/name))
    return dict(verified=True,draws=result["draws"],scope=result["scope"])
