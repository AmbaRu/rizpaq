use rizpaq_task::cmdline;
use serde_json::json;
use std::path::PathBuf;

fn cmd_for(dest: &PathBuf) -> Vec<String> {
    let settings = json!({
        "checkspace": "50G",
        "level": ["-m1"],
    });
    cmdline::build_create_cmd(
        "zpaqfranz.exe",
        &settings,
        &["C:\\data\\docs".to_string()],
        &dest.to_string_lossy(),
        None,
    )
}

fn checksize_value(cmd: &[String]) -> Option<&str> {
    cmd.iter()
        .position(|a| a == "-checksize")
        .and_then(|i| cmd.get(i + 1))
        .map(|s| s.as_str())
}

#[test]
fn existing_archive_uses_append_minimum() {
    let root = std::env::temp_dir().join(format!(
        "rizpaq_checksize_{}_{}",
        "existing",
        std::process::id()
    ));
    let _ = std::fs::remove_dir_all(&root);
    std::fs::create_dir_all(&root).unwrap();
    let dest = root.join("backup.zpaq");
    std::fs::write(&dest, b"existing archive").unwrap();

    let got = checksize_value(&cmd_for(&dest)).unwrap_or("").to_string();
    let _ = std::fs::remove_dir_all(&root);
    assert_eq!(got, "1G");
}

#[test]
fn new_archive_keeps_requested_value() {
    let root = std::env::temp_dir().join(format!(
        "rizpaq_checksize_{}_{}",
        "new",
        std::process::id()
    ));
    let _ = std::fs::remove_dir_all(&root);
    std::fs::create_dir_all(&root).unwrap();
    let dest = root.join("backup.zpaq");

    let got = checksize_value(&cmd_for(&dest)).unwrap_or("").to_string();
    let _ = std::fs::remove_dir_all(&root);
    assert_eq!(got, "50G");
}
