"""CA2 opposite-half kernel timing, without recurrence or held-out scores.

DESIGN CHECK: LESSONS 3-5. A sparse 10% sample cannot stand in for the frozen
people. Record its support and scale measured kernels to the full half, with
all 1000 references and fresh replay. Unmeasurable costs refuse projection.
No scientific cohort, recurrence, prototype, identification or AUC is emitted.
"""
from pathlib import Path
import time

import numpy as np
from threadpoolctl import threadpool_limits

from . import week3_alignment_stats as stats
from .week3_alignment_features import bind, source
from .menus_io import assert_equal, input_hashes, read, write, sha256


def run(output, inputs, config, verifying=False):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    if set(inputs) != {"prepared_summary", "prepared_complete", "features_summary", "features_complete"} or set(config)-{"fixture"}:
        raise ValueError("exact CA2 timing inputs/config required")
    fixture = bool(config.get("fixture", False))
    _, _, all_rows, _ = source(inputs); feature, root = bind(inputs, "features")
    if feature.get("card") != "CA1-features" or (not fixture and feature.get("mode") != "pilot"):
        raise ValueError("complete ten-percent feature pilot required")
    if feature["input_hashes"]["prepared_summary"] != sha256(inputs["prepared_summary"]):
        raise ValueError("timing source/feature binding differs")
    for name, expected in feature["output_hashes"].items():
        if sha256(root/name) != expected: raise ValueError("feature bytes changed")
    index = read(root/"INDEX.json"); selected = index["comparison_indices"]
    if not fixture and len(selected) != int(np.ceil(.1*len(all_rows))):
        raise ValueError("timing sample differs from frozen ten percent")
    rows = [all_rows[i] for i in selected]
    train = np.asarray([r["half"] == 1 for r in rows])
    full_train = [r for r in all_rows if r["half"] == 1]
    if not train.any() or not full_train: raise ValueError("opposite-half fit support absent")
    choices = np.asarray([r["choice"] for r in rows], int)
    countries, owners = np.asarray([r["country"] for r in rows]), np.asarray([r["writer"] for r in rows])
    full_people = sorted({r["writer"] for r in all_rows})
    times = {}; began = time.process_time()
    with threadpool_limits(limits=2):
        x, _ = stats.candidate_features(rows, np.load(root/"EMBEDDINGS.npy", allow_pickle=False), index["text_indices"])
    times["candidate_pca_cpu_seconds"] = time.process_time()-began
    began = time.process_time()
    with threadpool_limits(limits=2): population = stats.fit(x[train], choices[train], penalty=1.)
    times["population_cpu_seconds"] = time.process_time()-began
    fits = {}; began = time.process_time()
    for country in sorted(set(countries)):
        ix = train & (countries == country)
        if ix.any():
            with threadpool_limits(limits=2): fits[country] = stats.fit(x[ix], choices[ix], prior=population, penalty=10.)
    times["country_cpu_seconds"] = time.process_time()-began
    people = []; began = time.process_time()
    for person in full_people:
        ix = train & (owners == person)
        if not ix.any(): continue
        country = rows[int(np.flatnonzero(ix)[0])]["country"]
        with threadpool_limits(limits=2): stats.fit(x[ix], choices[ix], prior=fits[country], penalty=10.)
        people.append(person)
    times["individual_cpu_seconds"] = time.process_time()-began
    if not people or (not fixture and min(times[k] for k in ("population_cpu_seconds", "country_cpu_seconds", "individual_cpu_seconds")) <= 0):
        raise ValueError("opposite-half kernel cost not measurable")
    comparison_ratio = len(full_train)/int(train.sum())
    person_ratio = max(comparison_ratio, len(full_people)/len(people))
    projection = 2*(comparison_ratio*(times["population_cpu_seconds"]+times["country_cpu_seconds"])+person_ratio*times["individual_cpu_seconds"])
    report = {"card":"CA2-timing", "state":"timing_only", "scientific_inference":False,
              "input_hashes":input_hashes(inputs), "fixture":fixture, "train_half":1,
              "comparisons_sampled":len(rows), "comparisons_full":len(all_rows),
              "training_rows_sampled":int(train.sum()), "training_rows_full":len(full_train),
              "fixed_annotators_full":len(full_people), "sampled_annotators_with_training":len(people),
              "sampled_countries_with_training":len(fits),
              "whole_cohort_and_full_reference_bank_required":True,
              "missing_dependencies":["complete full CA1 feature table", "complete freshly verified CA1 and all 1000 first-half references"],
              "scope":"Kernel timing only, no recurrence, held-out score, decomposition, or selected-population inference"}
    if verifying: assert_equal(report, read(output/"SUMMARY.json"))
    else:
        write(output/"SUMMARY.json", report)
        write(output/"TIMING.json", times|{"engineering_margin":2,
              "one_opposite_half_full_fit_projection_cpu_seconds":projection,
              "all_1000_references_real_and_fresh_replay_projection_cpu_seconds":projection*1001*2,
              "original_CA2_cpu_cap_seconds":3600,
              "excluded_costs":"prior CA2 work, complete source and authenticated CA1 bank reads, full candidate PCA, full assignment/split reconstruction, summary/bootstrap and native startup; owner adds all charges",
              "projection_limit":"frozen twofold linear extrapolation margin, not a measured complexity guarantee; no controls or population may be reduced"})
    return report


def execute(output, inputs, config): return run(output, inputs, config)
def verify(output, inputs, config):
    run(output, inputs, config, True)
    return {"verified":True, "fresh_opposite_half_kernels_no_scientific_score":True}
