use serde_json::json;
use std::path::Path;
use std::process::Command;

fn stub_engine(root: &Path) -> std::path::PathBuf {
    let stub = root.join("stub_engine.cmd");
    std::fs::write(&stub, "@echo off\r\necho data > \"%~2\"\r\nexit /b 0\r\n").unwrap();
    stub
}

#[test]
fn missing_copy_field_does_not_create_none_folder() {
    let root = std::env::temp_dir().join(format!("rizpaq_none_field_{}", std::process::id()));
    let _ = std::fs::remove_dir_all(&root);
    std::fs::create_dir_all(&root).unwrap();

    let zpaq = stub_engine(&root);
    let source = root.join("data.txt");
    std::fs::write(&source, "missing field regression\n").unwrap();
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
        .current_dir(&root)
        .env("ZPAQ_GUI_CONFIG", &config_path)
        .env("ZPAQ_BIN", &zpaq)
        .status()
        .expect("запустить headless-раннер");

    let log = std::fs::read_to_string(container_path.with_extension("rzp.log"))
        .unwrap_or_default();
    let none_folder = root.join("None").exists();
    let _ = std::fs::remove_dir_all(&root);

    assert!(outcome.success(), "бэкап должен завершиться успехом");
    assert!(!none_folder, "папка 'None' не должна создаваться");
    assert!(!log.contains("second copy"), "копия не была запрошена");
}
