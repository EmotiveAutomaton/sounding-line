"""Validate the approved Santa Barbara map inside a mounted LGH1 job before analysis."""
import hashlib
from pathlib import Path, PurePosixPath
import wave
import zipfile


def mount_path(root, name):
    path = PurePosixPath(name)
    if not path.parts or path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name:
        raise ValueError("Invalid mount-relative path")
    value = (root / Path(*path.parts)).resolve(strict=True)
    if not value.is_relative_to(root) or not value.is_file():
        raise ValueError("File outside mount")
    return value


def verify_layout(root, mapping, *, expected_count=60):
    """Return matched-file count only. A successful layout check does not bind laugh timing or speakers."""
    root = Path(root).resolve(strict=True)
    rows = mapping["items"]
    for field in ("recording_id", "recording", "transcript_member"):
        if len(rows) != expected_count or len({row[field] for row in rows}) != expected_count:
            raise ValueError("Incomplete or ambiguous recording map")
    archive = mount_path(root, mapping["transcript_archive"])
    with archive.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != mapping["transcript_archive_sha256"]:
            raise ValueError("CHAT archive digest mismatch")
        stream.seek(0)
        with zipfile.ZipFile(stream) as bundle:
            names = bundle.namelist()
            for row in rows:
                member = row["transcript_member"]
                if names.count(member) != 1 or not member.endswith(".cha"):
                    raise ValueError("Ambiguous or absent CHAT member")
                info = bundle.getinfo(member)
                if info.file_size != row["transcript_bytes"] or f"{info.CRC:08x}" != row["transcript_zip_crc32"].lower():
                    raise ValueError("CHAT member binding mismatch")
                path = mount_path(root, row["recording"])
                if path.stat().st_size != row["bytes"]:
                    raise ValueError("Wave file length mismatch")
                with path.open("rb") as wav:
                    if hashlib.file_digest(wav, "sha256").hexdigest() != row["recording_sha256"]:
                        raise ValueError("Wave file digest mismatch")
                    wav.seek(0)
                    with wave.open(wav) as audio:
                        if audio.getnchannels() < 1 or audio.getframerate() <= 0 or audio.getnframes() <= 0:
                            raise ValueError("Invalid wave header")
    return len(rows)

