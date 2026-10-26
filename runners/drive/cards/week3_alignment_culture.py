"""CA2: disjoint-half personal directions beyond the fitted country direction.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-7. Common country directions alone
must not create personal deviation. Stable personal deviations recur and
reversed deviations reverse. Zero vectors contribute zero, not a lost person.
The real-minus-reassignment interval and permutation probability jointly gate
positive recurrence; unsupported assignments invalidate, never redraw/drop.
CA1's already verified first-half fits are authenticated; every second-half
fit is new and independently rebuilt in verification under identical controls.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import time

import numpy as np
from threadpoolctl import threadpool_limits

from . import week3_alignment_stats as stats
from .week3_alignment_features import bind, source
from .batch_runtime import atomic
from .menus_io import assert_equal, input_hashes, read, write, sha256

SEED = 20261026
INPUTS = {"prepared_summary", "prepared_complete", "features_summary", "features_complete", "ca1_summary", "ca1_complete"}


def fit_half(rows, x, assigned, people, half=1):
    halves, owners, support = stats.fixed_halves(rows, assigned, people, SEED)
    train = halves == half
    choices = np.asarray([r["choice"] for r in rows], int)
    countries = np.asarray([r["country"] for r in rows])
    population = stats.fit(x[train], choices[train], penalty=1.)
    country_fits = {}
    for country in sorted(set(countries)):
        ix = train & (countries == country)
        country_fits[country] = stats.fit(x[ix], choices[ix], prior=population, penalty=10.)
    profiles = {}
    for person in people:
        ix = train & (owners == person)
        country = support[person]["country"]; baseline = country_fits[country]
        individual = stats.fit(x[ix], choices[ix], prior=baseline, penalty=10.)
        profiles[person] = {"individual": individual.tolist(), "country": baseline.tolist(),
                            "support": support[person], "train_comparisons": int(ix.sum())}
    return {"profiles": profiles, "population": population.tolist(),
            "country": {k:v.tolist() for k,v in country_fits.items()}, "train_half": half, "split_rebuilt": True}


def paired(first, second, people):
    if sorted(first["profiles"]) != people or sorted(second["profiles"]) != people:
        raise ValueError("paired fixed annotator population differs")
    if first["train_half"] != 0 or second["train_half"] != 1:
        raise ValueError("paired directions must use opposite frozen halves")
    all_directions, deviations, countries = [], [], []
    for person in people:
        a, b = first["profiles"][person], second["profiles"][person]
        if a["support"] != b["support"]:
            raise ValueError("paired connected-component split differs")
        countries.append(a["support"]["country"])
        individual = np.asarray([a["individual"], b["individual"]], float)
        country = np.asarray([a["country"], b["country"]], float)
        if individual.shape != country.shape or individual.ndim != 2 or not np.isfinite(individual).all() or not np.isfinite(country).all():
            raise ValueError("invalid fitted directions")
        all_directions.append(individual); deviations.append(individual-country)
    return np.asarray(deviations), np.asarray(all_directions), countries


def cosines(deviations):
    deviations = np.asarray(deviations, float)
    denominator = np.linalg.norm(deviations[:, 0], axis=1) * np.linalg.norm(deviations[:, 1], axis=1)
    numerator = np.einsum("nd,nd->n", deviations[:, 0], deviations[:, 1])
    return np.divide(numerator, denominator, out=np.zeros(len(deviations)), where=denominator > 1e-14), denominator <= 1e-14


def decompose(directions, countries):
    """Orthogonal descriptive decomposition; halves are repeated estimates."""
    values = np.asarray(directions, float)
    if values.ndim != 3 or values.shape[1] != 2 or values.shape[0] != len(countries):
        raise ValueError("paired direction dimensions differ")
    grand = values.mean(axis=(0, 1)); person = values.mean(axis=1)
    group_means = {c:person[np.asarray(countries) == c].mean(axis=0) for c in sorted(set(countries))}
    group = np.asarray([group_means[c] for c in countries])
    components = {"country": float(2 * np.sum((group-grand)**2)),
                  "annotator_within_country": float(2 * np.sum((person-group)**2)),
                  "half_within_annotator_disagreement": float(np.sum((values-person[:, None])**2))}
    total = float(np.sum((values-grand)**2))
    if not np.isclose(sum(components.values()), total, atol=1e-9, rtol=1e-9):
        raise ValueError("paired direction decomposition does not close")
    return {"sum_squares": components, "total_sum_squares": total,
            "shares": {k:v/total if total > 1e-14 else 0. for k,v in components.items()},
            "definition": "country means of fitted individual directions, person means within country, and residual half disagreement; equal person and half weights",
            "limitation": "Descriptive fitted-direction variation; the residual mixes estimation noise and split-specific variation, not pure psychological residual."}


def summarize(real, references, draws=2000):
    real, null = np.asarray(real, float), np.asarray(references, float)
    if len(real) < 4:
        return {"state": "unsupported", "reason": "fewer than four fixed annotators", "annotators": len(real)}
    if null.ndim != 2 or null.shape[1] != len(real) or len(null) < 1:
        raise ValueError("complete reference population required")
    delta = real-null.mean(axis=0); delta[np.abs(delta) < 1e-14] = 0.
    samples = np.random.default_rng(SEED+10001).integers(0, len(real), size=(draws, len(real)))
    interval = np.quantile(delta[samples].mean(axis=1), [.025, .975]).tolist()
    observed, effect = float(real.mean()), float(delta.mean())
    null_means = null.mean(axis=1)
    p = float((1+np.sum(null_means >= observed-1e-14))/(len(null)+1))
    state = "positive" if interval[0] > 0 and p < .05 else "negative" if interval[1] < 0 else "marginal" if effect > 0 else "null"
    if interval[0] > 0 and p >= .05: state = "unresolved"
    return {"state": state, "annotators": len(real), "mean_personal_deviation_cosine": observed,
            "real_minus_permutation_mean": effect, "paired_annotator_95_interval": interval,
            "permutation_mean": float(null_means.mean()), "permutation_95_interval": np.quantile(null_means, [.025, .975]).tolist(),
            "permutation_p_one_sided": p, "permutation_draws": len(null), "bootstrap_draws": draws,
            "null_wording": "not detected; sensitivity untested" if state == "null" else None}


def load(inputs, config):
    if set(inputs) != INPUTS or set(config)-{"fixture", "permutation_draws", "bootstrap_draws"}:
        raise ValueError("exact CA2 source/config contract required")
    count, draws = int(config.get("permutation_draws", 1000)), int(config.get("bootstrap_draws", 2000))
    fixture = config.get("fixture", False)
    if count < 1 or draws < 2 or (not fixture and (count != 1000 or draws != 2000)):
        raise ValueError("full CA2 requires exactly 1000 references and 2000 bootstrap draws")
    prepared, _, rows, _ = source(inputs)
    features, root = bind(inputs, "features")
    parent, parent_root = bind(inputs, "ca1")
    if parent.get("card") != "CA1" or (not fixture and parent.get("mode") != "full"):
        raise ValueError("complete full CA1 comparison required, regardless of its outcome")
    if features.get("card") != "CA1-features" or (not fixture and features.get("mode") != "full"):
        raise ValueError("full CA1 features required")
    for key in ("prepared_summary", "prepared_complete", "features_summary", "features_complete"):
        if parent["input_hashes"].get(key) != sha256(inputs[key]):
            raise ValueError("CA1/CA2 source binding differs")
    if features["input_hashes"]["prepared_summary"] != sha256(inputs["prepared_summary"]):
        raise ValueError("feature preparation differs")
    for name, expected in features["output_hashes"].items():
        if sha256(root/name) != expected: raise ValueError("feature bytes changed")
    index = read(root/"INDEX.json")
    if index["comparison_indices"] != list(range(len(rows))):
        raise ValueError("CA2 must retain every frozen comparison")
    completion = read(inputs["ca1_complete"])
    def parent_file(name, contents=True):
        path = parent_root/name
        key = path.relative_to(Path(inputs["ca1_complete"]).resolve().parent).as_posix()
        if not path.is_file() or completion.get("outputs", {}).get(key) != sha256(path):
            raise ValueError("CA1 reference file lacks authenticated completion: "+name)
        return read(path) if contents else path
    binding = parent_file("BINDINGS.json")
    if int(binding["config"].get("seed", SEED)) != SEED or int(binding["config"].get("permutation_draws", 1000)) != count:
        raise ValueError("CA1 reference bank differs from frozen CA2 assignment bank")
    # Authenticate the whole required bank before any newly fitted output.
    first = parent_file("REAL.json")
    controls = [parent_file(f"permutations/{j:04}.json", False) for j in range(count)]
    with threadpool_limits(limits=2):
        x, pca = stats.candidate_features(rows, np.load(root/"EMBEDDINGS.npy", allow_pickle=False), index["text_indices"])
    assert_equal(pca, parent_file("PCA.json"))
    return prepared, rows, index, x, first, controls, count, draws


def run(output, inputs, config, verifying=False):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    bindings = {"inputs":input_hashes(inputs), "config":config, "module_sha256":sha256(__file__)}
    def save(name, value):
        path = output/name
        if path.exists(): assert_equal(value, read(path))
        elif verifying: raise ValueError("missing CA2 calculation: "+name)
        else: write(path, value)
    save("BINDINGS.json", bindings)
    prepared, rows, index, x, first, controls, count, draws = load(inputs, config)
    people = sorted({r["writer"] for r in rows})
    started = time.process_time()
    with threadpool_limits(limits=2): second = fit_half(rows, x, {}, people)
    save("PRIVATE_SECOND_HALF_REAL.json", second)
    deviations, directions, countries = paired(first, second, people)
    real, zero = cosines(deviations); null = []; timings = []
    for j in range(count):
        name = f"private_second_half_references/{j:04}.json"; path = output/name
        receipt = path.with_suffix(".receipt.json")
        if path.exists() and receipt.exists() and not verifying:
            prior = read(receipt)
            if prior["sha256"] != sha256(path): raise ValueError("changed CA2 checkpoint")
            result, charge = read(path), prior["cpu_seconds"]
        else:
            begun = time.process_time()
            assigned = stats.assignment(rows, index["prompt_clusters"], prepared["permutation_route"], SEED+j)
            with threadpool_limits(limits=2): result = fit_half(rows, x, assigned, people)
            save(name, result); charge = time.process_time()-begun
            if not verifying: write(receipt, {"sha256":sha256(path), "cpu_seconds":charge})
        fake, _, _ = paired(read(controls[j]), result, people)
        null.append(cosines(fake)[0]); timings.append(charge)
        if not verifying:
            atomic(output/"PROGRESS.json", {"phase":"opposite_half_references", "complete":j+1, "total":count})
            if (output/"YIELD_REQUEST.json").exists():
                return {"status":"yielded", "card":"CA2", "completed_permutations":j+1}
    report = {"card":"CA2", "input_hashes":input_hashes(inputs), "fixture":bool(config.get("fixture", False)),
              "primary":summarize(real, null, draws), "zero_deviation_annotators":int(zero.sum()),
              "decomposition":decompose(directions, countries),
              "direction":"individual coefficient minus its fitted country coefficient; cosine across the shared candidate-only PCA coordinates",
              "source_reuse":"authenticated independently verified CA1 first-half real/reference fits; exact candidate PCA regenerated; all second-half fits newly executed and replayed",
              "reference":"identical whole-conversation assignments within country/first-prompt stratum; all recipient halves and opposite-half readers rebuilt; no redraw or population reduction",
              "scope":"stability of fitted choice directions beyond country; no independent values, competence or causal claim",
              "original_cpu_cap_seconds":3600, "seed":SEED}
    save("SUMMARY.json", report)
    if not verifying and not (output/"TIMING.json").exists():
        write(output/"TIMING.json", {"reference_cpu_seconds":timings, "fit_and_summary_cpu_seconds":time.process_time()-started,
                                    "scope":"source loading and candidate PCA precede this timer; native owner accounts whole process and fresh replay"})
    return report


def execute(output, inputs, config): return run(output, inputs, config)
def verify(output, inputs, config):
    run(output, inputs, config, True)
    return {"verified":True, "authenticated_first_half_and_fresh_all_opposite_half_fits":True}
