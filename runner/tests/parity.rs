





use rizpaq_task::{cmdline, log, naming, tasks};
use serde_json::Value;
use std::path::PathBuf;

fn fixtures_dir() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("tests")
        .join("fixtures")
}

fn load_fixture(name: &str) -> Option<Value> {
    let path = fixtures_dir().join(name);
    if !path.exists() {
        eprintln!("SKIP: фикстура {} не найдена — запустите gen_cmd_fixtures.py", name);
        return None;
    }
    let text = std::fs::read_to_string(&path).expect("читать фикстуру");
    Some(serde_json::from_str(&text).expect("парсить фикстуру"))
}

fn str_vec(v: &Value) -> Vec<String> {
    v.as_array()
        .expect("список строк")
        .iter()
        .map(|x| x.as_str().expect("строка").to_string())
        .collect()
}

#[test]
fn create_cmd_matches_python() {
    let Some(cases) = load_fixture("cmd_cases.json") else { return; };
    let mut checked = 0;
    for case in cases.as_array().expect("массив кейсов") {
        if case["kind"].as_str() != Some("create") {
            continue;
        }
        let name = case["name"].as_str().unwrap_or("?");
        let srcs = str_vec(&case["srcs"]);
        let dest = case["dest"].as_str().unwrap_or("");
        let password = case["password"].as_str();
        let expected = str_vec(&case["expected"]);
        let got = cmdline::build_create_cmd(
            case["zpaq"].as_str().unwrap_or(""),
            &case["settings"],
            &srcs,
            dest,
            password,
        );
        assert_eq!(got, expected, "create-кейс {}", name);
        
        
        let expected_line = case["expected_cmdline"].as_str().unwrap_or("");
        let got_line = log::safe_cmdline(&got, password);
        assert_eq!(got_line, expected_line, "cmdline create-кейса {}", name);
        checked += 1;
    }
    assert!(checked > 0, "в фикстурах нет create-кейсов");
}

#[test]
fn test_cmd_matches_python() {
    let Some(cases) = load_fixture("cmd_cases.json") else { return; };
    let mut checked = 0;
    for case in cases.as_array().expect("массив кейсов") {
        if case["kind"].as_str() != Some("test") {
            continue;
        }
        let name = case["name"].as_str().unwrap_or("?");
        let dest = case["dest"].as_str().unwrap_or("");
        let password = case["password"].as_str();
        let test_mode = case["test_mode"].as_str();
        let tmp_dir = case["tmp_dir"].as_str();
        let expected = str_vec(&case["expected"]);
        let got = cmdline::build_test_cmd(
            case["zpaq"].as_str().unwrap_or(""),
            dest,
            password,
            test_mode,
            tmp_dir,
        );
        assert_eq!(got, expected, "test-кейс {}", name);
        checked += 1;
    }
    assert!(checked > 0, "в фикстурах нет test-кейсов");
}

#[test]
fn container_normalization_matches_python() {
    let Some(case) = load_fixture("container_case.json") else { return; };
    let expected = case["expected"].clone();
    let got = tasks::validate(&case["raw"])
        .expect("Python-эталон должен проходить валидацию");
    assert_eq!(got, expected, "нормализация контейнера");

    
    let job_id = case["job_id"].as_str().expect("job_id");
    let (work, job) = tasks::find_job(&got, job_id)
        .unwrap_or_else(|| panic!("задание {} не найдено в нормализованном контейнере", job_id));
    let got_settings = tasks::job_to_runnable_settings(work, job);
    assert_eq!(
        got_settings, case["expected_settings"],
        "job_to_runnable_settings для {}",
        job_id
    );
}

#[test]
fn foreign_container_becomes_empty() {
    
    
    let bad = serde_json::json!({"format": "nope", "works": []});
    let got = tasks::validate(&bad);
    assert!(got.is_none(), "чужой format должен давать None");

    let got = tasks::load_container(PathBuf::from("Z:/no/such/file.rzp").as_path());
    assert_eq!(got["format"].as_str(), Some("rizpaq.tasks"));
    assert_eq!(got["version"].as_i64(), Some(1));
    assert_eq!(got["works"].as_array().map(|a| a.len()), Some(0));
    assert!(got["created"].is_string());
}

#[test]
fn transliteration_matches_reference() {
    
    assert!(!naming::has_non_latin("plain-zpaq.1"));
    assert!(naming::has_non_latin("архив"));
    assert_eq!(naming::transliterate("Архив-2026"), "arhiv-2026");
    assert_eq!(naming::transliterate("Ёлка Жучок"), "yolka zhuchok");
    assert_eq!(naming::transliterate("汉 Ω"), " "); 
    assert_eq!(naming::transliterate("a_b_"), "a_b_"); 
}
