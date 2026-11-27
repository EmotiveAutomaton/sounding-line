"""Run the authenticated TP58 reader on the DJ projection and release eligible aggregates."""
import csv
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import sys

from independent_release import Entry
from runners.drive.cards.week6_sealed_support_v1 import SealedFailure
from runners.drive.sealed import week7_tmp1_shell as shell
from runners.drive.sealed import week8_tmp2_source as source
from runners.drive.sealed.r48_forms import choose


def capture(roster, producer, projection, destination):
    """Observe the actual authors fed to the unchanged registered calculations."""
    traits, learning = producer.trait_tables, producer.learning_tables

    def observe_traits(scores, labels, output):
        roster['traits'] = frozenset(scores)
        return traits(scores, labels, output)

    def observe_learning(frames, deep, output):
        for split_size, frame in frames.items():
            roster[split_size] = frozenset(frame)
        return learning(frames, deep, output)

    with patch.object(producer, 'trait_tables', observe_traits), patch.object(producer, 'learning_tables', observe_learning):
        producer.run(projection, destination)


def contributing(name, row, roster):
    if name in ('traits.csv', 'contrast.csv', 'channels.csv'):
        return roster['traits']
    if name in ('fixed_profile.csv', 'posts_needed.csv'):
        return roster[row['split'], 5]
    size = int(row['k'])
    group = roster[row['split'], size]
    if name in ('growth.csv', 'curve_check.csv'):
        return group & roster[row['split'], 5]
    if name in ('matching.csv', 'stability.csv'):
        return group
    raise SealedFailure(14, 'Unknown table membership')


def gated_tables(directory, contract, roster, universe, components):
    shell.check_tables(directory, contract)
    try:
        counts = source.count_table(universe, components)['counts']
    except SealedFailure as exc:
        if exc.code != 12:
            raise
        counts = []
    known = [components[r['measure'] - 1][1] for r in counts]
    known.extend([components[0][1], components[1][1]])
    tables = {}
    originals = []
    for file in sorted(directory.iterdir()):
        with file.open(encoding='utf8', newline='') as stream:
            table = []
            for row in csv.DictReader(stream, strict=True):
                people = contributing(file.name, row, roster)
                if len(people) != int(row['n']):
                    raise SealedFailure(14, 'Reader support differs from the actual contributing cohort')
                index = len(originals)
                originals.append(row)
                table.append(Entry(dict(index=index, n=len(people), estimate=float(row['value']),
                                        lower=float(row['lo']), upper=float(row['hi'])), people))
            tables[file.name] = table
    fine = [(i, name, entries) for i,(name, entries) in enumerate(tables.items(),1)]
    coarse = [t for t in fine if t[1] in ('traits.csv','contrast.csv','channels.csv')]
    summary = [t for t in coarse if t[1]=='contrast.csv']
    selected = choose(dict(fine=fine, coarse=coarse, summary=summary), universe, known)
    return {name:[originals[row['index']] for row in records] for name, records in selected.items()}


def calculate(archives, scratch, config, producer, contract):
    projection = scratch / 'clean'
    universe, components = source.filter_histories(archives, config['files'], scratch, projection)
    if components[1][0] < 11:
        raise SealedFailure(12, 'Insufficient retained contributors')
    roster = {}
    dest = scratch / 'producer'
    capture(roster, producer, projection, dest)
    if not dest.is_dir() or not any(dest.iterdir()):
        raise SealedFailure(12, 'No registered table')
    return gated_tables(dest, contract, roster, universe, components)


def run(root, out, config):
    if config['real_image']:
        shell.check_image()
    if root.is_symlink() or {p.name for p in root.iterdir()} != {'payload', 'projection'}:
        raise SealedFailure(21, 'Incorrect combined source')
    payload = root / 'payload'
    archives = root / 'projection'
    shell.verify_bundle(payload, config['payload'])
    source.verify(archives, config['files'])
    sys.path.insert(0, str(payload))
    try:
        import run as producer
        import tables as tables_module
        for module in (producer, tables_module):
            if Path(module.__file__).resolve().parent != payload.resolve():
                raise SealedFailure(21, 'Different reader loaded')
        contract = tables_module.contracts()
        first = None
        for _ in range(2):
            with TemporaryDirectory(prefix='tmp2-reader-') as path:
                reading = calculate(archives, Path(path), config, producer, contract)
            if first is None:
                first = reading
            elif first != reading:
                raise SealedFailure(14, 'Independent projection or reader replay differs')
        with TemporaryDirectory(prefix='tmp2-approved-') as folder:
            staging = Path(folder)
            for name, rows in first.items():
                with (staging / name).open('x', encoding='utf8', newline='') as stream:
                    writer = csv.DictWriter(stream, fieldnames=contract[name][0], lineterminator='\n')
                    writer.writeheader()
                    writer.writerows(rows)
            shell.check_tables(staging, contract)
            for file in sorted(staging.iterdir()):
                with (out / file.name).open('xb') as dest:
                    dest.write(file.read_bytes())
    finally:
        sys.path.remove(str(payload))
