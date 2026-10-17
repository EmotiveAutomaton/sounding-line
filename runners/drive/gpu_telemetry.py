"""Read-only NVML telemetry; no shell per candidate and no cached samples.

DESIGN CHECK: LESSONS 3-5 read October 17. NULL: unsupported API, invalid
memory accounting, identity mismatch or telemetry disagreement refuses.
ALTERNATIVE: fresh readings match the existing command; identical check cadence
and safety floors remain. Never alter driver settings or other GPU processes.
"""
import atexit,ctypes,math,os,subprocess
from pathlib import Path

DLL=Path('C:/Windows/System32/nvml.dll')
class Memory(ctypes.Structure):
    _fields_=[('version',ctypes.c_uint),('total',ctypes.c_ulonglong),
              ('reserved',ctypes.c_ulonglong),('free',ctypes.c_ulonglong),('used',ctypes.c_ulonglong)]

def checked(code):
    if code:raise RuntimeError('NVML query failed: '+str(code))

def reading(memory,temperature):
    if memory.total<=0 or any(x>memory.total for x in (memory.free,memory.used,memory.reserved)):
        raise ValueError('invalid NVML memory')
    if abs(memory.total-memory.free-memory.used-memory.reserved)>2**20 or not 0<temperature<150:
        raise ValueError('invalid NVML accounting/temperature')
    # Round free memory down, never above the existing integer-MiB safety floor.
    return dict(free_MiB=math.floor(memory.free/2**20),used_MiB=math.ceil(memory.used/2**20),temperature_C=temperature)

def compare(before,command,after):
    if before['uuid']!=after['uuid'] or command['uuid']!=before['uuid']:
        raise ValueError('GPU identity mismatch')
    for key,tolerance in [('free_MiB',16),('used_MiB',16),('temperature_C',2)]:
        if not min(before[key],after[key])-tolerance<=command[key]<=max(before[key],after[key])+tolerance:
            raise ValueError('GPU telemetry disagreement: '+key)
    return True

class Nvml:
    def __init__(self):
        if os.name!='nt' or not DLL.is_file():raise RuntimeError('installed Windows NVML required')
        self.lib=ctypes.CDLL(str(DLL));self.active=False
        signatures={'nvmlInit_v2':[], 'nvmlShutdown':[],
            'nvmlDeviceGetCount_v2':[ctypes.POINTER(ctypes.c_uint)],
            'nvmlDeviceGetHandleByIndex_v2':[ctypes.c_uint,ctypes.POINTER(ctypes.c_void_p)],
            'nvmlDeviceGetMemoryInfo_v2':[ctypes.c_void_p,ctypes.POINTER(Memory)],
            'nvmlDeviceGetTemperature':[ctypes.c_void_p,ctypes.c_uint,ctypes.POINTER(ctypes.c_uint)],
            'nvmlDeviceGetUUID':[ctypes.c_void_p,ctypes.c_char_p,ctypes.c_uint]}
        for name,args in signatures.items():
            function=getattr(self.lib,name);function.argtypes=args;function.restype=ctypes.c_int
        checked(self.lib.nvmlInit_v2());self.active=True
        try:
            count=ctypes.c_uint();checked(self.lib.nvmlDeviceGetCount_v2(ctypes.byref(count)))
            if count.value!=1:raise ValueError('single GPU required; do not guess device')
            self.device=ctypes.c_void_p();checked(self.lib.nvmlDeviceGetHandleByIndex_v2(0,ctypes.byref(self.device)))
            value=ctypes.create_string_buffer(96);checked(self.lib.nvmlDeviceGetUUID(self.device,value,96))
            self.uuid=value.value.decode('ascii')
            if not self.uuid.startswith('GPU-'):raise ValueError('invalid GPU identity')
        except BaseException:
            self.close();raise
        atexit.register(self.close)
    def close(self):
        if self.active:
            self.active=False;checked(self.lib.nvmlShutdown())
    def sample(self):
        if not self.active:raise RuntimeError('NVML closed')
        memory=Memory();memory.version=ctypes.sizeof(Memory)|(2<<24);temperature=ctypes.c_uint()
        checked(self.lib.nvmlDeviceGetMemoryInfo_v2(self.device,ctypes.byref(memory)))
        checked(self.lib.nvmlDeviceGetTemperature(self.device,0,ctypes.byref(temperature)))
        return dict(**reading(memory,temperature.value),uuid=self.uuid)
    def crosscheck(self):
        before=self.sample()
        raw=subprocess.check_output(['nvidia-smi','--query-gpu=uuid,memory.free,memory.used,temperature.gpu','--format=csv,noheader,nounits'],timeout=20,text=True)
        parts=raw.strip().split(',')
        if len(parts)!=4:raise ValueError('ambiguous command telemetry')
        command=dict(uuid=parts[0].strip(),**dict(zip(('free_MiB','used_MiB','temperature_C'),map(float,parts[1:]))))
        if not all(math.isfinite(command[k]) for k in ('free_MiB','used_MiB','temperature_C')):raise ValueError('nonfinite command telemetry')
        after=self.sample();compare(before,command,after)
        return dict(before=before,command=command,after=after)

_client=None
def client():
    global _client
    if _client is None:_client=Nvml()
    return _client
def gpu():
    return {k:v for k,v in client().sample().items() if k!='uuid'}
def crosscheck():return client().crosscheck()
