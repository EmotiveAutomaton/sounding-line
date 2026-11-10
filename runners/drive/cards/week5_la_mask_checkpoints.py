"""Exact original LA masked forwards, checkpointed between eight-token batches.

This primitive never loads a model and does not admit a human reader. A paired
producer must supply the already pinned model, unique act directory and input
binding, catch MaskCheckpointYield, and retain native all-attempt accounting.
"""
from pathlib import Path
import math
import os
import time

from . import week5_la as original
from .week5_at_scoring import digest
from .timing_census import read, filehash
from .timing_p6 import write_equal, progress

ORIGINAL_SHA = '75072eeff47f0559edca1e63681b49feae58cb82502d6f8d4b457c9d52ecdca7'
PRECISION = 'float32_original'


class MaskCheckpointYield(RuntimeError):
    def __init__(self, phase, new_batches):
        super().__init__('Masked resolution yielded at a sealed eight-token boundary')
        self.receipt = dict(status='yielded', phase=phase, new_mask_batches=new_batches,
                            completed_mask_batches_are_immutable=True)


class ResolutionScorer(original.ResolutionScorer):
    """The original score/crop/reduction, with only _pll execution split."""

    def __init__(self, model, tokenizer, torch, output, binding, *, verifying=False,
                 max_new_batches=32, max_wall_seconds=600, yield_request_path=None):
        if filehash(original.__file__) != ORIGINAL_SHA:
            raise ValueError('Original masked numerical kernel changed')
        if set(binding) != {'source_row_sha256', 'masked_manifest_sha256'} or any(
                type(v) is not str or len(v) != 64 or any(c not in '0123456789abcdef' for c in v)
                for v in binding.values()):
            raise ValueError('Exact source-row and masked-manifest SHA-256 bindings required')
        if type(max_new_batches) is not int or max_new_batches < 1:
            raise ValueError('Positive integral masked-batch quantum required')
        if type(max_wall_seconds) not in (int, float) or not math.isfinite(max_wall_seconds) or not 0 < max_wall_seconds <= 1200:
            raise ValueError('Positive bounded masked wall quantum required')
        if model.training or torch.get_num_threads() != 2 or any(
                p.device.type != 'cpu' or p.dtype != torch.float32 for p in model.parameters()):
            raise ValueError('Original evaluated float32 CPU masked model and two numerical threads required')
        super().__init__(model, tokenizer, torch, max_tokens=512, mask_batch=8)
        self.output = Path(output)
        self.output.mkdir(parents=True, exist_ok=True)
        self.binding = dict(binding)
        self.verifying = verifying
        self.phase = 'verify' if verifying else 'execute'
        self.max_new_batches, self.max_wall_seconds = max_new_batches, float(max_wall_seconds)
        self.yield_request = Path(yield_request_path) if yield_request_path is not None else self.output / 'YIELD_REQUEST.json'
        self.new_batches = 0
        self.arm = 0
        self.entries = []
        self.began = time.monotonic()
        self.score_binding = None

    def _check(self):
        if (self.yield_request.exists() or self.new_batches >= self.max_new_batches or
                time.monotonic() - self.began >= self.max_wall_seconds):
            raise MaskCheckpointYield(self.phase, self.new_batches)

    def _read_batch(self, directory, offset, expected):
        path = directory / f'{offset:06d}.json'
        seal = directory / f'{offset:06d}.seal.json'
        if not path.exists() and not seal.exists():
            return None
        if not path.exists() or not seal.exists():
            raise ValueError('Incomplete masked checkpoint seal; retain interrupted evidence')
        if read(seal) != dict(sha256=filehash(path), binding=expected):
            raise ValueError('Masked checkpoint byte or input binding changed')
        value = read(path)
        if set(value) != {'binding', 'values'} or value['binding'] != expected:
            raise ValueError('Masked checkpoint schema or semantic identity changed')
        if len(value['values']) != expected['count'] or any(type(v) not in (int, float) or not math.isfinite(v) for v in value['values']):
            raise ValueError('Invalid retained masked numerical support')
        return value['values']

    def _pll(self, ids, positions):
        arm = ('before', 'after')[self.arm]
        self.arm += 1
        values = []
        directory = self.output / self.phase / arm
        existing = sorted(directory.glob('*.seal.json')) if directory.exists() else []
        if directory.exists():
            data_files = {p.name for p in directory.glob('*.json') if not p.name.endswith('.seal.json')}
            if data_files != {p.name.replace('.seal.json', '.json') for p in existing}:
                raise ValueError('Masked checkpoint has an unsealed or unexpected value file')
        if [p.name for p in existing] != [f'{i * 8:06d}.seal.json' for i in range(len(existing))]:
            raise ValueError('Masked checkpoint prefix is not contiguous')
        if len(existing) > (len(positions) + 7) // 8:
            raise ValueError('Masked checkpoint contains undeclared token positions')
        for offset in range(0, len(positions), 8):
            self._check()
            selected = positions[offset:offset + 8]
            expected = dict(score_binding=self.score_binding, phase=self.phase, arm=arm,
                            offset=offset, count=len(selected), token_batch_sha256=digest(dict(ids=ids, positions=selected)),
                            mask_batch=8, precision=PRECISION)
            retained = self._read_batch(directory, offset, expected)
            if retained is None:
                # Calling the frozen original helper on exactly one original
                # eight-position slice performs the identical tensor batch,
                # forward, float32 conversion and cross-entropy operation.
                fresh = original.ResolutionScorer._pll(self, ids, selected)
                if self.verifying:
                    production_expected = dict(expected, phase='execute')
                    prior = self._read_batch(self.output / 'execute' / arm, offset, production_expected)
                    if prior is None or any(abs(a - b) > 1e-5 for a, b in zip(prior, fresh)):
                        raise ValueError('Original masked fresh-forward tolerance failed')
                path = directory / f'{offset:06d}.json'
                write_equal(path, dict(binding=expected, values=fresh))
                write_equal(directory / f'{offset:06d}.seal.json', dict(sha256=filehash(path), binding=expected))
                retained = fresh
                self.new_batches += 1
            elif self.verifying:
                prior = self._read_batch(self.output / 'execute' / arm, offset, dict(expected, phase='execute'))
                if prior is None or any(abs(a - b) > 1e-5 for a, b in zip(prior, retained)):
                    raise ValueError('Retained independent masked replay no longer matches production')
            values.extend(retained)
            path = directory / f'{offset:06d}.json'
            self.entries.append(dict(arm=arm, offset=offset, file=path.relative_to(self.output).as_posix(), sha256=filehash(path)))
            progress(self.output / 'PROGRESS.json', dict(phase=self.phase, arm=arm, old_tokens_completed=offset + len(selected),
                                                       arm_tokens=len(positions), new_mask_batches=self.new_batches))
            self._check()
        if not values or any(not math.isfinite(x) for x in values):
            raise ValueError('Unsupported masked target')
        return values

    def score(self, previous, current):
        cpu, wall, stamp = time.process_time(), time.monotonic(), time.time_ns()
        error, status = None, None
        try:
            self.score_binding = dict(source=self.binding, text_sha256=digest(dict(previous=previous, current=current)),
                                      original_kernel_sha256=ORIGINAL_SHA, implementation_sha256=filehash(__file__),
                                      precision=PRECISION, max_tokens=512, mask_batch=8)
            write_equal(self.output / 'ACT_BINDING.json', self.score_binding)
            if self.verifying and not (self.output / 'RESULT.json').is_file():
                raise ValueError('Incomplete masked act cannot enter independent verification')
            self._check()
            self.arm, self.entries = 0, []
            result = original.ResolutionScorer.score(self, previous, current)
            if self.arm != 2:
                raise ValueError('Both original masked arms are required')
            if self.verifying:
                prior = read(self.output / 'RESULT.json')
                if any(result[k] != prior[k] for k in ('old_tokens', 'old_tokens_dropped', 'current_tokens')) or any(
                        len(result[k]) != len(prior[k]) or any(abs(a - b) > 1e-5 for a, b in zip(result[k], prior[k]))
                        for k in ('before_logprobs', 'after_logprobs')):
                    raise ValueError('Full original masked numerical/support check failed')
                write_equal(self.output / 'VERIFY_INDEX.json', self.entries)
            else:
                write_equal(self.output / 'RESULT.json', result)
                write_equal(self.output / 'INDEX.json', self.entries)
            status = 'verified' if self.verifying else 'complete'
            return result
        except MaskCheckpointYield:
            status = 'yielded'
            raise
        except BaseException as exc:
            error = type(exc).__name__
            raise
        finally:
            write_equal(self.output / 'invocation_costs' / f'{os.getpid()}-{stamp}.json',
                        dict(phase=self.phase, status=status, error_class=error, new_mask_batches=self.new_batches,
                             process_cpu_seconds=time.process_time() - cpu, wall_seconds=time.monotonic() - wall,
                             native_all_attempt_accounting_authoritative=True))
