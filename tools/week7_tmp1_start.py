"""Prepare or submit the Week 7 TMP1 entry from a reviewed, metadata-only mount receipt."""
import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path

from runners.drive.cards import week7_gear as gear
from runners.stage14.common import filehash, freeze, now, read

HERE = Path(__file__).resolve().parents[1] / ".agent-state/drive-20261115/week7-phase1"
TRAITS = {"Openness", "Extraversion", "Agreeableness", "Conscientiousness", "Neuroticism"}
JOB = "tmp1-w7-pandora-real"
FIXTURE = "tmp1-tp58-delivery-a"


def candidate(receipt, binding_digest, requested, balance):
    source = receipt["mount"]
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,62}", source) or source == FIXTURE:
        raise ValueError("Expected the reviewed real source alias")
    if receipt["provider_binding_sha256"] != binding_digest:
        raise ValueError("Provider binding differs")
    fields = [receipt["comments_author_key"], receipt["profiles_author_key"],
              receipt["exclusion_list_reference"]]
    if set(receipt["traits"]) != TRAITS:
        raise ValueError("Five source traits required")
    for trait in receipt["traits"].values():
        fields.extend((trait["field"], trait["units"]))
    if not all(isinstance(value, str) and value.strip() for value in fields):
        raise ValueError("Incomplete provider mapping")
    total, by_row, invocations = balance
    used = sum(amount for (card, _), amount in by_row.items() if card == "TMP1")
    available = math.floor(min(20000 - used, gear.CEILING - total))
    if not 1 <= requested <= available or invocations >= gear.SEALED_LIMIT:
        raise ValueError("Insufficient remaining CPU or sealed invocations")
    qualified = {
        HERE / "prepare_tmp1_real.py": "18fcd1477db417e6499a63e5df69fd8493010f4724c2bdfdd7c35afcd454e0ca",
        gear.REPO / "runners/drive/sealed/week7_tmp1_shell.py": "9c5e8ff380cc28eb36a180e8f97c37428491665429e72c9eb4aa3723a650f5a6",
    }
    for path, digest in qualified.items():
        if filehash(path) != digest:
            raise ValueError("Qualified source differs: " + path.name)
    from prepare_tmp1_real import render
    return render(receipt["projection_sha256"], requested)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("receipt_sha256", help="SHA-256 from the owner's source review")
    parser.add_argument("provider_binding", type=Path, help="Reviewed release-specific mapping note")
    parser.add_argument("cpu_seconds", type=int)
    parser.add_argument("--submit", action="store_true")
    args = parser.parse_args()
    raw = args.receipt.read_bytes()
    if hashlib.sha256(raw).hexdigest() != args.receipt_sha256:
        raise ValueError("Source receipt differs from review")
    receipt = json.loads(raw)
    note_hash = filehash(args.provider_binding)
    sys.path.insert(0, str(HERE))
    entry = candidate(receipt, note_hash, args.cpu_seconds, gear.balance()).encode("utf8")
    entry_hash = hashlib.sha256(entry).hexdigest()
    if not args.submit:
        print(json.dumps({"prepared_entry_sha256": entry_hash, "source": receipt["mount"]}))
        return

    from submit_tmp1_image_check import image, opts, owner, remote, upload
    if remote("cat /srv/open/pins/sl-tabular-2026-11-16.txt").splitlines()[-1] != image:
        raise RuntimeError("Target image pin differs")
    controls = remote("sha256sum /usr/local/bin/sealed-run /usr/local/lib/sealed-gate.py")
    if [line.split()[0] for line in controls.splitlines()] != [
        owner["installed_runner_sha256"], owner["installed_gate_sha256"]
    ]:
        raise RuntimeError("Installed launcher or release gate differs")
    out = gear.ROOT / JOB
    remote_dir = "/home/agent/sealed-jobs/" + JOB
    pins = {str(args.receipt): args.receipt_sha256, str(args.provider_binding): note_hash}
    for path in (gear.AUTHORITY, Path(__file__), HERE / "prepare_tmp1_real.py",
                 HERE / "submit_tmp1_image_check.py", HERE / "TP58-delivery-a/manifest.json",
                 gear.REPO / "runners/drive/sealed/week7_tmp1_shell.py"):
        pins[str(path)] = filehash(path)
    path = HERE / ("tmp1-real-" + entry_hash + ".py")
    try:
        with path.open("xb") as stream:
            stream.write(entry)
    except FileExistsError:
        if filehash(path) != entry_hash:
            raise RuntimeError("Prepared entry differs")
    pins[str(path)] = entry_hash
    with gear.admit(out, card="TMP1", source=receipt["mount"], requested=args.cpu_seconds,
                    row_limit=20000, peak=2, sealed=True, pins=pins):
        submitted = False
        try:
            # The reservation is now in the ledger, including any concurrent admissions.
            _, charges, _ = gear.balance()
            if sum(v for (c, _), v in charges.items() if c == "TMP1") > 20000:
                raise RuntimeError("Whole-row allowance exhausted")
            (out / "run.py").write_bytes(entry)
            remote("mkdir " + remote_dir)
            upload(path, remote_dir + "/run.py")
            freeze(out / "SUBMITTED.json", dict(at=now(), entry=entry_hash, source=receipt["mount"]))
            submitted = True
            call = subprocess.run(["ssh", *opts, "spark", "sudo -n sealed-run " + JOB + " " +
                                   receipt["mount"]], stdin=subprocess.DEVNULL,
                                  capture_output=True, text=True)
            reply = call.stdout.strip()
            success = call.returncode == 0 and re.fullmatch(
                "gate passed; totals in /home/agent/sealed-totals/" + JOB + r"-[0-9]{8}T[0-9]{6}", reply)
            freeze(out / "EXIT.json", dict(at=now(), client_code=call.returncode,
                   totals=reply.split()[-1] if success else None))
            if not success:
                raise RuntimeError("Inspect sealed exit before any recovery")
        except BaseException:
            freeze(out / "FAILED.json", dict(at=now(), submitted=submitted,
                   inspect_remote_before_retry=submitted))
            raise
        finally:
            gear.settle(out, args.cpu_seconds if submitted else 0,
                        "Full reserved cap upon submission.", never_submitted=not submitted)
        freeze(out / "COMPLETE.json", dict(at=now(), passed_gate=True, entry=entry_hash))


if __name__ == "__main__":
    main()
