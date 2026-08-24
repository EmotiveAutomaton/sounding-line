"""Stage-2 Tree-A rebuild (discovery lane): scouts E24-A1 (order-larger bank), E24-A2
(stable locus), and the causal re-attempt under the rebuilt discipline.

Why a rebuild rather than a repair: the first ruler (L162) died to dev-power block
selection (blocks 27 then 1 across seeds on eighteen dev items) and a fixed dose that
lesioned the model. This bank is 2.5 times larger, the locus is chosen by CROSS-SEED
CONSENSUS (a block qualifies only if it is in the top three dev blocks under all three
seed splits; ties break toward the deeper block; blocks 0-2 are excluded as the known
degenerate input edge), and every dose is ladder-selected under the capability tolerance,
the discipline S8 re-earned.

DESIGN CHECK (2026-08-24, discovery lane). Lessons read at build time: section 3
(dev-selected hyperparameters are instruments and validate by stability, the L162 rule
this file exists to satisfy; the lexicon leak assertion runs at load; floors and shuffle
nulls as before; the control-quiet gate carries its null-effect failure condition),
section 4 (record measured doses), section 5 (produces guards, gpulock once). Failure
directions: locus consensus EMPTY means the representation is not stably placed at this
bank size, INSTRUMENT-FAILED with the instability quantified, no causal read; decoding
below the shuffle null or the lexical baseline is LEXICAL-ONLY; no ladder dose inside
tolerance is INSTRUMENT-FAILED at that cell. Scout statuses only.

Arms: decode (GPU: fit on explicit, consensus locus, held-out scrubbed accuracy vs
lexical and shuffle nulls, actor frames) · causal (GPU: fear/joy sign pair on 24
scenarios, dev/test split, ladder dose, random and shuffled controls).
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from prereg.g174 import (ACTOR_FRAMES, EXPLICIT_WORDS, LEXICON,                  # noqa: E402
                         NEUTRAL_PASSAGES, SCENARIOS as SCEN_V1,
                         explicit_sentences)

OUT = REPO / "results" / "scouts"
SEED0 = 19000
MODEL = "Qwen/Qwen2.5-1.5B"
CONCEPTS = ("fear", "anger", "sadness", "joy", "disgust", "surprise")
DEV_PER_CONCEPT = 8
ALPHA_LADDER = (2.0, 1.0, 0.5, 0.25)
CAPABILITY_TOL = 0.05
N_SHUFFLES = 200
N_PERMS = 20000

# ── the order-larger scrubbed bank: twenty situations per concept, topically spread,
# every word asserted against the frozen lexicon at load. The first eight per concept are
# the L162 bank, kept verbatim so the rebuild's gain is attributable to size and rule
# changes rather than rewritten items.
from prereg.g174 import SCRUBBED as _V1                                          # noqa: E402

_NEW = {
    "fear": [
        "The ladder wobbled twice as he reached for the highest shelf of the archive.",
        "The elevator stopped between floors and the lights flickered off.",
        "A second letter from the bank arrived, marked urgent and hand-delivered.",
        "The trail markers ended and the light was going fast under the trees.",
        "Her phone showed six missed calls from her son's school within an hour.",
        "The dog would not stop barking at the dark end of the basement stairs.",
        "The surgeon paused, then asked the nurse to bring the senior consultant.",
        "The ice made a long cracking sound somewhere out toward the middle.",
        "The turbulence got worse and the crew were told to take their seats.",
        "A man had been standing across the street for three hours without moving.",
        "The brakes warning light came on halfway across the mountain pass.",
        "The lab called twice and would only say she needed to come in person.",
    ],
    "anger": [
        "The insurer denied the claim on a technicality they had invented that week.",
        "His name was left off the paper whose experiments he had run for a year.",
        "The council approved the tower after promising the park would stay.",
        "She found her locked bike stripped to the frame outside the library.",
        "The airline canceled the last flight and offered a coupon as apology.",
        "His flatmate ate the meal he had labeled and prepped for the week.",
        "The manager took credit for the fix in the meeting, by name.",
        "The neighbor's contractor tore out the shared hedge without a word.",
        "The tow truck took her legally parked car while she watched from the queue.",
        "The editor cut the correction and ran the original error again.",
        "They raised the rent the week after he reported the broken heating.",
        "The referee ended the match early with her team a goal ahead.",
    ],
    "sadness": [
        "The nursing home returned his letters unopened with a short note.",
        "The orchard was sold and the new owners pulled every tree the same week.",
        "Her daughter's drawings were still taped inside the emptied locker.",
        "The last speaker of the dialect died before the recordings were finished.",
        "He watched the new family carry boxes into his childhood home.",
        "The team photo came down and nobody asked where it went.",
        "The bakery on the corner went dark after forty years, a paper sign on the door.",
        "She found his reading glasses in the couch a month after the funeral.",
        "The old dog's bowl stayed in the cupboard because nobody could throw it out.",
        "The reunion was canceled for the third year and the list of names grew shorter.",
        "The lighthouse was automated and the keeper's cottage boarded up.",
        "His granddaughter's violin sat untouched in the hall since the accident.",
    ],
    "joy": [
        "The adoption papers cleared after three years of waiting.",
        "The scan showed the treatment had worked completely.",
        "Her first loaf came out of the oven exactly like her mother's.",
        "The whole village turned out when the fishing boat came home early.",
        "He found his lost wedding ring in the garden bed after ten years.",
        "The shelter called: the old cat nobody wanted had found a family.",
        "Her visa was approved the morning of her sister's wedding.",
        "The seedlings the class had given up on came up overnight after the rain.",
        "The choir hit the final chord and the hall rose to its feet.",
        "His son's first word was the dog's name, and the dog came running.",
        "The librarian found the out-of-print book she had hunted for a decade.",
        "The bridge reopened and the two halves of the town met in the middle.",
    ],
    "disgust": [
        "The takeaway container in the fridge had been growing something for a month.",
        "The hotel mattress was stained through under the fresh-looking sheets.",
        "He found the source of the smell: a bag of prawns behind the radiator.",
        "The kitchen cloth had been used on the floor and then the counters.",
        "The pool filter came out coated in gray sludge and hair.",
        "Someone had been flicking gum under every desk in the reading room.",
        "The refill jug at the salad bar had a film floating on top.",
        "The vent above the stove dripped old grease onto the pan below.",
        "The shared microwave held a splatter no one had claimed for weeks.",
        "The landlord painted over the mold instead of treating it.",
        "The picnic table was sticky in a way the wipes could not fix.",
        "The recycling bin had been used for fish bones through a heat wave.",
    ],
    "surprise": [
        "The quiet intern stood up and corrected the keynote speaker, accurately.",
        "The wall they opened for rewiring held a sealed letter from 1911.",
        "Her carry-on suitcase was full of someone else's identical belongings.",
        "The stray cat she fed for years turned out to belong to the mayor.",
        "The demolition crew found the ballroom intact behind the false wall.",
        "His chess opponent, age seven, announced mate in four and was right.",
        "The lottery office called about a ticket he had used as a bookmark.",
        "The understudy sang the aria better than the recording they sold.",
        "The garden gnome returned after two years with photographs attached.",
        "The auditor found the missing money in an account nobody remembered opening.",
        "The old radio picked up a station that had been off the air for decades.",
        "The identical parcel arrived at both sisters' houses the same morning.",
    ],
}

SCRUBBED2 = {c: list(_V1[c]) + _NEW[c] for c in CONCEPTS}

# twelve additional causal scenarios; the twelve v1 scenarios are kept verbatim
_SCEN_NEW = [
    ("A drawer in the rented desk was locked, the key taped underneath.",
     "She unlocked it and looked inside.", "She left the key where it was."),
    ("The band on stage called for a volunteer from the crowd.",
     "He raised his hand and stepped forward.", "He stepped back behind the taller crowd."),
    ("The market stall offered free samples of something unfamiliar.",
     "She took one and tried it.", "She smiled and kept walking."),
    ("An old friend's number appeared on the screen after five years.",
     "He answered before the second ring.", "He watched it ring out."),
    ("The tide pool at the rocks held something moving under the weed.",
     "She reached in to turn the weed over.", "She kept her hands on the warm rock."),
    ("The last seat on the early boat was going once, going twice.",
     "He took the seat and boarded.", "He waited for the later, larger boat."),
    ("The workshop door was open and the machines were running unattended.",
     "She stepped in to look for the operator.", "She stayed outside and knocked."),
    ("The forum thread asked for a first volunteer to test the build.",
     "He installed it that evening.", "He bookmarked it for someday."),
    ("A side path off the main trail was marked only with a ribbon.",
     "They followed the ribbon path.", "They kept to the mapped trail."),
    ("The neighbor's ladder stood against the shared wall, unexplained.",
     "She climbed to see over.", "She went back inside and closed the blinds."),
    ("The recipe called for an ingredient he had never cooked with.",
     "He bought it and followed the recipe.", "He substituted the one he knew."),
    ("The dance floor was empty when their song came on.",
     "They got up first.", "They stayed at the table, watching."),
]
SCENARIOS2 = list(SCEN_V1) + _SCEN_NEW
CAUSAL_PREDICTIONS = {"fear": "withdraw", "joy": "approach"}


def assert_bank_clean() -> None:
    import re
    for c, sents in SCRUBBED2.items():
        assert len(sents) == 20, (c, len(sents))
        for s in sents:
            for w in re.findall(r"[a-z]+", s.lower()):
                assert w not in LEXICON, f"lexicon leak: {w!r} in {c}: {s}"
    for sc, a, wd in SCENARIOS2:
        for text in (sc, a, wd):
            for w in re.findall(r"[a-z]+", text.lower()):
                assert w not in LEXICON, f"lexicon leak in scenario: {w!r}"


def pooled_states(model, tok, texts):
    import torch                                                                 # noqa: PLC0415
    rows = []
    for t in texts:
        enc = tok(t, return_tensors="pt", add_special_tokens=False).to("cuda")
        with torch.no_grad():
            hs = model(**enc, output_hidden_states=True).hidden_states[1:]
        rows.append(np.stack([h[0].mean(0).float().cpu().numpy() for h in hs]))
    return np.stack(rows)


def fit_dirs(X, labels, n_classes):
    mu = X.mean(0)
    dirs = np.zeros((n_classes, X.shape[1], X.shape[2]))
    for c in range(n_classes):
        d = X[[i for i, l in enumerate(labels) if l == c]].mean(0) - mu
        dirs[c] = d / (np.linalg.norm(d, axis=-1, keepdims=True) + 1e-9)
    return dirs, mu


def decode_acc(dirs, mu, X, labels, block):
    proj = np.einsum("nd,cd->nc", X[:, block] - mu[block], dirs[:, block])
    return float((proj.argmax(1) == np.array(labels)).mean())


def arm_decode() -> int:
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock          # noqa: PLC0415
    from soundingline.probe.conditional_reader import load_reader                # noqa: PLC0415
    assert_bank_clean()
    n_c = len(CONCEPTS)
    exp_texts, exp_labels = [], []
    for ci, c in enumerate(CONCEPTS):
        for s in explicit_sentences(c):
            exp_texts.append(s)
            exp_labels.append(ci)
    acquire_gpu_lock("scout_a_decode")
    try:
        model, tok = load_reader(MODEL, device="cuda", dtype="float16")
        X_exp = pooled_states(model, tok, exp_texts)
        dirs, mu = fit_dirs(X_exp, exp_labels, n_c)
        n_blocks = X_exp.shape[1]

        # cross-seed consensus locus: three seeded dev splits; a block qualifies only if
        # in the top-3 dev blocks under ALL three; blocks 0-2 excluded (degenerate edge)
        all_texts = {c: SCRUBBED2[c] for c in CONCEPTS}
        state_cache = {}

        def states_for(texts):
            key = tuple(texts)
            if key not in state_cache:
                state_cache[key] = pooled_states(model, tok, list(texts))
            return state_cache[key]

        top3 = []
        splits = []
        for seed in (SEED0, SEED0 + 1, SEED0 + 2):
            rng = random.Random(seed)
            dev_t, dev_l, test_t, test_l = [], [], [], []
            for ci, c in enumerate(CONCEPTS):
                idx = list(range(20))
                rng.shuffle(idx)
                for j in idx[:DEV_PER_CONCEPT]:
                    dev_t.append(SCRUBBED2[c][j]); dev_l.append(ci)
                for j in idx[DEV_PER_CONCEPT:]:
                    test_t.append(SCRUBBED2[c][j]); test_l.append(ci)
            splits.append((dev_t, dev_l, test_t, test_l))
            X_dev = states_for(tuple(dev_t))
            accs = [decode_acc(dirs, mu, X_dev, dev_l, b) for b in range(n_blocks)]
            order = sorted(range(3, n_blocks), key=lambda b: -accs[b])
            top3.append(set(order[:3]))
        consensus = sorted(set.intersection(*top3))
        print(f"top-3 per seed: {[sorted(t) for t in top3]}; consensus {consensus}")
        if not consensus:
            (OUT / "a_decode.json").write_text(json.dumps(
                {"scout": "E24-A2", "status": "INSTRUMENT-FAILED",
                 "reason": "no cross-seed consensus block",
                 "top3_per_seed": [sorted(t) for t in top3]}, indent=1),
                encoding="utf-8", newline="\n")
            return 0
        block = max(consensus)          # ties break toward depth, frozen rule

        # held-out accuracy at the consensus block, per seed split, plus nulls and frames
        rng = random.Random(SEED0 + 5)
        test_accs, null95s, lex_accs = [], [], []
        from sklearn.feature_extraction.text import CountVectorizer              # noqa: PLC0415
        from sklearn.linear_model import LogisticRegression                      # noqa: PLC0415
        for (dev_t, dev_l, test_t, test_l) in splits:
            X_test = states_for(tuple(test_t))
            test_accs.append(decode_acc(dirs, mu, X_test, test_l, block))
            nulls = []
            for _ in range(N_SHUFFLES // 2):
                sh = exp_labels[:]
                rng.shuffle(sh)
                d_sh, mu_sh = fit_dirs(X_exp, sh, n_c)
                nulls.append(decode_acc(d_sh, mu_sh, X_test, test_l, block))
            null95s.append(float(np.quantile(nulls, 0.95)))
            vec = CountVectorizer(lowercase=True)
            lr = LogisticRegression(max_iter=2000, random_state=SEED0)
            lr.fit(vec.fit_transform(exp_texts), exp_labels)
            lex_accs.append(float(lr.score(vec.transform(test_t), test_l)))
        frame_accs = []
        dev_t, dev_l, test_t, test_l = splits[0]
        for frame in ACTOR_FRAMES[1:]:
            X_f = pooled_states(model, tok, [frame + t for t in test_t])
            frame_accs.append(decode_acc(dirs, mu, X_f, test_l, block))
    finally:
        release_gpu_lock()
    mean_acc = sum(test_accs) / 3
    passed = all(a > n and a > l for a, n, l in zip(test_accs, null95s, lex_accs))
    frames_ok = all(abs(f - test_accs[0]) <= 0.15 for f in frame_accs)
    status = "PROMISING" if (passed and frames_ok) else \
        ("QUIET" if passed else "LEXICAL-OR-NULL")
    (OUT / "a_decode.json").write_text(json.dumps(
        {"scout": "E24-A1/A2", "status": status, "consensus_blocks": consensus,
         "block": block, "test_accs": test_accs, "null95s": null95s,
         "lexical_accs": lex_accs, "frame_accs": frame_accs, "mean_acc": mean_acc,
         "chance": 1 / n_c, "bank_size": {c: len(SCRUBBED2[c]) for c in CONCEPTS}},
        indent=1), encoding="utf-8", newline="\n")
    print(f"{status}: consensus block {block}, test {[round(a,3) for a in test_accs]} "
          f"vs null95 {[round(n,3) for n in null95s]} vs lexical "
          f"{[round(x,3) for x in lex_accs]}")
    return 0


def arm_causal() -> int:
    import torch                                                                 # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock          # noqa: PLC0415
    from soundingline.probe.conditional_reader import (artifact_logprob,         # noqa: PLC0415
                                                       load_reader)
    from soundingline.probe.interventions import SubspaceIntervention            # noqa: PLC0415
    dec = json.loads((OUT / "a_decode.json").read_text(encoding="utf-8"))
    if dec["status"] not in ("PROMISING", "QUIET"):
        print("decode arm did not pass; causal arm does not run")
        (OUT / "a_causal.json").write_text(json.dumps(
            {"scout": "E24-A rebuild causal", "status": "NOT-RUN",
             "reason": f"decode status {dec['status']}"}, indent=1),
            encoding="utf-8", newline="\n")
        return 0
    block = dec["block"]
    assert_bank_clean()
    n_c = len(CONCEPTS)
    exp_texts, exp_labels = [], []
    for ci, c in enumerate(CONCEPTS):
        for s in explicit_sentences(c):
            exp_texts.append(s)
            exp_labels.append(ci)
    rng = random.Random(SEED0 + 11)
    scen = list(SCENARIOS2)
    rng.shuffle(scen)
    dev_sc, test_sc = scen[:8], scen[8:]
    acquire_gpu_lock("scout_a_causal")
    results = {}
    try:
        model, tok = load_reader(MODEL, device="cuda", dtype="float16")
        X_exp = pooled_states(model, tok, exp_texts)
        dirs, mu = fit_dirs(X_exp, exp_labels, n_c)
        d_model = X_exp.shape[2]

        def pref(s, iv):
            lw, _, _ = artifact_logprob(model, tok, s[0], s[2], intervention=iv)
            la, _, _ = artifact_logprob(model, tok, s[0], s[1], intervention=iv)
            return lw - la

        for concept, want in CAUSAL_PREDICTIONS.items():
            ci = CONCEPTS.index(concept)
            u = torch.tensor(dirs[ci, block], dtype=torch.float32).reshape(d_model, 1)
            m = torch.tensor(mu[block], dtype=torch.float32)
            # ladder dose under capability tolerance (the S8-earned discipline)
            dose = None
            for al in ALPHA_LADDER:
                iv = SubspaceIntervention({block: u}, {block: m}, al, "amplify")
                cb = [artifact_logprob(model, tok, "Text follows.", p)[0]
                      for p in NEUTRAL_PASSAGES[:3]]
                ca = [artifact_logprob(model, tok, "Text follows.", p, intervention=iv)[0]
                      for p in NEUTRAL_PASSAGES[:3]]
                if abs(sum(ca) / 3 - sum(cb) / 3) / abs(sum(cb) / 3) <= CAPABILITY_TOL:
                    dose = al
                    break
            if dose is None:
                results[concept] = {"status": "INSTRUMENT-FAILED",
                                    "reason": "no ladder dose inside tolerance"}
                continue
            # require a nonzero dev effect before spending the test set
            base_dev = [pref(s, None) for s in dev_sc]
            iv_a = SubspaceIntervention({block: u}, {block: m}, dose, "amplify")
            dev_eff = [pref(s, iv_a) - b for s, b in zip(dev_sc, base_dev)]
            base = {i: pref(s, None) for i, s in enumerate(test_sc)}

            def effect(iv):
                return [pref(s, iv) - base[i] for i, s in enumerate(test_sc)]

            iv_b = SubspaceIntervention({block: u}, {block: m}, 1.0, "ablate")
            g = torch.Generator().manual_seed(SEED0 + 23 + ci)
            u_r = torch.randn(d_model, 1, generator=g)
            sh = exp_labels[:]
            rng.shuffle(sh)
            d_sh, mu_sh = fit_dirs(X_exp, sh, n_c)
            u_s = torch.tensor(d_sh[ci, block], dtype=torch.float32).reshape(d_model, 1)
            e_amp, e_abl = effect(iv_a), effect(iv_b)
            e_rand = effect(SubspaceIntervention({block: u_r}, {block: m}, dose, "amplify"))
            e_shuf = effect(SubspaceIntervention({block: u_s}, {block: m}, dose, "amplify"))

            def perm(diffs):
                r2 = random.Random(SEED0 + 31 + ci)
                obs = sum(diffs) / len(diffs)
                ge = sum(1 for _ in range(N_PERMS)
                         if abs(sum(x * r2.choice((1, -1)) for x in diffs)
                                / len(diffs)) >= abs(obs))
                return obs, (ge + 1) / (N_PERMS + 1)

            sgn = 1.0 if want == "withdraw" else -1.0
            a_m, a_p = perm([sgn * x for x in e_amp])
            b_m, b_p = perm([sgn * x for x in e_abl])
            r_m, _ = perm(e_rand)
            s_m, _ = perm(e_shuf)
            ctrl_quiet = (max(abs(r_m), abs(s_m)) < 0.5 * abs(a_m)) if a_m != 0 else False
            sign_pair = a_m > 0 and a_p < 0.05 and b_m < 0
            results[concept] = {
                "dose": dose, "dev_effect_mean": sum(dev_eff) / len(dev_eff),
                "amp_signed": a_m, "amp_p": a_p, "abl_signed": b_m, "abl_p": b_p,
                "rand_mean": r_m, "shuf_mean": s_m,
                "sign_pair": sign_pair, "controls_quiet": ctrl_quiet,
                "status": ("PROMISING" if sign_pair and ctrl_quiet else
                           "RIVAL-FAVORED" if sign_pair else "QUIET")}
            print(f"{concept}: {results[concept]}")
    finally:
        release_gpu_lock()
    overall = ("PROMISING" if all(v.get("status") == "PROMISING"
                                  for v in results.values())
               else "QUIET" if any(v.get("status") in ("QUIET", "RIVAL-FAVORED")
                                   for v in results.values())
               else "INSTRUMENT-FAILED")
    (OUT / "a_causal.json").write_text(json.dumps(
        {"scout": "E24-A rebuild causal", "status": overall, "block": block,
         "concepts": results}, indent=1), encoding="utf-8", newline="\n")
    print(f"overall {overall}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=["decode", "causal"])
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    rc = {"decode": arm_decode, "causal": arm_causal}[a.arm]()
    print(f"{a.arm} in {(time.time() - t0) / 60:.0f} min")
    return rc


if __name__ == "__main__":
    sys.exit(main())
