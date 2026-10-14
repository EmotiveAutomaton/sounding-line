"""Bounded public-history intake, with no scientific admission or model calls.

DESIGN CHECK: LESSONS 2-5; CONTROLS; October errata SL8. NULL: absent rights,
hidden text, changed hashes, missing parents and incomplete support remain refused.
ALTERNATIVE: exact licensed parent/child records are retained for later admission.
Acquisition success never implies human authorship, freshness or reader validity.
"""
import base64
import hashlib
import json
import re
import subprocess
import time
from urllib.parse import urlencode, quote

from .common import now, freeze, digest

UA = 'SoundingLineResearch/0.1 (https://github.com/EmotiveAutomaton/sounding-line; local source audit)'


class SourceRefusal(ValueError):
    pass


class Client:
    def __init__(self, out, card, tick):
        self.out, self.card, self.tick = out, card, tick
        self.started = time.monotonic()
        self.last = 0
        self.calls = 0

    def get(self, source, params):
        if self.calls >= self.card['request_limit'] or time.monotonic()-self.started > self.card['intake_seconds']:
            raise SourceRefusal('bounded intake budget exhausted')
        time.sleep(max(0, self.card['request_interval']-(time.monotonic()-self.last)))
        self.calls += 1
        folder = self.out/'requests'/f'{self.calls:04d}'
        freeze(folder/'REQUEST.json', dict(source=source, parameters=params, at=now()))
        try:
            if source == 'wiki':
                import requests
                query = dict(action='query', format='json', formatversion=2, maxlag=5, **params)
                with requests.get('https://en.wikipedia.org/w/api.php', params=query,
                                  headers={'User-Agent':UA}, timeout=30, stream=True,
                                  allow_redirects=False) as response:
                    parts=[]; size=0
                    for chunk in response.iter_content(65536):
                        size += len(chunk)
                        if size > 10*1024**2: raise SourceRefusal('response byte ceiling')
                        parts.append(chunk)
                    body=b''.join(parts); status=response.status_code
            elif source == 'github':
                # Fixed public API path; never execute repository code or emit auth headers.
                if not params.startswith('repos/') or '..' in params:
                    raise SourceRefusal('invalid public API path')
                call=subprocess.run(['gh','api','--method','GET',params],capture_output=True,timeout=45)
                body=call.stdout; status=200 if call.returncode==0 else 0
                if len(body)>10*1024**2: raise SourceRefusal('response byte ceiling')
            else: raise SourceRefusal('unknown source')
            (folder/'RESPONSE.json').write_bytes(body)
            freeze(folder/'RECEIPT.json',dict(at=now(),status=status,bytes=len(body),sha256=hashlib.sha256(body).hexdigest()))
            if status!=200: raise SourceRefusal('public API request refused; no retry or bypass')
            data=json.loads(body)
            if isinstance(data,dict) and 'error' in data: raise SourceRefusal('public API error; no retry')
            return data
        finally:
            self.last=time.monotonic()
            self.tick(dict(requests=self.calls,request_limit=self.card['request_limit']))


def blob(obj):
    if obj.get('encoding') != 'base64': raise SourceRefusal('unavailable blob encoding')
    data=base64.b64decode(''.join(obj['content'].split()),validate=True)
    if len(data)>2*1024**2: raise SourceRefusal('text byte ceiling')
    actual=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    if actual!=obj['sha']: raise SourceRefusal('Git blob identity mismatch')
    data.decode('utf8')
    return data


def revision(obj):
    slot=obj.get('slots',{}).get('main',{})
    if any(k in obj or k in slot for k in ('texthidden','sha1hidden','userhidden','suppressed')):
        raise SourceRefusal('hidden revision')
    if slot.get('contentmodel')!='wikitext' or not isinstance(slot.get('content'),str):
        raise SourceRefusal('unavailable wikitext')
    data=slot['content'].encode('utf8')
    if len(data)>2*1024**2: raise SourceRefusal('text byte ceiling')
    hexdigest=hashlib.sha1(data).hexdigest()
    if obj.get('sha1',slot.get('sha1'))!=hexdigest: raise SourceRefusal('revision SHA1 mismatch')
    return data


def wiki_run(card,out,client):
    site=client.get('wiki',dict(meta='siteinfo',siprop='general|rightsinfo'))
    rights=site['query']['rightsinfo']
    if 'creativecommons.org/licenses/by-sa/4.0' not in rights.get('url',''):
        raise SourceRefusal('unexpected Wikipedia rights; review before content intake')
    pairs=[]; exclusions=[]; census=[]
    for title in card['titles']:
        listing=client.get('wiki',dict(prop='revisions',titles=title,rvprop='ids|timestamp|user|userid|tags',
            rvlimit=100,rvstart=card['since'],rvend=card['until'],rvdir='newer'))
        page=listing['query']['pages'][0]
        if page.get('ns')!=0: raise SourceRefusal('outside main namespace')
        rows=page.get('revisions',[])
        users=sorted({r['user'] for r in rows if r.get('userid',0)>0 and 'userhidden' not in r})
        groups={}
        for start in range(0,len(users),50):
            result=client.get('wiki',dict(list='users',ususers='|'.join(users[start:start+50]),usprop='groups'))
            groups.update({u['name']:u.get('groups',[]) for u in result['query']['users']})
        eligible=[r for r in rows if r.get('userid',0)>0 and r.get('user') in groups and 'bot' not in groups[r['user']]
                  and 'userhidden' not in r and r.get('parentid',0)>0]
        selected=eligible[:card['pairs_per_page']]
        census.append(dict(title=title,observed=len(rows),eligible=len(eligible),continuation_present='continue' in listing,
            bot_group_status='current membership; historical automation not excluded',selected=len(selected)))
        ids=sorted({v for r in selected for v in (r['revid'],r['parentid'])})
        if not ids: continue
        contents=client.get('wiki',dict(prop='revisions',revids='|'.join(map(str,ids)),
            rvprop='ids|timestamp|user|userid|sha1|content|contentmodel|tags',rvslots='main'))
        revisions={r['revid']:r for p in contents['query']['pages'] for r in p.get('revisions',[])}
        for r in selected:
            try:
                child=revisions[r['revid']];parent=revisions[r['parentid']]
                if child['parentid']!=parent['revid'] or not parent['timestamp']<=child['timestamp']:
                    raise SourceRefusal('parent/chronology mismatch')
                a,b=revision(parent),revision(child)
                key=str(child['revid']);folder=out/'texts'/key;folder.mkdir(parents=True,exist_ok=True)
                (folder/'parent.txt').write_bytes(a);(folder/'child.txt').write_bytes(b)
                pairs.append(dict(id=key,page=title,parent=parent['revid'],child=child['revid'],editor=child['user'],
                    timestamp=child['timestamp'],parent_timestamp=parent['timestamp'],
                    parent_sha256=hashlib.sha256(a).hexdigest(),child_sha256=hashlib.sha256(b).hexdigest(),
                    attribution=f'https://en.wikipedia.org/w/index.php?oldid={key}',rights=rights,
                    revert_status='unassessed; not a negative',fresh_confirmation=False))
            except (KeyError,SourceRefusal) as exc: exclusions.append(dict(id=r['revid'],reason=str(exc)))
    return dict(source='wikipedia',census=census,pairs=pairs,exclusions=exclusions,
                independent_editors=len({p['editor'] for p in pairs}),required_editors=64)


def github_run(card,out,client):
    census=[];pairs=[];exclusions=[]
    for repo in card['repositories']:
        try:
            meta=client.get('github','repos/'+repo)
            if meta.get('private') is not False or meta.get('fork') or meta.get('archived'):
                raise SourceRefusal('not a public independent maintained candidate')
            head=client.get('github',f'repos/{repo}/commits?'+urlencode(dict(until=card['until'],per_page=1)))
            if not head: raise SourceRefusal('no commit in fixed acquisition window')
            sha=head[0]['sha']; readme=client.get('github',f'repos/{repo}/readme?ref={sha}')
            text=blob(readme).decode('utf8')
            lic=client.get('github',f'repos/{repo}/license?ref={sha}'); license_bytes=blob(lic)
            grant=card['reviewed_grants'].get(repo)
            entry=dict(repository=repo,commit=sha,readme_sha=readme['sha'],license_sha=lic['sha'],
                       spdx=lic.get('license',{}).get('spdx_id'),rights_reviewed=False)
            census.append(entry)
            if not grant or grant['readme_sha']!=readme['sha'] or grant['phrase'] not in text:
                raise SourceRefusal('prose rights require explicit review; metadata retained')
            if entry['spdx']!='CC-BY-4.0': raise SourceRefusal('license outside reviewed grant')
            entry['rights_reviewed']=True
            tree=client.get('github',f'repos/{repo}/git/trees/{sha}?recursive=1')
            if tree.get('truncated'): raise SourceRefusal('truncated tree; no completeness claim')
            files=[x['path'] for x in tree['tree'] if x['type']=='blob' and x['path'].endswith(('.md','.mdx'))
                   and '/' in x['path'] and x['path'].split('/')[-1].lower() not in ('readme.md','license.md')]
            entry['candidate_documents']=len(files)
            entry['dated_posts_verified']=False
            entry['post_reader_cutoff_changes_verified']=False
            entry['thirty_document_commits_verified']=False
            for path in sorted(files)[:card['documents_per_repo']]:
                history=client.get('github',f'repos/{repo}/commits?'+urlencode(dict(path=path,per_page=3,since=card['since'],until=card['until'])))
                # Fixed newest-first listing, no outcome-based selection.
                for commit in history[:1]:
                    if len(commit['parents'])!=1:
                        exclusions.append(dict(repository=repo,path=path,commit=commit['sha'],reason='non-single-parent commit'));continue
                    child=commit['sha'];parent=commit['parents'][0]['sha']
                    try:
                        # Rights are witnessed at both historical versions, not inferred retroactively.
                        for version in (parent,child):
                            rm=client.get('github',f'repos/{repo}/readme?ref={version}')
                            if grant['phrase'] not in blob(rm).decode('utf8'):raise SourceRefusal('historical prose grant absent')
                            ls=client.get('github',f'repos/{repo}/license?ref={version}')
                            if blob(ls)!=license_bytes:raise SourceRefusal('historical license differs; review required')
                        versions=[]
                        for version in (parent,child):
                            obj=client.get('github',f'repos/{repo}/contents/{quote(path,safe="/")}?ref={version}')
                            if obj.get('type')!='file': raise SourceRefusal('not an ordinary source file')
                            versions.append(blob(obj))
                        a,b=versions
                        if a==b:raise SourceRefusal('unchanged file; no edit pair')
                        key=digest([repo,path,parent,child]);folder=out/'texts'/key;folder.mkdir(parents=True,exist_ok=True)
                        (folder/'parent.txt').write_bytes(a);(folder/'child.txt').write_bytes(b)
                        pairs.append(dict(id=key,repository=repo,path=path,parent=parent,child=child,
                            author=commit['commit']['author'],committer=commit['commit']['committer'],
                            commit_message=commit['commit']['message'],all_parents=commit['parents'],
                            parent_sha256=hashlib.sha256(a).hexdigest(),child_sha256=hashlib.sha256(b).hexdigest(),
                            attribution=f'https://github.com/{repo}/commit/{child}',license='CC-BY-4.0',
                            author_independence=False,fresh_confirmation=False))
                    except SourceRefusal as exc:exclusions.append(dict(repository=repo,path=path,commit=child,reason=str(exc)))
        except SourceRefusal as exc:exclusions.append(dict(repository=repo,reason=str(exc)))
    return dict(source='github_blogs',census=census,pairs=pairs,exclusions=exclusions,
                required_dated_posts=20,required_document_commits=30,required_post_cutoff_changes=8)


def run(card,out,raw,tick):
    if card.get('policy_authorized') is not True:raise SourceRefusal('source policy not authorized')
    client=Client(out,card,tick)
    result=(wiki_run if card['source']=='wikipedia' else github_run)(card,out,client)
    freeze(out/'SOURCE_RECORDS.json',result)
    freeze(out/'SUMMARY.json',dict(source=result['source'],pairs=len(result['pairs']),
        candidates=len(result['census']),exclusions=len(result['exclusions']),requests=client.calls,
        scope='bounded intake pilot only; source support and reader cutoff not admitted',
        reader_cutoffs_verified=False,fresh_confirmation=False))
    freeze(out/'ADMISSION.json',dict(admitted=False,intake_complete=True,scientific_promotion=False,
        reasons=['reader release cutoff pending','full source support not established','separate study and memory gates required']))
