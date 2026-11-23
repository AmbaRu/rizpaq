
use rizpaq_task::{engine, restore, util};
use std::path::{Path, PathBuf};

fn engine_path() -> Option<PathBuf> {
    let p = Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()?
        .join("zpaqfranz.exe");
    p.is_file().then_some(p)
}

fn run(zpaq: &str, args: &[&str]) -> (i32, String) {
    let mut cmd = vec![zpaq.to_string()];
    cmd.extend(args.iter().map(|s| s.to_string()));
    engine::run_engine(&cmd)
}

#[test]
fn real_restore_drill_succeeds() {
    let Some(zpaq_path) = engine_path() else {
        eprintln!("skip: zpaqfranz.exe not found next to runner/");
        return;
    };
    let zpaq = zpaq_path.to_string_lossy().into_owned();
    let Some(root) = util::make_tmp_dir("rizpaq_restore_e2e_") else {
        panic!("cannot create temp folder");
    };
    let data = root.join("data");
    std::fs::create_dir_all(&data).unwrap();
    let file = data.join("a.txt");
    let archive = root.join("probe.zpaq");
    let arc = archive.to_string_lossy().into_owned();
    let src = data.to_string_lossy().into_owned();

    for (i, text) in ["first", "second", "third"].iter().enumerate() {
        std::fs::write(&file, format!("version {}", text)).unwrap();
        std::thread::sleep(std::time::Duration::from_millis(1100 * i as u64));
        let (rc, out) = run(&zpaq, &["a", &arc, &src, "-m5"]);
        assert_eq!(rc, 0, "archive creation failed: {}", out);
    }

    let (ok, log) = restore::run_restore_drill(&zpaq, &arc, None, &[src]);
    println!("{}", log);
    let _ = std::fs::remove_dir_all(&root);
    assert!(ok, "restore drill must succeed on a healthy archive: {}", log);
    assert!(log.contains("OK"));
}
