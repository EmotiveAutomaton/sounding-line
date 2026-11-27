"""Receiver-side TP72 integration. Inputs, row memberships and scratch stay inside the seal."""
import csv
import json

from independent_release import Entry
from runners.drive.cards.week6_sealed_support_v1 import SealedFailure
from runners.drive.sealed import week7_tmp1_shell as shell
from runners.drive.sealed import week8_tmp2_source as original
from runners.drive.sealed.r48_forms import choose

HISTORY = frozenset(('traits.csv', 'channels.csv', 'contrast.csv', 'stability.csv',
                    'fixed_profile.csv', 'posts_needed.csv', 'matching.csv', 'growth.csv', 'curve_check.csv'))
CONVERSATION = frozenset(('conversation_affect.csv', 'conversation_traits.csv'))


def measured_exclusions(archives, pins, projection, components):
    groups = set(json.loads((projection / 'excluded_communities.json').read_text('utf8')))
    dropped = set()
    with original.selected(archives, pins, 'comments', ('subreddit', 'id', 'body')) as rows:
        for group, ident, text in rows:
            if group.strip().casefold() in groups:
                continue
            if original.TEST_NAMES.search(text) or original.reporting(text):
                if ident in dropped:
                    raise SealedFailure(22, 'Ambiguous dropped comment identity')
                dropped.add(ident)
    if len(dropped) != components[4][0]:
        raise SealedFailure(14, 'Exclusion replay disagrees with the measured count')
    return groups, dropped


def select_tables(mode, directory, contract, memberships, universe, known):
    expected = {'history': HISTORY, 'conversation': CONVERSATION}[mode]
    if set(contract) != expected:
        raise SealedFailure(14, 'Unregistered TP72 table set')
    if directory.is_dir() and not any(directory.iterdir()):
        raise SealedFailure(12, 'No eligible TP72 table')
    shell.check_tables(directory, contract)
    originals = []
    observed = set()
    fine, coarse, summary = [], [], []
    for index, path in enumerate(sorted(directory.iterdir()), 1):
        header = contract[path.name][0]
        label_fields = header[:header.index('n')]
        entries = []
        pooled = []
        with path.open(encoding='utf8', newline='') as stream:
            for row in csv.DictReader(stream, strict=True):
                labels = tuple(row[k] for k in label_fields)
                key = path.name, labels
                people = memberships.get(key)
                if (key in observed or people is None or len(people) != int(row['n'])
                        or not people <= universe):
                    raise SealedFailure(14, 'Cell cannot be reconciled with its observed contributors')
                observed.add(key)
                entry = Entry(dict(index=len(originals), n=len(people), estimate=float(row['value']),
                                   lower=float(row['lo']), upper=float(row['hi'])), people)
                originals.append(row)
                entries.append(entry)
                if (key == ('contrast.csv', ('diagonalMinusOther',))
                        or key == ('conversation_affect.csv', ('worry', 'affect'))):
                    pooled.append(entry)
        table = index, path.name, entries
        fine.append(table)
        if path.name in ('traits.csv', 'contrast.csv', 'channels.csv', 'conversation_affect.csv'):
            coarse.append(table)
        if pooled:
            summary.append((index, path.name, pooled))
    if observed != set(memberships):
        raise SealedFailure(14, 'Producer observation differs from its written cells')
    selected = choose(dict(fine=fine, coarse=coarse, summary=summary), universe, known)
    return {name: [originals[row['index']] for row in chosen] for name, chosen in selected.items()}


def receive(mode, dest, contract, universe, known, run_producer):
    """Run a separately authenticated producer with its documented person-roster callback."""
    memberships = {}

    def observe(name, labels, people):
        key = name, tuple(labels)
        if key in memberships or not isinstance(people, frozenset):
            raise SealedFailure(14, 'Ambiguous producer membership')
        memberships[key] = people

    run_producer(dest, observe)
    return select_tables(mode, dest, contract, memberships, universe, known)


def history(archives, pins, scratch, producer, frozen, contract, check, known):
    """Project the original archives under DJ and pass measured exclusion sets to TP72."""
    projection = scratch / 'clean'
    universe, parts = original.filter_histories(archives, pins, scratch, projection)
    if parts[1][0] < 11:
        raise SealedFailure(12, 'No eligible history roster')
    groups, dropped = measured_exclusions(archives, pins, projection, parts)
    try:
        counts = original.count_table(universe, parts)['counts']
    except SealedFailure as exc:
        if exc.code != 12:
            raise
        counts = []
    previous = [*known, parts[0][1], parts[1][1], *(parts[r['measure'] - 1][1] for r in counts)]
    def run(dest, observe):
        producer.history(projection, dest, frozen, check, observe, excluded=groups, dropped=dropped)
    return receive('history', scratch/'producer', contract, universe, previous, run)


def conversation(speakers, scratch, producer, frozen, contract, check, universe, known):
    """Use the receiver's reciprocal conversation projection and authenticated survey universe."""
    def run(dest, observe):
        producer.conversation(speakers, dest, frozen, check, observe)
    return receive('conversation', scratch/'producer', contract, universe, known, run)
