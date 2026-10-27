"""CA5.r.h1: text-only topics retaining unrepresented texts as uniform weights.

DESIGN CHECK: LESSONS 3-5 / CONTROLS 1-7. Empty vocabulary/component support
is explicit and uniform, never population deletion or a fabricated topic. All
represented-text fits, seeds and convergence gates retain the original design.
"""
from pathlib import Path
import warnings
import numpy as np
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.exceptions import ConvergenceWarning
from .week3_jester_preference import SEED,K
from .timing_census import read,filehash
from .timing_p6 import write_equal


def text_features(records):
    if (len(records)!=150 or sorted(r['joke_id'] for r in records)!=list(range(1,151))
            or any(not isinstance(r['text'],str) or not r['text'].strip() for r in records)):
        raise ValueError('all unique nonempty joke texts required')
    records=sorted(records,key=lambda r:r['joke_id'])
    vectorizer=TfidfVectorizer(lowercase=True,stop_words='english',ngram_range=(1,2),
        min_df=2,max_df=.95,sublinear_tf=True,norm='l2')
    x=vectorizer.fit_transform([r['text'] for r in records])
    if x.shape[1]<K:raise ValueError('text representation unsupported')
    empty=np.asarray(x.sum(axis=1)).ravel()==0
    model=NMF(n_components=K,init='nndsvda',solver='cd',beta_loss='frobenius',
        max_iter=2000,tol=1e-5,random_state=SEED)
    with warnings.catch_warnings():
        warnings.simplefilter('error',ConvergenceWarning)
        w=model.fit_transform(x)
    if not np.isfinite(w).all():raise ValueError('nonfinite topic representation')
    mass=w.sum(1,keepdims=True)
    normalized=np.divide(w,mass,out=np.zeros_like(w),where=mass>0)
    soft=np.exp(4*(normalized-normalized.max(1,keepdims=True)))
    soft/=soft.sum(1,keepdims=True)
    vocab=vectorizer.get_feature_names_out().tolist()
    return dict(joke_ids=list(range(1,151)),weights=soft.tolist(),vocabulary=vocab,
        idf=vectorizer.idf_.tolist(),components=model.components_.tolist(),
        iterations=int(model.n_iter_),top_terms=[[vocab[j] for j in np.argsort(-row,kind='stable')[:12]] for row in model.components_],
        seed=SEED,features_from_text_only=True,scope='Eight lexical topic proxies; not validated psychological categories.',
        empty_vocabulary_items=(np.flatnonzero(empty)+1).tolist(),
        zero_component_items=(np.flatnonzero(mass.ravel()==0)+1).tolist(),
        support_policy='Zero normalized component vector becomes uniform topic weights; no record omitted.')


def build(inputs,config):
    if set(inputs)!={'jester_texts'} or set(config)!={'source_sha256'}:raise ValueError('text-only inputs required')
    if filehash(inputs['jester_texts'])!=config['source_sha256']:raise ValueError('text source changed')
    return dict(source_sha256=config['source_sha256'],**text_features(read(inputs['jester_texts'])))


def execute(output,inputs,config):
    write_equal(Path(output)/'TOPICS.json',build(inputs,config))
    return dict(texts=150,topics=8,scientific_admission=False,ratings_read=False)


def verify(output,inputs,config):
    if build(inputs,config)!=read(Path(output)/'TOPICS.json'):raise ValueError('fresh complete feature replay differs')
    return dict(verified=True,complete_feature_replay=True,scientific_admission=False,ratings_read=False)
