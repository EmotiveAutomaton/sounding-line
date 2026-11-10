"""GO2 historical authorship support using the preserved h2 text projection.

Capture Git bytes first. Decode UTF8 strictly, or an explicit supported coding
declaration. Undeclared undecodable versions are counted adjacency gaps, never
guessed text; retained raw Git objects remain unchanged.
"""
from pathlib import Path
from types import FunctionType,MethodType
import os,re,subprocess,json
from . import week5_go as core
from . import week5_go_history_h1 as prior

ALIASES={'utf-8':'utf-8-sig','utf8':'utf-8-sig','latin-1':'latin-1','latin1':'latin-1',
         'iso-8859-1':'latin-1','iso8859-1':'latin-1','windows-1252':'cp1252','cp1252':'cp1252'}


def decode_blob(raw,counts):
    if b'\0' in raw:counts['excluded_binary_versions']+=1;return ''
    try:return raw.decode('utf-8-sig','strict')
    except UnicodeDecodeError:pass
    # Recognize header/footer coding declarations, not arbitrary body prose.
    lines=raw.splitlines();edges=b'\n'.join(lines[:10]+lines[-20:])
    labels={m.group(1).decode('ascii').lower() for m in re.finditer(
        rb'(?im)^\s*(?:[#;*]\s*)?(?:coding|encoding|charset)\s*[:=]\s*([-a-zA-Z0-9]+)\s*(?:-\*-)?\s*$',edges)}
    codecs={ALIASES.get(label) for label in labels}
    if len(codecs)!=1 or None in codecs:
        counts['excluded_undeclared_or_unsupported_encoding_versions']+=1;return ''
    codec=next(iter(codecs))
    try:text=raw.decode(codec,'strict')
    except UnicodeDecodeError:counts['excluded_invalid_declared_encoding_versions']+=1;return ''
    counts['explicit_legacy_encoding_versions']+=1;return text


class BytesCore:
    def __init__(self,counts):self.counts=counts
    def __getattr__(self,name):return getattr(core,name)
    def git(self,repo,*args):
        result=subprocess.run(['git','-C',str(repo),*args],capture_output=True,
            env={**os.environ,'GIT_NO_LAZY_FETCH':'1'},timeout=120)
        if result.returncode:raise ValueError('local pinned git object unavailable or git command refused')
        if args[0]=='show':return decode_blob(result.stdout,self.counts)
        return result.stdout.decode('utf8','strict')


class SourceCore(prior.SourceCore):
    def __init__(self):
        super().__init__();byte_core=BytesCore(self.counts)
        method=FunctionType(prior.SourceCore.git.__code__,dict(prior.SourceCore.git.__globals__,core=byte_core))
        self.git=MethodType(method,self)


def window(edits,reverse=False):
    chosen=[]
    for edit in reversed(edits) if reverse else edits:
        if edit is not None and edit.get('unreadable_gap'):break
        if edit is not None and edit['rest_changed'] and edit['added']:
            chosen.append(edit['added'])
            if len(chosen)==3:break
    return list(reversed(chosen)) if reverse else chosen


def source(output,inputs):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);salt=Path(inputs['salt']).read_bytes()
    if len(salt)!=32:raise ValueError('salt shape')
    rows=json.loads(Path(inputs['documents']).read_text('utf8'))['documents'];anchors=[];first=[]
    adapter=SourceCore();counts=adapter.counts;cache={}
    for row in rows:
        name=row['repository'];repo=Path(inputs[name])
        if adapter.git(repo,'rev-parse',core.PINS[name]).strip()!=core.PINS[name]:raise ValueError('history revision pin missing')
        log=adapter.git(repo,'log','--follow','--format=COMMIT %H %ct','--name-status',core.PINS[name],'--',row['relative_path'])
        manifest=[];current=row['relative_path'];entry=None
        for line in log.splitlines():
            if line.startswith('COMMIT '):
                if entry:manifest.append(entry)
                _,commit,stamp=line.split();entry={'commit':commit,'timestamp':int(stamp),'path':current}
            elif entry and line.startswith('R'):
                fields=line.split('\t')
                if len(fields)==3 and fields[2]==current:entry['path']=fields[2];current=fields[1]
        if entry:manifest.append(entry)
        versions=[]
        for revision in reversed(manifest):
            key=(name,revision['commit'])
            if key not in cache:
                changed=adapter.git(repo,'diff-tree','--root','--no-commit-id','--name-only','-r',revision['commit']).splitlines()
                cache[key]=sum(bool(re.search(r'(?:^|/)(?:pep-|eip-|erc-)\d+\.(?:rst|md|txt)$',p)) for p in changed)
            text=adapter.git(repo,'show',revision['commit']+':'+revision['path'])
            parsed,reason=core.parse_document(text,name,salt);counts['revisions_scanned']+=1
            if parsed is None:counts['excluded_revision_'+reason]+=1;versions.append(None);continue
            versions.append({**parsed,'bulk':cache[key]>5,'commit':revision['commit']})
        eligible_versions=[v for v in versions if v is not None]
        historical_multi_author=any(v['multi_author'] for v in eligible_versions)
        counts['documents_any_eligible_multi_author']+=int(historical_multi_author)
        counts['documents_with_eligible_authorship']+=int(bool(eligible_versions))
        earliest=next((v for v in versions if v is not None),None)
        if earliest is not None:
            first.append({**earliest,'document':row['document'],'relative_path':row['relative_path'],
                          'head':core.PINS[name],'version_scope':'earliest eligible licensed Motivation-bearing version'})
        edits=[]
        for earlier,later in zip(versions,versions[1:]):
            if earlier is None or later is None:edits.append({'unreadable_gap':True});continue
            fraction,_=prior.original.token_change(earlier['motivation'],later['motivation'])
            rest,added=prior.original.token_change(earlier['rest'],later['rest'])
            if later['bulk']:counts['bulk_document_commits_excluded']+=1;edits.append(None);continue
            if fraction==0 and rest==0:counts['markup_or_whitespace_only_excluded']+=1;edits.append(None);continue
            edits.append({'old_goal':earlier['motivation'],'new_goal':later['motivation'],'goal_fraction':fraction,
                          'added':added,'rest_changed':rest>0,'author':later['author']})
        for index,edit in enumerate(edits):
            if edit is None or edit.get('unreadable_gap') or edit['goal_fraction']<.2:continue
            counts['goal_change_anchors']+=1
            before=window(edits[:index],True);after=window(edits[index+1:])
            if not before or not after:counts['no_bilateral_added_text']+=1;continue
            anchors.append({'author':edit['author'],'document':row['document'],'old_goal':edit['old_goal'],
                            'new_goal':edit['new_goal'],'before':before,'after':after,'three_each':len(before)==len(after)==3,
                            'historical_multi_author':historical_multi_author})
        counts['documents']+=1;core.write(output/'PROGRESS.json',{'documents':counts['documents'],'total':len(rows)})
    core.write(output/'anchors.json',{'anchors':anchors});core.write(output/'first-drafts.json',{'documents':first})
    result={'counts':dict(counts),'bilateral_anchors':len(anchors),'three_each_anchors':sum(r['three_each'] for r in anchors),
            'heads':core.PINS,'anchors_sha256':core.sha(output/'anchors.json'),'first_drafts_sha256':core.sha(output/'first-drafts.json'),
            'source_only':True,'successor_module_sha256':core.sha(__file__),
            'history_semantics':'renames followed; copy-target starts retained; missing/undecodable versions stop both adjacency and before/after windows',
            'encoding_policy':'strict UTF8/BOM first; explicit supported legacy declaration only; no guessed text'}
    core.write(output/'SOURCE.json',result);return result
