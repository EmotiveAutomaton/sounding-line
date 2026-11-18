"""Additive single-independent-person interval refusal; frozen core untouched."""
try:
    from . import es_core_v1 as core
except ImportError:
    import es_core_v1 as core


def require_population_interval(stats):
    if len(stats['people'])<2:
        raise core.Unidentified('population interval needs at least two independent people')


def bootstrap(stats,*args,**kwargs):
    require_population_interval(stats)
    return core.bootstrap(stats,*args,**kwargs)
