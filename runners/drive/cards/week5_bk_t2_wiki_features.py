"""Outcome-independent final-text feature bridge, with no human source handler.

The exact CoAuthor lexical function and pinned CPU encoder are reused. Only
article/sentence ordinals, final text, relative position and completion enter.
Lineage and outcome metadata cannot pass this boundary.
"""
import numpy as np
from .week5_bk_t2_features import lexical
from .week5_go_readers import embeddings
from .week5_bk_t2_wiki_text import final_sentences

FIELDS = {'article_ordinal', 'sentence', 'text', 'position', 'complete'}


def units(article_ordinal, final_wikitext):
    if type(article_ordinal) is not int or article_ordinal < 0:
        raise ValueError('Private article ordinal required')
    projected = final_sentences(final_wikitext)
    return [dict(article_ordinal=article_ordinal, sentence=r['index'], text=r['text'],
                 position=r['position'], complete=r['complete']) for r in projected['sentences']], projected['removed']


def validate(rows):
    if not 1 <= len(rows) <= 64:
        raise ValueError('Bounded complete sentence slice must contain 1 to 64 rows')
    keys = set()
    for row in rows:
        if set(row) != FIELDS:
            raise ValueError('Only final-text feature fields may cross this boundary')
        if (type(row['article_ordinal']) is not int or row['article_ordinal'] < 0
                or type(row['sentence']) is not int or row['sentence'] < 0
                or type(row['complete']) is not bool or not isinstance(row['text'], str)
                or not row['text'].strip() or not np.isfinite(row['position'])
                or not 0 <= row['position'] <= 1):
            raise ValueError('Invalid final-text feature unit')
        key = row['article_ordinal'], row['sentence']
        if key in keys:
            raise ValueError('Duplicate sentence feature key')
        keys.add(key)


def combine(rows, vocabulary, vectors):
    validate(rows)
    if (not isinstance(vocabulary, set) or len(vocabulary) != 150
            or any(not isinstance(word, str) for word in vocabulary)):
        raise ValueError('The same frozen 150-word CoAuthor skeleton is required')
    vectors = np.asarray(vectors, float)
    if (vectors.ndim != 2 or len(vectors) != len(rows) or vectors.shape[1] < 1
            or not np.isfinite(vectors).all()
            or not np.allclose(np.linalg.norm(vectors, axis=1), 1., atol=1e-5, rtol=0)):
        raise ValueError('Complete normalized encoder-vector bank required')
    result = []
    for row, vector in zip(rows, vectors):
        base, full = lexical(row['text'], row['position'], vocabulary)
        result.append(dict(article_ordinal=row['article_ordinal'], sentence=row['sentence'],
                           complete=row['complete'], baseline=base, features=full+vector.tolist()))
    return result


def encode(rows, vocabulary, encoder_manifest, on_vector=None):
    validate(rows)
    # The original routine retains every token by fixed 126-token chunks;
    # this wrapper introduces no sentence truncation or length exclusion.
    vectors = embeddings([r['text'] for r in rows], encoder_manifest, on_vector=on_vector)
    return combine(rows, vocabulary, vectors)
