"""Actual pinned CPU encoder import/load/encode/replay before CA1 recovery.

Constructed strings only. No scientific scores, corpus text, model download or
dependency installation. Unlike the mathematical feature fixture, this gate
deliberately imports the actual inference package and loads the local model.
"""
import importlib.metadata
import os
from pathlib import Path
import sys

import numpy as np

from runners.stage14.common import freeze, filehash, read, digest
from . import week3_alignment_features as features

TEXTS = ('A person chooses an answer.', 'A person chooses an answer.',
         'Una persona elige una respuesta.', 'Une personne choisit une réponse.',
         'Eine Person wählt eine Antwort.', '一个人选择一个回答。',
         'شخص يختار إجابة.', 'Una frase construida; no son datos de participantes.')
PACKAGES = ('sentence-transformers','transformers','torch','huggingface-hub','tokenizers',
            'numpy','scikit-learn','scipy','typing-extensions','tqdm')


def environment():
    versions = {name:importlib.metadata.version(name) for name in PACKAGES}
    if versions['sentence-transformers'] != '6.2.0': raise ValueError('owner-reviewed inference dependency pin required')
    return dict(python=sys.version,packages=versions)


def validate(values):
    if values.shape != (len(TEXTS),384) or values.dtype != np.float32 or not np.isfinite(values).all():
        raise ValueError('actual encoder shape/type/finiteness failed')
    if not np.allclose(np.linalg.norm(values,axis=1),1,rtol=0,atol=1e-6): raise ValueError('normalized encoder output required')
    if not np.array_equal(values[0],values[1]): raise ValueError('identical texts differ within fixed batch')
    if all(np.array_equal(values[0],r) for r in values[2:]): raise ValueError('degenerate constant encoder output')


def calculate(inputs,config):
    if set(inputs) != {'model_summary','model_complete'} or config != {}: raise ValueError('exact actual model inputs required')
    versions = environment()
    os.environ['HF_HUB_OFFLINE']='1'; os.environ['TRANSFORMERS_OFFLINE']='1'
    os.environ['TOKENIZERS_PARALLELISM']='false'
    encode=features.encoder(inputs,{})
    values=encode(list(TEXTS)); repeat=encode(list(TEXTS));validate(values);validate(repeat)
    if not np.array_equal(values,repeat): raise ValueError('actual model repeat differs')
    return values,dict(card='CA1-actual-encoder-smoke',state='actual_cpu_inference_verified',
        input_hashes={k:filehash(v) for k,v in inputs.items()},environment=versions,
        texts_sha256=digest(TEXTS),constructed_strings=len(TEXTS),shape=list(values.shape),
        backend='CPU; same frozen encoder path as corpus features; local files only',
        feature_module_sha256=filehash(features.__file__),scientific_admission=False)


def execute(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);values,report=calculate(inputs,config)
    path=output/'VECTORS.npy'
    if path.exists():
        if not np.array_equal(np.load(path,allow_pickle=False),values): raise ValueError('immutable smoke vectors changed')
    else: np.save(path,values,allow_pickle=False)
    report['vectors_sha256']=filehash(path);freeze(output/'SUMMARY.json',report);return report


def verify(output,inputs,config):
    output=Path(output);values,report=calculate(inputs,config)
    if not np.array_equal(np.load(output/'VECTORS.npy',allow_pickle=False),values): raise ValueError('fresh real encoder replay differs')
    report['vectors_sha256']=filehash(output/'VECTORS.npy')
    if read(output/'SUMMARY.json') != report: raise ValueError('fresh encoder environment or result differs')
    return dict(verified=True,actual_model_fresh_cpu_encoding=True)
