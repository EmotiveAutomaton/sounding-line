"""Discarded full-size replay pilot; no discovery or reserve is opened.

DESIGN CHECK: LESSONS sections 1b, 1d, 3, 4, 5; CONTROLS section 6.
NULL: fewer examples, different tokenization, or mixed science lineage invalidates
the timing claim. ALTERNATIVE: 1600 examples and three epochs of the replay recipe.
gates: complete requested population and matching token identity; bands: pass or error.
This does not validate new learner-state recipes; those require their own timed collection.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time

from runners.stage9.common import ROOT, REPO, closure, digest, freeze
from runners.stage9.train import BASES


def prepare(family="qwen", count=1600):
    from transformers import AutoTokenizer
    from runners.stage8.constructor import population as pop
    from runners.stage8.reader import logfmt
    started = time.time()
    if count != 1600:
        raise ValueError("representative full training pilot must use 1600 examples")
    base = BASES[family]
    tok = AutoTokenizer.from_pretrained(base["model"], revision=base["revision"], local_files_only=True, trust_remote_code=False)
    examples, validation, choices = [], [], []
    truncations, tokens_discarded = 0, 0
    for domain in pop.DOMAINS:
        for i in range(count // 2):
            record = pop.training_example(i, domain, 9900000)
            # Exact historical original-recipe tokenization, including its explicit cap.
            all_ids = tok(record["text"] + tok.eos_token, add_special_tokens=True).input_ids
            ids = all_ids[:1024]
            truncations += len(all_ids) > len(ids)
            tokens_discarded += len(all_ids) - len(ids)
            examples.append({"key": record["lid"], "input_ids": ids, "lineages": record["lineages"]})
        for i in range(20):
            record = pop.training_example(i, domain, 9910000)
            ids = tok(record["text"] + tok.eos_token, add_special_tokens=True).input_ids[:1024]
            validation.append({"key": record["lid"], "input_ids": ids})
        kept = 0
        for i in range(200):
            w = pop.sample_world(pop.pop_lid(i, domain, 9920000), finish=True)
            if w["degenerate"] or w["hidden"]["next_action"] is None:
                continue
            ev = pop.evidence_at(w, w["cut"], {"unit_ref": "u", "condition_ref": "pilot"})
            options = ev["query"]["next_action_options"]
            prefix = logfmt.compose([], logfmt.header_from_evidence(ev), logfmt.prefix_lines(ev["process_prefix"]))
            choices.append({"key": w["lid"], "prefix": prefix,
                            "options": {a: logfmt.event_line(w["cut"], *a.split(":")) for a in options},
                            "truth": w["hidden"]["next_action"]})
            kept += 1
            if kept == 40:
                break
        if kept != 40:
            raise ValueError("representative validation did not realize 40 worlds per domain")
    paths = []
    for mod in list(sys.modules.values()):
        p = getattr(mod, "__file__", None)
        if p and Path(p).is_absolute() and Path(p).suffix == ".py" and Path(p).resolve().is_relative_to(REPO) and ".venv" not in Path(p).parts:
            paths.append(Path(p))
    identity = {"purpose": "discarded complete original-recipe timing pilot", "base": base, "n_examples": count,
                "training_band": 9900000, "validation_bands": [9910000, 9920000], "sources": closure(paths),
                "historical_max_tokens": 1024, "truncated_training_examples": truncations,
                "historically_discarded_training_tokens": tokens_discarded,
                "warning": "historical truncation reproduced explicitly; this is not a learner-state pilot or science"}
    result = {"split": "pilot", "identity": identity, "examples": examples, "validation": validation, "validation_choices": choices}
    path = ROOT / "private/pilot" / (family + "-corpus.json")
    freeze(path, result)
    receipt = {"corpus_sha256": digest(result), "identity": identity, "preparation_seconds": time.time() - started,
               "examples": len(examples), "validation_choices": len(choices), "pilot_only": True}
    freeze(ROOT / "pilot" / family / "PREPARATION.json", receipt)
    print(path, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--family", choices=BASES, default="qwen")
    prepare(parser.parse_args().family)
