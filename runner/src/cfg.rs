
use serde_json::Value;
use std::path::{Path, PathBuf};

pub const CONFIG_NAME: &str = "zpaq_gui.json";
pub const APP_DIR_NAME: &str = "Rizpaq";
const STALL_MIN_S: f64 = 5.0;
const STALL_MAX_S: f64 = 3600.0;
const LOG_MAX_BYTES: u64 = 256 * 1024;
const LOG_KEEP_BYTES: usize = 64 * 1024;

pub fn config_path() -> Option<PathBuf> {
    if let Ok(p) = std::env::var("ZPAQ_GUI_CONFIG") {
        if !p.is_empty() {
            return Some(PathBuf::from(p));
        }
    }
    if let Ok(exe) = std::env::current_exe() {
        if let Some(dir) = exe.parent() {
            for marker in ["portable.txt", "portable"] {
                if dir.join(marker).exists() {
                    return Some(dir.join(CONFIG_NAME));
                }
            }
        }
    }
    let base = match std::env::var("APPDATA") {
        Ok(a) if !a.is_empty() => PathBuf::from(a),
        _ => {
            let home = std::env::var("USERPROFILE").ok()?;
            PathBuf::from(home).join("AppData").join("Roaming")
        }
    };
    Some(base.join(APP_DIR_NAME).join(CONFIG_NAME))
}

fn load_config() -> Option<Value> {
    let text = std::fs::read_to_string(config_path()?).ok()?;
    serde_json::from_str(&text).ok()
}

pub struct NotifyConfig {
    pub mode: String,
    pub token: String,
    pub chat_id: String,
    pub language: String,
}

pub fn notify_config() -> Option<NotifyConfig> {
    let v = load_config()?;
    let mode = v
        .get("notify_mode")
        .and_then(Value::as_str)
        .unwrap_or("off")
        .trim()
        .to_lowercase();
    let mode = match mode.as_str() {
        "errors" | "all" => mode,
        _ => "off".to_string(),
    };
    let language = v
        .get("language")
        .and_then(Value::as_str)
        .unwrap_or("en")
        .trim()
        .to_string();
    let language = if language.is_empty() {
        "en".to_string()
    } else {
        language
    };
    Some(NotifyConfig {
        mode,
        token: v
            .get("notify_telegram_token")
            .and_then(Value::as_str)
            .unwrap_or("")
            .trim()
            .to_string(),
        chat_id: v
            .get("notify_telegram_chat_id")
            .and_then(Value::as_str)
            .unwrap_or("")
            .trim()
            .to_string(),
        language,
    })
}

pub fn config_zpaq_path() -> Option<PathBuf> {
    let v = load_config()?;
    let s = v.get("zpaq_path")?.as_str()?.trim().to_string();
    if s.is_empty() {
        None
    } else {
        Some(PathBuf::from(s))
    }
}

pub fn engine_stall_timeout(default: f64) -> f64 {
    let Some(v) = load_config() else { return default };
    let Some(raw) = v.get("engine_stall_timeout") else { return default };
    let Some(i) = raw.as_i64() else { return default };
    let f = i as f64;
    f.min(STALL_MAX_S).max(STALL_MIN_S)
}

fn log_candidates(name: &str) -> Vec<PathBuf> {
    let mut out: Vec<PathBuf> = Vec::new();
    if let Some(cp) = config_path() {
        if let Some(parent) = cp.parent() {
            out.push(parent.join(name));
        }
    }
    for var in ["LOCALAPPDATA", "APPDATA"] {
        if let Ok(value) = std::env::var(var) {
            if !value.is_empty() {
                out.push(PathBuf::from(value).join(APP_DIR_NAME).join(name));
            }
        }
    }
    for var in ["TEMP", "TMP"] {
        if let Ok(value) = std::env::var(var) {
            if !value.is_empty() {
                out.push(PathBuf::from(value).join(name));
            }
        }
    }
    if let Ok(cwd) = std::env::current_dir() {
        out.push(cwd.join(name));
    }
    let mut seen = std::collections::HashSet::new();
    out.into_iter().filter(|p| seen.insert(p.clone())).collect()
}

pub fn write_error_log_named(text: &str, name: &str) {
    if text.is_empty() {
        return;
    }
    let header = format!(
        "--- Rizpaq error {} ---",
        chrono::Local::now().format("%Y-%m-%dT%H:%M:%S")
    );
    let mut body = format!("{}\n{}", header, text);
    if !body.ends_with('\n') {
        body.push('\n');
    }
    for path in log_candidates(name) {
        let trimmed = trim_log(&path);
        let ok = std::fs::create_dir_all(path.parent().unwrap_or(Path::new(".")))
            .is_ok()
            && match trimmed {
                Some(prev) => std::fs::write(
                    &path,
                    format!("... (предыдущая запись обрезана) ...\n{}{}", prev, body),
                )
                .is_ok(),
                None => {
                    use std::io::Write;
                    std::fs::OpenOptions::new()
                        .create(true)
                        .append(true)
                        .open(&path)
                        .and_then(|mut f| f.write_all(body.as_bytes()))
                        .is_ok()
                }
            };
        if ok {
            return;
        }
    }
}

fn trim_log(path: &Path) -> Option<String> {
    let size = std::fs::metadata(path).ok()?.len();
    if size <= LOG_MAX_BYTES {
        return None;
    }
    let data = std::fs::read(path).ok()?;
    let start = data.len().saturating_sub(LOG_KEEP_BYTES);
    let mut tail = &data[start..];
    if let Some(pos) = tail.iter().position(|b| *b == b'\n') {
        tail = &tail[pos + 1..];
    }
    Some(String::from_utf8_lossy(tail).into_owned())
}
