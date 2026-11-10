"""Strict Week 5 byte accounting with the observed GO3 journal race handled.

DESIGN CHECK: LESSONS 5. Every present regular file, including temporary
journals, counts toward the unchanged byte cap. Only the exact approved
transient paths may disappear. Other I/O errors and link traversal refuse.
"""
from pathlib import Path
import os
import re
import stat

ATOMIC_JSON = re.compile(r'.+\.json\.[0-9a-f]{32}\.tmp|PROGRESS\.json\.[1-9][0-9]*\.tmp')
GO3_JOURNALS = frozenset({'projection.sqlite-journal', 'independent-replay/projection.sqlite-journal'})


def reject_link(info):
    if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
        raise ValueError('Output byte accounting refuses symlinks and reparse points')


def vanished_transient(path, root):
    if ATOMIC_JSON.fullmatch(path.name):
        return True
    if path.relative_to(root).as_posix() not in GO3_JOURNALS:
        return False
    # A suffix alone is not enough: this is the exact source producer's
    # DELETE-mode rollback-journal path, beside its existing regular database.
    sibling = path.with_name('projection.sqlite')
    info = sibling.lstat()
    reject_link(info)
    if not stat.S_ISREG(info.st_mode):
        raise ValueError('GO3 journal companion is not a regular database file')
    return True


def output_bytes(directory):
    root = Path(directory)
    try:
        info = root.lstat()
    except FileNotFoundError:
        # Preserve the original initial child-start state before output exists.
        return 0
    reject_link(info)
    if not stat.S_ISDIR(info.st_mode):
        raise ValueError('Output root is not a directory')
    total = 0
    pending = [root]
    while pending:
        current = pending.pop()
        # Unlike glob, explicit scandir does not silently suppress directory
        # permission/scan failures. No entry is followed before lstat checks.
        with os.scandir(current) as entries:
            for entry in entries:
                path = Path(entry.path)
                try:
                    info = path.lstat()
                except FileNotFoundError:
                    if vanished_transient(path, root):
                        continue
                    raise
                reject_link(info)
                if stat.S_ISREG(info.st_mode):
                    total += info.st_size
                elif stat.S_ISDIR(info.st_mode):
                    pending.append(path)
    return total
