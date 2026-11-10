# LA IDEMPOTENT COMPLETION

**Hypothesis.** Can language-act scoring resume safely without changing completed values or losing the original measured cost?

**METHOD.** Run the actual causal double-precision and masked single-precision scorers with tiny constructed weights, interrupt both a partial act and completed execution before verification, continue from exact checkpoints, collect the original and successor versions together, test malformed provenance refusals and repeat the entire lifecycle in a fresh counted process. Authenticate every output, source pin and native exit.

**Found.** The language-act scorer preserves complete numeric and cost records through partial and completed reentry, and its constructed mixed-version collection independently replays.

The table reports software qualification on constructed inputs, not pretrained-reader performance or a human result.

| Check | Result |
|---|---|
| Partial act and completed-execution reentry | Both pass |
| Original versus successor numeric bytes | Exact equality |
| Original completed cost | Preserved; every new invocation separately charged |
| Mixed producer collection | Equals original collector |
| Unknown producer, missing pin and malformed cost | Refused |
| Measured native CPU / wall seconds | 38.343750 / 79.197033 |

All 163 terminal outputs authenticate, and the native owner and children have exited. Design commit 38251d3c2 precedes admission. The fixture uses only the already completed constructed AT collection; internal dependency envelopes are explicitly constructed, not claims of production-native admission. The 600-CPU-second, 900-wall-second, three-GiB, two-thread bounds were retained, with the standard 30-second supervisor charge. Existing causal and masked numerical conventions and tolerances did not change.

**Means.** This narrow reentry and collection gap is qualified. Human language-act work still requires a complete corrected reader bank, selected-reader dependencies, measured costs and memory admission. Old failed evidence and numerical sources remain preserved. No scientific claim, p-value, GPU, Ollama or paid call is introduced.
