"""Stage 8 administrative integrity, independent of scientific outcome direction.

DESIGN CHECK (2026-09-06)
lessons read: LESSONS sections 3 and 5 (coverage is the declared enumeration;
file presence is not a verdict; a ledger closes after everything it counts).
gates: Under the NULL, corrupt, misidentified, unresolved or unreceipted required
evidence refuses validated completion; failure direction is DOWN. Under the ALTERNATIVE,
resolved valid evidence, including nulls and documented blocked branches, closes
administratively. Bands are exhaustive: ok or explicit failure reasons.
Revalidation labels its source hashes and never rewrites the evidence it reads.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
import sys

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from runners.stage8 import cards as C
from runners.stage8.admission import admitted_readers
from runners.stage8.claims import confirmation_warrant, mapping_errors
from runners.stage8.manifest import expected_cells, _declared_cells, inapplicability
from soundingline.stage8 import OUTCOMES7, S8, now_iso, write_json

VALID = set(OUTCOMES7) | {"NOT_RUN"}
TERMINAL = {"COMPLETE", "BLOCKED", "FAILED", "DEFERRED"}
VERSION = "stage8-integrity-20260906.1"
RECEIPTS = ("RUN_CONTRACT", "EXPECTED_CELLS", "QUEUE_MANIFEST", "IDENTITY_HASHES",
            "TESTBED_SOURCES", "CORPUS_MANIFESTS", "ACCESS_RECEIPT", "COMPUTE_LEDGER",
            "ADAPTERS", "GATES", "EXPERTISE_GATE", "GENERATION_GATE", "SPLIT_RECEIPT",
            "CONFIRMATION_REGISTRY", "FRONTIER_LEDGER", "KEYSTONE_LOCK", "SCIENTIFIC_LOCK")


def _validate(root: Path, origin: Path, excluded: set[str]) -> dict:
    reasons, inputs, verdicts, bad, missing = [], {}, {}, [], []

    def fail(code, cell, detail):
        reasons.append({"code": code, "cell": cell, "detail": detail})

    def read(path):
        p = root / path
        if not p.is_file():
            fail("missing", path, "required evidence absent")
            return {}
        raw = p.read_bytes()
        inputs[path] = hashlib.sha256(raw).hexdigest()
        try:
            v = json.loads(raw)
            if not isinstance(v, dict):
                raise ValueError("expected JSON object")
            return v
        except (ValueError, UnicodeError) as e:
            fail("schema", path, str(e))
            return {}

    def local_path(value):
        p = Path(value)
        if p.is_absolute():
            # Historical references map only through their declared origin root.
            # Never fall back to live scientific files when checking a snapshot.
            p = p.relative_to(origin)
        resolved = (root / p).resolve()
        resolved.relative_to(root)
        return resolved

    registries = {n: read(f"{n}.json") for n in RECEIPTS}
    # Validate the shapes consumed by closure, including records whose file exists
    # but whose contents would otherwise crash or mislead the reporter.
    for name in ("ADAPTERS", "COMPUTE_LEDGER", "GATES"):
        for key, record in registries[name].items():
            if not isinstance(record, dict):
                fail("registry_schema", name, f"{key}: expected object record")
                continue
            if name == "ADAPTERS" and (any(not isinstance(record.get(k), str) or not record[k] for k in ("base", "revision", "path", "sha"))
                                       or not isinstance(record.get("heldout"), dict)):
                fail("registry_schema", name, f"{key}: missing adapter identity or heldout record")
            if name == "COMPUTE_LEDGER" and (not isinstance(record.get("ledger"), dict)
                                             or type(record.get("gpu_held_s")) not in (int, float)
                                             or not math.isfinite(record["gpu_held_s"]) or record["gpu_held_s"] < 0):
                fail("registry_schema", name, f"{key}: malformed compute charge")
            if name == "GATES" and type(record.get("passed")) is not bool:
                fail("registry_schema", name, f"{key}: missing boolean gate disposition")
    for name, field in (("TESTBED_SOURCES", "clones"), ("CORPUS_MANIFESTS", "items")):
        if not isinstance(registries[name].get(field), dict):
            fail("registry_schema", name, f"{field}: expected object")
    if any(not isinstance(v, dict) for v in (registries["TESTBED_SOURCES"].get("clones") or {}).values()):
        fail("registry_schema", "TESTBED_SOURCES", "clone entries must be objects")
    source_manifest = read("SOURCE_MANIFEST.json") if (root / "SOURCE_MANIFEST.json").is_file() else {}
    closures = source_manifest.get("capsule_closures") or {}
    for digest, files in closures.items():
        if (not isinstance(files, dict) or not files or "bootstrap.py" not in files
                or any(not re.fullmatch(r"[a-f0-9]{64}", str(value)) for value in files.values())
                or hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest() != digest):
            fail("capsule_source", "SOURCE_MANIFEST", "copied source closure has an invalid digest")
    contract, manifest = registries["RUN_CONTRACT"], registries["QUEUE_MANIFEST"]
    exp = registries["EXPECTED_CELLS"].get("cells")
    if not isinstance(exp, list):
        fail("expected_schema", "EXPECTED_CELLS", "cells must be a list")
        exp = []
    def declaration(x):
        return json.dumps({k: x.get(k) for k in ("question", "arm", "reader", "domain", "corner", "targets")}, sort_keys=True)
    original_expected = len(exp)
    original_declarations = exp
    superseded_enumeration = []
    if (Counter(map(declaration, exp)) == Counter(map(declaration, _declared_cells()))
            and Counter(map(declaration, exp)) != Counter(map(declaration, expected_cells()))):
        # A dated derived correction of the exact known over-enumeration. The
        # original manifest and its hash remain in the evidence; arbitrary omissions
        # or changes cannot enter through this compatibility case.
        superseded_enumeration = [dict(x, reason=inapplicability(x)) for x in exp if inapplicability(x)]
        exp = [x for x in exp if inapplicability(x) is None]
    if Counter(map(declaration, exp)) != Counter(map(declaration, expected_cells())):
        fail("expected_identity", "EXPECTED_CELLS", "enumeration differs from reviewed card definitions")
    for x in original_declarations:
        try:
            if local_path(x.get("output", "")) != root / str(x.get("question")) / "verdict.json":
                raise ValueError("wrong question output")
        except (ValueError, TypeError) as e:
            fail("expected_path", str(x.get("question")), str(e))
    if registries["IDENTITY_HASHES"].get("hashes") != {c: C.identity_hash(c) for c in C.ALL}:
        fail("card_identity", "IDENTITY_HASHES", "card identities differ from reviewed definitions")
    if set(contract.get("questions") or []) != set(C.QUESTIONS) or set(contract.get("attacks") or []) != set(C.ATTACKS):
        fail("contract_identity", "RUN_CONTRACT", "mandatory cards differ from contract")

    required = (set(C.ALL) | set(manifest)) - excluded
    rows_total, source_hashes, contract_hashes = 0, set(), set()
    factor_coverage = []
    for cell in sorted(required):
        card = cell.split("/")[0]
        if card not in C.ALL or not re.fullmatch(r"[A-Z][0-9]{2}(?:/x[0-9]+)?", cell):
            fail("cell_identity", cell, "unknown executable cell")
            continue
        rec = manifest.get(cell) or {}
        if rec.get("cell_id") != cell or rec.get("card") != card:
            fail("manifest_identity", cell, "manifest card/cell mismatch")
        try:
            if local_path(rec.get("produces", "")) != root / cell / "verdict.json":
                raise ValueError("wrong produces path")
        except (ValueError, TypeError) as e:
            fail("manifest_path", cell, str(e))
        if rec.get("exec_state") not in TERMINAL:
            fail("unresolved", cell, f"execution state {rec.get('exec_state')!r}")
        vp = f"{cell}/verdict.json"
        if not (root / vp).is_file():
            missing.append(cell)
        v = read(vp)
        if not v:
            continue
        verdicts[cell] = v
        if v.get("card") != card or v.get("cell_id") != cell:
            fail("result_identity", cell, "verdict card/cell mismatch")
        oc = v.get("outcome")
        if not isinstance(oc, str) or oc not in VALID:
            bad.append([cell, oc])
            fail("outcome", cell, "unknown outcome")
        if v.get("exec") not in TERMINAL or rec.get("exec_state") != v.get("exec") or rec.get("outcome") != oc:
            fail("disposition", cell, "manifest and verdict must agree on terminal execution and outcome")
        if not isinstance(v.get("reason"), str) or not v["reason"].strip():
            fail("reason", cell, "terminal disposition requires an explanation")
        if v.get("exec") in {"BLOCKED", "FAILED", "DEFERRED"}:
            if oc not in {"NOT_RUN", "INSTRUMENT_FAILED", "VOID"}:
                fail("blocked_outcome", cell, "unexecuted branch cannot supply a scientific outcome")
            # Scheduler-authored blocked receipts have no measurement or marker.
            continue
        if v.get("lane") not in {"discovery", "confirmation", "attack", "transfer", "conformance", "pilot"}:
            fail("lane", cell, "missing or invalid lane")
        marker = v.get("marker") or {}
        if marker.get("contract_version") != contract.get("contract_version") or not re.fullmatch(r"[a-f0-9]{16}", str(marker.get("contract_hash", ""))):
            fail("marker_contract", cell, "missing or incompatible contract marker")
        contract_hashes.add(str(marker.get("contract_hash")))
        outputs = marker.get("outputs") or {}
        if "metrics" not in outputs:
            fail("marker_outputs", cell, "metrics output must be receipted")
        for group, records in (("inputs", marker.get("inputs") or {}), ("outputs", outputs)):
            for name, receipt in records.items():
                try:
                    p = local_path(receipt["path"])
                    if group == "outputs" and name in {"metrics", "cases"} and p != root / cell / ("metrics.json" if name == "metrics" else "cases.jsonl"):
                        raise ValueError("output points to another cell")
                    digest = hashlib.sha256(p.read_bytes()).hexdigest()
                    inputs[p.relative_to(root).as_posix()] = digest
                    if digest != receipt.get("sha256"):
                        raise ValueError("content hash mismatch")
                except (OSError, ValueError, KeyError, TypeError) as e:
                    fail("marker_hash", cell, f"{group}/{name}: {e}")
        metrics = read(f"{cell}/metrics.json")
        if metrics.get("card") != card or metrics.get("lane") != v.get("lane"):
            fail("metrics_identity", cell, "metrics card/lane mismatch")
        cp = root / cell / "cases.jsonl"
        factors_due = [x for x in exp if x["question"] == card] if C.ALL[card]["unit"] in {"world", "maker"} else []
        matched = [0] * len(factors_due)
        if cp.exists():
            if "cases" not in outputs:
                fail("unreceipted_cases", cell, "cases present without completion hash")
            with cp.open(encoding="utf-8") as f:
                for line_no, line in enumerate(f, 1):
                    try:
                        r = json.loads(line)
                        if r.get("card") != card or r.get("cell_id") != cell or r.get("lane") != v.get("lane"):
                            raise ValueError("row card/cell/lane mismatch")
                        if type(r.get("valid")) is not bool or not r.get("unit_id") or not r.get("arm"):
                            raise ValueError("row validity, unit and arm required")
                        if not re.fullmatch(r"[a-f0-9]{16}", str(r.get("code_hash", ""))):
                            raise ValueError("missing source hash")
                        source_hashes.add(r["code_hash"])
                        copied = (r.get("extra") or {}).get("capsule_source_sha256")
                        if copied and copied not in closures:
                            fail("capsule_source", cell, "measured row refers to an absent copied-source closure")
                        rows_total += 1
                        if r["valid"]:
                            factors = r.get("factors") or {}
                            rd = r.get("model_id") if r["arm"] in C.MODEL_ARMS else "-"
                            for i, expected in enumerate(factors_due):
                                if (r["arm"] == expected["arm"] and rd == expected["reader"]
                                        and factors.get("domain") == expected["domain"]
                                        and all(factors.get(k) == value for k, value in expected["corner"].items())):
                                    matched[i] += 1
                    except (ValueError, AttributeError, TypeError) as e:
                        fail("row_schema", cell, f"line {line_no}: {e}")
                        break
        for expected, count in zip(factors_due, matched):
            state = "OBSERVED" if count else ("INSTRUMENT_UNRESOLVED" if oc in {"INSTRUMENT_FAILED", "VOID", "NOT_RUN"} else "MISSING")
            factor_coverage.append({**{k: expected[k] for k in ("arm", "reader", "domain", "corner")},
                                    "cell": cell, "valid_rows": count, "status": state})
            if state == "MISSING":
                fail("factor_coverage", cell, f"no valid rows for {declaration(expected)}")
    for name, field in (("ACCESS_RECEIPT", "all_raised"), ("SPLIT_RECEIPT", "clean"),
                        ("KEYSTONE_LOCK", "signed"), ("SCIENTIFIC_LOCK", "locked")):
        if registries[name].get(field) is not True:
            fail("receipt_failed", name, f"{field} must be true")
    for card in ("X12", "B03"):
        if card not in excluded and verdicts.get(card, {}).get("outcome") != "INFRASTRUCTURE":
            fail("integrity_card", card, "required integrity card did not pass")
    usd = registries["FRONTIER_LEDGER"].get("total_usd")
    cap_ok = type(usd) in (int, float) and math.isfinite(usd) and 0 <= usd <= 40
    if not cap_ok:
        fail("frontier_cap", "FRONTIER_LEDGER", "finite nonnegative total under authorized $40 cap required")
    selected = registries["CONFIRMATION_REGISTRY"].get("selected")
    if not isinstance(selected, list):
        fail("confirmation_schema", "CONFIRMATION_REGISTRY", "selected must be a list")
        selected = []
    if len(selected) > 3:
        fail("confirmation_cap", "CONFIRMATION_REGISTRY", "at most three claims")
    slots, paths, claims = set(), set(), set()
    for claim in selected:
        for error in mapping_errors(claim):
            fail("confirmation_mapping", str(claim.get("claim_id")), error)
        for key, seen in (("slot", slots), ("result_path", paths), ("claim_id", claims)):
            val = claim.get(key)
            if val is not None and val in seen:
                fail("confirmation_collision", str(val), f"duplicate {key}")
            if val is not None:
                seen.add(val)
    admission = admitted_readers(root)
    warrant = confirmation_warrant(root, {"selected": selected}, admission)
    for claim, value in warrant.items():
        inputs.update(value.get("evidence_hashes") or {})
        if value["status"] in {"INVALID", "MISSING"}:
            fail("confirmation_evidence", claim, str(value["reasons"] or value["status"]))
    return {"ok": not reasons, "reasons": reasons, "input_hashes": inputs,
            "original_expected": original_expected, "superseded_enumeration": superseded_enumeration,
            "expected": len(exp), "complete": sum(c in verdicts for c in C.ALL), "mandatory_total": len(C.ALL),
            "missing_mandatory": missing, "invalid_dispositions": bad,
            "outcomes": dict(Counter(str(v.get("outcome")) for v in verdicts.values())),
            "rows_total": rows_total, "confirmations_selected": len(selected), "confirmation_cap_ok": len(selected) <= 3,
            "factor_coverage": factor_coverage,
            "frontier_usd": usd, "frontier_under_cap": cap_ok, "admission": admission, "warrant": warrant,
            "recorded_row_source_hashes": sorted(source_hashes), "recorded_contract_hashes": sorted(contract_hashes)}


def validate(write: bool = False, *, root: Path | None = None, origin_root: Path | None = None,
             output_dir: Path | None = None, exclude_pending: set[str] | None = None) -> dict:
    root = Path(root or S8).resolve()
    origin = Path(origin_root or root).resolve()
    excluded = set(exclude_pending or ())
    if excluded - {"B03"}:
        raise ValueError("only B03 may be pending while B03 reconciles its prerequisites")
    try:
        cov = _validate(root, origin, excluded)
    except (OSError, ValueError, TypeError, AttributeError, KeyError) as e:
        cov = {"ok": False, "reasons": [{"code": "validation_error", "cell": "evidence", "detail": f"{type(e).__name__}: {e}"}]}
    cov.update(written_at=now_iso(), validator_version=VERSION,
               validator_sources={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in
                                  (Path(__file__), Path(__file__).with_name("admission.py"), Path(__file__).with_name("claims.py"),
                                   Path(__file__).with_name("manifest.py"), Path(__file__).with_name("cards.py"))},
               evidence_root=str(root), origin_root=str(origin),
               phase="prereconciliation" if excluded else "final", excluded_pending=sorted(excluded),
               limitations=["Factor coverage checks observed valid rows for world/maker cells; analysis and administrative cards are checked through their own terminal receipts and result hashes.",
                            "Copied-source references are verified where recorded; historical rows without them are not retroactively assigned current source identity.",
                            "Historical contract hashes include mutable closure fields; recorded hashes are retained, not relabeled as the closure hash."])
    if write:
        dest = Path(output_dir).resolve() if output_dir else root
        if (root / "SNAPSHOT.json").exists() and (dest == root or root in dest.parents):
            raise ValueError("immutable snapshot: derived outputs require a separate directory")
        if output_dir is None and root != S8.resolve():
            raise ValueError("detached validation requires an explicit derived output directory")
        write_json(dest / "COVERAGE.json", cov)
    return cov


if __name__ == "__main__":
    cov = validate(write="--write" in sys.argv)
    print(json.dumps({k: cov[k] for k in ("validator_version", "ok", "reasons", "limitations")}, indent=2))
    sys.exit(0 if cov["ok"] else 1)
