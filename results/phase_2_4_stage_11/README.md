# Stage 11: retrospective contribution

Complete September 18, 2026 (L390). The finite Gear 2 study contains two separately
scored tranches: 24 initial and 17 extension episodes, fourteen writers in total.
Contribution accounts show no consistent handling advantage; the training prior
beats all model and feature baselines on probability error. No new work is queued.

- [Final report and two discussion questions](FINAL_REPORT.md)
- [Full complete-cell score table](REPORT.md)
- [All-attempt and valid-only comparisons, paired spreads and costs](COMPARISONS.json)
- [Source, attempt and budget dispositions](INTEGRITY.json)
- [Independent replay and arithmetic checks](VERIFICATION.json)
- Private [reviewed six-case contribution map](raw/contribution-map-reviewed-v2.html)

The original computational packet and original viewer remain intact. The separate
operator audit covers 49 proposed operations. All twenty targeted tests and viewer
script checks pass; browser visual QA remains unperformed because no browser surface
is connected. No wholly deleted/unlocated insertion was available in the frozen
example pool. Exact text, source identities and raw attempts remain in ignored `raw/`.

Replay without model calls:

```powershell
./.venv/Scripts/python.exe -B -m runners.stage11.run report --verify
./.venv/Scripts/python.exe -B -m runners.stage11_packet
./.venv/Scripts/python.exe -B -m runners.stage11_review
./.venv/Scripts/python.exe -B -m runners.stage11_viewer_repair
```

The [commission](../../docs/design/PHASE_2_4_STAGE_11_CONTEXT.md) and
[runner contract](../../runners/stage11/README.md) preserve the frozen evidence
boundary, original clock and finite limits. Stage 9/10 sources and scores are unchanged.

Precommit validity repair (OPS-S11-REPAIR1): the original viewer could hide
unlocated reference hypotheses after a passage click. The versioned viewer above
fixes this, with all 184 case/view/passage checks passing. Forecasts, source evidence,
semantic audits and scientific scores are unchanged. `FINAL_RECEIPT.json` remains
the original pre-repair receipt; its exact bound files are preserved privately.
`PRECOMMIT_RECEIPT.json` records the subsequent repair and publication checks.
