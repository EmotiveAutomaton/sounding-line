"""Direct-script worker bootstrap recording bytes actually compiled for project imports.

DESIGN CHECK: I01/X02/X12. Disable project bytecode-cache reads, hash the exact bytes
passed to Python's compiler, and require every loaded project source in the reviewed
closure. A parent-side current-file inventory is not a loaded-source receipt.
"""
import hashlib
import importlib.machinery
import json
import os
from pathlib import Path
import runpy
import sys
import time
import traceback


def main():
    config = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    repo = Path(config['repo']).resolve()
    output = Path(config['attempt']).resolve()
    expected = config['sources']['files']
    loaded = {}
    original = importlib.machinery.SourceFileLoader.get_code

    def record(path, source):
        key = path.relative_to(repo).as_posix()
        actual = hashlib.sha256(source).hexdigest()
        if expected.get(key) != actual:
            raise RuntimeError('unreviewed or changed loaded project source: '+key)
        loaded[key] = actual

    def get_code(loader, fullname):
        path = Path(loader.path).resolve()
        if path.is_relative_to(repo) and '.venv' not in path.parts:
            source = loader.get_data(str(path))
            record(path, source)
            return loader.source_to_code(source, str(path))
        return original(loader, fullname)

    record(Path(__file__).resolve(), Path(__file__).read_bytes())
    importlib.machinery.SourceFileLoader.get_code = get_code
    # Direct-script startup puts this package directory on sys.path. Leaving it
    # there makes `import queue` resolve our scheduler instead of the stdlib,
    # breaking dependencies such as torch. Project imports use the package root.
    script_directory = Path(__file__).resolve().parent
    sys.path[:] = [str(repo), *[entry for entry in sys.path
        if Path(entry or os.getcwd()).resolve() not in (script_directory, repo)]]
    started = time.time()
    code, error = 1, None
    try:
        from runners.stage9.common import write
        from runners.stage9.process_identity import native_identity
        write(output/'READY.json', {'process': native_identity(), 'at': time.time(),
                                   'cell_identity': config['cell_identity'], 'command': config['module']})
        os.environ['S9_CELL_IDENTITY'] = config['cell_identity']
        sys.argv = [config['module'], *config['arguments']]
        try:
            runpy.run_module(config['module'], run_name='__main__', alter_sys=True)
            code = 0
        except SystemExit as exc:
            code = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
    except BaseException:
        error = traceback.format_exc()
        sys.stderr.write(error)
    finally:
        # The parent also checks the final source files; this separate map records
        # only source bytes actually compiled and executed through this bootstrap.
        receipt = {'cell_identity': config['cell_identity'], 'started_at': started, 'ended_at': time.time(),
                   'returncode': code, 'loaded_project_sources': loaded, 'error': error,
                   'python': sys.version, 'bootstrap': 'project-source compilation bypasses pyc reads'}
        temporary = output/'EXECUTION.tmp'
        with temporary.open('w', encoding='utf-8', newline='\n') as stream:
            json.dump(receipt, stream, sort_keys=True, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, output/'EXECUTION.json')
    return code


if __name__ == '__main__':
    raise SystemExit(main())
