"""Measured three-world pilot and byte-exact full reuse for frozen V4.c core.

DESIGN CHECK: LESSONS 3-5. Incomplete/changed pilot evidence cannot admit a
full run. Valid retained worlds have identical full-run bindings and are copied
without refitting. This wrapper neither alters inference nor grants admission
on its own: the owner reviews measured whole execute+fresh-replay projection.
"""
from pathlib import Path
import time

from . import menus_v4_split as core
from .menus_io import assert_equal, input_hashes, read, sha256, write

MODES = ("pilot", "full", "fixture_pilot", "fixture_full")


def parse(inputs, config):
    mode=config["mode"]
    if mode not in MODES:
        raise ValueError("unknown split admission mode")
    scientific_config=dict(config,mode="fixture" if mode.startswith("fixture") else "full")
    scientific_inputs={key:inputs[key] for key in core.sources.INPUTS}
    extra=set(inputs)-core.sources.INPUTS
    expected={"pilot_plan","pilot_complete","pilot_summary"} if mode.endswith("full") else set()
    if extra != expected:
        raise ValueError("split admission input roster differs")
    source=core.load(scientific_inputs,scientific_config)
    if not mode.endswith("full"):
        source["worlds"]=[w for w in source["worlds"] if w["cell"]["delta"]==.4 and w["cell"]["replicate"]==0 and not w["cell"]["permuted"]]
    return mode,scientific_inputs,scientific_config,source


def binding(source,config):
    return dict(inputs=source["identity"],config=config,code={str(Path(m.__file__).resolve()):sha256(m.__file__) for m in (core.sources,core.stats,core)})


def pilot(output,source,config):
    bind=binding(source,config)
    if (output/"BINDING.json").exists():assert_equal(read(output/"BINDING.json"),bind)
    else:write(output/"BINDING.json",bind)
    times=[];names=[]
    for world in source["worlds"]:
        name=core.sources.world_name(world["cell"]);names.append(name)
        path=output/"worlds"/(name+".json");seal=path.with_suffix(".seal.json")
        timer=path.with_suffix(".timing.json")
        if seal.exists():
            assert_equal(read(seal),dict(binding=bind,sha256=sha256(path)))
            if read(timer)["world_sha256"] != sha256(path):raise ValueError("pilot timing changed world binding")
            elapsed=read(timer)["seconds"]
        else:
            if (output/"YIELD_REQUEST.json").exists():return dict(status="yielded",completed_worlds=len(times))
            start=time.perf_counter();result=core.one_world(source,world,config);elapsed=time.perf_counter()-start
            write(path,result);write(timer,dict(seconds=elapsed,world_sha256=sha256(path)))
            write(seal,dict(binding=bind,sha256=sha256(path)))
        times.append(elapsed)
    return dict(card="V4.c-pilot",status="complete",execution_only=True,primary=None,scientific_admission=False,
        synthetic_fixture_only=config["mode"]=="fixture",input_hashes=source["identity"],scientific_config=config,
        worlds=names,wall_seconds_by_world=times,
        projected_seconds=2*110*sum(times)/len(times),
        forecast_method="twice mean of three fixed plant worlds times110; includes whole fresh refit, no parallel speedup assumed",
        retained_hashes={p.relative_to(output).as_posix():sha256(p) for p in output.rglob("*") if p.is_file() and p.name not in ("SUMMARY.json","YIELD_REQUEST.json")})


def copy_exclusive(src,dest):
    dest.parent.mkdir(parents=True,exist_ok=True)
    with src.open("rb") as a,dest.open("xb") as b:
        for block in iter(lambda:a.read(1024*1024),b""):b.write(block)


def reuse(output,inputs,source,config):
    plan,complete,summary=(read(inputs[key]) for key in ("pilot_plan","pilot_complete","pilot_summary"))
    root=Path(inputs["pilot_complete"]).parent.resolve();old=Path(inputs["pilot_summary"]).parent.resolve()
    if old != root/"output" or plan["module"] != "runners.drive.cards.menus_v4_split_admitted" or complete.get("status")!="COMPLETE" or not complete.get("fresh_process_verified"):
        raise ValueError("verified V4.c pilot required")
    if plan["config"]["mode"] != ("fixture_pilot" if config["mode"]=="fixture" else "pilot"):
        raise ValueError("pilot/full modes differ")
    if plan["pins"].get(str(Path(__file__).resolve())) != sha256(__file__):
        raise ValueError("pilot/full admission source differs")
    assert_equal(dict(plan["config"],mode=config["mode"]),config)
    for key in ("pilot_plan","pilot_summary"):
        rel=Path(inputs[key]).resolve().relative_to(root).as_posix()
        if complete["outputs"].get(rel)!=sha256(inputs[key]):raise ValueError("pilot completed artifact changed")
    expected=[core.sources.world_name(w["cell"]) for w in source["worlds"] if w["cell"]["delta"]==.4 and w["cell"]["replicate"]==0 and not w["cell"]["permuted"]]
    assert_equal(summary["worlds"],expected);assert_equal(summary["scientific_config"],config)
    assert_equal(summary["input_hashes"],source["identity"])
    assert_equal(read(old/"BINDING.json"),binding(source,config))
    if not summary["execution_only"] or summary["primary"] is not None:
        raise ValueError("not an execution-only pilot")
    for name,digest in summary["retained_hashes"].items():
        path=old/name
        if sha256(path)!=digest or complete["outputs"].get("output/"+name)!=digest:
            raise ValueError("pilot retained checkpoint changed")
    retained=["BINDING.json"]+[f"worlds/{name}{suffix}" for name in expected for suffix in (".json",".seal.json")]
    for name in retained:
        path=output/name
        if path.exists():
            if sha256(path)!=sha256(old/name):raise ValueError("full existing checkpoint differs from pilot")
        else:copy_exclusive(old/name,path)
    receipt=dict(inputs=input_hashes(inputs),copied=retained,byte_exact=True)
    if (output/"PILOT_REUSE.json").exists():assert_equal(read(output/"PILOT_REUSE.json"),receipt)
    else:write(output/"PILOT_REUSE.json",receipt)


def execute(output:Path,inputs:dict,config:dict)->dict:
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    mode,scientific_inputs,scientific_config,source=parse(inputs,config)
    if mode.endswith("full"):
        reuse(output,inputs,source,scientific_config)
        return core.execute(output,scientific_inputs,scientific_config)
    result=pilot(output,source,scientific_config)
    if result["status"]=="yielded":return result
    if (output/"SUMMARY.json").exists():assert_equal(read(output/"SUMMARY.json"),result)
    else:write(output/"SUMMARY.json",result)
    return result


def verify(output:Path,inputs:dict,config:dict)->dict:
    output=Path(output);mode,scientific_inputs,scientific_config,source=parse(inputs,config)
    if mode.endswith("full"):
        reuse(output,inputs,source,scientific_config)
        return core.verify(output,scientific_inputs,scientific_config)
    bind=binding(source,scientific_config);assert_equal(read(output/"BINDING.json"),bind)
    summary=read(output/"SUMMARY.json")
    for name,digest in summary["retained_hashes"].items():
        if sha256(output/name)!=digest:raise ValueError("pilot saved output changed")
    for world in source["worlds"]:
        path=output/"worlds"/(core.sources.world_name(world["cell"])+".json")
        assert_equal(read(path.with_suffix(".seal.json")),dict(binding=bind,sha256=sha256(path)))
        assert_equal(read(path),core.one_world(source,world,scientific_config))
    # The immutable recorded timings are re-aggregated, not measured a second time.
    assert_equal(summary,pilot(output,source,scientific_config))
    return dict(verified=True,card="V4.c-pilot",worlds=len(source["worlds"]),fresh_source_refit=True)
