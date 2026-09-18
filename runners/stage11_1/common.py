"""Bounded continuation identity and immutable records.

DESIGN CHECK: LESSONS 2-5. NULL: inherited/private answers and prior costs cannot
become new observations or new authority. ALTERNATIVE: separate versioned records
bind the authorized branches to one absolute clock and cumulative ceilings.
"""
from pathlib import Path
from runners.stage11.core import read, freeze, digest, canonical

ROOT=Path('results/phase_2_4_stage_11_1')
PRIVATE=ROOT/'raw'
OLD=Path('results/phase_2_4_stage_11/raw')
BRANCH_LIMITS=dict(S1=1800,S2=1600,S3=1200,S4=1000,integration=800)


def allocation(root=PRIVATE):
    """Current explicit owner override; the original commissioning record stays intact."""
    return freeze(root/'ALLOCATION.json',dict(gear=2,cpu_threads=4,
        authority='Curator correction after Stage 11.1 setup: No, stay in gear two.',
        overrides='Initial Gear 1 default only; original branch/call/GPU/time limits remain.',
        gpu='one scientific owner at a time, short interruptible blocks',
        cooling='boost off; maximum 90 percent'))


def contract(root=PRIVATE):
    return freeze(root/'CONTRACT.json',dict(
        schema='stage11.1-contract-v1',commissioned_at='2026-09-18T16:18:24+00:00',
        clock_basis='First explicit new commissioning clock capture after brief orientation; fixed Sunday checkpoint is not extended.',
        reporting_starts='2026-09-20T13:00:00+00:00',checkpoint='2026-09-20T15:00:00+00:00',
        gear=1,cpu_threads=2,cooling='boost off; maximum 90 percent',
        maximum_attempts=6400,maximum_gpu_seconds=86400,branch_attempts=BRANCH_LIMITS,
        discovery_episodes=128,discovery_per_writer=8,breadth_episodes=128,
        account_variants=2,checkpoints_elapsed_hours=[4,12,24,36],
        historical_costs=dict(stage11_attempts=204,stage11_gpu_seconds=1584.7219638),
        authority='SOUNDING_LINE_STAGE_11_1_BRANCHING_STUDY_2026-09-18.md plus current commissioning instruction',
        closure='Sunday checkpoint, resource cap, or specific frontier/blocker report after admitted branches are exhausted; never first-screen completion alone'))
