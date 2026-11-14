
use crate::cfg;
use serde_json::Value;
use std::collections::HashMap;
use std::path::PathBuf;

pub const MODE_OFF: &str = "off";
pub const MODE_ERRORS: &str = "errors";
pub const MODE_ALL: &str = "all";

const MAX_TEXT: usize = 3900;

#[cfg(windows)]
const TIMEOUT_MS: i32 = 10_000;

const RETRY_COUNT: u32 = 3;
const RETRY_PAUSE_S: u64 = 2;

const NOTIFY_DEADLINE_S: u64 = 30;

#[derive(Debug)]
pub enum SendResult {
    Ok,
    Transport(String),
    Rejected(String),
}

pub fn should_notify(mode: &str, status: &str) -> bool {
    let mode = mode.trim().to_lowercase();
    let status = status.trim().to_lowercase();
    if status != "ok" && status != "error" {
        return false;
    }
    match mode.as_str() {
        MODE_ALL => true,
        MODE_ERRORS => status == "error",
        _ => false,
    }
}

pub fn format_message(
    strings: &HashMap<String, String>,
    work: &str,
    job: &str,
    status: &str,
    archive: &str,
    reason: &str,
    time_text: &str,
) -> String {
    fn tr(strings: &HashMap<String, String>, key: &str) -> String {
        strings
            .get(key)
            .cloned()
            .unwrap_or_else(|| key.to_string())
    }

    fn fill(
        strings: &HashMap<String, String>,
        key: &str,
        param: &str,
        value: &str,
    ) -> String {
        tr(strings, key).replace(&format!("{{{}}}", param), value)
    }

    let mut lines: Vec<String> = Vec::new();
    let title_key = if status.trim().to_lowercase() == "ok" {
        "notify.message.title_ok"
    } else {
        "notify.message.title_error"
    };
    lines.push(tr(strings, title_key));
    if !work.is_empty() {
        lines.push(fill(strings, "notify.message.work", "name", work));
    }
    if !job.is_empty() {
        lines.push(fill(strings, "notify.message.job", "name", job));
    }
    if !archive.is_empty() {
        lines.push(fill(
            strings,
            "notify.message.archive",
            "path",
            archive,
        ));
    }
    if !reason.is_empty() {
        let key = format!("backup.reason.{}", reason);
        let reason_text = strings
            .get(&key)
            .cloned()
            .unwrap_or_else(|| reason.to_string());
        lines.push(fill(
            strings,
            "notify.message.reason",
            "reason",
            &reason_text,
        ));
    }
    lines.push(fill(
        strings,
        "notify.message.time",
        "time",
        time_text,
    ));

    let mut text = lines.join("\n");
    if text.chars().count() > MAX_TEXT {
        text = text.chars().take(MAX_TEXT - 1).collect::<String>() + "…";
    }
    text
}

fn locale_dirs() -> Vec<PathBuf> {
    let mut out: Vec<PathBuf> = Vec::new();
    if let Ok(exe) = std::env::current_exe() {
        if let Some(dir) = exe.parent() {
            out.push(dir.join("locales"));
            out.push(dir.join("_internal").join("locales"));
        }
    }
    if let Ok(cwd) = std::env::current_dir() {
        out.push(cwd.join("locales"));
        if let Some(parent) = cwd.parent() {
            out.push(parent.join("locales"));
        }
    }
    out
}

fn read_lang(lang: &str) -> HashMap<String, String> {
    if lang.is_empty() {
        return HashMap::new();
    }
    for dir in locale_dirs() {
        let path = dir.join(format!("{}.json", lang));
        let Ok(text) = std::fs::read_to_string(&path) else {
            continue;
        };
        let Ok(data) = serde_json::from_str::<Value>(&text) else {
            continue;
        };
        let Some(obj) = data.get("strings").and_then(Value::as_object) else {
            continue;
        };
        return obj
            .iter()
            .filter_map(|(key, value)| {
                value
                    .as_str()
                    .map(|s| (key.clone(), s.to_string()))
            })
            .collect();
    }
    HashMap::new()
}

fn strings_for(lang: &str) -> HashMap<String, String> {
    let mut strings = read_lang("en");
    if !lang.is_empty() && lang != "en" {
        strings.extend(read_lang(lang));
    }
    strings
}

pub fn notify_job(
    work_title: &str,
    job_title: &str,
    status: &str,
    reason: Option<&str>,
    archive: &str,
) {
    let Some(cfg) = cfg::notify_config() else {
        return;
    };
    if !should_notify(&cfg.mode, status) {
        return;
    }
    if cfg.token.is_empty() || cfg.chat_id.is_empty() {
        log_failure("Telegram: токен или chat_id не задан");
        return;
    }
    let strings = strings_for(&cfg.language);
    let time_text = chrono::Local::now()
        .format("%d.%m.%Y %H:%M")
        .to_string();
    let text = format_message(
        &strings,
        work_title,
        job_title,
        status,
        archive,
        reason.unwrap_or(""),
        &time_text,
    );
    let token = cfg.token.clone();
    let chat_id = cfg.chat_id.clone();
    let (tx, rx) = std::sync::mpsc::channel();
    std::thread::spawn(move || {
        send_with_retries(&token, &chat_id, &text);
        let _ = tx.send(());
    });
    if rx
        .recv_timeout(std::time::Duration::from_secs(NOTIFY_DEADLINE_S))
        .is_err()
    {
        log_failure(&format!(
            "Telegram: отправка не завершилась за {} с",
            NOTIFY_DEADLINE_S
        ));
    }
}

fn send_with_retries(token: &str, chat_id: &str, text: &str) {
    let mut last_reason = String::new();
    for attempt in 1..=RETRY_COUNT {
        match post_json(token, chat_id, text) {
            SendResult::Ok => return,
            SendResult::Rejected(reason) => {
                log_failure(&format!("Telegram: {}", reason));
                return;
            }
            SendResult::Transport(reason) => {
                last_reason = reason;
                if attempt < RETRY_COUNT {
                    std::thread::sleep(std::time::Duration::from_secs(RETRY_PAUSE_S));
                }
            }
        }
    }
    log_failure(&format!("Telegram: {}", last_reason));
}

fn log_failure(text: &str) {
    cfg::write_error_log_named(text, "rizpaq_notify.log");
}


#[cfg(not(windows))]
fn post_json(_token: &str, _chat_id: &str, _text: &str) -> SendResult {
    SendResult::Transport("сборка без WinHTTP: отправка невозможна".to_string())
}

#[cfg(windows)]
fn post_json(token: &str, chat_id: &str, text: &str) -> SendResult {
    unsafe { post_json_inner(token, chat_id, text) }
}

#[cfg(windows)]
mod winhttp {
    use core::ffi::c_void;

    pub type Handle = *mut c_void;

    pub const ACCESS_TYPE_DEFAULT_PROXY: u32 = 0;
    pub const FLAG_SECURE: u32 = 0x0080_0000;
    pub const QUERY_STATUS_CODE: u32 = 19;
    pub const QUERY_FLAG_NUMBER: u32 = 0x2000_0000;

    #[allow(non_snake_case)]
    #[link(name = "winhttp")]
    extern "system" {
        pub fn WinHttpOpen(
            pszAgentW: *const u16,
            dwAccessType: u32,
            pszProxyW: *const u16,
            pszProxyBypassW: *const u16,
            dwFlags: u32,
        ) -> Handle;
        pub fn WinHttpConnect(
            hSession: Handle,
            pswzServerName: *const u16,
            nServerPort: u16,
            dwReserved: u32,
        ) -> Handle;
        pub fn WinHttpOpenRequest(
            hConnect: Handle,
            pwszVerb: *const u16,
            pwszObjectName: *const u16,
            pwszVersion: *const u16,
            pwszReferrer: *const u16,
            ppwszAcceptTypes: *const *const u16,
            dwFlags: u32,
        ) -> Handle;
        pub fn WinHttpSendRequest(
            hRequest: Handle,
            lpszHeaders: *const u16,
            dwHeadersLength: u32,
            lpOptional: *const c_void,
            dwOptionalLength: u32,
            dwTotalLength: u32,
            dwContext: usize,
        ) -> i32;
        pub fn WinHttpReceiveResponse(
            hRequest: Handle,
            lpReserved: *mut c_void,
        ) -> i32;
        pub fn WinHttpQueryHeaders(
            hRequest: Handle,
            dwInfoLevel: u32,
            pwszName: *const u16,
            lpBuffer: *mut c_void,
            lpdwBufferLength: *mut u32,
            lpdwIndex: *mut u32,
        ) -> i32;
        pub fn WinHttpSetTimeouts(
            hInternet: Handle,
            nResolveTimeout: i32,
            nConnectTimeout: i32,
            nSendTimeout: i32,
            nReceiveTimeout: i32,
        ) -> i32;
        pub fn WinHttpCloseHandle(hInternet: Handle) -> i32;
        pub fn WinHttpQueryDataAvailable(
            hRequest: Handle,
            lpdwDataAvailable: *mut u32,
        ) -> i32;
        pub fn WinHttpReadData(
            hRequest: Handle,
            lpBuffer: *mut c_void,
            dwBufferLength: u32,
            lpdwBytesRead: *mut u32,
        ) -> i32;
    }

    pub struct Guard(pub Handle);

    impl Drop for Guard {
        fn drop(&mut self) {
            if !self.0.is_null() {
                unsafe {
                    WinHttpCloseHandle(self.0);
                }
            }
        }
    }
}

#[cfg(windows)]
fn wide(text: &str) -> Vec<u16> {
    text.encode_utf16().chain(std::iter::once(0)).collect()
}

#[cfg(windows)]
unsafe fn post_json_inner(token: &str, chat_id: &str, text: &str) -> SendResult {
    use core::ffi::c_void;
    use winhttp::*;

    if token.is_empty() || chat_id.is_empty() || text.is_empty() {
        return SendResult::Rejected("токен, chat_id или текст пуст".to_string());
    }

    let body = serde_json::json!({
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": true,
    })
    .to_string();

    let agent = wide("Rizpaq");
    let session = Guard(WinHttpOpen(
        agent.as_ptr(),
        ACCESS_TYPE_DEFAULT_PROXY,
        core::ptr::null(),
        core::ptr::null(),
        0,
    ));
    if session.0.is_null() {
        return SendResult::Transport(
            "не удалось открыть сетевой сеанс (WinHttpOpen)".to_string(),
        );
    }
    let _ = WinHttpSetTimeouts(
        session.0,
        TIMEOUT_MS,
        TIMEOUT_MS,
        TIMEOUT_MS,
        TIMEOUT_MS,
    );

    let host = wide("api.telegram.org");
    let connect = Guard(WinHttpConnect(session.0, host.as_ptr(), 443, 0));
    if connect.0.is_null() {
        return SendResult::Transport(
            "не удалось подключиться к api.telegram.org".to_string(),
        );
    }

    let verb = wide("POST");
    let path = wide(&format!("/bot{}/sendMessage", token));
    let request = Guard(WinHttpOpenRequest(
        connect.0,
        verb.as_ptr(),
        path.as_ptr(),
        core::ptr::null(),
        core::ptr::null(),
        core::ptr::null(),
        FLAG_SECURE,
    ));
    if request.0.is_null() {
        return SendResult::Transport("не удалось создать HTTP-запрос".to_string());
    }

    let headers = wide("Content-Type: application/json\r\n");
    let sent = WinHttpSendRequest(
        request.0,
        headers.as_ptr(),
        u32::MAX,
        body.as_ptr() as *const c_void,
        body.len() as u32,
        body.len() as u32,
        0,
    );
    if sent == 0 {
        return SendResult::Transport(
            "запрос не отправлен (WinHttpSendRequest)".to_string(),
        );
    }
    if WinHttpReceiveResponse(request.0, core::ptr::null_mut()) == 0 {
        return SendResult::Transport(
            "ответ не получен (WinHttpReceiveResponse)".to_string(),
        );
    }

    let mut status: u32 = 0;
    let mut size: u32 = std::mem::size_of::<u32>() as u32;
    let queried = WinHttpQueryHeaders(
        request.0,
        QUERY_STATUS_CODE | QUERY_FLAG_NUMBER,
        core::ptr::null(),
        &mut status as *mut u32 as *mut c_void,
        &mut size,
        core::ptr::null_mut(),
    );
    if queried == 0 {
        return SendResult::Transport("не удалось прочитать код ответа".to_string());
    }
    if (200..300).contains(&status) {
        return SendResult::Ok;
    }

    let detail = read_response_description(request.0);
    let mut text = format!("Telegram ответил HTTP {}", status);
    if !detail.is_empty() {
        text.push(' ');
        text.push_str(&detail);
    }
    if status == 429 {
        return SendResult::Transport(text);
    }
    SendResult::Rejected(text)
}

#[cfg(windows)]
unsafe fn read_response_description(request: winhttp::Handle) -> String {
    let mut available: u32 = 0;
    if winhttp::WinHttpQueryDataAvailable(request, &mut available) == 0 {
        return String::new();
    }
    let mut buf = vec![0u8; (available as usize).min(4096)];
    if buf.is_empty() {
        return String::new();
    }
    let mut read: u32 = 0;
    if winhttp::WinHttpReadData(
        request,
        buf.as_mut_ptr() as *mut core::ffi::c_void,
        buf.len() as u32,
        &mut read,
    ) == 0
    {
        return String::new();
    }
    let text = String::from_utf8_lossy(&buf[..read as usize]).into_owned();
    match text.find("\"description\"") {
        Some(pos) => {
            let rest = &text[pos + "\"description\"".len()..];
            match rest.find(':') {
                Some(colon) => {
                    let tail = rest[colon + 1..].trim_start();
                    let tail = tail.strip_prefix('"').unwrap_or(tail);
                    match tail.find('"') {
                        Some(end) => tail[..end].to_string(),
                        None => String::new(),
                    }
                }
                None => String::new(),
            }
        }
        None => String::new(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn strings() -> HashMap<String, String> {
        let mut s = HashMap::new();
        s.insert(
            "notify.message.title_ok".to_string(),
            "[Rizpaq] Job completed".to_string(),
        );
        s.insert(
            "notify.message.title_error".to_string(),
            "[Rizpaq] Job failed".to_string(),
        );
        s.insert(
            "notify.message.work".to_string(),
            "Work: {name}".to_string(),
        );
        s.insert(
            "notify.message.job".to_string(),
            "Job: {name}".to_string(),
        );
        s.insert(
            "notify.message.archive".to_string(),
            "Archive: {path}".to_string(),
        );
        s.insert(
            "notify.message.reason".to_string(),
            "Reason: {reason}".to_string(),
        );
        s.insert(
            "notify.message.time".to_string(),
            "Time: {time}".to_string(),
        );
        s.insert(
            "backup.reason.par2_missing".to_string(),
            "set not created".to_string(),
        );
        s
    }

    #[test]
    fn off_never_notifies() {
        for status in ["ok", "error", "busy", ""] {
            assert!(!should_notify("off", status));
        }
    }

    #[test]
    fn errors_mode_only_errors() {
        assert!(should_notify("errors", "error"));
        assert!(!should_notify("errors", "ok"));
        assert!(!should_notify("errors", "busy"));
    }

    #[test]
    fn all_mode_ok_and_error_but_not_busy() {
        assert!(should_notify("all", "ok"));
        assert!(should_notify("all", "error"));
        assert!(!should_notify("all", "busy"));
    }

    #[test]
    fn unknown_mode_and_status_are_off() {
        assert!(!should_notify("weird", "ok"));
        assert!(!should_notify("all", "weird"));
        assert!(!should_notify("", ""));
    }

    #[test]
    fn case_and_whitespace_are_ignored() {
        assert!(should_notify(" ALL ", " OK "));
        assert!(should_notify("errors", " ERROR "));
    }

    #[test]
    fn ok_message_contains_fields() {
        let text = format_message(
            &strings(),
            "Docs",
            "Nightly",
            "ok",
            r"D:\arc\docs.zpaq",
            "",
            "12.11.2026 09:05",
        );
        assert!(text.contains("[Rizpaq] Job completed"));
        assert!(text.contains("Work: Docs"));
        assert!(text.contains("Job: Nightly"));
        assert!(text.contains(r"Archive: D:\arc\docs.zpaq"));
        assert!(text.contains("Time: 12.11.2026 09:05"));
        assert!(!text.contains("Reason:"));
    }

    #[test]
    fn error_message_has_title_and_reason() {
        let text = format_message(
            &strings(),
            "Work",
            "Check",
            "error",
            "",
            "par2_missing",
            "12.11.2026 09:05",
        );
        assert!(text.contains("[Rizpaq] Job failed"));
        assert!(text.contains("Reason: set not created"));
    }

    #[test]
    fn unknown_reason_is_shown_as_token() {
        let text = format_message(
            &strings(),
            "W",
            "J",
            "error",
            "",
            "future_reason",
            "12.11.2026 09:05",
        );
        assert!(text.contains("Reason: future_reason"));
    }

    #[test]
    fn empty_optional_fields_are_omitted() {
        let text = format_message(
            &strings(),
            "",
            "",
            "ok",
            "",
            "",
            "12.11.2026 09:05",
        );
        assert!(!text.contains("Work:"));
        assert!(!text.contains("Job:"));
        assert!(!text.contains("Archive:"));
        assert!(!text.contains("Reason:"));
    }

    #[test]
    fn message_is_bounded_by_chars() {
        let text = format_message(
            &strings(),
            &"W".repeat(10_000),
            "J",
            "ok",
            "",
            "",
            "12.11.2026 09:05",
        );
        assert_eq!(text.chars().count(), MAX_TEXT);
        assert!(text.ends_with('…'));
    }

    #[test]
    fn missing_translation_falls_back_to_key() {
        let text = format_message(
            &HashMap::new(),
            "W",
            "J",
            "ok",
            "",
            "",
            "12.11.2026 09:05",
        );
        assert!(text.contains("notify.message.title_ok"));
    }

    #[test]
    fn locales_contain_notify_keys() {
        let s = strings_for("en");
        assert!(s.contains_key("notify.message.title_ok"));
        assert!(s.contains_key("notify.message.title_error"));
        assert!(s.contains_key("notify.message.time"));
    }
}
