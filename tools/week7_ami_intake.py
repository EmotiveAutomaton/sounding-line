"""Compare AMI delivery metadata with the previously reviewed meeting inventory.

DESIGN CHECK: a partial meeting gives no successor. A complete new meeting
opens source review. A changed prior channel or assignment stops the comparison.
This command reads public annotation and catalogue metadata only.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

from runners.drive.cards.week7_ami_channels import channel_map, complete_meetings
from runners.stage14.common import filehash, freeze, read


def compare(mapping, previous, catalogue):
    required = catalogue["coverage"]["required_channel_paths"]
    if (catalogue["slug"] != "ami-close-talk" or catalogue["class"] != "open-clean"
            or catalogue["license"] != "CC BY 4.0"
            or len(required) != len(mapping) or set(required) != set(mapping)):
        raise ValueError("AMI source or headset assignments changed")
    if (previous["source"] != catalogue["slug"] or previous["required"] != len(mapping)
            or previous["complete"] != complete_meetings(mapping, previous["files"])):
        raise ValueError("inconsistent previous inventory")

    files = {}
    for item in catalogue["local_files"]:
        if not item["assigned_in_annotation_metadata"]:
            continue
        prefix = "open/ami-close-talk/raw/"
        path = item["path"].replace("\\", "/")
        relative = path.removeprefix(prefix)
        if (not path.startswith(prefix) or relative not in mapping or relative in files
                or type(item["bytes"]) is not int or item["bytes"] <= 0
                or not re.fullmatch("[a-f0-9]{64}", item["sha256"])):
            raise ValueError("invalid assigned channel record")
        files[relative] = {"bytes": item["bytes"], "sha256": item["sha256"]}
    if any(files.get(name) != value for name, value in previous["files"].items()):
        raise ValueError("a previously reviewed channel is missing or changed")
    complete = complete_meetings(mapping, files)
    added = sorted(complete.keys() - previous["complete"].keys())
    return files, complete, added


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("previous", "archive", "catalogue", "output_directory"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    previous = read(args.previous)
    if filehash(args.archive) != previous["annotations"]:
        raise ValueError("annotation archive changed")
    raw = args.catalogue.read_bytes()
    files, complete, added = compare(channel_map(args.archive), previous, json.loads(raw))
    if added:
        pin = hashlib.sha256(raw).hexdigest()
        prior = filehash(args.previous)
        output = args.output_directory / f"AMI-review-{prior}-{pin}.json"
        freeze(output, dict(source=previous["source"], annotations=previous["annotations"],
                            required=previous["required"], files=files, complete=complete,
                            new_complete_meetings=added, previous_sha256=prior,
                            catalogue_sha256=pin, research_admitted=False))
    print(f"{len(files)} assigned channels, {len(complete)} complete meetings, {len(added)} newly complete")


if __name__ == "__main__":
    main()
