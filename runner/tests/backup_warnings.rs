use rizpaq_task::tasks;
use serde_json::json;
use std::path::{Path, PathBuf};
use std::process::Command;

fn stub_engine(root: &Path) -> PathBuf {
    let stub = root.join("stub_engine.cmd");
    std::fs::write(
        &stub,
        "@echo off\r\necho 12345! with warnings\r\nexit /b 1\r\n",
    )
    .unwrap();
    stub
}

#[test]
fn backup_warning_rc_is_success() {
    let root =
        std::env::temp_dir().join(format!("rizpaq_warning_rc_{}", std::process::id()));
    let _ = std::fs::remove_dir_all(&root);
    std::fs::create_dir_all(&root).unwrap();

    let zpaq = stub_engine(&root);
    let source = root.join("data.txt");
    std::fs::write(&source, "warning rc regression\n").unwrap();
    let archive = root.join("a.zpaq");
    let container_path = root.join("job.rzp");
    let config_path = root.join("zpaq_gui.json");

    let container = json!({
        "format": "rizpaq.tasks",
        "version": 1,
        "works": [{
            "id": "w1",
            "title": "Work",
            "sources": [source.to_string_lossy()],
            "dest": archive.to_string_lossy(),
            "jobs": [{
                "id": "j1",
                "title": "Job",
                "action": "backup",
                "copy": "",
                "par2_enabled": false,
            }],
        }],
    });
    std::fs::write(
        &container_path,
        serde_json::to_string_pretty(&container).unwrap(),
    )
    .unwrap();
    std::fs::write(&config_path, json!({"language": "en"}).to_string()).unwrap();

    let outcome = Command::new(env!("CARGO_BIN_EXE_rizpaq_task"))
        .arg("--task")
        .arg(&container_path)
        .arg("--job")
        .arg("j1")
        .env("ZPAQ_GUI_CONFIG", &config_path)
        .env("ZPAQ_BIN", &zpaq)
        .status()
        .expect("запустить headless-раннер");

    let saved = tasks::load_container(&container_path);
    let job = &saved["works"][0]["jobs"][0];
    let status = job["last_status"].as_str().unwrap_or("").to_string();
    let _ = std::fs::remove_dir_all(&root);

    assert!(outcome.success(), "rc=1 with warnings is a successful backup");
    assert_eq!(status, "ok", "job status must be ok");
}
