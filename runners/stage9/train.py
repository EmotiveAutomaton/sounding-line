"""Checkpointable local adapter fitting on an immutable prepared corpus.

DESIGN CHECK: LESSONS sections 1b, 1d, 3, 4 and 5; CONTROLS section 6.
NULL: changed corpus/recipe, absent optimizer/RNG state, or a partial checkpoint
cannot resume. ALTERNATIVE: complete optimizer-step boundaries resume the same
example order and schedule. bands: matching complete checkpoint or explicit error.
This module fits a package; it never grants competence or selects a scientific claim.
"""
from __future__ import annotations

import argparse
import math
import os
from pathlib import Path
import random
import sys
import time

from runners.stage9.common import REPO, ROOT, closure, digest, file_hash, freeze, read, write

BASES = {
    "qwen": {"model": "Qwen/Qwen2.5-1.5B-Instruct", "revision": "989aa7980e4cf806f80c7fef2b1adb7bc71aa306"},
    "smollm": {"model": "HuggingFaceTB/SmolLM2-1.7B-Instruct", "revision": "31b70e2e869a7173562077fd711b654946d38674"},
}
LORA = {"r": 16, "lora_alpha": 32, "lora_dropout": 0.05,
        "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"], "task_type": "CAUSAL_LM"}


def encode(tok, examples, max_length):
    """Preparation supplies prefix/target separately; generated context is never a label.

    Full-log replay examples have empty prefix. Token truncation is explicit in the
    receipt; target truncation is forbidden. Long context discards its oldest tokens.
    """
    out, context_dropped = [], 0
    vocabulary_size = len(tok)
    for row in examples:
        if "input_ids" in row:
            ids = row["input_ids"]
            labels = row.get("labels", ids)
            if not 2 <= len(ids) <= max_length or len(labels) != len(ids):
                raise ValueError("invalid prepared training tokens")
            if not all(isinstance(i, int) and 0 <= i < vocabulary_size for i in ids):
                raise ValueError("prepared token outside tokenizer vocabulary")
            if not all(y == -100 or y == x for x, y in zip(ids, labels)) or all(y == -100 for y in labels[1:]):
                raise ValueError("invalid prepared target mask")
            out.append({"ids": ids, "labels": labels, "key": row["key"]})
            continue
        prefix = tok(row.get("prefix", ""), add_special_tokens=True).input_ids
        target = tok(row["target"] + tok.eos_token, add_special_tokens=False).input_ids
        if len(target) >= max_length:
            raise ValueError("target exceeds frozen training maximum; prepare an explicit shorter example")
        budget = max_length - len(target)
        context_dropped += max(0, len(prefix) - budget)
        prefix = prefix[-budget:]
        if not prefix:
            # Empty full-log context still needs the model's ordinary BOS where present.
            ids = target
            labels = list(target)
        else:
            ids = prefix + target
            labels = [-100] * len(prefix) + target
        if len(ids) < 2:
            raise ValueError("no causal training target")
        out.append({"ids": ids, "labels": labels, "key": row["key"]})
    return out, {"examples": len(out), "supervised_tokens": sum(sum(v != -100 for v in x["labels"][1:]) for x in out),
                 "context_tokens_discarded": context_dropped, "target_tokens_discarded": 0,
                 "maximum_tokens": max(map(lambda x: len(x["ids"]), out))}


def batch_tensors(torch, examples, pad, device):
    length = max(len(e["ids"]) for e in examples)
    ids = torch.full((len(examples), length), pad, dtype=torch.long)
    labels = torch.full_like(ids, -100)
    attention = torch.zeros_like(ids)
    for i, row in enumerate(examples):
        n = len(row["ids"])
        ids[i, :n] = torch.tensor(row["ids"])
        labels[i, :n] = torch.tensor(row["labels"])
        attention[i, :n] = 1
    return {"input_ids": ids.to(device), "labels": labels.to(device), "attention_mask": attention.to(device)}


def training_loss(model, batch, loss_mode):
    if loss_mode == 'full':
        return model(**batch).loss
    if loss_mode == 'streamed':
        from runners.stage9.streamed_loss import causal_loss
        return causal_loss(model, batch, chunk_tokens=64)
    raise ValueError('unregistered training loss computation')


def held_loss(model, tok, enc, loss_mode='full'):
    import torch
    total, count = 0.0, 0
    model.eval()
    with torch.no_grad():
        for row in enc:
            batch = batch_tensors(torch, [row], tok.pad_token_id, "cuda")
            n = int((batch["labels"][:, 1:] != -100).sum())
            loss = float(training_loss(model, batch, loss_mode))
            if not math.isfinite(loss):
                raise ValueError("nonfinite held-out loss")
            total += loss * n
            count += n
    return total / count


def train(corpus_path, output, family, seed=9001, epochs=3, batch_size=4, accumulation=2,
          lr=2e-4, max_length=1024, checkpoint_every=50, loss_mode='full'):
    import torch
    import transformers
    import peft
    from peft import LoraConfig, PeftModel, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from runners.s5_lib import GpuSession
    from runners.stage9.neural import choice_validation

    corpus_path, output = Path(corpus_path).resolve(), Path(output).resolve()
    if not output.is_relative_to(ROOT):
        raise ValueError("adapter output must be inside the Stage 9 root")
    if epochs < 1 or batch_size < 1 or accumulation < 1 or checkpoint_every < 1:
        raise ValueError("positive training dimensions required")
    if loss_mode not in ('full', 'streamed'):
        raise ValueError('unregistered training loss computation')
    corpus = read(corpus_path)
    if corpus["split"] not in ("training", "pilot"):
        raise ValueError("discovery and reserve cannot become training data")
    base = BASES[family]
    paths = [Path(__file__), REPO / "runners/stage9/common.py", REPO / "runners/stage9/neural.py"]
    if loss_mode == 'streamed':
        paths.append(REPO / 'runners/stage9/streamed_loss.py')
    source = closure(paths)
    identity = {"base": base, "family": family, "seed": seed, "epochs": epochs, "batch": batch_size,
                "accumulation": accumulation, "lr": lr, "max_length": max_length, "lora": LORA,
                "corpus_sha256": file_hash(corpus_path), "source": source, "split": corpus["split"],
                "loss": "mean supervised next-token cross entropy per microbatch; equal microbatch weight",
                "loss_computation": loss_mode, "projection_chunk_tokens": 64 if loss_mode == 'streamed' else None,
                "torch": torch.__version__, "transformers": transformers.__version__, "peft": peft.__version__}
    freeze(output / "IDENTITY.json", identity)
    complete = output / "COMPLETE.json"
    if complete.exists():
        receipt = read(complete)
        if receipt["identity_sha256"] != digest(identity):
            raise ValueError("completed adapter identity mismatch")
        return receipt
    started = time.time()
    current_path = output / "CURRENT.json"
    current = read(current_path) if current_path.exists() else None
    previous_s = current["cumulative_active_seconds"] if current else 0.0
    torch.set_num_threads(6)
    torch.manual_seed(seed)
    random.seed(seed)
    with GpuSession("s9_train_" + output.name):
        tok = AutoTokenizer.from_pretrained(base["model"], revision=base["revision"], local_files_only=True, trust_remote_code=False)
        if tok.pad_token is None:
            tok.pad_token = tok.eos_token
        enc, exposure = encode(tok, corpus["examples"], max_length)
        val, val_exposure = encode(tok, corpus["validation"], max_length)
        freeze(output / "EXPOSURE.json", {"train": exposure, "validation": val_exposure,
                                          "order": [e["key"] for e in enc], "corpus": corpus["identity"]})
        model = AutoModelForCausalLM.from_pretrained(base["model"], revision=base["revision"],
                    local_files_only=True, trust_remote_code=False, dtype=torch.bfloat16).to("cuda")
        if current:
            checkpoint = output / current["checkpoint"]
            if closure([checkpoint])["sha256"] != current["checkpoint_sha256"]:
                raise ValueError("checkpoint hash mismatch")
            model = PeftModel.from_pretrained(model, str(checkpoint), is_trainable=True)
        else:
            model = get_peft_model(model, LoraConfig(**LORA))
        model.gradient_checkpointing_enable()
        model.enable_input_require_grads()
        model.config.use_cache = False
        parameters = [p for p in model.parameters() if p.requires_grad]
        if not parameters:
            raise ValueError("adapter has no trainable parameters")
        opt = torch.optim.AdamW(parameters, lr=lr, weight_decay=0.0)
        updates_per_epoch = math.ceil(len(enc) / (batch_size * accumulation))
        total_updates = epochs * updates_per_epoch
        schedule = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: 0.5 * (1 + math.cos(math.pi * min(1, s / total_updates))))
        progress = {"epoch": 0, "offset": 0, "updates": 0, "curve": [], "epoch_loss_sum": 0.0, "epoch_loss_n": 0}
        if current:
            state = torch.load(checkpoint / "training-state.pt", map_location="cpu", weights_only=True)
            if state["identity_sha256"] != digest(identity):
                raise ValueError("optimizer identity mismatch")
            opt.load_state_dict(state["optimizer"])
            schedule.load_state_dict(state["schedule"])
            torch.set_rng_state(state["torch_rng"])
            torch.cuda.set_rng_state_all(state["cuda_rng"])
            random.setstate(state["python_rng"])
            progress = state["progress"]
        write(output / "RUNNING.json", {"pid": os.getpid(), "started": started, "identity_sha256": digest(identity),
                                        "resumed_updates": progress["updates"], "cumulative_active_seconds": previous_s})

        def save_checkpoint(epoch_receipt=None):
            # A directory is not a checkpoint until the atomic CURRENT record names it.
            name = "checkpoint-" + str(progress["updates"]).zfill(6)
            destination = output / name
            if destination.exists():
                # An interrupted unpublished save may be present. Use a unique new path.
                name += "-" + str(time.time_ns())
                destination = output / name
            model.save_pretrained(str(destination), safe_serialization=True)
            torch.save({"identity_sha256": digest(identity), "optimizer": opt.state_dict(), "schedule": schedule.state_dict(),
                        "torch_rng": torch.get_rng_state(), "cuda_rng": torch.cuda.get_rng_state_all(),
                        "python_rng": random.getstate(), "progress": progress}, destination / "training-state.pt")
            record = {"checkpoint": name, "checkpoint_sha256": closure([destination])["sha256"],
                      "identity_sha256": digest(identity), "updates": progress["updates"],
                      "cumulative_active_seconds": previous_s + time.time() - started, "saved_at": time.time(),
                      "next_epoch": progress["epoch"], "next_example_offset": progress["offset"]}
            if epoch_receipt is not None:
                write(output / f"EPOCH_{epoch_receipt['epoch']}.json", {**record, **epoch_receipt})
            write(current_path, record)
            print("checkpoint", progress["updates"], "epoch", progress["epoch"], "offset", progress["offset"], flush=True)
            return record

        while progress["epoch"] < epochs:
            ep = progress["epoch"]
            order = list(range(len(enc)))
            random.Random(seed + ep).shuffle(order)
            model.train()
            while progress["offset"] < len(order):
                start = progress["offset"]
                block = order[start:start + batch_size * accumulation]
                chunks = [block[i:i + batch_size] for i in range(0, len(block), batch_size)]
                opt.zero_grad(set_to_none=True)
                for indices in chunks:
                    batch = batch_tensors(torch, [enc[i] for i in indices], tok.pad_token_id, "cuda")
                    loss = training_loss(model, batch, loss_mode)
                    if not torch.isfinite(loss):
                        raise ValueError("nonfinite training loss; retain failing seed")
                    (loss / len(chunks)).backward()
                    progress["epoch_loss_sum"] += float(loss.detach())
                    progress["epoch_loss_n"] += 1
                torch.nn.utils.clip_grad_norm_(parameters, 1.0)
                opt.step()
                schedule.step()
                opt.zero_grad(set_to_none=True)
                progress["offset"] += len(block)
                progress["updates"] += 1
                if progress["updates"] % checkpoint_every == 0 and progress["offset"] < len(order):
                    save_checkpoint()
                if (output / "CHECKPOINT_REQUEST").exists():
                    save_checkpoint()
                    return {"checkpointed": True, "reason": "bounded stop requested", "updates": progress["updates"]}
            value = held_loss(model, tok, val, loss_mode)
            next_score = choice_validation(model, tok, corpus["validation_choices"])
            progress["curve"].append({"epoch": ep, "heldout_loss": value,
                                      **next_score, "training_loss": progress["epoch_loss_sum"] / progress["epoch_loss_n"], "updates": progress["updates"]})
            progress.update(epoch=ep + 1, offset=0, epoch_loss_sum=0.0, epoch_loss_n=0)
            saved = save_checkpoint({"epoch": ep, "heldout_loss": value, **next_score})
            progress["curve"][-1]["checkpoint"] = saved["checkpoint"]
        candidates = [read(output / f"EPOCH_{ep}.json") for ep in range(epochs)]
        best = max(candidates, key=lambda c: c["mean_next_action_log_score"])
        receipt = {"identity_sha256": digest(identity), "base": base, "family": family, "seed": seed,
                   "split": corpus["split"], "selected_checkpoint": best["checkpoint"],
                   "selected_checkpoint_sha256": best["checkpoint_sha256"], "selection": "maximum validation next-action log score, development only",
                   "curve": candidates, "active_seconds": previous_s + time.time() - started, "exposure": exposure,
                   "trainable_parameters": sum(p.numel() for p in parameters), "completed_at": time.time(),
                   "admission": "not evaluated; fitting never grants competence"}
        freeze(complete, receipt)
        return receipt


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--corpus", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--family", choices=BASES, required=True)
    p.add_argument("--seed", type=int, default=9001)
    p.add_argument("--epochs", type=int, default=3)
    p.add_argument("--batch", type=int, default=4)
    p.add_argument("--accumulation", type=int, default=2)
    p.add_argument("--checkpoint-every", type=int, default=50)
    a = p.parse_args()
    train(a.corpus, a.output, a.family, a.seed, a.epochs, a.batch, a.accumulation, checkpoint_every=a.checkpoint_every)


if __name__ == "__main__":
    main()
