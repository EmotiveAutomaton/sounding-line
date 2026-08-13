"""G147 — recreate the PAN 2024 hard-split winner (nycu-nlp) from its notebook paper.

The published 0.863 lives on the TIRA-held-back test set nobody can access, so the exact-value
gates are the notebook's own VALIDATION table (its Table 1, read at source by the pin agent):

    single roberta-base                     0.9435 / 0.8436 / 0.8423   (easy/medium/HARD)
    single microsoft/deberta-base (v1)      0.9584 / 0.8408 / 0.8567
    single nghuyong/ernie-2.0-base-en       0.9550 / 0.8496 / 0.8490
    3-model majority vote (the system)      0.9716 / 0.8626 / 0.8658

Stated by the paper (S2, READ): consecutive-paragraph pairs, max_length 256, lr 5e-5, dropout
0.25, epochs 10, batch 60, MLP head, majority vote of three; hard uses NO LaBSE stage; training
data = PAN24 hard train + PAN23 hard train (4,200 docs each). Metric = POOLED two-class macro-F1
over all pairs in the split (the official evaluator's form, confirmed against six published
baseline back-calculations; documents with a changes-length mismatch are silently dropped).

UNSTATED by the paper, chosen here and recorded (the faithful-arm convention): optimizer AdamW
(HF default), no warmup, weight_decay 0.0, loss CrossEntropy on a Linear head over CLS with the
stated 0.25 dropout, pair encoding tokenizer(p_i, p_j) with longest-first truncation, seed 42,
final-epoch checkpoint (per-epoch validation scores recorded so the checkpoint-rule sensitivity
is measurable, the ScholaWrite lesson).

Arms:
    --encoder roberta|deberta|ernie    train one member, save per-problem validation predictions
    --vote                             majority-vote the three saved prediction files, score

Output: results/pan_winner/{tag}.json (+ predictions beside it). 12 GB: batch 30 x accum 2
preserves the effective 60.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "pan_winner"
PAN24 = REPO / "corpora" / "public" / "pan_style" / "pan2024"
PAN23_HARD = (REPO / "corpora" / "public" / "pan_style" / "pan2023" / "release"
              / "pan23-multi-author-analysis-dataset3"
              / "pan23-multi-author-analysis-dataset3-train")

ENCODERS = {
    "roberta": "roberta-base",
    "deberta": "microsoft/deberta-base",
    "ernie": "nghuyong/ernie-2.0-base-en",
}
GATES_HARD = {"roberta": 0.8423, "deberta": 0.8567, "ernie": 0.8490, "vote": 0.8658}


def load_split(d: Path) -> list[dict]:
    """Problems as {id, paragraphs, changes}; mismatched docs recorded, not silently eaten."""
    out = []
    for t in sorted(d.glob("truth-problem-*.json")):
        pid = t.stem.replace("truth-", "")
        p = d / f"{pid}.txt"
        if not p.exists():
            continue
        truth = json.loads(t.read_text(encoding="utf-8"))
        paras = [x for x in p.read_text(encoding="utf-8", errors="replace").split("\n")
                 if x.strip()]
        out.append({"id": pid, "paragraphs": paras, "changes": truth["changes"],
                    "ok": len(paras) == len(truth["changes"]) + 1})
    return out


def pooled_macro_f1(truths: list[list[int]], preds: list[list[int]]) -> float:
    from itertools import chain                                        # noqa: PLC0415

    from sklearn.metrics import f1_score                               # noqa: PLC0415
    keep_t, keep_p = [], []
    for t, s in zip(truths, preds):
        if len(t) == len(s):                       # the evaluator drops mismatches silently
            keep_t.append(t)
            keep_p.append(s)
    return float(f1_score(list(chain.from_iterable(keep_t)),
                          list(chain.from_iterable(keep_p)),
                          average="macro", labels=[0, 1], zero_division=0))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--encoder", choices=sorted(ENCODERS), default=None)
    ap.add_argument("--vote", action="store_true")
    ap.add_argument("--difficulty", default="hard")
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--batch", type=int, default=30)
    ap.add_argument("--accum", type=int, default=2)
    ap.add_argument("--max-len", type=int, default=256)
    ap.add_argument("--lr", type=float, default=5e-5)
    ap.add_argument("--dropout", type=float, default=0.25)
    ap.add_argument("--warmup", type=float, default=0.0,
                    help="linear warmup ratio. Unstated by the paper; roberta-base collapsed "
                         "to constant predictions without it at their lr, so its arm runs 0.06 "
                         "as a recorded divergence-fix assumption")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--no-2023", action="store_true",
                    help="drop the PAN23 augmentation (the paper uses it for medium+hard)")
    args = ap.parse_args()

    RESULTS.mkdir(parents=True, exist_ok=True)
    val = load_split(PAN24 / args.difficulty / "validation")
    val_ok = [p for p in val if p["ok"]]
    print(f"validation: {len(val)} problems, {sum(not p['ok'] for p in val)} mismatched",
          flush=True)

    if args.vote:
        preds = {}
        for enc in sorted(ENCODERS):
            f = RESULTS / f"{enc}_{args.difficulty}_val_preds.json"
            if not f.exists():
                print(f"missing {f.name}; train the {enc} arm first")
                sys.exit(1)
            preds[enc] = json.loads(f.read_text(encoding="utf-8"))
        ids = [p["id"] for p in val_ok]
        truths = [p["changes"] for p in val_ok]
        voted = []
        for pid, t in zip(ids, truths):
            members = [preds[e].get(pid, []) for e in sorted(ENCODERS)]
            if any(len(m) != len(t) for m in members):
                voted.append([])                    # scored as a dropped mismatch
                continue
            voted.append([1 if sum(m[i] for m in members) >= 2 else 0
                          for i in range(len(t))])
        f1 = pooled_macro_f1(truths, voted)
        gate = GATES_HARD["vote"]
        out = {"arm": "vote", "difficulty": args.difficulty, "macro_f1": f1,
               "gate_validation": gate, "delta": f1 - gate,
               "members": sorted(ENCODERS)}
        (RESULTS / f"vote_{args.difficulty}.json").write_text(
            json.dumps(out, indent=1), encoding="utf-8", newline="\n")
        print(f"VOTE {args.difficulty}: {f1:.4f} vs gate {gate} (delta {f1 - gate:+.4f})")
        return

    import numpy as np                                                 # noqa: PLC0415
    import torch                                                       # noqa: PLC0415
    from torch.utils.data import DataLoader, Dataset                   # noqa: PLC0415
    from transformers import (AutoModelForSequenceClassification,      # noqa: PLC0415
                              AutoTokenizer)

    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock  # noqa: PLC0415

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    train = load_split(PAN24 / args.difficulty / "train")
    n23 = 0
    if not args.no_2023 and args.difficulty in ("medium", "hard"):
        extra = load_split(PAN23_HARD if args.difficulty == "hard" else PAN23_HARD)
        n23 = len(extra)
        train = train + [{**p, "id": "p23_" + p["id"]} for p in extra]
    pairs = [(p["paragraphs"][i], p["paragraphs"][i + 1], p["changes"][i])
             for p in train if p["ok"] for i in range(len(p["changes"]))]
    print(f"train: {len(train)} problems ({n23} from PAN23), {len(pairs)} pairs", flush=True)

    name = ENCODERS[args.encoder]
    acquire_gpu_lock(f"pan_{args.encoder}")
    tok = AutoTokenizer.from_pretrained(name)
    model = AutoModelForSequenceClassification.from_pretrained(name, num_labels=2)
    # the stated dropout, applied where the architecture exposes it
    if hasattr(model, "dropout") and isinstance(model.dropout, torch.nn.Dropout):
        model.dropout.p = args.dropout
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(dev)

    class Pairs(Dataset):
        def __init__(self, rows):
            self.rows = rows

        def __len__(self):
            return len(self.rows)

        def __getitem__(self, i):
            a, b, y = self.rows[i]
            return a, b, y

    def collate(batch):
        a, b, y = zip(*batch)
        enc = tok(list(a), list(b), truncation=True, max_length=args.max_len,
                  padding=True, return_tensors="pt")
        return enc, torch.tensor(y)

    dl = DataLoader(Pairs(pairs), batch_size=args.batch, shuffle=True,
                    collate_fn=collate, num_workers=0)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.0)
    sched = None
    if args.warmup > 0:
        from transformers import get_linear_schedule_with_warmup      # noqa: PLC0415
        total = (len(dl) // args.accum + 1) * args.epochs
        sched = get_linear_schedule_with_warmup(opt, int(total * args.warmup), total)
    scaler = torch.amp.GradScaler("cuda", enabled=dev == "cuda")

    def predict_validation() -> dict[str, list[int]]:
        model.eval()
        out = {}
        with torch.no_grad():
            for p in val_ok:
                vp = [(p["paragraphs"][i], p["paragraphs"][i + 1])
                      for i in range(len(p["changes"]))]
                preds = []
                for j in range(0, len(vp), 64):
                    a, b = zip(*vp[j:j + 64])
                    enc = tok(list(a), list(b), truncation=True, max_length=args.max_len,
                              padding=True, return_tensors="pt").to(dev)
                    with torch.amp.autocast("cuda", enabled=dev == "cuda"):
                        logits = model(**enc).logits
                    preds.extend(logits.argmax(-1).tolist())
                out[p["id"]] = preds
        model.train()
        return out

    truths = [p["changes"] for p in val_ok]
    history = []
    model.train()
    for ep in range(args.epochs):
        for bi, (enc, y) in enumerate(dl):
            enc = {k: v.to(dev) for k, v in enc.items()}
            y = y.to(dev)
            with torch.amp.autocast("cuda", enabled=dev == "cuda"):
                loss = torch.nn.functional.cross_entropy(model(**enc).logits, y)
            scaler.scale(loss / args.accum).backward()
            if (bi + 1) % args.accum == 0:
                scaler.step(opt)
                scaler.update()
                if sched is not None:
                    sched.step()
                opt.zero_grad()
            if bi % 100 == 0:
                print(f"epoch {ep} batch {bi} loss {loss.item():.3f}", flush=True)
        vp = predict_validation()
        f1 = pooled_macro_f1(truths, [vp[p["id"]] for p in val_ok])
        history.append(f1)
        print(f"epoch {ep} validation macro-F1 {f1:.4f}", flush=True)

    preds = predict_validation()
    f1 = pooled_macro_f1(truths, [preds[p["id"]] for p in val_ok])
    gate = GATES_HARD.get(args.encoder)
    (RESULTS / f"{args.encoder}_{args.difficulty}_val_preds.json").write_text(
        json.dumps(preds), encoding="utf-8", newline="\n")
    out = {"arm": args.encoder, "checkpoint": name, "difficulty": args.difficulty,
           "macro_f1_final_epoch": f1, "per_epoch_validation": history,
           "best_epoch_f1": max(history), "gate_validation": gate, "delta": f1 - gate,
           "n_train_pairs": len(pairs), "n_pan23_problems": n23,
           "assumptions": f"AdamW wd=0, warmup {args.warmup}, CE loss, CLS linear head, "
                          "pair-encoded longest-first truncation, seed 42, final epoch",
           "hypers": {"lr": args.lr, "batch_effective": args.batch * args.accum,
                      "epochs": args.epochs, "max_len": args.max_len,
                      "dropout": args.dropout, "warmup": args.warmup}}
    (RESULTS / f"{args.encoder}_{args.difficulty}.json").write_text(
        json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print(f"\n{args.encoder} {args.difficulty}: final {f1:.4f} vs gate {gate} "
          f"(delta {f1 - gate:+.4f}); best epoch {max(history):.4f}")
    release_gpu_lock()


if __name__ == "__main__":
    main()
