"""G148 — recreate the PAN 2025 hard-split winner (wqd) against the LABELED TEST SPLIT we hold.

The consensus fleet (L109) verified the 2025 test split in our store is genuine: the printed
test baselines reproduce from it to 0.0004. That makes this the phase's first reachable
TEST-set exact-value gate. The winner's system is fully specified in its notebook (pinned at
source, L102 fleet): single microsoft/deberta-base; sentence-level task; NLTK sent_tokenize
after newlines become spaces; pairs (s_i, s_{i+1}) labeled changes[i]; documents skipped when
len(sentences) != len(changes)+1 (their stated rule); [CLS] hidden state into a two-layer
linear head with ReLU and Dropout; BCEWithLogitsLoss; AdamW lr 1e-5; batch 16; max_length 128
with padding; 5 epochs; checkpoint = best validation F1 (their stated rule).

Gates: printed TEST hard 0.830 (easy 0.958, medium 0.823); their validation hard 0.8331.

Named assumptions (unstated by the notebook): head hidden width 768, dropout 0.1, seed 42,
fp32 (DeBERTa-v1 overflows under fp16 autocast, L104). Contamination gate per LESSONS §1d:
train-vs-test and train-vs-validation exact-hash overlap computed and recorded BEFORE
training; a train-test pair overlap above one percent aborts the arm loudly.

Output: results/pan25_winner/wqd_{difficulty}.json + test/val predictions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "pan25_winner"
PAN25 = REPO / "corpora" / "public" / "pan_style" / "pan2025"
GATES_TEST = {"easy": 0.958, "medium": 0.823, "hard": 0.830}
GATES_VAL = {"easy": 0.9558, "medium": 0.8414, "hard": 0.8331}


def versions() -> dict:
    import sklearn                                                     # noqa: PLC0415
    import torch                                                       # noqa: PLC0415
    import transformers                                                # noqa: PLC0415
    return {"transformers": transformers.__version__, "torch": torch.__version__,
            "sklearn": sklearn.__version__}


def load_split(d: Path) -> list[dict]:
    from nltk.tokenize import sent_tokenize                            # noqa: PLC0415
    out = []
    for t in sorted(d.glob("truth-problem-*.json")):
        pid = t.stem.replace("truth-", "")
        p = d / f"{pid}.txt"
        if not p.exists():
            continue
        truth = json.loads(t.read_text(encoding="utf-8"))
        text = p.read_text(encoding="utf-8", errors="replace").replace("\n", " ")
        sents = sent_tokenize(text)
        out.append({"id": pid, "sents": sents, "changes": truth["changes"],
                    "ok": len(sents) == len(truth["changes"]) + 1})
    return out


def pooled_macro_f1(truths, preds):
    from itertools import chain                                        # noqa: PLC0415

    from sklearn.metrics import f1_score                               # noqa: PLC0415
    keep_t, keep_p = [], []
    for t, s in zip(truths, preds):
        if len(t) == len(s):
            keep_t.append(t)
            keep_p.append(s)
    return float(f1_score(list(chain.from_iterable(keep_t)),
                          list(chain.from_iterable(keep_p)),
                          average="macro", labels=[0, 1], zero_division=0))


def overlap(a: list[dict], b: list[dict]) -> dict:
    def pairs(ps):
        return {hashlib.md5((q["sents"][i].strip() + "|P|" + q["sents"][i + 1].strip())
                            .encode()).hexdigest()
                for q in ps if q["ok"] for i in range(len(q["changes"]))}
    pa, pb = pairs(a), pairs(b)
    return {"pairs_b": len(pb), "shared": len(pa & pb),
            "share": (len(pa & pb) / len(pb)) if pb else 0.0}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--difficulty", default="hard")
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--max-len", type=int, default=128)
    ap.add_argument("--lr", type=float, default=1e-5)
    ap.add_argument("--hidden", type=int, default=768)
    ap.add_argument("--dropout", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--channels", default="",
                    help="G150 fusion arm: path prefix of the channel matrices "
                         "(results/pan25_channels/hard); concatenates the 158-dim "
                         "pair channels to the CLS embedding before the head. "
                         "Standardized on TRAIN statistics only")
    ap.add_argument("--out-tag", default="",
                    help="suffix so A/B arms never clobber")
    args = ap.parse_args()

    import numpy as np                                                 # noqa: PLC0415
    import torch                                                       # noqa: PLC0415
    from torch import nn                                               # noqa: PLC0415
    from torch.utils.data import DataLoader, Dataset                   # noqa: PLC0415
    from transformers import AutoModel, AutoTokenizer                  # noqa: PLC0415

    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock  # noqa: PLC0415

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    RESULTS.mkdir(parents=True, exist_ok=True)

    d = args.difficulty
    train = load_split(PAN25 / d / "train")
    val = load_split(PAN25 / d / "validation")
    test = load_split(PAN25 / d / "test")
    for name, sp in (("train", train), ("validation", val), ("test", test)):
        print(f"{name}: {len(sp)} problems, {sum(not q['ok'] for q in sp)} "
              f"length-mismatched (skipped per their rule)", flush=True)

    # LESSONS §1d: the contamination gate runs before any training
    o_test = overlap(train, test)
    o_val = overlap(train, val)
    print(f"contamination: train-vs-test shared pairs {o_test['shared']} "
          f"({o_test['share']:.2%}); train-vs-val {o_val['shared']} ({o_val['share']:.2%})",
          flush=True)
    if o_test["share"] > 0.01:
        print(">>> ABORT: train-test overlap above one percent; the gate is not honest")
        sys.exit(1)

    pairs = [(q["sents"][i], q["sents"][i + 1], float(q["changes"][i]), q["id"], i)
             for q in train if q["ok"] for i in range(len(q["changes"]))]
    print(f"train pairs: {len(pairs)}", flush=True)

    # ── G150 channels: per-pair 158-dim vectors aligned to load_split order, standardized
    # on TRAIN statistics only so no eval-side numbers enter the representation
    CH = None
    if args.channels:
        import numpy as _np
        CH = {}
        mu = sd = None
        for split_name, probs in (("train", train), ("validation", val), ("test", test)):
            X = _np.load(f"{args.channels}_{split_name}.npz")["X"].astype("float32")
            meta = json.loads(Path(f"{args.channels}_{split_name}_meta.json")
                              .read_text(encoding="utf-8"))
            if split_name == "train":
                mu, sd = X.mean(0), X.std(0) + 1e-6
            X = (X - mu) / sd
            k = 0
            for m in meta["problems"]:
                for i in range(m["n_pairs"]):
                    CH[(m["id"], i)] = X[k]
                    k += 1
            assert k == X.shape[0], (split_name, k, X.shape)
        print(f"channels: {len(CH)} pair vectors x {X.shape[1]} dims", flush=True)

    acquire_gpu_lock("pan25_wqd")
    tok = AutoTokenizer.from_pretrained("microsoft/deberta-base")
    dev = "cuda" if torch.cuda.is_available() else "cpu"

    n_chan = 0 if CH is None else next(iter(CH.values())).shape[0]

    class Wqd(nn.Module):
        def __init__(self):
            super().__init__()
            self.enc = AutoModel.from_pretrained("microsoft/deberta-base")
            self.head = nn.Sequential(
                nn.Linear(self.enc.config.hidden_size + n_chan, args.hidden), nn.ReLU(),
                nn.Dropout(args.dropout), nn.Linear(args.hidden, 1))

        def forward(self, chan=None, **enc):
            h = self.enc(**enc).last_hidden_state[:, 0]
            if chan is not None:
                h = torch.cat([h, chan], dim=1)
            return self.head(h).squeeze(-1)

    model = Wqd().to(dev)

    class Pairs(Dataset):
        def __init__(self, rows):
            self.rows = rows

        def __len__(self):
            return len(self.rows)

        def __getitem__(self, i):
            return self.rows[i]

    def collate(batch):
        a, b, y, pid, pi = zip(*batch)
        enc = tok(list(a), list(b), truncation=True, max_length=args.max_len,
                  padding="max_length", return_tensors="pt")
        chan = None
        if CH is not None:
            import numpy as _np
            chan = torch.from_numpy(_np.stack([CH[(p_, i_)] for p_, i_ in zip(pid, pi)]))
        return enc, chan, torch.tensor(y)

    dl = DataLoader(Pairs(pairs), batch_size=args.batch, shuffle=True, collate_fn=collate)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr)
    loss_fn = nn.BCEWithLogitsLoss()

    def predict(split):
        model.eval()
        out = {}
        with torch.no_grad():
            for q in split:
                if not q["ok"]:
                    continue
                sp = [(q["sents"][i], q["sents"][i + 1]) for i in range(len(q["changes"]))]
                preds = []
                for j in range(0, len(sp), 64):
                    a, b = zip(*sp[j:j + 64])
                    enc = tok(list(a), list(b), truncation=True, max_length=args.max_len,
                              padding=True, return_tensors="pt").to(dev)
                    c = None
                    if CH is not None:
                        import numpy as _np
                        c = torch.from_numpy(_np.stack(
                            [CH[(q["id"], j + k_)] for k_ in range(len(a))])).to(dev)
                    preds.extend((model(chan=c, **enc) > 0).long().tolist())
                out[q["id"]] = preds
        model.train()
        return out

    def score(split, preds):
        ok = [q for q in split if q["ok"]]
        return pooled_macro_f1([q["changes"] for q in ok],
                               [preds.get(q["id"], []) for q in ok])

    best_f1, best_state, history = -1.0, None, []
    model.train()
    for ep in range(args.epochs):
        for bi, (enc, chan, y) in enumerate(dl):
            enc = {k: v.to(dev) for k, v in enc.items()}
            c = chan.to(dev) if chan is not None else None
            loss = loss_fn(model(chan=c, **enc), y.to(dev))
            opt.zero_grad()
            loss.backward()
            opt.step()
            if bi % 200 == 0:
                print(f"epoch {ep} batch {bi} loss {loss.item():.3f}", flush=True)
        vp = predict(val)
        vf1 = score(val, vp)
        history.append(vf1)
        print(f"epoch {ep} validation macro-F1 {vf1:.4f}", flush=True)
        if vf1 > best_f1:
            best_f1 = vf1
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}

    model.load_state_dict(best_state)          # their stated rule: best validation checkpoint
    val_preds = predict(val)
    test_preds = predict(test)
    val_f1 = score(val, val_preds)
    test_f1 = score(test, test_preds)
    out = {"arm": "wqd", "difficulty": d, "test_macro_f1": test_f1,
           "channels": bool(args.channels), "n_channel_dims": n_chan,
           "gate_test_printed": GATES_TEST[d], "delta_test": test_f1 - GATES_TEST[d],
           "val_macro_f1_best": val_f1, "gate_val_printed": GATES_VAL[d],
           "per_epoch_val": history, "n_train_pairs": len(pairs),
           "contamination": {"train_vs_test": o_test, "train_vs_val": o_val},
           "assumptions": f"head hidden {args.hidden}, dropout {args.dropout}, seed "
                          f"{args.seed}, fp32",
           "hypers": {"lr": args.lr, "batch": args.batch, "epochs": args.epochs,
                      "max_len": args.max_len},
           "versions": versions()}
    (RESULTS / f"wqd_{d}{args.out_tag}.json").write_text(json.dumps(out, indent=1),
                                           encoding="utf-8", newline="\n")
    (RESULTS / f"wqd_{d}{args.out_tag}_test_preds.json").write_text(json.dumps(test_preds),
                                                      encoding="utf-8", newline="\n")
    (RESULTS / f"wqd_{d}{args.out_tag}_val_preds.json").write_text(json.dumps(val_preds),
                                                     encoding="utf-8", newline="\n")
    print(f"\nWQD {d}: TEST {test_f1:.4f} vs printed {GATES_TEST[d]} "
          f"(delta {test_f1 - GATES_TEST[d]:+.4f}); val best {val_f1:.4f} vs "
          f"{GATES_VAL[d]}")
    release_gpu_lock()


if __name__ == "__main__":
    main()
