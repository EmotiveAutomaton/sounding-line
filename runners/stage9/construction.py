"""Preparation/evaluation construction and continuation from actual learner states.

DESIGN CHECK: Stage 9 C01/C05/C06/X08; existing executable law is the authority.
NULL: resetting elapsed steps, previous action, goals or changed context disagrees with
the original executor on expert prefixes. ALTERNATIVE: state and policy match exactly.
Off-policy legality and policy probability are separate. This module never runs inside
an artifact reader and never passes the world object through the reader boundary.
"""
import ast
import copy
import math
import random

from runners.stage7.constructor import worlds as W
from runners.stage7.reader import law as LAW
from runners.stage8.constructor import population as POP
from runners.stage8.constructor import purpose as PURPOSE
from runners.stage8.reader import logfmt as LF
from runners.stage9.common import REPO, digest, file_hash


def secondary_laws():
    """Read the reviewed literal without importing the monolithic old stage engine."""
    path = REPO / 'runners/stage8/engines.py'
    tree = ast.parse(path.read_text(encoding='utf-8'))
    values = [ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id == 'LAWS2' for t in n.targets)]
    if len(values) != 1 or set(values[0]) != {'novice2', 'editor2', 'scholar2'}:
        raise ValueError('secondary law literal changed shape')
    return values[0], {'source': str(path.relative_to(REPO)), 'sha256': file_hash(path), 'operation': 'AST literal only; no source execution'}


def register():
    PURPOSE.register()
    laws, receipt = secondary_laws()
    for name, value in laws.items():
        if name in W.LAWS and W.LAWS[name] != value:
            raise ValueError('different existing secondary law')
        W.LAWS.setdefault(name, value)
    return receipt


class Replay:
    """Replay objective outcomes even when the action has zero teacher probability.

    Visibly legal actions absent from the original inventory can be introduced at the
    time they occur. The extension and its changed denominator are explicitly logged;
    this is a Stage 9 distribution, not the historical broad-admission distribution.
    Invalid actions raise before any state mutation; their attempts belong in the
    caller's failure receipt, not in a fabricated training continuation.
    """
    def __init__(self, world, prefix=(), extend_visible=False):
        self.world = world
        self.initial = copy.deepcopy(world['state'])
        self.c_ext = copy.deepcopy(self.initial['external_context'])
        self.belief = copy.deepcopy(self.initial['belief_state'])
        self.law = self.initial['expertise_law']
        self.residue = self.initial['history_residue']
        self.pending = copy.deepcopy(world['inventory'])
        self.inventory = copy.deepcopy(world['inventory'])
        self.sections = {s['name']: s['slots'] for s in world['doc']['sections']}
        self.goal_name = self.initial['proximal_goal']['name_ref']
        self.goal_last = self.goal_name
        self.last_type = None
        self.steps, self.done, self.extensions = [], set(), []
        self.extend_visible = extend_visible
        self.changes = [tuple(change) for change in world['trajectory'].get('changes', [])]
        self._change(0)
        for event in prefix:
            self.apply(event, verify_outcome=True)

    def _change(self, boundary):
        for when, kind in self.changes:
            if when == boundary:
                self.c_ext, self.belief = LAW.apply_change(self.c_ext, self.belief, kind)

    def snapshot(self):
        goal = LAW.next_goal(self.goal_name, self.pending, list(W.GOALS))
        context = LAW.maker_context(self.c_ext, self.belief, self.law)
        subjective = LAW.subjective_options(self.pending, context, self.belief, self.law)
        return {'external_context': copy.deepcopy(self.c_ext), 'belief_state': copy.deepcopy(self.belief),
                'expertise_law': copy.deepcopy(self.law), 'maker_context': context,
                'subjective_action_space': [LAW.action_id(a) for a in subjective],
                'proximal_goal': W._goal(goal), 'goal_last': self.goal_last,
                'history_residue': copy.deepcopy(self.residue), 'persistent_tendency': self.initial['persistent_tendency'],
                'pending': copy.deepcopy(self.pending), 'names': copy.deepcopy(self.initial['names'])}

    def probabilities(self):
        state = self.snapshot()
        opts = [a for a in self.pending if LAW.action_id(a) in state['subjective_action_space']]
        if not opts:
            return {'stop': 1.0}
        pol = LAW.policy(opts, state['proximal_goal'], self.law, self.residue, state['maker_context'],
                         list(self.sections), self.last_type, len(self.steps))
        hazard = 0.0
        if self.steps:
            remaining = [a for a in self.pending if a['goal_owner'] == self.goal_last]
            hazard, _ = LAW.stop_hazard(not remaining, len(self.done) / len(self.inventory), len(self.steps), self.law, state['maker_context'])
        return {'stop': hazard, **{k: (1 - hazard) * p for k, p in pol.items()}}

    def legal_actions(self):
        fixed = {'consult': 'src', 'cite': 'ref', 'restructure': 'order', 'probe': 'tech'}
        actions = []
        for section, slots in self.sections.items():
            for kind in LAW.ACTION_TYPES:
                for slot in ([fixed[kind]] if kind in fixed else slots):
                    action = {'type': kind, 'section': section, 'slot': slot}
                    if LAW.action_id(action) not in self.done:
                        action['outcome'] = 'done' if all(self.c_ext['tools'].get(t, False) for t in POP.TYPE_REQUIRES.get(kind, [])) else 'failed'
                        actions.append(action)
        return actions

    def apply(self, event, verify_outcome=True):
        if event.get('i', len(self.steps)) != len(self.steps):
            raise ValueError('event clock does not continue the actual prefix')
        if not {'type', 'section', 'slot'} <= event.keys():
            raise ValueError('incomplete action')
        aid = LAW.action_id(event)
        legal = {LAW.action_id(a): a for a in self.legal_actions()}
        if aid not in legal:
            raise ValueError('invalid visible action or repeated completed action')
        outcome = legal[aid]['outcome']
        if verify_outcome and event.get('outcome', outcome) != outcome:
            raise ValueError('claimed outcome differs from objective execution')
        action = next((a for a in self.pending if LAW.action_id(a) == aid), None)
        if action is None and not self.extend_visible:
            raise ValueError('action outside the declared inventory')
        self.goal_name = LAW.next_goal(self.goal_name, self.pending, list(W.GOALS))
        self.goal_last = self.goal_name
        if action is None:
            owner = self.goal_name if self.goal_name in PURPOSE.PURPOSES else POP.TYPE_OWNER[event['type']]
            action = {k: event[k] for k in ('type', 'section', 'slot')}
            action.update(requires=list(POP.TYPE_REQUIRES.get(event['type'], [])), goal_owner=owner)
            self.pending.append(action)
            self.inventory.append(action)
            self.extensions.append({'at_step': len(self.steps), 'action': copy.deepcopy(action)})
        if outcome == 'done':
            self.pending = [a for a in self.pending if LAW.action_id(a) != aid]
            self.done.add(aid)
        else:
            for tool in action['requires']:
                self.belief['believed_tools'][tool] = bool(self.c_ext['tools'].get(tool, False))
        self.last_type = event['type']
        actual = {'i': len(self.steps), 'type': event['type'], 'section': event['section'], 'slot': event['slot'],
                  'outcome': outcome, 'goal': self.goal_name, 'goal_owner': action['goal_owner']}
        self.steps.append(actual)
        self._change(len(self.steps))
        return actual

    def continue_teacher(self, seed, max_events=40):
        if max_events < len(self.steps):
            raise ValueError('continuation horizon is before the current state')
        rng, result = random.Random(seed), []
        while len(self.steps) < max_events:
            probabilities = self.probabilities()
            u, selected = rng.random(), None
            for aid, probability in sorted(probabilities.items()):
                u -= probability
                if u <= 0:
                    selected = aid
                    break
            selected = selected or sorted(probabilities)[-1]
            if selected == 'stop':
                return result, True
            action = next(a for a in self.pending if LAW.action_id(a) == selected)
            result.append(self.apply(action, verify_outcome=False))
        return result, False


def rendered_prefix(world, events, with_goal=False):
    c = world['state']['external_context']
    head = LF.header(world['doc']['topic'], c['audience'], c['tools'], c['deadline'], world['doc']['sections'],
                     world['state']['proximal_goal']['name_ref'] if with_goal else None)
    return LF.compose([], head, [LF.event_line(i, e['type'], e['section'], e['slot'], e['outcome']) for i, e in enumerate(events)])
