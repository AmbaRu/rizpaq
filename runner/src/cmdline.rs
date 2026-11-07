






use crate::tasks::{py_str, py_truthy};
use serde_json::Value;


fn truthy(settings: &Value, key: &str) -> bool {
    py_truthy(settings.get(key))
}


fn py_value(settings: &Value, key: &str) -> String {
    py_str(settings.get(key).unwrap_or(&Value::Null))
}









pub fn build_create_cmd(
    zpaq: &str,
    settings: &Value,
    srcs: &[String],
    dest: &str,
    password: Option<&str>,
) -> Vec<String> {
    let mut cmd: Vec<String> = Vec::new();
    cmd.push(zpaq.to_string());
    cmd.push("a".to_string());
    cmd.push(dest.to_string());
    for s in srcs {
        cmd.push(s.clone());
    }
    
    cmd.push("-open".to_string());

    
    if let Some(arr) = settings.get("level").and_then(Value::as_array) {
        for f in arr {
            cmd.push(py_str(f));
        }
    }
    if truthy(settings, "hash") {
        cmd.push(py_value(settings, "hash"));
    }
    if truthy(settings, "comment") {
        cmd.push("-comment".to_string());
        cmd.push(py_value(settings, "comment"));
    }
    if let Some(arr) = settings.get("only_masks").and_then(Value::as_array) {
        for m in arr {
            cmd.push("-only".to_string());
            cmd.push(py_str(m));
        }
    }
    if let Some(arr) = settings.get("not_masks").and_then(Value::as_array) {
        for m in arr {
            cmd.push("-not".to_string());
            cmd.push(py_str(m));
        }
    }
    
    if truthy(settings, "longpath") && !srcs.is_empty() && !srcs.iter().any(|s| s == "*") {
        cmd.push("-longpath".to_string());
    }
    if truthy(settings, "date") {
        cmd.push("-date".to_string());
    }
    if truthy(settings, "norecursion") {
        cmd.push("-norecursion".to_string());
    }
    if truthy(settings, "forcewindows") {
        cmd.push("-forcewindows".to_string());
    }
    if truthy(settings, "force_xls") {
        cmd.push("-xls".to_string());
    }
    if truthy(settings, "nochecksum") {
        cmd.push("-nochecksum".to_string());
    }
    if truthy(settings, "nodedup") {
        cmd.push("-nodedup".to_string());
    }
    if truthy(settings, "vss") {
        cmd.push("-vss".to_string());
    }
    if truthy(settings, "checkspace") {
        cmd.push("-checksize".to_string());
        cmd.push(py_value(settings, "checkspace"));
    }
    if truthy(settings, "noonedrive") {
        cmd.push("-noonedrive".to_string());
    }
    if truthy(settings, "ignore") {
        cmd.push("-ignore".to_string());
    }
    if truthy(settings, "errorlog") {
        cmd.push("-errorlog".to_string());
        cmd.push(py_value(settings, "errorlog"));
    }
    if truthy(settings, "shutdown") {
        cmd.push("-shutdown".to_string());
    }
    if truthy(settings, "sfx") {
        cmd.push("-sfx".to_string());
        cmd.push(py_value(settings, "sfx"));
    }
    if truthy(settings, "chunk") {
        cmd.push("-chunk".to_string());
        cmd.push(py_value(settings, "chunk"));
    }
    if let Some(pw) = password {
        if !pw.is_empty() {
            cmd.push("-key".to_string());
            cmd.push(pw.to_string());
        }
    }
    cmd
}







pub fn build_test_cmd(
    zpaq: &str,
    dest: &str,
    password: Option<&str>,
    test_mode: Option<&str>,
    tmp_dir: Option<&str>,
) -> Vec<String> {
    let mut cmd: Vec<String> = Vec::new();
    cmd.push(zpaq.to_string());
    cmd.push("t".to_string());
    cmd.push(dest.to_string());
    let mode = test_mode.unwrap_or("full").trim().to_lowercase();
    match mode.as_str() {
        "checksum" => {
            cmd.push("-all".to_string());
            cmd.push("-checksum".to_string());
        }
        "verify" => {
            cmd.push("-verify".to_string());
        }
        "paranoid" => {
            cmd.push("-verify".to_string());
            cmd.push("-paranoid".to_string());
            if let Some(tmp) = tmp_dir {
                if !tmp.is_empty() {
                    cmd.push("-to".to_string());
                    cmd.push(tmp.to_string());
                }
            }
        }
        
        _ => {}
    }
    if let Some(pw) = password {
        if !pw.is_empty() {
            cmd.push("-key".to_string());
            cmd.push(pw.to_string());
        }
    }
    cmd
}
