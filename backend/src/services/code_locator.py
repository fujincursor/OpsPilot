"""在项目源码中定位与问题描述相关的文件。"""

from __future__ import annotations

import re
from pathlib import Path

from ..models.codegen import CodeLocation

SOURCE_DIRS = ("frontend/src", "backend/src")
SOURCE_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx", ".vue", ".go", ".java", ".css", ".html"}
SKIP_DIRS = {
    "node_modules",
    ".git",
    "venv",
    ".venv",
    "dist",
    "build",
    "__pycache__",
    "coverage",
    "deerflow",
    "data",
}
GENERIC_TERMS = {
    "页面",
    "无法",
    "不能",
    "正常",
    "打开",
    "问题",
    "错误",
    "异常",
    "功能",
    "系统",
    "一个",
    "进行",
    "以及",
    "相关",
    "当前",
    "需要",
}
SYNONYMS = {
    "监控": ["monitor", "monitoring"],
    "登录": ["login", "auth"],
    "对话": ["chat"],
    "知识库": ["knowledge"],
    "需求": ["requirement"],
    "方案": ["solution"],
    "审核": ["review"],
    "测试": ["test"],
    "代码生成": ["codegen"],
    "通知": ["notification"],
    "项目": ["project"],
}
LINK_RE = re.compile(r"""\bto\s*=\s*["']([^"']+)["']""")
ROUTE_RE = re.compile(r"""\bpath\s*=\s*["']([^"']+)["']""")


def locate_code(root: Path, texts: list[str]) -> tuple[str, list[CodeLocation]]:
    """根据问题描述检索源码，返回结论和具体位置。"""
    focused, extra = _terms("\n".join(texts))
    terms = focused or extra
    files = _source_files(root)
    locations: list[CodeLocation] = []
    seen: set[tuple[str, int]] = set()

    if _is_page_open_problem("\n".join(texts)):
        for location in _missing_routes(root, files, terms):
            key = (location.path, location.line)
            if key not in seen:
                seen.add(key)
                locations.append(location)

    search_files = files
    if any("没有这个页面" in item.reason for item in locations):
        search_files = [path for path in files if path.suffix.lower() in {".tsx", ".jsx", ".vue", ".html"}]
    for location in _keyword_hits(root, search_files, focused or extra):
        key = (location.path, location.line)
        if key in seen:
            continue
        seen.add(key)
        locations.append(location)
        if len(locations) >= 8:
            break

    if not locations:
        shown = "、".join(terms[:6]) or "该问题"
        return f"已搜索项目源码，没有找到与「{shown}」对应的代码位置。", []

    summary = _summary(locations)
    return summary, locations[:8]


def _terms(text: str) -> tuple[list[str], list[str]]:
    focused: list[str] = []
    extra: list[str] = []

    def add(bucket: list[str], term: str) -> None:
        cleaned = term.strip()
        if len(cleaned) < 2 or cleaned.lower() in GENERIC_TERMS or cleaned in GENERIC_TERMS:
            return
        if cleaned not in bucket:
            bucket.append(cleaned)

    for piece in re.findall(r"[\u4e00-\u9fff]{2,}", text):
        for word, aliases in SYNONYMS.items():
            if word in piece:
                add(focused, word)
                for alias in aliases:
                    add(focused, alias)
    for word in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", text):
        if word.lower() not in {"bug", "feature", "bugfix"}:
            add(extra, word)
    return focused, extra


def _is_page_open_problem(text: str) -> bool:
    return "页面" in text and any(word in text for word in ("无法", "打不开", "打不开", "空白", "不存在", "404"))


def _source_files(root: Path) -> list[Path]:
    preferred = _collect_sources(root, [root / relative for relative in SOURCE_DIRS])
    if preferred:
        return preferred
    return _collect_sources(root, [root])


def _collect_sources(root: Path, directories: list[Path]) -> list[Path]:
    files: list[Path] = []
    for directory in directories:
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in SOURCE_SUFFIXES:
                continue
            relative_parts = path.relative_to(root).parts
            if any(part in SKIP_DIRS for part in relative_parts) or path.name == "code_locator.py":
                continue
            if path.stat().st_size > 1_000_000:
                continue
            files.append(path)
            if len(files) >= 3000:
                return files
    return files


def _relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _read_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return []


def _missing_routes(root: Path, files: list[Path], terms: list[str]) -> list[CodeLocation]:
    routes: set[str] = set()
    route_file = ""
    route_line = 1
    links: list[tuple[Path, int, str, str, str]] = []

    for path in files:
        if path.suffix.lower() not in {".ts", ".tsx", ".js", ".jsx"}:
            continue
        lines = _read_lines(path)
        for index, line in enumerate(lines, start=1):
            for match in ROUTE_RE.finditer(line):
                normalized = _normalize_route(match.group(1))
                if normalized:
                    routes.add(normalized)
                    if not route_file:
                        route_file = _relative(root, path)
                        route_line = index
            for match in LINK_RE.finditer(line):
                target = match.group(1)
                if target.startswith("/"):
                    nearby = "\n".join(lines[max(0, index - 1): index + 8])
                    links.append((path, index, target, nearby, line.strip()))

    locations: list[CodeLocation] = []
    reported_routes: set[str] = set()
    for path, line, target, nearby, source_line in links:
        normalized = _normalize_route(target)
        if not normalized or _route_exists(normalized, routes):
            continue
        haystack = f"{target}\n{nearby}".lower()
        if terms and not any(term.lower() in haystack for term in terms):
            continue
        locations.append(CodeLocation(
            path=_relative(root, path),
            line=line,
            snippet=source_line[:180],
            reason=f"导航指向 {normalized}，项目路由中没有这个页面",
        ))
        reported_routes.add(normalized)

    if reported_routes and route_file:
        missing = "、".join(sorted(reported_routes))
        locations.append(CodeLocation(
            path=route_file,
            line=route_line,
            snippet="",
            reason=f"页面路由注册在这里，但没有 {missing}",
        ))
    return locations


def _keyword_hits(root: Path, files: list[Path], terms: list[str]) -> list[CodeLocation]:
    ranked: list[tuple[int, CodeLocation]] = []
    chinese = [term for term in terms if any("\u4e00" <= char <= "\u9fff" for char in term)]
    specific = chinese or [term for term in terms if term not in GENERIC_TERMS and len(term) >= 2]
    if not specific:
        return []
    for path in files:
        lines = _read_lines(path)
        best_line = 0
        best_score = 0
        best_snippet = ""
        path_text = _relative(root, path).lower()
        path_score = sum(3 for term in specific if term.lower() in path_text)
        for index, line in enumerate(lines, start=1):
            lowered = line.lower()
            score = path_score + sum(lowered.count(term.lower()) for term in specific)
            if score > best_score:
                best_score = score
                best_line = index
                best_snippet = line.strip()[:180]
        if best_score <= 0 or best_line == 0:
            continue
        ranked.append((best_score, CodeLocation(
            path=_relative(root, path),
            line=best_line,
            snippet=best_snippet,
            reason="文件内容与问题描述匹配",
        )))
    ranked.sort(key=lambda item: item[0], reverse=True)
    path_matches = [
        item for item in ranked
        if any(term.lower() in item[1].path.lower() for term in specific)
    ]
    chosen = path_matches or ranked
    return [item[1] for item in chosen[:8]]


def _normalize_route(path: str) -> str:
    value = path.split("?", 1)[0].strip()
    if value in {"", "*", "#"} or value.startswith("http"):
        return ""
    if not value.startswith("/"):
        value = "/" + value
    if len(value) > 1:
        value = value.rstrip("/")
    return value


def _route_exists(link: str, routes: set[str]) -> bool:
    for route in routes:
        pattern = "^" + re.sub(r":[^/]+", "[^/]+", route) + "$"
        if re.match(pattern, link):
            return True
    return False


def _summary(locations: list[CodeLocation]) -> str:
    missing = [item for item in locations if "没有这个页面" in item.reason or "没有 /" in item.reason]
    if missing:
        first = missing[0]
        return f"已定位到代码。{first.path}:{first.line} {first.reason}。"
    names = "、".join(f"{item.path}:{item.line}" for item in locations[:3])
    return f"已在项目源码中定位到这些位置：{names}。"
