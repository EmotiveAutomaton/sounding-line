"""Count-only BG admission. Outcome-bearing speech is opened separately after the census."""
from pathlib import Path

from .batch_runtime import filehash, read, freeze
from .timing_p6 import gzread
from .week6_la78_support_v1 import census

FILES = {
    "acts": ("original", "ACTS", "46cde8e75a429e89224fdab746c237f6f0f2f5d68d624d2835b94a7b9d6d46cd"),
    "laughs": ("original", "LAUGHS", "44c7fcde05eb02e19a67f84765c6b00133d0cd8e9ebf176daf896b4f8f98ff3f"),
    "metadata": ("extended", "METADATA_EXT", "31a026f5f51e684139d34d7e7b74c71133063b1d1bac9d7bc2cf61334ed0f3b2"),
    "speech": ("extended", "SPEECH", "d53550651a3c87c6bae95da6f5cba4cd9db9ca55e83a4c123aae8db589fb611d"),
}


def checked_table(inputs, key):
    source, name, expected = FILES[key]
    root = Path(inputs[source]).resolve(strict=True)
    proof = root / "COMPLETE.json"
    if filehash(proof) != inputs[source+"_sha256"]:
        raise ValueError("Source terminal changed")
    receipt = read(proof)
    relative = "output/" + name + ".json.gz"
    table = root / relative
    if (receipt.get("status") != "COMPLETE" or receipt.get("fresh_process_verified") is not True
            or receipt["outputs"].get(relative) != expected or table.is_symlink()
            or table.resolve(strict=True) != table or filehash(table) != expected):
        raise ValueError("Unverified BG source table: " + key)
    rows = gzread(table)
    if filehash(table) != expected:
        raise ValueError("Source table changed during projection")
    return rows


def support_first(output, inputs):
    output = Path(output)
    path = output / "BG_SUPPORT.json"
    acts = checked_table(inputs, "acts")
    laughs = checked_table(inputs, "laughs")
    metadata = checked_table(inputs, "metadata")
    support = census(acts, laughs, metadata)
    record = dict(amendment="BG", source_sha256={key:FILES[key][2] for key in ("acts","laughs","metadata")},
                  original_terminal_sha256=inputs["original_sha256"],
                  extended_terminal_sha256=inputs["extended_sha256"], populations=support)
    if path.is_file():
        if read(path) != record:
            raise ValueError("Prior support census differs")
    else:
        output.mkdir(parents=True,exist_ok=True)
        freeze(path,record)
    return acts, laughs, metadata, record


def outcome_speech(inputs, support_file):
    record = read(support_file)
    if (record["amendment"] != "BG" or record["source_sha256"] !=
            {key:FILES[key][2] for key in ("acts","laughs","metadata")}
            or record["original_terminal_sha256"] != inputs["original_sha256"]
            or record["extended_terminal_sha256"] != inputs["extended_sha256"]
            or set(record["populations"]) != {"LA7","LA8"}):
        raise ValueError("Matching pre-outcome support census required")
    return checked_table(inputs, "speech")
