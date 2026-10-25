# CA1 actual encoder dependency gate

The first corpus feature pilot stopped at import because `sentence_transformers`
was absent. Neither `pyproject.toml` nor the existing environment lock declares
that optional package. The mathematical fixture used a deterministic encoder
stub and therefore did not exercise the actual package import/load path. The
failed corpus attempt remains intact; its counted cost belongs to CA1.

The proposed additive remedy is exactly `sentence-transformers==6.2.0`, with
no dependency upgrades. The [release metadata](https://pypi.org/project/sentence-transformers/6.2.0/)
and [tagged requirements](https://raw.githubusercontent.com/huggingface/sentence-transformers/v6.2.0/pyproject.toml)
were checked October 25. The installed Python 3.13.2, transformers 5.14.1,
torch 2.13.0+cu126, hub 1.26.0, tokenizers 0.22.2, numpy 2.4.6, scikit-learn
1.9.0, scipy 1.17.1, typing-extensions 4.16.0 and tqdm 4.70.0 meet its base
version constraints. This metadata compatibility is not a successful import.

The universal 6.2.0 wheel is 760.7 kB; PyPI gives SHA-256
`ffb51ccfef65427cfa61776d0eeeb257600b0099cf0c7533ae9a6856d31e4665`.
The private owner handoff supplies a hash-pinned requirement and isolated target
installation arguments using `--no-deps` and `--only-binary=:all:`. Installation,
environment registration and any corpus recovery are owner actions. No dependency
was installed by the builder, and the frozen model/feature modules are unchanged.

`cards/week3_alignment_encoder_smoke.py` exercises the original real encoder
path on eight constructed multilingual strings, including an exact duplicate.
It authenticates the complete pinned local model, requires the reviewed package
version, disables hub network access, and uses CPU with the original two-thread
setting. The gate checks finite float32 384-dimensional normalized vectors,
exact duplicate agreement, nonconstant output and repeated encoding equality.
Fresh verification reloads and re-encodes the complete constructed set. There
are no corpus texts, value scores, downloads or installation steps in this gate.

Three targeted checks validate the smoke gate itself. They do not claim that the
actual model import has run: the owner must launch this real-model native gate
after the additive dependency repair, before a separately identified corpus
feature-pilot recovery. A remaining import/load failure must be recorded rather
than substituted with a mock or silently different encoder.
