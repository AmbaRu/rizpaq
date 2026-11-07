
































from __future__ import annotations

import os
import time

                                                                        
                                   
STALL_TIMEOUT = 20

                                                                        
                                                                      
STALL_TIMEOUT_BUSY = 600

                                                                          
                                                                          
                                                             
                                                                       
          
CPU_SAMPLE_INTERVAL = 0.25

                                                                      
                                                  
 
                                                                        
                                                                        
                                                                     
                                                                         
                                                                      
                                              
 
                                                                    
                                                                          
                                                                    
                                                                   
                                                                   
                                                                          
                                                                   
CPU_BUSY_RATIO = 0.10

                                                                      
                                                                       
                                                  
CPU_BUSY_FLOOR = 0.05


def effective_stall_timeout(module_default: float, module_value: float,
                            config_path=None) -> float:
    pass














    if module_value != module_default:
        return float(module_value)
    try:
        from core.config import engine_stall_timeout
        return engine_stall_timeout(module_default, config_path)
    except Exception:
        return float(module_default)


def _cpu_seconds_windows(handle) -> float:
    pass
    try:
        import ctypes

        k32 = ctypes.windll.kernel32
        c = ctypes.c_ulonglong()
        e = ctypes.c_ulonglong()
        k = ctypes.c_ulonglong()
        u = ctypes.c_ulonglong()
        if not k32.GetProcessTimes(handle, ctypes.byref(c), ctypes.byref(e),
                                   ctypes.byref(k), ctypes.byref(u)):
            return 0.0
                                        
        return (k.value + u.value) / 10_000_000.0
    except Exception:
        return 0.0


def _cpu_seconds_posix(pid) -> float:
    pass
    try:
        with open(f"/proc/{pid}/stat", "rb") as f:
            data = f.read()
                                                                   
                                                                       
        tail = data[data.rindex(b")") + 2:].split()
        hz = os.sysconf("SC_CLK_TCK")
        return (int(tail[11]) + int(tail[12])) / hz
    except Exception:
        return 0.0


def make_cpu_reader(proc):
    pass






    handle = getattr(proc, "_handle", None)
    if handle is not None and os.name == "nt":
        return lambda: _cpu_seconds_windows(handle)
    pid = getattr(proc, "pid", None)
    if pid:
        return lambda: _cpu_seconds_posix(pid)
    return lambda: 0.0


class Liveness:
    pass


















    def __init__(self, cpu_reader, now=time.monotonic,
                 stall_timeout: float = STALL_TIMEOUT,
                 busy_timeout: float = STALL_TIMEOUT_BUSY):
        pass








        self._cpu = cpu_reader
        self._now = now
        self.stall_timeout = stall_timeout
        self.busy_timeout = busy_timeout
        self.last_data = now()
        self._cpu_at = now()
        self._cpu_val = cpu_reader()
                                                                          
                                                                      
                                                                 
                                           
        self._cpu_at_data = self._cpu_val
        self._cpu_sampled = self._cpu_val
        self._sample_at = self._cpu_at
        self.last_silent = 0.0
        self.last_cpu_delta = 0.0
        self.busy = False

    def note_data(self):
        pass
        t = self._now()
        self.last_data = t
        self._sample(t)
                                                                     
        self._cpu_at_data = self._cpu_sampled

    def _sample(self, t=None):
        pass











        t = self._now() if t is None else t
        if t - self._sample_at < CPU_SAMPLE_INTERVAL:
            return
        self._cpu_sampled = self._cpu()
        self._sample_at = t
        silent = t - self.last_data
        used = self._cpu_sampled - self._cpu_at_data
        self.last_cpu_delta = used
        self.busy = used > max(CPU_BUSY_FLOOR, CPU_BUSY_RATIO * silent)

    def verdict(self):
        pass




        t = self._now()
        self.last_silent = t - self.last_data
        self._sample(t)
        return self

    @property
    def stalled(self) -> bool:
        if self.busy:
            return self.last_silent > self.busy_timeout
        return self.last_silent > self.stall_timeout

    def describe(self) -> str:
        pass
        state = "работал" if self.busy else "простаивал"
        return (f"молчал {self.last_silent:.0f} с, при этом {state} "
                f"(процессорное время выросло на {self.last_cpu_delta:.1f} с)")
