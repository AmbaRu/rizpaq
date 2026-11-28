
use crate::engine;
use std::path::{Path, PathBuf};

pub const DEFAULT_POLICY: &str = "7d4w12my";

pub fn valid_policy(policy: &str) -> bool {
    let p = policy.trim();
    !p.is_empty()
        && p.len() <= 64
        && p.chars().all(|c| {
            c.is_ascii_alphanumeric() || matches!(c, ',' | ':' | '-' | ' ')
        })
}

pub fn preview_cmd(zpaq: &str, arc: &str, policy: &str,
                   password: Option<&str>) -> Vec<String> {
    let mut cmd = vec![
        zpaq.to_string(), "repack".to_string(), arc.to_string(),
        policy.trim().to_string(), "-test".to_string(),
    ];
    if let Some(pw) = password {
        if !pw.is_empty() {
            cmd.push("-key".to_string());
            cmd.push(pw.to_string());
        }
    }
    cmd
}

pub fn apply_cmd(zpaq: &str, arc: &str, policy: &str, temp: &str,
                 password: Option<&str>) -> Vec<String> {
    let mut cmd = vec![
        zpaq.to_string(), "repack".to_string(), arc.to_string(),
        policy.trim().to_string(), "-to".to_string(), temp.to_string(),
    ];
    if let Some(pw) = password {
        if !pw.is_empty() {
            cmd.push("-key".to_string());
            cmd.push(pw.to_string());
        }
    }
    cmd
}

pub fn verify_cmd(zpaq: &str, temp: &str, password: Option<&str>) -> Vec<String> {
    let mut cmd = vec![zpaq.to_string(), "i".to_string(), temp.to_string()];
    if let Some(pw) = password {
        if !pw.is_empty() {
            cmd.push("-key".to_string());
            cmd.push(pw.to_string());
        }
    }
    cmd
}

fn reserve_temp(arc: &str) -> Option<PathBuf> {
    let path = Path::new(arc);
    let folder = path.parent().unwrap_or_else(|| Path::new("."));
    let stem = path.file_stem().and_then(|s| s.to_str()).unwrap_or("archive");
    let stamp = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_nanos())
        .unwrap_or(0);
    for attempt in 0..100u32 {
        let candidate = folder.join(format!(
            ".rizpaq_retention_{}_{}_{:x}.zpaq",
            stem,
            std::process::id(),
            stamp + attempt as u128
        ));
        match std::fs::OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&candidate)
        {
            Ok(_) => {
                let _ = std::fs::remove_file(&candidate);
                return Some(candidate);
            }
            Err(e) if e.kind() == std::io::ErrorKind::AlreadyExists => continue,
            Err(_) => return None,
        }
    }
    None
}

pub fn run_apply(zpaq: &str, arc: &str, policy: &str,
                 password: Option<&str>) -> (bool, String) {
    if !valid_policy(policy) {
        return (false, format!("[retention] invalid policy: {}", policy));
    }
    if arc.contains('?') {
        return (false, "[retention] multipart archives are not supported".into());
    }
    if crate::cmdline::is_backup_set(arc) {
        return (
            false,
            "[retention] backup sets are not supported: merge the set with `m` first"
                .into(),
        );
    }
    let Some(temp) = reserve_temp(arc) else {
        return (false, "[retention] cannot reserve temporary file".into());
    };
    let temp_s = temp.to_string_lossy().into_owned();
    let mut notes = Vec::new();

    let (rc, out) = engine::run_engine(&apply_cmd(
        zpaq, arc, policy, &temp_s, password,
    ));
    notes.push(format!("[retention] repack rc={}\n{}", rc, out.trim()));
    if rc != 0 || !temp.is_file() {
        let _ = std::fs::remove_file(&temp);
        return (false, notes.join("\n"));
    }

    let (rc, out) = engine::run_engine(&verify_cmd(zpaq, &temp_s, password));
    notes.push(format!("[retention] verify rc={}\n{}", rc, out.trim()));
    if rc != 0 {
        let _ = std::fs::remove_file(&temp);
        return (false, notes.join("\n"));
    }

    match std::fs::rename(&temp, arc) {
        Ok(()) => {
            notes.push("[retention] archive replaced".to_string());
            (true, notes.join("\n"))
        }
        Err(e) => {
            let _ = std::fs::remove_file(&temp);
            notes.push(format!("[retention] replace failed: {}", e));
            (false, notes.join("\n"))
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rename_replaces_existing_archive() {
        let dir = std::env::temp_dir().join(format!(
            "rizpaq_retention_rename_{}", std::process::id()
        ));
        let _ = std::fs::create_dir_all(&dir);
        let arc = dir.join("a.zpaq");
        let temp = dir.join("t.zpaq");
        std::fs::write(&arc, b"old").unwrap();
        std::fs::write(&temp, b"new").unwrap();
        std::fs::rename(&temp, &arc).unwrap();
        assert_eq!(std::fs::read(&arc).unwrap(), b"new");
        let _ = std::fs::remove_dir_all(&dir);
    }

    #[test]
    fn builds_commands_and_validates_policy() {
        assert!(valid_policy("7d4w12my"));
        assert!(valid_policy("10last"));
        assert!(!valid_policy("a; rm"));
        let p = preview_cmd("zpaq", "F:/a.zpaq", "1d1w", Some("pw"));
        assert_eq!(p[1], "repack");
        assert_eq!(p.last().map(String::as_str), Some("pw"));
        let a = apply_cmd("zpaq", "F:/a.zpaq", "1d1w", "F:/t.zpaq", None);
        assert!(a.contains(&"-to".to_string()));
    }
}
