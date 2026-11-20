# Joined MIDUS structure recovery

Curator authority, November 20: wait for the archive thread's layout manifest
and unchanged joined folders; rebuild the mapping from that manifest; rehearse
a fixture with the same layout; rerun only `midus-m2-joined` and
`midus-m3-joined`. Reset this probe's three-failure count once. Preserve the
earlier failures and cumulative Spark invocation accounting. The reset is
available and unused; it is not an automatic repeated reset or a new campaign.

The successor component separates listing from table loading. A bounded,
non-following directory walk records fixed format counts without returning
filenames, identifiers, source values or exception messages. A reviewed mapping
names at most 64 exact relative tables, their daily/survey roles and the existing
documented person key. Unknown aliases, duplicate or escaping paths and a
different person key refuse mapping rather than guessing. The actual mapping
cannot be frozen before the incoming manifest is reviewed.

The component writes `status.csv` even when the mapping is invalid, the listing
is incomplete, all tables fail or no supported table exists. Its fixed schema
distinguishes files, table-load counts and read reservations. A successful
diagnostic is not source admission. Only successfully counted populations of
at least eleven people enter the separate `structure.csv`; small populations
remain suppressed. The same two-gigabyte read ceiling and original parser are
retained. Archive extraction, audio/video access and scientific fits are absent.

## Ratified return path: unchanged gate and fixed exit codes

The curator rejected the proposed metadata-only return channel on November 20.
The installed sealed runner and gate remain unchanged. Layout comes from the
archive thread's manifest outside the sealed boundary. The original v2 component
and its twenty-three checks are retained as local diagnostic construction; it
must not be deployed as a sealed entry point. Its original design bytes are
preserved with its qualification. `week6_sm0_probe_v3.py` reuses its bounded
inventory, strict mapping and fixed status-schema validation, with this return
contract in place of metadata-only output.

If at least one table loads with eleven or more verified distinct people, both
`structure.csv` and `status.csv` go through the existing aggregate writer in one
validated output set. Each status row identifies a neutral table ordinal and
uses exactly that table's actual person count as `n`. No shared denominator,
row count, estimate, padding or invented person is substituted. Loaded tables
below eleven people are suppressed in both outputs. The fixed listing/load
counters describe operational coverage, not attributes of those people;
per-category binary error flags make partial coverage explicit. No source
names, paths, identifiers, values or free-form exception text are returned.

When no eligible row exists, nothing is written to the returned output folder.
The probe returns one fixed child exit code below. The installed runner reports
that child code in its failure message while its own CLI exits with code 4;
these are distinct codes and both must be recorded. The gate is never asked to
admit a listing-only table. Even if a table loads, the all-small-population case
returns a code rather than violating the existing minimum-person rule.

Table: fixed child exit code, category and condition. All codes are within
10–119. None uses a timeout/signal-reserved code. Mapping and listing errors
stop before data reads; for several per-table failures without an eligible row,
the lowest observed code wins. That code identifies one observed condition,
not an assertion that other failures were absent. Zero means a gated diagnostic
candidate was written, never scientific source admission.

| Code | Category | Condition |
|---:|---|---|
| 10 | `mapping_schema` | Missing or extra mapping fields or non-object mapping. |
| 11 | `joined_alias` | Unsupported schema version or a source alias other than the two joined folders. |
| 12 | `table_roster` | Missing, empty or excessive table roster. |
| 13 | `table_declaration` | Missing or extra fields in a table declaration. |
| 14 | `nonportable_path` | A mapped path is non-string or contains a backslash or colon. |
| 15 | `unsupported_or_escaping_path` | Absolute, empty, dot-segment or unsupported-format path. |
| 16 | `duplicate_path` | Duplicate mapped path under case folding. |
| 17 | `unreviewed_key_or_role` | Person key or daily/survey role differs from the reviewed mapping contract. |
| 18 | `source_unavailable` | Source root missing, not a directory or linked. |
| 19 | `listing_error` | Directory census incomplete after an enumeration error. |
| 20 | `listing_limit` | Bounded directory census exhausted. |
| 21 | `empty_source` | Complete listing finds no regular file. |
| 22 | `archive_only` | Every listed regular file is an archive. |
| 23 | `no_supported_table` | Regular files exist but no supported loose table. |
| 24 | `mapped_file_missing` | A manifest-listed table is absent from the complete safe census. |
| 25 | `read_limit` | Conservative cumulative read reservation exceeds its cap. |
| 26 | `person_field_absent` | The reviewed person identifier column is missing. |
| 27 | `empty_table` | A delimited table has no header. |
| 28 | `ambiguous_columns` | Case-folded column names collide. |
| 29 | `malformed_table` | A delimited record does not match its header. |
| 30 | `nonregular_source` | The read target is no longer a regular nonlinked file. |
| 31 | `outside_source` | Resolved read target escapes the source root. |
| 32 | `source_io` | A table read raises an operating-system error. |
| 33 | `source_encoding` | A table read cannot decode its input. |
| 34 | `reader_value` | Reader rejects a value or layout. |
| 35 | `reader_csv` | CSV library rejects the input. |
| 36 | `unclassified_reader` | Other reader-library failure; exception text withheld. |
| 37 | `other_reader_refusal` | An unchanged reader refuses for another fixed reason. |
| 38 | `all_loaded_populations_below_floor` | Tables loaded but none has eleven verified people. |
| 39 | `output_unavailable` | Output directory does not exist. |
| 40 | `output_not_fresh` | Output directory already contains evidence; preserve it. |
| 41 | `output_inside_source` | Destination falls inside the source tree. |
| 42 | `invalid_bounds` | Invalid or expanded listing/read limits. |
| 43 | `internal_failure` | Unexpected probe failure; no exception text returned. |
| 44 | `output_refusal` | Existing aggregate writer refuses its output contract. |
| 45 | `status_schema` | Internal counters violate the fixed bounded status schema. |

## Admission and fixtures

Twenty-three constructed cases cover empty/archive-only sources, metadata without
a population denominator, distinct-person counting, small-cohort suppression,
missing keys, partial loads, read ceilings, both joined aliases, obsolete aliases,
path escapes, duplicate mappings, unknown keys, listing errors/truncation,
destination preservation, unclassified reader failures and the bounded metadata schema. These are component
checks. Twenty-two additional cases exercise the ratified exit-code and real-count
path, including every category, partial coverage, exact repeated-person counts,
all-small and mixed populations, unchanged aggregate limits, source privacy,
and a native child exit without diagnostic text. The original twenty-three
cases remain in the qualification roster. Actual manifest-layout fixtures and
in-image rehearsal remain required after the delivery. No joined-source
invocation has been made and the reset has not been consumed. A changed person
key in the incoming manifest requires a reviewed adapter, not an inferred key.

DESIGN CHECK: LESSONS 2-5 read. Under either scientific hypothesis, valid known
tables retain exact person counts; missing or malformed inputs produce explicit
diagnostic failures, never a null study. Listing counters are not people.
Incomplete listing or invalid mapping must prevent data reads. Every failure
condition and the all-tables-loaded state have an explicit disposition.
