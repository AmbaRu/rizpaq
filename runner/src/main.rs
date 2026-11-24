
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use rizpaq_task::{
    cfg, cmdline, copy, engine, errlog, index, log, mail, naming, notify, par2, pwstore, restore, retention, tasks, util,
};
use serde_json::Value;
use std::path::{Path, PathBuf};

const ACTION_TEST: &str = "test";
const ACTION_BACKUP: &str = "backup";
const ACTION_CROP: &str = "crop";
const ACTION_CONSOLIDATE: &str = "consolidate";

fn main() {
    let args: Vec<String> = std::env::args_os()
        .skip(1)
        .map(|s| s.to_string_lossy().into_owned())
        .collect();
    let rest: &[String] =
        if args.first().map(|s| s.trim() == "--task").unwrap_or(false) {
            &args[1..]
        } else {
            &args
        };
    std::process::exit(run(rest));
}

fn unsupported_action(action: &str) -> bool {
    action != ACTION_BACKUP
        && action != ACTION_TEST
        && action != ACTION_CROP
        && action != ACTION_CONSOLIDATE
}

fn need_par2_for_action(action: &str) -> bool {
    action == ACTION_BACKUP || action == ACTION_CROP
}

fn engine_success(rc: i32, action: &str) -> bool {
    rc == 0 || (rc == 1 && action == ACTION_BACKUP)
}

fn py_str_or_empty(v: Option<&Value>) -> String {
    if tasks::py_truthy(v) {
        tasks::py_str(v.unwrap())
    } else {
        String::new()
    }
}

fn py_repr_str(s: &str) -> String {
    let mut out = String::from("'");
    for c in s.chars() {
        match c {
            '\\' => out.push_str("\\\\"),
            '\'' => out.push_str("\\'"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if (c as u32) < 0x20 => out.push_str(&format!("\\x{:02x}", c as u32)),
            c => out.push(c),
        }
    }
    out.push('\'');
    out
}

fn py_repr_list(items: &[String]) -> String {
    let inner: Vec<String> = items.iter().map(|s| py_repr_str(s)).collect();
    format!("[{}]", inner.join(", "))
}

fn parse_task_args(rest: &[String]) -> (String, String) {
    if rest.is_empty() {
        return (String::new(), String::new());
    }
    let rzp_path = rest[0].trim().to_string();
    let mut job_id = String::new();
    let mut i = 1;
    while i < rest.len() {
        let arg = rest[i].trim();
        if arg == "--job" && i + 1 < rest.len() {
            job_id = rest[i + 1].trim().to_string();
            break;
        }
        i += 1;
    }
    (rzp_path, job_id)
}

fn has_task_flag(rest: &[String], flag: &str) -> bool {
    let target = flag.trim().to_lowercase();
    if target.is_empty() {
        return false;
    }
    rest.iter().any(|arg| arg.trim().to_lowercase() == target)
}

fn precheck_decision(rc: i32) -> &'static str {
    match rc {
        0 => "skip",
        2 => "run",
        _ => "error",
    }
}

fn precheck_blocked_reason(settings: &Value, dest: &str) -> String {
    let has = |key: &str| -> bool {
        match settings.get(key) {
            Some(Value::Array(a)) => !a.is_empty(),
            Some(Value::String(s)) => !s.trim().is_empty(),
            _ => false,
        }
    };
    if has("only_masks") || has("not_masks") {
        return "the work uses include/exclude masks".to_string();
    }
    if has("chunk") {
        return "the job writes a multi-volume archive".to_string();
    }
    if dest.contains('?') {
        return "the archive is multi-volume".to_string();
    }
    String::new()
}

fn archive_is_empty(path: &str) -> bool {
    match std::fs::metadata(path) {
        Ok(meta) => meta.is_file() && meta.len() == 0,
        Err(_) => false,
    }
}

fn continuous_precheck(
    zpaq: &str,
    dest: &str,
    password: Option<&str>,
    sources: &[String],
) -> (&'static str, i32, String, Vec<String>) {
    let cmd = cmdline::build_test_cmd(
        zpaq,
        dest,
        password,
        Some("sync"),
        None,
        sources,
    );
    let (rc, log) = engine::run_engine(&cmd);
    (precheck_decision(rc), rc, log, cmd)
}

fn zpaq_bin() -> String {
    if let Ok(z) = std::env::var("ZPAQ_BIN") {
        if !z.is_empty() {
            return z;
        }
    }
    if let Some(p) = cfg::config_zpaq_path() {
        if p.is_file() {
            return p.to_string_lossy().into_owned();
        }
    }
    "zpaqfranz".to_string()
}

fn run(rest: &[String]) -> i32 {
    let (rzp_path, job_id) = parse_task_args(rest);
    let if_changed = has_task_flag(rest, "--if-changed");
    if rzp_path.is_empty() {
        errlog::write_temp_error(&format!(
            "Rizpaq: --task без пути к контейнеру. Аргументы: {}\n",
            py_repr_list(rest)
        ));
        return 1;
    }
    if job_id.is_empty() {
        errlog::write_temp_error(&format!(
            "Rizpaq: --task без --job. Файл: {}. Аргументы: {}\n",
            rzp_path,
            py_repr_list(rest)
        ));
        return 1;
    }

    let container = tasks::load_container(Path::new(&rzp_path));

    let Some((work, job)) = tasks::find_job(&container, &job_id) else {
        errlog::write_temp_error(&format!(
            "Rizpaq: в контейнере {} нет задания с id={}. Возможно, контейнер отредактировали после регистрации задачи в Планировщике, и запись указывает на устаревший id.\n",
            rzp_path,
            py_repr_str(&job_id)
        ));
        return 1;
    };

    let settings = tasks::job_to_runnable_settings(work, job);

    let action = settings
        .get("action")
        .and_then(Value::as_str)
        .unwrap_or("backup")
        .trim()
        .to_lowercase();

    let srcs: Vec<String> = settings
        .get("sources")
        .and_then(Value::as_array)
        .map(|a| {
            a.iter()
                .map(tasks::py_str)
                .collect::<Vec<String>>()
        })
        .unwrap_or_default();

    let test_mode_raw = settings
        .get("test_mode")
        .and_then(Value::as_str)
        .unwrap_or("full");
    let test_mode = test_mode_raw.trim().to_lowercase();

    let log_mode = settings
        .get("task_log_mode")
        .and_then(Value::as_str)
        .unwrap_or("short")
        .to_string();

    if unsupported_action(&action) {
        let text = format!(
            "Rizpaq: job type '{}' is not supported by the headless runner. \
             Run this job from the program window, or use a backup/check job.\n",
            action
        );
        errlog::write_temp_error(&text);
        let header = log::build_log_header(&rzp_path, work, job, 1, None, None);
        log::write_task_log(&rzp_path, &header, &text, &log_mode, 1, false, "");
        return 1;
    }

    if action != ACTION_TEST && srcs.is_empty() {
        let header = log::build_log_header(&rzp_path, work, job, 1, None, None);
        log::write_task_log(&rzp_path, &header, "No sources specified in job.", "full", 1, false, "");
        return 1;
    }
    if action == ACTION_TEST && test_mode == "sync" && srcs.is_empty() {
        let header = log::build_log_header(&rzp_path, work, job, 1, None, None);
        log::write_task_log(&rzp_path, &header, "No sources specified for sync.", "full", 1, false, "");
        return 1;
    }

    let dest0 = py_str_or_empty(settings.get("dest"));
    if !tasks::py_truthy(settings.get("dest")) {
        let header = log::build_log_header(&rzp_path, work, job, 1, None, None);
        log::write_task_log(&rzp_path, &header, "No destination specified in job.", "full", 1, false, "");
        return 1;
    }

    let password = settings
        .get("password")
        .and_then(Value::as_str)
        .filter(|p| !p.is_empty());
    let zpaq = zpaq_bin();

    let mut dest = dest0;
    let mut rename_note = String::new();
    {
        let p = Path::new(&dest);
        let stem = p.file_stem().and_then(|s| s.to_str()).unwrap_or("");
        if naming::has_non_latin(stem) && !dest.contains('?') {
            let old_name = p.file_name().and_then(|s| s.to_str()).unwrap_or("");
            let new_dest = naming::make_latin_name(&dest);
            rename_note = format!(
                "\n[rizpaq] destination renamed for engine compatibility: '{}' -> '{}'\n",
                old_name,
                new_dest.file_name().and_then(|s| s.to_str()).unwrap_or("")
            );
            dest = new_dest.to_string_lossy().into_owned();
        }
    }

    let mut skip_run = false;
    let mut skip_note = String::new();
    let mut pre_rc: Option<i32> = None;
    let mut pre_log = String::new();
    let mut pre_cmd: Option<Vec<String>> = None;
    let mut sync_failed = false;
    if if_changed && action == ACTION_BACKUP {
        let blocked = precheck_blocked_reason(&settings, &dest);
        if !blocked.is_empty() {
            skip_note = format!("\n[rizpaq] precheck skipped: {}\n", blocked);
        } else if Path::new(&dest).is_file() {
            let (decision, rc0, log0, cmd0) =
                continuous_precheck(&zpaq, &dest, password, &srcs);
            pre_rc = Some(rc0);
            pre_log = log0;
            pre_cmd = Some(cmd0);
            if decision == "skip" {
                skip_run = true;
                skip_note =
                    "\n[rizpaq] no changes since the last backup, backup skipped\n"
                        .to_string();
            } else if decision == "error" {
                if !archive_is_empty(&dest) {
                    skip_run = true;
                    sync_failed = true;
                    skip_note =
                        "\n[rizpaq] sync precheck failed, backup not started\n"
                            .to_string();
                }
            }
        }
    }

    let par2_mode = action == ACTION_TEST && test_mode == "par2";
    let restore_mode = action == ACTION_TEST && test_mode == "restore";
    let mut extra_ok = true;
    let mut extra_note = String::new();
    let mut mail_note = String::new();

    let mut tmp_dir: Option<PathBuf> = None;
    let mut cmd: Option<Vec<String>> = None;
    let mut par2_note = String::new();
    let mut par2_reason: Option<&'static str> = None;

    let (mut rc, mut log_out, mut ok): (i32, String, bool) =
        (0, String::new(), false);

    if skip_run {
        cmd = pre_cmd;
        rc = pre_rc.unwrap_or(1);
        log_out = pre_log;
        ok = rc == 0;
    } else if restore_mode {
        let (r, l) = restore::run_restore_drill(&zpaq, &dest, password, &srcs);
        rc = if r { 0 } else { 1 };
        log_out = l;
        ok = r;
    } else if par2_mode {
        let (r, l, state) = par2::headless_par2_verify(&dest);
        rc = r;
        log_out = l.clone();
        par2_note = l;
        ok = state == par2::STATE_OK;
        if !ok {
            par2_reason = Some(par2::reason_by_state(state));
        }
    } else {
        if action == ACTION_TEST {
            if test_mode == "paranoid" {
                tmp_dir = util::make_tmp_dir("rizpaq_task_test_");
            }
            let tmp_arg: Option<String> = tmp_dir
                .as_ref()
                .map(|p| p.to_string_lossy().into_owned());
            cmd = Some(cmdline::build_test_cmd(
                &zpaq,
                &dest,
                password,
                Some(&test_mode),
                tmp_arg.as_deref(),
                &srcs,
            ));
        } else if action == ACTION_CONSOLIDATE {
            if !dest.contains('?') {
                rc = 1;
                log_out = "concatenate requires a multipart archive\n".to_string();
                ok = false;
                cmd = None;
            } else {
                let p = Path::new(&dest);
                let stem = p
                    .file_stem()
                    .and_then(|s| s.to_str())
                    .unwrap_or("merged")
                    .replace("_????", "")
                    .replace("????", "")
                    .trim_end_matches('_')
                    .to_string();
                let stem = if stem.is_empty() { "merged".to_string() } else { stem };
                let default_out = p.with_file_name(format!("{}.zpaq", stem));
                let out = py_str_or_empty(settings.get("consolidate_output"));
                let out = if out.trim().is_empty() {
                    default_out.to_string_lossy().into_owned()
                } else {
                    out
                };
                cmd = Some(vec![
                    zpaq.clone(),
                    "m".to_string(),
                    dest.clone(),
                    out.clone(),
                    "-verify".to_string(),
                ]);
                if Path::new(&out).exists() {
                    cmd.as_mut().unwrap().push("-force".to_string());
                }
            }
        } else if action == ACTION_CROP {
            let policy = py_str_or_empty(settings.get("retention_policy"));
            let policy = if policy.trim().is_empty() {
                retention::DEFAULT_POLICY.to_string()
            } else {
                policy
            };
            let (crop_ok, crop_text) = retention::run_apply(
                &zpaq, &dest, &policy, password,
            );
            rc = if crop_ok { 0 } else { 1 };
            log_out = crop_text;
            ok = crop_ok;
            cmd = None;
        } else {
            if tasks::py_truthy(settings.get("chunk")) && !dest.contains('?') {
                let p = Path::new(&dest);
                let stem = p
                    .file_stem()
                    .and_then(|s| s.to_str())
                    .unwrap_or("")
                    .to_string();
                let suffix = match p.extension() {
                    Some(e) if !e.is_empty() => format!(".{}", e.to_string_lossy()),
                    _ => ".zpaq".to_string(),
                };
                let joined = match p.parent() {
                    Some(parent)
                        if !parent.as_os_str().is_empty() && parent != Path::new(".") =>
                    {
                        parent.join(format!("{}_????{}", stem, suffix))
                    }
                    _ => PathBuf::from(format!("{}_????{}", stem, suffix)),
                };
                dest = joined.to_string_lossy().into_owned();
            }
            cmd = Some(cmdline::build_create_cmd(&zpaq, &settings, &srcs, &dest, password));
        }

        if let Some(c) = cmd.as_deref() {
            let (r, l) = engine::run_engine(c);
            rc = r;
            log_out = l;
            ok = engine_success(rc, &action);
        }

        if let Some(d) = tmp_dir {
            let _ = std::fs::remove_dir_all(d);
        }
    }

    let mut copy_failed = false;
    let mut copy_note = String::new();
    let mut copy_reason: Option<&'static str> = None;
    let copy_dir = py_str_or_empty(settings.get("copy")).trim().to_string();
    if action == ACTION_BACKUP && ok && !skip_run && !copy_dir.is_empty() {
        let (copy_ok, copy_text) = copy::copy_archive(&dest, &copy_dir);
        if copy_ok {
            if !copy_text.is_empty() {
                copy_note = format!("\n[rizpaq] second copy: {}\n", copy_text);
            }
        } else {
            copy_failed = true;
            copy_reason = Some("copy_failed");
            copy_note = format!("\n[rizpaq] second copy failed: {}\n", copy_text);
            rc = 1;
        }
    }

    if !rename_note.is_empty() {
        log_out = format!("{}{}", rename_note, log_out);
    }

    let busy = !ok && !skip_run && engine::looks_like_busy_error(&log_out);

    if ok && !skip_run {
        if let Some(p) = password {
            pwstore::set_password(&dest, Some(p));
        }
    }

    let mut verify_note = String::new();
    if ok && !skip_run && action == ACTION_BACKUP {
        let vm = py_str_or_empty(settings.get("verify")).trim().to_lowercase();
        if matches!(vm.as_str(), "full" | "checksum" | "verify" | "paranoid") {
            let vtmp = if vm == "paranoid" {
                util::make_tmp_dir("rizpaq_task_verify_")
            } else {
                None
            };
            let tmp_arg = vtmp.as_ref().map(|p| p.to_string_lossy().into_owned());
            let vcmd = cmdline::build_test_cmd(
                &zpaq, &dest, password, Some(&vm), tmp_arg.as_deref(), &srcs,
            );
            let (vrc, vout) = engine::run_engine(&vcmd);
            verify_note = format!(
                "\n[verify after create] mode={} rc={}\n{}\n",
                vm, vrc, vout.trim()
            );
            log_out.push_str(&verify_note);
            if let Some(d) = vtmp {
                let _ = std::fs::remove_dir_all(d);
            }
        }
    }

    if ok && !skip_run && need_par2_for_action(&action)
        && tasks::py_truthy(settings.get("par2_enabled")) {
        let (par2_ok, note) =
            par2::headless_par2_create(&rzp_path, work, &dest, &settings);
        par2_note = note;
        if !par2_ok {
            ok = false;
            par2_reason = Some("par2_failed");
        }
    }

    if ok && !skip_run && action != ACTION_TEST {
        index::refresh_index_sync(&zpaq, &dest, password);
    }

    if ok && !skip_run && action == ACTION_BACKUP {
        if let Some(arr) = settings.get("extra_dests").and_then(Value::as_array) {
            let mut seen: Vec<String> = vec![dest.clone()];
            for raw in arr {
                let extra = py_str_or_empty(Some(raw)).trim().to_string();
                if extra.is_empty() || seen.contains(&extra) {
                    continue;
                }
                seen.push(extra.clone());
                let extra_cmd =
                    cmdline::build_create_cmd(&zpaq, &settings, &srcs, &extra, password);
                let (r, l) = engine::run_engine(&extra_cmd);
                let mut step_ok = engine_success(r, &action);
                extra_ok = extra_ok && step_ok;
                let block = format!("\n[extra archive] {}\n{}\n", extra, l);
                extra_note.push_str(&block);
                log_out.push_str(&block);

                if step_ok && !copy_dir.is_empty() {
                    let (copy_ok, copy_text) = copy::copy_archive(&extra, &copy_dir);
                    let note = format!(
                        "[extra copy] {}: {}\n",
                        if copy_ok { "OK" } else { "FAIL" }, copy_text
                    );
                    extra_note.push_str(&note);
                    log_out.push_str(&note);
                    if !copy_ok {
                        extra_ok = false;
                        continue;
                    }
                }
                if step_ok && tasks::py_truthy(settings.get("par2_enabled")) {
                    let extra_work = par2::extra_par2_work(&extra);
                    let (set_ok, note) = par2::headless_par2_create(
                        &rzp_path, &extra_work, &extra, &settings,
                    );
                    extra_note.push_str(&note);
                    log_out.push_str(&note);
                    if !set_ok {
                        extra_ok = false;
                        step_ok = false;
                    }
                }
                if step_ok {
                    index::refresh_index_sync(&zpaq, &extra, password);
                }
            }
        }
    }

    if !skip_run && (action == ACTION_BACKUP || action == ACTION_TEST) {
        if let Some(mail) = cfg::mail_config() {
            if mail.ready() {
                let job_title = py_str_or_empty(job.get("title"));
                let customer = if mail.customer.is_empty() {
                    job_title.clone()
                } else {
                    mail.customer.clone()
                };
                let state = if ok && extra_ok && !copy_failed {
                    "OK"
                } else {
                    "ERROR"
                };
                let subject = format!("{} {} FULL", state, customer);
                let body = format!(
                    "Archive: {}\nStatus: {}\n\n{}{}{}{}",
                    dest,
                    state,
                    log_out,
                    copy_note,
                    par2_note,
                    extra_note
                );
                let (sent, out) = mail::send_text_report(
                    &zpaq, &mail, &subject, &body,
                );
                mail_note = if sent {
                    "\n[rizpaq] email report sent\n".to_string()
                } else {
                    format!("\n[rizpaq] email report NOT sent: {}\n", out)
                };
            }
        }
    }

    let status = if ok && !copy_failed && extra_ok {
        "ok"
    } else if busy {
        "busy"
    } else {
        "error"
    };
    {
        let jid = job_id.clone();
        let reason: Option<&str> = if sync_failed {
            Some("sync_failed")
        } else {
            par2_reason.or(copy_reason)
        };
        let _ = tasks::update_container(Path::new(&rzp_path), |c| {
            tasks::update_job_meta(c, &jid, status, reason);
        });
    }

    rc = log::final_rc(status, rc);
    let log_header =
        log::build_log_header(&rzp_path, work, job, rc, password, cmd.as_deref());
    let task_note = format!(
        "{}{}{}{}{}{}", skip_note, copy_note, verify_note, par2_note, extra_note, mail_note
    );
    log::write_task_log(
        &rzp_path,
        &log_header,
        &log_out,
        &log_mode,
        rc,
        busy,
        &task_note,
    );

    if !ok && !busy {
        errlog::append_raw(&format!("{}\n{}\n\n", log_header, log_out));
    }

    if !(skip_run && ok) {
        notify::notify_job(
            &py_str_or_empty(work.get("title")),
            &py_str_or_empty(job.get("title")),
            status,
            if sync_failed {
                Some("sync_failed")
            } else {
                par2_reason.or(copy_reason)
            },
            &dest,
        );
    }

    if ok && !copy_failed && extra_ok {
        0
    } else {
        1
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn args(items: &[&str]) -> Vec<String> {
        items.iter().map(|s| s.to_string()).collect()
    }

    #[test]
    fn has_task_flag_finds_flag_anywhere() {
        assert!(has_task_flag(
            &args(&[r"C:\tasks\t.rzp", "--job", "j1", "--if-changed"]),
            "--if-changed"
        ));
    }

    #[test]
    fn has_task_flag_is_case_insensitive() {
        assert!(has_task_flag(&args(&["--IF-CHANGED"]), "--if-changed"));
    }

    #[test]
    fn has_task_flag_ignores_whitespace() {
        assert!(has_task_flag(
            &args(&["  --if-changed  "]),
            "--if-changed"
        ));
    }

    #[test]
    fn has_task_flag_rejects_missing_and_empty() {
        assert!(!has_task_flag(&[], "--if-changed"));
        assert!(!has_task_flag(&args(&["--job", "j1"]), "--if-changed"));
        assert!(!has_task_flag(&args(&["--if-changed"]), ""));
        assert!(!has_task_flag(&args(&["--if-changed"]), "   "));
    }

    #[test]
    fn has_task_flag_requires_exact_match() {
        assert!(!has_task_flag(&args(&["--if-changed=1"]), "--if-changed"));
        assert!(!has_task_flag(
            &args(&[r"C:\--if-changed"]),
            "--if-changed"
        ));
    }

    #[test]
    fn precheck_zero_means_skip() {
        assert_eq!(precheck_decision(0), "skip");
    }

    #[test]
    fn precheck_two_means_run() {
        assert_eq!(precheck_decision(2), "run");
    }

    #[test]
    fn precheck_other_codes_mean_error() {
        for rc in [1, 3, 128, -1] {
            assert_eq!(precheck_decision(rc), "error", "rc={rc}");
        }
    }

    #[test]
    fn py_str_or_empty_maps_python_falsy_values() {
        assert_eq!(py_str_or_empty(None), "");
        assert_eq!(py_str_or_empty(Some(&serde_json::Value::Null)), "");
        assert_eq!(py_str_or_empty(Some(&serde_json::json!(0))), "");
        assert_eq!(py_str_or_empty(Some(&serde_json::json!(false))), "");
        assert_eq!(py_str_or_empty(Some(&serde_json::json!("Job"))), "Job");
    }

    #[test]
    fn par2_is_not_attempted_after_volume_merge() {
        assert!(need_par2_for_action("backup"));
        assert!(need_par2_for_action("crop"));
        assert!(!need_par2_for_action("consolidate"));
        assert!(!need_par2_for_action("test"));
    }

    #[test]
    fn runner_rejects_unported_actions() {
        assert!(!unsupported_action("backup"));
        assert!(!unsupported_action("test"));
        assert!(!unsupported_action("crop"));
        assert!(!unsupported_action("consolidate"));
        for action in [
            "sfx",
            "sfx",
            "info",
            "password",
            "checkpassword",
        ] {
            assert!(unsupported_action(action), "{action} должен быть отклонён");
        }
    }

    #[test]
    fn empty_archive_is_detected() {
        let dir = std::env::temp_dir().join("rizpaq_empty_archive_test");
        let _ = std::fs::create_dir_all(&dir);
        let path = dir.join("empty.zpaq");
        std::fs::write(&path, b"").unwrap();
        assert!(archive_is_empty(path.to_str().unwrap()));
        std::fs::write(&path, b"data").unwrap();
        assert!(!archive_is_empty(path.to_str().unwrap()));
        let missing = dir.join("missing.zpaq");
        assert!(!archive_is_empty(missing.to_str().unwrap()));
        let _ = std::fs::remove_dir_all(&dir);
    }

    #[test]
    fn precheck_is_blocked_for_masks_and_multivolume() {
        let plain = serde_json::json!({});
        assert_eq!(precheck_blocked_reason(&plain, r"D:\arc\arc.zpaq"), "");

        let only = serde_json::json!({"only_masks": ["*.txt"]});
        assert!(precheck_blocked_reason(&only, r"D:\arc\arc.zpaq").contains("masks"));

        let not = serde_json::json!({"not_masks": ["*.tmp"]});
        assert!(precheck_blocked_reason(&not, r"D:\arc\arc.zpaq").contains("masks"));

        let chunk = serde_json::json!({"chunk": "100m"});
        assert!(precheck_blocked_reason(&chunk, r"D:\arc\arc.zpaq").contains("multi-volume"));

        assert!(precheck_blocked_reason(&plain, r"D:\arc\arc_????.zpaq")
            .contains("multi-volume"));
    }
}
