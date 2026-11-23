# ICSI sound source and decoder

The original release contains 75 meeting transcripts and a separate preamble collection. The census selects one MRT whose session matches its meeting filename. Identical copies count once. Conflicting editions stop the run. The anonymous mixed-mark share table covers all 54 speakers with at least one marked laugh. Seven speakers had no laughter marks and therefore no share. An utterance can contain several mixed marks.

The original participant assignments identify 468 distinct headsets. Their labels use digits and the letters A and B. The first attempt stopped at the channel-label check before reading a waveform. The recovery checked the labels against every selected transcript and the frozen file inventory before admission. It preserves the original attempt and its charge.

The job decodes original NIST SPHERE recordings in memory with LDC’s sph2pipe 2.5. The two supplied little- and big-endian compressed test recordings reproduce the publisher’s expected WAV digest. Every original recording must match its size and SHA-256 digest. The decoded signal must also match the original sample count, sample rate, channel count and PCM checksum. The runner then computes the six registered features, held-out comparisons and a fresh-process replay. Only group outputs and the requested anonymous fractions are filed. [LDC software distribution at OpenSLR](https://www.openslr.org/3/)

| Input | SHA-256 |
|---|---|
| Original MRT transcript archive | `9db98ebdd61a085b4f45f24f46e9c9f6c6f26c3c9cd41643a3b9e74362c85de7` |
| LDC decoder distribution | `5be236dc94ed0a301c5c8a369f849f76799ec7e70f25dfc0521068d9d1d4d3e3` |
| Windows decoder | `cc9cd514a31122f2dbba6f7b18c3aa6f6e55819ee64c7e61ad8edef5e32ede35` |

The duration measure is **annotated utterance length**. Laughter that overlaps speech is not in the sample, and that may be a kind of its own. [Sampling and frame definitions](LGH1_RECORDING_BINDING.md)
