"""Separate PMAP source-only recovery for the broader upstream raw roster.

The frozen primary population is unchanged. All other source validation and all
scientific feature extraction remain the original implementation. Extras are
upstream-only records, not guessed invalid sessions or an analyst exclusion.
"""
from __future__ import annotations
from pathlib import Path
import math
import numpy as np
from . import timing_pmap_source as original
from .timing_pmap_source import INPUTS, completed, indexed, bound_record, dictionary
from .timing_census import read, filehash
from runners.stage9.common import digest


class Sources(original.Sources):
    def __init__(self, inputs):
        if set(inputs) != INPUTS: raise ValueError('exact PMAP inputs required')
        self.inputs = inputs; self.root = Path(inputs['repo_root']).resolve()
        plan = read(inputs['foundation_plan']); c = read(inputs['foundation_complete'])
        if c.get('status') != 'COMPLETE' or c.get('plan_sha256') != filehash(inputs['foundation_plan']):
            raise ValueError('foundation plan unauthenticated')
        for name in ('prepared_sessions','raw_roster','source_pins'):
            p = Path(inputs[name]).resolve()
            if plan['pins'].get(p.relative_to(self.root).as_posix()) != filehash(p):
                raise ValueError('foundation source metadata changed')
        for index, complete in (('session_index','foundation_complete'),('p6_index','p6_completion'),
                               ('p5_index','p5_completion'),('tc_primary','tc_completion')):
            completed(inputs[complete], inputs[index], fresh=index != 'session_index')
        self.tc = read(inputs['tc_primary'])
        self.p2, self.p5, self.p6 = (indexed(inputs[k]) for k in ('session_index','p5_index','p6_index'))
        self.meta, self.roster = (indexed(inputs[k]) for k in ('prepared_sessions','raw_roster'))
        if not (self.p2.keys() == self.p5.keys() == self.p6.keys() == self.meta.keys()):
            raise ValueError('source session populations differ')
        if not self.p2.keys() <= self.roster.keys():
            raise ValueError('raw roster lacks primary sessions')
        self.population = dict(primary_sessions=len(self.p2), raw_roster_sessions=len(self.roster),
            upstream_only_sessions=sorted(self.roster.keys()-self.p2.keys()),
            primary_session_ids=sorted(self.p2), policy='Exact P2/P5/P6/prepared equality; raw roster must cover every primary session; extras do not enter profiles')
        self.pins = {Path(k).as_posix():v for k,v in read(inputs['source_pins']).items()}
        content = Path(inputs['content_complete']).parent
        for name in ('RECORDS.json','VECTORS.npy','PLAN.json'):
            completed(inputs['content_complete'], content/name, fresh=False)
        cp = read(content/'PLAN.json')
        if cp['pins'].get(Path(inputs['prepared_sessions']).resolve().relative_to(self.root).as_posix()) != filehash(inputs['prepared_sessions']):
            raise ValueError('content/prepared population differs')
        records = read(content/'RECORDS.json'); self.content = {r['key']:r for r in records}
        if len(self.content) != len(records): raise ValueError('duplicate content key')
        self.vectors = np.load(content/'VECTORS.npy', mmap_mode='r', allow_pickle=False)
        if self.vectors.ndim != 2 or self.vectors.shape[1] != 384 or not np.isfinite(self.vectors).all():
            raise ValueError('invalid MiniLM vectors')
        audit = Path(inputs['selection_audit_complete']).parent
        completed(inputs['selection_audit_complete'], audit/'ROWS.json', fresh=False)
        ar = read(audit/'ROWS.json'); self.audit = {r['key']:r for r in ar}
        if len(self.audit) != len(ar) or self.audit.keys() != self.content.keys():
            raise ValueError('canonical/content menu populations differ')

    def metadata(self, sid):
        i = self.inputs; row = self.p2[sid]; meta = self.meta[sid]; roster = self.roster[sid]
        timeline = bound_record(i['session_index'], row)
        p5, p6 = bound_record(i['p5_index'],self.p5[sid]), bound_record(i['p6_index'],self.p6[sid])
        identity = (sid,row['writer'],timeline['prompt'])
        for r in (timeline,meta,p5,p6):
            if (r['session'],r['writer'],r['prompt']) != identity: raise ValueError('session identity mismatch')
        if p5['source_sha256'] != timeline['source_sha256'] or p5['p2_sha256'] != row['sha256']:
            raise ValueError('P5 source mismatch')
        if (p6['timestamp'],p6['end_at']) != (meta['timestamp'],meta['end_at']):
            raise ValueError('P6 chronology mismatch')
        raw = (self.root/roster['path']).resolve(); raw.relative_to(self.root)
        if filehash(raw) != timeline['source_sha256'] or self.pins.get(roster['path']) != timeline['source_sha256']:
            raise ValueError('raw source mismatch')
        canonical_path = self.root/'results/phase_2_4_stage_9/private/prepared/coauthor-v2/sessions'/(digest({'coauthor-session':raw.stem})+'.json')
        chash = filehash(canonical_path)
        if self.pins.get(canonical_path.relative_to(self.root).as_posix()) != chash:
            raise ValueError('canonical source unauthenticated')
        canonical = read(canonical_path)
        if not canonical['usable'] or not canonical['reconstructed'] or canonical['errors'] or canonical['final_document'] != timeline['final_document']:
            raise ValueError('canonical replay invalid')
        cr = {r['ordinal']:r for r in canonical['events'] if r['usable']}
        if len(cr) != sum(bool(r['usable']) for r in canonical['events']) or set(cr) != {m['ordinal'] for m in meta['rows']}:
            raise ValueError('canonical decision coverage differs')
        if {r['ordinal']:r['handling'] for r in timeline['decisions']} != {o:r['decision'] for o,r in cr.items()}:
            raise ValueError('canonical handling differs')
        na = nd = mismatch = 0
        for m in meta['rows']:
            c, a, v = cr[m['ordinal']], self.audit[m['key']], self.content[m['key']]
            if (a['key'],a['session'],a['writer'],a['ordinal'],a['prepared_handling']) != (m['key'],sid,row['writer'],m['ordinal'],m['handling']):
                raise ValueError('selection audit identity differs')
            choices = [j for j,o in enumerate(c['options']) if o['index'] in c['matched_option_indices']] if c['decision'] in ('accept','edit') else []
            if [o['original'] for o in c['options']] != m['menu'] or len(v['options']) != len(m['menu']):
                raise ValueError('canonical/content menu order mismatch')
            if (a['canonical_sha256'],a['canonical_positions'],a['raw_source_sha256'],a['canonical_handling']) != (chash,choices,timeline['source_sha256'],c['decision']):
                raise ValueError('selection audit disagrees with source reconstruction')
            if (v['session'],v['writer']) != (sid,row['writer']): raise ValueError('content identity differs')
            if any(type(index) is not int or index < 0 or index >= len(self.vectors) for index in v['options']):
                raise ValueError('content vector index invalid')
            if c['decision'] in ('accept','edit'):
                if not c['verified_insertion'] or len(choices) != 1:
                    raise ValueError('accepted option identity not uniquely verified')
                na += 1
                mismatch += int(a['index_status'] == 'proven_disjoint_choice')
            if c['decision']=='dismiss':
                if not v['options']:raise ValueError('dismissed menu has no offered vectors')
                nd += 1
        # Schema checks cover every field read downstream without computing any
        # source features, profiles, matches or scientific outcome statistics.
        if not isinstance(timeline['final_document'], str): raise ValueError('invalid final document')
        if any(d['handling'] not in original.ACTIONS for d in timeline['decisions']): raise ValueError('invalid handling')
        if any(e['split'] not in ('content','housekeeping','excluded') for e in p5['edits']): raise ValueError('invalid P5 split')
        if any(type(v) is not int or v < 0 for v in timeline['event_counts'].values()): raise ValueError('invalid event counts')
        for word in p6['words']:
            if not isinstance(word['token'],str) or type(word['is_word']) is not bool: raise ValueError('invalid P6 token')
            if not isinstance(word['within_intervals'],list): raise ValueError('invalid P6 intervals')
            for value in word['within_intervals']:
                if type(value) not in (int,float) or not math.isfinite(value): raise ValueError('nonfinite P6 interval')
            value=word['pause_seconds']
            if value is not None and (type(value) not in (int,float) or not math.isfinite(value)): raise ValueError('invalid P6 pause')
        return dict(session=sid, source_hashes=self.unit_binding(sid), menus=len(meta['rows']),
            accepted_options=na, dismissed_menus=nd, canonical_choice_disagreements=mismatch)

    def preflight(self):
        prepared_keys=[m['key'] for meta in self.meta.values() for m in meta['rows']]
        if len(set(prepared_keys))!=len(prepared_keys) or set(prepared_keys)!=self.content.keys():
            raise ValueError('full prepared/content menu population differs')
        units=[self.metadata(sid) for sid in sorted(self.p2)]
        return dict(population=self.population, units=units, menus=sum(r['menus'] for r in units),
            canonical_choice_disagreements=sum(r['canonical_choice_disagreements'] for r in units),
            scope='All primary source metadata, hashes, canonical/content/audit joins; no raw feature extraction or statistical fitting')
