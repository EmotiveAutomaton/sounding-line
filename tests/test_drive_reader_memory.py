"""Known-answer and numerical controls for the actual no-cache scorer."""
import math
import unittest
import torch
from transformers import GPTNeoXConfig, GPTNeoXForCausalLM
from runners.drive.readers_low_memory import token_losses, score_menu
from runners.drive.reader_precision import discrepancy
from runners.drive.reader_pilot_v5 import compare_scores


class MemoryScorerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)
        torch.manual_seed(140017)
        cls.model = GPTNeoXForCausalLM(GPTNeoXConfig(vocab_size=67, hidden_size=32,
            intermediate_size=64, num_hidden_layers=2, num_attention_heads=4,
            max_position_embeddings=2048, hidden_dropout=0., attention_dropout=0.)).float().eval()

    def test_full_direct_matches_chunks_and_causal_positions(self):
        for prefix, target in [([0], [1]), ([0, 2, 3], [5, 4, 2, 1, 6]),
                               ([i % 67 for i in range(2000)], [i % 67 for i in range(48)])]:
            x = dict(eligible=True, prefix=prefix, target=target)
            with torch.inference_mode():
                logits = self.model(torch.tensor([prefix + target[:-1]]), use_cache=False).logits[0, len(prefix)-1:]
                expected = torch.nn.functional.cross_entropy(logits, torch.tensor(target), reduction='none').tolist()
            for block in (1, 7, 32):
                actual = token_losses(self.model, x, torch, block_tokens=block)
                self.assertLess(discrepancy(expected, actual), 1e-5)

    def test_uniform_known_answer(self):
        model = GPTNeoXForCausalLM(self.model.config).float().eval()
        with torch.no_grad():
            for p in model.parameters(): p.zero_()
        got = token_losses(model, dict(eligible=True, prefix=[0, 2], target=[1, 3, 4]), torch)
        for value in got: self.assertAlmostEqual(value, math.log(67), places=5)

    def test_nonfinite_and_runtime_refuse(self):
        with self.assertRaises(ValueError):
            token_losses(self.model, {'eligible': False}, torch)
        with self.assertRaises(ValueError):
            score_menu(self.model, None, '', [], torch)
        model = GPTNeoXForCausalLM(self.model.config).float().eval()
        with torch.no_grad(): model.get_output_embeddings().weight.fill_(float('nan'))
        with self.assertRaises(ValueError):
            token_losses(model, dict(eligible=True, prefix=[0], target=[1]), torch)

    def test_retained_gate_rejects_shifted_tokens_or_missing_options(self):
        import copy
        old = dict(eligible=True, native_token_ids=[1, 2], codepoint_offsets=[[0, 1], [1, 2]],
                   prefix_tokens=1, target_tokens=2, utf8_bytes=2, native_token_nll=[1., 2.])
        self.assertEqual(compare_scores([old], [copy.deepcopy(old)], .02), [0.])
        for key, value in [('native_token_ids', [2, 1]), ('native_token_nll', [1., 2.03]),
                           ('native_token_nll', [1.]), ('native_token_nll', [1., float('nan')])]:
            bad = copy.deepcopy(old); bad[key] = value
            with self.assertRaises(ValueError): compare_scores([old], [bad], .02)
        with self.assertRaises(ValueError): compare_scores([old], [], .02)


if __name__ == '__main__': unittest.main()
