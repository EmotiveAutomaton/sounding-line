# E24-S3-H08 · Human-reader protocol (PREPARE ONLY — no recruitment, no execution)

**Status: prepared 2026-08-24. This document is the deliverable. Nothing here runs without
the curator's explicit authorization of recruitment, consent materials, and spend.**

## The question a human arm would answer

Every Stage-3 reader result (record-route accuracy, late-fusion updating, source
weighting, sycophancy) is measured on model readers against exact Bayesian ceilings. The
human arm asks: where do PEOPLE sit on the same rulers? The environment was built so the
same items run unchanged: scenarios are plain civic/workplace decisions, options are
plain sentences, ground truth is exact.

## Design (frozen while prepare-only)

- **Materials.** The Stage-3 decision environment verbatim: 24 scenarios × 2 domains,
  four options each. Item banks drawn by the same seeds as E02/C01/C02/C06 so every human
  cell has a model-reader twin and an exact-posterior ceiling.
- **Tasks (within-subject, 30-40 minutes).**
  1. Record route (the E02 twin): 8-choice record → predict the next choice. 12 items.
  2. Late fusion (the C01 twin): 6 consistent + {0, 2, 8} conflicting records → predict;
     HOLD and FLIP items balanced. 12 items.
  3. Source reliability (the C02 twin): verified-correct vs verified-wrong archives →
     predict from conflicting fresh reports. 8 items.
  4. Hope hint (the C06 twin): the experimenter's stated hope agrees/conflicts with the
     record. 8 items. Debriefed as a social-influence measure.
- **Readout.** Forced choice among the four options (click), so realization is exact.
  Confidence 1-5 per item. No free text needed for the primary analysis.
- **n and power.** 40 participants gives 480 record-route decisions; at the model arm's
  observed effect (record 0.42 vs nothing 0.23) a sign test per participant is over 0.95
  power; the interesting comparisons (human vs exact ceiling, human vs Qwen) are
  estimation, not testing.
- **Recruitment.** Prolific, adult, English-fluent; standard hourly-equivalent pay.
  REQUIRES: curator spend approval (Standing Ruling 7 applies), consent text sign-off,
  and a decision on whether IRB-equivalent review is wanted for publication.
- **Exclusions (pre-registered).** Completion under 8 minutes; failure of both catch
  trials (one dominant-option item per half, where every profile agrees).

## What is already done vs owed

| ready now | owed before launch |
|---|---|
| item banks (same seeds as the model cells) | consent + information sheet text |
| exact posteriors per item (the ceilings) | curator spend approval |
| model-reader twins for every cell | platform setup and pilot pass (n=4) |
| analysis plan (this section) | IRB-equivalence decision |

## Analysis plan (frozen)

Per task: human accuracy vs the exact ceiling and vs each model reader, per cell, with
participant-level sign-flip permutation. The headline table is a three-row ruler per task:
exact ceiling / humans / best model reader. The sycophancy cell reports hint-following
rate beside the model readers' rates. No aggregate "human score" — the reading is a
tuple, deliberately, as everywhere in this project.
