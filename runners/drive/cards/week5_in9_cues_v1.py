"""Frozen literal IN9 cue counter, separate from the qualified items table.

R6: these are words, not classifier labels or measurements of a feeling.
Semantic instrument review and prevalence gates precede any cue odds claim.
"""
import re

LEXICONS = {
    'VICTIM': ('hurt', 'upset her', 'upset him', 'let down', 'lied to', 'broke', 'forgot'),
    'AUDIENCE': ('in front of', 'everyone', 'people saw', 'caught', 'embarrassed'),
    'ANGRY_AT_ME': ('angry at me', 'mad at me', 'yelled at me', 'furious with me'),
    'LAUGHED_AT': ('laughed at me', 'made fun of me', 'mocked', 'looked down on', 'sneered'),
}


def count(text):
    # Exact case-folded token sequences; no stemming or inferred synonyms.
    tokens = re.findall(r"\w+(?:'\w+)?", str(text).casefold().replace('\u2019', "'"))
    result = {}
    for name, phrases in LEXICONS.items():
        total = 0
        for phrase in phrases:
            wanted = phrase.split()
            total += sum(tokens[i:i+len(wanted)] == wanted for i in range(len(tokens)-len(wanted)+1))
        result[name] = int(total)
    return result


def independent_count(text):
    normalized = ' '.join(re.findall(r"\w+(?:'\w+)?", str(text).casefold().replace('\u2019', "'")))
    return {name: sum(len(list(re.finditer(r'(?<!\w)'+re.escape(phrase)+r'(?!\w)', normalized)))
                      for phrase in phrases) for name, phrases in LEXICONS.items()}


def admission(prevalence, reviewed_hits, correct_hits):
    if prevalence < .05:
        return 'unsupported: under5% of the two prompts'
    if reviewed_hits != 100 or not 0 <= correct_hits <= reviewed_hits:
        return 'held: missing frozen100-hit semantic audit'
    return 'qualified literal cue' if correct_hits >= 80 else 'instrument failed'
