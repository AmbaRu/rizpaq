
use crate::cfg::MailConfig;
use crate::engine;
use std::path::PathBuf;
use std::time::{SystemTime, UNIX_EPOCH};

fn tmp_body_file() -> PathBuf {
    let stamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_millis())
        .unwrap_or(0);
    std::env::temp_dir().join(format!(
        "rizpaq_mail_{}_{}.log",
        std::process::id(),
        stamp
    ))
}

pub fn send_text_report(
    zpaq: &str,
    mail: &MailConfig,
    subject: &str,
    body: &str,
) -> (bool, String) {
    if !mail.ready() {
        return (false, "mail is not configured".to_string());
    }
    let path = tmp_body_file();
    if let Err(e) = std::fs::write(&path, body.as_bytes()) {
        return (false, format!("cannot write mail body: {}", e));
    }

    let mut cmd: Vec<String> = vec![
        zpaq.to_string(),
        "work".to_string(),
        "email".to_string(),
        "-mailserver".to_string(),
        mail.server.clone(),
    ];
    if !mail.port.is_empty() && mail.port != "0" {
        cmd.push("-mailport".to_string());
        cmd.push(mail.port.clone());
    }
    if mail.tls == "ssl" {
        cmd.push("-mailssl".to_string());
    }
    if !mail.user.is_empty() {
        cmd.push("-mailuser".to_string());
        cmd.push(mail.user.clone());
        if !mail.password.is_empty() {
            cmd.push("-mailpassword".to_string());
            cmd.push(mail.password.clone());
        }
    }
    cmd.push("-mailfrom".to_string());
    cmd.push(mail.from.clone());
    cmd.push("-mailto".to_string());
    cmd.push(mail.to.clone());
    cmd.push("-mailsubject".to_string());
    cmd.push(subject.to_string());
    if !mail.customer.is_empty() {
        cmd.push("-customer".to_string());
        cmd.push(mail.customer.clone());
    }
    cmd.push("-mailbodyfile".to_string());
    cmd.push(path.to_string_lossy().into_owned());

    let (rc, out) = engine::run_engine(&cmd);
    let _ = std::fs::remove_file(&path);
    let lower = out.to_lowercase();
    let ok = rc == 0 && !lower.contains("not sent");
    (ok, out)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn mail() -> MailConfig {
        MailConfig {
            enabled: true,
            server: "smtp.example.com".to_string(),
            port: "587".to_string(),
            tls: "starttls".to_string(),
            user: "user@example.com".to_string(),
            password: "secret".to_string(),
            from: "user@example.com".to_string(),
            to: "me@example.com".to_string(),
            customer: "Job".to_string(),
            heartbeat: false,
        }
    }

    #[test]
    fn not_ready_when_disabled() {
        let mut m = mail();
        m.enabled = false;
        let (ok, text) = send_text_report("zpaq", &m, "s", "body");
        assert!(!ok);
        assert!(text.contains("not configured"));
    }
}
