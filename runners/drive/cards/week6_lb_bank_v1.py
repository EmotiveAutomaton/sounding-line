"""Checkpointed whole-person banks for newly admitted lattice diary members.

DESIGN CHECK (LESSONS 3–5). The frozen source and member-specific seed pair
the same person multiplicities across that source's rows. A complete replay
compares every point, ordered draw and support count. A partial block saved
at a native yield is resumed without changing its draw indices.
"""
import json
import time
from pathlib import Path

import numpy as np

from .batch_runtime import freeze, read
from .week6_lattice_diary_v1 import person_draw
from .week6_ld_draws_v1 import CHUNK, DRAWS, RequestedYield, _values, compare, load_blocks, summarize


def run(directory, producer, data, *, member, source_digest, seed, guard, verify,
        execute_dir, limit, progress):
    if (type(seed) is not int or seed<=0 or not 1<=limit<=DRAWS or data.people<2
            or len(source_digest)!=64 or any(c not in "0123456789abcdef" for c in source_digest)):
        raise ValueError("Unreviewed source, draw bound or roster")
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=True)
    keys=sorted(data.specs)
    point=_values(producer.evaluate(data,None,guard,verify=verify),keys)
    schema=dict(member=member,source_seed=seed,source_sha256=source_digest,keys=keys,
                specs=data.specs,metadata=data.metadata,people=data.people,draws=DRAWS,
                resampling="all-source-person multiplicities, same draw id across cards")
    schema=json.loads(json.dumps(schema,allow_nan=False))
    for name,record in (("SCHEMA.json",schema),("POINT.json",point)):
        destination=directory/name
        if not destination.exists():
            freeze(destination,record)
        elif name=="POINT.json":
            compare(read(destination),record)
        elif read(destination)!=record:
            raise ValueError("LB diary checkpoint schema changed")
    rows=load_blocks(directory,keys)
    baseline=None
    if verify:
        if read(execute_dir/"SCHEMA.json")!=schema:
            raise ValueError("LB diary original and replay support differ")
        compare(read(execute_dir/"POINT.json"),point)
        baseline=load_blocks(execute_dir,keys)
        if len(baseline)!=DRAWS:
            raise ValueError("Cannot replay an incomplete original bank")
        for draw,existing in enumerate(rows):
            compare(baseline[draw],existing)
    stop=min(DRAWS,len(rows)+limit)
    units=np.arange(data.people)
    started=time.monotonic()
    while len(rows)<stop:
        first=len(rows)
        block=[]
        try:
            for i in range(first,min(first+CHUNK,stop)):
                guard()
                weights=person_draw(units,source_seed=seed,draw=i)
                value=_values(producer.evaluate(data,weights,guard,verify=verify),keys)
                if baseline is not None:
                    compare(baseline[i],value)
                block.append(value)
        finally:
            if block:
                freeze(directory/f"draws-{first:04d}.json",dict(start=first,values=block))
                rows.extend(block)
                progress(len(rows),time.monotonic()-started)
    if len(rows)<DRAWS:
        raise RequestedYield("draw quantum")
    return dict(status="complete",member=member,verified=verify,replay_compared_every_cell=verify,
                metrics=summarize(keys,data.specs,point,rows),support=data.metadata,
                source_seed=seed,draws=DRAWS)
