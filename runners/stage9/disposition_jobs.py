"""Carry a manually reviewed not-run decision through the actual Stage 9 queue.

DESIGN CHECK: I01/B03/B04; LESSONS 3--5, CONTROLS 6--7.
NULL: an empty reason, changed evidence, omitted prior failures, unknown card or
attempted scientific score refuses the receipt. ALTERNATIVE: the reviewed reason
and exact evidence survive execution and immutable reentry. Queue completion
records this operation's execution; the study remains NOT RUN WITH REASON.
The operator judges the evidence. This handler cannot invent a reason, choose a
study, turn a failed prerequisite into admission, or create a scientific score.
"""
import argparse
import copy
import time
from pathlib import Path

from .cards import BY_ID
from .common import REPO, ROOT, Units, digest, file_hash, freeze, read
from .launch import checked
from .queue import inside, writer
from .revision_predictions import sources, reentry, finish
from .training_jobs import cell_identity

KINDS = {'source_unavailable', 'failed_prerequisite', 'unsupported_measurement',
         'budget_unavailable', 'no_eligible_claim'}
FIELDS = {'card', 'kind', 'scope', 'reason', 'evidence', 'retained_failures',
          'finding', 'next_obligation'}


def validate_decision(decision, card):
    if not isinstance(decision, dict) or set(decision) != FIELDS:
        raise ValueError('exact reviewed not-run decision fields required; no scores')
    if card not in BY_ID or decision['card'] != card or decision['kind'] not in KINDS:
        raise ValueError('unknown or mismatched not-run card or reason kind')
    for key in ('scope', 'reason', 'finding', 'next_obligation'):
        if not isinstance(decision[key], str) or not decision[key].strip():
            raise ValueError('not-run decision needs a nonempty ' + key)
    evidence = decision['evidence']
    if (not isinstance(evidence, dict) or not evidence
            or any(not isinstance(k, str) or not k.strip() for k in evidence)):
        raise ValueError('not-run decision needs named evidence')
    failures = decision['retained_failures']
    if (not isinstance(failures, list) or any(not isinstance(k, str) for k in failures)
            or len(failures) != len(set(failures)) or not set(failures) <= set(evidence)):
        raise ValueError('retained failures must name distinct included evidence')
    if decision['kind'] == 'failed_prerequisite' and not failures:
        raise ValueError('failed prerequisite requires its original failure evidence')
    for pointer in evidence.values():
        if not isinstance(checked(pointer), dict):
            raise ValueError('not-run evidence must be an object receipt')
    return {**copy.deepcopy(decision), 'hypothesis': BY_ID[card].hypothesis,
            'disposition': 'NOT RUN WITH REASON', 'scientific_execution': False,
            'scientific_admission': False, 'scientific_launch_accepted': False,
            'public_claim': 'unchanged', 'review_owner': 'coding_operator',
            'meaning': 'manual evidence-backed disposition; no scientific outcome estimated'}


def run(directory, decision_path, card, scope):
    start, cpu = time.monotonic(), time.process_time()
    directory, decision_path = inside(directory), inside(decision_path)
    if (scope not in ('pilot', 'scientific') or card not in BY_ID
            or scope == 'pilot' and not directory.is_relative_to(ROOT / 'private/disposition-pilots')
            or scope == 'scientific' and directory != ROOT / card):
        raise ValueError('not-run output differs from its explicit card/scope')
    raw = read(decision_path)
    disposition = validate_decision(raw, card)
    identity = {'cell_identity': cell_identity(), 'operation': 'not-run-' + card,
                'scope': scope, 'source': sources(), 'card': card,
                'decision_path': str(decision_path.relative_to(REPO)),
                'decision_sha256': file_hash(decision_path), 'evidence': raw['evidence']}
    with writer(directory):
        Units(directory, identity)
        prior = reentry(directory, identity)
        if prior is not None:
            if read(directory / 'DISPOSITION.json') != disposition:
                raise ValueError('completed not-run disposition differs from reviewed evidence')
            return prior
        freeze(directory / 'DISPOSITION.json', disposition)
        # Revalidate external evidence before committing this whole operation.
        if file_hash(decision_path) != identity['decision_sha256']:
            raise ValueError('reviewed not-run decision changed during execution')
        validate_decision(raw, card)
        return finish(directory, identity, start, cpu, ['DISPOSITION.json'],
                      card=card, disposition='NOT RUN WITH REASON', accepted=False,
                      scientific_execution=False, scientific_launch_accepted=False,
                      public_claim='unchanged', scored_units=0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--decision', type=Path, required=True)
    parser.add_argument('--card', choices=sorted(BY_ID), required=True)
    parser.add_argument('--scope', choices=('pilot', 'scientific'), required=True)
    args = parser.parse_args()
    run(args.output, args.decision, args.card, args.scope)
