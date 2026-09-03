"""Stage 7: the clean-room capability bridge (docs/design/PHASE_2_4_STAGE_7_CONTEXT.md).

Constructor, reader, and scorer are separated at the module AND process level (§14): the
constructor/ and scoring/ packages never enter a reader capsule; reader/ and contracts.py
are the only code a capsule holds, and they import nothing from the repository.
"""
