"""G141 — recreate the ScholaWrite intention-prediction baselines, exact-value standard.

Published gates (fetched 2026-08-10): fine-tuned BERT weighted F1 0.64, RoBERTa 0.64,
Llama-8B-Instruct 0.13, GPT-4o 0.08; 15 intention classes in three Flower-Hayes groups;
61,504 keystroke edits, ten writers, five preprints; inter-annotator agreement 0.71.

Arms:
    --arm download   pull the dataset from the hub, dump its schema and split structure, cache
                     locally; FAILS LOUDLY if the schema surprises, writing the dump instead
    --arm bert       fine-tune bert-base-uncased on before-text -> intention, their split if the
                     dataset ships one (else grouped by preprint, recorded as the deviation);
                     weighted F1 against the 0.64 gate
    --arm roberta    the same for roberta-base, same gate
    --arm reader     the local model zero-shot on the test split with the 15 labels, the analogue
                     of their generative baselines (their Llama-8B managed 0.13)

PASS per arm = weighted F1 within 0.01 of the published number. The encoder arms are the load-
bearing ones; a large shortfall means our model of their task construction is wrong (input
windowing, label granularity, split), and the confusion matrix is the search map.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "scholawrite"
CACHE = RESULTS / "hf_cache"
OLLAMA = "http://127.0.0.1:11434/api/generate"
GATES = {"bert": 0.64, "roberta": 0.64, "reader": 0.13}
GPU_LOCK = REPO / "results" / ".gpu.lock"


def release_gpu_lock() -> None:
    try:
        GPU_LOCK.unlink()
    except OSError:
        pass


def acquire_gpu_lock() -> None:
    """One GPU training at a time, whatever shard we run on. Stale after 5h."""
    import atexit                                                     # noqa: PLC0415
    import os                                                         # noqa: PLC0415
    import time                                                       # noqa: PLC0415
    while True:
        try:
            fd = os.open(GPU_LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            atexit.register(release_gpu_lock)
            return
        except FileExistsError:
            try:
                age = time.time() - GPU_LOCK.stat().st_mtime
            except OSError:
                continue
            if age > 5 * 3600:
                release_gpu_lock()
                continue
            print("  gpu lock held, waiting 120s", flush=True)
            time.sleep(120)


def load_local():
    from datasets import load_from_disk                               # noqa: PLC0415
    return load_from_disk(str(RESULTS / "dataset"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True,
                    choices=["download", "bert", "roberta", "reader"])
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--eval", default="test", choices=["test", "test_small"],
                    help="evaluate on this shipped split (train always the shipped train)")
    ap.add_argument("--lopo", type=int, default=None,
                    help="leave-one-project-out fold index; overrides --eval")
    ap.add_argument("--faithful", action="store_true",
                    help="the authors' exact protocol per the 2026-08-11 subagent pin: "
                         "full before-text head-truncated at 512, the <INPUT><BT>...</BF> "
                         "wrapper with its published typo, six added special tokens, balanced "
                         "class weights with the arange hack, seed 42; pair with --epochs 10")
    args = ap.parse_args()
    RESULTS.mkdir(parents=True, exist_ok=True)

    if args.arm == "download":
        from datasets import load_dataset                             # noqa: PLC0415
        last_err = None
        for hub_id in ("minnesotanlp/scholawrite", "minnesotanlp/ScholaWrite"):
            try:
                ds = load_dataset(hub_id, cache_dir=str(CACHE))
                break
            except Exception as e:                                    # noqa: BLE001
                last_err = e
                ds = None
        if ds is None:
            (RESULTS / "download_error.txt").write_text(str(last_err), encoding="utf-8")
            print(f">>> DOWNLOAD-FAILED: {last_err}")
            sys.exit(1)
        schema = {split: {"n": len(ds[split]), "columns": ds[split].column_names}
                  for split in ds}
        print("schema:", json.dumps(schema, indent=1))
        sample = {k: str(v)[:160] for k, v in ds[list(ds.keys())[0]][0].items()}
        ds.save_to_disk(str(RESULTS / "dataset"))
        (RESULTS / "schema.json").write_text(json.dumps(
            {"schema": schema, "sample": sample}, indent=1), encoding="utf-8", newline="\n")
        print(f"wrote {(RESULTS / 'schema.json').relative_to(REPO)}")
        return

    ds = load_local()
    schema = json.loads((RESULTS / "schema.json").read_text(encoding="utf-8"))["schema"]
    splits = list(ds.keys())
    label_col = next((c for c in ds[splits[0]].column_names
                      if re.search(r"intention|label", c, re.I)), None)
    text_col = next((c for c in ds[splits[0]].column_names
                     if re.search(r"before|text|input", c, re.I)), None)
    if not label_col or not text_col:
        print(f">>> SCHEMA-SURPRISE: columns {ds[splits[0]].column_names}; no verdict")
        sys.exit(1)
    print(f"using text column {text_col!r}, label column {label_col!r}, splits {splits}")

    suffix = ""
    if args.lopo is not None:
        from datasets import concatenate_datasets                     # noqa: PLC0415
        proj_col = next((c for c in ds[splits[0]].column_names
                         if re.search(r"project|preprint|doc", c, re.I)), None)
        if not proj_col:
            print(f">>> SCHEMA-SURPRISE: no project column in "
                  f"{ds[splits[0]].column_names}; no verdict")
            sys.exit(1)
        whole = concatenate_datasets([ds["train"], ds["test"]])
        projects = sorted(set(whole[proj_col]))
        held = projects[args.lopo % len(projects)]
        train = whole.filter(lambda r: r[proj_col] != held)
        test = whole.filter(lambda r: r[proj_col] == held)
        split_note = f"leave-one-project-out, held out {held!r} of {len(projects)}"
        suffix = f"_lopo{args.lopo}"
    elif args.eval == "test_small" and "test_small" in splits:
        train, test = ds["train"], ds["test_small"]
        split_note = "shipped train, evaluated on shipped test_small"
        suffix = "_testsmall"
    elif "train" in splits and "test" in splits:
        train, test = ds["train"], ds["test"]
        split_note = "their split"
    else:
        whole = ds[splits[0]].train_test_split(test_size=0.2, seed=42)
        train, test = whole["train"], whole["test"]
        split_note = "80/20 seed-42 (no published split shipped; recorded deviation)"
    if args.faithful:
        suffix += "_faithful"
    labels = sorted(set(train[label_col]) | set(test[label_col]))
    lab2i = {l: i for i, l in enumerate(labels)}
    print(f"{len(train)} train / {len(test)} test, {len(labels)} labels ({split_note})")

    if args.arm == "reader":
        import numpy as np                                            # noqa: PLC0415
        from sklearn.metrics import f1_score                          # noqa: PLC0415
        rng = np.random.default_rng(31)
        n = min(1500, len(test))
        pick_idx = rng.choice(len(test), size=n, replace=False)
        opts = "\n".join(f"- {l}" for l in labels)
        preds, truths = [], []
        part = RESULTS / "reader_partial.jsonl"
        done = set()
        if part.exists():
            for line in part.read_text(encoding="utf-8").splitlines():
                done.add(json.loads(line)["i"])
        with part.open("a", encoding="utf-8", newline="\n") as fh:
            for j, i in enumerate(pick_idx):
                i = int(i)
                if i in done:
                    continue
                txt = str(test[i][text_col])[-1200:]
                req = urllib.request.Request(OLLAMA, data=json.dumps(
                    {"model": "qwen3.5:9b", "prompt":
                        f"A scholar is writing a LaTeX manuscript. Current text ends with:\n"
                        f"{txt}\nWhich writing intention best describes what they will do "
                        f"next? Answer with exactly one label from:\n{opts}\nLabel:",
                     "stream": False, "think": False,
                     "options": {"temperature": 0.0, "seed": 700 + i,
                                 "num_predict": 30}}).encode(),
                    headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=300) as r:
                    ans = json.loads(r.read()).get("response", "").lower()
                got = [l for l in labels if l.lower() in ans]
                pick = got[0] if got else labels[int(rng.integers(len(labels)))]
                fh.write(json.dumps({"i": i, "truth": test[i][label_col],
                                     "pick": pick}) + "\n")
                fh.flush()
                if (j + 1) % 100 == 0:
                    print(f"  {j + 1}/{n}", flush=True)
        rows = [json.loads(x) for x in part.read_text(encoding="utf-8").splitlines()]
        truths = [r["truth"] for r in rows]
        preds = [r["pick"] for r in rows]
        f1 = float(f1_score(truths, preds, average="weighted", labels=labels,
                            zero_division=0))
        out = {"arm": "reader", "n": len(rows), "weighted_f1": f1,
               "gate_llama8b": GATES["reader"], "split": split_note}
        print(f"reader weighted-F1 {f1:.3f} (their Llama-8B: 0.13)")
    else:
        import numpy as np                                            # noqa: PLC0415
        import torch                                                  # noqa: PLC0415
        from torch.utils.data import DataLoader                       # noqa: PLC0415
        from sklearn.metrics import f1_score                          # noqa: PLC0415
        from transformers import (AutoModelForSequenceClassification,  # noqa: PLC0415
                                  AutoTokenizer)
        name = {"bert": "bert-base-uncased", "roberta": "roberta-base"}[args.arm]
        acquire_gpu_lock()
        if args.faithful:
            torch.manual_seed(42)
            np.random.seed(42)
        tok = AutoTokenizer.from_pretrained(name)
        model = AutoModelForSequenceClassification.from_pretrained(
            name, num_labels=len(labels))
        if args.faithful:
            for t in ("<INPUT>", "</INPUT>", "<BT>", "</BT>", "<PWA>", "</PWA>"):
                tok.add_tokens(t)
            model.resize_token_embeddings(len(tok))
        model = model.cuda()

        def make_loader(split, shuffle):
            if args.faithful:
                # Their exact input: full before-text, head-kept by right truncation at
                # model_max_length; the </BF> closing tag is the published run's typo, kept.
                texts = ["<INPUT><BT>" + str(x) + "</BF> </INPUT>"
                         for x in split[text_col]]
                enc = tok(texts, truncation=True, padding="max_length",
                          return_tensors="pt")
            else:
                enc = tok([str(x)[-1500:] for x in split[text_col]], truncation=True,
                          max_length=512, padding="max_length", return_tensors="pt")
            ys = torch.tensor([lab2i[l] for l in split[label_col]])
            data = torch.utils.data.TensorDataset(enc["input_ids"],
                                                  enc["attention_mask"], ys)
            return DataLoader(data, batch_size=16, shuffle=shuffle)

        tr_loader = make_loader(train, True)
        te_loader = make_loader(test, False)
        opt = torch.optim.AdamW(model.parameters(), lr=2e-5)
        loss_fn = None
        if args.faithful:
            from sklearn.utils.class_weight import compute_class_weight  # noqa: PLC0415
            y_tr = np.array([lab2i[l] for l in train[label_col]])
            aug = np.concatenate((y_tr, np.arange(len(labels))))
            cw = compute_class_weight(class_weight="balanced",
                                      classes=np.unique(aug), y=aug)
            cwt = torch.tensor(cw, dtype=torch.float)
            cwt = cwt / cwt.sum()
            loss_fn = torch.nn.CrossEntropyLoss(weight=cwt.cuda())
        model.train()
        for ep in range(args.epochs):
            for bi, (ids, mask, ys) in enumerate(tr_loader):
                opt.zero_grad()
                if loss_fn is not None:
                    logits = model(input_ids=ids.cuda(),
                                   attention_mask=mask.cuda()).logits
                    loss = loss_fn(logits, ys.cuda())
                else:
                    loss = model(input_ids=ids.cuda(), attention_mask=mask.cuda(),
                                 labels=ys.cuda()).loss
                loss.backward()
                opt.step()
                if bi % 100 == 0:
                    print(f"  epoch {ep} batch {bi} loss {float(loss):.3f}", flush=True)
        model.eval()
        preds, truths = [], []
        with torch.no_grad():
            for ids, mask, ys in te_loader:
                out_l = model(input_ids=ids.cuda(), attention_mask=mask.cuda()).logits
                preds.extend(out_l.argmax(-1).cpu().tolist())
                truths.extend(ys.tolist())
        f1 = float(f1_score(truths, preds, average="weighted", zero_division=0))
        out = {"arm": args.arm, "n_train": len(train), "n_test": len(test),
               "weighted_f1": f1, "gate": GATES[args.arm], "epochs": args.epochs,
               "split": split_note, "faithful": bool(args.faithful)}
        if args.faithful:
            from sklearn.metrics import classification_report            # noqa: PLC0415
            rep = classification_report([labels[t] for t in truths],
                                        [labels[p] for p in preds],
                                        output_dict=True, zero_division=0)
            out["per_class_f1"] = {k: round(v["f1-score"], 3) for k, v in rep.items()
                                   if isinstance(v, dict) and "f1-score" in v
                                   and k not in ("macro avg", "weighted avg")}
            out["report_weighted_f1"] = round(rep["weighted avg"]["f1-score"], 4)
            out["paper_inconsistency_note"] = (
                "the published 0.64 is unreachable from the paper's own v5 per-class "
                "table (~0.59 on test); the per-class profile is the sharper target")
        print(f"{args.arm} weighted-F1 {f1:.3f} (gate {GATES[args.arm]})")

    if args.lopo is not None:
        out["verdict"] = "DIAGNOSTIC"        # no published number for this protocol
    else:
        out["verdict"] = ("PASS" if abs(out["weighted_f1"] - GATES[args.arm]) <= 0.01
                          else "NOT-MATCHED")
    print(f"  >>> {out['verdict']}")
    out_path = RESULTS / f"{args.arm}{suffix}.json"
    out_path.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print(f"wrote {out_path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
