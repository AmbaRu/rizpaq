









use base64::Engine as _;
use serde_json::{json, Map, Value};
use std::path::{Path, PathBuf};


pub const STORE_NAME: &str = "archive_passwords.json";

const CORRUPT_SUFFIX: &str = ".corrupt";

const TMP_PREFIX: &str = ".rizpaq_pw_";
const TMP_SUFFIX: &str = ".tmp";


fn store_dir() -> Option<PathBuf> {
    crate::cfg::config_path()?.parent().map(|d| d.to_path_buf())
}

fn store_path() -> Option<PathBuf> {
    store_dir().map(|d| d.join(STORE_NAME))
}




fn norm_key(archive_path: &str) -> String {
    let s = archive_path.replace('/', "\\").to_lowercase();
    
    let is_abs = s.starts_with('\\')
        || (s.len() >= 2 && s.as_bytes()[1] == b':');
    let s = if is_abs {
        s
    } else {
        let cwd = std::env::current_dir()
            .map(|c| c.to_string_lossy().replace('/', "\\").to_lowercase())
            .unwrap_or_default();
        if cwd.ends_with('\\') {
            format!("{}{}", cwd, s)
        } else {
            format!("{}\\{}", cwd, s)
        }
    };
    normpath(&s)
}



fn normpath(s: &str) -> String {
    
    let (prefix, rest, rooted): (String, &str, bool) = if s.len() >= 2 && s.as_bytes()[1] == b':' {
        (s[..2].to_string(), &s[2..], true)
    } else if s.starts_with("\\\\") {
        let after = &s[2..];
        match after.find('\\') {
            Some(p1) => match after[p1 + 1..].find('\\') {
                Some(p2) => (
                    s[..2 + p1 + 1 + p2].to_string(),
                    &after[p1 + 1 + p2..], 
                    true,
                ),
                None => (s.to_string(), "", true),
            },
            None => (s.to_string(), "", true),
        }
    } else {
        (String::new(), &s[..], s.starts_with('\\'))
    };

    let mut comps: Vec<&str> = Vec::new();
    for part in rest.split('\\') {
        if part.is_empty() || part == "." {
            continue;
        }
        if part == ".." {
            match comps.last() {
                Some(&"..") => comps.push(".."),
                Some(_) => {
                    comps.pop();
                }
                None => {
                    if !rooted {
                        comps.push("..");
                    }
                    
                }
            }
            continue;
        }
        comps.push(part);
    }

    if prefix.is_empty() {
        if comps.is_empty() {
            return if rooted { "\\".to_string() } else { ".".to_string() };
        }
        if rooted {
            return format!("\\{}", comps.join("\\"));
        }
        return comps.join("\\");
    }
    if prefix.ends_with(':') {
        format!("{}\\{}", prefix, comps.join("\\"))
    } else if comps.is_empty() {
        prefix
    } else {
        format!("{}\\{}", prefix, comps.join("\\"))
    }
}



fn report(message: &str) {
    crate::cfg::write_error_log_named(message, "password_store.log");
}




fn migrate_legacy(target: &Path) -> Option<String> {
    if target.is_file() {
        return None; 
    }
    let home = std::env::var("USERPROFILE").ok()?;
    let legacy = PathBuf::from(home)
        .join(".rizpaq")
        .join(STORE_NAME);
    if !legacy.is_file() {
        return None;
    }
    match std::fs::copy(&legacy, target) {
        Ok(_) => Some(format!(
            "перенесено: {} -> {}",
            legacy.display(),
            target.display()
        )),
        Err(e) => Some(format!(
            "не удалось перенести хранилище паролей из {} в {}: OSError: {}",
            legacy.display(),
            target.display(),
            e
        )),
    }
}



fn load(path: &Path) -> (Value, Option<String>) {
    
    if let Some(note) = migrate_legacy(path) {
        if let Some(rest) = note.strip_prefix("перенесено") {
            let _ = rest;
            report(&note);
        } else {
            return (json!({}), Some(note));
        }
    }

    if !path.is_file() {
        return (json!({}), None);
    }
    let text = match std::fs::read_to_string(path) {
        Ok(t) => t,
        Err(e) => {
            return (
                json!({}),
                Some(format!("файл паролей не читается: {} ({})", path.display(), e)),
            )
        }
    };
    if text.trim().is_empty() {
        return (json!({}), None);
    }
    let data: Value = match serde_json::from_str(&text) {
        Ok(v) => v,
        Err(e) => {
            let name = path
                .file_name()
                .map(|n| n.to_string_lossy().into_owned())
                .unwrap_or_default();
            return (
                json!({}),
                Some(format!(
                    "файл паролей повреждён и не будет прочитан: {} ({}). \
При следующем сохранении он будет отодвинут в {}{}.",
                    path.display(),
                    e,
                    name,
                    CORRUPT_SUFFIX
                )),
            );
        }
    };
    if !data.is_object() {
        let name = path
            .file_name()
            .map(|n| n.to_string_lossy().into_owned())
            .unwrap_or_default();
        return (
            json!({}),
            Some(format!(
                "файл паролей имеет неожиданный вид и не будет прочитан: {}. \
При следующем сохранении он будет отодвинут в {}{}.",
                path.display(),
                name,
                CORRUPT_SUFFIX
            )),
        );
    }
    (data, None)
}



fn quarantine(path: &Path) {
    let corrupt = PathBuf::from(format!("{}{}", path.display(), CORRUPT_SUFFIX));
    if std::fs::rename(path, &corrupt).is_ok() {
        return;
    }
    
    
    let copied = std::fs::copy(path, &corrupt).is_ok();
    report(&format!(
        "не удалось отодвинуть испорченный файл паролей; \
предыдущее содержимое сохранено в {} только если копирование прошло успешно{}",
        corrupt.display(),
        if copied { "" } else { " (копирование не удалось)" }
    ));
}




fn atomic_write(path: &Path, data: &Value) -> Option<String> {
    let parent = path.parent().unwrap_or(Path::new("."));
    if let Err(e) = std::fs::create_dir_all(parent) {
        return Some(format!(
            "не удалось сохранить пароль в {}: OSError: {}",
            path.display(),
            e
        ));
    }
    
    let nanos = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_nanos())
        .unwrap_or(0);
    let mut tmp: Option<PathBuf> = None;
    for attempt in 0..100u32 {
        let candidate = parent.join(format!(
            "{}{}_{:x}{}",
            TMP_PREFIX,
            std::process::id(),
            nanos + attempt as u128,
            TMP_SUFFIX
        ));
        match std::fs::OpenOptions::new()
            .create_new(true)
            .write(true)
            .open(&candidate)
        {
            Ok(_) => {
                tmp = Some(candidate);
                break;
            }
            Err(e) if e.kind() == std::io::ErrorKind::AlreadyExists => continue,
            Err(e) => {
                return Some(format!(
                    "не удалось сохранить пароль в {}: OSError: {}",
                    path.display(),
                    e
                ))
            }
        }
    }
    let tmp = match tmp {
        Some(t) => t,
        None => {
            return Some(format!(
                "не удалось сохранить пароль в {}: OSError: no temp name",
                path.display()
            ))
        }
    };

    let body = match serde_json::to_string_pretty(data) {
        Ok(s) => format!("{}\n", s),
        Err(e) => {
            let _ = std::fs::remove_file(&tmp);
            return Some(format!(
                "не удалось сохранить пароль в {}: ValueError: {}",
                path.display(),
                e
            ));
        }
    };
    let failed = (|| -> std::io::Result<()> {
        let mut f = std::fs::OpenOptions::new().write(true).open(&tmp)?;
        use std::io::Write;
        f.write_all(body.as_bytes())?;
        
        
        
        f.sync_all().ok();
        drop(f);
        std::fs::rename(&tmp, path)
    })();
    match failed {
        Ok(()) => None,
        Err(e) => {
            let _ = std::fs::remove_file(&tmp);
            Some(format!(
                "не удалось сохранить пароль в {}: OSError: {}",
                path.display(),
                e
            ))
        }
    }
}




pub fn set_password(archive_path: &str, password: Option<&str>) {
    let Some(path) = store_path() else {
        report("не удалось определить путь хранилища");
        return;
    };

    let (mut data, problem) = load(&path);
    if let Some(p) = problem {
        
        
        
        report(&p);
        if path.is_file() {
            quarantine(&path);
        }
        data = json!({});
    }

    let key = norm_key(archive_path);
    let mut fallback = Map::new();
    let obj = data.as_object_mut().unwrap_or(&mut fallback);
    match password {
        Some(p) if !p.is_empty() => {
            let encoded = base64::engine::general_purpose::STANDARD.encode(p.as_bytes());
            obj.insert(key, json!(encoded));
        }
        _ => {
            obj.remove(&key);
        }
    }

    if let Some(err) = atomic_write(&path, &data) {
        report(&err);
    }
}
