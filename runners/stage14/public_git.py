"""H03 bounded public document-history intake; all analysis/storage stays local.

DESIGN CHECK: LESSONS 2,5; SL7/SL8. NULL: missing license, absent parent/file,
truncated patch or unknown reader cutoff cannot become fresh historical truth.
ALTERNATIVE: pinned before/after blobs, all parent identities and exact public
commit metadata support typed recorded-change targets. Commit identity is not
proof of human authorship, private purpose or freedom from model assistance.
"""
import base64,json,subprocess,time
from urllib.parse import quote
from .common import freeze,read,digest,now

SOURCES=(('python/cpython','README.rst'),('numpy/numpy','README.md'),('pandas-dev/pandas','README.md'),
         ('scikit-learn/scikit-learn','README.rst'),('psf/requests','README.md'),('pallets/flask','README.md'),
         ('django/django','README.rst'),('scipy/scipy','README.rst'))
LICENSES={'MIT','BSD-2-Clause','BSD-3-Clause','Apache-2.0','Python-2.0','PSF-2.0'}

def get(path,out):
    key=digest(path);dest=out/'requests'/key
    if (dest/'RESPONSE.json').exists():return read(dest/'RESPONSE.json')
    if (dest/'REQUEST.json').exists():raise RuntimeError('previous intake request unresolved; inspect explicitly')
    freeze(dest/'REQUEST.json',dict(at=now(),method='GET',path=path));start=time.monotonic()
    r=subprocess.run(['gh','api','--method','GET',path],capture_output=True,text=True,encoding='utf8',timeout=120)
    freeze(dest/'RECEIPT.json',dict(at=now(),wall_seconds=time.monotonic()-start,returncode=r.returncode,error=r.stderr if r.returncode else None))
    if r.returncode:raise ValueError('public GET failed; preserved receipt')
    value=json.loads(r.stdout);freeze(dest/'RESPONSE.json',value);return value

def blob(repo,path,sha,out):
    value=get(f'repos/{repo}/contents/{quote(path,safe="/")}?ref={sha}',out)
    if value.get('type')!='file' or value.get('encoding')!='base64' or value['size']>80000:raise ValueError('document absent, unsupported or exceeds 80KB bound')
    data=base64.b64decode(value['content'],validate=False)
    if len(data)!=value['size']:raise ValueError('incomplete blob')
    return dict(git_blob=value['sha'],text=data.decode('utf8'),bytes=len(data),sha256=digest(data.hex()))

def run(card,out,raw,tick):
    records=[];excluded=[];licenses={}
    for repo,path in SOURCES:
        try:
            lic=get(f'repos/{repo}/license',out);spdx=lic.get('license',{}).get('spdx_id')
            licenses[repo]=dict(spdx=spdx,url=lic.get('html_url'),content_sha=lic.get('sha'))
            if spdx not in LICENSES:raise ValueError('license outside frozen permitted set; no implied permission')
            commits=get(f'repos/{repo}/commits?path={quote(path,safe="")}&since={card["since"]}&until={card["until"]}&per_page=16',out)
            if not isinstance(commits,list):raise ValueError('commit-list response malformed')
            for item in commits[:16]:
                sha=item['sha']
                try:
                    commit=get(f'repos/{repo}/commits/{sha}',out);parents=[p['sha'] for p in commit['parents']]
                    if not parents:raise ValueError('no parent comparison')
                    after=blob(repo,path,sha,out);before=[blob(repo,path,p,out) for p in parents]
                    if all(x['text']==after['text'] for x in before):
                        excluded.append(dict(repository=repo,commit=sha,reason='no document content change'));continue
                    who=commit['commit'];key=digest([repo,path,sha]);record=dict(key=key,repository=repo,path=path,commit=sha,parents=parents,
                        author=digest(who['author']),committer=digest(who['committer']),author_time=who['author']['date'],commit_time=who['committer']['date'],
                        message=who['message'],before=before,after=after,license=licenses[repo],source_url=commit['html_url'],
                        scope='public recorded document revision; author/committer separate; model assistance unknown; reader cutoff not yet verified')
                    freeze(out/'records'/f'{key}.json',record);records.append(record)
                except (ValueError,KeyError,UnicodeError) as exc:excluded.append(dict(repository=repo,commit=sha,reason=str(exc)))
                tick(dict(repositories_seen=len(licenses),changes_retained=len(records),excluded=len(excluded)))
        except (ValueError,KeyError) as exc:excluded.append(dict(repository=repo,reason=str(exc)))
    freeze(out/'MANIFEST.json',dict(records=[{k:v for k,v in r.items() if k not in ('before','after','message')} for r in records],licenses=licenses))
    freeze(out/'EXCLUSIONS.json',excluded)
    freeze(out/'SUMMARY.json',dict(repositories=len({r['repository'] for r in records}),changes=len(records),excluded=len(excluded),since=card['since'],until=card['until'],
        scope='source intake only; exact parent records; no model or private-intent truth',pretraining_status='UNVERIFIED per reader; dates alone do not license fresh confirmation'))
    freeze(out/'ADMISSION.json',dict(admitted=bool(records),source_intake=True,human_authorship=False,fresh_confirmation=False))
