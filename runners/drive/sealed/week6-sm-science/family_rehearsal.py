"""Joined-source rehearsal for the entirely artificial MIDUS family fixture."""
from math import fsum
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

import daily_fixture as fixture
from science_entry import run_joined
from week6_sealed_support_v1 import write_tables


def argument_answers():
    """Derive BF's three known points from the planted schedule, without the estimators."""
    paired, pooled = [], [[], []]
    for pattern, times in enumerate(fixture.HISTORIES):
        for response in range(4):
            scores = []
            for day, char in enumerate(times):
                current = int(char)
                last = int(times[day-1]) if day else 0
                negative = (response+day)%4 < (1+current+last)
                scores.append(fsum(1+(j+pattern+response)%4 for j in range(14)
                                   if negative and (j==0 or (pattern+day+j)%3!=0))/14)
            clear = [score for score, exposure in zip(scores,times) if exposure=="0"]
            baseline = fsum(clear)/len(clear)
            next_values, today = [[], []], [[], []]
            for day in range(len(times)-1):
                if times[day]=="1":
                    kind=(pattern+day)%2
                    next_values[kind].append(scores[day+1]-baseline)
                    today[kind].append(scores[day]-baseline)
            for kind,values in enumerate(next_values):
                pooled[kind].extend(values)
            if all(next_values):
                paired.append([np.mean(values[1])-np.mean(values[0]) for values in (next_values,today)])
    n = len(paired)*fixture.COPIES
    within,same = np.mean(paired,axis=0)
    return n, [within, np.mean(pooled[1])-np.mean(pooled[0]), same]


def verify(tables):
    n = fixture.check_known(tables)
    paired, expected=argument_answers()
    rows=sorted(tables.get("argument_estimates",[]),key=lambda row:row["comparison"])
    if [row["comparison"] for row in rows]!=[1,2,3]:
        raise ValueError("Complete argument estimates required on the constructed source")
    if [row["n"] for row in rows]!=[paired,n,paired] or any(
            row["resampling"]!=2 or row["valid_draws"]!=2000 for row in rows):
        raise ValueError("Constructed argument denominator or family bank differs")
    if not np.allclose([row["estimate"] for row in rows],expected,rtol=1e-8,atol=1e-9):
        raise ValueError("Constructed argument contrasts differ from their planted schedule")
    support,= [row for row in tables["argument_support"] if row["group"]==1]
    if support["n"]!=paired or support["primary_support_met"]!=int(paired>=100):
        raise ValueError("Constructed pre-outcome argument support differs")
    reading,=tables["argument_reading"]
    if reading["sign_disagreement"]!=int(expected[0]*expected[1]<0):
        raise ValueError("Argument sign-disagreement reading differs")
    return n


def run(registry, constructed_inside=False):
    """The mounted form can open only the pinned constructed source bytes."""
    import os
    if os.name == "posix":
        import resource
        import signal
        resource.setrlimit(resource.RLIMIT_CPU,(21600,21600))
        signal.alarm(21600)
    with TemporaryDirectory(prefix="sm-family-check-") as scratch:
        private=Path(scratch)
        directory = private/"invented" if constructed_inside else Path("/data")
        sources = fixture.construct(directory,registry) if constructed_inside else registry
        out=private/"aggregates"
        out.mkdir()
        tables=run_joined({"M2":directory},"M2",sources,out)
        n=verify(tables)
        write_tables(Path("/out"),{"known_answer":[dict(n=n, constructed=1, argument_contrasts=3,
                     daily_parameters=7, family_draws=2000, agreed=1)]})
    return 0
