use rizpaq_task::tasks;
use serde_json::json;
use std::path::{Path, PathBuf};
use std::process::Command;

fn engine_path() -> Option<PathBuf> {
    let p = Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()?
        .join("zpaqfranz.exe");
    p.is_file().then_some(p)
}

#[test]
fn par2_failure_is_saved_as_job_error() {
    let Some(zpaq) = engine_path() else {
        eprintln!("skip: zpaqfranz.exe not found next to runner/");
        return;
    };
    let root = std::env::temp_dir().join(format!(
        "rizpaq_task_status_{}_{}",
        "par2_failure",
        std::process::id()
    ));
    let _ = std::fs::remove_dir_all(&root);
    std::fs::create_dir_all(&root).unwrap();

    let source = root.join("data.txt");
    std::fs::write(&source, "task status regression\n").unwrap();
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
                "par2_enabled": true,
                "par2_options": {"redundancy": "not-a-number"},
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
    let reason = job["last_reason"].as_str().unwrap_or("").to_string();
    let _ = std::fs::remove_dir_all(&root);

    assert!(!outcome.success(), "PAR2 не создан — задание обязано быть ошибкой");
    assert_eq!(status, "error", "статус в контейнере должен быть error");
    assert_eq!(reason, "par2_failed", "причина отказа PAR2 должна сохраняться");
}
