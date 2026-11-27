# CRV1 · pitch in paired infant-directed and adult-directed speech clips

The curator approved this separately labelled within-speaker first comparison on November 25 at 04:45 Pacific and then directed the two pitch measures to run. Speech rate and vowel duration await validated timing measures. The original same-recording contrast and adult comforting remain open.

Hilton, Moser and Mehr v1 supplies two elicited takes. B denotes infant-directed speech and D adult-directed speech. Pair by fieldsite and participant number using the published naming convention. Preserve CC BY-NC-SA 4.0 attribution. Internal, noncommercial tests only. The SHA-256 receipt binds the raw archive, the Praat grids and the fieldsite companion. Only aggregate counts and contrasts may be retained. No voiceprint, speaker embedding, audio excerpt or individual pitch is retained. [Provider release](https://zenodo.org/records/5525161) · [Provider interval extractor](https://github.com/themusiclab/infant-speech-song/blob/main/analysis/acoustics_processing/1_export_subclips.py)

## Design check

The design follows the source, instrument, support, resource and replay checks in method lessons §§2–5. The layout review found 404 pairs before measuring pitch. Require both clips' annotation end times to match the waveform to within one sample. Use the provider's nonempty first-tier intervals, dropping frames that cross an interval boundary. Use the arithmetic channel mean, anti-aliased resampling to 8 kHz, and the existing Week 7 voiced-frame pitch estimator. Require at least ten voiced frames per clip. Report incomplete pairing, clock mismatches and insufficient voicing separately, counting each speaker once in that order.

Height is the median log pitch in semitones. Spread is its interquartile range in semitones. Take infant-directed minus adult-directed for each person, then the equal-person mean. File 95% percentile intervals from 2,000 paired whole-person draws, fixed seed 20261125. Below 20 usable pairs file support alone. These are descriptive contrasts on the retained speakers, with no new decision bar. The sampling intervals are conditional on the represented sites.

Identical tones should give zero difference. A doubled tone should add twelve semitones in height, and two equal sections one octave apart should span twelve semitones in spread. Silence and an incorrect annotation clock must be excluded. Check the pair inventory, full source digests and a fresh-process replay. Use one local CPU slot, two threads, with replay included in the 200,000 CPU-second sound-row allowance. Retain aggregate progress and stop at the resource floors or drain.

The clips were recorded on request and in separate takes, so recording conditions and performance differ between the two, and the listener is an infant, not a child who answers.

