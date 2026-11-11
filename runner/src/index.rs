
use crate::cfg;
use crate::engine;
use rusqlite::params;
use serde_json::Value;
use std::path::Path;

const INDEX_FILENAME: &str = "archive_index.sqlite";

const SCHEMA_VERSION: i64 = 2;

const LIST_FLAGS: &[&str] = &[
    "-all", "-terse", "-csv", "\t", "-csvhf", "#", "-utf", "-noeta",
];

#[derive(Debug, Clone, PartialEq)]
pub struct IndexEntry {
    pub path: String,
    pub size: i64,
    pub datetime: String,
    pub version: Option<i64>,
    pub flag: String,
    pub is_dir: bool,
    pub attr: String,
    pub ratio: String,
}

impl IndexEntry {
    pub fn name(&self) -> String {
        if self.path.is_empty() {
            return String::new();
        }
        self.path
            .trim_end_matches('/')
            .rsplit('/')
            .next()
            .unwrap_or("")
            .to_string()
    }
}

pub fn parse_size(value: &str) -> i64 {
    let cleaned: String = value
        .trim()
        .chars()
        .filter(|c| *c != '.' && *c != ',')
        .collect();
    cleaned.parse::<i64>().unwrap_or(0)
}

fn clean_csv_line(line: &str) -> &str {
    let mut line = line.trim_end_matches('\n');
    if let Some(rest) = line.strip_prefix('#') {
        line = rest;
    }
    if let Some(rest) = line.strip_suffix('#') {
        line = rest;
    }
    line
}

pub fn parse_csv_line(raw_line: &str) -> Option<IndexEntry> {
    if raw_line.trim().is_empty() {
        return None;
    }
    if raw_line.trim().starts_with("<<") {
        return None;
    }

    let line = clean_csv_line(raw_line);
    if line.is_empty() {
        return None;
    }

    let parts: Vec<&str> = line.split('\t').collect();
    let (dt, attr, size_s, ratio, version, flag, path) = match parts.len() {
        7 => (
            parts[0],
            parts[1],
            parts[2],
            parts[3],
            Some(parts[4]),
            parts[5],
            parts[6],
        ),
        6 => (parts[0], parts[1], parts[2], parts[3], None, parts[4], parts[5]),
        _ => return None,
    };

    let version = match version {
        Some(s) => match s.trim().parse::<i64>() {
            Ok(v) => Some(v),
            Err(_) => return None,
        },
        None => None,
    };

    let path = path.trim();
    if path.is_empty() {
        return None;
    }

    let is_dir = attr.to_uppercase().starts_with('D')
        || ratio.trim().eq_ignore_ascii_case("dir")
        || path.ends_with('/');
    let path = if is_dir { path.trim_end_matches('/') } else { path };

    Some(IndexEntry {
        path: path.to_string(),
        size: parse_size(size_s),
        datetime: dt.trim().to_string(),
        version,
        flag: flag.trim().to_string(),
        is_dir,
        attr: attr.trim().to_string(),
        ratio: ratio.trim().to_string(),
    })
}

pub fn parse_csv_list(text: &str) -> Vec<IndexEntry> {
    text.lines().filter_map(parse_csv_line).collect()
}

pub fn build_list_cmd(zpaq_bin: &str, path: &str, password: Option<&str>) -> Vec<String> {
    let mut cmd: Vec<String> = Vec::with_capacity(4 + LIST_FLAGS.len());
    cmd.push(zpaq_bin.to_string());
    cmd.push("l".to_string());
    cmd.push(path.to_string());
    cmd.extend(LIST_FLAGS.iter().map(|s| s.to_string()));
    if let Some(p) = password {
        if !p.is_empty() {
            cmd.push("-key".to_string());
            cmd.push(p.to_string());
        }
    }
    cmd
}

fn file_stamp(path: &str) -> Option<(i64, i64)> {
    let md = std::fs::metadata(path).ok()?;
    let mtime = md.modified().ok()?;
    let ns = mtime
        .duration_since(std::time::UNIX_EPOCH)
        .ok()?
        .as_nanos() as i64;
    Some((ns, md.len() as i64))
}

fn is_supported(path: &str) -> bool {
    !path.is_empty() && !path.contains('?')
}

fn index_path() -> Option<std::path::PathBuf> {
    cfg::config_path()?.parent().map(|d| d.join(INDEX_FILENAME))
}

fn migrate_if_needed(conn: &rusqlite::Connection) {
    let version: i64 = conn
        .query_row("PRAGMA user_version", [], |r| r.get(0))
        .unwrap_or(0);
    if version >= SCHEMA_VERSION {
        return;
    }
    let _ = conn.execute_batch(
        "DROP INDEX IF EXISTS idx_entries_archive;
         DROP TABLE IF EXISTS entries;
         DROP TABLE IF EXISTS archives;",
    );
    let ok = conn.execute_batch(
        "CREATE TABLE IF NOT EXISTS archives (
            path           TEXT PRIMARY KEY,
            mtime_ns       INTEGER NOT NULL,
            size           INTEGER NOT NULL,
            entries_count  INTEGER NOT NULL DEFAULT 0,
            updated_at     INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS entries (
            archive_path   TEXT NOT NULL,
            path_inside    TEXT NOT NULL,
            name           TEXT NOT NULL,
            size           INTEGER NOT NULL,
            date           TEXT NOT NULL,
            version        INTEGER,
            flag           TEXT NOT NULL,
            is_dir         INTEGER NOT NULL,
            attr           TEXT NOT NULL DEFAULT '',
            ratio          TEXT NOT NULL DEFAULT '',
            position       INTEGER NOT NULL,
            PRIMARY KEY (archive_path, position)
        );
        CREATE INDEX IF NOT EXISTS idx_entries_archive ON entries(archive_path);
        CREATE TABLE IF NOT EXISTS catalog (
            path           TEXT PRIMARY KEY,
            size           INTEGER NOT NULL DEFAULT 0,
            mtime_ns       INTEGER NOT NULL DEFAULT 0,
            discovered_at  INTEGER NOT NULL DEFAULT 0,
            missing        INTEGER NOT NULL DEFAULT 0
        );",
    );
    if ok.is_ok() {
        let _ = conn.execute("PRAGMA user_version = 2", []);
    }
}

fn store_entries(path: &str, mtime_ns: i64, size: i64, entries: &[IndexEntry]) {
    if !is_supported(path) {
        return;
    }
    let Some(db_path) = index_path() else { return };
    if let Some(parent) = db_path.parent() {
        let _ = std::fs::create_dir_all(parent);
    }

    let Ok(mut conn) = rusqlite::Connection::open(&db_path) else {
        return;
    };
    let _ = conn.query_row("PRAGMA journal_mode=WAL", [], |r| r.get::<_, String>(0));
    let _ = conn.query_row("PRAGMA synchronous=NORMAL", [], |r| r.get::<_, String>(0));
    let _ = conn.query_row("PRAGMA busy_timeout=3000", [], |r| r.get::<_, i64>(0));
    migrate_if_needed(&conn);

    let now = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs() as i64)
        .unwrap_or(0);

    let tx = match conn.transaction() {
        Ok(t) => t,
        Err(_) => return,
    };
    let result = (|| -> rusqlite::Result<()> {
        tx.execute(
            "DELETE FROM entries WHERE archive_path = ?1",
            params![path],
        )?;
        for (i, e) in entries.iter().enumerate() {
            tx.execute(
                "INSERT INTO entries \
                 (archive_path, path_inside, name, size, date, version, \
                  flag, is_dir, attr, ratio, position) \
                 VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11)",
                params![
                    path,
                    e.path,
                    e.name(),
                    e.size,
                    e.datetime,
                    e.version,
                    e.flag,
                    if e.is_dir { 1 } else { 0 },
                    e.attr,
                    e.ratio,
                    i as i64,
                ],
            )?;
        }
        tx.execute(
            "INSERT OR REPLACE INTO archives \
             (path, mtime_ns, size, entries_count, updated_at) \
             VALUES (?1, ?2, ?3, ?4, ?5)",
            params![path, mtime_ns, size, entries.len() as i64, now],
        )?;
        Ok(())
    })();
    if result.is_ok() {
        let _ = tx.commit();
    }
}

fn store_fresh_listing(path: &str, entries: &[IndexEntry]) -> usize {
    let Some((mtime_ns, size)) = file_stamp(path) else {
        return 0;
    };
    if path.contains('?') {
        return 0;
    }
    store_entries(path, mtime_ns, size, entries);
    entries.len()
}

pub fn refresh_index_sync(zpaq_bin: &str, path: &str, password: Option<&str>) -> usize {
    if !is_supported(path) {
        return 0;
    }
    if !Path::new(path).is_file() {
        return 0;
    }

    let Some(stamp) = file_stamp(path) else {
        return 0;
    };

    let cmd = build_list_cmd(zpaq_bin, path, password);
    let (rc, output) = engine::run_engine(&cmd);
    if rc != 0 || output.is_empty() {
        return 0;
    }

    if file_stamp(path) != Some(stamp) {
        return 0;
    }

    let entries = parse_csv_list(&output);
    if entries.is_empty() {
        return 0;
    }
    store_fresh_listing(path, &entries)
}

#[allow(dead_code)]
pub fn password_of(v: Option<&Value>) -> Option<&str> {
    match v {
        Some(Value::String(s)) if !s.is_empty() => Some(s),
        _ => None,
    }
}


#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_size_with_separators() {
        assert_eq!(parse_size("4.371"), 4371);
        assert_eq!(parse_size("39.551.238"), 39551238);
        assert_eq!(parse_size("119,064"), 119064);
        assert_eq!(parse_size(""), 0);
        assert_eq!(parse_size("abc"), 0);
    }

    #[test]
    fn csv_line_seven_columns() {
        let line = "2026-10-07 12:00:00\t-A-\t4.371\t55%\t3\t+file\tdocs/report.txt";
        let e = parse_csv_line(line).expect("разобрана");
        assert_eq!(e.path, "docs/report.txt");
        assert_eq!(e.size, 4371);
        assert_eq!(e.version, Some(3));
        assert_eq!(e.flag, "+file");
        assert_eq!(e.name(), "report.txt");
        assert!(!e.is_dir);
    }

    #[test]
    fn csv_line_six_columns_and_dirs() {
        let line = "2026-10-07 12:00:00\tD...\t0\tdir\t\tsub/";
        let e = parse_csv_line(line).expect("разобрана");
        assert_eq!(e.version, None);
        assert!(e.is_dir);
        assert_eq!(e.path, "sub");
    }

    #[test]
    fn csv_line_rejects_garbage() {
        assert!(parse_csv_line("<<D:\\b\\a.zpaq>>").is_none());
        assert!(parse_csv_line("a\tb\tc").is_none());
        assert!(parse_csv_line("dt\tattr\t1\t1\tabc\tf\tp").is_none());
        assert!(parse_csv_line("dt\tattr\t1\t1\t1\tf\t   ").is_none());
        let e = parse_csv_line("#dt\tattr\t1\t1\t1\tf\tp#").expect("разобрана");
        assert_eq!(e.path, "p");
    }

    #[test]
    fn list_cmd_matches_python() {
        let cmd = build_list_cmd("zpaqfranz", "D:\\b\\a.zpaq", Some("pw"));
        assert_eq!(
            cmd,
            vec![
                "zpaqfranz",
                "l",
                "D:\\b\\a.zpaq",
                "-all",
                "-terse",
                "-csv",
                "\t",
                "-csvhf",
                "#",
                "-utf",
                "-noeta",
                "-key",
                "pw",
            ]
        );
        let cmd = build_list_cmd("zpaqfranz", "a.zpaq", None);
        assert!(!cmd.contains(&"-key".to_string()));
    }
}
