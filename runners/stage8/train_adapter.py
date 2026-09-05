"""Adapter training OUTSIDE the capsule (brief §4 FM, §12.1, E02): a low-rank adapter on a
base reader, trained on population-sampled process logs in the one grammar (the goal line
on half the examples, one to three earlier artifacts by the same freshly sampled maker on
two in five), predicting the next token of the log; after every epoch the adapter is saved,
the held-out per-token loss and the held-out NEXT-MOVE log score through the forward-model
readout are measured against the frozen DOM on the same boundaries, and the curve is
written to the TRAINING registry; the epoch with the best held-out next-move score is
frozen under adapters/<name>/frozen with its directory hash in the ADAPTERS registry.
Nothing maker-specific is ever in the corpus: every maker is a fresh draw.

Usage: train_adapter.py --reader fm_qwen [--epochs 4] [--n-train 2400] [--pilot]
The pilot (one epoch on the smallest reader, a small corpus) measures the cost per epoch
the workload lock is sized from.

DESIGN CHECK (2026-09-04)
lessons read: LESSONS §4 (record environment versions and the measured revision; set model
  internals structurally and assert the change took: the adapter's trainable parameter count
  is asserted nonzero; a member that diverges is recorded, never silently dropped), §5 (a
  training longer than a few hours owes checkpoint-resume: every epoch is a checkpoint and
  the loop resumes from the last saved epoch; the GPU lock is taken once per invocation),
  §1d (the training and evaluation lineages sit in disjoint bands).
gates: E02 (convergence): NULL is a held-out next-move score that does not improve
  monotonically toward DOM's band, or a missed band by 0.05 nats or more after the one
  repair (fails DOWN: the reader closes for the stage); ALTERNATIVE: within DOM - 0.05 nats.
  Failure direction: DOWN. bands: exhaustive (within / missed by under 0.05, one repair /
  missed by 0.05 or more, closed).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import shutil
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from runners import s5_lib                                                         # noqa: E402
from runners.stage7.reader import baselines as B                                   # noqa: E402
from runners.stage8.constructor import population as POP                           # noqa: E402
from runners.stage8.reader import logfmt as LF                                     # noqa: E402
from soundingline.stage8 import (S8, EXPERTISE_BAND_NATS, adapter_hash, now_iso,    # noqa: E402
                                 read_registry, update_registry, write_registry)

BASES = {"fm_qwen": "Qwen/Qwen2.5-1.5B-Instruct", "fm_smollm": "HuggingFaceTB/SmolLM2-1.7B-Instruct",
         "fm_qwen05": "Qwen/Qwen2.5-0.5B-Instruct"}
ADAPTERS = S8 / "adapters"
LORA = {"r": 16, "alpha": 32, "dropout": 0.05, "targets": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]}
MAX_LEN = 1024


def build_corpus(n_train: int, n_heldout_worlds: int) -> tuple[list[dict], list[dict]]:
    train = POP.corpus(max(1, n_train // 2), POP.TRAIN_BAND)
    held = []
    for d in POP.DOMAINS:
        for i in range(n_heldout_worlds):
            w = POP.sample_world(POP.pop_lid(i, d, POP.HELDOUT_BAND), finish=True)
            if w["degenerate"] or w["hidden"]["next_action"] is None:
                continue
            held.append(w)
    return train, held


def heldout_texts(n: int) -> list[str]:
    return [POP.training_example(i, d, POP.HELDOUT_BAND + 500)["text"] for d in POP.DOMAINS for i in range(n)]


def score_next(model, tok, prefix: str, lines: list[str]) -> list[float]:
    import torch                                                                  # noqa: PLC0415
    pre = tok(prefix, add_special_tokens=True, return_tensors="pt").input_ids[0]
    P = pre.shape[0]
    seqs = [torch.cat([pre, tok(c, add_special_tokens=False, return_tensors="pt").input_ids[0]]) for c in lines]
    L = max(s.shape[0] for s in seqs)
    pad = tok.pad_token_id if tok.pad_token_id is not None else 0
    ids = torch.full((len(seqs), L), pad, dtype=torch.long)
    att = torch.zeros((len(seqs), L), dtype=torch.long)
    for i, s in enumerate(seqs):
        ids[i, :s.shape[0]] = s
        att[i, :s.shape[0]] = 1
    with torch.no_grad():
        logits = model(input_ids=ids.to("cuda"), attention_mask=att.to("cuda")).logits.float()
    lp = torch.log_softmax(logits[:, :-1], dim=-1)
    g = lp.gather(2, ids.to("cuda")[:, 1:].unsqueeze(-1)).squeeze(-1)
    out = []
    for i, s in enumerate(seqs):
        n = s.shape[0] - P
        out.append(float(g[i, P - 1:P - 1 + n].sum()))
    return out


def eval_next_move(model, tok, held: list[dict], dom_params: dict | None, max_worlds: int = 80) -> dict:
    """The held-out next-move log score through the forward-model readout, DOM beside it."""
    fm, dom, n = [], [], 0
    for w in held[:max_worlds]:
        cut = w["cut"]
        ev = POP.evidence_at(w, cut, {"unit_ref": "u", "condition_ref": "c"})
        ids = ev["query"]["next_action_options"]
        truth = w["hidden"]["next_action"]
        if not ids or truth not in ids:
            continue
        c = w["state"]["external_context"]
        head = LF.header(w["doc"]["topic"], c["audience"], c["tools"], c["deadline"], w["doc"]["sections"])
        prefix = LF.compose([], head, LF.prefix_lines(ev["process_prefix"]))
        lines = [LF.event_line(cut, *aid.split(":")) for aid in ids]
        lps = score_next(model, tok, prefix, lines)
        m = max(lps)
        z = sum(math.exp(v - m) for v in lps)
        p = math.exp(lps[ids.index(truth)] - m) / z
        fm.append(math.log(max(p, 1e-9)))
        if dom_params:
            d = B.dom(ev, dom_params) or {}
            dom.append(math.log(max(float((d.get("next_action") or {}).get(truth, 0.0)), 1e-9)))
        n += 1
    return {"n": n, "fm_next_move_ls": (sum(fm) / n) if n else None, "dom_next_move_ls": (sum(dom) / n) if (n and dom) else None,
            "gap_fm_minus_dom": ((sum(fm) - sum(dom)) / n) if (n and dom) else None}


def eval_loss(model, tok, texts: list[str]) -> float:
    import torch                                                                  # noqa: PLC0415
    tot, cnt = 0.0, 0
    with torch.no_grad():
        for t in texts:
            ids = tok(t + tok.eos_token, add_special_tokens=True, return_tensors="pt", truncation=True, max_length=MAX_LEN).input_ids.to("cuda")
            out = model(input_ids=ids, labels=ids)
            tot += float(out.loss) * (ids.shape[1] - 1)
            cnt += ids.shape[1] - 1
    return tot / max(1, cnt)


def train(reader: str, epochs: int, n_train: int, n_heldout: int, seed: int, lr: float, batch: int, accum: int,
          pilot: bool, resume: bool, tag: str = "") -> dict:
    import torch                                                                  # noqa: PLC0415
    from peft import LoraConfig, PeftModel, get_peft_model                        # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    base = BASES[reader]
    name = reader + (f"_{tag}" if tag else "")
    out_dir = ADAPTERS / name
    out_dir.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(seed)
    random.seed(seed)
    t0 = time.time()
    train_ex, held = build_corpus(n_train, n_heldout)
    held_txt = heldout_texts(20 if not pilot else 6)
    write_registry("POP_CORPUS", {**(read_registry("POP_CORPUS") or {}), name: {
        "n_train": len(train_ex), "bands": {"train": POP.TRAIN_BAND, "heldout": POP.HELDOUT_BAND}, "at": now_iso(),
        "lineages": sorted({lid for e in train_ex for lid in e["lineages"]}),
        "goal_share": sum(1 for e in train_ex if e["with_goal"]) / max(1, len(train_ex)),
        "earlier_share": sum(1 for e in train_ex if e["n_earlier"]) / max(1, len(train_ex)),
        "goals": sorted({e["goal"] for e in train_ex}), "shapes": sorted({e["shape"] for e in train_ex})}})
    corpus_s = time.time() - t0
    print(f"corpus built in {corpus_s:.0f}s: {len(train_ex)} examples, {len(held)} held-out worlds", flush=True)
    tok = AutoTokenizer.from_pretrained(base)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(base, dtype=torch.bfloat16).to("cuda")
    print("model loaded", flush=True)
    model.gradient_checkpointing_enable()
    model.config.use_cache = False
    start_epoch = 0
    last = sorted(out_dir.glob("epoch*"))
    if resume and last:
        model = PeftModel.from_pretrained(model, str(last[-1]), is_trainable=True)
        start_epoch = int(last[-1].name[5:]) + 1
    else:
        cfg = LoraConfig(r=LORA["r"], lora_alpha=LORA["alpha"], lora_dropout=LORA["dropout"], target_modules=LORA["targets"], task_type="CAUSAL_LM")
        model = get_peft_model(model, cfg)
    model.enable_input_require_grads()
    n_trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    assert n_trainable > 0, "the adapter has no trainable parameters"
    dom_params = read_registry("DOM_FROZEN")
    rev = s5_lib.model_revision(base)
    # tokenize
    enc = []
    for e in train_ex:
        ids = tok(e["text"] + tok.eos_token, add_special_tokens=True, truncation=True, max_length=MAX_LEN).input_ids
        enc.append(ids)
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=lr, weight_decay=0.0)
    steps_per_epoch = math.ceil(len(enc) / (batch * accum))
    total_steps = max(1, steps_per_epoch * (epochs - start_epoch))
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: 0.5 * (1 + math.cos(math.pi * min(1.0, s / total_steps))))
    curve = list(((read_registry("TRAINING") or {}).get(name) or {}).get("curve") or []) if resume else []
    pad = tok.pad_token_id
    for ep in range(start_epoch, epochs):
        model.train()
        order = list(range(len(enc)))
        random.Random(seed + ep).shuffle(order)
        t_ep = time.time()
        loss_sum, loss_n, step = 0.0, 0, 0
        cur_batch = batch
        i = 0
        while i < len(order):
            chunk = [enc[j] for j in order[i:i + cur_batch]]
            L = max(len(c) for c in chunk)
            ids = torch.full((len(chunk), L), pad, dtype=torch.long)
            att = torch.zeros((len(chunk), L), dtype=torch.long)
            for k, c in enumerate(chunk):
                ids[k, :len(c)] = torch.tensor(c)
                att[k, :len(c)] = 1
            labels = ids.clone()
            labels[att == 0] = -100
            try:
                out = model(input_ids=ids.to("cuda"), attention_mask=att.to("cuda"), labels=labels.to("cuda"))
                (out.loss / accum).backward()
            except torch.cuda.OutOfMemoryError:
                opt.zero_grad(set_to_none=True)
                torch.cuda.empty_cache()
                if cur_batch > 1:
                    cur_batch = max(1, cur_batch // 2)
                    print(f"OOM: batch halved to {cur_batch}", flush=True)
                    continue
                raise
            loss_sum += float(out.loss)
            loss_n += 1
            i += len(chunk)
            step += 1
            if step % 25 == 0:
                print(f"epoch {ep} step {step} examples {i}/{len(order)} loss {loss_sum / max(1, loss_n):.4f} elapsed {time.time() - t_ep:.0f}s", flush=True)
            if step % accum == 0:
                torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], 1.0)
                opt.step()
                sched.step()
                opt.zero_grad(set_to_none=True)
        opt.step()
        opt.zero_grad(set_to_none=True)
        ep_dir = out_dir / f"epoch{ep}"
        model.save_pretrained(str(ep_dir))
        model.eval()
        model.config.use_cache = True
        ev = eval_next_move(model, tok, held, dom_params, max_worlds=(24 if pilot else 80))
        hl = eval_loss(model, tok, held_txt)
        model.config.use_cache = False
        rec = {"epoch": ep, "train_loss": loss_sum / max(1, loss_n), "heldout_loss": hl, **ev, "epoch_s": round(time.time() - t_ep, 1),
               "batch": cur_batch, "n_examples": len(enc), "at": now_iso()}
        curve.append(rec)
        update_registry("TRAINING", lambda t: {**t, name: {"base": base, "revision": rev, "seed": seed, "lr": lr, "lora": LORA,
                                                           "n_trainable": n_trainable, "curve": curve, "corpus_s": round(corpus_s, 1),
                                                           "pilot": pilot, "env": s5_lib.env_versions(), "at": now_iso()}})
        print(json.dumps(rec), flush=True)
    # freeze the best epoch by held-out next-move score (chosen on POP held-out only)
    scored = [c for c in curve if c.get("fm_next_move_ls") is not None]
    best = max(scored, key=lambda c: c["fm_next_move_ls"]) if scored else curve[-1]
    frozen = out_dir / "frozen"
    if frozen.exists():
        shutil.rmtree(frozen)
    shutil.copytree(out_dir / f"epoch{best['epoch']}", frozen)
    sha = adapter_hash(frozen)
    band_ok = best.get("gap_fm_minus_dom") is not None and best["gap_fm_minus_dom"] >= -EXPERTISE_BAND_NATS
    miss = None if best.get("gap_fm_minus_dom") is None else max(0.0, -EXPERTISE_BAND_NATS - best["gap_fm_minus_dom"])
    rec = {"base": base, "revision": rev, "path": str(frozen), "sha": sha, "epoch": best["epoch"], "heldout": best,
           "band_ok": band_ok, "band_miss_nats": miss, "pilot": pilot, "seed": seed, "frozen_at": now_iso(),
           "training_lineages_registry": "POP_CORPUS"}
    update_registry("ADAPTERS", lambda a: {**a, name: rec})
    print(json.dumps({"frozen": str(frozen), "sha": sha, "best_epoch": best["epoch"], "band_ok": band_ok, "miss": miss}), flush=True)
    del model
    torch.cuda.empty_cache()
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reader", required=True, choices=sorted(BASES))
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--n-train", type=int, default=1600)
    ap.add_argument("--n-heldout", type=int, default=60)
    ap.add_argument("--seed", type=int, default=8001)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--batch", type=int, default=4)
    ap.add_argument("--accum", type=int, default=2)
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--tag", default="")
    ap.add_argument("--no-lock", action="store_true", help="the caller holds the GPU lock")
    a = ap.parse_args()
    if a.pilot:
        a.epochs, a.n_train, a.n_heldout = 1, min(a.n_train, 400), 12
    if a.no_lock:
        train(a.reader, a.epochs, a.n_train, a.n_heldout, a.seed, a.lr, a.batch, a.accum, a.pilot, a.resume, a.tag)
    else:
        with s5_lib.GpuSession(f"s8_train_{a.reader}"):
            train(a.reader, a.epochs, a.n_train, a.n_heldout, a.seed, a.lr, a.batch, a.accum, a.pilot, a.resume, a.tag)
    return 0


if __name__ == "__main__":
    sys.exit(main())
