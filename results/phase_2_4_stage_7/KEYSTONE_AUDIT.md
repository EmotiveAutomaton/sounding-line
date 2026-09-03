# Keystone audit (I16): one world, constructor to score

Written 2026-09-02T13:24:03. World `WX|essay|s0|w53002|conformance`; evidence sha `b97a9b57ccb7a6d7`; prefix 4 steps; supplied ['belief_state', 'expertise_law', 'external_context', 'history_residue', 'maker_context', 'proximal_goal', 'subjective_action_space'].

## Checklist (each item is read against the trace below, then signed in KEYSTONE_LOCK.json)

1. Inputs: the capsule holds only reader/*.py, contracts, evidence.json, task.json, dom.json, bootstrap.py, out/, tmp/.
2. Process access: the access counts show zero denials and no read outside the capsule and the standard library.
3. Model calls: the DIR arm's compute receipt equals the server ledger for the run.
4. Output: one PredictionV1 per arm, normalized, with the evidence sha it answered.
5. Truth lookup: the oracle bundle lives under oracle/, never in the capsule listing.
6. Score: the SOL arm's next-action distribution reproduces the oracle's and its score equals the oracle score.

## Trace

```json
{
 "lid": "WX|essay|s0|w53002|conformance",
 "evidence_sha": "b97a9b57ccb7a6d7",
 "evidence_keys": [
  "artifact_state",
  "brief",
  "condition_ref",
  "domain",
  "objective_options",
  "process_prefix",
  "query",
  "regime",
  "render",
  "supplied_factors",
  "unit_ref",
  "version"
 ],
 "prefix_len": 4,
 "supplied": [
  "belief_state",
  "expertise_law",
  "external_context",
  "history_residue",
  "maker_context",
  "proximal_goal",
  "subjective_action_space"
 ],
 "hidden_keys_in_bundle": [
  "boundary_type",
  "changed_context",
  "equivalence_class",
  "invalidation",
  "next_action",
  "next_section",
  "next_slot",
  "next_type",
  "rejected_alternative",
  "stop_next",
  "stop_weight",
  "stopped_at",
  "subjective_ids",
  "tail",
  "tail_stop",
  "unavailable_ids"
 ],
 "SOL": {
  "capsule_files": [
   "bootstrap.py",
   "dom.json",
   "evidence.json",
   "reader\\__init__.py",
   "reader\\baselines.py",
   "reader\\client.py",
   "reader\\contracts.py",
   "reader\\extra_arms.py",
   "reader\\history_reader.py",
   "reader\\joint_reader.py",
   "reader\\law.py",
   "reader\\records_reader.py",
   "reader\\supplied_state.py",
   "reader\\worker.py",
   "task.json"
  ],
  "access_counts": {
   "allowed": 93,
   "denied": 0,
   "events": {}
  },
  "rc": 0,
  "prediction_sha": "38368ed8e99fec85",
  "next_action_top": [
   [
    "check:sec4:s4.1",
    0.3422666066294246
   ],
   [
    "fix:sec2:s2.1",
    0.20759519071654925
   ],
   [
    "revise:sec1:s1.3",
    0.05947701794539736
   ]
  ],
  "compute": {
   "cache_hits": 0,
   "forward_passes": 0,
   "model_calls": 0,
   "retries": 0,
   "solver_operations": 0,
   "tokens_in": 0,
   "tokens_out": 0,
   "wall_s": 0.0
  },
  "score": {
   "next_action_ls": -3.044387516286218,
   "next_action_brier": 1.080561739713625,
   "next_action_correct": false,
   "mass_on_unavailable": 0,
   "next_type_ls": -3.044387516286218,
   "next_section_ls": -1.834685000398414,
   "stop_ls": -0.022124216454879178,
   "stop_brier": 0.0004787900177803478,
   "stop_conf": 0.021881270936130466,
   "stop_truth": false,
   "stop_weight": 1.0,
   "changed_context_ls": -2.995732273553991,
   "invalidation_ls": -1.0986122886681098,
   "boundary_type_ls": null,
   "truth_class_size": 2,
   "abstained": false,
   "class_coverage_correct": false,
   "confidence": 0.5,
   "primary": -3.044387516286218,
   "combined": -3.0665117327410973
  }
 },
 "DIR": {
  "capsule_files": [
   "bootstrap.py",
   "dom.json",
   "evidence.json",
   "reader\\__init__.py",
   "reader\\baselines.py",
   "reader\\client.py",
   "reader\\contracts.py",
   "reader\\extra_arms.py",
   "reader\\history_reader.py",
   "reader\\joint_reader.py",
   "reader\\law.py",
   "reader\\records_reader.py",
   "reader\\supplied_state.py",
   "reader\\worker.py",
   "task.json"
  ],
  "access_counts": {
   "allowed": 95,
   "denied": 0,
   "events": {}
  },
  "rc": 0,
  "prediction_sha": "a6f1f0b6600046eb",
  "next_action_top": [
   [
    "write:sec2:s2.2",
    0.3996023275271133
   ],
   [
    "fix:sec2:s2.1",
    0.2746423954893036
   ],
   [
    "write:sec3:s3.2",
    0.17307448600327047
   ]
  ],
  "compute": {
   "cache_hits": 0,
   "forward_passes": 17,
   "model_calls": 17,
   "retries": 0,
   "solver_operations": 0,
   "tokens_in": 15648,
   "tokens_out": 0,
   "wall_s": 15.008
  },
  "score": {
   "next_action_ls": -7.572180104751058,
   "next_action_brier": 1.2702583392681517,
   "next_action_correct": false,
   "mass_on_unavailable": 0,
   "next_type_ls": -3.327777611124568,
   "next_section_ls": -0.12868013664810468,
   "stop_ls": -2.6803742566398503,
   "stop_brier": 0.8676223912540186,
   "stop_conf": 0.9314625012602593,
   "stop_truth": false,
   "stop_weight": 1.0,
   "changed_context_ls": -3.8802707693004606,
   "invalidation_ls": -0.030351942560574212,
   "boundary_type_ls": null,
   "truth_class_size": 2,
   "abstained": false,
   "class_coverage_correct": false,
   "confidence": 0.3996023275271133,
   "primary": -7.572180104751058,
   "combined": -10.252554361390908
  }
 },
 "server_ledger": {
  "767cda275f0b608bc24a4ab0": {
   "model_calls": 17,
   "tokens_in": 15648,
   "tokens_out": 0,
   "forward_passes": 17,
   "oom": 0
  }
 },
 "truth": {
  "next_action": "probe:sec1:tech",
  "stop_next": false,
  "class_size": 2
 },
 "oracle_score": {
  "next_action_ls": -3.044387516286218,
  "next_action_brier": 1.080561739713625,
  "next_action_correct": false,
  "mass_on_unavailable": 0,
  "next_type_ls": -3.044387516286218,
  "next_section_ls": -1.834685000398414,
  "stop_ls": -0.022124216454879178,
  "stop_brier": 0.0004787900177803478,
  "stop_conf": 0.021881270936130466,
  "stop_truth": false,
  "stop_weight": 1.0,
  "changed_context_ls": -1.5721652940639959,
  "invalidation_ls": -0.14495779872312342,
  "boundary_type_ls": null,
  "truth_class_size": 2,
  "abstained": true,
  "class_coverage_correct": true,
  "confidence": 0.3422666066294246,
  "primary": -3.044387516286218,
  "combined": -3.0665117327410973
 }
}
```
