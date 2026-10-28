# P3c pinned public model intake

DESIGN CHECK: LESSONS 3–5 read October 27. A null and an alternative require the
same source identity. Missing or gated files, an unknown revision, size overruns
and changed Git/LFS hashes refuse. A successful intake does not validate labels.

Week 3 section 4 explicitly commissions the public IteraTeR classifier. Its
Hugging Face revision is `d9e6e6ee893e9f36cbba8047b838ccbfea1c1c32`.
The exact metadata reports public, ungated access. Retrieve only the seven
published configuration, vocabulary, model-card and PyTorch weight files, without
credentials, remote code or inference. The weight file must match its published
LFS SHA-256; the smaller files must match their published Git blob identities.
Retain SHA-256 and byte counts for every local file, and independently repeat the
entire inventory before completion. The two-GiB output ceiling includes the
1,421,620,013-byte weight file. Never deserialize weights during intake.

The [official repository](https://github.com/vipulraheja/iterater/tree/41adc0818356f78b362a9382a3732e0529f3fe35)
directly links this exact model and carries Apache 2.0 terms. Its README and
LICENSE were fetched and read; both original byte receipts and the pinned
repository revision are retained. The model card itself has no separate license
field. Record that distinction; no weights or participant records are redistributed.
The first metadata request was blocked by the local sandbox's network permission;
the approved read-only retry succeeded. No gate or access restriction was bypassed.

Six targeted checks exercise the actual intake handler with a fake transport,
unchanged reentry without another download, independent inventory verification,
corrupted large and small files, absent files, wrong/gated revisions and the size
ceiling. All pass on first execution. They establish transport/byte-accounting
behavior only. Model execution must subsequently use the exact local files,
weights-only loading, CPU evaluation and explicit token coverage, with its own
native numerical checks before corpus predictions.

The 200 annotations under [the frozen criteria](P3C_CALIBRATION_20261027.md)
were read and assigned by the operating agent in two complete blinded blocks.
Their immutable private receipt binds the prepared pairs and criteria; no
classifier prediction was visible. This is agent-made reference labeling, not
human validation, and licenses no downstream comparison on its own.

Charge an additional sixty CPU seconds for intake construction/tests, alongside
the already measured source charge, to the original 14,400-second P3c budget.
The download/inventory job is capped at 300 CPU seconds including verification,
1,800 wall seconds and two GiB retained output, with one counted CPU lease and
the existing host resource floors. There is no paid call, GPU use, scientific
effect, changed agreement gate or retry of any held card.
