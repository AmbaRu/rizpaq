
















#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use rizpaq_task::{cfg, cmdline, engine, errlog, index, log, naming, par2, pwstore, tasks, util};
use serde_json::Value;
use std::path::{Path, PathBuf};

const ACTION_TEST: &str = "test";

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

    if action != ACTION_TEST && srcs.is_empty() {
        
        let header = log::build_log_header(&rzp_path, work, job, 1, None, None);
        log::write_task_log(&rzp_path, &header, "No sources specified in job.", "full", 1, false, "");
        return 1;
    }

    let dest0 = tasks::py_str(settings.get("dest").unwrap_or(&Value::Null));
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
    let log_mode = settings
        .get("task_log_mode")
        .and_then(Value::as_str)
        .unwrap_or("short")
        .to_string();

    
    
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

    
    let test_mode_raw = settings
        .get("test_mode")
        .and_then(Value::as_str)
        .unwrap_or("full");
    let test_mode = test_mode_raw.trim().to_lowercase();
    let par2_mode = action == ACTION_TEST && test_mode == "par2";

    let mut tmp_dir: Option<PathBuf> = None;
    let mut cmd: Option<Vec<String>> = None;
    let mut par2_note = String::new();
    
    let mut par2_reason: Option<&'static str> = None;

    let (rc, mut log_out, ok): (i32, String, bool);

    if par2_mode {
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
            ));
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

        let (r, l) = engine::run_engine(cmd.as_deref().unwrap());
        rc = r;
        log_out = l;
        ok = rc == 0;

        if let Some(d) = tmp_dir {
            let _ = std::fs::remove_dir_all(d);
        }
    }

    if !rename_note.is_empty() {
        log_out = format!("{}{}", rename_note, log_out);
    }

    let busy = !ok && engine::looks_like_busy_error(&log_out);

    let status = if ok {
        "ok"
    } else if busy {
        "busy"
    } else {
        "error"
    };
    {
        let jid = job_id.clone();
        let reason: Option<&str> = par2_reason;
        let _ = tasks::update_container(Path::new(&rzp_path), |c| {
            tasks::update_job_meta(c, &jid, status, reason);
        });
    }

    if ok {
        if let Some(p) = password {
            pwstore::set_password(&dest, Some(p));
        }
    }

    if ok && action != ACTION_TEST && tasks::py_truthy(settings.get("par2_enabled")) {
        par2_note = par2::headless_par2_create(&rzp_path, work, &dest, &settings);
    }

    if ok && action != ACTION_TEST {
        index::refresh_index_sync(&zpaq, &dest, password);
    }

    let log_header =
        log::build_log_header(&rzp_path, work, job, rc, password, cmd.as_deref());
    log::write_task_log(&rzp_path, &log_header, &log_out, &log_mode, rc, busy, &par2_note);

    if !ok && !busy {
        errlog::append_raw(&format!("{}\n{}\n\n", log_header, log_out));
    }

    if ok {
        0
    } else {
        1
    }
}
