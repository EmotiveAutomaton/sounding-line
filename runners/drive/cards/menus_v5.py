"""V5: near-repeat handling agreement and personal half-Brier headroom.

All unordered pairs meeting both cosine cutoffs and the same prompt are kept.
Pair weighting is explicit: agreement is the mean over matched pairs. Writer
bootstrap multiplicities weight a within-writer pair once and a between-writer
pair by the product of its two writers' multiplicities. Session labels, rather
than decisions, are shuffled in the control. Saved pairs contain no raw text.

Near-repeat floors are descriptive proxies, conditional on matcher support;
they are not an identified ceiling for unmatched decisions or latent values.
"""
from __future__ import annotations

from pathlib import Path
import numpy as np

from .menus_io import assert_equal, input_hashes, read, sha256, write
from . import states

EPSILONS = (0.6, 0.7, 0.8, 0.9)
ACTIONS = ("accept", "edit", "dismiss", "ignore")


def normalized(values):
    values = np.asarray(values, dtype=np.float64)
    if values.ndim != 2 or not np.isfinite(values).all():
        raise ValueError("invalid embedding matrix")
    norms = np.linalg.norm(values, axis=1)
    if np.any(norms <= 1e-12):
        raise ValueError("zero context or menu-mean vector")
    return values / norms[:, None]


def decision_table(sessions, records, vectors):
    records_by_key = {row["key"]: row for row in records}
    if len(records_by_key) != len(records):
        raise ValueError("duplicate feature key")
    metadata, contexts, menus = [], [], []
    seen = set()
    for session in sorted(sessions, key=lambda row: row["session"]):
        for row in sorted(session["rows"], key=lambda item: item["key"]):
            if row["key"] in seen:
                raise ValueError("duplicate decision key")
            seen.add(row["key"])
            feature = records_by_key[row["key"]]
            if feature["session"] != session["session"] or feature["writer"] != session["writer"]:
                raise ValueError("feature identity mismatch")
            options = feature["options"]
            if not options or len(options) != len(row["menu"]):
                raise ValueError("feature menu support mismatch")
            metadata.append(dict(key=row["key"], writer=session["writer"], session=session["session"],
                                 prompt=session["prompt"], outcome=ACTIONS.index(row["handling"])))
            contexts.append(vectors[feature["context"]])
            menus.append(np.asarray(vectors[options], dtype=np.float64).mean(axis=0))
    if seen != set(records_by_key):
        raise ValueError("features and frozen decisions have different support")
    return metadata, normalized(contexts), normalized(menus)


def match_pairs(metadata, contexts, menus, block_size=256):
    """Exact bounded-memory cosine search; each unordered pair appears once."""
    if block_size < 1:
        raise ValueError("invalid matching block size")
    left, right, similarity = [], [], []
    prompts = sorted({row["prompt"] for row in metadata})
    for prompt in prompts:
        group = np.asarray([i for i, row in enumerate(metadata) if row["prompt"] == prompt], dtype=np.int32)
        for start in range(0, len(group), block_size):
            ids = group[start:start + block_size]
            context_cos = contexts[ids] @ contexts[group].T
            menu_cos = menus[ids] @ menus[group].T
            score = np.minimum(context_cos, menu_cos)
            mask = (score >= min(EPSILONS)) & (ids[:, None] < group[None, :])
            a, b = np.nonzero(mask)
            left.append(ids[a]); right.append(group[b]); similarity.append(score[a, b])
    return dict(left=np.concatenate(left) if left else np.empty(0, np.int32),
                right=np.concatenate(right) if right else np.empty(0, np.int32),
                similarity=np.concatenate(similarity) if similarity else np.empty(0, np.float64))


def encode_metadata(metadata):
    writers = sorted({row["writer"] for row in metadata})
    sessions = sorted({row["session"] for row in metadata})
    writer_index = {value: i for i, value in enumerate(writers)}
    session_index = {value: i for i, value in enumerate(sessions)}
    wi = np.asarray([writer_index[row["writer"]] for row in metadata], dtype=int)
    si = np.asarray([session_index[row["session"]] for row in metadata], dtype=int)
    sw = np.full(len(sessions), -1, dtype=int)
    for w, s in zip(wi, si):
        if sw[s] not in (-1, w):
            raise ValueError("session assigned to more than one writer")
        sw[s] = w
    truth = np.asarray([row["outcome"] for row in metadata], dtype=int)
    return writers, wi, si, sw, truth


def agreement_summary(left, right, equal, wi, si):
    same_writer = wi[left] == wi[right]
    same_session = si[left] == si[right]
    within = same_writer & ~same_session
    between = ~same_writer & ~same_session
    transient = same_writer & same_session
    def mean(mask):
        return float(equal[mask].mean()) if mask.any() else None
    aw, ab, at = mean(within), mean(between), mean(transient)
    return dict(A_w=aw, A_b=ab, A_same_session=at,
                personal_floor=None if aw is None else .5 * (1 - aw),
                pooled_floor=None if ab is None else .5 * (1 - ab),
                H=None if aw is None or ab is None else .5 * (aw - ab),
                transient_agreement=None if aw is None or at is None else at - aw,
                pairs_within=int(within.sum()), pairs_between=int(between.sum()),
                pairs_same_session=int(transient.sum()),
                writers_within=int(len(np.unique(wi[left[within]]))),
                writers_between=int(len(np.unique(np.r_[wi[left[between]], wi[right[between]]]))))


def bootstrap_intervals(left, right, equal, wi, si, writers, draws, seed):
    """Resample nodes of the dyadic pair graph, preserving within-writer blocks."""
    nw = len(writers)
    if nw < 2 or draws < 100:
        raise ValueError("at least two writers and 100 bootstrap draws required")
    same_session = si[left] == si[right]
    same = (wi[left] == wi[right]) & ~same_session
    other = (wi[left] != wi[right]) & ~same_session
    wc = np.bincount(wi[left[same]], minlength=nw).astype(float)
    wy = np.bincount(wi[left[same]], weights=equal[same], minlength=nw)
    index = wi[left[other]] * nw + wi[right[other]]
    bc = np.bincount(index, minlength=nw * nw).reshape(nw, nw)
    by = np.bincount(index, weights=equal[other], minlength=nw * nw).reshape(nw, nw)
    rng = np.random.default_rng(seed)
    multiplicities = rng.multinomial(nw, np.full(nw, 1 / nw), size=draws)
    wd = multiplicities @ wc
    bd = np.einsum("bi,ij,bj->b", multiplicities, bc, multiplicities, optimize=True)
    good = (wd > 0) & (bd > 0)
    if good.mean() < .95:
        return dict(interval95=None, reason="fewer than 95% supported writer bootstrap draws",
                    supported_draws=int(good.sum()), draws=draws)
    aw = (multiplicities @ wy)[good] / wd[good]
    ab = np.einsum("bi,ij,bj->b", multiplicities, by, multiplicities, optimize=True)[good] / bd[good]
    values = dict(A_w=aw, A_b=ab, personal_floor=.5 * (1 - aw), pooled_floor=.5 * (1 - ab), H=.5 * (aw - ab))
    return dict(interval95={key: np.quantile(value, [.025, .975]).tolist() for key, value in values.items()},
                supported_draws=int(good.sum()), draws=draws, seed=seed,
                method="writer node bootstrap; within edges weighted once, cross-writer edges by product")


def summarize(metadata, pairs, config):
    writers, wi, si, sw, truth = encode_metadata(metadata)
    left, right = pairs["left"], pairs["right"]
    if any(len(pairs[key]) != len(left) for key in ("right", "similarity")):
        raise ValueError("unaligned saved pair graph")
    if np.any(left >= right) or np.any(left < 0) or np.any(right >= len(metadata)):
        raise ValueError("invalid pair index/order")
    if not np.isfinite(pairs["similarity"]).all():
        raise ValueError("nonfinite pair similarities")
    equal = (truth[left] == truth[right]).astype(float)
    seed = int(config.get("seed", 20261017)); draws = int(config.get("bootstrap_draws", 2000))
    shuffles = int(config.get("shuffles", 200))
    if shuffles != 200:
        raise ValueError("V5 requires the frozen 200 session-label shuffles")
    curves = []
    for epsilon in EPSILONS:
        mask = pairs["similarity"] >= epsilon
        a, b, agree = left[mask], right[mask], equal[mask]
        point = agreement_summary(a, b, agree, wi, si)
        if point["H"] is not None and point["writers_within"] >= 2:
            intervals = bootstrap_intervals(a, b, agree, wi, si, writers, draws, seed)
        else:
            intervals = dict(interval95=None, reason="insufficient matched writer support", supported_draws=0, draws=draws)
        rng = np.random.default_rng(seed + 1)
        control = []
        for _ in range(shuffles):
            shuffled_writers = rng.permutation(sw)[si]
            control.append(agreement_summary(a, b, agree, shuffled_writers, si)["H"])
        usable = np.asarray([value for value in control if value is not None])
        controls = dict(draws=shuffles, supported_draws=len(usable),
                        mean=float(usable.mean()) if len(usable) else None,
                        interval95=np.quantile(usable, [.025, .975]).tolist() if len(usable) else None,
                        values=control,
                        p_upper=(1 + int(np.sum(usable >= point["H"]))) / (1 + len(usable))
                        if len(usable) and point["H"] is not None else None)
        curves.append(dict(epsilon=epsilon, **point, bootstrap=intervals, writer_shuffle=controls))
    primary = next(row for row in curves if row["epsilon"] == .8)
    interval = primary["bootstrap"]["interval95"]
    if interval is None:
        state, route = "invalid", "undetermined"
        ci = None
    else:
        ci = interval["H"]
        state = states.classify(primary["H"], ci[0], ci[1])
        route = "near_zero" if ci[1] < .005 else "personal_headroom" if ci[0] > 0 else "undetermined"
    return dict(card="V5", question="How much handling prediction remains for a personal reader?",
                descriptive=True, state=state, route=route,
                primary=dict(estimate=primary["H"], interval95=ci, epsilon=.8, direction="positive"),
                curves=curves, writers=len(writers), decisions=len(metadata),
                matching="all unordered same-prompt pairs, normalized context and normalized mean-menu cosine",
                weighting="matched pairs; writer-cluster uncertainty",
                caveat="Near-repeat agreements are matcher-conditional proxies. Differences in contexts or matched writer populations can change both floors.")


def gain_shares(gain, population_brier, personal_floor, headroom, headroom_upper=None):
    """A nonpositive or unavailable denominator never becomes a ratio."""
    available = population_brier - personal_floor if personal_floor is not None else None
    def ratio(denominator):
        return float(gain / denominator) if denominator is not None and denominator > 0 else None
    return dict(gain=float(gain), share_of_population_to_personal_floor=ratio(available),
                share_of_personal_headroom=ratio(headroom),
                share_using_headroom_upper=ratio(headroom_upper),
                nonpositive_denominators="undefined")


def execute(output: Path, inputs: dict, config: dict) -> dict:
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    vectors = np.load(inputs["vectors"], mmap_mode="r", allow_pickle=False)
    metadata, contexts, menus = decision_table(read(inputs["sessions"]), read(inputs["records"]), vectors)
    pairs = match_pairs(metadata, contexts, menus, int(config.get("block_size", 256)))
    write(output / "DECISIONS.json", metadata)
    with (output / "PAIRS.npz").open("xb") as stream:
        np.savez_compressed(stream, **pairs)
    report = summarize(metadata, pairs, config)
    report["input_hashes"] = input_hashes(inputs)
    report["intermediate_hashes"] = {name: sha256(output / name) for name in ("DECISIONS.json", "PAIRS.npz")}
    write(output / "SUMMARY.json", report)
    return report


def verify(output: Path, inputs: dict, config: dict) -> dict:
    output = Path(output); report = read(output / "SUMMARY.json")
    assert_equal(report["input_hashes"], input_hashes(inputs))
    for name, expected in report["intermediate_hashes"].items():
        if sha256(output / name) != expected:
            raise ValueError("saved matching intermediate changed")
    with np.load(output / "PAIRS.npz", allow_pickle=False) as values:
        pairs = {key: values[key] for key in values.files}
    recomputed = summarize(read(output / "DECISIONS.json"), pairs, config)
    assert_equal({key: report[key] for key in recomputed}, recomputed)
    return dict(verified=True, primary_recomputed=recomputed["primary"], state=recomputed["state"])
