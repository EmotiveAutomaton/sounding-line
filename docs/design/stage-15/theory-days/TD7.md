# TD7: frozen implementation note

DESIGN CHECK: LESSONS 1a-1c and 2-5; CONTROLS 6-7.
Under the null the control must retain zero; under the specified alternative it
must recover the registered direction. Invalid controls or missing support stop
scientific interpretation. The inconclusive band includes every case not admitted
by a passing control and an explicit support or against rule.

Practical bar: zero, as specified by the signed packet contrast; report effect intervals in standardized feature units. Unsupported writer/event counts stop before modeling.

[Review amendments](REVIEW.md) and [source intake](DATA_INTAKE.md) bind this
implementation alongside the unchanged supplied specification below. All draws
use seed 20261106 unless the packet explicitly retains a prior frozen sample.
Scientific execution must pin a Git commit containing this note. This design
records planned work, not completed validation or results.

### TD7. After rejecting an offer she has examined, does she stop weighing the source? (C10's function, on our records)

This tests the function the curator assigns to DISGUST, not the channel itself.
- **Data.** CoAuthor's canonical menus with option features and her state, from `runners/drive/cards/`: `week4_t4_menus_v2.py` (handling, open and resolution times), `week4_t4_history.py`, `week4_t4_encoding.py` and `week4_t4_inputs.py`; suggestion-hover events from `week4_s4_menu_source.py` (an opening or reopening snapshot is not a hover).
- **Model code.** `week4_t4_kernel_h1.py` and `week4_t4_choice.py` accept exactly five option features and two state terms, so the arm terms need a new versioned kernel. Check it against `week4_t4_choice.py` with the arm terms at zero, and against finite differences on the new terms, before any human fit.
- **Arms**, within writer:
  - after an examined dismissal: her upper tercile of open time (terciles over all her opened menus), or a suggestion-hover event while the menu was open;
  - after an examined acceptance, matched on open-time tercile and session-time decile;
  - fast dismissals reported separately.
- **Primary.** Over her next 3 opened menus with a canonical choice in the same session (ignored menus skipped; a menu inside two windows goes to the earlier event): how sensitive her choices are to option fit. One pooled conditional logit on these menus holds T4's five option features, writer-specific dismissal constants, and three arm terms (examined dismissal against examined acceptance): times cosine to her own history, times fit to the preceding sentence, and times the dismissal alternative. The primary is the mean of the two feature-by-arm coefficients, with features standardised on these menus, and a 2,000-resample writer-cluster interval; each coefficient is reported beside it. The controls enter as interactions with the dismissal alternative and with both fit features.
  - C10's function predicts flatter sensitivity after examined dismissals.
  - The rival, value learning, predicts a higher dismissal constant with sensitivity unchanged.
- **Outcomes.**
  - **Supports:** the primary's interval lies below zero.
  - **Against:** the interval lies at or above zero while the arm's dismissal term has an interval above zero.
  - **Inconclusive:** anything else.
- **Controls.** Characters typed between menus; time since the event; session-time decile.
- **Case check (amendment F).** At least 20 writers, each with at least 10 examined dismissals and 10 matched acceptances followed by 3 qualifying menus, as the primary defines them.
- **Pre-mortem.** Regression to the mean on open time (handled by matching); fatigue; general disengagement, which this design can't tell from closing a model. 14,285 of 16,855 opened menus carry a suggestion-hover event (S4(b)'s census), so the hover clause may make most dismissals examined: report how many qualify by each clause, and the primary with the open-time clause alone. After an acceptance the preceding sentence can be the accepted offer, which shifts the fit-to-sentence feature by arm: report each arm's share of post-event menus whose preceding sentence is writer-typed (R2's tags), and the primary on those menus.
- **Ceiling:** 3 CPU-hours. Past twice that, use the frozen 25-writer sample.
