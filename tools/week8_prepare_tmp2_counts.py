"""Qualify the amended two-archive PANDORA projection using invented histories."""
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from uuid import uuid4
from zipfile import ZipFile, ZIP_DEFLATED

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.week8_sealed import STATE,HOST,GATE
from runners.drive.cards import week8_gear as gear
from runners.drive.sealed import week8_package as bundle
from runners.stage14.common import filehash, freeze, read

UNIT='TMP2-DJ-archive-counts-DN'
CAP=4000
STUDY=bundle.LIB/'week8_tmp2_counts_dn.py'
SHELL=bundle.LIB/'week7_tmp1_shell.py'
MODULES=[STUDY,SHELL,bundle.LIB/'week8_tmp2_source.py',bundle.LIB/'r48_forms.py']
TRAITS=('Openness','Extraversion','Agreeableness','Conscientiousness','Neuroticism')
DESIGN=ROOT/'docs/design/stage-15/week8/TMP2_MAPPING.md'
NOTES=ROOT/'docs/design/stage-15/week8/TMP2_PROJECTION.md'


def fixture(root, flaw=None):
    root.mkdir()
    files={}
    def store(role,member,columns,rows):
        buffer=io.StringIO(newline='')
        w=csv.writer(buffer)
        w.writerow(columns)
        w.writerows(rows)
        content=buffer.getvalue().encode('utf8')
        p=root/('pandora_'+role+'.zip')
        with ZipFile(p,'w',ZIP_DEFLATED) as z:z.writestr(member,content)
        files[role]=dict(name=p.name,bytes=p.stat().st_size,expanded=len(content),sha256=filehash(p))
    profile=[]
    for i in range(120):
        scores=[str(40+(i+j)%25) for j in range(5)]
        if i>=72:scores[0]=''
        if flaw=='range' and i==0:scores[3]='101'
        profile.append(['actor'+str(i),*scores])
    store('profiles','author_profiles.csv',['author',*TRAITS],profile)
    def comments():
        for i in range(72):
            for j in range(1002 if i==0 else 101 if i<36 else 6):
                body=('horizon meadow garden river '*15).strip()
                yield ['actor'+str(i),body,'general',str(1600000000+j),'m'+str(i)+'-'+str(j)]
        for i in range(14):
            yield ['actor'+str(i),'Openness 73 and extraversion 58','shared'+str(i),'1600002000','r'+str(i)]
            yield ['actor31','Ordinary message in a reporting community','shared'+str(i),'1600002001','x'+str(i)]
        for i in range(48):
            yield ['actor'+str(i),'Words in a named community','club-intj-'+str(i%16),'1600003000','b'+str(i)]
        for i in range(61):
            yield ['actor'+str(75+i%24),'That personality inventory was long','general','1600004000','c'+str(i)]
        yield ['actor77','Agreeableness 6 neuroticism 50','ordinary','1600004000','outside']
    key='writer' if flaw=='key' else 'author'
    store('comments','all_comments_since_2015.csv',[key,'body','subreddit','created_utc','id'],comments())
    return files


def build():
    archive=Path(read(ROOT/'.agent-state/data_collection_root.json')['root'])
    source=archive/'_handoffs/repo-requests/DC-20261127-TMP2/SOURCE_RECEIPT.json'
    schema=archive/'private/pandora/SCHEMA.json'
    terms=archive/'private/pandora/REPORTING_R48.md'
    original=read(source)
    if original['source_alias']!='pandora-tmp2' or original['container_target']!='/data:ro':
        raise ValueError('Expected original read-only archive pair')
    public_pins={'comments':'eecd1c0193590ff02f9fd3254853ca4c19ac16f1ba746ced76fa312604c6a8c6','profiles':'5786a84d3e62c70e8c89e59838053f3a29b2f24c4892ea1df17c33c9b19f6a2a'}
    files={}
    for k,digest in public_pins.items():
        name='pandora_'+k+'.zip'
        entry,=[f for f in original['archives'] if f['path']==name]
        shape,=[f for f in read(schema)['files'] if Path(f['path']).name==name]
        if not entry['sha256']==shape['sha256']==digest or entry['bytes']!=shape['bytes'] or not shape['archive_safe']:
            raise ValueError('Archive proof differs')
        files[k]=dict(name=name,bytes=entry['bytes'],sha256=digest,expanded=shape['expanded_bytes'])
    if filehash(GATE)!=read(HOST)['installed_gate_sha256']:raise ValueError('Installed gate differs')
    base=STATE/'fixtures'/(UNIT+'-'+uuid4().hex[:10])
    base.mkdir(parents=True)
    for label,code in [('valid',0),('range',24),('key',22)]:
        mount=base/(label+'-source');out=base/(label+'-output');out.mkdir()
        pins=fixture(mount,label)
        run=base/(label+'.py')
        run.write_bytes(bundle.package(STUDY,MODULES,dict(files=pins,real_image=False),CAP,fixture=True))
        rc=subprocess.run([sys.executable,'-B',str(run),str(mount),str(out)]).returncode
        if rc!=code:raise ValueError('Bad fixture exit '+label+': '+str(rc))
        if code:
            if any(out.iterdir()):raise ValueError('Refusal produced files')
            continue
        if subprocess.check_output([sys.executable,'-I','-B',str(GATE),str(out)],text=True).strip()!='gate passed':
            raise ValueError('Constructed counts failed the installed gate')
        with (out/'counts.csv').open(newline='') as stream:rows=list(csv.DictReader(stream))
        result={int(r['measure']):int(r['count']) for r in rows}
        if result.get(1)!=72 or result.get(2)!=36 or {p.name for p in out.iterdir()}!={'counts.csv'}:
            raise ValueError('Known complete/kept counts did not reproduce')
        if any(set(r)!={'measure','count','n'} or min(int(r['count']),int(r['n']))<11 for r in rows):
            raise ValueError('Unexpected count schema')
        for i,r in enumerate(rows):
            for other in rows[:i]:
                if min(abs(int(r[k])-int(other[j])) for k in ('count','n') for j in ('count','n'))<11:
                    raise ValueError('Close counts disclosed')
        # Exercise the exact projection handed to the reader, wholly on invented authors.
        code=fixture_projection(mount,pins,base)
    rec=STATE/'TMP2_DJ_BINDING.json'
    mapped=dict(mount=original['source_alias'],comments_author_key='author',profiles_author_key='author',
        traits={t:dict(field='by rule: the one column named for the trait, letter case aside',units='percentile 0 to 100, checked in the seal') for t in TRAITS},
        exclusion_list_reference='amendment DJ',provider_binding_sha256=filehash(DESIGN),source_receipt_sha256=filehash(source),archives=files)
    if rec.exists():
        if read(rec)!=mapped:raise ValueError('Existing binding differs')
    else:freeze(rec,mapped)
    ev=base/'REHEARSAL.json'
    freeze(ev,dict(constructed=True,forms=['fine','coarse','summary'],distinct_people_checked=True,small_or_neighboring_counts_suppressed=True,known_scored=72,known_kept=36,
                  projected_latest_thousand=True,known_floor=True,header_refusal=22,range_refusal=24,
                  aggregate_sha256=filehash(base/'valid-output/counts.csv')))
    target=STATE/'sealed'/UNIT/'run.py'
    target.parent.mkdir(parents=True,exist_ok=True)
    raw=bundle.package(STUDY,MODULES,dict(files=files,real_image=True),CAP)
    if target.exists() and target.read_bytes()!=raw:raise ValueError('Existing entry differs')
    if not target.exists():target.write_bytes(raw)
    pins=[*MODULES,Path(bundle.__file__),bundle.SUPPORT,bundle.RELEASE,Path(gear.__file__),gear.AUTHORITY,DESIGN,NOTES,source,
          schema,terms,rec,ev,HOST,GATE,Path(__file__).resolve(),ROOT/'tools/week8_spark.ps1',ROOT/'tools/week8_sealed.py',target]
    freeze(STATE/'reviews'/(UNIT+'.json'),dict(unit=UNIT,card='TMP2',source=original['source_alias'],cap=CAP,tables=['counts.csv','summary.csv'],
        r48=dict(entry_sha256=filehash(target),rehearsal=str(ev),ruling=gear.RULING_SHA256),
        receipt_sha256=filehash(rec),provider_binding_sha256=filehash(DESIGN),fixture_gate_passed=True,fixture_sha256=filehash(ev),pins={str(p):filehash(p) for p in pins}))
    print('TMP2 DJ original archive count job rehearsed.',filehash(target))


def fixture_projection(mount,pins,base):
    sys.path.insert(0,str(bundle.LIB/'week6-sm-science'))
    sys.path.insert(0,str(bundle.SUPPORT.parent))
    from runners.drive.sealed import week8_tmp2_source as s
    excluded=[i for i in s.TYPES if not s.BY_NAME.search('club-'+i)]
    if excluded or s.reporting('Openness 30 and openness 40') or not s.reporting('Openness 30 and extraversion 54'):
        raise ValueError('Reporting definition failed')
    with tempfile.TemporaryDirectory(dir=base) as d:
        dest=Path(d)/'projection'
        _,components=s.filter_histories(mount,pins,Path(d),dest)
        if [v for v,_ in components]!=[72,36,14,16,62]:raise ValueError('DJ counts differ')
        with (dest/'comments.csv').open(newline='',encoding='utf8') as stream:
            ids=[r['id'] for r in csv.DictReader(stream)]
        if 'm0-0' in ids or 'm0-1' in ids or 'm0-2' not in ids or 'outside' in ids or len(ids)!=1000+35*101:
            raise ValueError('Latest-comment selection differs')
    return True


if __name__=='__main__':
    build()
