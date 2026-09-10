"""Preparation-only cross-corpus evidence and exposure inventory.

DESIGN CHECK: LESSONS 3-5; I02/X01/X05. NULL: a shared prompt or short
phrase cannot invent a common author; no new split name restores exposed data.
ALTERNATIVE: exact text reuse, long containment and known paper aliases are
detected across every prepared source. Fixed index passes exhaustive fixtures.
Bands: receipt complete or failed. Overlaps are witnessed dependencies requiring
consumer enforcement; absence is bounded by the fixed lexical rule. No scoring,
model fitting, hypothesis selection or human identity reconstruction occurs here.
"""
from collections import Counter, defaultdict
import math
import re
import time

from runners.stage9.common import ROOT, REPO, closure, digest, file_hash, freeze, read, write
from runners.stage9.text_overlap import Overlaps

LANES = ('pilot','train','development','discovery','reserve')


def paper_alias(value):
    match = re.search(r'(?<!\d)(\d{4}\.\d{4,5})(?:v\d+)?(?!\d)',value)
    return 'arxiv:'+match.group(1) if match else None


class Inventory:
    def __init__(self, root=ROOT):
        self.root = root
        self.overlaps = Overlaps()
        self.groups = {}
        self.inputs = {}
        self.counts = Counter()

    def load(self, path):
        path = self.root/path
        self.inputs[path.relative_to(REPO).as_posix()] = file_hash(path)
        return read(path)

    def group(self, corpus, value, split, *, kind, previously_exposed=False, alias=None):
        if split not in LANES:
            raise ValueError('unregistered allocation')
        key = corpus+':'+value
        record = {'corpus':corpus,'source_group':value,'split':split,'kind':kind,
                  'previously_exposed':previously_exposed,'paper_alias':alias}
        if key in self.groups and record != self.groups[key]:
            raise ValueError('inconsistent source group declaration')
        self.groups[key] = record
        return key

    def text(self, group, value, role='artifact'):
        self.overlaps.add(group,value,role)
        self.counts[self.groups[group]['corpus']] += 1

    def prepared(self, name, marker='COMPLETE.json'):
        path = 'private/prepared/'+name+'/'
        self.load(path+'IDENTITY.json')
        if marker:
            self.load(path+marker)
        audit = self.root/(path+'COMPLETION_AUDIT.json')
        if audit.exists(): self.load(path+'COMPLETION_AUDIT.json')
        return path

    def collect(self, progress=None):
        p = self.prepared('iterater-v2',None)
        for lane in LANES:
            for r in self.load(p+lane+'/records.json'):
                g = self.group('iterater',r['independent_unit'],lane,kind='paper_or_document',
                               alias=paper_alias(r['independent_unit']))
                self.text(g,r['before']); self.text(g,r['artifact'])
        if progress: progress('iterater')
        p = self.prepared('arxivedits-v1')
        for r in self.load(p+'RECORDS.json'):
            g = self.group('arxivedits',r['independent_unit'],'development',kind='paper',
                           previously_exposed=True,alias=paper_alias(r['independent_unit']))
            self.text(g,r['before'],'local_fragment'); self.text(g,r['artifact'],'local_fragment')
        # Whole allowed source sentence pairs, not just the annotated edit, can
        # reveal aliases with a whole-document revision source.
        for path in sorted((self.root/(p+'pairs')).glob('*.json')):
            r = self.load(path.relative_to(self.root))['source_pair']
            g = 'arxivedits:arxiv:'+r['arxiv-id']
            self.text(g,r['sentence-1'],'local_fragment'); self.text(g,r['sentence-2'],'local_fragment')
        if progress: progress('arxivedits')
        p = self.prepared('argrewrite-v3')
        for path in sorted((self.root/(p+'essays')).glob('*.json')):
            r = self.load(path.relative_to(self.root))
            g = self.group('argrewrite',r['group'],'development',kind='essay_student',previously_exposed=True)
            for text in r['drafts'].values(): self.text(g,text)
            for tables in r['tables'].values():
                for text in tables.values(): self.text(g,text)
            for unit in r['units']:
                self.text(g,unit['old'],'local_fragment'); self.text(g,unit['new'],'local_fragment')
        if progress: progress('argrewrite')
        p = self.prepared('scholawrite-v2')
        for item in self.load(p+'LEDGER.json'):
            g = self.group('scholawrite',item['unit'],'development',kind='project',previously_exposed=True)
            data = self.load(p+item['path'])
            for text in data['texts'].values(): self.text(g,text)
        if progress: progress('scholawrite')
        p = self.prepared('coauthor-v2')
        for item in self.load(p+'LEDGER.json'):
            if 'writer' not in item: continue
            g = self.group('coauthor',item['writer'],item['split'],kind='writer',previously_exposed=True)
            # Prompts are a second crossed dependency, never an independently
            # inferred person's identity and never a new reserve for old data.
            pg = self.group('coauthor_prompts',item['prompt'],'development',kind='crossed_prompt',previously_exposed=True)
            data = self.load(p+'sessions/'+item['key']+'.json')
            self.text(g,data['final_document'])
            for r in data['events']:
                self.text(g,r['document'])
                for option in r['options']:
                    self.text(pg,option['trimmed'],'candidate')
        if progress: progress('coauthor')
        p = self.prepared('commitbench-v1')
        allocation = self.load(p+'SPLITS.json')
        for unit,lane in allocation.items():
            self.group('commitbench',unit,lane,kind='repository')
        for lane in LANES:
            for r in self.load(p+lane+'/RECORDS.json'):
                g = 'commitbench:'+r['unit']
                self.text(g,r['diff']); self.text(g,r['message'],'candidate')
        if progress: progress('commitbench')
        p = self.prepared('sga',None)
        g = self.group('sga','Frankenstein','development',kind='one_work',previously_exposed=True)
        for r in self.load(p+'cases.json'):
            self.text(g,r['local_before'],'local_fragment'); self.text(g,r['local_after'],'local_fragment')
        if progress: progress('sga')
        p = self.prepared('broll-v1')
        identity = self.load(p+'IDENTITY.json')
        scripts = self.load(p+'SCRIPTS.json')
        for person,lane in identity['person_split'].items():
            self.group('broll_people',person,lane,kind='participant')
        for key,s in scripts.items():
            g = self.group('broll_scripts',key,identity['script_split'][key],kind='crossed_script')
            self.text(g,s['script'],'shared_stimulus')
        # Hash each complete split, but do not consume response labels or turn
        # selections of a common script into copied independently authored prose.
        for lane in ('pilot','development','discovery','reserve'):
            path = self.root/(p+lane+'.json')
            self.inputs[path.relative_to(REPO).as_posix()] = file_hash(path)
        if progress: progress('broll')


def summarize(result, groups):
    aliases = defaultdict(list)
    for g,r in groups.items():
        if r['paper_alias']: aliases[r['paper_alias']].append(g)
    alias_edges = [sorted(v) for v in aliases.values() if len(v)>1]
    by_corpus = {}
    for corpus in sorted({r['corpus'] for r in groups.values()}):
        rows = [r for r in groups.values() if r['corpus']==corpus]
        counts = Counter(r['split'] for r in rows)
        originally_eligible = sum(r['split']!='pilot' and not r['previously_exposed'] for r in rows)
        unexamined = sum(r['split'] in ('discovery','reserve') and not r['previously_exposed'] for r in rows)
        by_corpus[corpus] = {'groups':len(rows),'splits':dict(counts),
            'new_nonpilot_groups_before_baselines':originally_eligible,
            'currently_unexamined_discovery_or_reserve_groups':unexamined,
            'reserve_before_cross_source_exclusions':counts['reserve'],
            'thirty_percent_of_new_nonpilot_groups':math.ceil(.3*originally_eligible),
            'reserve_shortfall_against_original_inventory':max(0,math.ceil(.3*originally_eligible)-counts['reserve'])}
    pair_counts = Counter()
    for e in result['long_overlap_edges']:
        pair_counts[' / '.join(sorted(groups[g]['corpus'] for g in e['groups']))] += 1
    return {'corpora':by_corpus,'paper_alias_components':alias_edges,'long_overlap_corpus_pairs':dict(pair_counts),
            'exact_collision_buckets':len(result['exact_collision_buckets']),
            'long_overlap_group_role_pairs':len(result['long_overlap_edges'])}


def main():
    started = time.time()
    out = ROOT/'private/prepared/cross-source-v1'
    identity = {'sources':closure([REPO/'runners/stage9'/n for n in ('cross_source.py','text_overlap.py','common.py')]),
                'operation':'label-free preparation audit; no inference or reserve scoring',
                'rule':'complete lexical candidate retrieval; exact short collisions distinguished from long overlaps'}
    freeze(out/'IDENTITY.json',identity)
    if (out/'COMPLETE.json').exists():
        return read(out/'COMPLETE.json')
    def progress(value):
        write(out/'PROGRESS.json',{'at':time.time(),'elapsed_seconds':time.time()-started,'progress':value})
    try:
        inv = Inventory(); inv.collect(progress)
        result = inv.overlaps.run(progress)
        summary = summarize(result,inv.groups)
        freeze(out/'GROUPS.json',inv.groups)
        freeze(out/'OVERLAPS.json',result)
        freeze(out/'INPUTS.json',inv.inputs)
        for name,sha in inv.inputs.items():
            if file_hash(REPO/name)!=sha: raise ValueError('input changed during audit')
        receipt = {'identity_sha256':digest(identity),'completed_at':time.time(),'elapsed_seconds':time.time()-started,
            'input_hashes_reverified':True,'input_files':len(inv.inputs),'text_occurrences_by_corpus':dict(inv.counts),
            'search':{k:v for k,v in result.items() if k not in ('exact_collision_buckets','long_overlap_edges','fingerprint_inventory')},
            'summary':summary,'files':{n:file_hash(out/n) for n in ('GROUPS.json','OVERLAPS.json','INPUTS.json')},
            'scientific_split_accepted':False,
            'next':'review witnessed overlaps and enforce exposure/group/fit-test exclusions in scientific consumers; no new reserve by relabeling'}
        freeze(out/'COMPLETE.json',receipt)
        public = dict(receipt); public['summary'] = {k:v for k,v in summary.items() if k!='paper_alias_components'}
        public['summary']['paper_alias_components'] = len(summary['paper_alias_components'])
        freeze(ROOT/'intake/CROSS_SOURCE_AUDIT_V1.json',public)
        return public
    except Exception as exc:
        freeze(out/'FAILED.json',{'identity_sha256':digest(identity),'at':time.time(),
                                 'elapsed_seconds':time.time()-started,'error':str(exc)})
        raise


if __name__ == '__main__':
    print(main())
