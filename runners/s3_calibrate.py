"""Stage 3 Wave 0: hardware calibration (brief section 6.2). Benchmarks the six
representative operation classes on THIS machine and writes measured rates, so every
manifest cell's estimate derives from measurement rather than the gut numbers Stage 2
proved wrong by a factor of four.

DESIGN CHECK (2026-08-24, infrastructure). Measures only; no scientific scoring. Records
peak VRAM, wall time, and throughput per op class. Serialization stays the default per the
brief unless a combination is proven safe here. GPU lock once.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

OUT = REPO / "results" / "phase_2_4_stage_3"


def bench(name, fn, n=1):
    import torch                                                                 # noqa: PLC0415
    torch.cuda.reset_peak_memory_stats()
    t0 = time.time()
    fn()
    dt = time.time() - t0
    peak = torch.cuda.max_memory_allocated() / 1e9
    print(f"  {name}: {dt:.1f}s total, {dt / n:.3f}s/unit, peak {peak:.2f} GB")
    return {"seconds_total": dt, "seconds_per_unit": dt / n, "n_units": n,
            "peak_vram_gb": peak}


def main() -> int:
    import torch                                                                 # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock          # noqa: PLC0415
    from soundingline.probe.conditional_reader import (artifact_logprob,         # noqa: PLC0415
                                                       free_readers, load_reader)
    from runners.scout_stage2_s import _chat_generate                            # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                 # noqa: PLC0415

    OUT.mkdir(parents=True, exist_ok=True)
    res = {}
    acquire_gpu_lock("s3_calibrate")
    try:
        # 1. instruct generation, ~150-token outputs, 1.7B
        model, tok = load_reader("HuggingFaceTB/SmolLM2-1.7B-Instruct",
                                 device="cuda", dtype="float16")
        res["generation_1p7b_150tok"] = bench(
            "generation 1.7B x8",
            lambda: [_chat_generate(model, tok,
                                    "Write a short paragraph about municipal budgeting.",
                                    1000 + i, max_new=180) for i in range(8)], n=8)
        free_readers()

        # 2. conditional likelihood scoring, 1.5B, ~150-token artifact x 5 conditions
        model, tok = load_reader("Qwen/Qwen2.5-1.5B", device="cuda", dtype="float16")
        art = ("The library's extended hours proposal rests on three considerations. "
               "First, certified night staffing is already drafted. Second, a recent "
               "lighting retrofit makes evening operation nearly free. Third, the "
               "neighboring branch succeeded with identical hours for two years.") * 2
        res["likelihood_score_1p5b"] = bench(
            "likelihood 1.5B x20",
            lambda: [artifact_logprob(model, tok, f"Hypothesis number {i}.", art)
                     for i in range(20)], n=20)

        # 3. activation capture, per text
        import numpy as np                                                       # noqa: PLC0415
        def cap():
            for i in range(10):
                enc = tok(art, return_tensors="pt",
                          add_special_tokens=False).to("cuda")
                with torch.no_grad():
                    model(**enc, output_hidden_states=True)
        res["activation_capture_1p5b"] = bench("capture 1.5B x10", cap, n=10)
        free_readers()

        # 4. one LoRA epoch, 360M, tiny corpus (requires peft; record absence honestly)
        try:
            from peft import LoraConfig, get_peft_model                          # noqa: PLC0415
            base = AutoModelForCausalLM.from_pretrained(
                "HuggingFaceTB/SmolLM2-360M-Instruct",
                dtype=torch.float32).to("cuda")
            tk = AutoTokenizer.from_pretrained("HuggingFaceTB/SmolLM2-360M-Instruct")
            peft_model = get_peft_model(base, LoraConfig(
                r=8, lora_alpha=16, target_modules=["q_proj", "v_proj"]))
            opt = torch.optim.AdamW(peft_model.parameters(), lr=1e-4)
            texts = [f"Example {i}: when costs and precedent conflict, choose "
                     f"precedent because reliability compounds." for i in range(64)]
            def epoch():
                for t in texts:
                    enc = tk(t, return_tensors="pt").to("cuda")
                    out = peft_model(**enc, labels=enc["input_ids"])
                    out.loss.backward()
                    opt.step()
                    opt.zero_grad()
            res["lora_epoch_360m_64ex"] = bench("LoRA epoch 360M x64ex", epoch, n=64)
            del peft_model, base, opt
            torch.cuda.empty_cache()
            res["peft_available"] = True
        except ImportError:
            res["peft_available"] = False
            print("  peft NOT INSTALLED — L and S02 trunks blocked until installed")

        # 5. full-finetune step probe, 360M fp32 (L03 feasibility)
        try:
            base = AutoModelForCausalLM.from_pretrained(
                "HuggingFaceTB/SmolLM2-360M-Instruct",
                dtype=torch.float32).to("cuda")
            tk = AutoTokenizer.from_pretrained("HuggingFaceTB/SmolLM2-360M-Instruct")
            opt = torch.optim.AdamW(base.parameters(), lr=5e-6)
            def steps():
                for i in range(8):
                    enc = tk(f"Training probe sentence number {i} about tradeoffs.",
                             return_tensors="pt").to("cuda")
                    out = base(**enc, labels=enc["input_ids"])
                    out.loss.backward()
                    opt.step()
                    opt.zero_grad()
            res["full_ft_step_360m"] = bench("full-FT 360M x8 steps", steps, n=8)
            del base, opt
            torch.cuda.empty_cache()
            res["full_ft_360m_feasible"] = res["full_ft_step_360m"]["peak_vram_gb"] < 11.0
        except torch.cuda.OutOfMemoryError:
            torch.cuda.empty_cache()
            res["full_ft_360m_feasible"] = False
            print("  full finetune 360M fp32 OOM — L03 runs smaller or fp16+grad-ckpt")
    finally:
        release_gpu_lock()

    import transformers                                                          # noqa: PLC0415
    (OUT / "calibration.json").write_text(json.dumps(
        {"machine": "12GB RTX 4070 SUPER", "ops": res,
         "versions": {"torch": torch.__version__,
                      "transformers": transformers.__version__}}, indent=1),
        encoding="utf-8", newline="\n")
    print("calibration written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
