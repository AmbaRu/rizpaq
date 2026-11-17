
use std::fs::{self, File};
use std::io::Read;
use std::path::{Path, PathBuf};

pub const COMPARE_CHUNK: usize = 1024 * 1024;

pub const PART_SUFFIX: &str = ".rizpaq-part";

fn chars_equal(a: char, b: char) -> bool {
    if cfg!(windows) {
        a.to_lowercase().eq(b.to_lowercase())
    } else {
        a == b
    }
}

pub fn glob_match(pattern: &str, name: &str) -> bool {
    let pat: Vec<char> = pattern.chars().collect();
    let text: Vec<char> = name.chars().collect();
    fn walk(pat: &[char], text: &[char]) -> bool {
        match pat.first() {
            None => text.is_empty(),
            Some('*') => {
                walk(&pat[1..], text)
                    || (!text.is_empty() && walk(pat, &text[1..]))
            }
            Some('?') => {
                !text.is_empty() && walk(&pat[1..], &text[1..])
            }
            Some(ch) => {
                !text.is_empty()
                    && chars_equal(*ch, text[0])
                    && walk(&pat[1..], &text[1..])
            }
        }
    }
    walk(&pat, &text)
}

pub fn copy_sources(dest: &str) -> Vec<PathBuf> {
    let path = Path::new(dest);
    let name = match path.file_name().and_then(|s| s.to_str()) {
        Some(n) if !n.is_empty() => n,
        _ => return Vec::new(),
    };
    if name.contains('?') || name.contains('*') {
        let parent = match path.parent() {
            Some(p) if !p.as_os_str().is_empty() => p,
            _ => Path::new("."),
        };
        let mut found: Vec<PathBuf> = Vec::new();
        if let Ok(entries) = fs::read_dir(parent) {
            for entry in entries.flatten() {
                let candidate = entry.path();
                if !candidate.is_file() {
                    continue;
                }
                let fname = match candidate.file_name().and_then(|s| s.to_str()) {
                    Some(f) => f,
                    None => continue,
                };
                if glob_match(name, fname) {
                    found.push(candidate);
                }
            }
        }
        found.sort();
        return found;
    }
    if path.is_file() {
        vec![path.to_path_buf()]
    } else {
        Vec::new()
    }
}

pub fn files_equal(first: &Path, second: &Path) -> bool {
    let (meta_a, meta_b) = match (fs::metadata(first), fs::metadata(second)) {
        (Ok(a), Ok(b)) => (a, b),
        _ => return false,
    };
    if meta_a.len() != meta_b.len() {
        return false;
    }
    let (mut a, mut b) = match (File::open(first), File::open(second)) {
        (Ok(a), Ok(b)) => (a, b),
        _ => return false,
    };
    let mut buf_a = vec![0u8; COMPARE_CHUNK];
    let mut buf_b = vec![0u8; COMPARE_CHUNK];
    loop {
        let read_a = match a.read(&mut buf_a) {
            Ok(n) => n,
            Err(_) => return false,
        };
        let read_b = match b.read(&mut buf_b) {
            Ok(n) => n,
            Err(_) => return false,
        };
        if read_a != read_b {
            return false;
        }
        if read_a == 0 {
            return true;
        }
        if buf_a[..read_a] != buf_b[..read_b] {
            return false;
        }
    }
}

fn same_file(first: &Path, second: &Path) -> bool {
    match (first.canonicalize(), second.canonicalize()) {
        (Ok(a), Ok(b)) => a == b,
        _ => false,
    }
}

pub fn copy_one(src: &Path, target_dir: &Path) -> Result<bool, String> {
    let name = match src.file_name().and_then(|s| s.to_str()) {
        Some(n) => n.to_string(),
        None => src.to_string_lossy().into_owned(),
    };
    let dst = target_dir.join(&name);
    if same_file(src, &dst) {
        return Ok(false);
    }
    let part = dst.with_file_name(format!("{}{}", name, PART_SUFFIX));
    let _ = fs::remove_file(&part);

    let copied = (|| -> std::io::Result<()> {
        fs::copy(src, &part)?;
        let handle = fs::OpenOptions::new().write(true).open(&part)?;
        handle.sync_all()?;
        if let Ok(modified) = fs::metadata(src).and_then(|m| m.modified()) {
            let times = fs::FileTimes::new().set_modified(modified);
            let _ = handle.set_times(times);
        }
        Ok(())
    })();
    if let Err(exc) = copied {
        let _ = fs::remove_file(&part);
        return Err(format!("{}: {}", name, exc));
    }
    if !files_equal(src, &part) {
        let _ = fs::remove_file(&part);
        return Err(format!("{}: copy differs from the source", name));
    }
    if let Err(exc) = fs::rename(&part, &dst) {
        let _ = fs::remove_file(&part);
        return Err(format!("{}: {}", name, exc));
    }
    Ok(true)
}

pub fn copy_archive(dest: &str, copy_dir: &str) -> (bool, String) {
    let folder = copy_dir.trim();
    if folder.is_empty() {
        return (false, "copy folder is not set".to_string());
    }
    let target_dir = Path::new(folder);
    if target_dir.exists() && !target_dir.is_dir() {
        return (
            false,
            format!("not a folder: {}", target_dir.display()),
        );
    }
    if let Err(exc) = fs::create_dir_all(target_dir) {
        return (
            false,
            format!("cannot create {}: {}", target_dir.display(), exc),
        );
    }
    if !target_dir.is_dir() {
        return (
            false,
            format!("not a folder: {}", target_dir.display()),
        );
    }

    let sources = copy_sources(dest);
    if sources.is_empty() {
        return (false, format!("archive file not found: {}", dest));
    }

    let mut errors: Vec<String> = Vec::new();
    let mut copied = 0usize;
    for src in &sources {
        match copy_one(src, target_dir) {
            Ok(true) => copied += 1,
            Ok(false) => {}
            Err(text) => errors.push(text),
        }
    }
    if !errors.is_empty() {
        return (false, errors.join("; "));
    }
    if copied == 0 {
        return (true, String::new());
    }
    (
        true,
        format!(
            "{} file(s) copied to {} and verified",
            copied,
            target_dir.display()
        ),
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    fn tmp_dir(name: &str) -> PathBuf {
        let dir = std::env::temp_dir().join(format!(
            "rizpaq_copy_{}_{}",
            name,
            std::process::id()
        ));
        let _ = fs::remove_dir_all(&dir);
        fs::create_dir_all(&dir).unwrap();
        dir
    }

    #[test]
    fn glob_question_matches_exactly_one_char() {
        assert!(glob_match("arch_????.zpaq", "arch_0001.zpaq"));
        assert!(!glob_match("arch_????.zpaq", "arch_001.zpaq"));
        assert!(!glob_match("arch_????.zpaq", "arch_00001.zpaq"));
    }

    #[test]
    fn glob_star_matches_any_tail() {
        assert!(glob_match("*.zpaq", "archive.zpaq"));
        assert!(glob_match("arch*", "arch_0001.zpaq"));
        assert!(!glob_match("*.zpaq", "archive.rzp"));
    }

    #[test]
    fn copy_archive_expands_mask_and_verifies() {
        let src_dir = tmp_dir("mask_src");
        let dst_dir = tmp_dir("mask_dst");
        fs::write(src_dir.join("arch_0001.zpaq"), b"first").unwrap();
        fs::write(src_dir.join("arch_0002.zpaq"), b"second").unwrap();
        fs::write(src_dir.join("notes.txt"), b"ignore").unwrap();
        let mask = src_dir.join("arch_????.zpaq");

        let (ok, note) = copy_archive(
            &mask.to_string_lossy(),
            &dst_dir.to_string_lossy(),
        );
        assert!(ok, "{}", note);
        assert!(note.contains("2 file(s)"));
        assert!(files_equal(
            &src_dir.join("arch_0001.zpaq"),
            &dst_dir.join("arch_0001.zpaq")
        ));
        assert!(files_equal(
            &src_dir.join("arch_0002.zpaq"),
            &dst_dir.join("arch_0002.zpaq")
        ));
        assert!(!dst_dir.join("notes.txt").exists());

        let _ = fs::remove_dir_all(&src_dir);
        let _ = fs::remove_dir_all(&dst_dir);
    }

    #[test]
    fn copy_archive_reports_missing_archive() {
        let src_dir = tmp_dir("missing_src");
        let dst_dir = tmp_dir("missing_dst");
        let (ok, note) = copy_archive(
            &src_dir.join("absent.zpaq").to_string_lossy(),
            &dst_dir.to_string_lossy(),
        );
        assert!(!ok);
        assert!(note.contains("archive file not found"));
        let _ = fs::remove_dir_all(&src_dir);
        let _ = fs::remove_dir_all(&dst_dir);
    }

    #[test]
    fn copy_archive_into_same_folder_is_not_an_error() {
        let dir = tmp_dir("same_dir");
        let archive = dir.join("arch.zpaq");
        fs::write(&archive, b"data").unwrap();
        let (ok, note) = copy_archive(
            &archive.to_string_lossy(),
            &dir.to_string_lossy(),
        );
        assert!(ok);
        assert_eq!(note, "");
        assert_eq!(fs::read(&archive).unwrap(), b"data");
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn files_equal_detects_different_content() {
        let dir = tmp_dir("equal");
        let first = dir.join("a.bin");
        let second = dir.join("b.bin");
        fs::write(&first, b"same").unwrap();
        fs::write(&second, b"same").unwrap();
        assert!(files_equal(&first, &second));
        fs::write(&second, b"diff").unwrap();
        assert!(!files_equal(&first, &second));
        let _ = fs::remove_dir_all(&dir);
    }
}
