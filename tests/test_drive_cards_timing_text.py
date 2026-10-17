from runners.drive.cards.timing_text import replay_words


def event(i, ops=None, source="user", doc=None):
    out = dict(eventName="text-insert" if i else "system-initialize", eventTimestamp=i * 100,
               eventSource=source)
    if doc is not None:
        out["currentDoc"] = doc
    if ops is not None:
        out["textDelta"] = {"ops": ops}
    return out


def test_deleted_words_survive_with_revision_and_nonuser_excluded():
    rows = [event(0, doc=""), event(1, [{"insert": "cat "}]),
            event(2, [{"delete": 3}, {"insert": "dog"}]),
            event(3, [{"retain": 4}, {"insert": "model "}], "api")]
    result = replay_words(rows)
    assert result["final_document"] == "dog model "
    words = {w["token"]: w for w in result["words"]}
    assert set(words) == {"cat", "dog"}
    assert words["cat"]["revised"]
    assert not words["dog"]["revised"]
    assert words["cat"]["first_delta_characters"] == 4


def test_single_character_composition_no_partial_word_invention():
    rows = [event(0, doc="\n")]
    for i, char in enumerate("cat dog ", 1):
        rows.append(event(i, [{"retain": i - 1}, {"insert": char}]))
    words = replay_words(rows)["words"]
    assert [w["token"] for w in words] == ["cat", "dog"]
    assert words[1]["context"] == ["cat"]
    assert words[1]["previous_typed_token_index"] == 0
    assert words[1]["all_single_character_deltas"]
    assert abs(words[1]["pause_seconds"] - .1) < 1e-12


def test_unicode_utf16_and_inside_word_rewrite():
    rows = [event(0, doc=""), event(1, [{"insert": "😀 cat "}]),
            event(2, [{"retain": 4}, {"insert": "h"}])]
    words = replay_words(rows)["words"]
    cat = next(w for w in words if w["token"] == "cat")
    assert cat["revised"]
    assert any(w["token"] == "chat" for w in words)
