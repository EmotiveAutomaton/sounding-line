"""CA1 conditional value directions with whole-conversation reference assignments.

DESIGN CHECK: LESSONS 3-5 and CONTROLS. A country-only world must not license an
individual direction. A planted personal direction must improve new-prompt
choice prediction. Candidate-only PCA uses no choices, explanations or prompts.
The frozen original cohort is never reselected under a reference assignment;
every comparison, conversation and disjoint half is reconstructed instead.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import time

import numpy as np
from scipy.special import logsumexp, softmax
from sklearn.decomposition import PCA
from threadpoolctl import threadpool_limits

from .batch_runtime import atomic
from .menus_io import assert_equal, input_hashes, read, write, sha256
from .week3_alignment_features import bind, source
from .week3_alignment_inputs import UnionFind, hashed

SEED = 20261026
DIMENSIONS = 16


def objective(x, choice, beta, prior, penalty, hessian=True):
    logits = np.einsum("nkd,d->nk", x, beta); p = softmax(logits, axis=1)
    chosen = x[np.arange(len(x)), choice]
    residual = beta - prior
    value = float(np.sum(logsumexp(logits, axis=1) - logits[np.arange(len(x)), choice])
                  + .5 * penalty * residual @ residual)
    means = np.einsum("nk,nkd->nd", p, x)
    grad = np.sum(means - chosen, axis=0) + penalty * residual
    if not hessian: return value, grad
    centered = x - means[:, None, :]
    hess = np.einsum("nk,nkd,nke->de", p, centered, centered) + penalty * np.eye(x.shape[2])
    return value, grad, hess


def fit(x, choice, prior=None, penalty=10.):
    x = np.asarray(x, dtype=float); choice = np.asarray(choice, dtype=int)
    if x.ndim != 3 or x.shape[1] != 4 or choice.shape != (len(x),) or not len(x):
        raise ValueError("nonempty four-candidate reference design required")
    if not np.isfinite(x).all() or not np.isin(choice, np.arange(4)).all() or penalty <= 0:
        raise ValueError("invalid conditional-logit design")
    prior = np.zeros(x.shape[2]) if prior is None else np.asarray(prior, dtype=float)
    if prior.shape != (x.shape[2],) or not np.isfinite(prior).all(): raise ValueError("invalid prior direction")
    beta = prior.copy(); certificate = np.inf
    for _ in range(40):
        value, gradient, hessian = objective(x, choice, beta, prior, penalty)
        certificate = float(np.max(np.abs(gradient)))
        if certificate <= 1e-6: break
        delta = np.linalg.solve(hessian, gradient); descent = float(delta @ gradient)
        if not np.isfinite(delta).all() or descent <= 0: raise ValueError("conditional-logit non-descent step")
        for backtrack in range(40):
            scale = 2. ** -backtrack; candidate = beta - scale * delta
            next_value, next_grad = objective(x, choice, candidate, prior, penalty, False)
            rounding = 8 * np.finfo(float).eps * max(1., abs(value))
            if (next_value <= value - 1e-4 * scale * descent or
                (next_value <= value + rounding and np.max(np.abs(next_grad)) < certificate)):
                beta = candidate; break
        else: raise ValueError("conditional-logit line search failed")
    certificate = float(np.max(np.abs(objective(x, choice, beta, prior, penalty, False)[1])))
    if certificate > 1e-4: raise ValueError("conditional-logit gradient certificate failed")
    return beta


def losses(x, choice, beta):
    logits = np.einsum("nkd,d->nk", x, beta)
    return logsumexp(logits, axis=1) - logits[np.arange(len(x)), choice]


def candidate_features(rows, embeddings, text_indices, dimensions=DIMENSIONS, seed=SEED):
    lookup = {int(value): i for i, value in enumerate(text_indices)}
    ids = sorted({i for row in rows for i in row["candidates"]})
    if any(i not in lookup for i in ids): raise ValueError("missing candidate vector")
    # No prompt vectors, chosen labels, explanations or identity terms enter PCA.
    values = np.array([embeddings[lookup[i]] for i in ids], dtype=float)
    k = min(int(dimensions), len(values) - 1, values.shape[1])
    if k < 1: raise ValueError("insufficient candidate representation")
    pca = PCA(n_components=k, svd_solver="randomized", random_state=seed, whiten=False)
    reduced = pca.fit_transform(values)
    scale = np.sqrt(pca.explained_variance_)
    if np.any(scale < 1e-10): raise ValueError("candidate PCA rank below frozen dimensions")
    reduced /= scale
    projected = {i: reduced[j] for j, i in enumerate(ids)}
    x = np.array([[projected[i] for i in row["candidates"]] for row in rows])
    # A common offset of all candidates cannot affect a conditional choice.
    x -= x.mean(axis=1, keepdims=True)
    return x, {"dimensions": k, "candidate_texts": len(ids), "candidate_only": True,
               "components": pca.components_.tolist(), "mean": pca.mean_.tolist(), "scale": scale.tolist()}


def conversations(rows):
    groups = defaultdict(list)
    for i, row in enumerate(rows): groups[row["conversation"]].append(i)
    for group in groups.values():
        if len({rows[i]["writer"] for i in group}) != 1 or len({rows[i]["country"] for i in group}) != 1:
            raise ValueError("conversation owner or country changed")
        if len({rows[i]["turn"] for i in group}) != len(group): raise ValueError("duplicate conversation turn")
    return groups


def assignment(rows, prompt_clusters, route, seed):
    groups = conversations(rows); strata = defaultdict(list)
    for conversation, indices in sorted(groups.items()):
        first = min(indices, key=lambda i: rows[i]["turn"]); row = rows[first]
        if "cluster" in route:
            if row["prompt"] not in prompt_clusters: raise ValueError("missing first-prompt cluster")
            key = row["country"], prompt_clusters[row["prompt"]]
        else:
            # The same literal prompt is additionally conditioned on country,
            # retaining the nuisance variable in the own-beyond-culture question.
            key = row["country"], row["prompt"]
        strata[key].append(conversation)
    rng = np.random.default_rng(seed); result = {}
    for _, group in sorted(strata.items()):
        owners = [rows[groups[c][0]]["writer"] for c in group]
        result.update({c: str(w) for c, w in zip(group, rng.permutation(owners))})
    return result


def fixed_halves(rows, assigned, fixed_writers, seed=SEED):
    grouped = defaultdict(list)
    for i, row in enumerate(rows): grouped[assigned.get(row["conversation"], row["writer"])].append(i)
    if sorted(grouped) != sorted(fixed_writers): raise ValueError("reference changed fixed annotator population")
    halves = np.full(len(rows), -1, dtype=int); owners = np.empty(len(rows), dtype=object); details = {}
    for writer, indices in sorted(grouped.items()):
        uf = UnionFind(); prompts = set(); countries = set()
        for i in indices:
            row = rows[i]; prompts.add(row["prompt"]); countries.add(row["country"])
            uf.join("p:" + row["prompt"], "c:" + row["conversation"])
        if len(countries) != 1: raise ValueError("reference annotator crosses country")
        components = defaultdict(set)
        for prompt in prompts: components[uf.find("p:" + prompt)].add(prompt)
        if len(components) < 2: raise ValueError("reference has unsupported connected-component split")
        ordered = sorted(components, key=lambda c: (-len(components[c]), hashed(f"{seed}:{writer}:{c}")))
        counts = [0, 0]; component_halves = {}
        for component in ordered:
            half = 0 if counts[0] <= counts[1] else 1
            component_halves[component] = half; counts[half] += len(components[component])
        for i in indices:
            halves[i] = component_halves[uf.find("c:" + rows[i]["conversation"])]; owners[i] = writer
        details[writer] = {"comparisons": len(indices), "prompts": len(prompts),
                           "comparisons_per_half": [int(np.sum(halves[indices] == h)) for h in (0, 1)],
                           "prompts_per_half": counts, "country": next(iter(countries))}
        if min(details[writer]["comparisons_per_half"]) < 1: raise ValueError("empty reference half")
    return halves, owners, details


def evaluate(rows, x, assigned, fixed_writers, seed=SEED, half=0):
    halves, owners, support = fixed_halves(rows, assigned, fixed_writers, seed)
    train = halves == half; test = ~train
    choices = np.array([r["choice"] for r in rows], dtype=int)
    countries = np.array([r["country"] for r in rows]); country_fit = {}
    population = fit(x[train], choices[train], penalty=1.)
    for country in sorted(set(countries)):
        mask = train & (countries == country)
        country_fit[country] = fit(x[mask], choices[mask], prior=population, penalty=10.)
    output = {}
    for writer in sorted(fixed_writers):
        own_train = train & (owners == writer); own_test = test & (owners == writer)
        country = support[writer]["country"]; baseline = country_fit[country]
        beta = fit(x[own_train], choices[own_train], prior=baseline, penalty=10.)
        individual_loss = losses(x[own_test], choices[own_test], beta)
        country_loss = losses(x[own_test], choices[own_test], baseline)
        population_loss = losses(x[own_test], choices[own_test], population)
        output[writer] = {"heldout_individual_minus_country_gain": float(np.mean(country_loss-individual_loss)),
                          "heldout_country_minus_population_gain": float(np.mean(population_loss-country_loss)),
                          "train_comparisons": int(own_train.sum()), "test_comparisons": int(own_test.sum()),
                          "individual": beta.tolist(), "country": baseline.tolist(), "support": support[writer]}
    return {"profiles": output, "population": population.tolist(), "country": {k:v.tolist() for k,v in country_fit.items()},
            "split_rebuilt": True, "train_half": half}


def summarize(real, controls, draws=2000, seed=SEED):
    writers = sorted(real["profiles"])
    if len(writers) < 4: return {"state": "unsupported", "reason": "fewer than four fixed annotators"}
    if not controls or any(sorted(c["profiles"]) != writers for c in controls): raise ValueError("reference population changed")
    field = "heldout_individual_minus_country_gain"
    values = np.array([real["profiles"][w][field] for w in writers])
    null = np.array([[c["profiles"][w][field] for w in writers] for c in controls])
    null_means = null.mean(axis=1); observed = float(values.mean())
    p = float((1+np.sum(null_means >= observed-1e-14))/(len(null)+1))
    rng = np.random.default_rng(seed+101); raw = []; excess = []
    for _ in range(draws):
        ix = rng.integers(0,len(writers),len(writers))
        raw.append(float(values[ix].mean())); excess.append(float(values[ix].mean()-null[:,ix].mean()))
    interval = np.quantile(raw,[.025,.975]).tolist(); contrast_interval = np.quantile(excess,[.025,.975]).tolist()
    state = "positive" if interval[0]>0 and p<.05 else "negative" if interval[1]<0 else "marginal" if observed>0 else "null"
    if interval[0]>0 and p>=.05: state="unresolved"
    bins = {}
    for low,high in ((0,9),(10,19),(20,39),(40,79),(80,10**9)):
        chosen=[w for w in writers if low<=real["profiles"][w]["train_comparisons"]<=high]
        bins[f"{low}-{high if high<10**9 else 'plus'}"]={"annotators":len(chosen),
            "individual_gain":float(np.mean([real["profiles"][w][field] for w in chosen])) if chosen else None}
    return {"state":state,"annotators":len(writers),"heldout_log_loss_gain":observed,
            "annotator_cluster_95_interval":interval,"permutation_mean":float(null_means.mean()),
            "permutation_95_interval":np.quantile(null_means,[.025,.975]).tolist(),"permutation_p_one_sided":p,
            "real_minus_permutation_mean":float(observed-null_means.mean()),"paired_annotator_95_interval":contrast_interval,
            "country_over_population_gain":float(np.mean([real["profiles"][w]["heldout_country_minus_population_gain"] for w in writers])),
            "training_comparison_curve_descriptive":bins,"bootstrap_draws":draws,"permutation_draws":len(null),
            "prototype_cosines":"deferred until independently admitted CA3/VAL labels",
            "null_wording":"not detected; sensitivity untested" if state=="null" else None}


def run(output, inputs, config, verifying=False):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    mode=config.get("mode","full");permutations=int(config.get("permutation_draws",1000));seed=int(config.get("seed",SEED))
    if mode not in ("full","fixture"): raise ValueError("statistical pilot uses separate timing handler")
    if mode=="full" and permutations<1000: raise ValueError("full CA1 requires 1000 reference assignments")
    bindings={"inputs":input_hashes(inputs),"config":config,"module_sha256":sha256(__file__)}
    if (output/"BINDINGS.json").exists():assert_equal(bindings,read(output/"BINDINGS.json"))
    elif verifying:raise ValueError("missing source bindings")
    else:write(output/"BINDINGS.json",bindings)
    prepared,_,rows,_=source(inputs);features,root=bind(inputs,"features")
    if features.get("card")!="CA1-features":raise ValueError("completed CA1 features required")
    if features["input_hashes"]["prepared_summary"]!=sha256(inputs["prepared_summary"]):raise ValueError("features came from different prepared inputs")
    if mode=="full" and features.get("mode")!="full":raise ValueError("full comparison requires full features")
    for name,expected in features["output_hashes"].items():
        if sha256(root/name)!=expected:raise ValueError("feature table changed")
    index=read(root/"INDEX.json");selected=index["comparison_indices"]
    selected_rows=[rows[i] for i in selected]
    if mode=="full" and selected!=list(range(len(rows))):raise ValueError("full CA1 comparison population changed")
    fixed=sorted({r["writer"] for r in selected_rows})
    embeddings=np.load(root/"EMBEDDINGS.npy",allow_pickle=False)
    with threadpool_limits(limits=2):
        x,pca=candidate_features(selected_rows,embeddings,index["text_indices"],seed=seed)
        real=evaluate(selected_rows,x,{},fixed,seed)
    def save_or_compare(name,value):
        path=output/name
        if path.exists():assert_equal(value,read(path))
        elif verifying:raise ValueError("missing calculation "+name)
        else:write(path,value)
    save_or_compare("PCA.json",pca);save_or_compare("REAL.json",real)
    controls=[];timings=[]
    for number in range(permutations):
        started=time.process_time();path=output/"permutations"/f"{number:04}.json";receipt=path.with_suffix(".receipt.json")
        if path.exists() and receipt.exists() and not verifying:
            prior=read(receipt)
            if prior["sha256"]!=sha256(path):raise ValueError("changed null checkpoint")
            result=read(path);charge=prior["cpu_seconds"]
        else:
            assigned=assignment(selected_rows,index["prompt_clusters"],prepared["permutation_route"],seed+number)
            with threadpool_limits(limits=2):result=evaluate(selected_rows,x,assigned,fixed,seed)
            save_or_compare(f"permutations/{number:04}.json",result);charge=time.process_time()-started
            if not verifying:write(receipt,{"sha256":sha256(path),"cpu_seconds":charge})
        controls.append(result);timings.append(charge)
        if not verifying:
            atomic(output/"PROGRESS.json",{"phase":"reference_assignments","complete":number+1,"total":permutations})
            if (output/"YIELD_REQUEST.json").exists():return {"status":"yielded","card":"CA1","completed_permutations":number+1}
    report={"card":"CA1","mode":mode,"input_hashes":input_hashes(inputs),
            "reader":"candidate-only PCA16, conditional logit; ridge population 1, country toward population 10, individual toward country 10",
            "cohort":"original eligible annotators fixed; no reselection/redraw after reference reassignment",
            "reference":"whole conversations within country and frozen first-prompt stratum; all connected-component halves and fits rebuilt",
            "prompt_stratum_route":prepared["permutation_route"],
            "literal_turn_level_reference":"unrun; would split conversational dependence",
            "primary":summarize(real,controls,int(config.get("bootstrap_draws",2000)),seed),
            "scope":"held-out choice prediction under the pinned representation; no competence, ground-truth values or causal claim"}
    save_or_compare("SUMMARY.json",report)
    if not verifying and not (output/"TIMING.json").exists():
        write(output/"TIMING.json",{"reference_cpu_seconds":timings,"one_pass_1000_reference_projection":float(np.mean(timings)*1000),
              "projection_scope":"fit/reference work on selected comparisons only; charge full features, actual real fit, source work and fresh replay separately"})
    return report


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):
    run(output,inputs,config,True)
    return {"verified":True,"fresh_candidate_pca_splits_all_readers_and_nulls":True}
