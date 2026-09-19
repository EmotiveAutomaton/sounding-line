# Copyright 2026 Anthropic PBC
# SPDX-License-Identifier: Apache-2.0
"""Jacobian lens: fit and apply the average input-output Jacobian as a readout
of decoder-transformer residuals."""

# Local Stage 11.2 subset: optional logging helper omitted.
from jlens.fitting import fit, jacobian_for_prompt
from jlens.hf import HFLensModel, Layout, from_hf
from jlens.hooks import ActivationRecorder
from jlens.lens import JacobianLens
from jlens.protocol import LensModel

__all__ = [
    "ActivationRecorder",
    "HFLensModel",
    "JacobianLens",
    "Layout",
    "LensModel",
    "fit",
    "from_hf",
    "jacobian_for_prompt",
]
