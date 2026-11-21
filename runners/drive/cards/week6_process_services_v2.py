"""Exact native proof for the completion-first watcher. Other service proofs remain shared."""
from pathlib import Path
from .week6_process_services_v1 import (REPO, WATCHER, WINDOWLESS, CODE_PINS as PREVIOUS_PINS,
    IMAGE_PINS, check_pins, check_census, observe, watcher_boot, key, need)

CODE_PINS = {**PREVIOUS_PINS, str(WATCHER): "bb9376d2bf96d7c3fcace3a9b84061f2e486ee7957a7c5fd825988fca7b8ca9b"}

def watcher_compatibility(record):
    need(record.get('kind')=='sounding-line-durable-watcher' and record.get('owner_reviewed') is True,
         'Unreviewed non-budget service')
    need(record['source_pins']==CODE_PINS,'Different watcher implementation')
    need(record['image_pins']=={str(WINDOWLESS):IMAGE_PINS[str(WINDOWLESS)]},'Different watcher image')
    check_pins(CODE_PINS);check_pins(record['image_pins'])
    native=record['native'];key(native)
    need(native['executable']==str(WINDOWLESS),'Different watcher interpreter')
    expected=[str(WINDOWLESS),'-B',str(WATCHER),'run']
    need(record['command']==expected and Path(record['cwd'])==REPO,'Different watcher command or cwd')
    boot=watcher_boot()
    need(boot==record['startup'] and boot['pid']==native['pid'],'Watcher startup changed')
    for name,field in ((WATCHER,'source_sha256'),(REPO/'tools/codex_common.py','common_sha256'),
                       (REPO/'tools/codex_queue_api.py','queue_api_sha256')):
        need(boot[field]==CODE_PINS[str(name)],'Loaded watcher code differs')
    birth=native['created_ticks']/10_000_000-11644473600
    need(0<=boot['started']-birth<=60,'Watcher startup and creation time differ')
    for name in CODE_PINS:
        need(Path(name).stat().st_mtime<=birth,'Watcher dependency changed since process creation')
    current=observe(native['pid'])
    if current is None:return None
    need(current['native']==native,'Watcher PID identity changed')
    need(current['command']==record['command'] and current['cwd']==record['cwd'],
         'Live watcher command or cwd changed')
    return native
