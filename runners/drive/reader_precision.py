"""Exact alignment before comparing two teacher-forced implementations.

DESIGN CHECK: LESSONS 3-5. NULL: short, empty or nonfinite vectors refuse;
ALTERNATIVE: equal complete vectors have zero discrepancy. No tolerance change.
"""
import math

def discrepancy(reference,cached):
    if not reference or len(reference)!=len(cached):raise ValueError('cache/reference token alignment')
    if not all(math.isfinite(x) for x in [*reference,*cached]):raise ValueError('nonfinite cache/reference')
    return max(abs(a-b) for a,b in zip(reference,cached))
