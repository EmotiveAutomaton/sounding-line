"""G159 echo decomposition — the follow-on L146 made mandatory: split the P+ recovery
into echo-consistent and echo-independent evidence, on the recorded arm data.

For every P+ event: the echo pick is the candidate with maximum content-word overlap.
Events where the echo pick IS the truth cannot distinguish reading from word-matching;
events where the echo pick is WRONG are the decisive subset — reader accuracy there is
recovery that word overlap cannot explain.

DESIGN CHECK (2026-08-20, at design time). Lessons read: LESSONS §3; CONTROLS 6/7.
Exploratory decomposition of a landed result, no verdict bands, nothing VOIDs, no new
reader calls (pure re-scoring of recorded picks). Expectations both ways: under the
words-only account of L146's 0.86, reader accuracy on the echo-wrong subset falls to
chance (0.25); under genuine semantic reading it stays above. Reported beside the twin
baseline on the same split. Failure direction of the instrument: the echo-wrong subset
is small and composition-biased (events where execution left weak lexical trace), so
its n is reported and cells under 15 are labeled thin.

Output: results/g159/echo_decomp.json. CPU seconds.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "runners"))
from run_g159_recovery import (load_arts, content_words, echo_score, MANIFEST,  # noqa: E402
                               OUT)


def main() -> None:
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    arts = load_arts()
    rows = {a: [json.loads(x) for x in
                (OUT / f"{a}_partial.jsonl").read_text(encoding="utf-8").splitlines()]
            for a in ("p_plus", "p_minus")}

    def decomp(arm):
        events = man[arm]
        out = {"echo_right": {"n": 0, "hit": 0}, "echo_wrong": {"n": 0, "hit": 0}}
        for r in rows[arm]:
            if r["pick"] is None:
                continue
            e = events[r["i"]]
            tw = content_words(arts[(e["family"], e["artifact_id"])]["text"])
            scores = [echo_score(c, tw) for c in e["cands"]]
            echo_pick = scores.index(max(scores))
            cell = "echo_right" if echo_pick == e["truth_idx"] else "echo_wrong"
            out[cell]["n"] += 1
            out[cell]["hit"] += int(r["pick"] == r["truth_idx"])
        for c in out.values():
            c["accuracy"] = round(c["hit"] / max(c["n"], 1), 4)
            c["thin"] = c["n"] < 15
        return out

    res = {"prereg": "runner docstring DESIGN CHECK (exploratory decomposition)",
           "p_plus": decomp("p_plus"), "p_minus_baseline": decomp("p_minus"),
           "reading": "echo_wrong accuracy is recovery word overlap cannot explain; "
                      "chance 0.25"}
    (OUT / "echo_decomp.json").write_text(json.dumps(res, indent=1),
                                          encoding="utf-8", newline="\n")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
