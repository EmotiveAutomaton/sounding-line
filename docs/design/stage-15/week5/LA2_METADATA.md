# LA2 ICSI metadata variants

The source qualification in [LA](LA.md) remains operative: ICSI records
English variety and region, with no native-language or nationality declaration.
These two descriptive variants retain their actual labels and are separate
from AMI's native-language primary. No demographic proxy is invented.

## DESIGN CHECK

Method LESSONS sections 3–5 and CONTROLS sections 1–6 informed this implementation.
The native fixture reparses actual-format ICSI speaker XML, then exercises the
production preparation and analysis handlers on twenty-four constructed
meetings. A separately written symmetric-event oracle checks the joined-laugh
fractions, rates and same-background labels; a direct within-meeting regression
checks the point contrast. Both variants complete all 2,000 cluster refits.
Unknown metadata and a participant with no laughs remain counted exclusions.
Requesting unrecorded native language returns unsupported, never a zero effect.
The existing signed and null statistical fixtures remain required.

The smaller route is the already declared below-twenty-meeting pooled
descriptive fit. No same/different contrast, or a source with no supported
pairs, is unsupported; it is never a negative finding. The two metadata fields
share LA2's 20,000-CPU ceiling and LA's 450,000 family ceiling. Preparation,
native verification and every resample are charged. Any forecast above 7,200
requires its first five-percent in-slot pilot under amendment K.

Dispatch the already frozen `week5_la_pipeline` with `card='LA2'`,
`corpus='ICSI'`, and `background='english_variety'` or `background='region'`.
Its only input is the verified LA0 source root. Feed each complete
`ROWS.json.gz` to the already frozen `week5_la` with `card='LA2', draws=2000`.
Neither variant depends on a language model, LA1, or AT2 selection. The new
fixture adds proof for these paths without changing either frozen module.
