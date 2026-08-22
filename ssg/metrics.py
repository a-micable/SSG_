from typing import Dict

EXT_LANGUAGE_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".java": "Java",
    ".go": "Go",
    ".rb": "Ruby",
    ".php": "PHP",
    ".rs": "Rust",
    ".c": "C",
    ".cpp": "C++",
    ".h": "C/C++ Header",
    ".md": "Markdown",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".json": "JSON",
    ".html": "HTML",
    ".css": "CSS",
}


NORMALIZE_LANG = {
    "py": "Python",
    "python": "Python",
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "java": "Java",
    "go": "Go",
    "rb": "Ruby",
    "ruby": "Ruby",
    "php": "PHP",
    "rust": "Rust",
    "c": "C",
    "c++": "C++",
    "c/c++": "C/C++",
    "markdown": "Markdown",
    "md": "Markdown",
    "toml": "TOML",
    "txt": "Text",
    "sample": "Sample",
    "tag": "Tag",
    "example": "Example",
    "jsx": "JSX",
    "yaml": "YAML",
    "json": "JSON",
    "html": "HTML",
    "css": "CSS",
}


def languages_from_ext(files_by_ext: Dict[str, int]) -> Dict[str, int]:
    result = {}
    for ext, count in files_by_ext.items():
        lang = EXT_LANGUAGE_MAP.get(ext, ext.lstrip(".") or "other")
        result[lang] = result.get(lang, 0) + count
    return result


def loc_summary(loc_by_ext: Dict[str, int]) -> Dict[str, int]:
    result = {}
    for ext, loc in loc_by_ext.items():
        lang = EXT_LANGUAGE_MAP.get(ext, ext.lstrip(".") or "other")
        result[lang] = result.get(lang, 0) + loc
    return result


def normalize_language_key(key: str) -> str:
    if not key:
        return "Other"
    k = key.strip().lower()
    return NORMALIZE_LANG.get(k, key.title())


def languages_from_lang(files_by_lang: Dict[str, int]) -> Dict[str, int]:
    result: Dict[str, int] = {}
    for key, count in files_by_lang.items():
        lang = normalize_language_key(key)
        result[lang] = result.get(lang, 0) + count
    return result


def loc_summary_from_lang(loc_by_lang: Dict[str, int]) -> Dict[str, int]:
    result: Dict[str, int] = {}
    for key, loc in loc_by_lang.items():
        lang = normalize_language_key(key)
        result[lang] = result.get(lang, 0) + loc
    return result
