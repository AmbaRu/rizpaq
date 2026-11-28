
use rizpaq_task::cmdline;
use std::path::PathBuf;

const SIGNATURE: &str = "$zpaqfranz backupfile|";

fn temp_root(tag: &str) -> PathBuf {
    let root = std::env::temp_dir().join(format!(
        "rizpaq_backup_paths_{}_{}",
        tag,
        std::process::id()
    ));
    let _ = std::fs::remove_dir_all(&root);
    std::fs::create_dir_all(&root).unwrap();
    root
}

#[test]
fn base_with_trailing_digits_is_recognized() {
    let root = temp_root("base");
    for n in 1..=2 {
        std::fs::write(
            root.join(format!("photo_2024_{:08}.zpaq", n)),
            b"part",
        )
        .unwrap();
    }
    std::fs::write(
        root.join("photo_2024_00000000_backup.txt"),
        format!("{}something\n", SIGNATURE),
    )
    .unwrap();

    let base = root.join("photo_2024.zpaq");
    let part = root.join("photo_2024_00000001.zpaq");
    let mask = root.join("photo_2024_????????.zpaq");
    let base = base.to_string_lossy().into_owned();
    let part = part.to_string_lossy().into_owned();
    let mask = mask.to_string_lossy().into_owned();

    assert!(cmdline::is_backup_set(&base), "база набора не распознана");
    assert!(cmdline::is_backup_set(&part), "часть набора не распознана");
    assert_eq!(cmdline::backup_base(&base), base);
    assert_eq!(cmdline::backup_base(&part), base);
    assert_eq!(cmdline::backup_mask(&base), mask);
    assert_eq!(cmdline::archive_alias(&base), mask);
    assert_eq!(cmdline::multipart_pattern(&base), mask);
    assert_eq!(cmdline::multipart_pattern(&part), mask);
    assert!(cmdline::backup_set_exists(&base));
    assert_eq!(cmdline::backup_parts(&base).len(), 2);

    let _ = std::fs::remove_dir_all(root);
}

#[test]
fn five_digit_suffix_is_not_a_part() {
    let path = "D:/data_00001.zpaq";
    assert_eq!(cmdline::multipart_base(path), path);
    assert_eq!(cmdline::backup_base(path), path);
}

#[test]
fn ordinary_volume_keeps_its_own_mask() {
    assert_eq!(
        cmdline::archive_alias("D:/plain_0001.zpaq"),
        "D:/plain_????.zpaq"
    );
    assert_eq!(
        cmdline::archive_alias("D:/odd_12345.zpaq"),
        "D:/odd_12345.zpaq"
    );
}

#[test]
fn backup_create_uses_backup_and_drops_sfx() {
    let settings = serde_json::json!({
        "create_mode": "backup",
        "sfx": "C:/out/self.exe",
    });
    let srcs = vec!["D:/data".to_string()];
    let got = cmdline::build_create_cmd(
        "zpaq",
        &settings,
        &srcs,
        "D:/arc.zpaq",
        None,
    );
    assert_eq!(got[0], "zpaq");
    assert_eq!(got[1], "backup", "режим backup должен сменить команду");
    assert_eq!(got[2], "D:/arc.zpaq", "база передаётся без маски");
    assert_eq!(got[3], "D:/data");
    assert!(got.contains(&"-open".to_string()));
    assert!(
        !got.iter().any(|a| a == "-sfx"),
        "-sfx несовместим с backup"
    );
}

#[test]
fn normal_create_keeps_a_and_sfx() {
    let settings = serde_json::json!({ "sfx": "C:/out/self.exe" });
    let srcs = vec!["D:/data".to_string()];
    let got = cmdline::build_create_cmd(
        "zpaq",
        &settings,
        &srcs,
        "D:/arc.zpaq",
        None,
    );
    assert_eq!(got[1], "a");
    assert!(got
        .windows(2)
        .any(|w| w[0] == "-sfx" && w[1] == "C:/out/self.exe"));
}
