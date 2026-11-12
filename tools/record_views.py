"""Additive evidence navigation. No scoring, claim inference, network or job dispatch.

The legacy ledger and its source bindings remain authoritative. Reviewed annotations
are pinned to semantic row content and reviewed documents; missing data stays unknown.
Run build after a full landing, then check. Readers must check before trusting a view.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import uuid
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
SHELF = "docs/records"
LEDGER = "results/phase_2_4_stage_15/CLAIM_LEDGER.json"
STAGE = "results/phase_2_4_stage_15"
THEORY = [f"docs/theory/{n}.md" for n in (
    "THE_TRIPLE_INFERENCE", "THREE_COGNITIVE_LAYERS", "DECISION_TRACES",
    "READER_HEURISTICS", "ALIGNMENT")]
KINDS = {"run", "texture", "claim", "unknown"}
POPULATIONS = {"people", "models", "constructed", "mixed", "not_applicable", "unknown"}
PURPOSES = {"primary", "probe", "calibration", "texture", "operations", "engineering_repair", "unknown"}
BEARINGS = {"supports", "narrows", "against", "uninformative", "context", "unknown"}
TAGS = {"channel", "set_point", "ladder", "attention", "reader", "gate", "kith", "laughter"}
PENDING = ".agent-state/record-views.pending.json"


class Invalid(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Invalid(message)


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf8")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def semantic(row):
    # Source line/digest changes when another finding is prepended. The substantive
    # row, including corrections, controls, estimates and relationships, must not drift.
    return digest(encode({k: v for k, v in row.items() if k not in {"source", "additional_source"}}))


def atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def mark_pending(root, evidence_id):
    """Writer-side start marker; final build/check clears it after full filing."""
    atomic(root / PENDING, encode(dict(evidence_id=evidence_id, generation=uuid.uuid4().hex)))


class Sources:
    def __init__(self, root):
        self.root = root.resolve()
        self.data = {}
        self.lines = {}

    def path(self, name):
        path = (self.root / name).resolve()
        require(path.is_relative_to(self.root), f"Outside repository: {name}")
        return path

    def read(self, name):
        name = Path(name).as_posix()
        if name not in self.data:
            path = self.path(name)
            require(path.is_file(), f"Missing source: {name}")
            self.data[name] = path.read_bytes()
        return self.data[name]

    def json(self, name):
        return json.loads(self.read(name).decode("utf-8-sig"))

    def binding(self, source):
        name = source["file"]
        raw = self.read(name)
        require(digest(raw) == source["source_sha256"], f"Source digest changed: {name}")
        if name not in self.lines:
            self.lines[name] = raw.decode("utf-8-sig").splitlines()
        lines = self.lines[name]
        n = source["line"]
        require(isinstance(n, int) and 0 < n <= len(lines), f"Invalid source line: {name}:{n}")
        require(source["anchor"] in lines[n - 1], f"Source anchor changed: {name}:{n}")

    def verify_unchanged(self):
        for name, value in self.data.items():
            require(self.path(name).read_bytes() == value, f"Concurrent source change: {name}; retry after landing")


def bindings(value):
    if isinstance(value, dict):
        if {"file", "line", "anchor", "source_sha256"} <= value.keys():
            yield value
        for child in value.values():
            yield from bindings(child)
    elif isinstance(value, list):
        for child in value:
            yield from bindings(child)


def unique(items, key, name):
    values = [x[key] for x in items]
    require(len(values) == len(set(values)), f"Duplicate {name}")
    return {x[key]: x for x in items}


def annotation(row, overlay, sources):
    result = dict(review_state="unreviewed", record_kind="unknown", purpose="unknown",
                  population="unknown", readout="unknown", evidence_validity="unknown",
                  by_construction="unreviewed", construction_reason=None, theory_tags=[],
                  theory_ids=[], classification_provenance=[])
    # Exact structural fact only. Outcome='infrastructure' cannot classify purpose.
    if row.get("scope") == "Operational record" and row.get("estimand") == "Operational integrity and execution accounting":
        result.update(record_kind="run", classification_provenance=[dict(
            rule="operational-record-shape-v1", fields=["scope", "estimand"],
            source_id=row["id"], limits="Run record only; scientific purpose and population remain unreviewed")])
    substrate = row.get("scope_qualifiers", {}).get("substrate")
    literal_populations = {"human self-report": "people", "human reports": "people",
                          "Human typing process records": "people"}
    if substrate in literal_populations:
        result["population"] = literal_populations[substrate]
        result["classification_provenance"].append(dict(rule="literal-substrate-v1",
            field="scope_qualifiers.substrate", value=substrate, source_id=row["id"],
            limits="Literal substrate classification only; no claim-bearing review inferred"))
    entry = overlay.get(row["id"])
    if entry is None:
        return result
    require(entry["row_sha256"] == semantic(row), f"Reviewed row changed; re-review {row['id']}")
    require(entry["source_locator"] == {k: row["source"][k] for k in ("file", "anchor")}, f"Reviewed source locator changed: {row['id']}")
    require(entry["review_state"] == "reviewed" and entry.get("reason"), f"Review provenance missing: {row['id']}")
    require(entry.get("sources"), f"Review sources missing: {row['id']}")
    for source in entry["sources"]:
        require(digest(sources.read(source["file"])) == source["sha256"], f"Review document changed: {source['file']}")
    result.update({k: v for k, v in entry.items() if k not in {"id", "row_sha256"}})
    require(result["record_kind"] in KINDS and result["population"] in POPULATIONS, "Invalid classification")
    require(result["purpose"] in PURPOSES and result["evidence_validity"] in {"valid", "limited", "invalid", "unknown"}, "Invalid purpose/validity")
    require(type(result["by_construction"]) is bool or result["by_construction"] == "unreviewed", "Invalid construction state")
    require(result["by_construction"] == "unreviewed" or result.get("construction_reason"), "Construction judgment needs a reason")
    require(set(result["theory_tags"]) <= TAGS, "Unknown theory tag")
    return result


def quotes(sources, paths):
    """Exact currently filed blockquotes, not a claim of transcript authentication."""
    output = []
    occurrences = {}
    for name in paths:
        lines = sources.read(name).decode("utf8").splitlines(keepends=True)
        fence = None
        i = 0
        while i < len(lines):
            stripped = lines[i].lstrip()
            match = re.match(r"(`{3,}|~{3,})", stripped)
            if match:
                mark = match.group(1)
                if fence is None:
                    fence = mark
                elif mark[0] == fence[0] and len(mark) >= len(fence):
                    fence = None
                i += 1
                continue
            if fence or not re.match(r"^ {0,3}>", lines[i]):
                i += 1
                continue
            start = i
            while i < len(lines) and re.match(r"^ {0,3}>", lines[i]):
                i += 1
            raw = "".join(lines[start:i])
            key = name + "\0" + raw
            occurrences[key] = occurrences.get(key, 0) + 1
            identity = digest(key.encode())[:20] + "-" + str(occurrences[key])
            output.append(dict(id="Q-" + identity, file=name, line=start + 1,
                end_line=i, source_sha256=digest(sources.read(name)), raw_markdown=raw,
                text_sha256=digest(raw.encode()), status="unreviewed", attribution="unreviewed",
                source_date=None, filing_date=None, theory_tags=[], superseded_by=[],
                transcript_verified=False, repairs="See source context and original filing receipts; not independently revalidated",
                context="".join(lines[max(0, start - 3):min(len(lines), i + 4)])))
    return output


def link(name, start=SHELF, line=None):
    url = quote(os.path.relpath(name, start).replace("\\", "/"), safe="/.-_")
    return url + (f"#L{line}" if line else "")


def cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", "")


def query(records, register, filters):
    require(set(filters) <= {"population", "purpose", "record_kind", "review_state",
            "evidence_validity", "theory_tags", "theory_ids", "claim"}, "Unknown query filter")
    if "claim" in filters:
        require(filters["claim"] in {c["id"] for c in register["claims"]}, "Unknown query claim")
    selected = list(records)
    for field in ("population", "purpose", "record_kind", "review_state", "evidence_validity"):
        if field in filters:
            selected = [r for r in selected if r["annotation"][field] == filters[field]]
    for field in ("theory_tags", "theory_ids"):
        if field in filters:
            selected = [r for r in selected if filters[field] in r["annotation"][field]]
    if "claim" in filters:
        ids = {e["evidence_id"] for e in register["links"] if e["claim_id"] == filters["claim"]}
        selected = [r for r in selected if r["id"] in ids]
    return sorted(selected, key=lambda r: r["id"])


def load(root):
    src = Sources(root)
    ledger = src.json(LEDGER)
    rows = unique(ledger["rows"], "id", "ledger ID")
    overlay = src.json(f"{SHELF}/ANNOTATIONS.json")
    register = src.json(f"{SHELF}/CLAIM_REGISTER.json")
    require(overlay["schema_version"] == register["schema_version"] == 1, "Unknown schema version")
    annotations = unique(overlay["entries"], "id", "annotation ID")
    require(set(annotations) <= rows.keys(), "Annotation refers to missing evidence")
    for source in bindings(ledger):
        src.binding(source)
    records = []
    for ident, row in sorted(rows.items()):
        detail = row.get("detail")
        detail_path = f"{STAGE}/{detail}" if isinstance(detail, str) else None
        if detail_path:
            src.read(detail_path)
        records.append(dict(row, detail_path=detail_path,
            detail_kind="path" if detail_path else "inline legacy ledger detail",
            row_sha256=semantic(row), annotation=annotation(row, annotations, src)))
    by_id = {r["id"]: r for r in records}
    claims = unique(register["claims"], "id", "claim ID")
    edges = set()
    for edge in register["links"]:
        require(edge["claim_id"] in claims and edge["evidence_id"] in rows, "Dangling claim/evidence link")
        require(edge["bearing"] in BEARINGS and edge.get("scope") and edge.get("reason"), "Incomplete evidence relationship")
        require(by_id[edge["evidence_id"]]["annotation"]["review_state"] == "reviewed", "Unreviewed claim basis")
        key = (edge["claim_id"], edge["evidence_id"], edge["scope"])
        require(key not in edges, "Duplicate relationship")
        edges.add(key)
    for claim in claims.values():
        require(claim["standing_source"] in rows, "Missing standing source")
        require(any(e["claim_id"] == claim["id"] and e["evidence_id"] == claim["standing_source"] for e in register["links"]), "Standing source must be linked")
        require(claim.get("reviewed_at") and claim.get("scope") and claim.get("standing"), "Incomplete claim review")
        require(claim["standing_quote"] == rows[claim["standing_source"]]["public_wording"], "Standing quote differs from source")
    config = src.json(f"{SHELF}/CONFIG.json")
    for name in config["theory_files"]:
        require(name.startswith("docs/theory/"), "Unexpected quotation source")
    quote_records = quotes(src, config["theory_files"])
    inventory = src.json(f"{SHELF}/MIGRATION_INVENTORY.json")
    require({r["id"] for r in inventory["records"]} <= rows.keys(), "Baseline evidence disappeared")
    src.read("tools/record_views.py")
    src.read(f"{SHELF}/README.md")
    src.read(f"{SHELF}/REVIEW_QUEUE.md")
    return src, records, register, config, quote_records


def table(records, title, preface):
    lines = [f"# {title}", "", "Generated; run `python tools/record_views.py check` before use.", "", preface, "",
        "Each row is an existing evidence ID, its navigation classification and original source. Outcome and correction labels remain the source's labels.", "",
        "| Evidence | Purpose / review | Population | Original outcome / correction | Source |",
        "|---|---|---|---|---|"]
    for r in records:
        a = r["annotation"]; s = r["source"]
        target = r["detail_path"] or s["file"]
        lines.append(f"| [{cell(r['id'])}]({link(target)}) | {a['purpose']} / {a['review_state']} | {a['population']} | {cell(r['outcome'])} / {cell(r['correction_class'] or 'none recorded')} | [original]({link(s['file'], line=s['line'])}) |")
    return "\n".join(lines) + "\n"


def render(root):
    src, records, register, config, quote_records = load(root)
    by_id = {r["id"]: r for r in records}
    reviewed = [r for r in records if r["annotation"]["review_state"] == "reviewed"]
    unknown = [r for r in records if r["annotation"]["review_state"] != "reviewed"]
    science = [r for r in reviewed if r["annotation"]["purpose"] in {"primary", "probe", "calibration", "texture"}]
    operations = [r for r in reviewed if r["annotation"]["purpose"] in {"operations", "engineering_repair"}]
    outputs = {}
    def put(name, value):
        outputs[name] = value.encode("utf8") if isinstance(value, str) else encode(value)
    coverage = f"Coverage: {len(records)} legacy records retained; {len(reviewed)} reviewed annotations; {len(unknown)} unreviewed. This pilot is not an exhaustive theory synthesis."
    put(f"{SHELF}/RECORDS.json", dict(schema_version=1, ledger_sha256=digest(src.read(LEDGER)), coverage=dict(total=len(records), reviewed=len(reviewed), unreviewed=len(unknown)), records=records))
    put(f"{SHELF}/SCIENCE.md", table(science, "Reviewed science navigation", coverage + "\n\nSensitivity calibrations are included even when their original outcome is infrastructure. Also inspect [unclassified records](UNCLASSIFIED.md); unknown does not mean uninformative."))
    put(f"{SHELF}/OPERATIONS.md", table(operations, "Reviewed operations navigation", coverage + "\n\nThis is an additive view. Original OPS_LOG, failures and scientific instrument checks remain in their original locations. Failed calibration belongs in the science view, not silently in this bucket."))
    put(f"{SHELF}/UNCLASSIFIED.md", table(unknown, "Records awaiting classification", coverage + "\n\nEvery unreviewed record stays reachable, including legacy science, operations, invalid results and corrections. No unknown field implies false or uninformative."))
    score = ["# Reviewed claim scoreboard", "", "Generated from the reviewed register, not inferred from runs. Check freshness with `python tools/record_views.py check`.", "", coverage, "",
        "Families group individual claims; they do not share one voted standing. Dates distinguish standing changes from annotation review. Unknown dates are explicit. A control/source/dependency failure can invalidate evidence immediately; theory interpretation remains curator-owned.", "",
        "| Claim / family | Reviewed standing and scope | Basis health | Last standing change / evidence review | Evidence |", "|---|---|---|---|---|"]
    for c in register["claims"]:
        edges = [e for e in register["links"] if e["claim_id"] == c["id"]]
        bad = [e for e in edges if e.get("basis", True) and by_id[e["evidence_id"]]["annotation"]["evidence_validity"] in {"invalid", "unknown"}]
        health = "REVIEW REQUIRED: invalid or unknown evidence; no positive claim licensed" if bad else "Reviewed, within recorded limits"
        evidence = "; ".join(f"[{e['evidence_id']}]({link(by_id[e['evidence_id']]['detail_path'] or by_id[e['evidence_id']]['source']['file'], start='.')}) ({e['bearing']})" for e in edges)
        score.append(f"| {cell(c['id'])}: {cell(c['statement'])} / {cell(c['family'])} | {cell(c['standing'])}; {cell(c['scope'])} | {health} | {c['last_standing_change'] or 'unknown'} / {c['reviewed_at']} | {evidence} |")
    score += ["", "Exact source wording and relationship reasons are retained in [the claim register](docs/records/CLAIM_REGISTER.json). [Science](docs/records/SCIENCE.md) · [Operations](docs/records/OPERATIONS.md) · [Unclassified](docs/records/UNCLASSIFIED.md).", ""]
    put("SCOREBOARD.md", "\n".join(score))
    examples = ["# Five checked navigation queries", "", coverage, "", "Queries return reviewed mappings only. An empty answer is not absence of evidence. Full source outcomes, numerical results and corrections remain accessible.", ""]
    for q in config["queries"]:
        answer = query(records, register, q["filters"])
        require([r["id"] for r in answer] == sorted(q["expected_ids"]), f"Pilot query changed: {q['name']}")
        examples += [f"## {q['name']}", "", q["question"], "", f"`python tools/record_views.py query {q['name']}`", ""]
        examples += [f"- [{r['id']}]({link(r['detail_path'] or r['source']['file'])}); original correction: {r['correction_class'] or 'none recorded'}." for r in answer]
        examples += ["", q["limit"], ""]
    put(f"{SHELF}/QUERIES.md", "\n".join(examples))
    put(f"{SHELF}/QUOTES.json", dict(schema_version=1, scope="Currently filed blockquotes in five canonical theory files; attribution, dates and supersession require review", quotes=quote_records))
    quote_md = ["# Filed quotation inventory", "", "Generated exact blockquote inventory, not authenticated original transcripts. All entries are unreviewed for attribution, source date, filing date and supersession. See adjacent source context and its repair/filing receipts. No current/superseded status is guessed; removed quotes are not resurrected. Previous inventory revisions belong in Git history.", ""]
    for q in quote_records:
        quote_md += [f"## {q['id']}", "", f"[Filed source, lines {q['line']}–{q['end_line']}]({link(q['file'], line=q['line'])}); status: unreviewed; source/filing dates: unknown; transcript: not independently checked.", "", q["raw_markdown"].rstrip(), ""]
    put(f"{SHELF}/QUOTES.md", "\n".join(quote_md))
    texture_paths = []
    for r in reviewed:
        a = r["annotation"]
        if r["annotation"]["record_kind"] != "texture":
            continue
        require(a.get("texture_note"), "Reviewed texture lacks a narrative note")
        name = f"{SHELF}/texture/{r['id']}.md"
        texture_paths.append(name)
        put(name, f"# {r['id']}\n\nGenerated annotation of an existing complete texture; no primary promotion.\n\nTheory links: {', '.join(a['theory_ids'])}.\n\n{a['texture_note']}\n\n[Full frozen outcome, estimates, controls and limits]({link(r['detail_path'], start=SHELF+'/texture')}). Construction judgment: {a['by_construction']}; {a['construction_reason']}\n")
    put(f"{SHELF}/TEXTURES.md", "# Reviewed texture notes\n\n" + coverage + "\n\n" + "\n".join(f"- [{Path(p).stem}]({link(p)})" for p in texture_paths) + "\n")
    start = f"""# Start here for evidence navigation

Generated additive navigation, approved November 11, 2026. Existing source records and stage authority remain binding.

1. Run `python tools/record_views.py check`. A stale or invalid view is not current evidence; finish the landing and run `build`, then `check`.
2. Read [SCOREBOARD](../SCOREBOARD.md) for the bounded reviewed claim register.
3. Choose [science](records/SCIENCE.md), [operations](records/OPERATIONS.md), [texture](records/TEXTURES.md), or [unclassified](records/UNCLASSIFIED.md) navigation.
4. Follow the original source and detail links for methods, estimates, controls, scope and corrections. [All records](records/RECORDS.json) retains every legacy ID and relationship.
5. Read the [five checked queries](records/QUERIES.md) and [format contract](records/README.md).

{coverage}

This view does not replace current AGENTS, STATE, TODO or the relevant current FINDINGS entries. The theory reading and continuity contract still applies before interpretation. A navigation tag such as attention is not evidence that attention was identified.

The ledger and FINDINGS remain the authoritative run record. No entry, anchor or original outcome has been moved or rewritten. Invalid, superseded and null results remain accessible. Claim standing comes from the reviewed register; new operations rows cannot promote it. Evidence validity may be withdrawn immediately, while theoretical interpretation waits for its authorized curator pass.

Every full landing still owes the existing write-through. After the last receipt/ACK and source update, run `python tools/record_views.py build` and `python tools/record_views.py check`. Never edit generated files by hand. If a reviewed row or document changes, re-review its overlay rather than blindly refreshing a pin. Unreviewed classification is not a scientific result.

[QUOTES](records/QUOTES.md) inventories currently filed text with exact source links; attribution and dates remain explicitly unreviewed. CURRENT is not generated: no exact versioned theory-thread state source has been identified. The existing theory files stay authoritative and are not retired as archives.

One bounded old-stage annotation task is in [the review queue](records/REVIEW_QUEUE.md). It uses existing authorized attention, creates no new wake or experiment, and cannot silently change theory. Physical relocation is deferred until every live writer and reader has a verified compatibility path.

Rollback: remove the additive navigation pointers and stop invoking the generator; original evidence remains in place. Preserve overlay/register history. Do not reset unrelated working-tree changes or alter live jobs.
"""
    require(len(start.splitlines()) < 300, "Startup view exceeds 300 lines")
    put("docs/START_HERE_FOR_AGENTS.md", start)
    src.verify_unchanged()
    manifest = dict(schema_version=1, generator="tools/record_views.py", sources={n: digest(v) for n, v in sorted(src.data.items())}, outputs={n: digest(v) for n, v in sorted(outputs.items())}, coverage=dict(records=len(records), reviewed=len(reviewed), unreviewed=len(unknown), quotes=len(quote_records)))
    put(f"{SHELF}/MANIFEST.json", manifest)
    return src, outputs


def run(root, command):
    pending_path = root / PENDING
    pending = pending_path.read_bytes() if pending_path.exists() else None
    require(command != "check" or pending is None, "Landing pending: finish full write-through, then build and check views")
    src, outputs = render(root)
    previous = root / f"{SHELF}/MANIFEST.json"
    if previous.exists():
        old = json.loads(previous.read_text('utf8'))
        obsolete = set(old["outputs"]) - outputs.keys()
        require(not obsolete, "Obsolete generated artifacts require explicit reconciliation: " + ", ".join(sorted(obsolete)))
    if command == "check":
        wrong = [n for n, data in outputs.items() if not (root/n).is_file() or (root/n).read_bytes() != data]
        require(not wrong, "Stale/missing generated views: " + ", ".join(wrong))
        src.verify_unchanged()
        require(not pending_path.exists(), "Landing started during freshness check")
    else:
        # Manifest is written last. check detects an interrupted or mixed generation.
        src.verify_unchanged()
        for name, data in outputs.items():
            if not (root/name).is_file() or (root/name).read_bytes() != data:
                atomic(root/name, data)
        src.verify_unchanged()
        current_pending = pending_path.read_bytes() if pending_path.exists() else None
        require(current_pending == pending, "Another writer started during generation; finish landing and retry")
        if pending is not None:
            pending_path.unlink()
    return json.loads(outputs[f"{SHELF}/MANIFEST.json"])["coverage"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["build", "check", "query"])
    parser.add_argument("name", nargs="?")
    args = parser.parse_args()
    try:
        if args.command == "query":
            require(not (ROOT/PENDING).exists(), "Landing pending; query after full filing")
            src, records, register, config, _ = load(ROOT)
            q = next((q for q in config["queries"] if q["name"] == args.name), None)
            require(q is not None, "Unknown query name")
            answer = query(records, register, q["filters"])
            src.verify_unchanged()
            require(not (ROOT/PENDING).exists(), "Landing started during query")
            print(json.dumps(dict(query=q["question"], limit=q["limit"], evidence=[dict(id=r["id"], source=r["source"], detail=r["detail_path"], correction=r["correction_class"]) for r in answer]), ensure_ascii=False, indent=2))
        else:
            print(json.dumps(dict(status="ok", command=args.command, **run(ROOT, args.command))))
    except (Invalid, OSError, KeyError, json.JSONDecodeError) as exc:
        print(f"record views: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
