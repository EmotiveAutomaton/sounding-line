"""D2 primary: held-session choice gain across menu-dissimilarity quintiles.

DESIGN CHECK 2026-10-17: lessons read: LESSONS 3-5 and CONTROLS 1-3.
NULL: randomized choices cannot improve held-out log score over uniform;
identical attributes imply uniform probabilities. ALTERNATIVE: a content-linked
choice rule with larger attribute differences yields greater gain in distant
menus. Reverse exclusion is negative, zero-crossing positive point marginal,
zero-crossing nonpositive point null; bands exhaustive. Nonfinite, unsupported or uncertified
fits fail closed, never become a null. These are descriptive states, not gates
for identification. The hierarchical Bayes extension is NOT computed here.

Forecasts condition on uptake and unique observed selected text. Each recipient
uses pooled training sessions ending strictly before their calibration starts;
calibration chooses one fixed L2 penalty. PCA, scaling and quintile edges use
training only. Equal-weight writer intervals condition on fitted forecasts.
Position and producer-score rivals remain in the model: gain is predictive,
not content-specific or person-specific. Producer scores are not probabilities.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import hashlib
import json
import math
import re
import time
import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp
from sklearn.decomposition import PCA

from .menus_io import read, write, sha256, input_hashes, assert_equal
from .menus_p4 import chronological_partitions, recipient_split
from .menus_p8 import SETTINGS
from .menus_v5 import normalized
from .states_v2 import contrast_state

CONFIG = dict(seed=20261017, bootstrap=2000, penalties=[.01, .1, 1., 10.],
              pca_components=16, minimum_writers=3)


def authenticated(inputs):
    for marker, names in (("content_complete", ("records", "vectors")),
                          ("p8_complete", ("p8",))):
        path = Path(inputs[marker]); receipt = read(path)
        if receipt.get("status") != "COMPLETE":
            raise ValueError("incomplete dependency")
        for name in names:
            relative = Path(inputs[name]).resolve().relative_to(path.parent.resolve()).as_posix()
            if receipt["outputs"].get(relative) != sha256(inputs[name]):
                raise ValueError("dependency output identity differs")
    # P8 was extracted against this exact prepared session roster.
    p8root = Path(inputs["p8_complete"]).parent
    p8plan = p8root / "PLAN.json"
    if read(inputs["p8_complete"])["outputs"].get("PLAN.json") != sha256(p8plan):
        raise ValueError("P8 plan changed")
    pp = read(p8plan)
    if pp["pins"].get(str(Path(inputs["sessions"]).resolve())) != sha256(inputs["sessions"]):
        raise ValueError("P8 session binding differs")


def assemble(sessions, records, vectors, p8):
    features = {r["key"]: r for r in records}
    if len(features) != len(records):
        raise ValueError("duplicate content key")
    producer = defaultdict(list)
    for item in p8:
        producer[item["key"]].append(item)
    vectors = normalized(vectors)
    seen = set(); cases = {}; excluded = Counter()
    for session in sorted(sessions, key=lambda s: s["session"]):
        for row in session["rows"]:
            key = row["key"]
            if key in seen or row["session"] != session["session"] or row["writer"] != session["writer"]:
                raise ValueError("duplicate or mismatched decision")
            seen.add(key); feature = features[key]
            options = feature["options"]; menu = row["menu"]
            scores = sorted(producer[key], key=lambda r: r["position"])
            if (feature["writer"] != row["writer"] or feature["session"] != row["session"]
                    or len(options) != len(menu) or len(scores) != len(menu)
                    or [r["position"] for r in scores] != list(range(len(menu)))
                    or len({r["suggestion_index"] for r in scores}) != len(menu)):
                raise ValueError("option coverage differs")
            if any(r["writer"] != row["writer"] or r["session"] != row["session"]
                   or r["ordinal"] != row["ordinal"] for r in scores):
                raise ValueError("P8 identity mismatch")
            if row["handling"] not in ("accept", "edit"):
                excluded["no_observed_selection"] += 1; continue
            if len(menu) < 2:
                excluded["single_option"] += 1; continue
            matches = [i for i, text in enumerate(menu) if text == row["inserted"]]
            if len(matches) != 1:
                excluded["ambiguous_or_absent_selected_text"] += 1; continue
            v = vectors[options]; distance = 1 - v @ v.T
            novelty = (distance.sum(axis=1) - np.diag(distance)) / (len(menu) - 1)
            dissimilarity = float(np.mean(distance[np.triu_indices(len(menu), 1)]))
            overlap_context = v @ vectors[feature["context"]]
            prior = set(re.findall(r"\w+", row["document"][-1200:].lower()))
            x = []
            for i, text in enumerate(menu):
                words = set(re.findall(r"\w+", text.lower())); p = scores[i]
                score = p["logged_score"]
                settings = [p["decoding_numeric"][k] for k in SETTINGS]
                if any(a is not None and (isinstance(a, bool) or not math.isfinite(a))
                       for a in [score] + settings):
                    raise ValueError("nonfinite producer field")
                setting_values = [0. if a is None else math.copysign(math.log1p(abs(a)), a) for a in settings]
                x.append([math.log1p(len(text)), i / (len(menu)-1), float(i == 0),
                          float(overlap_context[i]), len(words & prior)/max(1, len(words)),
                          float(novelty[i]), 0. if score is None else math.copysign(math.log1p(abs(score)), score),
                          float(score is None)] + setting_values + [float(a is None) for a in settings]
                         + [a * overlap_context[i] for a in setting_values]
                         + [a * novelty[i] for a in setting_values])
            cases[key] = dict(key=key, writer=row["writer"], session=row["session"],
                              truth=matches[0], x=np.asarray(x), embeddings=v,
                              dissimilarity=dissimilarity)
    if seen != set(features) or seen != set(producer):
        raise ValueError("decision coverage differs")
    return cases, dict(excluded)


def transformed(cases, pca, scale=None):
    matrices = [np.column_stack((c["x"], pca.transform(c["embeddings"]))) for c in cases]
    matrices = [x-x.mean(axis=0) for x in matrices]
    if scale is None:
        scale = np.sqrt(np.mean(np.concatenate(matrices)**2, axis=0))
        scale[scale < 1e-10] = 1.
    return [x/scale for x in matrices], scale


def pack(matrices, truths):
    sizes = np.array([len(x) for x in matrices], dtype=int)
    if not len(sizes) or np.any(sizes < 2) or len(truths) != len(sizes):
        raise ValueError("empty or unsupported choice set")
    truths = np.asarray(truths, int)
    if np.any(truths < 0) or np.any(truths >= sizes):
        raise ValueError("choice outside offer set")
    x = np.concatenate(matrices); starts = np.r_[0, np.cumsum(sizes)[:-1]]
    if not np.isfinite(x).all():
        raise ValueError("nonfinite design")
    return x, sizes, starts, starts + truths


def objective(beta, data, penalty):
    x, sizes, starts, selected = data
    z = x @ beta; maximum = np.maximum.reduceat(z, starts)
    ez = np.exp(z-np.repeat(maximum, sizes)); den = np.add.reduceat(ez, starts)
    prob = ez / np.repeat(den, sizes); prob[selected] -= 1
    loss = np.mean(maximum + np.log(den) - z[selected]) + penalty * np.dot(beta, beta)/2
    return float(loss), x.T @ prob / len(sizes) + penalty * beta


def fit(data, penalty):
    result = minimize(objective, np.zeros(data[0].shape[1]), args=(data, penalty), jac=True,
                      method="L-BFGS-B", options=dict(maxiter=2000, ftol=1e-13, gtol=1e-8))
    loss, gradient = objective(result.x, data, penalty)
    gap = float(np.max(np.abs(gradient)))
    if not result.success or not np.isfinite(loss) or gap > 1e-6:
        raise ValueError(f"uncertified choice fit: {result.message}, gradient={gap}")
    return result.x, dict(objective=loss, gradient_max=gap, iterations=int(result.nit))


def log_scores(beta, matrices, truths):
    return np.array([(x @ beta)[truth] - logsumexp(x @ beta) for x, truth in zip(matrices, truths)])


def labels(cases, arm, seed):
    if arm == "primary": return [c["truth"] for c in cases]
    if arm != "uniform_control": raise ValueError("unknown arm")
    # Independent per-menu uniform choices, fixed across recipient folds.
    return [int(np.random.default_rng(int.from_bytes(hashlib.sha256(
        f'{seed}:{c["key"]}'.encode()).digest()[:8], "little")).integers(len(c["x"]))) for c in cases]


def fit_recipient(split, cases, config):
    groups = [[cases[r["key"]] for s in split[k] for r in s["rows"] if r["key"] in cases]
              for k in ("train", "calibration", "test")]
    if any(not g for g in groups): return None
    train, calibration, test = groups
    pca = PCA(n_components=min(config["pca_components"], len(np.concatenate([c["embeddings"] for c in train])),
                               train[0]["embeddings"].shape[1]), svd_solver="full")
    pca.fit(np.concatenate([c["embeddings"] for c in train]))
    tr, scale = transformed(train, pca)
    ca, _ = transformed(calibration, pca, scale); te, _ = transformed(test, pca, scale)
    edges = np.quantile([c["dissimilarity"] for c in train], [.2, .4, .6, .8])
    output = dict(edges=edges.tolist(), train_count=len(train), calibration_count=len(calibration),
                  test_count=len(test), cutoff=split["cutoff"], test_cutoff=split["test_cutoff"],
                  preprocessing=dict(scale=scale.tolist(), pca_mean=pca.mean_.tolist(),
                                     pca_components=pca.components_.tolist()), arms={})
    for arm in ("primary", "uniform_control"):
        ty, cy, ey = [labels(g, arm, config["seed"]) for g in groups]
        fits = []
        for penalty in config["penalties"]:
            beta, certificate = fit(pack(tr, ty), penalty)
            loss = float(-log_scores(beta, ca, cy).mean())
            fits.append((loss, penalty, beta, certificate))
        loss, penalty, beta, certificate = min(fits, key=lambda v: (v[0], v[1]))
        scores = log_scores(beta, te, ey)
        output["arms"][arm] = dict(beta=beta.tolist(), penalty=penalty,
            calibration_losses=[dict(penalty=p, loss=l) for l,p,_,_ in fits], certificate=certificate,
            predictions=[dict(key=c["key"], session=c["session"], writer=c["writer"], truth=y,
                size=len(c["x"]), quintile=int(np.searchsorted(edges, c["dissimilarity"], side="right")),
                log_probability=float(lp), gain=float(lp + math.log(len(c["x"]))))
                for c,y,lp in zip(test, ey, scores)])
    return output


def summarize(predictions, config):
    by_writer = defaultdict(lambda: defaultdict(list))
    for row in predictions:
        by_writer[row["writer"]][row["quintile"]].append(row["gain"])
    paired = sorted(w for w,g in by_writer.items() if g[0] and g[4])
    if len(paired) < config["minimum_writers"]:
        raise ValueError("insufficient writers with both extreme quintiles")
    values = np.array([np.mean(by_writer[w][4])-np.mean(by_writer[w][0]) for w in paired])
    rng = np.random.default_rng(config["seed"])
    draws = values[rng.integers(len(values), size=(config["bootstrap"], len(values)))].mean(axis=1)
    low, high = np.quantile(draws, [.025,.975]); point = float(values.mean()); se = float(draws.std(ddof=1))
    return dict(primary=dict(effect=point, ci95=[float(low),float(high)], standard_error=se,
                            p_approx=math.erfc(abs(point/se)/math.sqrt(2)) if se > 0 else None),
        state=contrast_state(point,low,high), writers=len(paired), menus=len(predictions),
        primary_menus=sum(len(by_writer[w][q]) for w in paired for q in (0,4)),
        writers_without_both_extremes=len(by_writer)-len(paired),
        quintiles=[dict(quintile=q, writers=sum(bool(g[q]) for g in by_writer.values()),
            menus=sum(len(g[q]) for g in by_writer.values()),
            mean_writer_gain=float(np.mean([np.mean(g[q]) for g in by_writer.values() if g[q]]))
            if any(g[q] for g in by_writer.values()) else None) for q in range(5)],
        uncertainty="equal-writer bootstrap conditional on fitted forecasts, fitted preprocessing and training-defined quintiles; not full refit uncertainty")


def load(inputs):
    authenticated(inputs)
    sessions=read(inputs["sessions"])
    with Path(inputs["p8"]).open(encoding="utf8") as stream: producer=[json.loads(line) for line in stream]
    cases,excluded=assemble(sessions,read(inputs["records"]),np.load(inputs["vectors"],allow_pickle=False),producer)
    splits,unsupported=chronological_partitions(sessions)
    return cases,splits,dict(menu_exclusions=excluded,session_exclusions=unsupported)


def execute(output, inputs, config):
    output=Path(output); output.mkdir(parents=True,exist_ok=True); started=time.perf_counter()
    binding=dict(inputs=input_hashes(inputs),config=config)
    if (output/"BINDING.json").exists(): assert_equal(read(output/"BINDING.json"),binding)
    else: write(output/"BINDING.json",binding)
    if (output/"SUMMARY.json").exists(): verify(output,inputs,config); return read(output/"SUMMARY.json")
    cases,splits,excluded=load(inputs); predictions=defaultdict(list); manifests={}; support=[]
    for number,writer in enumerate(sorted(splits),1):
        if (output/"YIELD_REQUEST.json").exists(): return dict(status="yielded",completed=number-1)
        split=recipient_split(writer,splits)
        if split["reason"]:
            support.append(dict(writer=writer,reason=split["reason"])); continue
        name=hashlib.sha256(writer.encode()).hexdigest()[:24]+".json"; path=output/"recipients"/name
        if path.exists():
            if sha256(path)!=read(path.with_suffix(".seal.json"))["sha256"]: raise ValueError("checkpoint changed")
            saved=read(path); assert_equal(saved["binding"],binding)
        else:
            result=fit_recipient(split,cases,config)
            saved=dict(binding=binding,result=result)
            write(path,saved);write(path.with_suffix(".seal.json"),dict(sha256=sha256(path)))
        manifests[path.relative_to(output).as_posix()]=sha256(path)
        if saved["result"] is None: support.append(dict(writer=writer,reason="empty actual choice partition"))
        else:
            for arm,record in saved["result"]["arms"].items(): predictions[arm].extend(record["predictions"])
        if number>=max(1,math.ceil(.1*len(splits))) and not (output/"FIRST_TENTH.json").exists():
            elapsed=time.perf_counter()-started
            write(output/"FIRST_TENTH.json",dict(completed_recipients=number,total_recipients=len(splits),
                  elapsed_seconds=elapsed,projected_seconds=elapsed*len(splits)/number))
    if (output/"YIELD_REQUEST.json").exists(): return dict(status="yielded",completed=len(splits))
    report=dict(card="D2",descriptive=True,scientific_admission=False,**summarize(predictions["primary"],config),
                uniform_control=summarize(predictions["uniform_control"],config),exclusions=excluded,
                unsupported_recipients=support,input_hashes=binding["inputs"],config=config,
                recipient_hashes=manifests,extension_computed=False)
    write(output/"SUMMARY.json",report)
    return report


def verify(output, inputs, config):
    output=Path(output); report=read(output/"SUMMARY.json")
    assert_equal(report["input_hashes"],input_hashes(inputs)); assert_equal(report["config"],config)
    authenticated(inputs); predictions=defaultdict(list)
    for name,expected in sorted(report["recipient_hashes"].items()):
        if sha256(output/name)!=expected: raise ValueError("changed saved recipient")
        saved=read(output/name)
        assert_equal(saved["binding"],dict(inputs=report["input_hashes"],config=config))
        if saved["result"]:
            for arm,record in saved["result"]["arms"].items():
                for row in record["predictions"]:
                    if not 0 <= row["truth"] < row["size"] or row["size"] < 2:
                        raise ValueError("saved choice outside offer set")
                    if not math.isfinite(row["log_probability"]) or row["log_probability"] > 1e-12:
                        raise ValueError("invalid saved log probability")
                    if row["gain"] != row["log_probability"] + math.log(row["size"]):
                        raise ValueError("saved gain differs from probability")
                predictions[arm].extend(record["predictions"])
    for arm in ("primary","uniform_control"):
        actual=summarize(predictions[arm],config)
        expected=report if arm=="primary" else report["uniform_control"]
        assert_equal(actual,{k:expected[k] for k in actual})
    return dict(verified=True,primary_recomputed=report["primary"],state=report["state"])
