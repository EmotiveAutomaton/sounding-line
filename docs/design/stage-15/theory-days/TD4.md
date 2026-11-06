# TD4: frozen implementation note

DESIGN CHECK: LESSONS 1a-1c and 2-5; CONTROLS 6-7.
Under the null the control must retain zero; under the specified alternative it
must recover the registered direction. Invalid controls or missing support stop
scientific interpretation. The inconclusive band includes every case not admitted
by a passing control and an explicit support or against rule.

Practical bars: exactly the inversion and residual-ratio bands in the supplied packet. Missing/zero-variance components are untestable, never zero-valued.

[Review amendments](REVIEW.md) and [source intake](DATA_INTAKE.md) bind this
implementation alongside the unchanged supplied specification below. All draws
use seed 20261106 unless the packet explicitly retains a prior frozen sample.
Scientific execution must pin a Git commit containing this note. This design
records planned work, not completed validation or results.

### TD4. Are the word scales single scales? (C2)

- **Words.** The curator's scales, weak to strong:
  - FEAR: uneasy, worried, anxious, scared, terrified.
  - RAGE: annoyed, frustrated, mad, angry, furious, rage.
  - SEEKING: interested, curious, eager, enthusiastic, excited.
  - PANIC/GRIEF: sad, lonely, grief, anguish, heartbroken.
  - CARE: tender, fond, protective, devoted, love.
  - PLAY: amused, silly, giddy, playful, hilarious, hysterical.
  - LUST: desire, passionate, lust, aroused.
  - DISGUST: dislike, yucky, disgusted, gross, loathe.
- **Mapping to intensity columns.**
  - RAGE to anger, FEAR to fear, PANIC/GRIEF to sadness, DISGUST to disgust.
  - SEEKING to anticipation, with joy beside it.
  - PLAY to joy; CARE to trust, with joy beside it.
  - LUST has no column, so it gets VAD only.
- **Coverage first.** Use NRC Emotion Intensity Lexicon v1 and NRC VAD v2.1. Report which words each lexicon holds. A word is covered for intensity only where it has a score in its scale's mapped column, since the intensity lexicon scores a word only for emotions it is associated with. A scale with fewer than 4 covered words is "not covered" for that lexicon. Adjacent pairs are neighbours in the curator's order among covered words; LUST's order is checked on VAD arousal.
- **Primary, per covered scale.**
  - The number of adjacent pairs that are out of order on the mapped intensity, with Spearman's correlation.
  - In VAD, the off-line ratio: the residual standard deviation of dominance after a straight-line fit on the mapped intensity (on arousal for LUST), divided by the standard deviation of arousal. Words on one line score near 0 whatever the line's slope, so the ratio reads a second dimension, not the scale's direction.
- **Outcomes, per scale.**
  - **Against:** more than one adjacent inversion, or an off-line ratio above 1.
  - **Supports:** no inversions and a ratio below 0.5.
  - **Inconclusive:** anything else.
- **Scope.** These are word norms. A positive result shows how people rate words, not that a channel fires in grades.
- **Ceiling:** 0.1 CPU-hour.
