# Joined-source SM0 recovery

The owner-reviewed collector manifest supplies two loose SPSS files per joined
wave. `build.py` embeds the exact four probe modules and the reviewed mappings
into fresh, self-contained jobs. It does not upload, invoke Spark or read data.
The real jobs use only the joined aliases and the ratified v3 exit-code path;
the installed sealed runner and gate remain unchanged.

`fixture.py` reproduces the four mapped filenames and formats using made-up
people. Ten cases check both wave layouts, repeated-person counts, suppressed
populations, partial/missing-key loads, empty/archive-only input and read bounds.
An audit hook refuses private-source opens and enumeration. Local counted
qualification precedes the identical in-image rehearsal; real probes follow
only after both pass. All outputs retain the existing person-count gate.

See `docs/design/stage-15/week6/SM0_JOINED_LAYOUT_V1.md` for manifest provenance,
mapping limits and the one-time reset. No scientific source is admitted by SM0.
