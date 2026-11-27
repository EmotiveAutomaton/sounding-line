"""Return a reduced BF argument comparison on the original analytical populations."""
from pathlib import Path
from tempfile import TemporaryDirectory

import argument_bank as bank
import argument_panel as panel
from family_draws import family_index
from independent_release import Entry
from joined_source import take_snapshot
from r48_forms import choose
from week6_sealed_support_v1 import SealedFailure, write_tables
from week7_mib1 import reconstruct
from week7_mib3 import latest_trait_rosters


def forms(data, replay, families, repeat_families, known):
    groups, margins = bank.contributors(data)
    if (groups, margins) != bank.contributors(replay) or families != repeat_families:
        raise SealedFailure(14, 'Argument roster replay differs')
    # Emit statistics only on original, already-disclosed memberships. The
    # historical population catalog is reconstructed inside the same seal.
    eligible = {frozenset(g) for g in known if len(g) >= 11}
    estimates = {}
    for key, people in groups.items():
        related = margins if key == bank.ALL_REPORTS else ()
        if any(frozenset(g) not in eligible for g in (people, *related)):
            continue
        r, interval = bank.compare_branch(data, replay, people, key, families, repeat_families)
        if interval:
            estimates[key] = Entry(r, frozenset(people), tuple(map(frozenset, related)))
    def form(keys):
        if all(key in estimates for key in keys):
            return [(1, 'argument', [estimates[key] for key in keys])]
        return []
    # Original full form included outcome-free support and detailed margins.
    # These three new forms omit those counts and keep the original estimands.
    return {'fine':form((bank.WITHIN, bank.ALL_REPORTS, bank.SAME_DAY)),
            'coarse':form((bank.WITHIN, bank.ALL_REPORTS)),
            'summary':form((bank.ALL_REPORTS,))}


def run(mount, out, config):
    mapping = config['files']
    with TemporaryDirectory() as scratch:
        wave, paths = take_snapshot(Path(mount), Path(scratch), mapping,
                                    sum(v['bytes'] for v in mapping['M2'].values()))
        if wave != 'M2':
            raise SealedFailure(11, 'Wrong wave')
        previous = config['history']
        _, sets, groups = reconstruct(paths, previous, False)
        _, repeated, sources = reconstruct(paths, previous, True)
        if sets != repeated or groups != sources or any(len(sets[k]) != n for k,n in previous.items()):
            raise SealedFailure(14, 'Historic membership changed')
        extra = latest_trait_rosters(paths, config['sld4'])
        known = [groups['diary'], groups['survey'], *sets.values(), *extra.values()]
        routed = panel.support_plan(paths)
        panel.support_summary(routed)
        data, replica = panel.outcome_plan(paths, routed)
        allowed = choose(forms(data, replica, family_index(paths['survey']),
                                family_index(paths['survey']), known), groups['diary'], known)
        write_tables(out, allowed)
