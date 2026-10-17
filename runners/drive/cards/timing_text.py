"""Private replay ledger of completed writer-produced words and punctuation.

Retains later-deleted occurrences rather than selecting only final surviving
text. A delta's characters share one observed timestamp; no keypress is invented.
"""
from __future__ import annotations

import math
import re
from collections import defaultdict

from runners.stage9.coauthor import delta_ops, units, text_of

TOKEN = re.compile(r"[^\W_]+(?:['’][^\W_]+)*|[^\w\s]", re.UNICODE)
WORD = re.compile(r"[^\W_]+(?:['’][^\W_]+)*\Z", re.UNICODE)


def tokens(text):
    return [m.group().casefold() for m in TOKEN.finditer(text)]


def replay_words(events):
    if not events or events[0]["eventName"] != "system-initialize":
        raise ValueError("initialization required")
    doc = units(events[0]["currentDoc"])
    owners = [-1] * len(doc)
    characters, records, observed, pending = [], [], {}, {}
    membership = defaultdict(set)
    previous_delta = None
    previous_time = -math.inf
    last_ordinal = 0

    def save(ids, record, ordinal):
        if ids in observed:
            return
        record["index"] = len(records)
        observed[ids] = record["index"]
        record["completed_ordinal"] = ordinal
        records.append(record)
        pending.pop(ids, None)
        for identity in ids:
            membership[identity].add(record["index"])

    def mark_revised(ids):
        for identity in set(ids):
            for index in membership.get(identity, ()):
                records[index]["revised"] = True

    def collect(left, right, ordinal, final=False):
        # Expand only the affected whitespace-delimited region. UTF-16 whitespace
        # code units have the same values as Unicode whitespace codepoints.
        while left > 0 and not chr(doc[left - 1]).isspace():
            left -= 1
        while right < len(doc) and not chr(doc[right]).isspace():
            right += 1
        # Include the word immediately before an inserted separator.
        if left > 0 and left == right:
            left -= 1
            while left > 0 and not chr(doc[left - 1]).isspace():
                left -= 1
        if not doc[left:right]:
            return
        fragment = text_of(doc[left:right])
        offsets = [0]
        for char in fragment:
            offsets.append(offsets[-1] + len(units(char)))
        for match in TOKEN.finditer(fragment):
            a, b = left + offsets[match.start()], left + offsets[match.end()]
            # A trailing word is still being composed until a delimiter or end
            # of session. Punctuation is immediately a completed token.
            word = bool(WORD.fullmatch(match.group()))
            if word and b < len(doc) and (chr(doc[b]).isalnum() or chr(doc[b]) in "'’_"):
                continue
            ids = tuple(dict.fromkeys(owners[a:b]))
            if not ids or -1 in ids or ids in observed:
                continue
            before = text_of(doc[:a])
            context = tokens(before)[-2:]
            prior = list(TOKEN.finditer(before))
            previous_index = None
            if prior:
                p = prior[-1]
                pa, pb = len(units(before[:p.start()])), len(units(before[:p.end()]))
                previous_index = observed.get(tuple(dict.fromkeys(owners[pa:pb])))
            meta = [characters[c] for c in ids]
            first, last = meta[0], meta[-1]
            intervals = [meta[j]["seconds"] - meta[j - 1]["seconds"] for j in range(1, len(meta))
                         if meta[j]["ordinal"] != meta[j - 1]["ordinal"]]
            record = dict(index=len(records), token=match.group().casefold(), is_word=word,
                          ordinal=first["ordinal"], completed_ordinal=ordinal,
                          seconds=first["seconds"], pause_seconds=first["pause_seconds"],
                          first_delta_characters=first["delta_characters"],
                          length=len(match.group()), context=context,
                          previous_typed_token_index=previous_index,
                          sentence_start=not before.strip() or bool(re.search(r"[.!?]\s*$", before)),
                          after_punctuation=bool(re.search(r"[^\w\s]\s*$", before)),
                          within_intervals=intervals, duration_seconds=last["seconds"] - first["seconds"],
                          all_single_character_deltas=all(m["delta_characters"] == 1 for m in meta),
                          revised=False)
            right_owner = owners[b] if b < len(owners) else -1
            new_delimiter = right_owner >= 0 and characters[right_owner]["ordinal"] >= max(m["ordinal"] for m in meta)
            if word and not final and not new_delimiter:
                pending[ids] = record
            else:
                save(ids, record, ordinal)

    for ordinal, event in enumerate(events):
        timestamp = float(event["eventTimestamp"]) / 1000
        if not math.isfinite(timestamp) or timestamp < previous_time:
            raise ValueError("invalid source chronology")
        previous_time = timestamp
        last_ordinal = ordinal
        ops = delta_ops(event.get("textDelta"))
        if not ops:
            continue
        # A cursor move away completes a pending word. Adjacent insertion or
        # deletion keeps it in composition until the new local word is parsed.
        touched, cursor = set(), 0
        for op in ops:
            if "insert" in op:
                touched.update(owners[max(0, cursor - 1):cursor + 1])
            elif "delete" in op:
                touched.update(owners[cursor:cursor + op["delete"]])
                cursor += op["delete"]
            else:
                cursor += op["retain"]
        for ids, record in list(pending.items()):
            if touched.isdisjoint(ids):
                save(ids, record, ordinal)
            else:
                del pending[ids]
        pause = timestamp - previous_delta if previous_delta is not None else None
        source_user = event.get("eventSource") == "user"
        size = sum(len(op["insert"]) for op in ops if "insert" in op)
        out, provenance, position, affected = [], [], 0, []
        for op in ops:
            if "insert" in op:
                if source_user and 0 < position < len(doc):
                    common = membership.get(owners[position - 1], set()) & membership.get(owners[position], set())
                    for index in common:
                        records[index]["revised"] = True
                start = len(out)
                for char in op["insert"]:
                    values = units(char)
                    identity = -1
                    if source_user:
                        identity = len(characters)
                        characters.append(dict(ordinal=ordinal, seconds=timestamp,
                                               pause_seconds=pause, delta_characters=size))
                    out.extend(values)
                    provenance.extend([identity] * len(values))
                affected.append((max(0, start - 1), len(out)))
            else:
                key = "retain" if "retain" in op else "delete"
                count = op[key]
                if type(count) is not int or count < 0 or position + count > len(doc):
                    raise ValueError("invalid UTF-16 delta boundary")
                if key == "retain":
                    out.extend(doc[position:position + count])
                    provenance.extend(owners[position:position + count])
                else:
                    mark_revised(owners[position:position + count])
                    affected.append((max(0, len(out) - 1), len(out)))
                position += count
        out.extend(doc[position:])
        provenance.extend(owners[position:])
        doc, owners = out, provenance
        text_of(doc)  # Refuse a split surrogate instead of corrupting positions.
        previous_delta = timestamp
        for left, right in affected:
            collect(min(left, len(doc)), min(right, len(doc)), ordinal)
    collect(0, len(doc), last_ordinal, final=True)
    return dict(words=records, final_document=text_of(doc),
                timing_unit="logged delta interval, not individual keypress")
