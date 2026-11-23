
use crate::{engine, index, util};
use std::path::{Path, PathBuf};

const MAX_DRILL_SIZE: i64 = 64 << 20;

#[derive(Clone)]
struct Candidate {
    path: String,
    size: i64,
    version: String,
}

fn parse_listing(text: &str) -> Vec<Candidate> {
    let mut out = Vec::new();
    for line in text.lines() {
        let parts: Vec<&str> = line.split('\t').collect();
        if parts.len() < 6 {
            continue;
        }
        let (size_s, version, flag, path, ratio, attr) = if parts.len() >= 7 {
            (parts[2], parts[4].to_string(), parts[5], parts[6], parts[3], parts[1])
        } else {
            (parts[2], String::new(), parts[4], parts[5], parts[3], parts[1])
        };
        let size: i64 = size_s.trim().parse().unwrap_or(0);
        let path = path.trim().trim_end_matches('#').to_string();
        let attr = attr.trim().to_uppercase();
        let ratio = ratio.trim().to_lowercase();
        if path.is_empty()
            || attr.starts_with('D')
            || ratio == "dir"
            || path.ends_with('/')
            || flag.trim() == "-"
            || size <= 0
            || size > MAX_DRILL_SIZE
        {
            continue;
        }
        out.push(Candidate { path, size, version });
    }
    out
}

fn find_extracted(dir: &Path) -> Option<PathBuf> {
    let entries = std::fs::read_dir(dir).ok()?;
    for entry in entries.flatten() {
        let p = entry.path();
        if p.is_dir() {
            if let Some(found) = find_extracted(&p) {
                return Some(found);
            }
        } else if p.is_file() {
            return Some(p);
        }
    }
    None
}

fn extract_cmd(
    zpaq: &str,
    dest: &str,
    password: Option<&str>,
    entry: &Candidate,
    target: &Path,
) -> Vec<String> {
    let mut cmd = vec![
        zpaq.to_string(),
        "x".to_string(),
        dest.to_string(),
    ];
    if let Some(pw) = password {
        if !pw.is_empty() {
            cmd.push("-key".to_string());
            cmd.push(pw.to_string());
        }
    }
    cmd.push(entry.path.clone());
    if !entry.version.is_empty() {
        cmd.push("-until".to_string());
        cmd.push(entry.version.clone());
    }
    cmd.push("-to".to_string());
    let mut target = target.to_string_lossy().into_owned();
    if !target.ends_with(['/', '\\']) {
        target.push(std::path::MAIN_SEPARATOR);
    }
    cmd.push(target);
    cmd
}

pub fn run_restore_drill(
    zpaq: &str,
    dest: &str,
    password: Option<&str>,
    sources: &[String],
) -> (bool, String) {
    let list_cmd = index::build_list_cmd(zpaq, dest, password);
    let (rc, listing) = engine::run_engine(&list_cmd);
    if rc != 0 {
        return (false, format!("[restore] cannot read listing: {}", listing));
    }
    let candidates = parse_listing(&listing);
    if candidates.is_empty() {
        return (true, "[restore] no suitable files to test".to_string());
    }
    let latest = candidates
        .iter()
        .map(|c| c.version.parse::<u64>().unwrap_or(0))
        .max()
        .unwrap_or(0);
    let candidates: Vec<Candidate> = candidates
        .into_iter()
        .filter(|c| c.version.parse::<u64>().unwrap_or(0) == latest)
        .collect();
    let pick = (std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0) as usize)
        % candidates.len();
    let entry = candidates[pick].clone();

    let Some(first_dir) = util::make_tmp_dir("rizpaq_restore_") else {
        return (false, "[restore] cannot create temp folder".to_string());
    };
    let cmd = extract_cmd(zpaq, dest, password, &entry, &first_dir);
    let (rc, out) = engine::run_engine(&cmd);
    if rc != 0 {
        let _ = std::fs::remove_dir_all(&first_dir);
        return (false, format!("[restore] cannot extract {}:\n{}", entry.path, out));
    }
    let Some(restored) = find_extracted(&first_dir) else {
        let _ = std::fs::remove_dir_all(&first_dir);
        return (false, format!("[restore] extracted file not found: {}", entry.path));
    };
    let restored_bytes = std::fs::read(&restored).ok();

    let mut expected: Option<Vec<u8>> = None;
    let mut how = "second extraction".to_string();
    for source in sources {
        let candidate = Path::new(source).join(&entry.path);
        if candidate.is_file() {
            expected = std::fs::read(&candidate).ok();
            how = format!("source {}", candidate.display());
            break;
        }
    }
    let mut second_dir: Option<PathBuf> = None;
    if expected.is_none() {
        if let Some(dir) = util::make_tmp_dir("rizpaq_restore2_") {
            let cmd2 = extract_cmd(zpaq, dest, password, &entry, &dir);
            let (rc2, _) = engine::run_engine(&cmd2);
            if rc2 == 0 {
                if let Some(other) = find_extracted(&dir) {
                    expected = std::fs::read(other).ok();
                }
            }
            second_dir = Some(dir);
        }
    }

    let ok = expected.is_some()
        && restored_bytes.is_some()
        && expected == restored_bytes;

    if let Some(dir) = second_dir {
        let _ = std::fs::remove_dir_all(dir);
    }
    let _ = std::fs::remove_dir_all(&first_dir);

    let log = format!(
        "[restore] file: {} ({} bytes, version {})\n[restore] compare: {}\n[restore] verdict: {}",
        entry.path,
        entry.size,
        if entry.version.is_empty() { "-" } else { &entry.version },
        how,
        if ok { "OK" } else { "MISMATCH" },
    );
    (ok, log)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn extract_cmd_targets_a_folder() {
        let entry = Candidate {
            path: "dir/file.txt".to_string(),
            size: 10,
            version: "2".to_string(),
        };
        let target = Path::new("D:/tmp");
        let cmd = extract_cmd("zpaq", "F:/a.zpaq", None, &entry, target);
        assert_eq!(cmd[cmd.len() - 1], format!("D:/tmp{}", std::path::MAIN_SEPARATOR));
        let with_sep = Path::new("D:/tmp/");
        let cmd2 = extract_cmd("zpaq", "F:/a.zpaq", None, &entry, with_sep);
        assert_eq!(cmd2[cmd2.len() - 1], "D:/tmp/");
    }

    #[test]
    fn parses_csv_listing_and_filters() {
        let text = "2026-01-01 00:00:00\tA\t100\t1,0\t2\t+\tdir/file.txt\n\
                    2026-01-01 00:00:00\tD\t0\tdir\t2\t+\tfolder/\n\
                    2026-01-01 00:00:00\tA\t0\t1,0\t2\t+\tempty.txt\n\
                    2026-01-01 00:00:00\tA\t10\t1,0\t3\t-\tdeleted.txt\n";
        let found = parse_listing(text);
        assert_eq!(found.len(), 1);
        assert_eq!(found[0].path, "dir/file.txt");
        assert_eq!(found[0].version, "2");
        let marked =
            "#2026-01-01 00:00:00\tA\t100\t1,0\t2\t+\tdir/file.txt#\n";
        assert_eq!(parse_listing(marked)[0].path, "dir/file.txt");
    }
}
