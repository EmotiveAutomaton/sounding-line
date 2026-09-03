
import os, sys
CAP = os.path.normcase(os.path.abspath(os.getcwd()))
STD = [os.path.normcase(os.path.abspath(sys.base_prefix)), os.path.normcase(os.path.abspath(sys.exec_prefix))]
OUT = os.path.join(CAP, "out")
TMP = os.path.join(CAP, "tmp")
_ep = os.environ.get("S7_ENDPOINT", "http://127.0.0.1:0")
_hp = _ep.split("//", 1)[-1].split("/", 1)[0]
HOST, PORT = _hp.split(":")[0], int(_hp.split(":")[1])
DENY_MODULES = ("runners", "soundingline", "constructor", "scoring", "oracle", "torch", "numpy", "transformers", "ctypes", "subprocess", "multiprocessing")
COUNTS = {"allowed": 0, "denied": 0, "events": {}}

def _norm(p):
    if isinstance(p, bytes):
        p = p.decode("utf-8", "replace")
    return os.path.normcase(os.path.abspath(str(p)))

def _under(p, roots):
    p = _norm(p)
    return any(p == r or p.startswith(r.rstrip("\\/") + os.sep) for r in roots)

def _deny(event, why):
    COUNTS["denied"] += 1
    COUNTS["events"][event] = COUNTS["events"].get(event, 0) + 1
    raise RuntimeError("capsule boundary: %s (%s)" % (event, why))

WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC

def _hook(event, args):
    if event == "open":
        path, mode, flags = args
        if path is None or isinstance(path, int):
            return
        writing = (mode and any(c in mode for c in "wax+")) or (flags and (flags & WRITE_FLAGS))
        if writing:
            if not _under(path, [OUT, TMP]):
                _deny(event, "write outside out/ and tmp/: %s" % path)
        elif not _under(path, [CAP] + STD):
            _deny(event, "read outside the capsule: %s" % path)
        COUNTS["allowed"] += 1
    elif event in ("os.listdir", "os.scandir", "glob.glob", "os.walk"):
        p = args[0] if args else None
        if p is not None and not isinstance(p, int) and not _under(p, [CAP] + STD):
            _deny(event, str(p))
    elif event in ("os.mkdir", "os.rename", "os.remove", "os.unlink", "os.rmdir", "os.truncate", "shutil.rmtree", "shutil.move", "shutil.copyfile"):
        for p in args[:2]:
            if isinstance(p, (str, bytes)) and not _under(p, [OUT, TMP]):
                _deny(event, str(p))
    elif event == "socket.connect":
        addr = args[1] if len(args) > 1 else None
        if not (isinstance(addr, tuple) and len(addr) >= 2 and addr[0] in (HOST, "127.0.0.1", "localhost") and int(addr[1]) == PORT):
            _deny(event, str(addr))
    elif event == "socket.getaddrinfo":
        host = args[0]
        if host not in (HOST, "127.0.0.1", "localhost"):
            _deny(event, str(host))
    elif event in ("subprocess.Popen", "os.system", "os.exec", "os.spawn", "os.fork", "os.posix_spawn",
                   "os.startfile", "ctypes.dlopen", "ctypes.cdll", "ctypes.seh_exception", "os.putenv",
                   "os.unsetenv", "os.chdir", "os.kill", "os.killpg", "winreg.OpenKey", "winreg.CreateKey",
                   "webbrowser.open", "socket.bind", "socket.sendto", "os.link", "os.symlink", "os.chmod"):
        _deny(event, "forbidden operation")
    elif event == "import":
        module, filename = args[0], args[1]
        top = str(module).split(".")[0]
        if top in DENY_MODULES:
            _deny(event, str(module))
        if filename and not _under(filename, [CAP] + STD):
            _deny(event, "%s from %s" % (module, filename))
    elif event == "sys.addaudithook":
        _deny(event, "a second hook")

sys.addaudithook(_hook)
sys.path[:] = [CAP] + [p for p in sys.path if p and _under(p, STD)]
import json
try:
    from reader import worker
    rc = worker.main()
finally:
    try:
        os.makedirs(OUT, exist_ok=True)
        with open(os.path.join(OUT, "access.json"), "w", encoding="utf-8") as fh:
            json.dump({"counts": COUNTS, "sys_path": sys.path, "cwd": CAP, "env": sorted(os.environ)}, fh, indent=1, sort_keys=True)
    except Exception:
        pass
sys.exit(rc)
