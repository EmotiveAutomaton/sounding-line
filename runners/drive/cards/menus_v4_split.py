"""V4.c corrected split existence test, separate from immutable original V4.

DESIGN CHECK: LESSONS 3-5 and October18 errata read. Null false alarms above
the original V4 bands force a blind label, regardless of planted power. A
calibrated reader with >=80% recovery at .4 sees that representation; at .8
only it sees large effects only; otherwise blind. No finite-grid reference
or bootstrap may rewrite the gate after observing its result. Exact original
110-world roster is required for a scientific summary. Synthetic fixture mode
cannot produce a primary or scientific admission. Full recalculation verifies
the primary from authenticated constructions, not just retained fit numbers.

Curator authorization relayed October18: "Build the corrected split test."
Learned choices/nuisance use A only; histories are separate within halves;
nonnegative variance components are estimated on B; swap and average. The
independent-between-halves Gaussian reference is an explicit approximation.
"""
from __future__ import annotations

import math
import time
from pathlib import Path

import numpy as np

from . import states_v2 as states
from . import menus_v4_saved_diagnostics as sources
from . import menus_v4_split_stats as stats
from .menus_io import assert_equal, read, sha256, write

CONFIG = dict(mode="full", seed=20261018, optimizer_maxiter=100,
              reference_draws=20000, bootstrap_draws=2000)
FIXTURE_CONFIG = dict(CONFIG, mode="fixture", reference_draws=2000)


def load(inputs, config):
    if config not in (CONFIG, FIXTURE_CONFIG):
        raise ValueError("V4.c split configuration differs from frozen design")
    source = sources.load(inputs, dict(bootstrap_draws=2000, bootstrap_seed=20261017))
    if config["mode"] == "fixture":
        if not source["complete"].get("synthetic_fixture_only") or not source["plan"].get("synthetic_fixture_only"):
            raise ValueError("fixture mode forbidden for corpus sources")
        source["worlds"] = [w for w in source["worlds"] if sources.world_name(w["cell"]) == "taste_matched-0.4-0"]
    return source


def one_world(source, world, config):
    construction, saved = sources.load_world(source, world)
    rows = sources.rebuild(source["sessions"], construction, source["plan"]["config"]["seed"])
    world_index = sources.roster().index(world["cell"])
    result = stats.split_world(rows, source["sessions"], saved, source["geometry"], source["base"],
        config["seed"] + 1000*world_index, config["optimizer_maxiter"], config["reference_draws"])
    result["cell"] = world["cell"]
    return result


def wilson(k, n):
    if n < 1 or not 0 <= k <= n:
        raise ValueError("invalid calibration count")
    z = 1.959963984540054; p = k/n; divisor=1+z*z/n
    center=(p+z*z/(2*n))/divisor; radius=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/divisor
    return [float(center-radius),float(center+radius)]


def recovery(worlds, reader):
    count=sum(w["readers"][reader]["detected"] for w in worlds); n=len(worlds)
    return dict(detected=count,worlds=n,rate=count/n,wilson95=wilson(count,n))


def label(zero, medium, large, shuffled):
    if zero > .1 or shuffled > .1:
        return "blind"
    if medium >= .8:
        return "sees"
    if large >= .8:
        return "sees_large_only"
    return "blind"


def difference(medium, zero, seed, draws, valid):
    a=np.asarray(medium,float); b=np.asarray(zero,float)
    rng=np.random.default_rng(seed)
    estimates=a[rng.integers(len(a),size=(draws,len(a)))].mean(1)-b[rng.integers(len(b),size=(draws,len(b)))].mean(1)
    effect=float(a.mean()-b.mean()); ci=np.quantile(estimates,[.025,.975]).tolist(); se=float(estimates.std(ddof=1))
    p=math.erfc(abs(effect)/se/math.sqrt(2)) if se else float(effect==0.)
    return dict(estimate=effect,interval95=ci,standard_error=se,approximate_two_sided_wald_p=p,
        state=states.contrast_state(effect,*ci,valid=valid), bootstrap_draws=draws,seed=seed,
        valid_under_null_calibration=valid,
        method="independent constructed-world bootstrap within matched .4 and zero cells; conditional on retained real-data design")


def summary(source, worlds, config):
    common=dict(card="V4.c",status="complete",input_hashes=source["identity"],config=config,
        original_V4_unchanged=True,world_count=len(worlds),extension=None,
        curator_decision=dict(date="2026-10-18",verbatim="Build the corrected split test."),
        method=dict(split="alternate decisions sorted by open time/key within each session",
            population="original B-pop class-frequency pseudocount +1; only learning-half decisions in strictly earlier completed sessions",
            choices="original chronological train/calibration masks restricted to learning half; K in {2,4}, decay in {.5,.8,.95}; minimum calibration half-Brier, lexical name breaks ties",
            scaling="learning-half chronological training mean/SD only; original <1e-10 constant convention",
            history="separate causal outcome stream for each half; original frozen whole-writer baseline center",
            testing="full original eligible roster in opposite half; only nonnegative variance components estimated there; exact original Laplace objective/tolerances",
            statistic="mean of two swapped marginal-likelihood ratio statistics",
            reference="correlated Gaussian variance-score cone within half; independent draws between halves approximate shared-world cross-fit dependence",
            validity="original null bands decisive; no reference tuning after outcomes"))
    if config["mode"] == "fixture":
        return dict(common,synthetic_fixture_only=True,primary=None,scientific_admission=False,
                    fixture_readers=worlds[0]["readers"])
    if len(worlds)!=110 or {sources.world_name(w["cell"]) for w in worlds}!={sources.world_name(c) for c in sources.roster()}:
        raise ValueError("incomplete V4.c scientific roster")
    null=[w for w in worlds if w["cell"]["permuted"]]; curves={}; labels={}
    for reader in stats.READERS:
        curves[reader]={}; labels[reader]={}; size=recovery(null,reader)
        for plant in sources.PLANTS:
            cells={str(d):recovery([w for w in worlds if not w["cell"]["permuted"] and w["cell"]["plant"]==plant and w["cell"]["delta"]==d],reader) for d in sources.SIZES}
            curves[reader][plant]=dict(cells=cells,shuffled_null=size)
            labels[reader][plant]=label(cells["0.0"]["rate"],cells["0.4"]["rate"],cells["0.8"]["rate"],size["rate"])
    selected=curves["R-both"]["taste_matched"]
    valid=selected["cells"]["0.0"]["rate"]<=.1 and selected["shuffled_null"]["rate"]<=.1
    pick=lambda d:[w["readers"]["R-both"]["detected"] for w in worlds if not w["cell"]["permuted"] and w["cell"]["plant"]=="taste_matched" and w["cell"]["delta"]==d]
    primary=difference(pick(.4),pick(0.),config["seed"],config["bootstrap_draws"],valid)
    return dict(common,primary=primary,curves=curves,labels=labels,scientific_admission=False,
        calibrated_matched_coordinate_reader=labels["R-both"]["taste_matched"]=="sees",
        control_scope="exact stipulated 30 zero-effect and20 saved shuffled worlds; no optional199-world whole-pipeline Monte Carlo step run",
        limits=["Constructed outcomes on an exposed real-data design; no real human taste result.",
                "The original 1/10 and2/20 null bands are retained; Wilson intervals disclose their coarse uncertainty.",
                "Chi-bar reference uses fixed-design information; learned cross-fit directions and causal history make exact joint size unknown before the saved null check.",
                "Original V4 label and any prior scientific route are not rewritten by this separate card."])


def execute(output:Path,inputs:dict,config:dict)->dict:
    output=Path(output);output.mkdir(parents=True,exist_ok=True);source=load(inputs,config)
    binding=dict(inputs=source["identity"],config=config,code={str(Path(m.__file__).resolve()):sha256(m.__file__) for m in (sources,stats)})
    binding["code"][str(Path(__file__).resolve())]=sha256(__file__)
    if (output/"BINDING.json").exists():assert_equal(read(output/"BINDING.json"),binding)
    else:write(output/"BINDING.json",binding)
    results=[];started=time.perf_counter();computed=0
    for world in source["worlds"]:
        path=output/"worlds"/(sources.world_name(world["cell"])+".json");seal=path.with_suffix(".seal.json")
        if seal.exists():
            assert_equal(read(seal),dict(binding=binding,sha256=sha256(path))); result=read(path)
        else:
            if (output/"YIELD_REQUEST.json").exists():return dict(status="yielded",completed_worlds=len(results))
            result=one_world(source,world,config);write(path,result);write(seal,dict(binding=binding,sha256=sha256(path)));computed+=1
        results.append(result)
        if computed>=11 and not (output/"FIRST_TENTH.json").exists():
            write(output/"FIRST_TENTH.json",dict(computed_worlds=computed,projected_seconds=2*len(source["worlds"])*(time.perf_counter()-started)/computed,
                includes_fresh_replay=True,method="twice measured mean world cost for execute plus independent complete refit"))
    report=summary(source,results,config)
    if (output/"SUMMARY.json").exists():assert_equal(read(output/"SUMMARY.json"),report)
    else:write(output/"SUMMARY.json",report)
    return report


def verify(output:Path,inputs:dict,config:dict)->dict:
    output=Path(output);source=load(inputs,config);results=[]
    binding=dict(inputs=source["identity"],config=config,code={str(Path(m.__file__).resolve()):sha256(m.__file__) for m in (sources,stats)})
    binding["code"][str(Path(__file__).resolve())]=sha256(__file__)
    assert_equal(read(output/"BINDING.json"),binding)
    for world in source["worlds"]:
        path=output/"worlds"/(sources.world_name(world["cell"])+".json")
        assert_equal(read(path.with_suffix(".seal.json")),dict(binding=binding,sha256=sha256(path)))
        actual=one_world(source,world,config);assert_equal(read(path),actual);results.append(actual)
    assert_equal(read(output/"SUMMARY.json"),summary(source,results,config))
    return dict(verified=True,card="V4.c",worlds=len(results),full_fresh_source_refit=True)
