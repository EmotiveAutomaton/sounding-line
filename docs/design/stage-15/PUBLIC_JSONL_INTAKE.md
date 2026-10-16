# PRISM and MultiPref intake

The confirmed next-round commission permits public data acquisition before the
Friday packet. This finite pass retains pinned official PRISM and MultiPref
releases locally. It makes no model calls, fits, outcome comparisons or paid calls.
It uses one serial downloader, a one-GiB ceiling per file, three-hour wall ceiling,
host memory/commit and disk floors, exact notice hashes and no automatic retry.
The tested transport requires identity encoding and rejects incomplete downloads.

- [PRISM](https://huggingface.co/datasets/HannahRoseKirk/prism-alignment): survey,
  conversations, utterances and metadata stay distinct. The long utterance form
  duplicates human inputs by design; its rows are not independent decisions.
  Human text is CC-BY-4.0; model text is CC-BY-NC-4.0 plus originating model terms.
  This is research use only, with no re-identification or cross-dataset identity
  linkage. Keep the supplied privacy/moderation metadata and original notices.
- [MultiPref](https://huggingface.co/datasets/allenai/multipref): ODC-BY original
  JSONL preserves normal and expert annotations, reasons, confidence, ties and
  timestamps. Do not substitute the binarized variants: a tied human vote is
  randomly broken there, and the GPT variant has a different label source.

Each source revision and file URL is frozen in the raw plan. Only object parsing,
row counts, field names and hashes are recorded during acquisition; these do not
prove semantic validity, privacy or scientific admission. Preserve human/model
provenance, within-dataset identities and exposure. No raw records or identifying
annotations are exported. Before modeling, validate codebooks, units, temporal
semantics, quality sensitivity and held-out components in separate frozen adapters.

`runners/next_round/intake_jsonl.py` produces a completion or failure manifest at
`results/phase_2_4_stage_15/raw/public-jsonl-v1/`; exact native disappearance is
watched separately. Completion requires independent full-file hash/schema checks
and internal write-through before ACK. No existing attempt or live code is edited.
