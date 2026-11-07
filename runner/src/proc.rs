









use std::os::windows::io::AsRawHandle;
use std::process::Child;



pub const DEFAULT_STALL_TIMEOUT: f64 = 90.0;



pub const BUSY_STALL_MULTIPLIER: f64 = 30.0;


pub const CPU_SAMPLE_INTERVAL: f64 = 0.25;



pub const CPU_BUSY_RATIO: f64 = 0.10;



pub const CPU_BUSY_FLOOR: f64 = 0.05;

type HANDLE = *mut core::ffi::c_void;

#[link(name = "kernel32")]
extern "system" {
    fn GetProcessTimes(
        hProcess: HANDLE,
        lpCreationTime: *mut u64,
        lpExitTime: *mut u64,
        lpKernelTime: *mut u64,
        lpUserTime: *mut u64,
    ) -> i32;
}



pub fn cpu_seconds(child: &Child) -> f64 {
    let handle = child.as_raw_handle();
    let mut c: u64 = 0;
    let mut e: u64 = 0;
    let mut k: u64 = 0;
    let mut u: u64 = 0;
    let ok = unsafe {
        GetProcessTimes(handle as HANDLE, &mut c, &mut e, &mut k, &mut u)
    };
    if ok == 0 {
        return 0.0;
    }
    
    (k.wrapping_add(u)) as f64 / 10_000_000.0
}



pub struct Liveness {
    cpu_reader: Box<dyn Fn() -> f64>,
    pub stall_timeout: f64,
    pub busy_timeout: f64,
    last_data: f64,
    cpu_at_data: f64,
    cpu_sampled: f64,
    sample_at: f64,
    pub last_silent: f64,
    pub last_cpu_delta: f64,
    pub busy: bool,
}

fn now_monotonic() -> f64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs_f64())
        .unwrap_or(0.0)
}

impl Liveness {
    pub fn new(cpu_reader: Box<dyn Fn() -> f64>, stall_timeout: f64, busy_timeout: f64) -> Self {
        let t = now_monotonic();
        let cpu0 = cpu_reader();
        Liveness {
            cpu_reader,
            stall_timeout,
            busy_timeout,
            last_data: t,
            cpu_at_data: cpu0,
            cpu_sampled: cpu0,
            sample_at: t,
            last_silent: 0.0,
            last_cpu_delta: 0.0,
            busy: false,
        }
    }

    
    
    pub fn note_data(&mut self) {
        let t = now_monotonic();
        self.last_data = t;
        self.sample(t);
        self.cpu_at_data = self.cpu_sampled;
    }

    
    
    
    fn sample(&mut self, t: f64) {
        if t - self.sample_at < CPU_SAMPLE_INTERVAL {
            return;
        }
        self.cpu_sampled = (self.cpu_reader)();
        self.sample_at = t;
        let silent = t - self.last_data;
        let used = self.cpu_sampled - self.cpu_at_data;
        self.last_cpu_delta = used;
        self.busy = used > CPU_BUSY_FLOOR.max(CPU_BUSY_RATIO * silent);
    }

    
    pub fn verdict(&mut self) {
        let t = now_monotonic();
        self.last_silent = t - self.last_data;
        self.sample(t);
    }

    
    
    pub fn stalled(&self) -> bool {
        if self.busy {
            self.last_silent > self.busy_timeout
        } else {
            self.last_silent > self.stall_timeout
        }
    }
}
