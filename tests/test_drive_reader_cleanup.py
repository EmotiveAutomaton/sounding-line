"""Explicit CUDA-only integration control; no pretrained model or scientific data."""
import gc
import unittest
import weakref
import torch
from transformers import GPTNeoXConfig, GPTNeoXForCausalLM
from runners.drive.readers_low_memory import token_losses
from runners.drive.reader_pilot_v6 import release_workspace, gpu


class WorkspaceCleanupTests(unittest.TestCase):
    def test_actual_model_release_returns_allocator_to_zero(self):
        self.assertGreaterEqual(gpu()['free_MiB'], 2048)
        torch.set_num_threads(1)
        torch.cuda.set_per_process_memory_fraction(.02)
        release_workspace(torch)
        self.assertEqual(torch.cuda.memory_allocated(), 0)
        model = GPTNeoXForCausalLM(GPTNeoXConfig(vocab_size=67, hidden_size=32,
            intermediate_size=64, num_hidden_layers=2, num_attention_heads=4,
            max_position_embeddings=2048)).float().to('cuda').eval()
        handle = weakref.ref(model)
        values = token_losses(model, dict(eligible=True, prefix=[0]+[1]*63, target=[1]*32), torch)
        self.assertEqual(len(values), 32)
        del model
        gc.collect()
        self.assertIsNone(handle())
        release_workspace(torch)
        self.assertEqual(torch.cuda.memory_allocated(), 0)
        self.assertEqual(torch.cuda.memory_reserved(), 0)


if __name__ == '__main__': unittest.main()
