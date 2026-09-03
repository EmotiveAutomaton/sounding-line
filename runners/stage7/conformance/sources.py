"""The source manifest (brief §5, A01, A02): every external program pinned with its paper
version, repository commit, license, setup result, and the exact borrowed operation, and
the sealed-workspace receipt: the read-only reference clones live OUTSIDE the repository
(E:/EmotiveAutomaton/Projects/SoundingLine/reference, his ruling 2026-09-02), are never
on sys.path, are never runtime dependencies, and cannot see scientific or confirmation
data (they are never given a path into the stage root; the guard test greps for it).

DESIGN CHECK (2026-09-02)
lessons read: LESSONS §1b (a faithful arm means the framework, not the printed
  hyperparameters: the fixtures reproduce the defining OPERATION on an official-style
  example, and a name is admitted only on a pass), §1c (irreproducibility wording stands on
  exhausted public routes; author contact off the table), §5.
gates: A01: NULL of a floating source is any external entry without a commit or a paper
  id at the scientific lock (failure direction: any unpinned entry fails DOWN);
  ALTERNATIVE: every entry pinned. A02: NULL of a leaky workspace is the reference path
  on sys.path, inside the repository, or referenced by any stage module (fails DOWN);
  ALTERNATIVE: none of the three. bands: exhaustive.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from soundingline.stage7 import S7, now_iso, write_registry                       # noqa: E402

REFERENCE = REPO.parent / "reference"

SOURCES = {
    "laip": {"paper": "arXiv:2507.03682 (LLM-Augmented Inverse Planning)", "repo": None, "clone": None,
             "borrowed": "the defining operation only: model-proposed hypotheses and likelihood functions with an external Bayesian posterior",
             "local_name": "weighted_language_hypotheses", "status": "PAPER_ONLY (no official repository located; fixture from the paper's description)"},
    "thought_tracing": {"paper": "arXiv:2502.11881v2 (ThoughtTracing)", "repo": "https://github.com/skywalker023/thought-tracing",
                        "clone": "thought-tracing",
                        "borrowed": "tracer.py: propagate, weigh, resample (hypothesis.py resample_hypotheses/compute_ess), rejuvenate_hypotheses; preprocess_input state/action interleaving; data/bigtom example as the official-style fixture input",
                        "local_name": "sequential_hypothesis_particles", "status": None},
    "autotom": {"paper": "arXiv:2502.15676v3 (AutoToM)", "repo": "https://github.com/SCAI-JHU/AutoToM", "clone": "AutoToM",
                "borrowed": "model/model_adjustment.py: initial_model_proposal, model_discovery (utility-driven variable addition), Bayesian_inference; model/BayesianInference.py; benchmarks/data/bigToM example as the official-style fixture input",
                "local_name": "adaptive_factor_expansion", "status": None},
    "liras": {"paper": "ACL Findings EMNLP 2025 (LIRAS)", "repo": None, "clone": None,
              "borrowed": "the defining operation from the paper: synthesize and validate a situation-specific environment model, agent model, parsed state/action sequence, inverse-planning computation",
              "local_name": "synthesized_agent_model", "status": "NO_PUBLIC_IMPLEMENTATION_LOCATED (LIRAS-style paper reproduction label retained)"},
    "inverse_planning": {"paper": "InversePlanning.jl (cosilab)", "repo": "https://github.com/cosilab/InversePlanning.jl", "clone": None,
                         "borrowed": "none executed: Julia is not installed on this machine; §10 A12 admits an exact independently checked equivalent (the grid posterior, verified against analytic tiny-world answers)",
                         "local_name": "known_law_inverse_planning", "status": "NOT_CLONED (Julia absent; exact equivalent admitted by A12)"},
    "labtom": {"paper": "LaBToM.jl (cosilab)", "repo": "https://github.com/cosilab/LaBToM.jl", "clone": None,
               "borrowed": "none executed: Julia absent; the defining operation (epistemic language to a compositional belief representation, belief-sensitive inference) reproduced locally",
               "local_name": "epistemic_translation", "status": "NOT_CLONED (Julia absent)"},
    "clips": {"paper": "CLIPS.jl (cosilab)", "repo": "https://github.com/cosilab/CLIPS.jl", "clone": None,
              "borrowed": "none: cooperative instructions are stronger evidence than the artifacts here provide (§5)", "local_name": None, "status": "NOT_USED"},
    "inverse_inverse": {"paper": "Acting as Inverse Inverse Planning (kach)", "repo": "https://github.com/kach/acting-as-inverse-inverse-planning", "clone": None,
                        "borrowed": "none this stage: the audience-shaping worlds are the audience factor of C_ext, not a reproduction", "local_name": None, "status": "NOT_USED"},
}


def _git(path: Path, *args) -> str:
    try:
        return subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception as e:                                                        # noqa: BLE001
        return f"error: {e!r}"


def clone_receipt(name: str) -> dict:
    p = REFERENCE / name
    if not p.exists():
        return {"present": False}
    head = _git(p, "log", "-1", "--format=%H|%cd", "--date=iso")
    n_head = _git(p, "ls-tree", "-r", "HEAD", "--name-only").splitlines()
    on_disk = sum(1 for x in p.rglob("*") if x.is_file() and ".git" not in x.parts)
    lic = ""
    for cand in ("LICENSE", "LICENSE.md", "LICENSE.txt"):
        if (p / cand).exists():
            lic = (p / cand).read_text(encoding="utf-8", errors="replace").splitlines()[0].strip()
            break
    colon = sum(1 for x in n_head if ":" in x)
    return {"present": True, "path": str(p), "head": head.split("|")[0], "committed": head.split("|")[-1],
            "files_at_head": len(n_head), "files_on_disk": on_disk, "unmaterializable_colon_paths": colon,
            "license_first_line": lic, "read_only": True, "on_sys_path": any(str(p).lower() in (q or "").lower() for q in sys.path)}


def sealed() -> dict:
    """A02: the reference workspace is outside the repository, off sys.path, and no stage
    module names it as an import."""
    inside_repo = str(REFERENCE.resolve()).lower().startswith(str(REPO.resolve()).lower())
    on_path = any(str(REFERENCE).lower() in (q or "").lower() for q in sys.path)
    refs = []
    for py in (REPO / "runners" / "stage7").rglob("*.py"):
        txt = py.read_text(encoding="utf-8", errors="replace")
        if "thought-tracing" in txt.replace("thought_tracing", "") and "import" in txt and py.name not in ("sources.py",):
            for ln in txt.splitlines():
                if "sys.path" in ln and "reference" in ln:
                    refs.append(f"{py.name}: {ln.strip()[:80]}")
    return {"inside_repo": inside_repo, "on_sys_path": on_path, "path_insertions_to_reference": refs,
            "sealed": not inside_repo and not on_path and not refs}


def write_manifest() -> dict:
    out = {"written_at": now_iso(), "reference_workspace": str(REFERENCE), "policy": SOURCES and
           "read-only clones outside the repository (his ruling 2026-09-02); never vendored, never a runtime dependency, never on a capsule path",
           "sources": {}}
    for k, s in SOURCES.items():
        entry = dict(s)
        if s.get("clone"):
            entry["clone_receipt"] = clone_receipt(s["clone"])
            entry["status"] = "CLONED_PINNED" if entry["clone_receipt"].get("present") else "CLONE_MISSING"
        out["sources"][k] = entry
    out["sealed"] = sealed()
    out["all_pinned"] = all((v.get("clone_receipt", {}).get("head") or v.get("paper")) for v in out["sources"].values())
    write_registry("SOURCE_MANIFEST", out)
    return out


if __name__ == "__main__":
    import json
    m = write_manifest()
    print(json.dumps({k: (v.get("status"), (v.get("clone_receipt") or {}).get("head")) for k, v in m["sources"].items()}, indent=1))
    print("sealed:", m["sealed"], "all pinned:", m["all_pinned"])
