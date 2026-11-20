"""Map the parent table's annotation labels before fitting the LA9 follow-up."""
from collections import Counter
from hashlib import sha256
from pathlib import Path
import re


def dictionaries(registration, ami_ontology, icsi_file):
    """Require the published dictionaries at the exact prospective identities."""
    if registration["schema"] != "LA9_PUBLISHED_CLASS_MAPS_V1":
        raise ValueError("Unexpected LA9 registration")
    from xml.etree import ElementTree
    ami = registration["ami"]
    if sha256(ami_ontology).hexdigest() != ami["ontology_sha256"]:
        raise ValueError("AMI ontology differs")
    keys = {entry.get("{http://nite.sourceforge.net/}id")
            for entry in ElementTree.fromstring(ami_ontology).iter("da-type")}
    lookup = {}
    for category, numbers in ami["groups"].items():
        for number in numbers:
            tag = f"ami_da_{number}"
            if tag in lookup or tag not in keys:
                raise ValueError("AMI pointer missing or duplicated")
            lookup[tag] = category
    if set(lookup) != {key for key in keys if key and re.fullmatch(r"ami_da_\d+", key)}:
        raise ValueError("Incomplete AMI mapping")
    scheme = registration["icsi"]
    data = Path(icsi_file).read_bytes()
    if sha256(data).hexdigest() != scheme["sha256"]:
        raise ValueError("ICSI class dictionary differs")
    tagged = {}
    for line in data.decode("utf-8").splitlines():
        key, code = line.split("\t")
        if key in tagged or code not in {*scheme["groups"], scheme["unscored"]}:
            raise ValueError("Unexpected or duplicate MRDA class")
        tagged[key] = scheme["groups"].get(code)
    if len(tagged) != scheme["records"]:
        raise ValueError("Incomplete MRDA mapping")
    return {"AMI": lookup, "ICSI": tagged}


def pooled_class(corpus, label, maps):
    if corpus == "AMI":
        match = re.fullmatch(r"id\((ami_da_\d+)\)", label)
        category = maps[corpus].get(match.group(1)) if match else None
    elif corpus == "ICSI":
        category = maps[corpus].get(label)
    else:
        raise ValueError("Meeting has no recognized corpus")
    return f"{corpus}/{category}" if category is not None else None


def relabel(rows, meeting_corpora, maps, floor=50):
    """Retain all parent pairs. Control reuse adds a fit weight, never a new utterance."""
    if type(floor) is not int or floor < 1:
        raise ValueError("Positive distinct-utterance floor required")
    known = {}
    changed = []
    for row in rows:
        meeting = row["meeting"]
        corpus = meeting_corpora[meeting]
        original = row["act_type"]
        tag = pooled_class(corpus, original, maps)
        if tag is None:
            # Unmapped annotations remain distinct nuisance levels in the original pairs.
            tag = "unmapped/" + corpus + "/" + sha256(original.encode()).hexdigest()
        key = (meeting, row["id"])
        if known.setdefault(key, tag) != tag:
            raise ValueError("Inconsistent class for a reused utterance")
        changed.append(dict(row, act_type=tag))
    counted = Counter(known.values())
    classes = sorted({corpus + "/" + group for corpus, table in maps.items()
                      for group in table.values() if group is not None})
    support = {tag: {"distinct_utterances": counted[tag], "eligible": counted[tag] >= floor}
               for tag in classes}
    return changed, support, sum(n for tag,n in counted.items() if tag.startswith("unmapped/"))
