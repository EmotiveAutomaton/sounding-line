"""CA0: counts-only, turn-aware census of the pinned Community Alignment CSV.

DESIGN CHECK: LESSONS sections 2-5; CONTROLS sections 1-7. This instrument
has no hypothesis gate. Known-answer fixtures count conversations separately
from comparisons, reject malformed choice/candidate support and preserve absent
turns. Missing support is excluded explicitly, never interpreted as a null.
No choice distribution, identity, participant text or fitted model is reported.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import csv
import hashlib
from pathlib import Path

from .menus_io import assert_equal, input_hashes, read, write

TURNS = ("first", "second", "third", "fourth")
OPTIONS = tuple("response_" + s for s in "abcd")
ENCODER = {"model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
           "revision": "e8f8c211226b894fcb81acc59f3b34ba3efd5f42",
           "device": "cpu", "license": "Apache-2.0"}


def digest(text):
    return hashlib.sha256(text.encode("utf8")).hexdigest()


def prompt_id(text):
    # Exact Unicode text after outer whitespace removal; no translation or fuzzy join.
    return digest(text.strip())


def census(path):
    csv.field_size_limit(16 * 1024 * 1024)
    conversations = set(); annotators = set(); rows = 0
    counts = Counter(); reasons = Counter(); candidates = Counter(); by_turn = Counter()
    countries = Counter(); languages = Counter(); waves = Counter()
    support = defaultdict(lambda: {"comparisons": 0, "prompts": set()})
    prompt_writers = defaultdict(set); context_writers = defaultdict(set)
    comparison_metadata = []
    required = {"conversation_id", "annotator_id", "annotator_country", "assigned_lang", "wave"}
    required |= {f"{turn}_turn_{suffix}" for turn in TURNS
                 for suffix in ("prompt", "preferred_response", "feedback", *OPTIONS)}
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not required <= set(reader.fieldnames or []):
            raise ValueError("Community Alignment schema missing required codebook fields")
        if any("timestamp" in name.lower() for name in reader.fieldnames):
            raise ValueError("unexpected timestamp column: review source version")
        for row in reader:
            rows += 1
            if None in row or any(row[k] is None for k in required):
                raise ValueError("malformed CSV record")
            conversation, writer = row["conversation_id"].strip(), row["annotator_id"].strip()
            if not conversation or not writer or conversation in conversations:
                raise ValueError("missing identity or duplicate conversation")
            conversations.add(conversation); annotators.add(writer)
            countries[row["annotator_country"] or "missing"] += 1
            languages[row["assigned_lang"] or "missing"] += 1
            waves[row["wave"] or "missing"] += 1
            history = []; earlier_complete = True
            for number, turn in enumerate(TURNS, 1):
                prefix = turn + "_turn_"
                prompt = row[prefix + "prompt"].strip()
                choice = row[prefix + "preferred_response"].strip()
                options = [row[prefix + option].strip() for option in OPTIONS]
                feedback = bool(row[prefix + "feedback"].strip())
                present = bool(prompt or choice or any(options) or feedback)
                if not present:
                    counts["absent_turns"] += 1; earlier_complete = False
                    continue
                counts["present_turns"] += 1
                candidates[str(sum(bool(x) for x in options))] += 1
                failures = []
                if not prompt: failures.append("missing_prompt")
                if choice not in OPTIONS: failures.append("missing_or_unrecognized_choice")
                if not all(options): failures.append("incomplete_four_candidate_set")
                if not earlier_complete: failures.append("incomplete_prior_turn")
                if not row["annotator_country"].strip(): failures.append("missing_country")
                if not row["assigned_lang"].strip(): failures.append("missing_language")
                if failures:
                    reasons.update(failures); counts["excluded_turns"] += 1
                    earlier_complete = False
                    continue
                counts["valid_comparisons"] += 1; by_turn[str(number)] += 1
                counts["comparisons_with_explanation"] += feedback
                pid = prompt_id(prompt)
                # Context-aware count is a declared diagnostic; packet's prompt text
                # overlap remains the routing quantity, with preceding context retained.
                cid = digest("\0".join([*history, prompt]))
                prompt_writers[pid].add(writer); context_writers[cid].add(writer)
                support[writer]["comparisons"] += 1; support[writer]["prompts"].add(pid)
                comparison_metadata.append((writer, pid, cid))
                history.extend([prompt, options[OPTIONS.index(choice)]])
    eligible = {writer for writer, value in support.items()
                if value["comparisons"] >= 20 and len(value["prompts"]) >= 10}
    usable = [(w, p, c) for w, p, c in comparison_metadata if w in eligible]
    eligible_prompt_writers = defaultdict(set); eligible_context_writers = defaultdict(set)
    for w, p, c in usable:
        eligible_prompt_writers[p].add(w); eligible_context_writers[c].add(w)
    shared = sum(len(eligible_prompt_writers[p]) >= 5 for _, p, _ in usable)
    context_shared = sum(len(eligible_context_writers[c]) >= 5 for _, _, c in usable)
    return {"conversation_rows": rows, "unique_conversations": len(conversations),
            "annotators": len(annotators), "turn_counts": dict(sorted(counts.items())),
            "valid_comparisons_by_turn": dict(sorted(by_turn.items())),
            "exclusion_reasons_nonexclusive": dict(sorted(reasons.items())),
            "present_turn_candidate_counts": dict(sorted(candidates.items())),
            "conversation_country_counts": dict(sorted(countries.items())),
            "conversation_language_counts": dict(sorted(languages.items())),
            "conversation_wave_counts": dict(sorted(waves.items())),
            "eligible_annotators": len(eligible), "eligible_comparisons": len(usable),
            "eligible_distinct_prompts": len(eligible_prompt_writers),
            "comparisons_on_prompts_shared_by_five_eligible_annotators": shared,
            "comparisons_on_complete_context_shared_by_five_eligible_annotators": context_shared,
            "permutation_route": "within_prompt" if usable and 2 * shared >= len(usable)
            else "within_country_and_50_prompt_clusters",
            "analysis_unit": "one valid four-candidate turn-level comparison",
            "eligibility": "at least 20 valid comparisons on at least 10 exact prompts",
            "temporal_order": "absent; turn order only; no ordering of conversations inferred",
            "context_caveat": "same current prompt may have different preceding conversation; retain full context and split complete conversations together",
            "counts_only": True}


def calculate(inputs, config):
    hashes = input_hashes(inputs)
    expected = config.get("source_sha256")
    if expected is not None and hashes.get("source") != expected:
        raise ValueError("pinned Community Alignment source changed")
    if config.get("encoder", ENCODER) != ENCODER:
        raise ValueError("encoder revision differs from frozen CA0 choice")
    return {"card": "CA0", "state": "instrument_complete", "counts": census(inputs["source"]),
            "encoder": ENCODER, "encoder_execution": "not run; immutable revision selected for CA1",
            "input_hashes": hashes, "scope": "public release metadata and support only; no preference model or inference"}


def execute(output, inputs, config):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    report = calculate(inputs, config)
    write(output / "SUMMARY.json", report)
    return report


def verify(output, inputs, config):
    assert_equal(calculate(inputs, config), read(Path(output) / "SUMMARY.json"))
    return {"verified": True, "fresh_full_csv_replay": True, "counts_only": True}
