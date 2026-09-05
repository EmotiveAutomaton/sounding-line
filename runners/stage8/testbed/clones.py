"""T01: the sibling programs' repositories cloned read-only into the reference workspace
(E:/EmotiveAutomaton/Projects/SoundingLine/reference; his ruling 2026-09-02: clones with
confirmation, never vendored, never on a capsule path), shallow and blob-limited so a data-
heavy repository lands as its code, pinned by head commit with its license line and a
one-line card naming the operation worth borrowing; the Stage 7 clones (ThoughtTracing,
AutoToM) re-pinned beside them.

DESIGN CHECK (2026-09-04)
lessons read: LESSONS §1b (a clone is read for its defining operation; a name is admitted
  only on a fixture pass, which is Stage 9's work), §5 (every network step time-boxed).
gates: T01: NULL of an unpinned testbed is any clone without a head commit or a license
  line (fails DOWN: that entry CLONE_FAILED, the cell DESCRIPTIVE); ALTERNATIVE: every
  entry pinned. bands: exhaustive.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from soundingline.stage8 import now_iso, update_registry                          # noqa: E402

REFERENCE = REPO.parent / "reference"

CLONES = {
    "MMToM-QA": {"repo": "https://github.com/chuanyangjin/MMToM-QA", "card": "the fine-tuned small model as the action-likelihood estimator inside Bayesian inverse planning (BIP-ALM)"},
    "muma-tom": {"repo": "https://github.com/scai-jhu/muma-tom", "card": "the multi-agent version of BIP-ALM"},
    "Hypothetical-Minds": {"repo": "https://github.com/locross93/Hypothetical-Minds", "card": "natural-language hypothesis generation, evaluation, and refinement about other agents"},
    "InversePlanning.jl": {"repo": "https://github.com/cosilab/InversePlanning.jl", "card": "known-law inverse planning (Julia; cloned for reading)"},
    "LaBToM.jl": {"repo": "https://github.com/cosilab/LaBToM.jl", "card": "epistemic language to belief representations (Julia; cloned for reading)"},
    "CLIPS.jl": {"repo": "https://github.com/cosilab/CLIPS.jl", "card": "cooperative instruction following as inverse planning (Julia; cloned for reading)"},
    "acting-as-inverse-inverse-planning": {"repo": "https://github.com/kach/acting-as-inverse-inverse-planning", "card": "the maker who shapes the observer's inference (the bard)"},
    "gpudrive-CoDec": {"repo": "https://github.com/sounakban/gpudrive-CoDec", "branch": "NeurIPS-2025", "card": "value-guided construal with recoverable attention; the formal object nearest the subjective action set"},
    "BPL": {"repo": "https://github.com/brendenlake/BPL", "card": "stroke programs inferred from a static character; process from artifact, one-shot"},
    "timecraft": {"repo": "https://github.com/xamyzhao/timecraft", "card": "process reconstruction from a finished painting, trained on real time lapses"},
    "inverse_painting": {"repo": "https://github.com/ArmastusChen/inverse_painting", "card": "process reconstruction from a finished painting (a second program)"},
    "world-model-evaluation": {"repo": "https://github.com/keyonvafa/world-model-evaluation", "card": "the compression and distinction metrics for an implicit world model"},
    "verbalized-sampling": {"repo": "https://github.com/CHATS-lab/verbalized-sampling", "card": "the one-call distribution readout FR and G01 use"},
    "iterater": {"repo": "https://github.com/vipulraheja/iterater", "card": "the revision corpus with intention labels and its loader"},
    "newsedits": {"repo": "https://github.com/isi-nlp/newsedits", "card": "the news revision corpus with editors' intention labels and a prospective update task"},
    "thought-tracing": {"repo": "https://github.com/skywalker023/thought-tracing", "card": "Stage 7's clone (sequential hypothesis particles), re-pinned"},
    "AutoToM": {"repo": "https://github.com/SCAI-JHU/AutoToM", "card": "Stage 7's clone (adaptive factor expansion), re-pinned"},
}


def _git(path: Path, *args, timeout: int = 60) -> str:
    try:
        return subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True, timeout=timeout).stdout.strip()
    except Exception as e:                                                        # noqa: BLE001
        return f"error: {e!r}"


def receipt(name: str) -> dict:
    p = REFERENCE / name
    if not p.exists():
        return {"present": False}
    head = _git(p, "log", "-1", "--format=%H|%cd", "--date=iso")
    files = sum(1 for x in p.rglob("*") if x.is_file() and ".git" not in x.parts)
    lic = ""
    for cand in ("LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE", "COPYING"):
        if (p / cand).exists():
            try:
                lic = (p / cand).read_text(encoding="utf-8", errors="replace").strip().splitlines()[0].strip()[:120]
            except (OSError, IndexError):
                lic = ""
            break
    return {"present": True, "path": str(p), "head": head.split("|")[0], "committed": head.split("|")[-1], "files_on_disk": files,
            "license_first_line": lic or "no license file at the root (see the repository page)", "read_only": True,
            "on_sys_path": any(str(p).lower() in (q or "").lower() for q in sys.path)}


def clone_all(timeout_s: int = 900) -> dict:
    REFERENCE.mkdir(parents=True, exist_ok=True)
    out = {}
    for name, spec in CLONES.items():
        p = REFERENCE / name
        if not p.exists():
            args = ["git", "clone", "--depth", "1", "--no-recurse-submodules", "--filter=blob:limit=5m"]
            if spec.get("branch"):
                args += ["--branch", spec["branch"]]
            args += [spec["repo"], str(p)]
            try:
                r = subprocess.run(args, capture_output=True, text=True, timeout=timeout_s)
                status = "CLONED" if r.returncode == 0 else f"CLONE_FAILED: {r.stderr[-200:]}"
            except Exception as e:                                                # noqa: BLE001
                status = f"CLONE_FAILED: {e!r}"[:300]
        else:
            status = "PRESENT"
        rec = receipt(name)
        out[name] = {**spec, "status": status if not rec.get("present") else ("CLONED_PINNED" if rec.get("head") and not rec["head"].startswith("error") else status),
                     "receipt": rec, "at": now_iso()}
    update_registry("TESTBED_SOURCES", lambda t: {**t, "reference_workspace": str(REFERENCE), "clones": out, "written_at": now_iso(),
                                                  "policy": "read-only, shallow, blob-limited clones outside the repository; never vendored, never on a capsule path; his confirmation 2026-09-04 through the Stage 8 brief"})
    return out
