"""Standard-library text features and frozen multinomial baseline prediction.

DESIGN CHECK: only explicit artifact/pair fields enter features; no IDs or labels.
NULL: same text under swapped private metadata has identical features/probabilities.
ALTERNATIVE: a trained lexical association changes held-out predictions.
"""
from collections import Counter
import math
import re
from difflib import SequenceMatcher


def words(text):
    return re.findall(r"\w+(?:['’-]\w+)?", text.casefold())


def features(evidence):
    if set(evidence) == {'text', 'context'}:
        tokens = words(evidence['text'])
        out = Counter('w:' + w for w in tokens)
        out.update('b:' + a + ' ' + b for a, b in zip(tokens, tokens[1:]))
        return out
    if set(evidence) == {'before', 'after', 'context'}:
        before, after = Counter(words(evidence['before'])), Counter(words(evidence['after']))
        out = Counter({'after:' + k: v for k, v in after.items()})
        out.update({'added:' + k: v for k, v in (after - before).items()})
        out.update({'deleted:' + k: v for k, v in (before - after).items()})
        return out
    raise ValueError('unregistered visible text schema')


def predict(evidence, parameters):
    classes, prior = parameters['classes'], parameters['log_prior']
    if set(classes) != set(prior) or not classes:
        raise ValueError('invalid baseline class support')
    x = features(evidence)
    score = {}
    for category in classes:
        terms = parameters['log_likelihood'][category]
        value = prior[category] + math.fsum(count * terms[word] for word, count in x.items() if word in terms)
        if not math.isfinite(value):
            raise ValueError('invalid baseline likelihood')
        score[category] = value
    maximum = max(score.values())
    unnorm = {k: math.exp(v - maximum) for k, v in score.items()}
    total = math.fsum(unnorm.values())
    # Frozen contamination component bounds overconfidence on out-of-vocabulary text.
    epsilon = parameters['uniform_mixture']
    if not 0 <= epsilon <= 1:
        raise ValueError('invalid smoothing mass')
    return {k: (1 - epsilon) * v / total + epsilon / len(classes) for k, v in unnorm.items()}


def copy_probabilities(current_text, options):
    """Fixed copied-text rival: normalized character similarity, no fitted labels."""
    if not isinstance(current_text, str) or not options or any(not isinstance(k, str) or not isinstance(v, str) for k, v in options.items()):
        raise ValueError('invalid copied-text inputs')
    if len(current_text) > 4096 or any(len(v) > 4096 for v in options.values()) or len(options) > 128:
        raise ValueError('copied-text operation outside frozen envelope')
    source = ' '.join(current_text.casefold().split())
    logits = {k: 8 * SequenceMatcher(None, source, ' '.join(v.casefold().split()), autojunk=False).ratio() for k, v in options.items()}
    maximum = max(logits.values())
    weights = {k: math.exp(v - maximum) for k, v in logits.items()}
    total = math.fsum(weights.values())
    return {k: .99 * v / total + .01 / len(options) for k, v in weights.items()}
