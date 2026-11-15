# RW1 source intake and marker candidate

Status: source/terms review and constructed marker components prepared. The new
source/annotation wrapper and fixtures are prepared for owner review but untested.
The exact pre-existing author release has been copied locally with owner approval.
No network body download, annotation study, human outcome, native admission or author contact.
Authority is [the supplied packet](PACKET.md), sections 2 AB and 3F. The owner's
[execution addendum](EXECUTION_ADDENDUM.md) governs the 20,000 CPU-second ceiling
and campaign clock.

## Source record, checked 15 November 2026

The [authors' repository](https://github.com/ben-aaron188/covid19worry) identifies
itself as the source of the Real World Worry datasets and variable descriptions.
The fetched current revision is `7324d50869578589a47781bc1d26123ca48e27c8`.
Only repository/project metadata, README and LICENSE bytes were fetched over the network. The complete
recursive tree response was not truncated. Its only README/license/terms paths
were the root README and LICENSE; dataset paths were inventoried without reading
their contents. No demographic columns or participant records were imported.

This table records exact source-byte pins, not participant-data authentication.

| File at that revision | Bytes | SHA-256 |
|---|---:|---|
| README.md | 6,598 | `2fd310e4c1e0a6dc51617e032d906cbc03fa355030223698e8e391a535ba3b26` |
| LICENSE | 35,149 | `3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986` |

The [root LICENSE at the pinned revision](https://github.com/ben-aaron188/covid19worry/blob/7324d50869578589a47781bc1d26123ca48e27c8/LICENSE)
contains GNU GPL version 3. The earlier helper's statement that no license was
found is superseded. GitHub's license history records that notice in the initial
commit, `41e9c1f0853926bbd3c84b9f03b5dd6f9c9a51cf`, on 7 April 2020. The README
does not separately state dataset-license scope, and the complete path inventory
contains no distinct dataset notice. The root notice alone was therefore not
treated as proof of dataset applicability.

That applicability question is now resolved by the authors' explicit
[OSF dataset-project metadata](https://api.osf.io/v2/nodes/awy7r/). Its title is
"COVID-19 Real World Worry Datatset" and its description identifies it as the
data repository for the original dataset paper. The project has a license
relationship to [GNU General Public License (GPL) 3.0](https://api.osf.io/v2/licenses/563c1cf88c5e4a3877f9e973/),
with the complete GPL text and its GNU source URL. This is a license declaration
for the author's dataset project, not an inference from an unrelated code
repository. It agrees with the pinned GitHub notice. The license-applicability
hold is released; there is no remaining absence-of-license blocker. Retain the
license, author/source attribution and derivative notices with the approved
local copy described below. No redistribution or external transfer is proposed here.

The initial OSF web fetch returned HTTP 403 and the browser API attempt failed.
A subsequent public API metadata fetch succeeded; the earlier statement that
OSF terms were unverified is superseded. Exact responses are retained in the
ignored `.agent-state/drive-20261115/week6-builder-c-checks/RW1_AUTHOR_NOTICES/`
directory, together with the pinned GitHub notice bytes. This table authenticates
the inspected notice/metadata responses, not downloaded participant data.

| Response | SHA-256 |
|---|---|
| `OSF_NODE_METADATA.json` | `f1f3acb649cd71bedb5ceb848202925cf85871df542e11833259df963512e219` |
| `OSF_LICENSE_METADATA.json` | `8d71e017c62bb83ba853725a35cd04b7c9d74e48779c605ff8e1bdc186976e9b` |
| `OSF_ROOT_FILE_METADATA.json` | `948411229e873f0688a017ddaad6583e0349b400070e887ac35c30c4b0755096` |
| `OSF_ORIGINAL_FILES_LEVEL_1.json` | `251c20f97890662cf8d044e3a42cb822a65f41df63c058b39ef00a0da330357c` |

The [pinned README](https://github.com/ben-aaron188/covid19worry/blob/7324d50869578589a47781bc1d26123ca48e27c8/README.md)
distinguishes original first-wave files, a cleaned first-wave version and a later
repeated-measures release. The packet names the original first-wave population.
The candidate metadata path is `data_phase_1/files/meta/rwwd_full.csv`, Git blob
`1fc84fa83c893391ad0e9a5663082f3210518ea5`. The separate metadata-only CSV has blob
`8cf93ceb03c400b6ef1b3054aa441fa7ac23f6a3`. These are Git object IDs, not downloaded
file SHA-256 hashes. The original full-file bytes are now authenticated by the
approved local-copy receipt below; no participant record has been parsed. Cleaned and repeated-wave
populations cannot silently replace the packet population. The source paper is
[Kleinberg, van der Vegt and Mozes (2020)](https://arxiv.org/abs/2004.04225), as
specified by the packet; this intake makes no new interpretation of the paper.

The OSF original-release metadata separately identifies
`/data/files/meta/rwwd_full.csv`, file ID `5e8c70b8430166012ba09787`, version 1,
2,278,256 bytes, with declared SHA-256
`ff47e3e7860f4c63be356fa7eec6be6587422fef1ec1e94f28b1be8d33c4d7dd`.
The inspected path is under the licensed dataset project; `files_clean` is a
separate directory. Root, original-files and metadata-directory listings are
complete, with no next page and no separate license notice in those directories.
The text directory was not enumerated or opened. The approved local copy now
matches both this OSF-declared SHA-256 and the pinned GitHub blob. This resolves
the original metadata-only byte-authentication gap without selecting a different
release or downloading a network body.

## Marker component

`runners/drive/cards/week6_rw1_intake_v1.py` contains a literal first-person plan
candidate and an annotation receipt gate. It covers the packet phrases, including
ordinary contractions. Sentence segmentation, corpus sampling and semantic
judgments are not asserted qualified. Negation, hypothetical language, quotations
and non-agentive future statements stay visible for the independent marker check.

The gate requires exactly 200 uniquely identified sentence hashes in a fixed
order, two different builder identities, pinned candidate/revision, independently
annotated provenance, and both list and hand labels from each builder. It reports
both list-versus-hand agreements and hand-versus-hand agreement. Owner review of
the actual isolation/provenance is still required: a self-reported flag does not
prove independence. One list revision is permitted; a second is rejected.

DESIGN CHECK: LESSONS sections 2 and 3 were read. A perfectly matching constructed
receipt is reviewable but remains unadmitted. Missing sentences, changed source
bytes, same-builder receipts and disagreement below the packet threshold must
fail. The constructed positive and negative phrase cases test only literal
implementation. They cannot count as the two-builder human-text check.

## Remaining holds and handoff

### Original-release projection and marker workflow, proposed freeze

The pinned GitHub original release is 2,278,256 bytes by a successful HEAD-only
request; the OSF metadata declares the same size. HEAD receipt:
`.agent-state/drive-20261115/week6-builder-c-checks/RW1_AUTHOR_NOTICES/GITHUB_RELEASE_HEAD.json`.
The body retrieval stopped before network/body/file access at the 50-GiB
source-download floor that the builder carried forward from Week 5 packet
section 0.5 (line 123). That is distinct from Week 6's generic 20-GiB runtime
start floor. The owner confirmed that the blanket download floor remains;
neither floor was weakened and no cleanup occurred. The refused attempt read
no participant bytes.
The refusal is retained in `RW1_RELEASE_ATTEMPT_RESOURCE_REFUSAL.json` beside
the builder receipts. Licensing is resolved independently of the download hold.

After exact-filename discovery, the owner separately approved copying the
pre-existing ToMpathy author release into
`corpora/store/external/real_world_worry/phase1_original_7324d508/`.
`SOURCE_RECEIPT.json` there has SHA-256
`2949d04cf94ccc7abeb3cfccefa6377aaeb0f182df44c28058a011b2f59e1258`.
It records six copied files: the original CSV, README, LICENSE, upstream intake
metadata, OSF project metadata and OSF license metadata. All destinations were
verified ignored before copying; source hashes were unchanged afterward, and
every destination matches its source hash. The CSV matches both the Git blob
and OSF SHA-256 above. The upstream intake metadata SHA-256 is
`bab11d00a905c50ef4029ce6a9ad5d93ceac593e82ed9fe5778c081e420d7dfe`.
The remaining notice pins are in the tables above. No source was modified and
no network body was downloaded. Header-only inspection confirmed the six
commissioned columns; no participant row or text was decoded. Projection,
sample construction and actual annotation remain unrun.

`runners.drive.cards.week6_rw1_source_v1` prepares a source-only projection and
blank hand/list forms. It reads a local original-release CSV only after checking
the immutable Git blob and OSF SHA-256, an 8-MiB byte bound and all four pinned author notices.
Its fixed CSV import allowlist is long text, worry, anxiety, fear, relaxation and
sadness. No short text, demographic field, raw personal identifier or other rating
is imported. Each of the original 2,500 source rows receives a salted opaque
person key. Missing required ratings remain null with dispositions; nonintegral
or out-of-range ratings refuse. Empty text remains a source row. There is no
selection on observed variation or fitted support.

Sentence boundaries are punctuation followed by whitespace/end, and line breaks.
Closing quotes/brackets stay with punctuation; exact Unicode offsets and text
hashes are retained. Abbreviations may split at periods. This transparent rule
is a proposed frozen tokenizer, not a claim of linguistic qualification. Sample
the lowest 200 hashes of `RW1-marker|20261107|opaque-sentence-id` among all
nonempty long-text sentences. Ratings and candidate-marker status never enter
selection. Multiple sentences from one person are permitted by this sentence
sample. The same ordered sample must reach both independent builders.

Both forms initially contain null labels and no automatic answers. Each builder
must first complete and seal the hand form without seeing automatic labels,
then complete a separate list form that binds the hand-file hash. Each must
provide independent-session provenance. The marker-review phase verifies exact
sentences, sealed files, builder identities and all original marker pins before
calling the existing agreement gate. A claimed independence flag remains subject
to owner provenance review. No actual annotations or provenance are fabricated.
Only original revision 0 is prepared by this wrapper; an allowed future list
revision needs its own frozen marker-code pin on the unchanged sentence sample.

The source handler has 128-person checkpoints and fresh replay. Inputs:
`source_file`, `notice_directory`, `identity_salt`; configuration
`{"phase":"RW1-source","max_new_blocks":4,"max_wall_seconds":600}`.
The marker-review phase consumes `prepared_run`, both builders' `*_hand` and
`*_list` sealed files; configuration `{"phase":"RW1-marker-review"}`.
Participant artifacts are refused outside ignored local output roots. Neither
phase computes a plan/worry relationship, learns a vocabulary or grants admission.

Nine proposed constructed checks in `tests/test_week6_rw1_source_v1.py` cover
exact sentence offsets, field/rating validation, outcome-independent sampling,
blank form refusal, hand sealing and exact text, source-byte refusal before CSV
import, the fixed CSV allowlist with a constructed forbidden-column sentinel,
bounded source/replay, and two sealed constructed builder pairs that still cannot
grant admission. Source authentication is substituted only inside fixtures;
there is no production bypass flag. They have **not run**: owner design/fixture
review and a serial test-slot allocation are required first. The wrapper does not yet implement RW1's partial
correlation, cross-fitted 200-word vocabulary, person bootstrap or secondary
time/place marker. Those require their own prospective design before outcomes.

- Retain the now-qualified GPL 3.0 dataset terms and exact authenticated local
  release. Qualify the selective projection before running it; read only long text and the five ratings,
  reject demographic imports and keep all participant content in ignored storage.
- Freeze sentence segmentation and the 200-sentence sample without outcome
  selection, then obtain two independent builder annotations. None exists yet.
- Build the cross-fitted bad-news vocabulary, person bootstrap and the packet's
  planted partial-correlation/zero fixtures before any human RW1 outcome. No
  human plan/worry relationship has been computed by this intake.
- Owner review, complete native fixture, source/cost pins and campaign admission
  are still required. The original supplied files remain unchanged.

All 15 constructed marker/receipt checks in `tests/test_week6_rw1_intake_v1.py`
passed within the initial 33-check builder suite, using two numerical threads,
unique temporary storage and disabled pytest caching. The marker code has not
changed since that check. Source hashes, process identity, CPU/wall usage and exit
are in `.agent-state/drive-20261115/week6-builder-c-checks/BUILDER_C_TEST_RECEIPT.json`.
These fixtures are not the independent annotation study and do not release the
marker-qualification or production-admission holds. The dataset-license finding
above rests on author notice metadata, independently of these fixtures.
