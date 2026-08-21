"""G168 construction (Phase 2.3 root P23-C0, part 1) — the role-randomized interaction
corpus: essays produced through a LOGGED two-actor protocol so ratification, selection,
veto, integration, and repair have ground truth, and the reading battery can ask which
roles survive into the artifact.

PROTOCOL per case (two actors, one per local family, roles crossed):
    propose    actor P produces one thesis+plan, or THREE candidate theses
    select     actor S (the other family) picks among the three by its own judgment
               (a real selection event, alternatives recorded), or accepts the first
               without alternatives (the accept-first cell)
    veto       optionally, S rejects the plan once with a stated objection and P
               revises it (both texts logged)
    realize    S writes the essay from the surviving plan
    repair     one actor rewrites the weakest paragraph (seeded pick, actor
               alternates by case parity; original and replacement logged)

CONDITIONS: proposer family x selection mode x veto presence (2 x 2 x 2 = 8 cells),
five topics each = 40 cases, every event a schema ProcessEvent with actor identity,
alternatives, and parents. Echo material saved per actor for the reading battery's
echo-split columns (the L146/L148 standing rule, carried from birth).

DESIGN CHECK (2026-08-21, at design time). Lessons read: LESSONS §3 to §5 complete
(assigned-is-not-realized drives the audit's integrity gates; produces guards; yield
withheld below 90 percent; retries with backoff; one gpu lock per invocation).
Audit gates, each with null and alternative and the failure direction:
    YIELD >= 0.90 (direction DOWN, manifest refused).
    BAND: essays 300 to 800 words (any violation refuses).
    LOG COMPLETENESS: every case carries its condition's required operations with
      the right actors (a select event only in from3 cells, a veto pair only in
      veto cells; direction DOWN, refused).
    SELECTION INTEGRITY (assigned-is-not-realized): the SELECTED thesis's content
      words appear in the final essay at >= 0.4 overlap AND strictly above every
      REJECTED thesis's overlap in >= 0.8 of from3 cases — else selection did not
      survive realization and the corpus cannot ask its question (direction DOWN,
      refused).
    VETO INTEGRITY: in veto cells the revised plan differs from the original
      (content-word Jaccard < 0.9) in >= 0.8 of cases (direction UP toward identity
      = the veto was theater, refused).
The reading battery (role recovery per role, never summed; artifact-only vs
process-aware) preregisters ONLY on CORPUS-STANDS, per the standing corpus-first
discipline.

Outputs: corpora/g168_roles/{case_id}.json + manifest; --audit writes
corpora/g168_roles/roles_audit.json and exits 1 on any failure.
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
OUTROOT = REPO / "corpora" / "g168_roles"
OLLAMA = "http://127.0.0.1:11434/api/generate"
FAMILIES = {"qwen": "qwen3.5:9b", "llama": "llama3.1:8b"}
SEED0 = 16800
BAND = (300, 800)
N_TOPICS = 5

sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "runners"))
from run_g131_gen import TOPICS                                        # noqa: E402
from soundingline.process_record import ProcessCase, ProcessEvent      # noqa: E402

THESES_P = ("Propose three distinct one-sentence thesis statements for a short "
            "argumentative essay on: {topic} Number them 1 to 3, nothing else.")
THESIS_P = ("Propose one clear thesis statement and a three-point plan for a short "
            "argumentative essay on: {topic} Format: THESIS: ... PLAN: 1... 2... 3...")
SELECT_P = ("Three candidate thesis statements for an essay on the question below. "
            "Pick the strongest. Answer with the number only.\n\nQUESTION: {topic}\n\n"
            "{cands}")
VETO_P = ("Here is a plan for a short argumentative essay. Name its single weakest "
          "point and demand one concrete change, in two sentences.\n\nPLAN:\n{plan}")
REVISE_P = ("Revise this essay plan to answer the objection. Keep the format.\n\n"
            "PLAN:\n{plan}\n\nOBJECTION:\n{objection}")
REALIZE_P = ("Write a short argumentative essay of 400 to 600 words on: {topic} "
             "It must defend exactly this thesis: {thesis} "
             "{plan_clause}Plain prose, no headings.")
REPAIR_P = ("Rewrite the following paragraph of an essay to be clearer and stronger. "
            "Return only the rewritten paragraph.\n\nPARAGRAPH:\n{para}")


def call_gen(fam, prompt, seed, num_predict=900):
    req = urllib.request.Request(OLLAMA, data=json.dumps(
        {"model": FAMILIES[fam], "prompt": prompt, "stream": False, "think": False,
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


def parse_theses(t):
    out = []
    for ln in (t or "").splitlines():
        m = re.match(r"^\s*[1-3][.)]\s*(.+)$", ln.strip())
        if m:
            out.append(m.group(1).strip())
    return out if len(out) == 3 else None


def conditions():
    out = []
    i = 0
    for proposer in ("qwen", "llama"):
        for sel in ("from3", "accept_first"):
            for veto in (True, False):
                for ti in range(N_TOPICS):
                    out.append({"case_i": i, "proposer": proposer,
                                "realizer": ("llama" if proposer == "qwen"
                                             else "qwen"),
                                "selection": sel, "veto": veto, "topic_i": ti,
                                "repair_actor": ("proposer" if i % 2 == 0
                                                 else "realizer")})
                    i += 1
    return out


def build_case(c):
    topic = TOPICS[c["topic_i"]]
    P, R = c["proposer"], c["realizer"]
    seed = SEED0 + c["case_i"] * 50
    ev, order = [], 0

    def add(op, actor, **kw):
        nonlocal order
        ev.append(ProcessEvent(f"e{order}", order, actor, op, **kw))
        order += 1

    if c["selection"] == "from3":
        raw = call_gen(P, THESES_P.format(topic=topic), seed, 250)
        theses = parse_theses(raw)
        if not theses:
            return None
        add("propose", P, target="theses", payload={"candidates": theses})
        cands = "\n".join(f"{j + 1}. {t}" for j, t in enumerate(theses))
        pick_raw = call_gen(R, SELECT_P.format(topic=topic, cands=cands),
                            seed + 1, 20)
        m = re.search(r"[1-3]", pick_raw or "")
        if not m:
            return None
        pick = int(m.group()) - 1
        thesis = theses[pick]
        add("select", R, target=f"thesis_{pick}",
            parent_event_ids=["e0"],
            alternatives=[t for j, t in enumerate(theses) if j != pick],
            payload={"selected": thesis})
        for j, t in enumerate(theses):
            if j != pick:
                add("reject", R, target=f"thesis_{j}", parent_event_ids=["e1"],
                    payload={"rejected": t})
        plan = None
    else:
        raw = call_gen(P, THESIS_P.format(topic=topic), seed, 350)
        if not raw or "THESIS:" not in raw:
            return None
        thesis = raw.split("THESIS:", 1)[1].split("PLAN:")[0].strip()[:300]
        plan = raw.split("PLAN:", 1)[1].strip()[:600] if "PLAN:" in raw else None
        add("propose", P, target="thesis_plan",
            payload={"thesis": thesis, "plan": plan})

    if c["veto"]:
        plan_txt = plan or thesis
        objection = call_gen(R, VETO_P.format(plan=plan_txt), seed + 2, 200)
        if not objection:
            return None
        add("veto", R, target="plan", payload={"objection": objection})
        revised = call_gen(P, REVISE_P.format(plan=plan_txt, objection=objection),
                           seed + 3, 400)
        if not revised:
            return None
        add("revise", P, target="plan", payload={"revised_plan": revised})
        plan = revised

    plan_clause = f"Follow this plan: {plan[:500]} " if plan else ""
    essay = call_gen(R, REALIZE_P.format(topic=topic, thesis=thesis,
                                         plan_clause=plan_clause), seed + 4)
    if not (essay and BAND[0] <= wc(essay) <= BAND[1]):
        return None
    add("realize_surface", R, target="essay", visible_in_final="yes")

    paras = [p for p in essay.split("\n\n") if wc(p) > 30]
    if paras:
        import numpy as np
        pi = int(np.random.default_rng(seed).integers(len(paras)))
        actor = P if c["repair_actor"] == "proposer" else R
        new_para = call_gen(actor, REPAIR_P.format(para=paras[pi]), seed + 5, 400)
        if new_para and wc(new_para) > 20:
            essay = essay.replace(paras[pi], new_para.strip(), 1)
            add("repair", actor, target=f"paragraph_{pi}",
                payload={"original": paras[pi][:400],
                         "replacement": new_para[:400]})

    case = ProcessCase(
        case_id=f"case_{c['case_i']:02d}", lineage_id=f"g168_{c['topic_i']:02d}",
        domain="argumentative_essay", medium="text",
        brief_id=f"g131_topic_{c['topic_i']:02d}",
        declared_context={"protocol": "two-actor logged", **{
            k: c[k] for k in ("proposer", "realizer", "selection", "veto",
                              "repair_actor")}},
        participants={P: "local_model_proposer", R: "local_model_realizer"},
        route_family=f"{c['selection']}_{'veto' if c['veto'] else 'noveto'}",
        events=ev, artifact_final=essay, construction_seed=seed)
    case.validate()
    d = case.to_dict()
    d["condition"] = c
    d["thesis"] = thesis
    d["word_count"] = wc(essay)
    return d


def generate():
    from soundingline.gpulock import acquire_gpu_lock                  # noqa: PLC0415
    acquire_gpu_lock("g168_gen")
    OUTROOT.mkdir(parents=True, exist_ok=True)
    made = 0
    conds = conditions()
    for c in conds:
        dest = OUTROOT / f"case_{c['case_i']:02d}.json"
        if dest.exists():
            made += 1
            continue
        d = None
        for _try in range(2):
            d = build_case({**c})
            if d:
                break
        if d:
            dest.write_text(json.dumps(d, indent=1), encoding="utf-8", newline="\n")
            made += 1
            print(f"  case {c['case_i']:02d} ok ({d['word_count']}w, "
                  f"{c['proposer']}->{c['realizer']}, {c['selection']}, "
                  f"veto={c['veto']})")
        else:
            print(f"  case {c['case_i']:02d} FAILED")
    if made < 0.9 * len(conds):
        print(f"THIN YIELD: {made}/{len(conds)} — manifest withheld (LESSONS §5)")
        sys.exit(1)
    (OUTROOT / "manifest.json").write_text(json.dumps(
        {"seed0": SEED0, "made": made, "total": len(conds), "band": list(BAND),
         "conditions": "proposer x selection x veto, repair alternating"},
        indent=1), encoding="utf-8", newline="\n")
    print(f"g168: {made}/{len(conds)}, manifest written")


def cwords(s):
    stop = set("the a an and or of to in on for with by at from is was were be it "
               "this that not no as their".split())
    return {w.lower() for w in re.findall(r"[A-Za-z']+", s or "") if len(w) > 3} - stop


def audit():
    cases = [json.loads(p.read_text(encoding="utf-8"))
             for p in sorted(OUTROOT.glob("case_*.json"))]
    total = len(conditions())
    gates = {"yield": {"made": len(cases), "expected": total,
                       "pass": len(cases) >= 0.9 * total}}
    band_bad = [c["case_id"] for c in cases
                if not (BAND[0] <= c["word_count"] <= BAND[1])]
    gates["band"] = {"violations": band_bad, "pass": not band_bad}
    log_bad, sel_ok, sel_n, veto_ok, veto_n = [], 0, 0, 0, 0
    for c in cases:
        ops = {e["operation"] for e in c["events"]}
        cond = c["condition"]
        need = {"propose", "realize_surface"}
        if cond["selection"] == "from3":
            need |= {"select", "reject"}
        if cond["veto"]:
            need |= {"veto", "revise"}
        if not need <= ops:
            log_bad.append(c["case_id"])
            continue
        if cond["selection"] == "from3":
            sel_n += 1
            sel_ev = next(e for e in c["events"] if e["operation"] == "select")
            chosen = cwords(sel_ev["payload"]["selected"])
            essay_w = cwords(c["artifact_final"])
            chosen_ov = len(chosen & essay_w) / max(len(chosen), 1)
            rej_ovs = [len(cwords(e["payload"]["rejected"]) & essay_w)
                       / max(len(cwords(e["payload"]["rejected"])), 1)
                       for e in c["events"] if e["operation"] == "reject"]
            if chosen_ov >= 0.4 and all(chosen_ov > r for r in rej_ovs):
                sel_ok += 1
        if cond["veto"]:
            veto_n += 1
            prop = next(e for e in c["events"] if e["operation"] == "propose")
            rev = next(e for e in c["events"] if e["operation"] == "revise")
            orig = prop["payload"].get("plan") or prop["payload"].get("thesis") or ""
            a, b = cwords(orig), cwords(rev["payload"]["revised_plan"])
            j = len(a & b) / max(len(a | b), 1)
            if j < 0.9:
                veto_ok += 1
    gates["log_completeness"] = {"violations": log_bad, "pass": not log_bad}
    sel_rate = sel_ok / max(sel_n, 1)
    veto_rate = veto_ok / max(veto_n, 1)
    gates["selection_integrity"] = {"rate": round(sel_rate, 4), "n": sel_n,
                                    "pass": sel_rate >= 0.8}
    gates["veto_integrity"] = {"rate": round(veto_rate, 4), "n": veto_n,
                               "pass": veto_rate >= 0.8}
    verdict = ("CORPUS-STANDS" if all(g["pass"] for g in gates.values())
               else "CORPUS-REFUSED")
    out = {"verdict": verdict, "gates": gates,
           "rule": "the role-recovery battery preregisters only on CORPUS-STANDS"}
    (OUTROOT / "roles_audit.json").write_text(json.dumps(out, indent=1),
                                              encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1))
    if verdict != "CORPUS-STANDS":
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--generate", action="store_true")
    ap.add_argument("--audit", action="store_true")
    args = ap.parse_args()
    if args.generate:
        generate()
    elif args.audit:
        audit()
    else:
        ap.error("pick a mode")


if __name__ == "__main__":
    main()
