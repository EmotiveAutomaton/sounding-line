"""Canonical-source rank-only D12 successor commissioned October18.

DESIGN CHECK: LESSONS3-5, original D12 and its source-validity audit read.
Canonical unique insertion determines selection; logged index and prepared
inserted text are provenance only. Midranks survive increasing transforms of
the raw score; missing/all-tied/single-option menus are explicitly unsupported.
Known positive/reverse/constant controls validate correlation and graph pairing.
Invalid source identities refuse before any statistic. Original D12 stays held.
"""
from collections import Counter
import hashlib
import math
from pathlib import Path
import time

import numpy as np
from scipy.stats import rankdata

from . import menus_d12 as original
from . import menus_canonical_selection as canonical
from . import menus_d12_rank_stats as stats
from . import states_v2 as states
from .menus_io import read,write,sha256,input_hashes,assert_equal

CONFIG=dict(seed=20261018,bootstrap=2000,permutations=200,
            minimum_writers=4,maximum_undefined_fraction=.05)
INPUTS={"sessions","p8","p8_complete","selection_reader","selection_complete"}


def load(inputs,config):
    if set(inputs)!=INPUTS or config!=CONFIG:
        raise ValueError("D12 rank source/config differs from frozen contract")
    audit=canonical.load(inputs)
    sessions,producer=original.load(inputs)
    writers,by_key=original.prepare(sessions,producer)
    return audit,writers,by_key


def writer_rows(writer,sessions,by_key,audit,seed):
    rows=[];exclusions=Counter();source_census=Counter()
    for ordinal,session in enumerate(sessions):
        for row in sorted(session["rows"],key=lambda r:(r["ordinal"],r["key"])):
            options=sorted(by_key[row["key"]],key=lambda p:p["position"])
            proof,chosen=canonical.join(audit,row,options)
            source_census[proof["index_status"]]+=1
            result=dict(key=row["key"],writer=writer,session=session["session"],session_ordinal=ordinal,
                half=ordinal%2,handling=row["handling"],accepted=int(row["handling"]=="accept"),selected=False,
                canonical_choice_changed=proof["index_status"]=="proven_disjoint_choice",
                canonical_source_sha256=proof["canonical_sha256"],raw_source_sha256=proof["raw_source_sha256"])
            if chosen is None:exclusions["no_observed_selection"]+=1
            elif len(options)<2:exclusions["single_option"]+=1
            elif any(p["logged_score"] is None for p in options):exclusions["menu_has_missing_score"]+=1
            else:
                values=np.asarray([p["logged_score"] for p in options],float)
                if values.max()==values.min():exclusions["all_tied_score_menu"]+=1
                else:
                    rank=rankdata(values,method="average");centered=(rank-1)/(len(rank)-1)-.5
                    rng=np.random.default_rng(int.from_bytes(hashlib.sha256(f'{seed}:{row["key"]}'.encode()).digest()[:8],"little"))
                    uniform=int(rng.integers(len(values)))
                    result.update(selected=True,size=len(values),chosen=chosen,option_id=proof["canonical_option_ids"][chosen],
                        prepared_positions=proof["prepared_positions"],raw_scores=values.tolist(),midranks=rank.tolist(),
                        centered_rank=float(centered[chosen]),uniform_rank=float(centered[uniform]),uniform_choice=uniform,
                        favorite=bool(values[chosen]==values.max()),least=bool(values[chosen]==values.min()),
                        favorite_tied=bool(np.sum(values==values.max())>1),least_tied=bool(np.sum(values==values.min())>1))
            rows.append(result)
    return dict(writer=writer,rows=rows,exclusions=dict(exclusions),source_census=dict(source_census))


def summarize(units,identity):
    census=Counter()
    for unit in units:census.update(unit["source_census"])
    return dict(card="D12-rank-canonical",descriptive=True,scientific_admission=False,input_hashes=identity,
        config=CONFIG,extension_computed=False,original_D12_unchanged_and_held=True,
        source_census=dict(census),**stats.summarize(units,CONFIG))


def execute(output:Path,inputs:dict,config:dict)->dict:
    output=Path(output);output.mkdir(parents=True,exist_ok=True);start=time.perf_counter()
    audit,writers,by_key=load(inputs,config);identity=input_hashes(inputs)
    binding=dict(inputs=identity,config=config)
    if (output/"BINDING.json").exists():assert_equal(read(output/"BINDING.json"),binding)
    else:write(output/"BINDING.json",binding)
    units=[];hashes={}
    for number,(writer,group) in enumerate(writers.items(),1):
        path=output/"writers"/(hashlib.sha256(writer.encode()).hexdigest()[:24]+".json");seal=path.with_suffix(".seal.json")
        if seal.exists():
            assert_equal(read(seal),dict(binding=binding,sha256=sha256(path)));unit=read(path)
        else:
            if (output/"YIELD_REQUEST.json").exists():return dict(status="yielded",completed_writers=len(units))
            unit=writer_rows(writer,group,by_key,audit,config["seed"]);write(path,unit)
            write(seal,dict(binding=binding,sha256=sha256(path)))
        units.append(unit);hashes[path.relative_to(output).as_posix()]=sha256(path)
        if number>=max(1,math.ceil(.1*len(writers))) and not (output/"FIRST_TENTH.json").exists():
            write(output/"FIRST_TENTH.json",dict(completed_writers=number,total_writers=len(writers),
                projected_seconds=2*(time.perf_counter()-start)*len(writers)/number,
                method="source extraction doubled for fresh replay;200 paired graph bootstraps extra, included in owner full forecast"))
    report=summarize(units,identity);report["writer_hashes"]=hashes
    if (output/"SUMMARY.json").exists():assert_equal(read(output/"SUMMARY.json"),report)
    else:write(output/"SUMMARY.json",report)
    return report


def verify(output:Path,inputs:dict,config:dict)->dict:
    output=Path(output);audit,writers,by_key=load(inputs,config);identity=input_hashes(inputs)
    binding=dict(inputs=identity,config=config);assert_equal(read(output/"BINDING.json"),binding)
    report=read(output/"SUMMARY.json");units=[];hashes={}
    for writer,group in writers.items():
        path=output/"writers"/(hashlib.sha256(writer.encode()).hexdigest()[:24]+".json")
        assert_equal(read(path.with_suffix(".seal.json")),dict(binding=binding,sha256=sha256(path)))
        actual=writer_rows(writer,group,by_key,audit,config["seed"]);assert_equal(read(path),actual);units.append(actual)
        hashes[path.relative_to(output).as_posix()]=sha256(path)
    actual=summarize(units,identity);actual["writer_hashes"]=hashes;assert_equal(report,actual)
    return dict(verified=True,primary_recomputed=actual["primary"],canonical_source_replayed=True,
                paired_fake_recomputed=actual["own_minus_fake"])
