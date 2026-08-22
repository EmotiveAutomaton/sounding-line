"""G177 (Phase 2.4 root P24-H0) — natural human-process baselines: before any intervention,
which recorded human process facts are recoverable, at which interface, by which reader?

Three arms, interfaces never pooled (context §7.2):

  ANCHOR (artifact-only, positive control). The G159 realized-revision cases — the one
    bounded artifact-only positive the repository owns (0.86 direct-prompted against twins).
    The new conditional-likelihood reader scores the same candidate sets; this validates the
    Phase 2.4 instrument against a target known to carry signal before it reads anything new.
    The direct 0.86 belongs to a different reader and is a reference line, never a bar.

  SCHOLAWRITE (prospective). Leave-one-project-out ONLY (the shipped split leaks ~30 points,
    L82). At each edit the target is the NEXT annotated writing-intention class, future text
    withheld. The label is an annotation of writing intention, never verified mental state.
    Baselines: project-frequency (majority), previous-label Markov. Reader arm: the local
    instruct model over the label set, sampled per project. Macro-F1 with the label set FIXED
    (L108); per-project table, never a single pooled number.

  COAUTHOR (paired-delta / prospective import). Fetch and inventory the CoAuthor session
    logs; targets are objective actions only (suggestion accepted vs rejected; accepted
    unchanged vs edited; retained vs later removed). Token share is never a target. This arm
    is an import-and-map stage; its reading batteries are Stage-2 material.

DESIGN CHECK (2026-08-22, at design time). Lessons read: LESSONS §3 (known-answer before
signal; floors follow label marginals; fixed label sets in macro-F1; power before verdicts),
§4 (the L139 adjudicator rule — the reader arm is validated on a mechanically decidable
subset BEFORE its verdicts count), §5 (produces guards; retries with backoff on the local
endpoint; manifests withheld on thin yield). Gates, null/alternative/direction:

    ANCHOR KNOWN-ANSWER: the conditional reader's echo probe (own first sentence vs three
      foreign) at >= 0.90 before the anchor scores; failure DOWN = scorer broken here.
    ANCHOR SIGNAL: top-1 on the G159 candidate sets above the 0.25 candidate floor with a
      binomial p < 0.05. Null: the likelihood form reads nothing the prompted form read.
      Failure DOWN = the non-generative reader cannot see the known-positive target, and
      G176 may not use artifact-only targets through it (routing consequence, not repair).
    SW LEAK ASSERTION: no project id crosses a train/eval boundary (mechanical; any
      violation voids the arm — the L82 receipt).
    SW READER KNOWN-ANSWER (the L139 rule): on edits whose intention class is mechanically
      decidable (a citation-command token appears in the delta and the label is the
      citation class), the reader must score >= 0.80; below, the reader arm is
      INSTRUMENT-FAIL and only the mechanical baselines report.
    COAUTHOR FETCH: the import either lands with its inventory manifest or exits nonzero
      and retries; a thin or partial download never writes the manifest.

Verdict bands per arm, exhaustive:
    anchor:  READS (gate + signal) · BLIND (known-answer passes, signal at floor) ·
             INSTRUMENT-FAIL (known-answer fails)
    scholawrite: for each of reader/Markov/frequency, report macro-F1 per project;
             the arm's band is INTERFACE-MAPPED when all 5 released projects complete
             per arm, else INCOMPLETE (the release holds exactly five scholarly
             projects; this arm maps a boundary and has no positive/negative pole)
    coauthor: IMPORTED (manifest with >= 40 writers' sessions inventoried) · DEFERRED
             (fetch unreachable this pass)

No p-value here enters multiplicity-audit exempt: the anchor binomial and any quoted
scholawrite comparison land in runners/audit_multiplicity.py in the same pass they are
first quoted.
"""

from __future__ import annotations

SEED0 = 17700

ANCHOR_READER = "Qwen/Qwen2.5-1.5B"
ANCHOR_CONDITION = "This essay was written under the instruction: {cand}."
ANCHOR_FLOOR = 0.25
KNOWN_ANSWER_FLOOR = 0.90

SW_HUB_ID = "minnesotanlp/scholawrite"
SW_SAMPLE_PER_PROJECT = 120
SW_READER_MODEL = "qwen3.5:9b"
SW_CITATION_MARKERS = ("\\cite", "\\bibliography", "\\bibitem")
SW_READER_KA_FLOOR = 0.80

COAUTHOR_URLS = (
    "https://cs.stanford.edu/~minalee/zip/chi2022-coauthor-v1.0.zip",
    "https://coauthor.stanford.edu/downloads/chi2022-coauthor-v1.0.zip",
)
COAUTHOR_MIN_WRITERS = 40
