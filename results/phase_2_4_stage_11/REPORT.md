# Stage 11: retrospective contribution comparison

Complete registered human-data tranches; descriptive evidence.

Question: does a bounded contribution account recover recorded suggestion handling better than direct reading of the same evidence?

The two evidence views and registered tranches remain separate. Writers are weighted equally after their episodes are averaged. Half multiclass Brier loss is probability error; lower is better. Accuracy selects the largest probability. Log loss is infinite when the observed outcome receives zero probability. Invalid forecasts retain Brier loss one and accuracy zero.

| Tranche | Evidence | Reader | Episodes | Writers | Components | Brier loss | Accuracy | Log loss | Invalids |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| initial | artifact | prior | 24 | 14 | 3 | 0.337035 | 0.428571 | 1.207723 | 0 |
| initial | artifact | features | 24 | 14 | 3 | 0.671841 | 0.142857 | 3.518075 | 0 |
| initial | artifact | direct | 24 | 14 | 3 | 0.407068 | 0.428571 | 1.562745 | 0 |
| initial | artifact | account | 24 | 14 | 3 | 0.413125 | 0.285714 | infinite | 0 |
| initial | alternatives | prior | 24 | 14 | 3 | 0.337035 | 0.428571 | 1.207723 | 0 |
| initial | alternatives | features | 24 | 14 | 3 | 0.549281 | 0.357143 | 2.807222 | 0 |
| initial | alternatives | direct | 24 | 14 | 3 | 0.448129 | 0.428571 | 1.787264 | 0 |
| initial | alternatives | account | 24 | 14 | 3 | 0.435536 | 0.321429 | infinite | 3 |
| extension | artifact | prior | 17 | 13 | 3 | 0.254659 | 0.730769 | 0.898874 | 0 |
| extension | artifact | features | 17 | 13 | 3 | 0.381920 | 0.423077 | 1.439705 | 0 |
| extension | artifact | direct | 17 | 13 | 3 | 0.337954 | 0.653846 | 1.247957 | 0 |
| extension | artifact | account | 17 | 13 | 3 | 0.329185 | 0.653846 | 1.212854 | 0 |
| extension | alternatives | prior | 17 | 13 | 3 | 0.254659 | 0.730769 | 0.898874 | 0 |
| extension | alternatives | features | 17 | 13 | 3 | 0.410301 | 0.461538 | 1.462952 | 0 |
| extension | alternatives | direct | 17 | 13 | 3 | 0.311669 | 0.653846 | 1.210543 | 0 |
| extension | alternatives | account | 17 | 13 | 3 | 0.422500 | 0.615385 | infinite | 1 |

The primary observed differences are contribution account minus direct Brier loss; negative favors the account.
- initial, artifact: +0.006057.
- initial, alternatives: -0.012593.
- extension, artifact: -0.008769.
- extension, alternatives: +0.110831.

These exposed records provide descriptive comparisons, not fresh human confirmation. Connected dependence components and observed writer/prompt spreads are in COMPARISONS.json; no population confidence interval is asserted. Handling accuracy does not validate the account’s goals, dependencies, review claims or values.

Retained requests: 204. Charged GPU service: 0.440 hours. Preparation, phase dispositions, tokens, latency, raw-response replay and caps are in INTEGRITY.json and COMPARISONS.json. All original failures remain private.

Local contribution viewer: `raw/contribution-map.html`. Its example-selection rule and missing case types are disclosed in the page. The operation audit is descriptive; unrecognized or unobservable claims remain unresolved. Visual browser QA remains pending if no connected browser is available.

Replay without model calls: `python -B -m runners.stage11.run report --verify`.
Build this packet: `python -B -m runners.stage11_packet`.

Scientific interpretation and the full theory/FINDINGS landing are a subsequent operator review.
