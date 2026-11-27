"""In-seal selection of one previously registered release form, finest first."""
from independent_release import decide
from week6_sealed_support_v1 import SealedFailure


def choose(forms, universe, known):
    if tuple(forms) != ('fine', 'coarse', 'summary'):
        raise SealedFailure(14, 'Three ordered release forms required')
    for form, candidate in forms.items():
        if not candidate:
            continue
        if form == 'summary' and (len(candidate) != 1 or len(candidate[0][2]) != 1):
            raise SealedFailure(14, 'Summary must be one pooled estimate')
        for _, _, entries in candidate:
            for entry in entries:
                if entry.fields.get('n') != len(entry.people):
                    raise SealedFailure(14, 'Distinct-person count mismatch')
                if form == 'summary' and not {'estimate','lower','upper'} <= entry.fields.keys():
                    raise SealedFailure(14, 'Incomplete pooled summary')
        allowed, _ = decide(candidate, universe, known)
        if all(entries and len(allowed.get(name, ())) == len(entries) for _,name,entries in candidate):
            return allowed
    raise SealedFailure(12, 'No independently disclosable form')
