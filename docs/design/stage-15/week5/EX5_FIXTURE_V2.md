# EX5 constructed XML fixture correction

This operational addendum preserves EX5_TWO_DAY_V1.md and the production exporter unchanged. The initial constructed suite completed four checks and refused three source-chain checks because ElementTree's `encoding='utf8'` emitted an XML declaration before every row. The strict production source parser correctly rejected that non-source-shaped document before selection or export.

The separately named fixture uses `encoding='utf-8', xml_declaration=False` for row fragments. Its document still writes exactly one explicit XML declaration and one posts root. The seven original check bodies, expected selection, support gates, complete independent parser/replay and immutable-copy checks remain identical; only the fixture import changes in the successor test file. No source, model, selection, threshold, supervisor or publication rule changes.

## DESIGN CHECK

Read LESSONS's actual-byte/serialization checks and the original EX5 design. A valid constructed dump contains one declaration followed by complete row fragments; a repeated declaration remains refused. The expected null is an insufficient site with no bundle; the known answer remains exactly 400 fixed-hash questions per each of five sites with every answer/field replayed. Four prior passing checks and all three prior refusals remain preserved in the original resource receipt. The successor repeats the same seven tests under the original 180-second owned-tree cap, two numerical threads and resource floors. Owner review and all real-source/export-copy gates remain pending. This note is prepared, not a claim of committed or admitted status.
