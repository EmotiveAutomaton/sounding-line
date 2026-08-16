"""GEAR 3 — cloud burst execution on Modal, behind the curator's stone guardrails.

THE STONE RULES (his ruling, 2026-08-16, verbatim intent):
  1. Gear 3 NEVER runs without his explicit approval, per use. Every invocation requires
     --approval carrying his approving words and their date; absent that, this script
     refuses before any cloud object is touched.
  2. NO MORE THAN $10 EVER runs without a fresh explicit approval: the cumulative estimated
     spend since his last recorded cap-approval, plus the requested run's estimate, must
     stay under HARD_CAP_DOLLARS. Crossing it requires a FINAL APPROVAL REQUEST submitted
     to him first - exactly what will run, how long it will take, every test's details, and
     the total dollar amount - and his response recorded via --cap-approval. The refusal
     path prints the request template; there is no override flag that skips him.
  3. Gear 3 is for RARE bursts. Recreation-gate arms stay local (hardware and precision
     drift move second-decimal values); gear 3 is for Phase-2 experiments whose comparisons
     are internal to one cloud run.

Every run and every cap-approval is appended to results/gear3_ledger.json - the ledger is
the enforcement record and commits with the repo (it contains no secrets; the token lives
in ~/.modal.toml).

Usage:
  python runners/gear3.py estimate --cmd "..." --gpu A100 --est-minutes 12
  python runners/gear3.py run --cmd "runners/run_pan_winner.py --encoder roberta ..."
      --produces results/pan_winner/x.json --gpu A100 --est-minutes 12
      --approval "his words, YYYY-MM-DD" [--cap-approval "his words raising the window"]
  python runners/gear3.py ledger

One-time corpus upload (billed as storage, cents):
  modal volume create sounding-line-corpora
  modal volume put sounding-line-corpora corpora/public/pan_style/pan2024 /pan2024
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LEDGER = REPO / "results" / "gear3_ledger.json"

# Modal's rich progress output prints unicode glyphs; the Windows console's cp1252 raised
# UnicodeEncodeError mid-run and killed the client (2026-08-16). Force utf-8, never crash
# on a glyph.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                                 # noqa: BLE001
        pass

HARD_CAP_DOLLARS = 10.00          # the curator's stone ceiling - never edit without his words
RATES = {"A100": 2.50, "H100": 3.95, "L40S": 1.95, "L4": 0.80}   # Modal $/h, 2026-08-16
SAFETY = 1.4                      # estimate tax: image pull, data mount, eval overhead


LEDGER_LOCK = LEDGER.with_suffix(".lock")


def _lock_ledger() -> None:
    """The ledger is the stone's enforcement record; concurrent package invocations must
    never lose a spend entry to a read-modify-write race."""
    import os
    for _ in range(600):
        try:
            fd = os.open(LEDGER_LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            return
        except FileExistsError:
            time.sleep(0.5)
    raise RuntimeError("gear3 ledger lock held for 5 minutes; investigate before spending")


def _unlock_ledger() -> None:
    LEDGER_LOCK.unlink(missing_ok=True)


def load_ledger() -> dict:
    if LEDGER.exists():
        return json.loads(LEDGER.read_text(encoding="utf-8"))
    return {"runs": [], "cap_approvals": []}


def save_ledger(led: dict) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(led, indent=1), encoding="utf-8", newline="\n")


def window_spend(led: dict) -> float:
    """Estimated dollars spent since the curator's last cap-approval."""
    last = max((a["ts"] for a in led["cap_approvals"]), default=0.0)
    return sum(r["est_actual_dollars"] for r in led["runs"] if r["ts"] > last)


def estimate_dollars(gpu: str, est_minutes: float) -> float:
    return round(RATES[gpu] * (est_minutes / 60.0) * SAFETY, 2)


def refuse_over_cap(led: dict, est: float, args) -> None:
    spent = window_spend(led)
    print("=" * 72)
    print("GEAR 3 REFUSED: the $10 stone ceiling would be crossed.")
    print(f"  spent since last cap-approval: ${spent:.2f}")
    print(f"  this run's estimate:           ${est:.2f}")
    print(f"  ceiling:                       ${HARD_CAP_DOLLARS:.2f}")
    print()
    print("FINAL APPROVAL REQUEST to submit to the curator before proceeding:")
    print(f"  planned command : {args.cmd}")
    print(f"  GPU / est time  : {args.gpu} / ~{args.est_minutes} min")
    print(f"  est cost        : ${est:.2f} (rate ${RATES[args.gpu]}/h x {SAFETY} tax)")
    print(f"  window total if approved: ${spent + est:.2f}")
    print("  plus: what the test is, its hypothesis, and its produces path.")
    print("On his approval, rerun with --cap-approval \"<his exact words, dated>\".")
    print("=" * 72)
    sys.exit(3)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["estimate", "run", "ledger"])
    ap.add_argument("--cmd", help="repo-relative runner command line")
    ap.add_argument("--produces", help="repo-relative result path the runner writes")
    ap.add_argument("--gpu", choices=sorted(RATES), default="A100")
    ap.add_argument("--est-minutes", type=float, default=15.0)
    ap.add_argument("--timeout-minutes", type=float, default=None,
                    help="hard kill in the cloud; defaults to 3x the estimate")
    ap.add_argument("--approval", default="",
                    help="the curator's approving words for THIS use, with date. Required.")
    ap.add_argument("--cap-approval", default="",
                    help="the curator's words approving spend past the $10 window")
    args = ap.parse_args()

    led = load_ledger()
    if args.mode == "ledger":
        print(json.dumps(led, indent=1))
        print(f"window spend since last cap-approval: ${window_spend(led):.2f} "
              f"of ${HARD_CAP_DOLLARS:.2f}")
        return

    est = estimate_dollars(args.gpu, args.est_minutes)
    if args.mode == "estimate":
        print(f"estimate: ${est:.2f} ({args.gpu} ~{args.est_minutes} min, "
              f"window ${window_spend(led):.2f}/${HARD_CAP_DOLLARS:.2f})")
        return

    # ── STONE RULE 1: no run without his words ───────────────────────────────────────────
    if not args.approval.strip():
        print("GEAR 3 REFUSED: no --approval given. Gear 3 never runs without the "
              "curator's explicit approval for this specific use.")
        sys.exit(2)
    if not args.cmd or not args.produces:
        print("gear3 run needs --cmd and --produces")
        sys.exit(2)

    # ── STONE RULE 2: the $10 window, checked AND reserved under the ledger lock so
    # parallel package chains cannot each pass the ceiling before the other's spend lands.
    # The estimate is written as the entry's cost at launch (conservative) and corrected to
    # the measured figure at completion.
    _lock_ledger()
    try:
        led = load_ledger()
        if window_spend(led) + est > HARD_CAP_DOLLARS:
            if not args.cap_approval.strip():
                _unlock_ledger()
                refuse_over_cap(led, est, args)
            led["cap_approvals"].append({"ts": time.time(), "text": args.cap_approval,
                                         "amount_at_approval": round(window_spend(led) + est, 2)})
        t0 = time.time()
        led["runs"].append({"ts": t0, "cmd": args.cmd, "gpu": args.gpu,
                            "est_dollars": est, "duration_s": None,
                            "est_actual_dollars": est, "approval": args.approval,
                            "returncode": None, "status": "LAUNCHED"})
        save_ledger(led)
    finally:
        _unlock_ledger()

    # ── the cloud call ───────────────────────────────────────────────────────────────────
    import modal                                                      # noqa: PLC0415

    timeout_s = int((args.timeout_minutes or args.est_minutes * 3) * 60)
    # serialized functions require the image's python minor to match the local interpreter
    image = (modal.Image.debian_slim(python_version="3.13")
             .uv_pip_install("torch", "transformers", "scikit-learn", "numpy")
             .add_local_dir(str(REPO / "runners"), "/repo/runners")
             .add_local_dir(str(REPO / "soundingline"), "/repo/soundingline"))
    vol = modal.Volume.from_name("sounding-line-corpora", create_if_missing=True)
    app = modal.App("sounding-line-gear3")

    @app.function(image=image, gpu=args.gpu, timeout=timeout_s,
                  volumes={"/vol": vol}, serialized=True)
    def run_stage(cmd: str, produces: str, tmo: int) -> dict:
        import shlex as _shlex
        import subprocess
        import zipfile
        from pathlib import Path as _P
        # data ships as zips on the volume (thousands of small files transfer poorly);
        # unpack container-locally where the runners expect each tree
        for zname, dest in (("pan_style.zip", "/repo/corpora/public/pan_style"),
                            ("pan25_channels.zip", "/repo/results/pan25_channels")):
            zp, dp = _P("/vol") / zname, _P(dest)
            if zp.exists() and not dp.exists():
                dp.mkdir(parents=True)
                zipfile.ZipFile(zp).extractall(dp)
        r = subprocess.run(["python"] + _shlex.split(cmd), cwd="/repo",
                           capture_output=True, text=True, timeout=tmo)
        out = {"returncode": r.returncode, "stdout_tail": r.stdout[-4000:],
               "stderr_tail": r.stderr[-4000:]}
        p = _P("/repo") / produces
        if p.exists():
            out["produced"] = p.read_text(encoding="utf-8")
        return out

    print(f"[gear3] launching {args.gpu} (~{args.est_minutes} min, est ${est:.2f}) "
          f"under approval: {args.approval!r}", flush=True)
    with modal.enable_output(), app.run():
        result = run_stage.remote(args.cmd, args.produces, timeout_s - 60)
    dur = time.time() - t0
    actual = round(RATES[args.gpu] * (dur / 3600.0) * 1.05, 2)

    _lock_ledger()
    try:
        led = load_ledger()                       # reload under the lock: parallel chains
        mine = next(r for r in led["runs"] if r["ts"] == t0)
        mine.update({"duration_s": round(dur, 1), "est_actual_dollars": actual,
                     "returncode": result["returncode"], "status": "DONE"})
        save_ledger(led)
    finally:
        _unlock_ledger()

    dest = REPO / args.produces
    if "produced" in result:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(result["produced"], encoding="utf-8", newline="\n")
        print(f"[gear3] wrote {args.produces} ({dur / 60:.1f} min, ~${actual:.2f}; "
              f"window ${window_spend(led):.2f}/${HARD_CAP_DOLLARS:.2f})")
    else:
        print(f"[gear3] NO PRODUCE (exit {result['returncode']}, {dur / 60:.1f} min, "
              f"~${actual:.2f}). stderr tail:\n{result['stderr_tail'][-2000:]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
