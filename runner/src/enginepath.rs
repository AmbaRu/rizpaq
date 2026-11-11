
use std::ffi::OsStr;
use std::os::windows::ffi::OsStrExt;
use std::path::Path;

pub const READ_ONLY_SUBCOMMANDS: &[&str] = &["l", "t", "e", "x", "v"];

pub struct EnginePathError(pub String);

pub fn has_non_latin(text: &str) -> bool {
    text.chars().any(|c| !c.is_ascii())
}

pub fn short_path(long_path: &str) -> String {
    #[link(name = "kernel32")]
    extern "system" {
        fn GetShortPathNameW(
            lpLongPath: *const u16,
            lpBuffer: *mut u16,
            cchBuffer: u32,
        ) -> u32;
    }
    let wide: Vec<u16> = OsStr::new(long_path)
        .encode_wide()
        .chain(std::iter::once(0))
        .collect();
    let mut buf = vec![0u16; 4096];
    let n = unsafe { GetShortPathNameW(wide.as_ptr(), buf.as_mut_ptr(), 4096) };
    if n == 0 || n as usize > buf.len() {
        return String::new();
    }
    String::from_utf16_lossy(&buf[..n as usize])
}

pub fn is_zpaq_cmd(cmd: &[String]) -> bool {
    match cmd.first() {
        Some(exe) => Path::new(exe)
            .file_name()
            .and_then(|s| s.to_str())
            .map(|s| s.to_lowercase().contains("zpaq"))
            .unwrap_or(false),
        None => false,
    }
}

pub fn subcommand_of(cmd: &[String]) -> String {
    for arg in cmd.iter().skip(1) {
        if !arg.starts_with('-') {
            return arg.to_lowercase();
        }
    }
    String::new()
}

pub fn archive_index(cmd: &[String]) -> i64 {
    let mut seen_sub = false;
    for (i, arg) in cmd.iter().enumerate().skip(1) {
        if arg.starts_with('-') {
            continue;
        }
        if !seen_sub {
            seen_sub = true;
            continue;
        }
        return i as i64;
    }
    -1
}

fn latin_substitute(path: &str) -> Result<(String, Option<String>), EnginePathError> {
    let folder = crate::util::make_tmp_dir("rizpaq_link_").ok_or_else(|| {
        EnginePathError(
            "не удалось приготовить временную папку для чтения архива".to_string(),
        )
    })?;
    let src = Path::new(path);
    let stem = src.file_stem().and_then(|s| s.to_str()).unwrap_or("");
    let ascii_stem: String = stem
        .chars()
        .filter(|c| c.is_ascii() && c.is_ascii_alphanumeric())
        .collect();
    let ascii_stem = if ascii_stem.is_empty() {
        "archive".to_string()
    } else {
        ascii_stem
    };
    let tmp = folder.join(format!("{}.zpaq", ascii_stem));

    if std::fs::hard_link(src, &tmp).is_ok() {
        return Ok((tmp.to_string_lossy().into_owned(), None));
    }
    match std::fs::copy(src, &tmp) {
        Ok(_) => Ok((tmp.to_string_lossy().into_owned(), None)),
        Err(exc) => {
            let _ = std::fs::remove_dir_all(&folder);
            Err(EnginePathError(format!(
                "не удалось прочитать архив с нелатинским именем: движок не \
понимает такой путь, короткие имена на диске отключены, а жёсткая \
ссылка и копия не получились ({}). Переименуйте файл или перенесите \
его в папку на диске, где короткие имена разрешены: {}",
                exc, path
            )))
        }
    }
}

pub fn read_target(path: &str) -> Result<(String, Option<String>, Vec<String>), EnginePathError> {
    if !has_non_latin(path) {
        return Ok((path.to_string(), None, vec![]));
    }
    let short = short_path(path);
    if !short.is_empty() && !has_non_latin(&short) {
        return Ok((short, None, vec![]));
    }
    let p = Path::new(path);
    let name = p.file_name().and_then(|s| s.to_str()).unwrap_or("");
    let folder = p.parent().map(|s| s.to_string_lossy().into_owned());
    if !has_non_latin(name) && folder.as_deref().map(|f| !f.is_empty()).unwrap_or(false) {
        return Ok((name.to_string(), folder, vec![]));
    }
    let (arg, cwd) = latin_substitute(path)?;
    let subs = vec![arg.clone()];
    Ok((arg, cwd, subs))
}

pub fn create_target(path: &str) -> Result<(String, Option<String>, Vec<String>), EnginePathError> {
    if !has_non_latin(path) {
        return Ok((path.to_string(), None, vec![]));
    }
    if Path::new(path).is_file() {
        return read_target(path);
    }
    let p = Path::new(path);
    let folder = p.parent().map(|s| s.to_string_lossy().into_owned()).unwrap_or_default();
    if !folder.is_empty() && has_non_latin(&folder) {
        let name = p.file_name().and_then(|s| s.to_str()).unwrap_or("");
        return Ok((name.to_string(), Some(folder), vec![]));
    }
    Ok((path.to_string(), None, vec![]))
}

pub fn rewrite_cmd(cmd: &[String]) -> Result<(Vec<String>, Option<String>, Vec<String>), EnginePathError> {
    if !is_zpaq_cmd(cmd) {
        return Ok((cmd.to_vec(), None, vec![]));
    }
    let idx = archive_index(cmd);
    if idx < 0 || idx as usize >= cmd.len() {
        return Ok((cmd.to_vec(), None, vec![]));
    }
    let raw = &cmd[idx as usize];
    if !has_non_latin(raw) {
        return Ok((cmd.to_vec(), None, vec![]));
    }

    let sub = subcommand_of(cmd);
    let (new_arg, new_cwd, subs) = if Path::new(raw).is_file() {
        if !READ_ONLY_SUBCOMMANDS.contains(&sub.as_str()) {
            let short = short_path(raw);
            let name = Path::new(raw)
                .file_name()
                .and_then(|s| s.to_str())
                .unwrap_or("")
                .to_string();
            let folder = Path::new(raw)
                .parent()
                .map(|s| s.to_string_lossy().into_owned())
                .unwrap_or_default();
            if !short.is_empty() && !has_non_latin(&short) {
                (short, None, vec![])
            } else if !has_non_latin(&name) && !folder.is_empty() {
                (name, Some(folder), vec![])
            } else {
                return Err(EnginePathError(format!(
                    "движок не умеет работать с архивом, имя которого \
нелатинское, и пишет в него, а не только читает: {}. Копию подставить \
нельзя — добавленное ушло бы в копию, а настоящий архив остался бы \
прежним. Переименуйте файл или перенесите его в папку на диске, где \
короткие имена разрешены.",
                    raw
                )));
            }
        } else {
            read_target(raw)?
        }
    } else {
        create_target(raw)?
    };

    let mut out = cmd.to_vec();
    out[idx as usize] = new_arg;
    Ok((out, new_cwd, subs))
}

pub fn drop_substitutes(paths: &[String]) {
    for p in paths {
        let path = Path::new(p);
        if path.is_file() {
            let _ = std::fs::remove_file(path);
        }
        if let Some(parent) = path.parent() {
            let base = parent.file_name().and_then(|s| s.to_str()).unwrap_or("");
            if base.starts_with("rizpaq_link_") {
                let _ = std::fs::remove_dir_all(parent);
            }
        }
    }
}
