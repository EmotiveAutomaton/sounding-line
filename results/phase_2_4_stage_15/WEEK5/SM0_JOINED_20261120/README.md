# Sealed joined-source structure aggregates

These four CSVs are the unchanged, hash-verified outputs returned through the
installed Spark gate. They contain operational structure diagnostics, not study
estimates. In each wave, table_001 is the main survey and table_002 the diary.
`n` is the exact number of distinct nonmissing people in that file, not its row
count or a cross-file union. Structure columns are fixed codebook presence
flags. Status counters describe source listing/load coverage; error columns
are fixed binary categories. Every status row retains its own table's actual n.

See [full method and limits](../SM0_JOINED_COMPLETE_20261120.md). No participant
records, identifiers, raw values, filenames or source paths occur in these CSVs.
