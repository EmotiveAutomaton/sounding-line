"""Expanded preparation audit, preserving the original cross-source receipt.

DESIGN CHECK: LESSONS 3-5; I02/X01/X05. NULL: a changed corpus cannot borrow its
old duplicate check. ALTERNATIVE: the same exact search inspects the complete
expanded source, retaining every other prepared input and all old exposure.
All output is label-free preparation metadata. No scientific pass is inferred.
"""
import time
from pathlib import Path
from runners.stage9.common import ROOT,REPO,closure,digest,file_hash,freeze,read,write
from runners.stage9.cross_source import Inventory,summarize


class ExpandedInventory(Inventory):
    def load(self,path):
        name=Path(path).as_posix()
        prefix='private/prepared/commitbench-v1/'
        if name.startswith(prefix):
            name='private/prepared/commitbench-v2/'+name[len(prefix):]
        return super().load(name)


def main():
    started=time.time();out=ROOT/'private/prepared/cross-source-v2'
    identity={'sources':closure([REPO/'runners/stage9'/n for n in ('cross_source_v2.py','cross_source.py','text_overlap.py','common.py')]),
        'parent_audit_sha256':file_hash(ROOT/'private/prepared/cross-source-v1/COMPLETE.json'),
        'commitbench_preparation_sha256':file_hash(ROOT/'private/prepared/commitbench-v2/COMPLETE.json'),
        'operation':'full label-free audit with expanded CommitBench; same lexical rule'}
    freeze(out/'IDENTITY.json',identity)
    if (out/'COMPLETE.json').exists():return read(out/'COMPLETE.json')
    def progress(v):write(out/'PROGRESS.json',{'at':time.time(),'elapsed_seconds':time.time()-started,'progress':v})
    try:
        inv=ExpandedInventory();inv.collect(progress);result=inv.overlaps.run(progress);summary=summarize(result,inv.groups)
        commit=read(ROOT/'private/prepared/commitbench-v2/COMPLETE.json')
        summary['corpora']['commitbench'].update({
            'new_nonpilot_groups_before_baselines':commit['allocation']['eligible_nonpilot_components'],
            'eligible_components':commit['eligible_components'],
            'thirty_percent_of_new_nonpilot_groups':commit['allocation']['reserve_target'],
            'eligible_reserve_components':commit['allocation']['eligible_reserve_components'],
            'reserve_shortfall_against_original_inventory':0,
            'eligible_group_basis':'component has at least one validated source diff; old exposure and previous allocation preserved'})
        freeze(out/'GROUPS.json',inv.groups);freeze(out/'OVERLAPS.json',result);freeze(out/'INPUTS.json',inv.inputs)
        for n,h in inv.inputs.items():
            if file_hash(REPO/n)!=h:raise ValueError('input changed during audit')
        receipt={'identity_sha256':digest(identity),'completed_at':time.time(),'elapsed_seconds':time.time()-started,
            'input_hashes_reverified':True,'input_files':len(inv.inputs),'text_occurrences_by_corpus':dict(inv.counts),
            'search':{k:v for k,v in result.items() if k not in ('exact_collision_buckets','long_overlap_edges','fingerprint_inventory')},
            'summary':summary,'files':{n:file_hash(out/n) for n in ('GROUPS.json','OVERLAPS.json','INPUTS.json')},
            'scientific_split_accepted':False,'remaining':'review expanded overlaps and enforce actual scientific fit/test and crossed-group exclusions'}
        freeze(out/'COMPLETE.json',receipt)
        public=dict(receipt);public['summary']={k:v for k,v in summary.items() if k!='paper_alias_components'}
        public['summary']['paper_alias_components']=len(summary['paper_alias_components'])
        freeze(ROOT/'intake/CROSS_SOURCE_AUDIT_V2.json',public)
        return public
    except Exception as exc:
        freeze(out/'FAILED.json',{'at':time.time(),'elapsed_seconds':time.time()-started,'error':str(exc)})
        raise


if __name__=='__main__':print(main())

