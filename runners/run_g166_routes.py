"""G166 (Phase 2.3 root P23-B0-near construction) — the route-varied process-recorded
corpus: the same topic reached through five distinct recorded production routes, so the
equifinality root can ask whether any reader separates routes from final artifacts that
were surface-matched by construction.

FIVE ROUTES, every intermediate recorded as ProcessEvents (soundingline/process_record):
    direct        one-shot essay from the brief
    outline       five-point outline first, then realization following it
    rewrite       full rewrite of the recorded G131 base draft (the draft is a prior
                  recorded artifact, actor logged as the base lineage)
    select        three candidate theses proposed, one selected by SEEDED MECHANICAL
                  draw (selection + rejections recorded with alternatives), essay
                  committed to the selected thesis
    revise        draft, then explicit two-weakness self-critique and full revision

Surface matching by construction: identical topic briefs (the G131 topic set), identical
register instruction, identical length band. What varies is the recorded route only.

DESIGN CHECK (2026-08-21, at design time). Lessons read: LESSONS §3 (ruler-first — the
corpus self-audits on mechanically decidable properties before any reading battery
preregisters; assigned-is-not-realized — route logs record what HAPPENED, and the audit
verifies structural compliance), §5 complete (produces guards, yield guard at 90% with
the manifest withheld below it, retry-with-backoff on every ollama call, deterministic
seeds SEED0 + indices recorded per artifact, append-at-end queueing). Audit gates, each
with null and alternative and the failure direction:
    YIELD >= 0.90 per family (null: compliant generation passes; alternative: parse or
      band failures thin the corpus, direction DOWN, manifest refused — a thin corpus
      frozen behind a produces guard is the named lesson).
    BAND: every accepted essay inside 300-700 words (hard, by construction at accept
      time; the audit re-verifies against drift, direction: any violation refuses).
    LOG COMPLETENESS: every case validates under the ProcessCase schema AND carries its
      route's required operations (outline: outline+realize; select: propose+select+
      reject x2; revise: critique+revise; rewrite: revise with the base as parent).
      Null: complete by construction; alternative: a silent parse failure dropped an
      intermediate, direction DOWN, refused — a route corpus without its recorded
      route is worthless.
    DEGENERACY: within one family+topic, no essay pair across routes with content-word
      Jaccard > 0.90 (null: ~0 pairs; alternative: seeded collapse or model laziness
      produces near-identical texts across routes, direction UP, refused — equifinality
      is only a question when the routes actually produced distinguishable texts by
      accident rather than by trivial identity).
    SURFACE REPORT (report-only, no gate): per-route length and lexical means, so any
      gross surface separation is visible BEFORE the reading battery preregisters its
      surface-matched baseline; the binding cheap-baseline contest belongs to that
      card, not this audit.
The reading battery (B0-near reading, B0-exact equivalence arms) preregisters ONLY on
CORPUS-STANDS, in its own card, per the G162 precedent.

Outputs: corpora/g166_routes/{family}/{route}_{ti:02d}.json + manifest_{family}.json;
--audit writes corpora/g166_routes/routes_audit.json and exits 1 on any gate failure.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUTROOT = REPO / "corpora" / "g166_routes"
OLLAMA = "http://127.0.0.1:11434/api/generate"
GENERATORS = {"qwen": "qwen3.5:9b", "llama": "llama3.1:8b"}
SEED0 = 16600
BAND = (300, 700)
TRIES = 3
ROUTES = ("direct", "outline", "rewrite", "select", "revise")

sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "runners"))
from run_g131_gen import TOPICS                                        # noqa: E402
from run_g162_gen import load_base                                     # noqa: E402
from soundingline.process_record import ProcessCase, ProcessEvent      # noqa: E402

BRIEF = ("Write a short argumentative essay of 400 to 600 words on the question: "
         "{topic} Plain prose, no headings, no lists.")

OUTLINE_P = ("Plan a short argumentative essay on the question: {topic} Give exactly "
             "five numbered outline points, one line each. The outline only, nothing "
             "else.")

REALIZE_P = ("Write a short argumentative essay of 400 to 600 words on the question: "
             "{topic} Follow this outline exactly, in order. Plain prose, no headings, "
             "no lists.\n\nOUTLINE:\n{outline}")

REWRITE_P = ("Rewrite the following draft essay into a stronger version. Keep its "
             "content and position; improve the structure and clarity. 400 to 600 "
             "words, plain prose, no headings.\n\nDRAFT:\n{base}")

THESES_P = ("Propose three distinct thesis statements a short argumentative essay on "
            "the question below could defend. Number them 1 to 3, one sentence each, "
            "nothing else.\n\nQUESTION: {topic}")

COMMIT_P = ("Write a short argumentative essay of 400 to 600 words on the question: "
            "{topic} The essay must be committed to exactly this thesis: {thesis} "
            "Plain prose, no headings, no lists.")

CRITIQUE_P = ("Here is a draft essay. First list exactly two weaknesses as two "
              "numbered lines. Then write the single word REVISED: on its own line, "
              "followed by the full revised essay of 400 to 600 words, plain prose, "
              "no headings.\n\nDRAFT:\n{draft}")


def call_gen(model, prompt, seed, num_predict=1400):
    req = urllib.request.Request(OLLAMA, data=json.dumps(
        {"model": model, "prompt": prompt, "stream": False, "think": False,
         "options": {"temperature": 0.8, "top_p": 0.95, "top_k": 40,
                     "repeat_penalty": 1.1, "num_predict": num_predict,
                     "seed": int(seed)}}).encode(),
        headers={"Content-Type": "application/json"})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=900) as r:
                resp = json.loads(r.read()).get("response", "")
            return re.sub(r"<think>.*?</think>", "", resp, flags=re.DOTALL).strip()
        except Exception as e:                                        # noqa: BLE001
            print(f"  gen failed (attempt {attempt + 1}): {e}")
            time.sleep(20 * (attempt + 1))
    return None


def wc(t):
    return len(re.findall(r"[A-Za-z']+", t or ""))


def in_band(t):
    return BAND[0] <= wc(t) <= BAND[1]


def parse_theses(t):
    lines = [ln.strip() for ln in (t or "").splitlines() if ln.strip()]
    out = []
    for ln in lines:
        m = re.match(r"^[1-3][.)]\s*(.+)$", ln)
        if m:
            out.append(m.group(1).strip())
    return out if len(out) == 3 else None


def parse_revision(t):
    if not t or "REVISED:" not in t:
        return None, None
    head, _, tail = t.partition("REVISED:")
    crit = [ln.strip() for ln in head.splitlines()
            if re.match(r"^[12][.)]\s*\S", ln.strip())]
    essay = tail.strip()
    return (crit if len(crit) == 2 else None), essay


def make_case(gen, route, ti, seed, events, text, intermediates):
    case = ProcessCase(
        case_id=f"{gen}_{route}_{ti:02d}", lineage_id=f"g166_{gen}_{ti:02d}",
        domain="argumentative_essay", medium="text", brief_id=f"g131_topic_{ti:02d}",
        declared_context={"brief": BRIEF.format(topic=TOPICS[ti]),
                          "register": "plain argumentative prose",
                          "length_band_words": list(BAND)},
        participants={gen: "local_model",
                      **({"g131_base": "recorded_prior_artifact"}
                         if route == "rewrite" else {})},
        route_family=route, events=events, artifact_final=text,
        artifact_versions=intermediates,
        near_equivalence_group=f"{gen}_{ti:02d}",
        construction_seed=seed)
    case.validate()
    return case


def build_route(gen, model, route, ti, seed):
    """Returns (case, n_calls) or (None, n_calls) on failure. Every intermediate is a
    ProcessEvent with its verbatim payload."""
    topic = TOPICS[ti]
    ev, versions = [], []
    if route == "direct":
        text = call_gen(model, BRIEF.format(topic=topic), seed)
        if not (text and in_band(text)):
            return None, 1
        ev.append(ProcessEvent("e1", 0, gen, "realize_surface", target="essay",
                               visible_in_final="yes"))
        return make_case(gen, route, ti, seed, ev, text, versions), 1

    if route == "outline":
        outline = call_gen(model, OUTLINE_P.format(topic=topic), seed, num_predict=300)
        if not outline:
            return None, 1
        text = call_gen(model, REALIZE_P.format(topic=topic, outline=outline), seed + 1)
        if not (text and in_band(text)):
            return None, 2
        ev.append(ProcessEvent("e1", 0, gen, "outline", target="plan",
                               visible_in_final="partial",
                               payload={"outline": outline}))
        ev.append(ProcessEvent("e2", 1, gen, "realize_surface", target="essay",
                               parent_event_ids=["e1"], visible_in_final="yes"))
        return make_case(gen, route, ti, seed, ev, text, [outline]), 2

    if route == "rewrite":
        base = load_base(gen, ti)["text"]
        text = call_gen(model, REWRITE_P.format(base=base), seed)
        if not (text and in_band(text)):
            return None, 1
        ev.append(ProcessEvent("e1", 0, "g131_base", "propose", target="draft",
                               visible_in_final="partial",
                               payload={"base_ref": f"g131 {gen} none_0_none_{ti:02d}"}))
        ev.append(ProcessEvent("e2", 1, gen, "revise", target="essay",
                               parent_event_ids=["e1"], visible_in_final="yes"))
        return make_case(gen, route, ti, seed, ev, text, [base]), 1

    if route == "select":
        theses_raw = call_gen(model, THESES_P.format(topic=topic), seed,
                              num_predict=250)
        theses = parse_theses(theses_raw)
        if not theses:
            return None, 1
        import numpy as np
        pick = int(np.random.default_rng(seed).integers(3))
        text = call_gen(model, COMMIT_P.format(topic=topic, thesis=theses[pick]),
                        seed + 1)
        if not (text and in_band(text)):
            return None, 2
        ev.append(ProcessEvent("e1", 0, gen, "propose", target="theses",
                               visible_in_final="partial",
                               payload={"candidates": theses}))
        ev.append(ProcessEvent("e2", 1, "seeded_draw", "select",
                               target=f"thesis_{pick}", parent_event_ids=["e1"],
                               alternatives=[t for j, t in enumerate(theses)
                                             if j != pick],
                               payload={"selected": theses[pick], "draw_seed": seed}))
        for j, t in enumerate(theses):
            if j != pick:
                ev.append(ProcessEvent(f"e3_{j}", 2, "seeded_draw", "reject",
                                       target=f"thesis_{j}",
                                       parent_event_ids=["e2"],
                                       payload={"rejected": t}))
        ev.append(ProcessEvent("e4", 3, gen, "realize_surface", target="essay",
                               parent_event_ids=["e2"], visible_in_final="yes"))
        return make_case(gen, route, ti, seed, ev, text, [theses_raw]), 2

    if route == "revise":
        draft = call_gen(model, BRIEF.format(topic=topic), seed)
        if not (draft and in_band(draft)):
            return None, 1
        out = call_gen(model, CRITIQUE_P.format(draft=draft), seed + 1,
                       num_predict=1600)
        crit, text = parse_revision(out)
        if not (crit and text and in_band(text)):
            return None, 2
        ev.append(ProcessEvent("e1", 0, gen, "realize_surface", target="draft",
                               visible_in_final="partial"))
        ev.append(ProcessEvent("e2", 1, gen, "critique", target="draft",
                               parent_event_ids=["e1"],
                               payload={"weaknesses": crit}))
        ev.append(ProcessEvent("e3", 2, gen, "revise", target="essay",
                               parent_event_ids=["e2"], visible_in_final="yes"))
        return make_case(gen, route, ti, seed, ev, text, [draft]), 2
    raise ValueError(route)


def generate(gen):
    from soundingline.gpulock import acquire_gpu_lock                  # noqa: PLC0415
    acquire_gpu_lock(f"g166_gen_{gen}")
    model = GENERATORS[gen]
    outdir = OUTROOT / gen
    outdir.mkdir(parents=True, exist_ok=True)
    made, attempted = 0, 0
    for ti in range(len(TOPICS)):
        for fi, route in enumerate(ROUTES):
            dest = outdir / f"{route}_{ti:02d}.json"
            if dest.exists():
                made += 1
                continue
            attempted += 1
            case = None
            for tr in range(TRIES):
                seed = SEED0 + ti * 1000 + fi * 20 + tr * 2
                case, _ = build_route(gen, model, route, ti, seed)
                if case:
                    break
            if case:
                d = case.to_dict()
                d["generator"] = gen
                d["word_count"] = wc(case.artifact_final)
                dest.write_text(json.dumps(d, indent=1), encoding="utf-8",
                                newline="\n")
                made += 1
                print(f"  {gen} {route} {ti:02d} ok ({d['word_count']}w)")
            else:
                print(f"  {gen} {route} {ti:02d} FAILED after {TRIES} tries")
    total = len(TOPICS) * len(ROUTES)
    if made < 0.9 * total:
        print(f"THIN YIELD {gen}: {made}/{total} — manifest withheld (LESSONS §5)")
        sys.exit(1)
    man = {"generator": gen, "model": model, "seed0": SEED0, "routes": list(ROUTES),
           "n_topics": len(TOPICS), "made": made, "total": total,
           "band": list(BAND)}
    (OUTROOT / f"manifest_{gen}.json").write_text(json.dumps(man, indent=1),
                                                  encoding="utf-8", newline="\n")
    print(f"{gen}: {made}/{total} artifacts, manifest written")


REQUIRED_OPS = {"direct": {"realize_surface"},
                "outline": {"outline", "realize_surface"},
                "rewrite": {"propose", "revise"},
                "select": {"propose", "select", "reject", "realize_surface"},
                "revise": {"realize_surface", "critique", "revise"}}


def audit():
    from itertools import combinations
    gates, surface = {}, {}
    all_cases = {}
    for gen in GENERATORS:
        for p in sorted((OUTROOT / gen).glob("*.json")):
            all_cases[(gen, p.stem)] = json.loads(p.read_text(encoding="utf-8"))
    total_expected = len(GENERATORS) * len(TOPICS) * len(ROUTES)
    gates["yield"] = {"made": len(all_cases), "expected": total_expected,
                      "pass": len(all_cases) >= 0.9 * total_expected}
    band_bad = [k for k, c in all_cases.items()
                if not (BAND[0] <= c["word_count"] <= BAND[1])]
    gates["band"] = {"violations": len(band_bad), "pass": not band_bad}
    log_bad = []
    for k, c in all_cases.items():
        ops = {e["operation"] for e in c["events"]}
        need = REQUIRED_OPS[c["route_family"]]
        if not need <= ops:
            log_bad.append("_".join(k))
    gates["log_completeness"] = {"violations": log_bad, "pass": not log_bad}

    def cwords(t):
        return {w.lower() for w in re.findall(r"[A-Za-z']+", t) if len(w) > 3}
    degen = []
    for gen in GENERATORS:
        for ti in range(len(TOPICS)):
            texts = {r: all_cases.get((gen, f"{r}_{ti:02d}"), {}).get("artifact_final")
                     for r in ROUTES}
            for a, b in combinations([r for r in ROUTES if texts[r]], 2):
                wa, wb = cwords(texts[a]), cwords(texts[b])
                j = len(wa & wb) / max(len(wa | wb), 1)
                if j > 0.90:
                    degen.append(f"{gen}_{ti:02d}_{a}~{b}")
    gates["degeneracy"] = {"pairs_over_0.90": degen, "pass": not degen}
    for r in ROUTES:
        lens = [c["word_count"] for k, c in all_cases.items()
                if c["route_family"] == r]
        surface[r] = {"n": len(lens),
                      "mean_words": round(sum(lens) / max(len(lens), 1), 1)}
    verdict = ("CORPUS-STANDS" if all(g["pass"] for g in gates.values())
               else "CORPUS-REFUSED")
    out = {"verdict": verdict, "gates": gates, "surface_report": surface,
           "rule": "the B0 reading battery preregisters only on CORPUS-STANDS"}
    (OUTROOT / "routes_audit.json").write_text(json.dumps(out, indent=1),
                                               encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1))
    if verdict != "CORPUS-STANDS":
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--generator", choices=list(GENERATORS))
    ap.add_argument("--audit", action="store_true")
    args = ap.parse_args()
    if args.generator:
        generate(args.generator)
    elif args.audit:
        audit()
    else:
        ap.error("pick a mode")


if __name__ == "__main__":
    main()
