from typing import Dict

EXT_LANGUAGE_MAP = {
    '.py': 'Python',
    '.js': 'JavaScript',
    '.ts': 'TypeScript',
    '.java': 'Java',
    '.go': 'Go',
    '.rb': 'Ruby',
    '.php': 'PHP',
    '.rs': 'Rust',
    '.c': 'C',
    '.cpp': 'C++',
    '.h': 'C/C++ Header',
    '.md': 'Markdown',
    '.yml': 'YAML',
    '.yaml': 'YAML',
    '.json': 'JSON',
    '.html': 'HTML',
    '.css': 'CSS',
}


def languages_from_ext(files_by_ext: Dict[str, int]) -> Dict[str, int]:
    result = {}
    for ext, count in files_by_ext.items():
        lang = EXT_LANGUAGE_MAP.get(ext, ext.lstrip('.') or 'other')
        result[lang] = result.get(lang, 0) + count
    return result


def loc_summary(loc_by_ext: Dict[str, int]) -> Dict[str, int]:
    result = {}
    for ext, loc in loc_by_ext.items():
        lang = EXT_LANGUAGE_MAP.get(ext, ext.lstrip('.') or 'other')
        result[lang] = result.get(lang, 0) + loc
    return result
