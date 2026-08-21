"""Pre-registration for G167-A5 — the evidence-conflict test, the Wing A root's single
predeclared follow-up (prereg/g167.py, PROJECTION at L155), frozen before any arm runs.

THE QUESTION (design brief A5). L155 showed a false production fact steers this reader
as hard as a true one — on a substrate where L154 showed the artifact evidence is
unreadable, so suggestion met no resistance. The honest remaining question: can a false
note override artifact evidence the reader PROVABLY reads? The realized-choice events
are that substrate: direct instruction recovery at 0.86 (L146), echo-independent
(L148). If evidence holds there, context-following is bounded suggestibility that real
evidence defeats; if the note wins there too, supplied context is an unconditional
override channel and every context-bearing interface in the program must quarantine it.

SUBSTRATE. The frozen G159 manifest's 100 P+ events (verified executed instructions,
echo-matched decoys), recorded direct arm 0.86 as the anchor and no-note baseline.

ARMS (GPU, 100 events each):
  TN true note: "An unverified production note claims the applied instruction was:
     '<the truth>'" above the standard forced choice. Null expectation: accuracy at
     or above 0.86 (agreement costs nothing).
  FN false note: the same note naming a SEEDED DECOY from the event's candidate set.
     The primary arm.
  FF false note with a conflict flag: the FN prompt plus one added option, "the note
     does not match the essay". Measures whether the reader can NAME the conflict
     when the format permits, separately from resisting it in forced choice.

DESIGN CHECK (2026-08-21)
lessons read: LESSONS §3 (ruler-first — the anchor is the recorded 0.86; the
criterion can fail in both directions and the bands are exhaustive; the format-is-
the-instrument lesson from L143/L139 is why FF exists as its own arm), §5 (produces
guards, gpu lock once, append-at-end, retries).
gates:
  ANCHOR: recorded p_plus at 0.86/100 readable, else abort (wiring).
  TN sanity: null >= 0.80 (true note plus readable evidence should not HURT; below
    0.80 the note format itself damages reading, direction DOWN, and FN is read
    against TN instead of 0.86, disclosed).
  PIPELINE PURITY: prompts byte-pure in (essay, note text, candidates); permuted
    hidden fields leave hashes fixed; runs first, CPU.
primary: FN accuracy on the true instruction (not the note's decoy), against the
  recorded 0.86.
bands, exhaustive:
  EVIDENCE-HOLDS  FN >= 0.70 (the note costs at most ~16 points against evidence)
  SUGGESTIBLE     FN <= 0.40 (the note overrides evidence the reader provably reads)
  MIXED           everything between, stated as partial override with the number
secondary, reported never banded: note-following rate in FN (picks == the decoy the
  note named); FF conflict-flag rates under false vs true notes (a reader that flags
  conflicts under FN and not TN discriminates conflict even if forced choice bends).

RESPONSES, recorded now. EVIDENCE-HOLDS: context-following is bounded suggestibility;
Wing A pauses with the W3 row qualified (projection where evidence is absent, evidence
wins where present) and the wing's product guidance is "context permitted only beside
readable evidence". SUGGESTIBLE: supplied context is an unconditional override; the
wing pauses with context quarantined from every reader interface pending redesign,
stated without softening. MIXED: the wing pauses with the measured trade curve as the
record; no third arm, no prompt search. In every branch the wing PAUSES after this
card per the brief's W3 routing — the pause is the response, and lifting it is a
curator decision at the root map.

Seed 16750 (decoy draw per event: the echo-matched decoy with index seeded); reader
qwen3.5:9b at temperature 0; every statistic on disk; sha256 of this card in the
landing entry.
"""

from __future__ import annotations

CARD = {
    "id": "G167-A5",
    "parent": "G167 (prereg/g167.py), the predeclared evidence-conflict follow-up",
    "phase": "2.3 Wing A, terminal follow-up before the pause",
    "theory_group": "Reader Heuristics",
    "written_before_run": True,
    "seed": 16750,
    "substrate": "results/g159/manifest.json P+ events; recorded direct 0.86 anchor",
    "primary": "false-note accuracy on the TRUE instruction vs the recorded 0.86",
    "bands": {"EVIDENCE-HOLDS": ">= 0.70", "SUGGESTIBLE": "<= 0.40",
              "MIXED": "between, stated with the number"},
    "gates": ["pipeline_purity_first", "anchor 0.86/100", "true-note sanity >= 0.80"],
    "interfaces": {"all arms": "I1 plus a declared (untrusted) production note"},
}
