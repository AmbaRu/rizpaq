
use std::fs::OpenOptions;
use std::io::Write;
use serde_json::Value;

const PASSWORD_VALUE_FLAGS: &[&str] = &["-key"];
const PASSWORD_INLINE_PREFIX: &str = "-p";
const MASK: &str = "***";

pub fn mask_secrets(cmd: &[String], password: Option<&str>) -> Vec<String> {
    let pw = match password {
        Some(p) if !p.is_empty() => p,
        _ => return cmd.to_vec(),
    };
    let mut masked: Vec<String> = Vec::with_capacity(cmd.len());
    let mut expect_value = false;
    for arg in cmd {
        if expect_value {
            masked.push(MASK.to_string());
            expect_value = false;
            continue;
        }
        if PASSWORD_VALUE_FLAGS.contains(&arg.as_str()) {
            masked.push(arg.clone());
            expect_value = true;
            continue;
        }
        if let Some(tail) = arg.strip_prefix(PASSWORD_INLINE_PREFIX) {
            if tail == pw {
                masked.push(format!("{}{}", PASSWORD_INLINE_PREFIX, MASK));
                continue;
            }
        }
        if arg == pw {
            masked.push(MASK.to_string());
        } else {
            masked.push(arg.clone());
        }
    }
    masked
}

pub fn list2cmdline(args: &[String]) -> String {
    let mut out = String::new();
    for arg in args {
        if !out.is_empty() {
            out.push(' ');
        }
        let needquote = arg.is_empty() || arg.contains(' ') || arg.contains('\t');
        let mut bs = 0usize;
        if needquote {
            out.push('"');
        }
        for c in arg.chars() {
            if c == '\\' {
                bs += 1;
            } else if c == '"' {
                for _ in 0..bs * 2 {
                    out.push('\\');
                }
                bs = 0;
                out.push_str("\\\"");
            } else {
                for _ in 0..bs {
                    out.push('\\');
                }
                bs = 0;
                out.push(c);
            }
        }
        if needquote {
            for _ in 0..bs * 2 {
                out.push('\\');
            }
            out.push('"');
        } else {
            for _ in 0..bs {
                out.push('\\');
            }
        }
    }
    out
}

pub fn safe_cmdline(cmd: &[String], password: Option<&str>) -> String {
    list2cmdline(&mask_secrets(cmd, password))
}

fn vstr(v: Option<&Value>) -> String {
    v.and_then(Value::as_str).unwrap_or("").to_string()
}

pub fn build_log_header(
    rzp_path: &str,
    work: &Value,
    job: &Value,
    rc: i32,
    password: Option<&str>,
    cmd: Option<&[String]>,
) -> String {
    let mut lines: Vec<String> = Vec::new();
    lines.push(format!(
        "--- Rizpaq task run {} ---",
        chrono::Local::now().format("%Y-%m-%d %H:%M:%S%.6f")
    ));
    lines.push(format!("Task file: {}", rzp_path));
    lines.push(format!("Work id:   {}", vstr(work.get("id"))));
    lines.push(format!("Work:      {}", vstr(work.get("title"))));
    lines.push(format!("Job id:    {}", vstr(job.get("id"))));
    lines.push(format!("Job:       {}", vstr(job.get("title"))));
    lines.push(format!(
        "Action:    {}",
        job.get("action").and_then(Value::as_str).unwrap_or("backup")
    ));
    if let Some(c) = cmd {
        lines.push(format!("Command:   {}", safe_cmdline(c, password)));
    }
    lines.push(format!("Return code: {}", rc));
    lines.join("\n")
}

pub fn write_task_log(
    rzp_path: &str,
    header: &str,
    log: &str,
    mode: &str,
    rc: i32,
    busy: bool,
    note: &str,
) {
    if mode == "none" {
        return;
    }
    let path = format!("{}.log", rzp_path);
    let mut buf = String::new();
    buf.push_str(header);
    buf.push('\n');
    if !note.is_empty() {
        buf.push_str(note);
        if !note.ends_with('\n') {
            buf.push('\n');
        }
    }
    if mode == "full" {
        if !log.is_empty() {
            buf.push_str(log);
        }
    } else if mode == "short" {
        if rc == 0 {
            buf.push_str("Status: OK\n");
        } else if busy {
            buf.push_str("Status: BUSY (another zpaqfranz is running)\n");
        } else {
            buf.push_str(&format!("Status: ERROR (rc={})\n", rc));
            if !log.is_empty() {
                let clean = log.replace('\r', "\n");
                let lines: Vec<&str> = clean
                    .split('\n')
                    .filter(|l| !l.trim().is_empty())
                    .collect();
                let start = lines.len().saturating_sub(10);
                buf.push_str("--- Last output lines ---\n");
                buf.push_str(&lines[start..].join("\n"));
                buf.push('\n');
            }
        }
    }
    buf.push_str(&"=".repeat(50));
    buf.push_str("\n\n");
    if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(&path) {
        let _ = f.write_all(buf.as_bytes());
    }
}
