"""The unscored next answered prompt after each rating of solitary boredom.

DESIGN CHECK: LESSONS 2–5. Count adjacent answered prompts before examining
boredom. Row order, missing outcomes and midnight cannot invent a successor.
Output consists only of pooled counts over the six named rating levels.
"""
from collections import Counter, defaultdict

from .es_clock_v1 import utc_seconds
from .es_source_v1 import rating


def _coded(value, missing):
    if value is None or value in missing:
        return None
    number = float(value)
    if not number.is_integer() or number < 1:
        raise ValueError("Undocumented categorical response")
    return int(number)


def describe(rows, missing_tokens, guard):
    by_person = defaultdict(list)
    unplaced_people = set()
    coverage = Counter()
    for row in rows:
        guard()
        coverage["source_rows"] += 1
        who, created, ended = row["id"], row["created_esm"], row["ended_esm"]
        if who in missing_tokens:
            coverage["missing_identity"] += 1
            continue
        if ended in missing_tokens:
            coverage["without_answered_clock"] += 1
            unplaced_people.add(who)
            continue
        if created in missing_tokens:
            unplaced_people.add(who)
            coverage["answered_missing_created_clock"] += 1
            continue
        created_at = utc_seconds(created)
        day = int(created_at // 86400)
        answer = utc_seconds(ended)
        if answer < created_at:
            unplaced_people.add(who)
            coverage["inverted_clock"] += 1
        by_person[who].append((answer, day, row))
    counts = {str(i): Counter() for i in range(1, 7)}
    modes = {str(i): Counter() for i in range(1, 7)}
    types = {str(i): Counter() for i in range(1, 7)}
    for who, prompts in by_person.items():
        guard()
        ordered = sorted(prompts, key=lambda x: x[0])
        if who in unplaced_people or len({item[0] for item in ordered}) != len(ordered):
            coverage["ambiguous_day_prompts"] += len(ordered)
            continue
        for j, (_, day, current) in enumerate(ordered):
            context = _coded(current["interaction"], missing_tokens)
            if context not in (None, 1, 2):
                raise ValueError("Unknown interaction code")
            if context != 2:
                continue
            if current["occup_bored"] in missing_tokens:
                coverage["solitary_missing_boredom"] += 1
                continue
            score = rating(current["occup_bored"], 6, missing_tokens)
            if not float(score).is_integer():
                raise ValueError("Boredom item requires a documented category")
            level = str(int(score))
            counts[level]["anchors"] += 1
            if j + 1 == len(ordered) or ordered[j + 1][1] != day:
                counts[level]["last_answered_prompt_of_day"] += 1
                continue
            successor = ordered[j + 1][2]
            next_context = _coded(successor["interaction"], missing_tokens)
            if next_context is None:
                counts[level]["next_context_missing"] += 1
            elif next_context == 2:
                counts[level]["next_solitary"] += 1
            elif next_context == 1:
                counts[level]["next_interaction"] += 1
                mode = _coded(successor["communication"], missing_tokens)
                kind = _coded(successor.get("type_interaction"), missing_tokens)
                if mode not in (None, 1, 2) or kind not in (None, 1, 2, 3):
                    raise ValueError("Undocumented interaction mode or activity type")
                modes[level]["missing" if mode is None else str(mode)] += 1
                types[level]["missing" if kind is None else str(kind)] += 1
            else:
                raise ValueError("Unknown successor interaction code")
    return dict(coverage=dict(coverage), by_boredom={k: dict(v) for k, v in counts.items()},
                next_interaction_type_codes={k: dict(v) for k, v in types.items()},
                interaction_type_labels={"1":"job-related task/chore", "2":"private task/chore", "3":"leisure activity"},
                next_interaction_communication_codes={k: dict(v) for k, v in modes.items()},
                communication_labels={"1":"directly/in person", "2":"via phone/chat"},
                method="adjacent answered end times within the same UTC created date",
                inferential_status="descriptive")
