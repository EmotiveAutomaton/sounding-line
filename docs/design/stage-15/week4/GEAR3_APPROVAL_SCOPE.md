# Week 4 paid campaign approval scope

Prepared request for `G3-S15-WEEK4`; no paid call is authorized by this file alone. Destination for every node is Anthropic's Message Batches API (`api.anthropic.com`), using the existing commissioned Haiku reader with thinking disabled. Raw text is limited to the payload column; no participant identities or per-person profiles are sent. Only aggregate outputs leave through repository reporting.

| Node | Payload sent | Admission rung | Gross node cap |
|---|---|---|---:|
| PROC | CoAuthor final-document sentences and their preceding document context | 100 blind agent labels; agreement at least 0.6 and format floor | $2.00 |
| PLAN | Qualifying sessions' text up to midpoint and later offered option texts | Format on 100 sessions; 100 blind option/plan ratings, collapsed three-level agreement at least 0.6 | $1.50 |
| DRIVE | Writer-typed CoAuthor sentences and their preceding sentence | 100 blind agent labels; pooled agreement at least 0.6, category diagnostics | $1.50 |
| PLANT | Frozen 12-goal library and genre prompts; no source text | Format; at least 45 of 50 blind-checked pieces must not state the hidden goal outright | $0.50 |
| REV | CoAuthor final documents and the 600 PLANT pieces | Format; substantive accuracy is the research outcome | $0.50 |
| VAL | Week3 frozen Community Alignment explanations, up to 10 per annotator, restricted to CA1.s1 including the approved 836 subset | 100 blind agent labels; pooled agreement at least 0.6, category diagnostics | $2.00 |
| AUTH | Pairs of writer-typed texts, at most 400 words each | AUC at least 0.6 on 100 argument pairs; these pairs excluded from primary | $1.00 |

For every node: one recorded prompt correction and one fresh 100-item rerun are included within the same cap; a second failed rung stops the node. Constrained output is required; the stated format floor is 98 of 100, with malformed responses retained and never interpreted as labels. PLANT's blind non-disclosure check remains 50 pieces. PLAN and DRIVE main batches also require their local source-support checks. No automatic resubmission after uncertain delivery. Inputs are deduplicated; every POST is reserved before submission; prior-node billing is reconciled before the next node.

Caps sum to $9, with a separate hard $10 gross campaign ceiling; forecast about $4.25. Dispatch closes November 6 at 17:00 PST. This approval covers only section5's nodes, listed text transfers, calibration, main runs, and one prompt-fix rerun per node. It does not authorize new providers, identities/profiles, GPU jobs, extra nodes or a higher cap. The original Week3 approval and ledger remain unchanged.
