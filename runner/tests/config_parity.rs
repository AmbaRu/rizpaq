use rizpaq_task::cfg;
use serde_json::{json, Value};
use std::path::PathBuf;

static ENV_LOCK: std::sync::Mutex<()> = std::sync::Mutex::new(());

fn config_with_port(port: Value) -> PathBuf {
    let path = std::env::temp_dir().join(format!(
        "rizpaq_cfg_port_{}_{}.json",
        std::process::id(),
        port.to_string().replace(|c: char| !c.is_ascii_alphanumeric(), "_")
    ));
    let data = json!({
        "mail_report_enabled": true,
        "mail_smtp_server": "smtp.example.com",
        "mail_smtp_port": port,
        "mail_from": "from@example.com",
        "mail_to": "to@example.com",
    });
    std::fs::write(&path, data.to_string()).unwrap();
    path
}

#[test]
fn mail_port_accepts_json_number() {
    let _guard = ENV_LOCK.lock().unwrap_or_else(|e| e.into_inner());
    let path = config_with_port(json!(2525));
    std::env::set_var("ZPAQ_GUI_CONFIG", &path);
    let mail = cfg::mail_config().expect("конфиг прочитан");
    let _ = std::fs::remove_file(&path);
    assert_eq!(mail.port, "2525");
}

#[test]
fn mail_port_rejects_out_of_range() {
    let _guard = ENV_LOCK.lock().unwrap_or_else(|e| e.into_inner());
    let path = config_with_port(json!(70000));
    std::env::set_var("ZPAQ_GUI_CONFIG", &path);
    let mail = cfg::mail_config().expect("конфиг прочитан");
    let _ = std::fs::remove_file(&path);
    assert_eq!(mail.port, "", "порт вне диапазона должен значить «авто»");
}

#[test]
fn mail_port_accepts_numeric_string() {
    let _guard = ENV_LOCK.lock().unwrap_or_else(|e| e.into_inner());
    let path = config_with_port(json!("465"));
    std::env::set_var("ZPAQ_GUI_CONFIG", &path);
    let mail = cfg::mail_config().expect("конфиг прочитан");
    let _ = std::fs::remove_file(&path);
    assert_eq!(mail.port, "465");
}
