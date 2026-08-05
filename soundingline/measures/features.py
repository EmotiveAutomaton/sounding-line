"""Off-the-shelf linguistic features — the population this project never had.

── WHY ───────────────────────────────────────────────────────────────────────────────────────

Ten measures were hand-written and ten died. `docs/design/ENGINEERING_LOOP.md` names the cause:
**a search with a population size of one.** Meanwhile the evaluator — length, echo, construction,
transfer, no-maker, rung -1, positive control — was already built and runs in minutes.

This module supplies candidates instead of inventing them:

    LFTK              220 handcrafted features (lexical, syntactic, readability, semantic)
    BiberPlus          96 Biber tags (grammatical/stylistic register features)
    TextDescriptives   descriptive stats, readability indices, syntactic complexity

**~350 candidates, none of them ours, all of them already validated in the literature.**

── THE MANDATORY PAIRING ─────────────────────────────────────────────────────────────────────

**Never score these without false-discovery control.** 350 features at p < 0.05 produce ~18 false
positives by construction, and known weakness 1 in `FINDINGS.md` is that we have never corrected
for multiple comparisons at all. Use `soundingline.measures.select.significant()`, which wraps
tsfresh's Benjamini-Yekutieli procedure. Installing the features without the correction would be
strictly worse than having neither.

── KNOWN PACKAGE BUG (Windows) ───────────────────────────────────────────────────────────────

BiberPlus builds its dictionary keys from **file paths**, so on Windows the key is
`constants\\function_words` while `load_tags()` looks up `function_words`, and every call raises
`KeyError`. `_biber_config()` below works around it by resolving the key by suffix and passing the
list in explicitly. Filed here rather than patched in site-packages so the workaround survives a
reinstall.
"""

from __future__ import annotations

import functools
import re
from typing import Any

_WS = re.compile(r"\s+")
MAX_CHARS = 20_000          # spaCy default max is 1e6, but these are O(n) and we window anyway


# ── lazy singletons: loading spaCy per call would dominate the runtime ────────────────────────

@functools.lru_cache(maxsize=1)
def _nlp():
    import spacy                                                     # noqa: PLC0415
    return spacy.load("en_core_web_sm")


@functools.lru_cache(maxsize=1)
def _patch_biber_paths() -> None:
    """BiberPlus keys its constant dictionaries by FILE PATH, so on Windows every lookup fails.

    `build_variable_dictionaries()` returns `{'constants\\\\quantifiers': [...], ...}` while the
    tagger asks for `'quantifiers'`. Worse, `calculate_tag_frequencies` wraps the whole body in a
    bare `except`, prints the input text and the KeyError, and **returns None** — so the failure is
    silent unless you check the return type.

    Patched at the source rather than worked around per-key, because the bug affects all ~40
    constant lists. Both the basename and the original key are kept so nothing that happens to work
    on POSIX breaks here.
    """
    from biberplus.tagger import tagger_utils                        # noqa: PLC0415

    orig = tagger_utils.build_variable_dictionaries

    @functools.wraps(orig)
    def patched(*a: Any, **k: Any):
        d = orig(*a, **k)
        for key in list(d):
            base = key.replace("\\", "/").split("/")[-1]
            d.setdefault(base, d[key])
        return d

    patched._sl_patched = True                                       # noqa: SLF001
    if getattr(tagger_utils.build_variable_dictionaries, "_sl_patched", False):
        return
    tagger_utils.build_variable_dictionaries = patched

    # At least four submodules do `from ... import build_variable_dictionaries` at module scope
    # (tagger, tag_frequencies, function_words_tagger, biber_plus_tagger), so rebinding one is not
    # enough. Walk the whole package and rebind wherever the symbol is held.
    import importlib                                                 # noqa: PLC0415
    import pkgutil                                                   # noqa: PLC0415
    import biberplus                                                 # noqa: PLC0415

    for info in pkgutil.walk_packages(biberplus.__path__, "biberplus."):
        try:
            m = importlib.import_module(info.name)
        except Exception:                                            # noqa: BLE001
            continue
        if getattr(m, "build_variable_dictionaries", None) is orig:
            m.build_variable_dictionaries = patched


@functools.lru_cache(maxsize=1)
def _biber():
    _patch_biber_paths()
    from biberplus.tagger import load_config, load_pipeline          # noqa: PLC0415

    cfg = load_config()
    cfg.update({"biber": True, "function_words": True,
                "use_gpu": False, "token_normalization": 100})
    return load_pipeline(cfg), cfg


def lftk_features(text: str) -> dict[str, float]:
    """220 handcrafted features. Returns {} rather than raising, so one bad text cannot kill a run."""
    try:
        import lftk                                                  # noqa: PLC0415
        doc = _nlp()(text[:MAX_CHARS])
        ex = lftk.Extractor(docs=doc)
        ex.customize(stop_words=True, punctuations=False, round_decimal=6)
        return {f"lftk_{k}": float(v) for k, v in ex.extract().items()
                if isinstance(v, (int, float))}
    except Exception:                                                # noqa: BLE001
        return {}


def biber_features(text: str) -> dict[str, float]:
    """Biber tags as rates per 1,000 tokens.

    **We aggregate ourselves rather than calling `calculate_tag_frequencies`.** BiberPlus's tagger
    works; its aggregation does not — `update_tag_counts` does `tagged_df.tags` on what pandas 3
    hands it as a bare ndarray, and the enclosing bare `except` turns that into a silent `None`.

    Counting from `tag_text` output is about ten lines, avoids the incompatibility entirely, and
    means the normalisation is ours and matches the rest of this repository (rates per 1,000 tokens,
    as in `measures/leakage.py`) instead of BiberPlus's per-100-token windows.
    """
    try:
        _patch_biber_paths()
        from biberplus.tagger import tag_text                        # noqa: PLC0415
        from biberplus.tagger.constants import BIBER_PLUS_TAGS       # noqa: PLC0415
        from collections import Counter                              # noqa: PLC0415

        pipe, cfg = _biber()
        words = tag_text(text[:MAX_CHARS], pipe, cfg)
        if not words:
            return {}
        counts: Counter = Counter()
        for w in words:
            for t in (w.get("tags") or ()):
                counts[t] += 1
        n = len(words)
        known = set(BIBER_PLUS_TAGS) if BIBER_PLUS_TAGS else set(counts)
        return {f"biber_{t}": 1000.0 * counts.get(t, 0) / n for t in sorted(known)}
    except Exception:                                                # noqa: BLE001
        return {}


def textdesc_features(text: str) -> dict[str, float]:
    """Readability indices, descriptive statistics, syntactic complexity."""
    try:
        import textdescriptives as td                                # noqa: PLC0415
        nlp = _nlp()
        for c in ("textdescriptives/descriptive_stats",
                  "textdescriptives/readability",
                  "textdescriptives/dependency_distance"):
            if c not in nlp.pipe_names:
                nlp.add_pipe(c)
        doc = nlp(text[:MAX_CHARS])
        d = td.extract_dict(doc)[0]
        return {f"td_{k}": float(v) for k, v in d.items()
                if isinstance(v, (int, float)) and k != "text"}
    except Exception:                                                # noqa: BLE001
        return {}


def extract(text: str, sources: tuple[str, ...] = ("lftk", "biber", "td")) -> dict[str, float]:
    """Every available feature for one text, as a flat dict with source-prefixed keys.

    Each source is independent: if one is unavailable or throws, the others still return. That is
    deliberate — a 350-feature sweep should not die because one package dislikes one artifact.
    """
    out: dict[str, float] = {}
    if "lftk" in sources:
        out.update(lftk_features(text))
    if "biber" in sources:
        out.update(biber_features(text))
    if "td" in sources:
        out.update(textdesc_features(text))
    return out


def extract_many(texts: list[str], **kw: Any) -> tuple[list[str], list[list[float]]]:
    """Feature matrix over a corpus, restricted to features present and finite for EVERY text.

    Dropping partial features is the conservative choice: a feature defined on only some artifacts
    would otherwise let corpus composition leak into a comparison.
    """
    import math                                                      # noqa: PLC0415
    rows = [extract(t, **kw) for t in texts]
    if not rows:
        return [], []
    keys = sorted(set.intersection(*(set(r) for r in rows)))
    keys = [k for k in keys if all(math.isfinite(r[k]) for r in rows)]
    return keys, [[r[k] for k in keys] for r in rows]
