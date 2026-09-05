"""The testbed cells T01 to T05 (brief §10): CPU lane, network only in the fetch side."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from runners.stage8 import cards as C                                              # noqa: E402
from runners.stage8.cardrun import SMOKE, CardRun8                                 # noqa: E402
from soundingline.stage8 import now_iso, read_registry, update_registry            # noqa: E402


def _finish(run: CardRun8, metrics: dict, outcome: str, reason: str) -> int:
    run.finish(metrics, {"exec": "COMPLETE", "outcome": outcome, "primary": C.ALL[run.card]["primary"], "reason": reason},
               rival=C.ALL[run.card]["discriminator"])
    return 0


def run_T01(run: CardRun8) -> int:
    from runners.stage8.testbed import clones as CL                               # noqa: PLC0415
    if SMOKE:
        out = {k: {"status": "SMOKE_SKIPPED"} for k in CL.CLONES}
        update_registry("TESTBED_SOURCES", lambda t: {**t, "clones": {k: {**v, "receipt": CL.receipt(k)} for k, v in CL.CLONES.items()}, "smoke": True})
        return _finish(run, {"clones": out}, "INFRASTRUCTURE", "smoke: no clone attempted; receipts of what is present written")
    out = CL.clone_all()
    pinned = sum(1 for v in out.values() if v["status"] == "CLONED_PINNED")
    failed = [k for k, v in out.items() if v["status"].startswith("CLONE_FAILED")]
    return _finish(run, {"clones": {k: {"status": v["status"], "head": (v.get("receipt") or {}).get("head"), "license": (v.get("receipt") or {}).get("license_first_line")} for k, v in out.items()}},
                   "INFRASTRUCTURE" if not failed else "DESCRIPTIVE", f"{pinned}/{len(out)} pinned; failed {failed}")


def run_T02(run: CardRun8) -> int:
    from runners.stage8.testbed import corpora as CO                              # noqa: PLC0415
    if SMOKE:
        update_registry("CORPUS_MANIFESTS", lambda c: {**c, "items": {k: ("IN_HAND" if v.get("in_hand") else "SMOKE_SKIPPED") for k, v in CO.CORPORA.items()}, "smoke": True})
        return _finish(run, {"items": len(CO.CORPORA)}, "INFRASTRUCTURE", "smoke: no fetch attempted")
    out = CO.fetch_all()
    st = {k: v["status"] for k, v in out["items"].items()}
    bad = [k for k, v in st.items() if v == "MANIFEST_FAILED"]
    return _finish(run, {"status": st, "manifest": str(CO.MANIFEST)}, "INFRASTRUCTURE" if not bad else "DESCRIPTIVE", f"{sum(1 for v in st.values() if v in ('MANIFESTED', 'IN_HAND'))}/{len(st)} manifested or in hand; failed {bad}")


def run_T04(run: CardRun8) -> int:
    from runners.stage8.testbed import loaders as L                               # noqa: PLC0415
    fx = L.fixtures_pass()
    sm = L.smoke_reads() if not SMOKE else {"argrewrite_v2": {"present": True, "files": 0}, "coauthor": {"sessions": 0}, "scholawrite": {"sessions": 0}}
    update_registry("TESTBED", lambda t: {**t, "fixtures": fx, "smoke": sm, "at": now_iso()})
    ok = all(v.get("pass") is not False for v in fx.values())
    return _finish(run, {"fixtures": fx, "smoke": sm}, "INFRASTRUCTURE" if ok else "INSTRUMENT_FAILED", f"fixtures {sum(1 for v in fx.values() if v.get('pass'))} pass of {sum(1 for v in fx.values() if v.get('pass') is not None)}; smoke {sm}")


def run_T05(run: CardRun8) -> int:
    from runners.stage8.testbed import loaders as L                               # noqa: PLC0415
    sm = (read_registry("TESTBED") or {}).get("smoke") or {}
    bl = L.baselines(sm)
    update_registry("TESTBED", lambda t: {**t, "baselines": bl, "at": now_iso()})
    n_rep = sum(1 for v in bl.values() if v.get("reproduced") is not None)
    return _finish(run, {"baselines": bl}, "DESCRIPTIVE", f"{n_rep}/{len(bl)} corpora with a measured number; the rest NOT_REPRODUCED with the reason on the card")


def run_T03(run: CardRun8) -> int:
    from runners.stage8.testbed import catalog as CAT                             # noqa: PLC0415
    if SMOKE:
        return _finish(run, {"cards": len(CAT.CLONES) + len(CAT.CORPORA), "rendered_chars": len(CAT.render())}, "INFRASTRUCTURE", "smoke: cards rendered, TOOLS.md not written")
    rec = CAT.write_cards()
    return _finish(run, rec, "INFRASTRUCTURE", f"{rec['cards']} catalog cards written to docs/TOOLS.md")


def run_card(run: CardRun8) -> int:
    return {"T01": run_T01, "T02": run_T02, "T03": run_T03, "T04": run_T04, "T05": run_T05}[run.card](run)
