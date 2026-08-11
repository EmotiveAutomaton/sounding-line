# BST 2009 reference data, digitized from the paper's vector figures

Human judgment means and best-fit model predictions for Baker, Saxe & Tenenbaum (2009),
"Action understanding as inverse planning", *Cognition* 113(3), recovered 2026-08-11 by a
research subagent from the publisher PDF's vector graphics (every figure is pure vector; the
scatter markers are zero-length dot paths whose coordinates decode to data units).

Files: `SL_BST2009_exp1_from_fig5.csv` (300 rows, 100 stimuli × 3 goals, includes the
targeted-analysis flag), `SL_BST2009_exp2_from_fig8.csv` (285 rows), `SL_BST2009_exp3_from_fig10.csv`
(32 rows, human side complete). `sl_*.py` are the extraction scripts, kept for provenance;
`sl_fig*.json` are the raw decoded marker sets.

Validation, three independent checks plus one local re-check: recomputed Pearson r per panel
reproduces every printed correlation to two decimals (e.g. Exp 1: .8271/.9780/.9424/.9658
against printed .83/.98/.94/.97); consecutive rating triples sum to 1.000, matching the
paper's per-stimulus normalization; human coordinates are identical across panels to 5e-5.
Known caveats from the source paper itself: the text says 99 Exp-1 stimuli while the figure
plots 100 distinct triples; Fig 5 and Fig 6f disagree on M3's beta (2.5 vs 2.0).

The exact fitting procedure (grids, BSCV bootstrap, Exp-3 z-score pipeline) is recorded in
FINDINGS L78 and the TODO recreation row.
