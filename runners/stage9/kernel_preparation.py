"""Evaluator-side explicit supplied-program projection; never imported in a capsule.

DESIGN CHECK: I06. This is privileged numeric-state diagnostic input, not an artifact.
Only the named operative fields survive. Source lineage and hidden target stay outside.
"""
import copy

from runners.stage9.construction import W
from runners.stage9.kernel import RULES, VERSION, validate


def supplied_program(replay):
    state = replay.snapshot()
    goal = state['proximal_goal']['name_ref']
    goals = {g: dict(W._goal(g)['utility']) for g in W.GOALS}
    goals[goal] = dict(state['proximal_goal']['utility'])
    program = {'version': VERSION, 'rules': copy.deepcopy(RULES), 'context': state['external_context'],
               'belief': state['belief_state'], 'law': state['expertise_law'], 'history': state['history_residue'],
               'goal_name': goal, 'goal_last': replay.goal_last, 'goal_order': list(W.GOALS), 'goal_utilities': goals,
               'pending': copy.deepcopy(replay.pending), 'inventory_size': len(replay.inventory),
               'done_ids': sorted(replay.done), 'sections': list(replay.sections),
               'last_type': replay.last_type, 'step': len(replay.steps)}
    validate(program)
    return program
