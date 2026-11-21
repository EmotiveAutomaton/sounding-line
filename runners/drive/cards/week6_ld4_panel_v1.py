"""Counted original-source projection and participant resampling for LD4.

DESIGN CHECK (LESSONS 2–5). Compare both fitting paths with literal repeated
people. A missing feeling changes that word's sample only. Keep the same sorted
source roster and indexed draw in both contexts, including people with no
usable rows. No participant key leaves the projection. A failed numerical or
source gate cannot produce a replacement weight.
"""
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import linalg

from .es_source_v1 import sha256
from .week6_lattice_bindings_v1 import ACTIVITY, STATUS
from .week6_lattice_source_v1 import feeling_names
from .week6_ld4_recipes_v1 import (
    CONTEXTS, agreement, anchors_and_others, fit_recipe, sanity, spectrum,
)

CONDUCT = ("leadership", "criticism", "uninvolved", "selfesteem", "unfriendly", "reserved")


def features(member):
    feeling_names(member)
    interaction = tuple("status_"+s for s in STATUS) + tuple("beh_"+s for s in CONDUCT)
    if member == "0057":
        interaction += ("beh_help", "comfort")
    return {"interaction": interaction, "solitary": ACTIVITY}


@dataclass
class Group:
    columns: tuple
    units: np.ndarray
    products: np.ndarray
    n_rows: int


@dataclass
class Prepared:
    member: str
    people: int
    groups: dict
    observed: dict
    readable: dict
    metadata: dict
    specs: dict
    reference: bool


def grouped_panels(ids, x, y, guard, reference):
    complete_x = np.isfinite(x).all(axis=1)
    masks = {}
    for j in range(y.shape[1]):
        mask = complete_x & np.isfinite(y[:,j])
        key = np.packbits(mask).tobytes()
        if key not in masks:
            masks[key] = (mask, [])
        masks[key][1].append(j)
    panels = []
    for mask, cols in masks.values():
        guard()
        order = np.argsort(ids[mask], kind="stable")
        cluster_ids = ids[mask][order]
        data = np.column_stack((x[mask], y[mask][:,cols]))[order]
        units, starts, sizes = np.unique(cluster_ids, return_index=True, return_counts=True)
        products = np.empty((len(units), data.shape[1], data.shape[1]))
        for i, (start, size) in enumerate(zip(starts, sizes)):
            block = data[start:start+size]
            if reference:
                # Pairwise-difference identity, computed relative to the first
                # row to avoid loss of precision from an unrelated offset.
                d = block-block[0]
                s = d.sum(axis=0)
                products[i] = d.T@d - np.outer(s,s)/size
            else:
                centered = block-block.mean(axis=0)
                products[i] = centered.T@centered
        panels.append(Group(tuple(cols), units, products, len(cluster_ids)))
    return panels


def coefficient_table(groups, masses, p, n_words, reference):
    table = np.full((n_words,p), np.nan)
    for panel in groups:
        weights = masses[panel.units]
        if not np.any(weights):
            continue
        joint = np.einsum("i,ijk->jk", weights, panel.products)
        scales = np.sqrt(np.maximum(np.diag(joint), 0.))
        if np.any(scales[:p] <= np.finfo(float).eps):
            continue
        xx = joint[:p,:p]/np.outer(scales[:p],scales[:p])
        # The standardized Gram matrix is positive semidefinite. With rank
        # loss there is no unique joint Form L coefficient row.
        if np.linalg.matrix_rank(xx) < p:
            continue
        valid = scales[p:] > np.finfo(float).eps
        if not np.any(valid):
            continue
        xy = joint[:p,p:][:,valid]/np.outer(scales[:p],scales[p:][valid])
        beta = linalg.lstsq(xx, xy, lapack_driver="gelsy")[0] if reference else np.linalg.solve(xx, xy)
        table[np.asarray(panel.columns)[valid]] = beta.T
    return table


def prepare_arrays(member, n_people, data, source_counts, guard, *, reference=False):
    names = features(member)
    words = feeling_names(member)
    anchors, mixed = anchors_and_others(member)
    if set(data) != set(CONTEXTS) or n_people < 2 or not callable(guard):
        raise ValueError("The two contexts and an authenticated person roster are required")
    groups, observed, readable, specs, support = {}, {}, {}, {}, {}
    def register(key, role):
        specs[key] = {"role":role}
    for context in CONTEXTS:
        ids, x, y = (np.asarray(v) for v in data[context])
        p = len(names[context])
        if (ids.ndim != 1 or ids.dtype.kind not in "iu" or np.any(ids<0) or np.any(ids>=n_people)
                or x.shape != (len(ids),p) or y.shape != (len(ids),len(words))):
            raise ValueError("Context has an invalid roster or feature layout")
        groups[context] = grouped_panels(ids,x,y,guard,reference)
        table = coefficient_table(groups[context],np.ones(n_people),p,len(words),reference)
        observed[context] = table
        condition, _ = fit_recipe(table,member,reference=reference)
        readable[context] = condition is not None and condition<15
        support[context] = {}
        for group in groups[context]:
            for j in group.columns:
                support[context][words[j]] = {"people":len(group.units),"rows":group.n_rows}
        register(context+"/condition","diagnostic")
        register(context+"/noise","diagnostic")
        for i in range(min(table.shape)):
            register(f"{context}/singular/{i+1:02d}","diagnostic")
        for word in mixed:
            for anchor in anchors:
                register(f"{context}/recipe/{word}/{anchor}","recipe")
        for key in sanity(np.ones((len(mixed),len(anchors))),member):
            register(f"{context}/sanity/{key}","descriptive")
    register("cross_context","primary" if member=="0057" else "descriptive")
    metadata = dict(source=source_counts, people=n_people, support=support, features=names,
                    words=words, anchors=anchors, nonanchors=mixed,
                    weight_pairs=len(anchors)*len(mixed))
    return Prepared(member,n_people,groups,observed,readable,metadata,specs,reference)


def _ratings(frame, names, missing):
    result = np.empty((len(frame),len(names)), dtype=float)
    for j,name in enumerate(names):
        raw = frame[name]
        valid = ~raw.isin(missing)
        values = pd.to_numeric(raw.where(valid),errors="coerce").to_numpy(dtype=float)
        x = values[valid.to_numpy()]
        if not np.isfinite(x).all() or np.any((x<1)|(x>6)) or np.any(x!=np.floor(x)):
            raise ValueError("Undocumented rating in "+name)
        result[:,j] = values
    return result


def prepare(member,path,pin,missing_tokens,guard,*,reference=False):
    if not callable(guard) or not isinstance(missing_tokens,list) or not missing_tokens:
        raise ValueError("A guarded source and frozen missing tokens are required")
    path = Path(path)
    names, words = features(member), feeling_names(member)
    outcomes = {k:tuple(("int_" if k=="interaction" else "occup_")+w for w in words) for k in CONTEXTS}
    selected = ["id","interaction",*names["interaction"],*names["solitary"],*outcomes["interaction"],*outcomes["solitary"]]
    def authenticate():
        guard()
        if path.stat().st_size!=pin["bytes"] or sha256(path,guard)!=pin["sha256"]:
            raise ValueError("Original source pin differs")
    authenticate()
    parts = {c:[] for c in CONTEXTS}
    roster = set()
    counts = dict(rows=0,missing_id=0,missing_context=0)
    with pd.read_csv(path, sep="\t", usecols=selected, dtype=str, keep_default_na=False,
                     na_filter=False, chunksize=12000) as reader:
        for frame in reader:
            guard()
            counts["rows"] += len(frame)
            missing_id = frame["id"].isin(missing_tokens)
            counts["missing_id"] += int(missing_id.sum())
            frame = frame.loc[~missing_id]
            roster.update(frame["id"])
            missing = frame["interaction"].isin(missing_tokens)
            counts["missing_context"] += int(missing.sum())
            frame = frame.loc[~missing]
            context = pd.to_numeric(frame["interaction"],errors="raise")
            if not context.isin((1,2)).all():
                raise ValueError("Undocumented interaction type")
            for code,name in enumerate(CONTEXTS,start=1):
                sub = frame.loc[context==code]
                parts[name].append((sub["id"].tolist(),_ratings(sub,names[name],missing_tokens),
                                    _ratings(sub,outcomes[name],missing_tokens)))
    authenticate()
    lookup = {k:i for i,k in enumerate(sorted(roster))}
    data = {}
    for name in CONTEXTS:
        blocks = parts[name]
        ids = np.array([lookup[k] for block in blocks for k in block[0]],dtype=int)
        x = np.concatenate([b[1] for b in blocks]) if blocks else np.empty((0,len(names[name])))
        y = np.concatenate([b[2] for b in blocks]) if blocks else np.empty((0,len(words)))
        data[name] = ids,x,y
        counts[name+"_rows"] = len(ids)
    return prepare_arrays(member,len(roster),data,counts,guard,reference=reference)


def evaluate(prepared,weights,guard,*,verify=False):
    if bool(verify)!=prepared.reference:
        raise ValueError("Replay must reconstruct its own person moments")
    masses = np.ones(prepared.people,dtype=int) if weights is None else np.asarray(weights)
    if (masses.shape!=(prepared.people,) or masses.dtype.kind not in "iu"
            or np.any(masses<0) or masses.sum()!=prepared.people):
        raise ValueError("A complete whole-person draw is required")
    result = dict.fromkeys(prepared.specs)
    recipes = {}
    anchors,mixed = anchors_and_others(prepared.member)
    for context in CONTEXTS:
        guard()
        original = prepared.observed[context]
        table = original if weights is None else coefficient_table(prepared.groups[context],masses,
                                                                    original.shape[1],original.shape[0],verify)
        singular,perturbation = spectrum(table),spectrum(table-original)
        if singular is not None:
            for i,value in enumerate(singular):
                result[f"{context}/singular/{i+1:02d}"] = float(value)
        if perturbation is not None:
            result[context+"/noise"] = float(perturbation[0])
        condition, recipe = fit_recipe(table,prepared.member,reference=verify)
        result[context+"/condition"] = condition
        recipes[context] = recipe if prepared.readable[context] else None
        if recipes[context] is None:
            continue
        for i,word in enumerate(mixed):
            for j,anchor in enumerate(anchors):
                value = recipe[i,j]
                if np.isfinite(value):
                    result[f"{context}/recipe/{word}/{anchor}"] = float(value)
        for name,value in sanity(recipe,prepared.member).items():
            result[f"{context}/sanity/{name}"] = value
    result["cross_context"] = agreement(recipes["interaction"],recipes["solitary"],reference=verify)
    return result
