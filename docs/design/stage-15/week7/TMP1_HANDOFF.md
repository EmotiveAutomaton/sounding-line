# TMP1 before the TP58 handoff

## Receiver inspection on November 23

The engine recorded Sounding Line’s rehearsal request. Q21 supplies the fitted PRIDE head required by TP58. The producer sheet still lists construction, offline rehearsal and delivery as pending. On Spark, Q18 advanced from 4,919 to 5,179 of 7,666 rows between 04:33 and 04:38 Pacific. The worker and weekly dispatcher matched their recorded native identities. The workstation handoff and readout supervisors were live. [Producer sheet at the inspected revision](https://github.com/EmotiveAutomaton/tompathy/blob/3f2e4cb56da1c3906fec0d16338c0bda6ff89156/docs/exchange/result-sheets/TP58.md).

Sounding Line watches the producer sheet for revisions through the Week 7 freeze. Its starting SHA-256 is `6623d61f6361fa33babb1177ef72af01bfc9ba59a94bf446d73c5aae005750ff`. A revision signals the existing owner watcher for review. A constructed two-revision check verified that an unchanged sheet generates no duplicate. The delivered bundle still requires independent manifest review, file verification and rehearsal. [Delivery monitor](../../../../tools/watch_tp58_delivery.ps1).

All four receiver shell and release-gate tests passed on November 23. The local Docker Linux engine pipe was still unavailable. Target-image verification and the made-text rehearsal of the engine bundle remain pending.

## Receiver protocol

The curator confirmed on November 22 at 11:20 Pacific that the engine is building TP58 this week. Delivery follows the curator’s storage handback under CF. TMP1 retains its position between LGH2 and SLD2 in the sealed queue.

The [job shell](../../../../runners/drive/sealed/week7_tmp1_shell.py) currently permits only an image check. In the target Linux image it verifies that loopback is the sole network interface, checks for exposed accelerator and fabric devices, and exercises CPU array arithmetic. The runner must also enforce its installed network isolation, CPU-only device configuration and read-only mounts. Exit 0 in image-check mode means those in-image checks passed. Exit 20 means they could not be verified. The study entry exits 21 after a successful image check and writes nothing. The output table list is empty.

The [local checks](../../../../tests/test_week7_tmp1_shell.py) exercise the shell and output validator on literal CSV rows. They check minimum participant support, interval order, allowed fields and labels, file sizes, row counts and the separate installed-gate mirror. These fixtures exercise the release contract only. The engine owns the reader, the substantive table definitions and the bar.

At handoff, record the independently reviewed manifest digest and verify the complete set of delivered payload files and every SHA-256 value. Review the reader’s selection of trait-scored histories, exclusion of the collection communities and omission of demographic columns. Bind only the exact TP58 table names, columns, interval roles and finite label sets. Confirm that each row’s count measures distinct contributing people. The sealed job must publish validated aggregate tables from private scratch through the installed gate. All returned rows require intervals and real participant counts of at least 11. Rehearse the hash-verified reader on made text, inspect outputs against those definitions, and pin the exact candidate before the first research invocation. Image dependencies, if needed, follow CM’s offline file and provenance rule.

The workstation check found the local Docker Linux engine pipe absent. Actual execution of the target image remains unverified for this shell. Its no-data smoke command, once an approved local image is available, is `docker run --pull=never --rm --network none --read-only --cap-drop ALL -e CUDA_VISIBLE_DEVICES= -e OPENBLAS_NUM_THREADS=2 -e OMP_NUM_THREADS=2 -v <absolute-shell-path>:/job/run.py:ro <reviewed-image-id> python3 -B /job/run.py --check-image`. A fabricated reader or a successful local unit test cannot supply the real-bundle rehearsal.
