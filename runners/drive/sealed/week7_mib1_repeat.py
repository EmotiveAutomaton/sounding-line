"""Repeat the four MI1 contrasts on a previously released M2 roster at M3.

All membership comparisons and the family lookup stay inside the sealed process.

DESIGN CHECK (2026-11-26)
Lessons read: LESSONS §2 (source roster and study population), §3 (independent verification), and §5 (immutable dependencies).
Gates, null/alternative/direction: four original file hashes, the diary row
and person counts, cross-wave person binding, and agreement between observed
family links must hold under the null and under the alternative. A changed
edition or conflicting link must stop before fitting. A candidate roster must
match a released count by reconstructed membership, and every member must
contribute in both waves. Losing even one member voids that candidate under
either hypothesis. Independent decodes and draws must agree under either
hypothesis; disagreement stops the return. The sealed disclosure rule
withholds unsafe memberships regardless of coefficient direction.
Verdict bands per arm, exhaustive: an eligible identifiable contrast can
have its entire interval above zero, its entire interval below zero, or an
interval containing zero including either endpoint. Missing family linkage
or an invalid draw can leave a point without an interval. An unidentified
point has no direction. No eligible roster gives code 32 with empty output.
Source or replay failures and withheld rows give no scientific verdict.
"""
from pathlib import Path
from tempfile import TemporaryDirectory

import pyreadstat
import aggregate_register_v1 as register
import mi_source_contract_v1 as contract
from bm_numeric import numerical_outputs
from family_draws import family_index, positive_integer
from independent_release import Entry, decide
from joined_source import take_snapshot
from panels import plan
from science_entry import inspect_tables, read_available, MAX_PRIVATE_BYTES
from sealed_io_v1 import selected_columns
from table_support import supported_columns
from week6_sealed_support_v1 import SealedFailure, write_tables
from week7_mib1 import reconstruct, bind
from week7_mib3 import latest_trait_rosters


def check_diary(path, expected):
    frame, _ = pyreadstat.read_sav(str(path), usecols=['M2ID'], user_missing=False)
    people = {positive_integer(value) for value in frame['M2ID']}
    if None in people or (len(frame), len(people)) != tuple(expected):
        raise SealedFailure(11, 'Repeat diary count or key differs')


def run(mount, out, source_map, published, trait_releases, diary_counts):
    if set(source_map) != {'M2', 'M3'} or any(set(rows) != {'diary', 'survey'} for rows in source_map.values()):
        raise SealedFailure(11, 'Combined source roles differ')
    total = sum(f['bytes'] for records in source_map.values() for f in records.values())
    if total > MAX_PRIVATE_BYTES:
        raise SealedFailure(13, 'Source exceeds read bound')
    with TemporaryDirectory(prefix='mib-repeat-') as temp:
        paths, fields = {}, {}
        for wave, records in sorted(source_map.items()):
            dest = Path(temp) / wave
            dest.mkdir()
            actual, paths[wave] = take_snapshot(Path(mount), dest, source_map,
                sum(f['bytes'] for f in records.values()), combined_wave=wave)
            if actual != wave:
                raise SealedFailure(11, 'Wrong wave')
            fields[wave] = {role: selected_columns(wave + '_' + suffix, contract.fields)
                            for role, suffix in [('diary','P2'),('survey','P1')]}
        check_diary(paths['M3']['diary'], diary_counts)
        _, measured, groups = inspect_tables(paths, fields, 'M3')
        if 'MI1' not in supported_columns(measured, 'M3'):
            raise SealedFailure(11, 'Missing registered fields')
        family2 = family_index(paths['M2']['survey'])
        family3 = family_index(paths['M3']['survey'])
        if family2 is None or family3 is None:
            raise SealedFailure(11, 'Family linkage field unavailable')

        complete_counts = dict(published)
        for trait, counts in trait_releases.items():
            complete_counts.update({trait+'/'+key: count for key,count in counts.items()})

        def prepare(reference):
            _, historical, _ = reconstruct(paths['M2'], published, reference)
            historical.update(latest_trait_rosters(paths['M2'], trait_releases))
            tables = {w:read_available(paths[w], fields[w], measured[w]) for w in paths}
            panels, _ = plan(tables, 'M3', reference, ('MI1',), measured)
            # A roster that was disclosed at wave two must be eligible in BOTH waves.
            return historical, panels

        first, panels = prepare(False)
        second, replay_panels = prepare(True)
        if first != second:
            raise SealedFailure(14, 'Independent historical roster differs')
        # Check eligibility and whole-roster selection independently even on a void.
        def select(panels, rosters):
            try:
                return bind(complete_counts, rosters, panels, 'MI1')
            except SealedFailure as exc:
                if exc.code != 32:
                    raise
                return None
        selection = select(panels, first)
        replica = select(replay_panels, second)
        if selection is None and replica is None:
            raise SealedFailure(32, 'No eligible released roster')
        if selection is None or replica is None:
            raise SealedFailure(14, 'Independent repeat selection differs')
        key, roster, people, related = selection
        other_key, other_roster, others, other_related = replica
        if (key, roster, related) != (other_key, other_roster, other_related):
            raise SealedFailure(14, 'Independent repeat selection differs')
        for person in roster:
            a, b = family2.get(person), family3.get(person)
            if a is not None and b is not None and a != b:
                raise SealedFailure(11, 'Conflicting family linkage')
        tables = numerical_outputs({'MI1': (people, others, roster, related)},
            family2, family_index(paths['M2']['survey']))
        parameters = {i for i,(_,role,_) in enumerate(register.columns('MI1'),1) if role == 'primary'}
        protected = [*first.values(), groups['M2']['diary'], groups['M2']['survey'], groups['M3']['survey']]
        catalogue = [(i,name,[Entry(row,roster,tuple(related)) for row in rows if row['parameter'] in parameters])
                     for i,(name,rows) in enumerate(sorted(tables.items()),1)]
        allowed,_ = decide(catalogue,groups['M3']['diary'],protected)
        if not allowed:
            raise SealedFailure(12, 'Repeat disclosure withheld')
        return write_tables(out,allowed)
