






use std::fs::OpenOptions;
use std::io::Write;

pub const TEMP_ERROR_NAME: &str = "rizpaq_task_error.log";





pub fn write_temp_error(text: &str) {
    let path = std::env::temp_dir().join(TEMP_ERROR_NAME);
    let iso = chrono::Local::now().format("%Y-%m-%dT%H:%M:%S");
    let mut buf = format!("--- Rizpaq task error {} ---\n", iso);
    buf.push_str(text);
    if !text.ends_with('\n') {
        buf.push('\n');
    }
    buf.push_str(&"=".repeat(50));
    buf.push_str("\n\n");
    if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(&path) {
        let _ = f.write_all(buf.as_bytes());
    }
}






pub fn append_raw(text: &str) {
    let path = std::env::temp_dir().join(TEMP_ERROR_NAME);
    if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(&path) {
        let _ = f.write_all(text.as_bytes());
    }
}
