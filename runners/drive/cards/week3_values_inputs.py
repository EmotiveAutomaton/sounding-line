"""VAL private source preparation; no provider access or scientific inference.

DESIGN CHECK: LESSONS 3-5 and packet CA3/WE1. Source-complete CA1 people are
fixed before sampling; every argumentative session retains an explicit status.
Reuse authenticated surviving-typed fragments and their gap boundaries. Deleted
production is a separate unrun interpretation. Full fresh replay authenticates
all sources and reconstructs the sample, deduplication and private joins.
"""
from collections import Counter, defaultdict
from pathlib import Path

from runners.stage14.common import digest, filehash, read, freeze
from runners.drive.engine_export_join import typed_fragments
from .week3_alignment_features import source as alignment_source
from .timing_pmap_source import completed, bound_record

SEED = 20261026
INPUTS = {"prepared_summary", "prepared_complete", "ev_complete", "ev_index",
          "roster", "roster_complete"}


def choice_sample(rows, people):
    groups = defaultdict(list); seen = set()
    for row in rows:
        key = (row["writer"], row["conversation"], row["turn"])
        if key in seen: raise ValueError("duplicate comparison identity")
        seen.add(key); groups[row["writer"]].append(row)
    if set(groups) != set(people): raise ValueError("full CA1 population differs")
    selected, census = [], []
    for writer in sorted(people):
        candidates = [r for r in groups[writer] if isinstance(r["explanation"], str) and r["explanation"].strip()]
        order = sorted(candidates, key=lambda r: digest([SEED, writer, r["conversation"], r["turn"]]))
        for r in order[:10]:
            selected.append(dict(text=r["explanation"], link=dict(kind="choice-explanation", writer=writer,
                conversation=r["conversation"], turn=r["turn"], prompt=r["prompt"], half=r["half"])))
        census.append(dict(writer=writer, comparisons=len(groups[writer]), available_explanations=len(candidates),
                           selected_explanations=min(10, len(candidates))))
    return selected, census


def coauthor_items(records, roster):
    by = {r["session"]: r for r in roster}
    if len(by) != len(roster): raise ValueError("duplicate roster session")
    seen = set(); items, census = [], []
    for record in records:
        keys = record["document"]["keys"]; sid = keys["session"]
        if sid in seen or sid not in by: raise ValueError("duplicate or missing source session")
        seen.add(sid); genre = by[sid]["domain"]
        if genre not in ("argumentative", "creative"): raise ValueError("unknown source genre")
        if genre != "argumentative": continue
        fragment = typed_fragments(record)
        row = dict(**keys, canonical=True, domain=genre, status=fragment["status"], support=fragment["support"])
        if fragment["status"] == "complete":
            document = fragment["document"]
            items.append(dict(text=document["text"], link=dict(kind="argumentative-typed", **keys,
                              construction=document["fragmentConstruction"])))
        elif fragment["status"] != "unsupported-no-typed-words": raise ValueError("unknown typed disposition")
        census.append(row)
    # The already admitted canonical EV population is smaller than the raw H01
    # roster. Keep upstream-only rows as an audit, not as missing canonical text.
    for sid in sorted(set(by)-seen):
        census.append(dict(session=sid, canonical=False, domain=by[sid]["domain"],
                           status="outside-admitted-canonical-EV-population"))
    return items, census


def deduplicate(items):
    texts, joins = {}, defaultdict(list)
    for row in items:
        text = row["text"]
        if not isinstance(text, str) or not text.strip(): raise ValueError("empty value item")
        ident = digest({"VAL-text": text})
        if ident in texts and texts[ident] != text: raise ValueError("text hash collision")
        texts[ident] = text; joins[ident].append(row["link"])
    ordered = sorted(texts, key=lambda k: digest([SEED, "VAL-rung-order", k]))
    return [dict(item_id=k, text=texts[k]) for k in ordered], dict(joins)


def calculate(inputs, config):
    if set(inputs) != INPUTS or config not in ({}, {"fixture": True}): raise ValueError("exact VAL source inputs/config required")
    report, _, choices, splits = alignment_source(inputs)
    chosen, choice_census = choice_sample(choices, splits["writer_splits"])
    completed(inputs["ev_complete"], inputs["ev_index"])
    index = read(inputs["ev_index"])
    if len({r["session"] for r in index}) != len(index): raise ValueError("duplicate EV session index")
    roster_path = Path(inputs["roster"]).resolve(); terminal_path = Path(inputs["roster_complete"]).resolve()
    terminal = read(terminal_path)
    if terminal.get("status") not in ("COMPLETE", "complete") or terminal.get("outputs", {}).get(
            roster_path.relative_to(terminal_path.parent).as_posix()) != filehash(roster_path):
        raise ValueError("roster is not authenticated by its completion")
    roster = read(roster_path)
    if not config.get("fixture") and len(index) != 1399: raise ValueError("original full CoAuthor population required")
    records = []
    for row in index:
        record = bound_record(inputs["ev_index"], row)
        if record["document"]["keys"]["session"] != row["session"]: raise ValueError("EV index identity differs")
        records.append(record)
    typed, typed_census = coauthor_items(records, roster)
    items, joins = deduplicate(chosen + typed)
    if len(items) < 200: raise ValueError("need original and fresh 100-item calibration rungs")
    return dict(items=items, joins=joins, population=dict(choice=choice_census, argumentative=typed_census)), dict(
        card="VAL-inputs", state="private_inputs_ready", seed=SEED, ca1_annotators=len(choice_census),
        ca1_comparisons=len(choices), sampled_explanations=len(chosen),
        annotators_without_explanations=sum(r["selected_explanations"] == 0 for r in choice_census),
        coauthor_source_sessions=len(index), argumentative_sessions=sum(r["canonical"] for r in typed_census),
        raw_roster_only_sessions=sum(not r["canonical"] for r in typed_census),
        raw_roster_only_argumentative=sum(not r["canonical"] and r["domain"] == "argumentative" for r in typed_census),
        typed_dispositions=dict(sorted(Counter(r["status"] for r in typed_census if r["canonical"]).items())),
        unique_items=len(items), input_hashes={k:filehash(v) for k,v in inputs.items()},
        construction="canonical authenticated surviving typed spans; two-newline gap boundaries; not original continuous prose",
        original_all_produced_deleted_word_route="separate and unrun", scientific_admission=False)


def execute(output, inputs, config):
    output = Path(output); values, report = calculate(inputs, config)
    for name, key in (("ITEMS.json", "items"), ("PRIVATE_JOIN.json", "joins"), ("PRIVATE_POPULATION.json", "population")):
        freeze(output/name, values[key])
    report["output_hashes"] = {name:filehash(output/name) for name in ("ITEMS.json", "PRIVATE_JOIN.json", "PRIVATE_POPULATION.json")}
    freeze(output/"SUMMARY.json", report); return report


def verify(output, inputs, config):
    output = Path(output); values, report = calculate(inputs, config)
    for name, key in (("ITEMS.json", "items"), ("PRIVATE_JOIN.json", "joins"), ("PRIVATE_POPULATION.json", "population")):
        if read(output/name) != values[key]: raise ValueError("fresh VAL source reconstruction differs")
    report["output_hashes"] = {name:filehash(output/name) for name in ("ITEMS.json", "PRIVATE_JOIN.json", "PRIVATE_POPULATION.json")}
    if read(output/"SUMMARY.json") != report: raise ValueError("VAL source summary differs")
    return dict(verified=True, full_population_and_sample_replay=True)
