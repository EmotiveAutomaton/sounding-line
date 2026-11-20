"""Shared source-bound producer for the November 20 diary rows, in packet order."""
from pathlib import Path

import pandas as pd

from . import week6_lattice_source_v1 as source
from . import week6_ld1_v1 as ld1
from . import week6_ld2_v1 as ld2
from . import week6_ld3_v1 as ld3
from . import week6_ld12_common_v1 as common
from . import week6_ld_runtime_v1 as runtime
from .batch_runtime import filehash, freeze, read
from .es_source_v1 import sha256
from .week6_ld3_follow_v1 import describe


OPERATORS = {"LD2": ld2, "LD1": ld1, "LD3": ld3}
ROUTES = {"LD2": ("LD2-support", "LD2-product"), "LD1": ("LD1",), "LD3": ("LD3",)}


def reviewed_file(binding):
    path = Path(binding["path"])
    if filehash(path) != binding["sha256"]:
        raise ValueError("Reviewed diary evidence digest changed: " + path.name)
    return path


def bind_rows(card, member, review, source_pin):
    table, book, layout = [read(reviewed_file(review[key]))
                           for key in ("rows_table", "codebook", "source_layout")]
    if (table["version"] != 1 or table["draws_per_registered_contrast"] != 2000
            or member != book["dataset_id"] or review["codebook"]["sha256"] != common.CODEBOOK_HASHES[member]):
        raise ValueError("Wrong member, codebook or draw registration")
    physical = [f for f in layout["files"] if f["sha256"] == source_pin["sha256"]
                and f["bytes"] == source_pin["bytes"]]
    if len(physical) != 1:
        raise ValueError("Member schema does not authenticate the prompt table")
    documented = {entry["name"] for entry in book["features"]}
    present = {column["name"] for column in physical[0]["columns"]}
    rows = [row for row in table["rows"] if (row["operator"], row["member"]) == (card, member)]
    if not rows or len({row["id"] for row in rows}) != len(rows):
        raise ValueError("Empty or duplicate row registration")
    columns = set().union(*(source.columns(member, name) for name in ROUTES[card]))
    if card == "LD3":
        aliases = {"occup_" + name: name for name in source.ACTIVITY}
        columns = {aliases.get(col, col) for col in columns}
    if card == "LD1":
        columns.update(("communication", "no_interactionpartner"))
    for row in rows:
        if row["kind"] not in ("description", "contrast") or row["context"] not in ("both", "interaction", "solitary"):
            raise ValueError("Unknown diary row or context")
        columns.update(row["support_items"])
    missing = sorted(columns - (documented & present))
    if missing:
        raise ValueError("Missing documented source items: " + ", ".join(missing))
    return rows, sorted(columns)


def support_before_outcomes(path, pin, rows, missing, guard):
    """Count predictor/context eligibility; model complete cases are recorded later."""
    rows = [row for row in rows if row["kind"] == "contrast"]
    columns = sorted({"id", "interaction"}.union(*(r["support_items"] for r in rows)))
    if path.stat().st_size != pin["bytes"] or sha256(path, guard) != pin["sha256"]:
        raise ValueError("Source bytes differ before support")
    people = {row["id"]: set() for row in rows}
    counts = {row["id"]: 0 for row in rows}
    with pd.read_csv(path, sep="\t", usecols=columns, dtype=str, keep_default_na=False,
                     na_filter=False, chunksize=20000) as frames:
        for frame in frames:
            guard()
            context = pd.to_numeric(frame["interaction"], errors="coerce")
            valid_id = ~frame["id"].isin(missing)
            for row in rows:
                ok = valid_id & context.isin([1, 2])
                if row["context"] == "both":
                    success = frame["int_success"].where(context == 1, frame["occup_success"])
                    ok &= pd.to_numeric(success, errors="coerce").isin(range(1, 7))
                else:
                    ok &= context.eq(1 if row["context"] == "interaction" else 2)
                    for col in row["support_items"]:
                        values = pd.to_numeric(frame[col], errors="coerce")
                        allowed = (range(1, 12) if col == "interaction_partner1" else
                                   range(1, 6) if col == "no_interactionpartner" else range(1, 7))
                        ok &= values.isin(allowed)
                counts[row["id"]] += int(ok.sum())
                people[row["id"]].update(frame.loc[ok, "id"])
    if sha256(path, guard) != pin["sha256"]:
        raise ValueError("Source changed during support count")
    return {rid: {"eligible_prompts": n, "eligible_people": len(people[rid])} for rid, n in counts.items()}


def one_pass(folder, name, binding, produce, verify):
    path = folder / (name + ".json")
    receipt_path = folder / (name + ".receipt.json")
    recovering = path.exists() and not receipt_path.exists()
    if not path.exists():
        if verify or receipt_path.exists():
            raise ValueError("Missing one-pass evidence: " + name)
        freeze(path, {"binding": binding, "values": produce()})
    value = read(path)
    if value["binding"] != binding:
        raise ValueError("One-pass source or row identity differs: " + name)
    digest = filehash(path)
    if receipt_path.exists():
        if read(receipt_path) != {"sha256": digest}:
            raise ValueError("One-pass digest differs: " + name)
    elif verify:
        raise ValueError("One-pass receipt missing: " + name)
    else:
        if recovering and value["values"] != produce():
            raise ValueError("Interrupted one-pass output differs on reconstruction: " + name)
        freeze(receipt_path, {"sha256": digest})
    return digest, value["values"]


class RowProducer:
    def __init__(self, card, review, output, verify):
        self.card = card
        self.module = OPERATORS[card]
        self.review = review
        self.output = Path(output)
        self.verify = verify

    def prepare(self, member, path, pin, missing, guard):
        rows, items = bind_rows(self.card, member, self.review, pin)
        binding = {"member": member, "card": self.card, "source_sha256": pin["sha256"],
                   "table_sha256": self.review["rows_table"]["sha256"],
                   "codebook_sha256": self.review["codebook"]["sha256"], "items": items}
        support_digest, counts = one_pass(
            self.output, "ROW_SUPPORT", binding,
            lambda: support_before_outcomes(path, pin, rows, missing, guard), self.verify)
        receipts = {"support_sha256": support_digest}
        if self.card == "LD3":
            def description():
                frames = common.next_prompt_frames(member, path, pin, missing, guard)
                return describe((row for frame in frames for row in frame.to_dict("records")), missing, guard)
            receipts["description_sha256"], _ = one_pass(
                self.output, "NEXT_PROMPT_DESCRIPTION", binding, description, self.verify)
            prepared = self.module.prepare(member, path, pin, missing, guard, include_description=False)
        else:
            prepared = self.module.prepare(member, path, pin, missing, guard)
        expected = set()
        for row in rows:
            if row["kind"] == "contrast":
                spec = prepared.specs[row["metric"]]
                if (spec["role"] == "primary") != row["registered"] or spec.get("bar") != row["bar"]:
                    raise ValueError("Operator and row registration disagree: " + row["id"])
                spec["row_id"] = row["id"]
                spec.update(counts[row["id"]])
                if row["registered"]:
                    expected.add(row["metric"])
        if expected != {key for key, spec in prepared.specs.items() if spec["role"] == "primary"}:
            raise ValueError("Unregistered primary metric")
        prepared.metadata["row_evidence"] = receipts
        return prepared

    def evaluate(self, prepared, weights, guard, *, verify=False):
        return self.module.evaluate(prepared, weights, guard, verify=verify)


def _run(output, inputs, config, verify):
    card = config["panel_config"]["card"]
    runtime.validate(card, inputs, config)
    producer = RowProducer(card, read(Path(inputs["source_admission_path"])), output, verify)
    return runtime.operate(card, producer, output, inputs, config, verify=verify)


def execute(output, inputs, config):
    return _run(output, inputs, config, False)


def verify(output, inputs, config):
    return _run(output, inputs, config, True)
