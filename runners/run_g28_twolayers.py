"""G28 — do the leaked and emblematic layers come back as two distributions, or one?

The standing caveat over the whole leak battery (DECISION_TRACES §3): "until this runs, every
leak result is equally compatible with the probe asking one question twice." Three arms per
text, the local reader distributing 100 points over the eight concepts:

    leaked      the affect the maker did NOT choose to display, carried in habit and style
    emblematic  the affect the maker deliberately performed for the reader
    leaked2     the leaked prompt again at a different seed, the test-retest ceiling

The estimand: mean per-text profile correlation r(leaked, emblematic), judged against
r(leaked, leaked2). One question twice predicts the two are equal; two real layers predicts
between-layer r sits clearly below test-retest r. Paired bootstrap CI on the difference.

Lessons applied (LESSONS §3): the null is built in as the third arm rather than assumed;
checkpointed partials so a kill loses nothing; denominators are texts, not words.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

OUT = REPO / "results" / "g28_twolayers"
OLLAMA = "http://127.0.0.1:11434/api/generate"
CONCEPTS = ["seeking", "rage", "fear", "lust", "care", "panic_grief", "play",
            "none_recoverable"]

PROMPTS = {
    "leaked": ("Read the passage as evidence about its maker. Estimate the affect the maker "
               "did NOT choose to display: what leaks through habit, style, pacing, and "
               "attention, the involuntary layer."),
    "emblematic": ("Read the passage as evidence about its maker. Estimate the affect the "
                   "maker DELIBERATELY performed for the reader: the chosen, social, "
                   "displayed layer."),
}


def ask(text: str, which: str, seed: int) -> dict | None:
    prompt = (f"{PROMPTS[which]}\n\nDistribute exactly 100 points over these eight "
              f"categories: {', '.join(CONCEPTS)}. Passage:\n---\n{text[:4000]}\n---\n"
              f"Answer with ONLY a JSON object mapping each category to an integer.")
    req = urllib.request.Request(OLLAMA, data=json.dumps(
        {"model": "qwen3.5:9b", "prompt": prompt, "stream": False, "think": False,
         "format": "json",
         "options": {"temperature": 0.3, "seed": seed, "num_predict": 200}}).encode(),
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            raw = json.loads(r.read()).get("response", "")
        d = json.loads(raw)
        v = [max(0.0, float(d.get(c, 0))) for c in CONCEPTS]
        s = sum(v)
        return {c: x / s for c, x in zip(CONCEPTS, v)} if s > 0 else None
    except Exception:                                                  # noqa: BLE001
        return None


def load_texts() -> list[dict]:
    """Five 4,000-char mid-book segments from each manifest book, straight from the store
    (the feature cache's segment ids collide across books of one author, verified 2026-08-11,
    so the cache is not a usable text index)."""
    from runners.run_author_convergence import store_lookup            # noqa: PLC0415
    man = json.loads((REPO / "corpora" / "manifests" / "books.json")
                     .read_text(encoding="utf-8"))
    lut = store_lookup()
    out = []
    chunk = 4000
    for m in man["items"]:
        p = (lut.get(m.get("url")) or lut.get(m.get("final_url"))
             or REPO / "corpora" / "store" / f"{m['id']}.txt")
        if not p.exists():
            continue
        txt = p.read_text(encoding="utf-8", errors="replace")
        start = len(txt) // 4                    # skip front matter
        for k in range(5):
            seg = txt[start + k * chunk: start + (k + 1) * chunk]
            if len(seg.split()) >= 150:
                out.append({"id": f"{m['id']}#s{k}", "text": seg})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=150)
    args = ap.parse_args()
    import numpy as np                                                # noqa: PLC0415
    from scipy import stats                                           # noqa: PLC0415

    from soundingline.gpulock import acquire_gpu_lock                 # noqa: PLC0415
    acquire_gpu_lock("g28:ollama")

    texts = load_texts()[: args.n]
    if len(texts) < 40:
        print(f">>> VOID: only {len(texts)} usable texts")
        sys.exit(1)
    print(f"{len(texts)} texts, three arms each", flush=True)

    OUT.mkdir(parents=True, exist_ok=True)
    part = OUT / "partial.jsonl"
    done: dict[tuple, dict] = {}
    if part.exists():
        for line in part.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            done[(r["id"], r["arm"])] = r
    arms = [("leaked", 100), ("emblematic", 200), ("leaked2", 300)]
    with part.open("a", encoding="utf-8", newline="\n") as fh:
        for i, it in enumerate(texts):
            for arm, base_seed in arms:
                if (it["id"], arm) in done:
                    continue
                which = "leaked" if arm == "leaked2" else arm
                prof = ask(it["text"], which, base_seed + i)
                if prof is None:
                    continue
                rec = {"id": it["id"], "arm": arm, "profile": prof}
                fh.write(json.dumps(rec) + "\n")
                fh.flush()
                done[(it["id"], arm)] = rec
            if (i + 1) % 20 == 0:
                print(f"  {i + 1}/{len(texts)} texts", flush=True)

    ids = [t["id"] for t in texts
           if all((t["id"], a) in done for a, _ in arms)]
    if len(ids) < 40:
        print(f">>> VOID: only {len(ids)} complete triples")
        sys.exit(1)

    def prof(i, arm):
        import numpy as _np
        return _np.array([done[(i, arm)]["profile"][c] for c in CONCEPTS])

    r_between = np.array([stats.pearsonr(prof(i, "leaked"),
                                         prof(i, "emblematic")).statistic for i in ids])
    r_retest = np.array([stats.pearsonr(prof(i, "leaked"),
                                        prof(i, "leaked2")).statistic for i in ids])
    diff = r_retest - r_between
    boot = []
    rng = np.random.default_rng(28)
    for _ in range(5000):
        idx = rng.integers(0, len(ids), len(ids))
        boot.append(float(np.mean(diff[idx])))
    lo, hi = np.percentile(boot, [2.5, 97.5])

    if lo > 0.05:
        verdict = "TWO-LAYERS"
    elif hi < 0.05:
        verdict = "ONE-QUESTION-TWICE"
    else:
        verdict = "UNDECIDED"
    out = {"n_texts": len(ids), "mean_r_between": round(float(np.mean(r_between)), 3),
           "mean_r_retest": round(float(np.mean(r_retest)), 3),
           "mean_diff": round(float(np.mean(diff)), 3),
           "diff_ci95": [round(float(lo), 3), round(float(hi), 3)],
           "verdict": verdict}
    (OUT / "summary.json").write_text(json.dumps(out, indent=1),
                                      encoding="utf-8", newline="\n")
    print(f"between-layer r {out['mean_r_between']}, test-retest r {out['mean_r_retest']}, "
          f"diff {out['mean_diff']} CI {out['diff_ci95']}\n  >>> {verdict}")
    print(f"wrote {(OUT / 'summary.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
