# ARGREWRITE LOCAL INVENTORY 20261107

**Hypothesis.** Does the local ArgRewrite V.2 material include writers' own pre-study survey responses, or only drafts and revision annotations?

**METHOD.** Enumerate every local file, compare all extracted bytes with the retained ZIP, read the corpus and annotation guides, and inspect questionnaire labels and aggregate nonblank-response counts without reporting response values or participant identifiers. Correct only the ArgRewrite entry in the public corpus manifest; retain other datasets and historical failed candidate lookups unchanged.

**Found.** ArgRewrite V.2 is available locally, including the writers’ pre-study survey and revision-goal self-reports; the manifest’s unavailable status was stale.

The table lists local source files by their generic relative paths under `corpora/public/argrewrite/`. Counts are files, except where response rows are explicitly identified. The complete per-file inventory remains private and is linked in the curator reply.

| Material | Relative path | Count |
|---|---|---:|
| Original archive | `ArgRewrite.V2.zip` | 1 |
| Corpus guide | `readme.txt` | 1 |
| Essay drafts | `essays/Draft1/*.txt`, `essays/Draft2/*.txt`, `essays/Draft3/*.txt` | 86 each; 258 total |
| Revision annotation workbooks | `annotations/**/*.xlsx`, excluding names starting `~$` | 172 |
| Excel temporary lock file | `annotations/**/~$*.xlsx` | 1; excluded from analysis |
| Annotation guide | `annotations/readme.txt` | 1 |
| Writers' pre-study survey | `meta-data/Surveys/Pre_Study.csv` | 1; 86 response rows |
| Writers' post-study surveys | `meta-data/Surveys/Post_Study_A.csv` through `Post_Study_D.csv` | 4; 20/22/22/22 response rows |
| Expert feedback | `meta-data/ExpertFeedback/*.docx` | 86 |
| Revision-verification logs | `meta-data/RevisionVerification/**/*.txt` | 109 |
| Draft scores | `meta-data/Scores/scores.xlsx` | 1 |

**Survey content and scope.** The source guide explicitly describes the surveys as students' own responses. The pre-study questionnaire includes a goal-setting habit item (Q26: 86 nonblank responses), a content/thesis-goal item (Q27: 43), and a surface-change-goal item (Q28: 42). These are self-reports of typical revision habits, not the annotation workbook's revision-purpose labels. Their presence does not establish a per-draft intention or initiator label. The free-response item's stored label (Q38) only refers to Step 2, so no additional goal semantics are inferred from that label. Each survey has a questionnaire-label record after its CSV header; the response counts above exclude it. Missing item responses are retained, not filled or inferred.

**Integrity and manifest correction.** The 4,630,133-byte archive has SHA-256 `5b4e97225cc2a1480326c134a38ea570c9cf354cb04753efa61c2e589b6153e7`. All 634 extracted members match their source bytes; the total local inventory is 635 files including the ZIP. The apparent extra annotation workbook is an Excel temporary lock file, leaving the source guide's 172 data workbooks. `corpora/public/MANIFEST.json` now records status `ok`, version, local paths, archive hash, grouped counts, survey presence and explicit scope limits. Its Wikipedia and RAID entries are unchanged. Historical unsuccessful Hugging Face candidates remain as history; their failure did not describe this local archive. No original data were altered or refetched.

**Means.** Use the verified local inventory, exclude the Excel lock file and questionnaire-label rows, and validate licensing, joins and the intended goal construct before any B3 scientific use. Availability is established; licensing and study-specific scientific admission remain separate. No new tests were harvested, no participant response or identifier is copied into public output, and no research execution, paid call, staging, commit, push or watcher ACK was performed.
