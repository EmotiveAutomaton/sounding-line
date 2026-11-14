# RF1 and CP1: private intake and frozen marker qualification

Proposed 2026-11-13 under `PACKET_TWO_DAY.md` §3E and Builder B's §4 assignment.
This version is not committed or admitted. It qualifies intake and lexical counting,
not the scientific RF1/CP1 comparisons. No original source or pinned runner changes.

## Authority and source evidence

The full two-day packet controls. The referenced R13–R15 handoffs and `claude/`
directory were absent in the locations checked on this build; their content has
not been invented. The existing theory's standing discussion and correction history
(`THREE_COGNITIVE_LAYERS.md` lines750–841 and relevant afterword1120) were reread.
The new packet's seen-competent/seen-kind framing supersedes older wording for this
build. The three-read account is expressly a proposal, not a settled theory change.

Private acquisition receipts live in `corpora/store/external/stanford_wiki_rfa/`
and `corpora/store/external/convokit_wiki_corpus/`, each with `SOURCE.md`, exact
SHA-256 pins, source-page snapshots and licence qualifications. RF1's official
archive has SHA-256 `88d53196fb2564a2e20286dbba818832f718cc352bb181a2101d23d2556f0862`
(14,936,383 bytes). CP1's official `wiki-corpus` version4 archive has SHA-256
`9995d3b885338e9332496193a0b7b01453174c2d6008ec88634ad7cb884f8f41`
(238,414,152 bytes). These are acquired bytes, not qualified rows.

[SNAP's dataset description](https://snap.stanford.edu/data/wiki-RfA.html)
documents seven vote fields and repeated candidacies. Its linked
[licence page](https://snap.stanford.edu/snap/license.html) describes SNAP software
under BSD; this receipt does not extend that wording into a dataset-specific
licence for comment text. Cite West, Paskov, Leskovec and Potts (2014), *Exploiting
Social Network Structure for Person-to-Person Sentiment Analysis*, TACL. No raw
redistribution is proposed.

[ConvoKit's corpus documentation](https://convokit.cornell.edu/documentation/wiki.html)
states CC BY-SA4.0. Cite Danescu-Niculescu-Mizil, Lee, Pang and Kleinberg (2012),
*Echoes of power: Language effects and power differences in social interaction*,
WWW. The archived official download configuration identifies `wiki-corpus`,
version4. The separate gone-awry and Wikipedia politeness corpora are not substituted.
Only archive directory metadata and one record's field names/types were inspected;
no real marker tally or scientific source transformation has run.

## Source semantics, privacy and unresolved source gates

RF raw fields are `SRC,TGT,VOT,RES,YEA,DAT,TXT`. Blank lines delimit records;
continuations after TXT remain comment text. Votes are -1/0/1, outcomes -1/1,
years2003–2013. Empty text is retained as a zero-marker comment. All raw records
remain in the frequency denominator; declared refusals count separately. The
official count is198,275. An election identifier is absent. **Candidate-year,
outcome, archive order and an invented date-gap rule cannot replace that identifier.**
RF election grouping and the early-third comparison stay source-held until exact
boundary provenance is recovered and separately reviewed. The marker instrument
can be checked on all comments independently of that hold. `election=null` and
`election_identity_qualified=false` are structural outputs.

CP archive schema uses `id,user,root,reply-to,timestamp,text,meta`; its API aliases
are not file-field names. `meta.is-admin` is an utterance boolean; speaker metadata
also has `is-admin` and string `edit-count`. Retain both admin fields separately.
Later reply-pair analysis uses utterance admin, not a silently substituted global
role. Edit-count's observation clock is unqualified and must remain an explicitly
associational secondary. The official total is391,294 utterances. The large parsed
and arc files are not needed and are never extracted or loaded by this intake.

Use the existing private32-byte Week5 salt. HMAC-SHA256 identities share a user
namespace within each corpus but never identify people across corpora. Salt source
record, conversation, voter and candidate IDs before emitting any derived row.
No salt or identity map is exported. Raw archives, deidentified per-item tables,
manual review snippets and annotations stay ignored and local; only aggregate
receipts are candidates for later publication. No usernames enter queries or URLs.
There is no content-topic selector, no self-harm analysis and no emotion classifier.

## Frozen lexical rule

The complete terms are literal tuples in `week5_rf_cp_markers_v1.py`, exactly the
packet's starting lists. No stemming, synonyms or learned labels. NFC, casefold,
straightened curly apostrophes and U+2010/U+2011 hyphens precede matching.
Terms require Unicode word boundaries; spaces inside a phrase match whitespace.
Within each family, retain longest non-overlapping phrases, preferring a listed
negative RF phrase on equal length. Thus `don't trust` counts against trust once
and not for trust. Unlisted negation is not inferred: `not competent` still has
the literal positive hit and can fail semantic review. No hindsight repair is allowed.
RF stores separate for/against counts and family-presence indicators. Selection of
scientific rates or signed pooling belongs to the later frozen scientific handler.

CP strips lines whose first nonspace character is `>` and HTML blockquotes before
tokenization. An unmatched opening blockquote removes the trailing quoted region.
Ordinary Wikipedia colon/list indentation is retained. Tokens are Unicode letter/
digit runs with internal apostrophes; punctuation and underscores separate tokens.
All utterances, including quote-only/empty ones, remain in the frequency denominator.
Every count is reported with tokens and its rate per100 tokens; zero-token rates
are null, not infinity or a supported pair. Sentence starts are the text start,
newlines, or `.?!` followed by whitespace; opening quotation/parenthesis marks may
precede a listed command. `Do/Don't` followed by a subject pronoun is not a bare
command. These are frozen surface rules whose semantic errors the manual check
must expose. Later pairs require different authors and at least10 tokens on both
stripped sides, exactly as the packet states.

## Instrument qualification and annotation rule

For each corpus and family, count utterances/comments with at least one family
hit. The frequency gate is >=3% of all records. Select100 distinct hit records by
ascending SHA-256 of `family|20261112|marker_family|salted_record_id`; if fewer100
exist, retain all and mark unsupported. This deterministic uniform hash sample is
fixed before correctness labels. A record may appear in more than one family and
is separately judged for each. No review rows are selected on correctness, votes,
outcomes, admin status or theories.

The builder reads only the selected private file. RF correct means the counted
expressions actually evaluate a person's competence/experience,
trustworthiness/character, or interpersonal liking/dislike, in the named family
and with the indicated for/against polarity. A false or wrongly polarized counted
match makes the sampled record incorrect; quotations, purely topical mentions and
evaluation of an impersonal proposal do not suffice. CP correct means an actual warmth/repair expression, softened or
deferential request/assertion, or imperative/forceful assertion in that utterance;
mere citations, quoted words or topic mentions do not suffice. Negated or ironic
uses are judged in their actual local meaning. Ambiguous = incorrect. Record a
boolean for every sampled item with a private short reason. No model adjudicator.
The owner reviews aggregate tallies, not hits. Each family needs >=80 correct of
exactly100, as well as frequency. No partial correctness score is emitted while
labels are incomplete. A failing family remains failed; changing words requires a
new version/freeze and a new independent sample, never salvage of this sample.

## Engineering execution and review boundary

`week5_rf_cp_source_v1.py` writes immutable512-record compressed blocks, bound to
archive/marker/source-module/salt hashes. Each block has its own byte seal. It yields
at closed block boundaries and honors `YIELD_REQUEST.json`; resumed source bytes,
record order and closed prefixes are authenticated. A full independent replay
reconstructs all rows and the selected review file from the raw archive, compares
every block and final receipt, and emits `SOURCE_VERIFIED.json`. Completed execution
is idempotent. A complete source receipt is not scientific admission or a semantic
review pass. Parent runtime still owns native identity, resources and accounting.

`week5_rf_cp_instrument_v1.py` consumes the complete source-native envelope,
including COMPLETE/VERIFIED/PLAN identities, source replay and all relevant output
pins, plus a frozen manual annotation file tied to the private review digest.
Constructed labels cannot pass as human review. Every label has a private reason;
the human method must be `manual_private_read`. Its fresh verifier independently
recounts the labels and frequency gate; it does not pretend to rejudge semantic
labels. A passing result licenses only this lexical instrument, never science.

The first counted quantum is a source cost probe; actual CPU, wall time, memory,
output size and whole-source forecast are unmeasured now. All costs stay in RF40,000
or CP60,000 CPU-second ceilings. If forecast exceeds7,200, use the packet's counted
checkpointed first5% pilot before long admission. No sample size or forecast is
invented; whole candidate/conversation sample routes depend on a measured E trigger
and, for RF, resolved election identity. No cost-held source occupies a slot.

The native fixture's constructed corpora exercise both actual handlers, source
and wrong-pin refusal, sealed-prefix resume, completed reentry, complete fresh
replay and exact hand answers. Twelve RF comments and ten CP pairs have literal
expected values written independently from the adapter. Tests also exercise
quote removal, apostrophes, lexical boundaries, altered blocks, altered summaries,
duplicate labels, incomplete review and exact80/100 and3% admission boundaries.
The packet's RF three-read planted model and CP complementary/convergent statistical
worlds are **not qualified by this intake fixture**; the later scientific comparison
handlers and their model fixtures remain unbuilt/unadmitted.

## DESIGN CHECK

Read LESSONS §2, all§3, §4 and applicable§5, the project and drive-folder contracts,
the full two-day packet and the relevant theory/correction history above.

| Gate | Null expectation | Alternative expectation | Refusal direction |
|---|---|---|---|
| Literal counts | No listed phrase gives exact0 | Known listed spans give literal hand count | Any mismatch |
| Source pin/order/seal | Same bytes reconstruct same rows | Same requirement, irrespective of outcomes | Changed/missing pin, ID or sealed row |
| Source population | Official raw count and <=1% explicit refusals | Same count/refusal rule | Wrong total or >1% refuses source qualification |
| Review coverage | Rare marker may be unsupported | A useful marker still needs>=3% and100hits | Below either floor never licenses a family |
| Manual correctness | A misleading lexical list can fail | Useful list needs>=80/100 | <80, ambiguous labels, duplicate/missing review |
| Semantic vs scientific | Lexical pass implies no effect | Lexical pass only licenses later comparison | No automatic claim or election reconstruction |

Case/check: literal source fields can supply all comment/utterance marker checks;
RF's election unit is presently unavailable and cannot supply its scientific case.
Smaller route: no arbitrary marker/pilot sample. Measured whole-unit E routing and
original scientific-model gates remain owner decisions after counted cost evidence.
Instrument/source records are S `run`, not `claim`, with tagsH15-T3/H15-T4 and real/
constructed status explicit. P's estimate/interval/bar/SE, sees2.8SE and supportsat
bar+2.8SE are obligations of later scientific fits, not fabricated from marker counts.
Activation X: these intake records say nothing about CARE/PLAY/FEAR/RAGE or a set
point. They establish only whether language can serve the proposed social readout.
