


use chrono::Local;
use std::path::{Path, PathBuf};


pub fn has_non_latin(name: &str) -> bool {
    name.chars().any(|c| !c.is_ascii())
}


fn translit_char(c: char) -> Option<&'static str> {
    let s = match c {
        'а' => "a",
        'б' => "b",
        'в' => "v",
        'г' => "g",
        'д' => "d",
        'е' => "e",
        'ё' => "yo",
        'ж' => "zh",
        'з' => "z",
        'и' => "i",
        'й' => "y",
        'к' => "k",
        'л' => "l",
        'м' => "m",
        'н' => "n",
        'о' => "o",
        'п' => "p",
        'р' => "r",
        'с' => "s",
        'т' => "t",
        'у' => "u",
        'ф' => "f",
        'х' => "h",
        'ц' => "ts",
        'ч' => "ch",
        'ш' => "sh",
        'щ' => "sch",
        'ъ' => "",
        'ы' => "y",
        'ь' => "",
        'э' => "e",
        'ю' => "yu",
        'я' => "ya",
        _ => return None,
    };
    Some(s)
}

pub fn transliterate(name: &str) -> String {
    let mut out = String::new();
    for ch in name.to_lowercase().chars() {
        if let Some(rep) = translit_char(ch) {
            out.push_str(rep);
        } else if ch.is_ascii() && (ch.is_ascii_alphanumeric() || ch == '.' || ch == '-') {
            out.push(ch);
        } else if !ch.is_ascii() {
        } else {
            out.push(ch);
        }
    }
    out
}

pub fn make_latin_name(dest: &str) -> PathBuf {
    let p = Path::new(dest);
    let stem = p.file_stem().and_then(|s| s.to_str()).unwrap_or("");
    let suffix = match p.extension() {
        Some(e) if !e.is_empty() => format!(".{}", e.to_string_lossy()),
        _ => ".zpaq".to_string(),
    };
    let mut latin_stem = transliterate(stem);
    latin_stem = latin_stem
        .split('_')
        .filter(|part| !part.is_empty())
        .collect::<Vec<_>>()
        .join("_");
    if latin_stem.len() < 2 {
        latin_stem = format!("archive_{}", Local::now().format("%Y%m%d_%H%M%S"));
    }
    let parent = p.parent().unwrap_or(Path::new(""));
    let mut new_dest = parent.join(format!("{}{}", latin_stem, suffix));
    if avoid_existing(&new_dest) {
        let mut counter = 1;
        while new_dest.exists() {
            new_dest = parent.join(format!("{}_{}{}", latin_stem, counter, suffix));
            counter += 1;
        }
    }
    new_dest
}

fn avoid_existing(_p: &Path) -> bool {
    true
}
