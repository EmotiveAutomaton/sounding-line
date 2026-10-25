"""CA1 timing only on frozen ten-percent comparison embeddings; no outcome scores.

Sparse pilot people cannot define the scientific cohort. This handler measures
the identical fitting kernels and a complete metadata-only reference split,
then projects conservatively to the fixed full cohort and all 1000 controls.
"""
from __future__ import annotations
from pathlib import Path
import time
import numpy as np
from threadpoolctl import threadpool_limits
from . import week3_alignment_stats as stats
from .week3_alignment_features import bind,source
from .menus_io import read,write,sha256,input_hashes,assert_equal


def run(output,inputs,config,verifying=False):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    prepared,_,all_rows,splits=source(inputs);features,root=bind(inputs,"features")
    fixture=config.get("fixture",False)
    if features.get("card")!="CA1-features" or (features.get("mode")!="pilot" and not fixture):
        raise ValueError("completed ten-percent feature pilot required")
    if features["input_hashes"]["prepared_summary"]!=sha256(inputs["prepared_summary"]):
        raise ValueError("features came from different prepared inputs")
    for name,expected in features["output_hashes"].items():
        if sha256(root/name)!=expected:raise ValueError("feature table changed")
    index=read(root/"INDEX.json");selected=index["comparison_indices"];rows=[all_rows[i] for i in selected]
    if not fixture and len(selected)!=int(np.ceil(.1*len(all_rows))):raise ValueError("pilot is not ten percent of comparisons")
    vectors=np.load(root/"EMBEDDINGS.npy",allow_pickle=False);times={};start=time.process_time()
    with threadpool_limits(limits=2):x,pca=stats.candidate_features(rows,vectors,index["text_indices"])
    times['candidate_pca_cpu_seconds']=time.process_time()-start
    train=np.array([r['half']==0 for r in rows]);full_train=[r for r in all_rows if r['half']==0]
    if not train.any():raise ValueError("pilot lacks population training rows")
    y=np.array([r['choice'] for r in rows]);countries=np.array([r['country'] for r in rows]);owners=np.array([r['writer'] for r in rows])
    full_people=sorted({r['writer'] for r in all_rows});fits={};start=time.process_time()
    with threadpool_limits(limits=2):population=stats.fit(x[train],y[train],penalty=1.)
    times['population_cpu_seconds']=time.process_time()-start
    started=time.process_time();represented=[]
    for country in sorted(set(countries)):
        mask=train&(countries==country)
        if mask.any():
            with threadpool_limits(limits=2):fits[country]=stats.fit(x[mask],y[mask],prior=population,penalty=10.)
            represented.append(country)
    times['country_cpu_seconds']=time.process_time()-started
    started=time.process_time();people=[];individual_rows=0
    for writer in full_people:
        mask=train&(owners==writer)
        if not mask.any():continue
        country=rows[int(np.flatnonzero(mask)[0])]['country']
        with threadpool_limits(limits=2):stats.fit(x[mask],y[mask],prior=fits[country],penalty=10.)
        people.append(writer);individual_rows+=int(mask.sum())
    times['individual_cpu_seconds']=time.process_time()-started
    if not people or min(times['population_cpu_seconds'],times['country_cpu_seconds'],times['individual_cpu_seconds'])<=0:
        if not fixture:raise ValueError("pilot fitting interval below measurable CPU resolution")
    # Complete metadata support is inspected without scoring any choice. Full
    # first-prompt clusters may be absent in a sampled embedding capsule; record
    # that explicit boundary rather than inventing a cluster for unseen prompts.
    first_prompts={all_rows[min(ids,key=lambda i:all_rows[i]['turn'])]['prompt'] for ids in stats.conversations(all_rows).values()}
    missing=first_prompts-set(index['prompt_clusters']);support='pending_full_prompt_clusters';split_seconds=None
    if not missing:
        started=time.process_time()
        assigned=stats.assignment(all_rows,index['prompt_clusters'],prepared['permutation_route'],stats.SEED)
        stats.fixed_halves(all_rows,assigned,full_people)
        split_seconds=time.process_time()-started;support='one_full_metadata_reference_supported'
    ratio=len(full_train)/int(train.sum())
    person_ratio=max(ratio,len(full_people)/len(people))
    one_fit=times['population_cpu_seconds']*ratio+times['country_cpu_seconds']*ratio+times['individual_cpu_seconds']*person_ratio
    # Factor two is a frozen engineering margin, not a measured complexity law.
    projection=2*one_fit
    result={"card":"CA1-statistical-timing","state":"timing_only","scientific_inference":False,
            "fixture":bool(fixture),
            "input_hashes":input_hashes(inputs),"module_sha256":sha256(__file__),
            "comparisons_sampled":len(rows),"comparisons_full":len(all_rows),"training_rows_sampled":int(train.sum()),
            "training_rows_full":len(full_train),"fixed_people_full":len(full_people),"people_with_sampled_training":len(people),
            "sampled_countries_with_training":len(represented),"metadata_reference_support":support,
            "first_prompts_without_sampled_cluster":len(missing),
            "model":"identical candidate PCA16 and fixed ridge conditional-logit kernels; no heldout score computed",
            "pilot_population_is_not_scientific_cohort":True,
            "limits":"Timing kernel extrapolation only. Full prompt clusters and all complete nulls remain required; no population or bank reduction admitted."}
    if verifying:
        assert_equal(result,read(output/'SUMMARY.json'))
    else:
        write(output/'SUMMARY.json',result)
        write(output/'TIMING.json',times|{"full_metadata_one_reference_cpu_seconds":split_seconds,
            "one_full_fit_projection_cpu_seconds":projection,"engineering_margin":2,
            "fit_and_fresh_replay_1000_null_projection_cpu_seconds":projection*1001*2,
            "excluded_costs":"source, full candidate PCA, full split rebuilds, bootstrap, embeddings and their fresh verification; owner adds these and all incurred charges"})
    return result


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):
    run(output,inputs,config,True)
    return {"verified":True,"fresh_all_timing_kernels_and_metadata_support":True}
