"""The lock register. Every hash-locked artifact in the project, and its recorded hash.

This is the file that makes the pre-registration checkable by someone who does not trust the
author — which is the only kind of pre-registration worth having. `pytest tests/test_locks.py`
verifies all of it and is intended to run in CI on every commit.

**Adding a hash here is not how a locked file gets changed.** See docs/DEVIATIONS.md: record the
deviation first, retain the original, keep computing it, and report it as failing if it fails.
"""

from __future__ import annotations

from pathlib import Path

from .hashlock import verify

REPO_ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------------------------
# Locked at Gate 0, 2026-08-02, before any probe code existed.
LOCKS: dict[str, str] = {
    # The spec. Written before code and never edited afterwards; amendments live in
    # docs/gate0/LITERATURE.md §8 rather than in the spec itself. This hash is the reason that
    # sentence is verifiable rather than merely asserted.
    "SOUNDING_LINE_SPEC.md":
        "09e41edff4e765b6ca13233333c4f936f2e24c6ee955f62ca2e592aabe223b41",

    # The Gate 0 literature review. Locked because it is the gate's verdict — including the
    # record in §9 of what WOULD have failed the gate, which is worthless if editable after
    # the fact.
    "docs/gate0/LITERATURE.md":
        "b7d2c6e9f12bb78c85aa04424b3396c20fd70a85006be792a52f2901f40fc583",

    # The bounded hypothesis family. Changing this changes the instrument: a reading produced
    # under one family hash is not comparable to a reading produced under another.
    "soundingline/family/family_v1.yaml":
        "6884b59c72fa92e5923f6c01e8ff194d341d0633dfc7a5d9a84db8dd9bb94db8",

    # The Gate 1 pre-registration.
    "prereg/gate1.py":
        "c1af65d0886b83cb4fc4e05d913d112c2a603d806f983c3db2356f7b753936f0",

    # The Gate 3 pre-registration and its corpus. Gate 3 is a CLAIM gate, so both the criteria
    # AND the artifact list are locked before the instrument reads any of it — a corpus that can
    # be edited after a result is not a corpus.
    "prereg/gate3.py":
        "57fc1b7eda862f620722b06a93ea4c50a158f943489e44f08d99014a0288b203",
    "corpora/manifests/gate3.json":
        "d50f2e946840e10eb233d3c71d9a9195767fe61dd3a137f5e907416689980371",

    # The Gate 2 pre-registration. F2 is a CLAIM falsifier — the first point where a failure is
    # allowed to stop the project — so it is locked before the corpus was read, and its stop
    # condition is written into the card rather than decided afterwards.
    "prereg/gate2.py":
        "d72ca0db4af17d84f2e4fbf44fd9d66bfeeda22f3de52849d4322476340a8981",

    # The prompts. In an LLM-based instrument the prompt IS the measurement apparatus — the
    # simulation had no analogue of this, and Gate 0 named prompt drift as the most likely
    # place undocumented change enters the project. Locked before the first Gate 1 run.
    "soundingline/probe/prompts/bounded_v1.yaml":
        "08a0ddbbecd9c750e98504b930d851f801092e28f996b9026db478aadc9a531a",

    # The free-form baseline arm. Locked for a second reason beyond drift: this arm decides
    # whether the project is a contribution (A-2), and it is trivially easy to weaken it after
    # seeing a result that went the wrong way. The lock is what makes "we did not sandbag the
    # baseline" checkable rather than asserted.
    # v2 adds the two effort dimensions and the 100-point convention so the baseline is coerced
    # into exactly the form the bounded arm is. Locked for the same reason v1 was: this arm
    # decides whether the project is a contribution, and it is trivially easy to weaken after
    # seeing a result go the wrong way.
    "soundingline/probe/prompts/freeform_v2.yaml":
        "4d7dcac95828aa6d02f69dd3ece06a7e952e44faf93b6df14d68c7c78ff10a9f",
    "soundingline/probe/prompts/freeform_v1.yaml":
        "bf9aaa7d7a6f593058a150a3464434b554ae080629499a8f5c0b8938249d2c46",
    # ── family v2 and its prompt. v1 entries above are unchanged and stay locked, so readings
    # taken under v1 remain comparable to each other. Two families coexist on purpose.
    # family v3 adds `performed_affect` — the first non-instrumental dimension, and the answer
    # C-23 has been owed since it was raised. Locked on creation, NOT the default, and it ships
    # with a mandatory null (N-AFF) written before the dimension exists: on artifacts with no
    # reconstructible maker the affective posterior must stay flat. An affective label is exactly
    # what a language model supplies fluently whether or not anything supports it.
    "soundingline/family/family_v3.yaml":
        "5b3a11f6a975f2e9c18566140ca01c76383b2ea923ab85a6c00b9b6a91098df4",
    "soundingline/family/family_v2.yaml":
        "ea256f1c664d0fa2d77cc23a38a233361fe94a4f4a08ef930eca0d29108bd89a",
    # Re-locked once, before commit and before any run: the first hash was taken while the
    # file still had CRLF line endings, which .gitattributes forbids and which hashlock treats
    # as content by design. The lock fired on the conversion, correctly. Recorded in
    # docs/DEVIATIONS.md rather than silently updated — this is a hash recorded in error, not a
    # criterion changed after seeing a result, and the distinction is the whole point.
    # v3 asks for 100 integer points rather than probabilities. Forced by the live bring-up:
    # asked for floats summing to 1.0, the model returned 2.50, then omitted a family value
    # entirely, then silently switched to percentages. "Distribute 100 points" is a task models
    # do reliably. v2 is retained, locked and unedited.
    # v4 adds the two-stage execution prompts. Reason in prose, then coerce — the published
    # mitigation for the format tax, and the fix for a confound that would have biased the
    # load-bearing comparison: the free-form baseline already had two-call reason-then-coerce
    # while the bounded arm generated straight into the grammar. Both arms now match.
    # v5 rewrites stage B as bounded counterfactual enumeration: list the moves a maker with
    # this purpose COULD have made, before reading what this one did. Gate 1 found the previous
    # wording made `support` a keyword detector — item B, a nine-word prompt, scored 1.00 on the
    # strength of a section headed "Alternative Builds Worth Considering", while item A, whose
    # rejections are stated outright, scored 0.00. Constraining the reading is the same move
    # SPEC §2 makes for the hypothesis family, applied one level down.
    # v6 adds stage ZERO, the anomaly pass, and a stage A that receives its output. Locked on
    # creation and NOT the default render path — the Gate 3 run in flight renders v5, and a
    # prompt that changes under a running gate is the drift Gate 0 named as this project's most
    # likely undocumented change. Callers opt in.
    "soundingline/probe/prompts/bounded_v6.yaml":
        "e4e3a945504751069281aa40190b33a764a4895383b6f1ad8e0974d247fdcbdd",
    "soundingline/probe/prompts/bounded_v5.yaml":
        "6a0f408f330c6dcf64508b978539d172ff3843e30b338871d49b0a8c9f20ec62",
    "soundingline/probe/prompts/bounded_v4.yaml":
        "ea0df083d8def48ee16cf94daf25eb043daf261d72976f8fc0af70ccd63747f9",
    "soundingline/probe/prompts/bounded_v3.yaml":
        "3f220ed07b7574b87545780db2bb95bb70cc6bc843aea4b3b303239e46c351ac",
    "soundingline/probe/prompts/bounded_v2.yaml":
        "8b1f4e0c5cc40bd9ce2ac88d2894549edd506b1a53ce0ea95b9898995ce2b371",

    # ── the generated rich/thin artifacts and their sealed protocol. Locked because the
    # protocol names which is which and predicts the ordering; a key that can be edited after
    # the curator answers is not a key.
    "docs/gate1/artifacts/item_A.md":
        "3b70b7e3d4bb587dc62811264206c49e4b306d9dec0635dceb88ce049f7ae1c8",
    "docs/gate1/artifacts/item_B.md":
        "8042aef86c1ce2c08f1c77f2393d54776cb39f4574d1fd8848c739ca69b58a88",
    "docs/gate1/artifacts/item_C.md":
        "a3260b9c432d57bda2a3045ff25dfb08cdd197b2b7267269d3c9afc0fddcf03e",
    "docs/gate1/artifacts/PROTOCOL_SEALED.md":
        "1a5bcbb64bf171dc23842700ce10f37b80b330e247b9eec485cdd6a3f3e23b7b",
}

# Not yet locked, and named here so the omission is deliberate rather than forgotten:
#
#   corpora/manifests/*  -- lock when the Gate 1 hand-picked set is chosen, so that
#                           "hand-picked by the author" is at least a fixed and inspectable
#                           selection. Cannot be locked before the artifacts exist.


def verify_all() -> None:
    """Raise on the first locked artifact that no longer matches.

    Called at the top of every experiment, before any model is touched.
    """
    for rel, expected in LOCKS.items():
        verify(REPO_ROOT / rel, expected)


if __name__ == "__main__":
    verify_all()
    print(f"all {len(LOCKS)} locks verified")
