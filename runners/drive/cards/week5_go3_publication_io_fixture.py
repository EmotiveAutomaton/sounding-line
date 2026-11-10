"""Counted non-statistical publication proof with actual pause/fresh-replay units."""
from pathlib import Path
import ctypes
from ctypes import wintypes
import json
import os
import threading
import time
from . import week5_go3_publication as publication
from . import week5_output_size as monitor

io = publication.io
MODULE = 'runners.drive.cards.week5_go3_publication_io_fixture'
SOURCES = [Path(__file__), Path(monitor.__file__)]


def race_case(output):
    output.mkdir(parents=True, exist_ok=True)
    target, stable = output / 'VALUE.json', output / 'stable.bin'
    stable.write_bytes(b'preserved-stable-data')
    captured = []
    replace, lstat = io.os.replace, Path.lstat

    def replace_during_scan(source, destination):
        source, destination = Path(source), Path(destination)
        if not monitor.ATOMIC_JSON.fullmatch(source.name):
            raise ValueError('Actual writer did not use accepted UUID temporary format')
        before = monitor.output_bytes(output)
        if before != stable.stat().st_size + source.stat().st_size:
            raise ValueError('Existing temporary bytes were not counted')
        moved = False
        def racing_stat(path, *args, **kwargs):
            nonlocal moved
            if path == source and not moved:
                replace(source, destination)
                moved = True
            return lstat(path, *args, **kwargs)
        Path.lstat = racing_stat
        try:
            monitor.output_bytes(output)
        finally:
            Path.lstat = lstat
        if not moved or not destination.exists():
            raise ValueError('Deterministic real atomic-replace race was not exercised')
        captured.append(True)

    io.os.replace = replace_during_scan
    try:
        io.write_json(target, dict(numbers=[0, 1.25, -3], text='literal\nUnicode: \u03b2'))
    finally:
        io.os.replace = replace
        Path.lstat = lstat
    if publication.read(target) != dict(numbers=[0, 1.25, -3], text='literal\nUnicode: \u03b2') or captured != [True]:
        raise ValueError('Publication content or race count changed')
    return dict(actual_uuid_writer=True, present_temporary_counted=True, real_replaced_temporary_disappearance_tolerated=True,
                parsed_values_unchanged=True, stable_bytes_counted=True)


def refusal_case(output):
    output.mkdir(parents=True, exist_ok=True)
    stable = output / 'ordinary.bin'
    stable.write_bytes(b'retain')
    lstat = Path.lstat
    passed = []
    for error in (FileNotFoundError, PermissionError):
        def refused(path, *args, **kwargs):
            if path == stable:
                raise error('constructed precise scan failure')
            return lstat(path, *args, **kwargs)
        Path.lstat = refused
        try:
            try:
                monitor.output_bytes(output)
            except error:
                passed.append(error.__name__)
            else:
                raise ValueError('Ordinary file/permission error was weakened')
        finally:
            Path.lstat = lstat
    return dict(ordinary_disappearance_refused=True, permission_error_refused=True, observed=passed)


def sharing_case(output):
    if os.name != 'nt':
        raise ValueError('Actual Windows sharing fixture must run on its declared platform')
    output.mkdir(parents=True, exist_ok=True)
    target = output / 'SHARED.json'
    io.write_json(target, dict(version=0))
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
                                  wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = kernel.CreateFileW(str(target.resolve()), 0x80000000, 0x1, None, 3, 0x80, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    replace, failures = io.os.replace, []
    released = threading.Event()
    def release():
        time.sleep(.075)
        try:
            if not kernel.CloseHandle(handle):
                raise ctypes.WinError(ctypes.get_last_error())
        finally:
            released.set()
    def attempted(source, destination):
        try:
            return replace(source, destination)
        except PermissionError:
            failures.append(True)
            raise
    closer = threading.Thread(target=release)
    closer.start()
    io.os.replace = attempted
    try:
        io.write_json(target, dict(version=1))
    finally:
        io.os.replace = replace
        closer.join(timeout=3)
    if not released.is_set() or not failures or publication.read(target) != dict(version=1):
        raise ValueError('Actual non-delete-sharing denial and bounded recovery were not observed')
    return dict(real_windows_non_delete_sharing_denial=True, bounded_replace_retry_recovered=True,
                final_value_replayed=True)


CASES = (race_case, refusal_case, sharing_case)


def execute(output, inputs, config):
    if inputs or config != {'phase': 'publication-qualification'}:
        raise ValueError('Exact isolated publication qualification contract required')
    output = Path(output)
    publication.bind(output, MODULE, SOURCES, inputs, config)
    state_path = output / 'CASES.json'
    seal = output / 'CASES.seal.json'
    if state_path.exists() or seal.exists():
        if not state_path.is_file() or not seal.is_file() or publication.read(seal).get('sha256') != io.sha(state_path):
            raise ValueError('Publication case checkpoint is unsealed or changed')
        rows = publication.read(state_path)
    else:
        rows = []
    if len(rows) > len(CASES):
        raise ValueError('Extra publication fixture cases')
    for index, function in enumerate(CASES):
        if index < len(rows):
            if rows[index]['case'] != function.__name__:
                raise ValueError('Changed publication case order')
            directory = output / ('case-' + str(index))
            current = {p.relative_to(directory).as_posix(): io.sha(p) for p in directory.rglob('*') if p.is_file()}
            if rows[index]['files'] != current:
                raise ValueError('Completed publication case output changed')
            continue
        directory = output / ('case-' + str(index))
        if directory.exists():
            raise ValueError('Unsealed publication case output is not resumable')
        result = function(directory)
        files = {p.relative_to(directory).as_posix(): io.sha(p) for p in directory.rglob('*') if p.is_file()}
        rows.append(dict(case=function.__name__, result=result, files=files))
        io.write_json(state_path, rows)
        io.write_json(output / 'CASES.seal.json', dict(sha256=io.sha(state_path)))
        if index == 0:
            return dict(status='yielded', phase='publication_qualification', completed=1, total=3,
                        constructed_only=True, no_model_or_source_execution=True)
    proof = dict(verified=True, constructed_only=True, no_model_or_source_execution=True,
                 deterministic_atomic_publication_cases_passed=True, cases=rows,
                 publication_spec='GO3-UUID-1', sources=publication.identity(MODULE, SOURCES, inputs, config)['sources'])
    io.write_json(output / 'PROOF.json', proof)
    return proof


def verify(output, inputs, config):
    output = Path(output)
    publication.bind(output, MODULE, SOURCES, inputs, config)
    result = execute(output / 'independent-replay', inputs, config)
    if result.get('status') == 'yielded':
        return result | dict(verified=False)
    if result != publication.read(output / 'PROOF.json'):
        raise ValueError('Independent publication cases did not replay')
    return dict(verified=True, constructed_only=True, deterministic_publication_cases_replayed=True,
                no_model_or_source_execution=True, publication_spec='GO3-UUID-1')
