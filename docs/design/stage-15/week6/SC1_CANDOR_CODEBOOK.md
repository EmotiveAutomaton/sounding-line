# SC1. CANDOR codebook review

The collector’s card, schema and release-pinned provider dictionaries identify
the three partner reports needed for SC2. In each survey row, `user_id` is
the respondent, `partner_id` identifies the person being rated and
`conversation_id` identifies their conversation. On a transcript row,
`speaker` uses the participant’s `user_id`. Match the partner’s rating to the
speaker being rated within the same conversation. A participant can appear in
several conversations.

| Requested measure | Survey field | What the respondent rated |
| --- | --- | --- |
| Humor | `you_are_funny` | How funny their conversation partner was |
| Status | `i_think_your_status` | Where their partner belongs on the ten-rung social-status ladder |
| Liking | `i_like_you` | How much they liked their conversation partner |

All three names occur in the 223-column survey header. The survey also
contains self-ratings and guesses about the partner’s impression, with
different field names. Conversation identifiers and partner identifiers
are available in the same survey table.

The provider documents four v1.1 transcript tables, Audiophile, Backbiter,
Cliffhanger and NaturalTurn. All four have `conversation_id`, `speaker` and
`utterance`. They are different segmentations of the same speech-to-text
source. In NaturalTurn, double angle brackets mark low-confidence words.
Backchannel, turn timing and speech-recognition confidence have their own
fields. The dictionaries do not establish which of the four tables retains
laughter marks, filled pauses or restarts in the words themselves. The
survey’s `laughter` item asks which person laughed more.

The outstanding SC1 check counts conversations containing each of the six
registered text markers separately in each transcript version, inside the
sealed runner. A literal mention of laughing gives a different measurement
from a bracketed laughter annotation. Neither alone establishes that
restarts are annotated. SC3 requires evidence that its input distinguishes
its two kinds of speech. Four versions of one conversation contribute one
conversation to each version’s own table.

The only inputs to this review were collection metadata and provider
dictionaries. Their SHA-256 digests identify the exact release objects.

| Source | SHA-256 |
| --- | --- |
| Collector card | `6a49e516ed597657dac01a5a5f8a4c1f8d06aa7526ccf17538acae0e4e066a3d` |
| Collector schema | `d268e21765fe24077d95bbb59b93b31f2aaa8dd0c677edddaeab7eb151f4ffcd` |
| Provider survey dictionary | `7feaf9a5a3b4a12d091036ae30d7ba78c66f071f1fbbce81f038f2d51b3d9314` |
| Provider transcript dictionary | `cc2ea478af1b3df72c8146cd981c9cd04cf263bb47bcc7392c426caab2422f47` |

The [Week 6 packet](PACKET_EXTENSION_2026-11-19.md) contains the prospective
marker list, the SC2 comparison and the SC3 dependency.
