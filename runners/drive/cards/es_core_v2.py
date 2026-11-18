"""Additive population guard; all ES estimands and v1 exception identity retained.

The source population, not the number of distinct resampled people in one draw,
must contain at least two independent people. No source I/O or native launch.
"""
if __package__:
    from . import es_core_v1 as original
    from .es_core_v1 import *  # noqa: F403; exact frozen API, no copied estimators
else:
    import es_core_v1 as original
    from es_core_v1 import *  # noqa: F403


def population_interval_support(stats):
    n = len(stats['people'])
    return {'eligible_people': n, 'minimum_independent_people': 2,
            'minimum_independent_population_met': n >= 2}


def require_population_interval(stats):
    if len(stats['people']) < 2:
        raise original.Unidentified('population interval requires at least two independent people')


def bootstrap(stats, statistic, seed, draws=2000, progress=lambda row: None, prior=()):
    # Refuse before accepting a cached draw prefix or invoking the statistic.
    require_population_interval(stats)
    return original.bootstrap(stats, statistic, seed, draws=draws,
                              progress=progress, prior=prior)
