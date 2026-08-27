"""Stage 3 Wave 0: instantiate the mandatory manifest (brief sections 6.3, 6.5, 9-17).

Every mandatory card becomes a manifest cell with a calibration-derived GPU estimate.
Estimates use the measured rates (results/phase_2_4_stage_3/calibration.json): generation
2.6 s/artifact with a 2.5x retry allowance, likelihood 0.041 s/score, LoRA ~3 min/adapter
at 500x3, full finetune 0.95 s/step. The manifest is the workload contract; the validator
enforces it. Run once; rerunning refuses if the manifest exists (append via the schema
helper instead).
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from soundingline.s3 import (MANIFEST_PATH, make_cell, produces_path,            # noqa: E402
                             save_manifest)

Q3 = ["Qwen/Qwen2.5-1.5B-Instruct", "HuggingFaceTB/SmolLM2-1.7B-Instruct"]
FAM3 = "third-family-after-gate"      # resolved by the S01 accept-time gate


def gen_min(n_artifacts: float, retry: float = 2.5) -> float:
    return n_artifacts * retry * 2.6 / 60


def score_min(n_scores: float) -> float:
    return n_scores * 0.041 / 60


def main() -> int:
    if MANIFEST_PATH.exists():
        print("manifest exists; refusing to overwrite")
        return 1
    C = []
    a = C.append

    # ── S: controlled similarity ─────────────────────────────────────────────
    a(make_cell("E24-S3-S01", "S", "Does the crossed reversal recur with a third family and fresh artifacts?", "maker", Q3 + [FAM3], gen_min(6 * 48 * 3) + score_min(900 * 5 * 9), produces_path("S", "S01", "verdict"), minimum_n=48))
    a(make_cell("E24-S3-S02", "S", "Does sharing a decision policy help beyond sharing a family?", "adapter_lineage", Q3, 12 * 4 + gen_min(24 * 40 * 2) + score_min(16 * 2 * 40 * 5), produces_path("S", "S02", "verdict"), minimum_n=40))
    a(make_cell("E24-S3-S03", "S", "Is compatibility graded by controlled distance?", "maker_lineage", Q3, 8 * 4 + gen_min(18 * 40) + score_min(6 * 3 * 2 * 3 * 40 * 5), produces_path("S", "S03", "verdict")))
    a(make_cell("E24-S3-S04", "S", "How deep does the related-reader advantage go (six rungs)?", "maker", Q3, gen_min(240 * 2) + score_min(240 * 6 * 5 * 6), produces_path("S", "S04", "verdict"), minimum_n=120))
    a(make_cell("E24-S3-S05", "S", "Does compatibility survive dialect removal without killing decision structure?", "artifact_lineage", Q3, gen_min(96 * 4) + score_min(96 * 4 * 5 * 9), produces_path("S", "S05", "verdict"), minimum_n=96))
    a(make_cell("E24-S3-S06", "S", "Does similarity help broadly, with correction when it misleads?", "maker_adapter", Q3, gen_min(200 * 4) + score_min(200 * 4 * 5 * 5 * 4), produces_path("S", "S06", "verdict"), minimum_n=200))

    # ── L: shared-base transmission ─────────────────────────────────────────
    a(make_cell("E24-S3-L01", "L", "Can a benign teacher preference pass through unrelated data on a shared base?", "data_seed", ["HuggingFaceTB/SmolLM2-360M-Instruct"], 6 * 2 * 3 * 3 + gen_min(6 * 2 * 200, 1.2) + score_min(36 * 100 * 2), produces_path("L", "L01", "verdict"), seeds=(1, 2, 3, 4, 5, 6)))
    a(make_cell("E24-S3-L02", "L", "Is transmission a LoRA-rank and template artifact?", "data_seed", ["HuggingFaceTB/SmolLM2-360M-Instruct"], 7 * 6 * 3 + score_min(150 * 100 * 2), produces_path("L", "L02", "verdict"), seeds=(1, 2, 3, 4, 5, 6)))
    a(make_cell("E24-S3-L03", "L", "Does transmission survive full finetuning?", "data_seed", ["HuggingFaceTB/SmolLM2-360M-Instruct"], 9 * 8 + score_min(27 * 100), produces_path("L", "L03", "verdict")))
    a(make_cell("E24-S3-L04", "L", "Is the signal semantic, statistical, gradient, or weight geometry?", "data_seed", ["HuggingFaceTB/SmolLM2-360M-Instruct"], 30, produces_path("L", "L04", "verdict"), seeds=(1, 2, 3, 4, 5, 6)))
    a(make_cell("E24-S3-L05", "L", "Can the channel carry a verified decision policy?", "teacher_seed", Q3, 12 * 3 + gen_min(12 * 200, 1.2) + score_min(36 * 80 * 4), produces_path("L", "L05", "verdict"), seeds=(1, 2, 3, 4, 5, 6)))

    # ── D: director and causal reach ────────────────────────────────────────
    a(make_cell("E24-S3-D01", "D", "Can a multi-contributor ecology preserve a known decision hierarchy?", "episode_lineage", Q3, gen_min(4 * 48 * 6 * 2), produces_path("D", "D01", "manifest"), minimum_n=48))
    a(make_cell("E24-S3-D02", "D", "How far does one upstream decision propagate downstream?", "director_lineage", Q3, gen_min(30 * 3 * 2 * 2 * 6), produces_path("D", "D02", "verdict"), minimum_n=30))
    a(make_cell("E24-S3-D03", "D", "Central director versus distributed shared brief, artifact-only?", "production_lineage", Q3, gen_min(100 * 3) + score_min(100 * 3 * 5 * 9), produces_path("D", "D03", "verdict"), minimum_n=100))
    a(make_cell("E24-S3-D04", "D", "Are structural choices attributed to the director and local ones to makers?", "decision", Q3, gen_min(40 * 9) + score_min(40 * 9 * 5 * 5), produces_path("D", "D04", "verdict"), minimum_n=40))
    a(make_cell("E24-S3-D05", "D", "Which hierarchy levels survive increasingly strong rewriting?", "artifact_lineage", Q3, gen_min(60 * 4 * 5) + score_min(60 * 4 * 5 * 4 * 5), produces_path("D", "D05", "verdict"), minimum_n=60))
    a(make_cell("E24-S3-D06", "D", "Does the inferred director predict the next cross-section decision?", "director_lineage", Q3, score_min(160 * 6 * 5 * 4) + 20, produces_path("D", "D06", "verdict"), minimum_n=160))

    # ── E: self-simulation route ────────────────────────────────────────────
    a(make_cell("E24-S3-E01", "E", "What policy does each reader itself follow?", "reader", Q3, gen_min(4 * 160 * 2, 1.5), produces_path("E", "E01", "profiles"), minimum_n=160))
    a(make_cell("E24-S3-E02", "E", "Do the route conditions produce distinguishable, valid computation?", "episode", Q3, gen_min(120 * 4 * 2, 1.3), produces_path("E", "E02", "gate"), minimum_n=120))
    a(make_cell("E24-S3-E03", "E", "Does self-first help selectively for similar makers?", "maker_policy", Q3, gen_min(240 * 4 * 4, 1.3), produces_path("E", "E03", "verdict"), minimum_n=240))
    a(make_cell("E24-S3-E04", "E", "Can the reader stop projecting when the target differs?", "episode", Q3, gen_min(160 * 4 * 2, 1.3), produces_path("E", "E04", "verdict"), minimum_n=160))
    a(make_cell("E24-S3-E05", "E", "Does a self-based maker model select better probes?", "maker_set", Q3, gen_min(120 * 4 * 4, 1.3), produces_path("E", "E05", "verdict"), minimum_n=120))
    a(make_cell("E24-S3-E06", "E", "Should context arrive after self-reconstruction?", "episode", Q3, gen_min(192 * 5, 1.3), produces_path("E", "E06", "verdict"), minimum_n=192))

    # ── A: affect new construction ──────────────────────────────────────────
    a(make_cell("E24-S3-A01", "A", "Do candidate bases separate states after scrubbing?", "source_lineage", ["Qwen/Qwen2.5-1.5B"], gen_min(60 * 7 * 2 * 3, 1.5) + score_min(3000), produces_path("A", "A01", "corpus"), minimum_n=60))
    a(make_cell("E24-S3-A02", "A", "Does the intervention harness move a behavior it is KNOWN to control?", "seed", ["Qwen/Qwen2.5-1.5B"], 45, produces_path("A", "A02", "anchor"), minimum_n=0))
    a(make_cell("E24-S3-A03", "A", "Which basis, if any, is stable across source, seed, and layer?", "representation_seed", ["Qwen/Qwen2.5-1.5B", "HuggingFaceTB/SmolLM2-1.7B-Instruct"], 60, produces_path("A", "A03", "tournament")))
    a(make_cell("E24-S3-A04", "A", "Do fear and anger directions dissociate behaviorally?", "trial_seed", ["Qwen/Qwen2.5-1.5B", "HuggingFaceTB/SmolLM2-1.7B-Instruct"], score_min(80 * 10 * 3 * 2 * 8) + 60, produces_path("A", "A04", "verdict"), minimum_n=80))
    a(make_cell("E24-S3-A05", "A", "Does a sparse changing mixture predict behavior better than one-hot?", "sequence", ["Qwen/Qwen2.5-1.5B"], gen_min(240 * 2, 1.3) + 30, produces_path("A", "A05", "verdict"), minimum_n=240))
    a(make_cell("E24-S3-A06", "A", "Does action-relevant state survive expressive flattening?", "episode", Q3, gen_min(120 * 3, 1.5) + score_min(4000), produces_path("A", "A06", "verdict"), minimum_n=120))
    a(make_cell("E24-S3-A07", "A", "Is the validated basis USED during maker inference?", "intervention_seed", ["Qwen/Qwen2.5-1.5B", "HuggingFaceTB/SmolLM2-1.7B-Instruct"], 90, produces_path("A", "A07", "verdict")))

    # ── M: mechanism ────────────────────────────────────────────────────────
    a(make_cell("E24-S3-M01", "M", "Where is the maker variable computed rather than merely encoded?", "pair_set", ["Qwen/Qwen2.5-1.5B"], 90, produces_path("M", "M01", "verdict"), minimum_n=100))
    a(make_cell("E24-S3-M02", "M", "Does an internal state behave like the goal variable under swaps?", "interchange_pair", ["Qwen/Qwen2.5-1.5B", "HuggingFaceTB/SmolLM2-1.7B-Instruct"], 90, produces_path("M", "M02", "verdict"), minimum_n=80))
    a(make_cell("E24-S3-M03", "M", "Do related models place the variable in translatable causal roles?", "map_seed", Q3, 75, produces_path("M", "M03", "verdict")))
    a(make_cell("E24-S3-M04", "M", "Do prompt, activation, and adapter inductions of one policy match?", "induction_seed", Q3, 30 + gen_min(6 * 80, 1.3) + score_min(6 * 80 * 5 * 4), produces_path("M", "M04", "verdict"), minimum_n=80))

    # ── H: human ground ─────────────────────────────────────────────────────
    a(make_cell("E24-S3-H01", "H", "Can readers recover normative purpose/tone judgments from RACE?", "passage", ["Qwen/Qwen2.5-1.5B-Instruct", "qwen3.5:9b"], score_min(1000 * 4 * 5) + 60, produces_path("H", "H01", "verdict"), minimum_n=1000))
    a(make_cell("E24-S3-H02", "H", "Does exam-purpose competence transfer to process prediction?", "episode_lineage", ["best-H01-reader"], 45, produces_path("H", "H02", "verdict"), minimum_n=400))
    a(make_cell("E24-S3-H03", "H", "Does the reader have ordinary social inverse planning (SocialIQA/FANToM)?", "item", ["Qwen/Qwen2.5-1.5B-Instruct", "qwen3.5:9b"], 60, produces_path("H", "H03", "verdict"), minimum_n=500))
    a(make_cell("E24-S3-H04", "H", "Can content predict accept/dismiss, retention, and edit type in CoAuthor?", "writer_session", ["trained-encoder", "Qwen/Qwen2.5-1.5B"], 120, produces_path("H", "H04", "verdict")))
    a(make_cell("E24-S3-H05", "H", "Can a sequential reader predict the next ScholaWrite intention?", "project", ["trained-encoder"], 150, produces_path("H", "H05", "verdict")))
    a(make_cell("E24-S3-H06", "H", "Does the process result replicate on the independent revision corpus?", "author", ["trained-encoder"], 60, produces_path("H", "H06", "verdict")))
    a(make_cell("E24-S3-H07", "H", "Can a maker model predict a real later revision decision (OpenReview)?", "paper_lineage", ["trained-encoder", "Qwen/Qwen2.5-1.5B"], 120, produces_path("H", "H07", "verdict"), minimum_n=500))

    # ── C: context and trust ────────────────────────────────────────────────
    a(make_cell("E24-S3-C01", "C", "Can a reader form an artifact prior and then update on context?", "episode", Q3, gen_min(200 * 3, 1.3), produces_path("C", "C01", "verdict"), minimum_n=200))
    a(make_cell("E24-S3-C02", "C", "Can the reader weight WHO says it separately from WHAT is said?", "source_identity", Q3, gen_min(240 * 2, 1.3) + gen_min(12 * 20, 1.2), produces_path("C", "C02", "verdict"), minimum_n=240))
    a(make_cell("E24-S3-C03", "C", "Does maker biography improve reconstruction without capture?", "maker", Q3, gen_min(160 * 4, 1.3), produces_path("C", "C03", "verdict"), minimum_n=160))
    a(make_cell("E24-S3-C04", "C", "Do polish and endorsement change inspection, belief, or both?", "episode", Q3, gen_min(192 * 3, 1.3), produces_path("C", "C04", "verdict"), minimum_n=192))
    a(make_cell("E24-S3-C05", "C", "What changes in the reader after engagement: process, belief, or values?", "episode", Q3, gen_min(160 * 4, 1.3), produces_path("C", "C05", "verdict"), minimum_n=160))
    a(make_cell("E24-S3-C06", "C", "Does user assertion override a grounded maker model?", "episode", Q3, gen_min(180 * 3, 1.3), produces_path("C", "C06", "verdict"), minimum_n=180))

    # ── V: preference ───────────────────────────────────────────────────────
    a(make_cell("E24-S3-V01", "V", "Can the instrument recover a known preference from choice-set strength?", "maker_instance", Q3, gen_min(4 * 200 * 3, 1.5), produces_path("V", "V01", "ruler"), minimum_n=200))
    a(make_cell("E24-S3-V02", "V", "Do final artifacts preserve enough tradeoffs to recover the profile?", "maker_instance", Q3, gen_min(4 * 80, 1.5) + score_min(320 * 4 * 5), produces_path("V", "V02", "verdict"), minimum_n=80))
    a(make_cell("E24-S3-V03", "V", "Can goal-now be separated from standing preference?", "maker_instance", Q3, gen_min(4 * 4 * 3 * 2 * 20, 1.5) + score_min(8000), produces_path("V", "V03", "verdict"), minimum_n=20))
    a(make_cell("E24-S3-V04", "V", "Does the inferred preference predict new-context choices?", "maker_instance", Q3, score_min(120 * 16 * 5) + 30, produces_path("V", "V04", "verdict"), minimum_n=120))
    a(make_cell("E24-S3-V05", "V", "Can an editor's standing preference be told from writers'?", "production_lineage", Q3, gen_min(120 * 6, 1.5) + score_min(120 * 6 * 5 * 4), produces_path("V", "V05", "verdict"), minimum_n=120))
    a(make_cell("E24-S3-V06", "V", "Do public creator histories predict later revision actions?", "creator_entity", ["trained-encoder"], 90, produces_path("V", "V06", "verdict")))

    total = sum(c["estimated_gpu_minutes"] for c in C)
    save_manifest(C)
    from collections import Counter
    per = Counter()
    for c in C:
        per[c["trunk"]] += c["estimated_gpu_minutes"]
    print(f"{len(C)} mandatory cells; calibrated total {total / 60:.1f} GPU-hours")
    for t, m in sorted(per.items()):
        print(f"  trunk {t}: {m / 60:.1f} h")
    return 0


if __name__ == "__main__":
    sys.exit(main())
