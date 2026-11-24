"""Whole-roster binding for the Week 7 sealed returns.

Inputs to this routine are reconstructed inside the sealed job. The caller must
authenticate each public key and count against the archived release first.
"""
def largest_released_roster(published_counts, reconstructed, supported):
    candidates = []
    for code, expected_n in published_counts.items():
        if code not in reconstructed:
            raise ValueError("Missing previously released roster")
        people = frozenset(reconstructed[code])
        if len(people) != expected_n:
            raise ValueError("Changed roster count")
        if expected_n >= 11 and people.issubset(supported):
            candidates.append((code, people))
    if not candidates:
        return None
    return min(candidates, key=lambda candidate: (-len(candidate[1]),candidate[0]))
