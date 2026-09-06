"""Deterministic adversarial checks; no model transport or production roots."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

assert os.environ.get("S7_ROOT") and os.environ.get("S7_SMOKE") == "1"
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from runners.stage8 import admission as A, claims as CL, confirmation as CF, report as R, validate as V
from runners.stage8 import cards as C, manifest as M, scheduler as S
from soundingline.stage8 import RunContract8, S8, write_registry


def put(root, name, value):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8", newline="\n")
    return path


def identity(reader="r1"):
    return {k: (reader if k == "reader" else "same-" + k) for k in A.IDENTITY_FIELDS}


def gates():
    return ({"readers": {r: {"prediction_passed": True, "identity": identity(r)} for r in ("r1", "r2")}},
            {"fm": {"readers": {r: {"generation_passed": True, "identity": identity(r)} for r in ("r1", "r2")}}})


def fixture(root):
    """Complete valid nulls, one instrument failure, and honestly unrun confirmations."""
    for name in V.RECEIPTS:
        put(root, name + ".json", {"fixture": True})
    for name in ("ADAPTERS", "COMPUTE_LEDGER"):
        put(root, name + ".json", {})
    put(root, "TESTBED_SOURCES.json", {"clones": {}})
    put(root, "CORPUS_MANIFESTS.json", {"items": {}})
    put(root, "RUN_CONTRACT.json", {"questions": list(C.QUESTIONS), "attacks": list(C.ATTACKS), "contract_version": "8.0.0"})
    exp = [dict(x, output=str(root / x["question"] / "verdict.json")) for x in M.expected_cells()]
    put(root, "EXPECTED_CELLS.json", {"cells": exp})
    put(root, "IDENTITY_HASHES.json", {"hashes": {c: C.identity_hash(c) for c in C.ALL}})
    for name, field in (("ACCESS_RECEIPT", "all_raised"), ("SPLIT_RECEIPT", "clean"),
                        ("KEYSTONE_LOCK", "signed"), ("SCIENTIFIC_LOCK", "locked")):
        put(root, name + ".json", {field: True})
    put(root, "FRONTIER_LEDGER.json", {"total_usd": 0})
    put(root, "CONFIRMATION_REGISTRY.json", {"selected": []})
    pred, gen = gates()
    for r in gen["fm"]["readers"].values():
        r["generation_passed"] = False
    put(root, "EXPERTISE_GATE.json", pred)
    put(root, "GENERATION_GATE.json", gen)
    put(root, "GATES.json", {})
    manifest = {}
    for card in C.ALL:
        oc = "INFRASTRUCTURE" if card in ("B03", "X12") else ("INSTRUMENT_FAILED" if card == "E04" else "VALID_NULL")
        if card in ("B01", "B02"):
            oc = "NOT_RUN"
        mp = put(root, f"{card}/metrics.json", {"card": card, "lane": "discovery"})
        outputs = {"metrics": {"path": str(mp), "sha256": CL.file_hash(mp)}}
        if C.ALL[card]["unit"] in {"world", "maker"}:
            cp = root / card / "cases.jsonl"
            rows = [{"card": card, "cell_id": card, "lane": "discovery", "unit_id": f"fixture-{i}",
                     "arm": x["arm"], "model_id": x["reader"], "valid": True, "code_hash": "b" * 16,
                     "factors": dict(x["corner"], domain=x["domain"])} for i, x in enumerate(exp) if x["question"] == card]
            cp.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8", newline="\n")
            outputs["cases"] = {"path": str(cp), "sha256": CL.file_hash(cp)}
        put(root, f"{card}/verdict.json", {"card": card, "cell_id": card, "lane": "discovery",
            "exec": "COMPLETE", "outcome": oc, "reason": "fixture disposition",
            "marker": {"contract_version": "8.0.0", "contract_hash": "a" * 16,
                       "outputs": outputs, "inputs": {}}})
        manifest[card] = {"card": card, "cell_id": card, "exec_state": "COMPLETE", "outcome": oc,
                          "produces": str(root / card / "verdict.json")}
    put(root, "QUEUE_MANIFEST.json", manifest)


class Maintenance(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=S8)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.p, self.g = gates()

    def read(self, name):
        return json.loads((self.root / name).read_text(encoding="utf-8"))

    def change(self, name, **fields):
        v = self.read(name)
        v.update(fields)
        put(self.root, name, v)

    def test_gate_failure_and_rerun_cannot_admit(self):
        self.g["fm"]["readers"]["r1"]["generation_passed"] = False
        for _ in range(2):
            self.p["readers"]["r1"] = {"prediction_passed": True, "identity": identity()}
            x = A.eligibility(self.p, self.g)
            self.assertFalse(x["r1"]["admitted"])
            self.assertTrue(x["r2"]["admitted"])

    def test_missing_and_mismatched_gate_identity_stays_pending(self):
        self.assertEqual(A.eligibility(self.p, {})["r1"]["admission"], "PENDING")
        for key in A.IDENTITY_FIELDS:
            g = deepcopy(self.g)
            g["fm"]["readers"]["r1"]["identity"][key] = "different"
            self.assertFalse(A.eligibility(self.p, g)["r1"]["admitted"], key)

    def test_admission_is_read_only(self):
        before = deepcopy((self.p, self.g))
        A.eligibility(self.p, self.g)
        self.assertEqual(before, (self.p, self.g))

    def test_measured_identity_rejects_mixed_rows(self):
        row = {"model_id": "r1", "arm": "FM", "valid": True, "code_hash": "code", "contract_hash": "contract",
               "extra": {"capsule_source_sha256": "copied", "notes": {"revision": "actual", "adapter_sha": "adapter"}}}
        self.assertEqual(A.gate_identity([row], "r1", "FM")["model_revision"], "actual")
        other = deepcopy(row)
        other["extra"]["notes"]["adapter_sha"] = "other"
        self.assertIn("error", A.gate_identity([row, other], "r1", "FM"))

    def test_runtime_confirmation_and_routing_share_admission(self):
        from runners.stage8 import engines as E
        from types import SimpleNamespace
        fixture(self.root)
        with patch.object(A, "admitted_readers", return_value=A.admitted_readers(self.root)):
            self.assertFalse(any(x["passed"] for x in E.admitted_readers().values()))
            with patch.object(CF, "read_registry", side_effect=lambda name: self.read(name + ".json") if (self.root / (name + ".json")).exists() else {}), patch.object(CF, "S8", self.root), patch.object(CF, "interrupts", return_value=[]):
                self.assertEqual(CF.freeze_confirmations()["selected"], [])
                captured = []
                CF.run_B04(SimpleNamespace(finish=lambda metrics, verdict: captured.append(metrics)))
                self.assertIn("no trained reader passes both", captured[0]["routing"][0]["shape"])

    def test_frozen_legacy_registry_preserved(self):
        reg = {"selected": [{"card": "G02", "slot": 1}, {"card": "A03", "slot": 2}, {"card": "E08", "slot": 3}]}
        with patch.object(CF, "read_registry", return_value=deepcopy(reg)), patch.object(CF, "write_registry") as writer:
            self.assertEqual(CF.freeze_confirmations(), reg)
            writer.assert_not_called()
        self.assertTrue(CL.mapping_errors(reg["selected"][2]))

    def test_copied_source_receipt_changes_with_inherited_helper(self):
        from runners.stage8.runtime import copied_sources
        (self.root / "reader").mkdir()
        (self.root / "reader/client.py").write_text("original", encoding="utf-8")
        (self.root / "bootstrap.py").write_text("bootstrap", encoding="utf-8")
        first = copied_sources(self.root)
        (self.root / "reader/client.py").write_text("changed", encoding="utf-8")
        second = copied_sources(self.root)
        self.assertNotEqual(first["sha256"], second["sha256"])
        self.assertEqual(first["files"]["bootstrap.py"], second["files"]["bootstrap.py"])

    def test_inherited_scoring_counterexamples_remain_quarantined(self):
        from runners.stage7.reader.client import Client
        class Stub(Client):
            def __init__(self, valid):
                self.calls, self.valid = [], valid
            def likelihood(self, body, options, evidence_sha, salt, instruction=""):
                self.calls.append((salt, list(options)))
                return {"valid": self.valid, "probs": {k: 1/len(options) for k in options}}
        client = Stub(True)
        result = client.likelihood_any("fixture", {str(i): str(i) for i in range(21)}, "fixture", "test")
        final = set(client.calls[-1][1])
        late = set(client.calls[2][1]) | set(client.calls[3][1])
        self.assertFalse(final & late)  # reproduced historical defect, not a repair assertion
        self.assertTrue(result["valid"])
        client = Stub(False)
        self.assertTrue(client.likelihood_any("fixture", {str(i): str(i) for i in range(21)}, "fixture", "test")["valid"])

    def candidates(self):
        for card, scope, point in (("G02", "whole", .4), ("A03", "whole", .3), ("E08", "tail", .2)):
            put(self.root, f"{card}/verdict.json", {"card": card, "exec": "COMPLETE", "outcome": "SUPPORT_CANDIDATE"})
            put(self.root, f"{card}/metrics.json", {scope: {"r1": {"outcome": "SUPPORT_CANDIDATE", "point": point,
                "ci": [point-.1, point+.1], "arm": "FM", "rival": "DOM", "threshold": .03}}})
            self.measured_rows(card)
        return CL.select_claims(self.root, A.eligibility(self.p, self.g))

    def measured_rows(self, cell):
        stamp = identity()
        row = {"cell_id": cell, "model_id": "r1", "arm": "FM", "valid": True,
               "code_hash": stamp["scoring"], "contract_hash": stamp["contract"],
               "extra": {"capsule_source_sha256": stamp["capsule_sources"],
                         "notes": {"revision": stamp["model_revision"], "adapter_sha": stamp["adapter_sha"]}}}
        # The historical code hash represents both construction and scoring.
        self.p["readers"]["r1"]["identity"]["construction"] = stamp["scoring"]
        self.g["fm"]["readers"]["r1"]["identity"]["construction"] = stamp["scoring"]
        (self.root / cell / "cases.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8", newline="\n")

    def confirmation_result(self, claim, outcome="COUNTEREVIDENCE"):
        cell = f"{claim['card']}/confirmation"
        put(self.root, f"{cell}/verdict.json", {"card": claim["card"], "cell_id": cell,
            "lane": "confirmation", "exec": "COMPLETE", "outcome": outcome})
        put(self.root, f"{cell}/metrics.json", {"card": claim["card"], "lane": "confirmation",
            claim["slice"]: {claim["reader"]: dict(claim["estimand"], outcome=outcome)}})
        self.measured_rows(cell)
        put(self.root, claim["result_path"], {"card": claim["result_card"], "claim_id": claim["claim_id"],
            "reader": claim["reader"], "exec": "COMPLETE", "outcome": outcome,
            "confirmation_hashes": {name: CL.file_hash(self.root / cell / name) for name in
                                    ("verdict.json", "metrics.json", "cases.jsonl")}})

    def test_three_claims_have_two_paths_and_explicit_unrun(self):
        reg = self.candidates()
        self.assertEqual([x["slot"] for x in reg["selected"]], [1, 2, 3])
        self.assertEqual([x["result_path"] for x in reg["selected"]], ["B01/verdict.json", "B02/verdict.json", None])
        self.assertEqual(reg["selected"][2]["status"], "UNIMPLEMENTED")
        self.assertTrue(all(not CL.mapping_errors(x) for x in reg["selected"]))

    def test_other_reader_and_diagnosis_cannot_qualify(self):
        self.candidates()
        self.g["fm"]["readers"]["r1"]["generation_passed"] = False
        self.assertEqual(CL.select_claims(self.root, A.eligibility(self.p, self.g))["selected"], [])
        for card in ("G02", "A03", "E08"):
            self.change(f"{card}/verdict.json", diagnosis_only=True)
        self.assertEqual(CL.select_claims(self.root, A.eligibility(*gates()))["selected"], [])

    def test_failed_confirmation_stays_failed_and_b03_cannot_replace(self):
        reg = self.candidates()
        claim = reg["selected"][0]
        self.confirmation_result(claim)
        w = CL.confirmation_warrant(self.root, reg, A.eligibility(self.p, self.g))
        self.assertEqual(w[claim["claim_id"]]["outcome"], "COUNTEREVIDENCE")
        claim["result_path"] = "B03/verdict.json"
        self.assertTrue(CL.mapping_errors(claim))
        self.assertIsNone(CL.confirmation_warrant(self.root, reg, A.eligibility(self.p, self.g))[claim["claim_id"]]["outcome"])

    def test_confirmation_source_changes_and_identity_mismatch_refuse(self):
        reg = self.candidates()
        claim = reg["selected"][0]
        self.confirmation_result(claim)
        def warrant():
            return CL.confirmation_warrant(self.root, reg, A.eligibility(self.p, self.g))[claim["claim_id"]]
        self.assertEqual(warrant()["status"], "RESOLVED")
        self.change(claim["result_path"], outcome="SUPPORT_CANDIDATE")
        self.assertEqual(warrant()["status"], "INVALID")
        self.confirmation_result(claim)
        self.change(claim["confirmation_source_path"], diagnosis_only=True)
        self.assertEqual(warrant()["status"], "INVALID")
        self.confirmation_result(claim)
        self.change(claim["source_path"], reason="changed after freeze")
        self.assertEqual(warrant()["status"], "INVALID")

    def test_measured_discovery_identity_required_for_selection(self):
        self.candidates()
        for card in ("G02", "A03", "E08"):
            path = self.root / card / "cases.jsonl"
            row = json.loads(path.read_text(encoding="utf-8"))
            row["extra"]["notes"]["adapter_sha"] = "different"
            path.write_text(json.dumps(row) + "\n", encoding="utf-8", newline="\n")
        self.assertEqual(CL.select_claims(self.root, A.eligibility(self.p, self.g))["selected"], [])

    def test_null_and_instrument_failure_close_administratively(self):
        fixture(self.root)
        cov = V.validate(root=self.root)
        self.assertTrue(cov["ok"], cov["reasons"])
        self.assertEqual(cov["outcomes"]["INSTRUMENT_FAILED"], 1)
        self.assertEqual(cov["confirmations_selected"], 0)

    def test_exact_legacy_overenumeration_is_explicitly_superseded(self):
        fixture(self.root)
        legacy = [dict(x, output=str(self.root / x["question"] / "verdict.json")) for x in M._declared_cells()]
        self.change("EXPECTED_CELLS.json", cells=legacy)
        cov = V.validate(root=self.root)
        self.assertTrue(cov["ok"], cov["reasons"])
        self.assertEqual(len(cov["superseded_enumeration"]), 10)
        self.assertEqual(cov["original_expected"] - cov["expected"], 10)
        self.change("EXPECTED_CELLS.json", cells=legacy[1:])
        self.assertFalse(V.validate(root=self.root)["ok"])
        excluded = next(x for x in legacy if M.inapplicability(x))
        excluded["output"] = str(self.root / "B03/verdict.json")
        self.change("EXPECTED_CELLS.json", cells=legacy)
        self.assertFalse(V.validate(root=self.root)["ok"])

    def test_unreceipted_copied_source_refuses(self):
        fixture(self.root)
        cp = self.root / "A01/cases.jsonl"
        rows = [json.loads(line) for line in cp.read_text(encoding="utf-8").splitlines()]
        rows[0]["extra"] = {"capsule_source_sha256": "c" * 64}
        cp.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8", newline="\n")
        v = self.read("A01/verdict.json")
        v["marker"]["outputs"]["cases"]["sha256"] = CL.file_hash(cp)
        put(self.root, "A01/verdict.json", v)
        cov = V.validate(root=self.root)
        self.assertFalse(cov["ok"])
        self.assertTrue(any(r["code"] == "capsule_source" for r in cov["reasons"]))

    def test_documented_blocked_branch_closes(self):
        fixture(self.root)
        self.change("G01/verdict.json", exec="BLOCKED", outcome="NOT_RUN", reason="generation gate failed")
        m = self.read("QUEUE_MANIFEST.json")
        m["G01"].update(exec_state="BLOCKED", outcome="NOT_RUN")
        put(self.root, "QUEUE_MANIFEST.json", m)
        self.assertTrue(V.validate(root=self.root)["ok"])
        self.change("G01/verdict.json", reason="")
        self.assertFalse(V.validate(root=self.root)["ok"])

    def test_bad_verdicts_refuse(self):
        for mutation in ({"card": "G02"}, {"cell_id": "G01/x1"}, {"outcome": "MAGIC"}, {"exec": "RUNNING"}, {"marker": []}):
            fixture(self.root)
            self.change("G01/verdict.json", **mutation)
            self.assertFalse(V.validate(root=self.root)["ok"], mutation)
        (self.root / "G01/verdict.json").write_text("{broken", encoding="utf-8")
        self.assertFalse(V.validate(root=self.root)["ok"])

    def test_missing_receipts_and_nonfinite_caps_refuse(self):
        for receipt in V.RECEIPTS:
            fixture(self.root)
            (self.root / (receipt + ".json")).unlink()
            self.assertFalse(V.validate(root=self.root)["ok"], receipt)
        for total in (41, -1, float("nan"), float("inf"), None, "0"):
            fixture(self.root)
            self.change("FRONTIER_LEDGER.json", total_usd=total)
            self.assertFalse(V.validate(root=self.root)["ok"], total)

    def test_malformed_registry_record_cannot_pass_then_crash_reporter(self):
        for name, value in (("ADAPTERS", {"broken": True}), ("COMPUTE_LEDGER", {"broken": {}}),
                            ("TESTBED_SOURCES", {"clones": {"broken": True}}), ("GATES", {"broken": {"passed": "yes"}})):
            fixture(self.root)
            put(self.root, name + ".json", value)
            self.assertFalse(V.validate(root=self.root)["ok"], name)

    def test_removing_expected_factor_and_wrong_hash_refuse(self):
        fixture(self.root)
        e = self.read("EXPECTED_CELLS.json")
        self.change("EXPECTED_CELLS.json", cells=e["cells"][1:])
        self.assertFalse(V.validate(root=self.root)["ok"])
        fixture(self.root)
        self.change("G01/metrics.json", surprise="changed after completion")
        self.assertFalse(V.validate(root=self.root)["ok"])

    def test_missing_measured_factor_refuses_even_with_updated_hash(self):
        fixture(self.root)
        cp = self.root / "A01/cases.jsonl"
        rows = [json.loads(x) for x in cp.read_text().splitlines()]
        cp.write_text("".join(json.dumps(x) + "\n" for x in rows if x["factors"]["n_earlier"] != 3), encoding="utf-8")
        v = self.read("A01/verdict.json")
        v["marker"]["outputs"]["cases"]["sha256"] = CL.file_hash(cp)
        put(self.root, "A01/verdict.json", v)
        cov = V.validate(root=self.root)
        self.assertFalse(cov["ok"])
        self.assertTrue(any(x["code"] == "factor_coverage" for x in cov["reasons"]))

    def test_unresolved_expansion_refuses(self):
        fixture(self.root)
        m = self.read("QUEUE_MANIFEST.json")
        m["A01/x1"] = dict(m["A01"], cell_id="A01/x1", exec_state="RUNNING", produces=str(self.root / "A01/x1/verdict.json"))
        put(self.root, "QUEUE_MANIFEST.json", m)
        self.assertFalse(V.validate(root=self.root)["ok"])

    def test_b03_prereconciliation_cannot_exclude_other_cards(self):
        fixture(self.root)
        (self.root / "B03/verdict.json").unlink()
        cov = V.validate(root=self.root, exclude_pending={"B03"})
        self.assertTrue(cov["ok"], cov["reasons"])
        self.assertEqual(cov["phase"], "prereconciliation")
        self.assertFalse(V.validate(root=self.root)["ok"])
        with self.assertRaises(ValueError):
            V.validate(root=self.root, exclude_pending={"E04"})

    def test_snapshot_writes_are_refused_and_bytes_preserved(self):
        fixture(self.root)
        put(self.root, "SNAPSHOT.json", {"immutable": True})
        before = {p.relative_to(self.root).as_posix(): CL.file_hash(p) for p in self.root.rglob("*") if p.is_file()}
        with self.assertRaises(ValueError):
            V.validate(write=True, root=self.root, output_dir=self.root)
        V.validate(write=True, root=self.root, output_dir=Path(self.tmp.name).parent / "derived")
        after = {p.relative_to(self.root).as_posix(): CL.file_hash(p) for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_reporter_and_scheduler_refuse_integrity_failure(self):
        contract = RunContract8.create()
        contract.data.update(execution_start="2026-09-04T00:00:00", exhausted=True)
        contract.save()
        bad = {"ok": False, "phase": "final", "validator_version": "fixture", "reasons": ["known failure"]}
        with patch.object(V, "validate", return_value=bad), self.assertRaises(R.PacketRefused):
            R.write_final_packet(force=True)
        with patch.object(S, "validate", return_value=bad), patch.object(R, "write_final_packet") as packet, patch.object(S, "log"):
            self.assertEqual(S.finalize_report(), 2)
            packet.assert_not_called()
        status = json.loads((S8 / "SCHEDULER_STATUS.json").read_text())
        self.assertTrue(status["execution_closed"])
        self.assertFalse(status["integrity_ok"])
        good = {"ok": True, "reasons": [], "validator_version": "fixture"}
        with patch.object(S, "validate", return_value=good), patch.object(R, "write_final_packet", side_effect=OSError("disk full")), patch.object(S, "log"):
            self.assertEqual(S.finalize_report(), 2)
        status = json.loads((S8 / "SCHEDULER_STATUS.json").read_text())
        self.assertTrue(status["integrity_ok"])
        self.assertFalse(status["packet_written"])
        self.assertEqual(status["packet_error"], "disk full")

    def test_reporter_accepts_valid_null_fixture_without_licensing_reader(self):
        from types import SimpleNamespace
        fixture(self.root)
        contract = SimpleNamespace(data={"execution_start": "fixture", "exhausted": True},
            elapsed_h=lambda: 48, hash=lambda: "fixture", duration_report=lambda _: {
                "elapsed_hours": 48, "gpu_lock_held_hours": 0, "lost_hours_recorded": 0})
        reg = lambda name: self.read(name + ".json") if (self.root / (name + ".json")).exists() else {}
        admission = A.admitted_readers(self.root)
        with patch.object(R.RunContract8, "load", return_value=contract), patch.object(R, "S8", self.root), patch.object(V, "S8", self.root), patch.object(R, "read_registry", side_effect=reg), patch.object(R, "interrupts", return_value=[]), patch.object(A, "admitted_readers", return_value=admission), patch.object(R, "write_packet", return_value=self.root / "packet.md") as write:
            R.write_final_packet()
            text = write.call_args.args[0]
            self.assertIn("Administrative integrity passed", text)
            self.assertIn("NOT_ADMITTED", text)
            self.assertIn("Support candidates: none", text)
            self.assertIn("INSTRUMENT_FAILED", text)


if __name__ == "__main__":
    S8.mkdir(parents=True, exist_ok=True)
    unittest.main(verbosity=2)
