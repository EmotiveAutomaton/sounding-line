"""Return only the finest admissible DJ source-accounting form."""
from math import sqrt
from tempfile import TemporaryDirectory
from pathlib import Path

from independent_release import Entry
from runners.drive.cards.week6_sealed_support_v1 import SealedFailure, write_tables
from runners.drive.sealed import week8_tmp2_source as original
from runners.drive.sealed.r48_forms import choose


def forms(universe, components):
    try:
        allowed=original.count_table(universe,components)['counts']
    except SealedFailure as exc:
        if exc.code!=12:
            raise
        allowed=[]
    entries=[Entry(record,components[record['measure']-1][1]) for record in allowed]
    coarse=[e for e in entries if e.fields['measure'] in (1,2)]
    n,scored=components[0]
    k,retained=components[1]
    if len(scored)!=n or len(retained)!=k or not retained<=scored:
        raise SealedFailure(14,'Invalid distinct-author count')
    summary=[]
    if k>=11 and n-k>=11:
        # Wilson interval for the registered descriptive retention share.
        z=1.959963984540054
        p=k/n
        denom=1+z*z/n
        center=(p+z*z/(2*n))/denom
        margin=z*sqrt(p*(1-p)/n+z*z/(4*n*n))/denom
        summary=[(1,'summary',[Entry(dict(estimate=p,lower=center-margin,upper=center+margin,n=n),
                                     scored,(retained,scored-retained))])]
    return choose({'fine':[(1,'counts',entries)] if len(entries)==len(components) else [],
                   'coarse':[(1,'counts',coarse)] if len(coarse)==2 else [],
                   'summary':summary},universe,[])


def run(root,out,config):
    if config['real_image']:
        original.check_image()
    pins=config['files']
    original.verify(root,pins)
    def once():
        with TemporaryDirectory(prefix='dj-counts-') as tmp:
            return forms(*original.filter_histories(root,pins,Path(tmp)))
    result=once()
    if once()!=result:
        raise SealedFailure(14,'Independent recount differs')
    write_tables(out,result)
