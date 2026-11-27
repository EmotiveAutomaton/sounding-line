"""Week 8 MIDUS extensions. Person keys and memberships remain inside the seal."""
from hashlib import sha256
import math
from pathlib import Path
from runners.drive.cards.week6_sealed_support_v1 import ReadBudget, SealedFailure, write_tables

TRAITS = {'agreeableness':'B1SAGREE','neuroticism':'B1SNEURO','extraversion':'B1SEXTRA',
          'conscientiousness':'B1SCONS1','openness':'B1SOPEN'}
NEGATIVE = (1,2,3,4,5,6,13,14,15,16,17,18,19,20)
KINDS = ((0,1),(2,3),(5,))


def day_class(values):
    if len(values) != 7:
        raise SealedFailure(22, 'Occurrence fields missing')
    yes, unknown = set(), set()
    for pos,value in enumerate(values):
        if value is None or math.isnan(value) or value in (7,8,9):
            unknown.add(pos)
        elif value == 1:
            yes.add(pos)
        elif value != 2:
            raise SealedFailure(24, 'Unbound occurrence code')
    if not yes and not unknown:
        return 0
    for number,group in enumerate(KINDS,1):
        allowed=set(group)
        if yes and yes <= allowed and unknown <= allowed:
            return number
    return None


def source_file(root, role, sources):
    spec=sources[role]
    name=spec['filename']
    if name!=Path(name).name:
        raise SealedFailure(13, 'Unexpected source name')
    path=ReadBudget(root).reserve(Path(root)/name, passes=2)
    h=sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):
            h.update(chunk)
    if path.stat().st_size!=spec['bytes'] or h.hexdigest()!=spec['sha256']:
        raise SealedFailure(13, 'Changed source')
    return path


def probe(root, spec):
    import pyreadstat
    survey=source_file(root,'survey',spec['files'])
    diary=source_file(root,'diary',spec['files'])
    _,dmeta=pyreadstat.read_sav(str(diary),metadataonly=True)
    required=['M2ID','B2DDAY',*['B2DF'+str(i) for i in range(1,8)],*['B2DC'+str(i) for i in NEGATIVE]]
    if any(dmeta.column_names.count(k)!=1 for k in required):
        raise SealedFailure(22, 'Required diary field absent or ambiguous')
    df,smeta=pyreadstat.read_sav(str(survey),usecols=['M2ID'],user_missing=False)
    if list(df)!=['M2ID'] or df.M2ID.isna().any() or df.M2ID.duplicated().any() or (df.M2ID<=0).any():
        raise SealedFailure(22, 'Ambiguous survey roster')
    _,smeta=pyreadstat.read_sav(str(survey),metadataonly=True)
    flags={name:int(smeta.column_names.count(key)==1) for name,key in TRAITS.items()}
    if smeta.column_names.count('M2FAMNUM')!=1 or not all(flags[k] for k in ('agreeableness','neuroticism','extraversion')):
        raise SealedFailure(22, 'Required survey field absent or ambiguous')
    n=len(df)
    if not 11<=n==spec['survey_people']:
        raise SealedFailure(12, 'Previously published full survey roster differs')
    return dict(structure=[dict(flags,n=n)])


def run(root,out,config):
    first=probe(root,config)
    if first!=probe(root,config):
        raise SealedFailure(14,'Source header replay differs')
    write_tables(out,first)
