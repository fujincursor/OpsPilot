"""按修改后的代码生成用例，并在沙箱里执行。"""

from __future__ import annotations

import ast
import difflib
import json
import re
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from ..models.codegen import CodeFile, FileAction
from ..models.test import CoverageInfo, TestCase, TestCaseType


LOAD_PY = '''"""按相对路径加载修改后的 Python 文件。"""
import importlib.util
from pathlib import Path


def load_py(relative: str):
    path = Path(relative)
    name = "changed_" + "_".join(path.with_suffix("").parts)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
'''

LOAD_SOURCE_MJS = '''import fs from "node:fs";

export function readSource(relativePath) {
  return fs.readFileSync(relativePath, "utf8");
}
'''

RUNNER = r'''# -*- coding: utf-8 -*-
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import traceback
from pathlib import Path

ROOT = Path(".").resolve()
sys.path.insert(0, str(ROOT / "tests" / "support"))
sys.path.insert(0, str(ROOT))


def non_empty_lines(path: Path):
    rows = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    return {number for number, line in enumerate(rows, start=1) if line.strip()}


def run_python(measured):
    import trace

    results = []
    tracer = trace.Trace(count=1, trace=0)
    generated = ROOT / "tests" / "generated"
    for path in sorted(generated.glob("test_*.py")):
        try:
            spec = importlib.util.spec_from_file_location(path.stem, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception as exc:
            results.append({
                "name": path.stem,
                "status": "failed",
                "detail": str(exc),
                "trace": traceback.format_exc(),
            })
            continue
        for name in sorted(item for item in dir(module) if item.startswith("test_")):
            fn = getattr(module, name)
            if not callable(fn):
                continue
            try:
                tracer.runfunc(fn)
                results.append({"name": name, "status": "passed", "detail": "通过"})
            except Exception as exc:
                results.append({
                    "name": name,
                    "status": "failed",
                    "detail": str(exc),
                    "trace": traceback.format_exc(),
                })
    counts = {}
    for (filename, lineno), hits in tracer.results().counts.items():
        if hits:
            counts.setdefault(os.path.normcase(os.path.normpath(filename)), set()).add(lineno)
    files = {}
    for relative in measured:
        if not relative.endswith(".py"):
            continue
        target = ROOT / relative
        if not target.is_file():
            continue
        interesting = non_empty_lines(target)
        covered = set()
        suffix = os.path.normcase(os.path.normpath(relative))
        for filename, lines in counts.items():
            if filename.endswith(suffix):
                covered |= lines & interesting
        uncovered = sorted(interesting - covered)
        total = len(interesting)
        files[relative] = {
            "lines_total": total,
            "lines_covered": total - len(uncovered),
            "lines_percent": 100.0 if total == 0 else (total - len(uncovered)) / total * 100,
            "uncovered": uncovered[:80],
            "covered_lines": sorted(covered),
        }
    return results, files


def expand_uncovered(text):
    numbers = []
    for part in (text or "").split(","):
        part = part.strip()
        if not part or part.lower() == "none":
            continue
        if "-" in part:
            start, end = part.split("-", 1)
            if start.strip().isdigit() and end.strip().isdigit():
                numbers.extend(range(int(start), int(end) + 1))
        elif part.isdigit():
            numbers.append(int(part))
    return numbers


def run_node(measured):
    node = shutil.which("node")
    tests = sorted((ROOT / "tests" / "generated").glob("*.test.mjs"))
    tests += sorted((ROOT / "tests" / "generated").glob("*.test.js"))
    if not tests:
        return [], {}
    if not node:
        return [{
            "name": "node-tests",
            "status": "failed",
            "detail": "沙箱所在机器没有 node，前端测试没有执行",
        }], {}
    completed = subprocess.run(
        [node, "--test", "--experimental-test-coverage", "--test-reporter=spec", *[str(item) for item in tests]],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=90,
    )
    output = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
    results = []
    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith(("✔", "✖", "√", "×")):
            status = "passed" if stripped[0] in {"✔", "√"} else "failed"
            name = stripped[1:].strip()
            name = name.split(" (", 1)[0].strip()
            results.append({"name": name, "status": status, "detail": "通过" if status == "passed" else stripped})
    if not results and completed.returncode != 0:
        results.append({
            "name": "node-tests",
            "status": "failed",
            "detail": (completed.stderr or completed.stdout or "node 测试没有返回结果")[:1000],
        })
    files = {}
    pattern = re_file()
    for line in output.splitlines():
        match = pattern.search(line)
        if not match:
            continue
        filename = match.group("file")
        if filename in {"file", "all"} or set(filename) <= {"-"}:
            continue
        relative = next((item for item in measured if item.endswith(filename) or filename.endswith(item)), "")
        if not relative:
            continue
        uncovered = expand_uncovered(match.group("uncovered"))
        percent = float(match.group("line"))
        target = ROOT / relative
        total = len(non_empty_lines(target)) if target.is_file() else 0
        covered = int(round(total * percent / 100))
        files[relative] = {
            "lines_total": total,
            "lines_covered": covered,
            "lines_percent": percent,
            "uncovered": uncovered[:80],
            "branches_percent": float(match.group("branch")),
            "functions_percent": float(match.group("funcs")),
        }
    return results, files


def re_file():
    import re
    return re.compile(
        r"(?P<file>[A-Za-z0-9_./\\-]+\.(?:py|mjs|js|cjs|ts|tsx|jsx))\s+\|\s+"
        r"(?P<line>[\d.]+)\s+\|\s+(?P<branch>[\d.]+)\s+\|\s+(?P<funcs>[\d.]+)\s+\|\s*(?P<uncovered>.*)$"
    )


def apply_changed(files, changed_lines):
    hits = {}
    hit_path = ROOT / "tests" / "changed-hits.txt"
    if hit_path.is_file():
        for row in hit_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if ":" not in row:
                continue
            path, _, number = row.rpartition(":")
            if number.strip().isdigit():
                hits.setdefault(path, set()).add(int(number))
    for relative, numbers in (changed_lines or {}).items():
        wanted = [int(number) for number in numbers]
        info = files.setdefault(relative, {
            "lines_total": 0,
            "lines_covered": 0,
            "lines_percent": 0,
            "uncovered": [],
        })
        if str(relative).endswith(".py"):
            seen = set(info.get("covered_lines") or [])
            hit = [number for number in wanted if number in seen]
        else:
            seen = hits.get(relative, set())
            hit = [number for number in wanted if number in seen]
        missed = [number for number in wanted if number not in set(hit)]
        info["changed_total"] = len(wanted)
        info["changed_covered"] = len(hit)
        info["changed_uncovered"] = missed[:80]
        if wanted:
            info["lines_total"] = len(wanted)
            info["lines_covered"] = len(hit)
            info["lines_percent"] = len(hit) / len(wanted) * 100
            info["uncovered"] = missed[:80]
        info.pop("covered_lines", None)
    for info in files.values():
        info.pop("covered_lines", None)


def main():
    raw = json.loads(Path("tests/measured.json").read_text(encoding="utf-8"))
    if isinstance(raw, list):
        measured, changed_lines = raw, {}
    else:
        measured = raw.get("files") or []
        changed_lines = raw.get("changed_lines") or {}
    python_results, python_files = run_python(measured)
    node_results, node_files = run_node(measured)
    seen = set(python_files)
    for path, info in node_files.items():
        if path not in seen:
            python_files[path] = info
    for relative in measured:
        python_files.setdefault(relative, {
            "lines_total": len(non_empty_lines(ROOT / relative)) if (ROOT / relative).is_file() else 0,
            "lines_covered": 0,
            "lines_percent": 0,
            "uncovered": [],
        })
    apply_changed(python_files, changed_lines)
    print("OPSPILOT_RESULT " + json.dumps({
        "cases": python_results + node_results,
        "files": python_files,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
'''


def changed_sources(files: List[CodeFile]) -> List[CodeFile]:
    """只取这次生成结果里的新增和修改。"""
    selected: List[CodeFile] = []
    seen: set[str] = set()
    for item in files:
        if item.action not in {FileAction.CREATE, FileAction.MODIFY}:
            continue
        if not item.content.strip() or item.path in seen:
            continue
        seen.add(item.path)
        selected.append(item)
    return selected


def _safe_test_path(path: str) -> Optional[str]:
    cleaned = (path or "").replace("\\", "/").strip().lstrip("/")
    parts = [part for part in cleaned.split("/") if part not in {"", "."}]
    if not parts or any(part == ".." for part in parts):
        return None
    relative = "/".join(parts)
    if not relative.startswith("tests/generated/"):
        return None
    if not relative.endswith((".py", ".mjs", ".js")):
        return None
    return relative


def parse_suite(text: str) -> Optional[dict]:
    """从模型输出里取出用例和测试文件。"""
    raw = text or ""
    chunks = re.findall(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL | re.IGNORECASE)
    sources = chunks or [raw]
    found: Optional[dict] = None
    for chunk in sources:
        start = chunk.find("{")
        while start != -1:
            try:
                obj, end = json.JSONDecoder().raw_decode(chunk[start:])
            except json.JSONDecodeError:
                start = chunk.find("{", start + 1)
                continue
            if isinstance(obj, dict) and isinstance(obj.get("files"), list):
                found = obj
            start = chunk.find("{", start + end)
    return found


def suite_from_payload(payload: dict) -> tuple[str, List[TestCase], Dict[str, str]]:
    summary = " ".join(str(payload.get("summary") or "").split())
    file_contents: Dict[str, str] = {}
    for item in payload.get("files") or []:
        if not isinstance(item, dict):
            continue
        path = _safe_test_path(str(item.get("path") or ""))
        content = str(item.get("content") or "")
        if path and content.strip():
            file_contents[path] = content
    cases: List[TestCase] = []
    for item in payload.get("cases") or []:
        if not isinstance(item, dict):
            continue
        name = " ".join(str(item.get("name") or "").split())[:200]
        if not name:
            continue
        file_path = _safe_test_path(str(item.get("file_path") or "")) or ""
        kind = str(item.get("type") or "unit").lower()
        if kind not in {entry.value for entry in TestCaseType}:
            kind = TestCaseType.UNIT.value
        cases.append(TestCase(
            name=name,
            description=str(item.get("description") or "")[:2000],
            type=TestCaseType(kind),
            code=file_contents.get(file_path, "")[:200000],
            expected_result=str(item.get("expected_result") or "断言通过")[:500],
            file_path=file_path,
            target_function=str(item.get("target") or "")[:200] or None,
        ))
    if not cases:
        for path, content in file_contents.items():
            for name in _test_names(path, content):
                cases.append(TestCase(
                    name=name,
                    description=f"覆盖 {path}",
                    type=TestCaseType.UNIT,
                    code=content[:200000],
                    expected_result="断言通过",
                    file_path=path,
                ))
    return summary[:4000], cases, file_contents


def _test_names(path: str, content: str) -> List[str]:
    if path.endswith(".py"):
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return [Path(path).stem]
        names = [
            node.name for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
        ]
        return names or [Path(path).stem]
    names = re.findall(r"""test\(\s*["']([^"']+)["']""", content)
    return names or [Path(path).stem]


@dataclass
class ChangeTarget:
    """一次变更里需要被实际调用的文件。"""

    path: str
    kind: str
    added_lines: List[int] = field(default_factory=list)
    symbols: List[str] = field(default_factory=list)
    diff: str = ""
    excerpt: str = ""
    module: str = ""


def _executable_added_line(line: str) -> bool:
    """签名、括号和空行不会单独执行，不拿来当作必须覆盖的变更。"""
    stripped = line.strip()
    if not stripped or stripped.startswith(("//", "#", "*", "/*", "import ")):
        return False
    if stripped in {"{", "}", "(", ")", "};", ");", ">", "/>", "):"}:
        return False
    if re.match(r"^(export\s+)?(default\s+)?(async\s+)?function\b", stripped):
        return False
    if re.match(r"^(export\s+)?(default\s+)?class\b", stripped):
        return False
    if re.match(r"^(export\s+)?(const|let|var)\s+\w+.*=\s*(async\s*)?\(?.*\)?\s*(:\s*[\w.<>, ]+)?\s*=>\s*\{?\s*$", stripped):
        return False
    if re.match(r"^(async\s+)?def\s+\w+", stripped) or re.match(r"^class\s+\w+", stripped):
        return False
    return True


def added_line_numbers(old: str, new: str) -> List[int]:
    """新文件里新增或替换出来、并且会真正执行的行。没有旧文件时，全部可执行行都算变更。"""
    new_lines = new.splitlines()
    if not (old or "").strip():
        return [number for number, line in enumerate(new_lines, start=1) if _executable_added_line(line)]
    numbers: List[int] = []
    matcher = difflib.SequenceMatcher(a=old.splitlines(), b=new_lines)
    for tag, _i1, _i2, j1, j2 in matcher.get_opcodes():
        if tag not in {"insert", "replace"}:
            continue
        for number in range(j1 + 1, j2 + 1):
            if _executable_added_line(new_lines[number - 1]):
                numbers.append(number)
    return numbers


def _short_diff(path: str, old: str, new: str) -> str:
    text = "".join(difflib.unified_diff(
        (old or "").splitlines(keepends=True),
        new.splitlines(keepends=True),
        fromfile=f"a/{path}",
        tofile=f"b/{path}",
        n=2,
    ))
    if len(text) > 4000:
        return text[:4000] + "\n..."
    return text or "新文件"


def _python_symbols(content: str, added: set[int]) -> tuple[List[str], str]:
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return [], ""
    names: List[str] = []
    excerpts: List[str] = []
    for node in tree.body:
        functions = []
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions = [node]
        elif isinstance(node, ast.ClassDef):
            functions = [item for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))]
        for fn in functions:
            end = getattr(fn, "end_lineno", fn.lineno) or fn.lineno
            if not (set(range(fn.lineno, end + 1)) & added):
                continue
            names.append(fn.name)
            segment = ast.get_source_segment(content, fn) or ""
            if segment:
                excerpts.append(segment)
    return names, "\n\n".join(excerpts)[:8000]


def _line_of(content: str, index: int) -> int:
    return content.count("\n", 0, index) + 1


def _match_brace(content: str, open_at: int) -> int:
    depth = 0
    i = open_at
    while i < len(content):
        char = content[i]
        if char in {"'", '"', "`"}:
            i = _skip_js_string(content, i)
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return len(content) - 1


def _skip_js_string(content: str, index: int) -> int:
    quote = content[index]
    i = index + 1
    while i < len(content):
        if content[i] == "\\":
            i += 2
            continue
        if content[i] == quote:
            return i + 1
        i += 1
    return len(content)


def _script_entries(content: str, added: set[int]) -> List[tuple[int, str, str]]:
    patterns = [
        re.compile(r"(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*\{"),
        re.compile(
            r"(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>\s*\{"
        ),
    ]
    found: List[tuple[int, str, str]] = []
    seen_span: set[tuple[int, int]] = set()
    for pattern in patterns:
        for match in pattern.finditer(content):
            open_at = match.end() - 1
            close_at = _match_brace(content, open_at)
            if (open_at, close_at) in seen_span:
                continue
            seen_span.add((open_at, close_at))
            start = _line_of(content, match.start())
            end = _line_of(content, close_at)
            if not added or not (set(range(start, end + 1)) & added):
                continue
            found.append((start, match.group(1), content[match.start():close_at + 1]))
    found.sort(key=lambda item: (item[0], -len(item[2])))
    unique: List[tuple[int, str, str]] = []
    seen_names: set[str] = set()
    for item in found:
        if item[1] in seen_names:
            continue
        seen_names.add(item[1])
        unique.append(item)
    return unique


def _script_symbols(content: str, added: set[int]) -> tuple[List[str], str]:
    entries = _script_entries(content, added)
    names = [name for _start, name, _source in entries]
    excerpts = [source for _start, _name, source in entries]
    return names, "\n\n".join(excerpts)[:8000]


def _module_path(path: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9_]+", "_", path).strip("_") or "changed"
    return f"tests/support/changed/{stem}.mjs"


def change_focus(files: List[CodeFile], originals: Dict[str, str]) -> List[ChangeTarget]:
    """从新旧内容里找出必须被调用的变更函数。"""
    targets: List[ChangeTarget] = []
    for item in files:
        old = originals.get(item.path, "")
        added = added_line_numbers(old, item.content)
        kind = "python" if item.path.endswith(".py") else "script"
        if kind == "python":
            symbols, excerpt = _python_symbols(item.content, set(added))
            module = ""
        else:
            symbols, excerpt = _script_symbols(item.content, set(added))
            module = _module_path(item.path) if symbols else ""
        targets.append(ChangeTarget(
            path=item.path,
            kind=kind,
            added_lines=added,
            symbols=symbols,
            diff=_short_diff(item.path, old, item.content),
            excerpt=excerpt,
            module=module,
        ))
    return targets


def _is_jsx_start(source: str, index: int) -> bool:
    if index >= len(source) or source[index] != "<":
        return False
    nxt = source[index + 1:index + 2]
    if not (nxt.isalpha() or nxt in {"_", "$", "/", ">"}):
        return False
    i = index - 1
    while i >= 0 and source[i].isspace():
        i -= 1
    if i < 0:
        return True
    if source[i] in "([{= ,?:;&|!>":
        return True
    word_end = i + 1
    while i >= 0 and (source[i].isalnum() or source[i] in {"_", "$"}):
        i -= 1
    return source[i + 1:word_end] in {"return", "throw"}


def _read_js_expr(source: str, index: int) -> tuple[str, int]:
    if source[index] in {"'", '"', "`"}:
        end = _skip_js_string(source, index)
        return source[index:end], end
    if source[index] == "{":
        end = _match_brace(source, index)
        return source[index:end + 1], end + 1
    start = index
    while index < len(source) and source[index] not in " \t\r\n>/=,":
        index += 1
    return source[start:index], index


def _read_jsx(source: str, index: int) -> tuple[str, int]:
    if source.startswith("</", index):
        return '""', index + 2
    if source.startswith("<>", index):
        name = ""
        i = index + 2
    else:
        i = index + 1
        start = i
        while i < len(source) and (source[i].isalnum() or source[i] in {"_", "$", "."}):
            i += 1
        name = source[start:i]
    props: List[str] = []
    while i < len(source):
        while i < len(source) and source[i].isspace():
            i += 1
        if i >= len(source) or source[i] in {">", "/"}:
            break
        if source[i] == "{":
            expr, i = _read_js_expr(source, i)
            props.append(expr[1:-1].strip())
            continue
        key_start = i
        while i < len(source) and (source[i].isalnum() or source[i] in {"_", "$", "-"}):
            i += 1
        key = source[key_start:i]
        while i < len(source) and source[i].isspace():
            i += 1
        if i < len(source) and source[i] == "=":
            i += 1
            while i < len(source) and source[i].isspace():
                i += 1
            value, i = _read_js_expr(source, i)
            if value.startswith("{"):
                value = value[1:-1].strip()
            props.append(f"{key}: {value}")
        elif key:
            props.append(f"{key}: true")
    self_close = source.startswith("/>", i)
    if self_close:
        i += 2
        children: List[str] = []
    elif i < len(source) and source[i] == ">":
        i += 1
        children = []
        close = f"</{name}>" if name else "</>"
        while i < len(source) and not source.startswith(close, i):
            if source[i].isspace():
                i += 1
                continue
            if _is_jsx_start(source, i):
                child, i = _read_jsx(source, i)
                children.append(child)
                continue
            if source[i] == "{":
                expr, i = _read_js_expr(source, i)
                children.append(expr[1:-1].strip())
                continue
            start = i
            while i < len(source) and source[i] not in "<{" and not source.startswith(close, i):
                i += 1
            text = source[start:i].strip()
            if text:
                children.append(json.dumps(text, ensure_ascii=False))
        i += len(close)
    else:
        children = []
    tag = json.dumps(name) if name else "Fragment"
    child_src = (", " + ", ".join(children)) if children else ""
    return f"h({tag}, {{{', '.join(props)}}}{child_src})", i


def jsx_to_h(source: str) -> str:
    """把 JSX 转成 h() 调用，便于在没有构建工具的沙箱里执行。"""
    out: List[str] = []
    i = 0
    while i < len(source):
        char = source[i]
        if char in {"'", '"', "`"}:
            end = _skip_js_string(source, i)
            out.append(source[i:end])
            i = end
            continue
        if _is_jsx_start(source, i):
            expr, i = _read_jsx(source, i)
            out.append(expr)
            continue
        out.append(char)
        i += 1
    return "".join(out)


def _strip_ts(source: str) -> str:
    source = re.sub(r"\bexport\s+default\s+", "", source)
    source = re.sub(r"\bexport\s+", "", source)
    source = re.sub(r"\)\s*:\s*[^{=]+(?=\s*[{=])", ")", source)
    source = re.sub(r"([A-Za-z_$][\w$]*)\s*:\s*[A-Za-z_][\w.<>\[\]|& ]*(?=\s*[,)=])", r"\1", source)
    source = re.sub(r"\s+as\s+[A-Za-z_][\w.<>\[\]]*", "", source)
    return source


def _inject_marks(source: str, start_line: int, path: str, added: set[int]) -> str:
    lines = source.splitlines()
    body_start = 0
    for index, line in enumerate(lines):
        if "{" in line:
            body_start = index
            break
    owned: Dict[int, List[int]] = {}
    for index, line in enumerate(lines):
        if index <= body_start or "return" not in line:
            continue
        group = []
        if start_line + index in added:
            group.append(start_line + index)
        for follow in range(index + 1, len(lines)):
            stripped = lines[follow].strip()
            if not stripped:
                continue
            if stripped.startswith("<") or stripped.startswith(")"):
                number = start_line + follow
                if number in added:
                    group.append(number)
                continue
            break
        if group:
            owned[index] = group
    out: List[str] = []
    marked: set[int] = set()
    for index, line in enumerate(lines):
        number = start_line + index
        if index in owned:
            for item in owned[index]:
                if item not in marked:
                    out.append(f"mark({json.dumps(path)}, {item});")
                    marked.add(item)
        elif index > body_start and number in added and line.strip() and not line.strip().startswith(("<", "//", "*", "/*", "{", "}")):
            if number not in marked:
                out.append(f"mark({json.dumps(path)}, {number});")
                marked.add(number)
        out.append(line)
    return "\n".join(out)


_CHANGED_PRELUDE = """import fs from "node:fs";
const Fragment = Symbol("Fragment");
function h(type, props, ...children) {
  return { type, props: props || {}, children };
}
export function mark(file, line) {
  fs.appendFileSync("tests/changed-hits.txt", file + ":" + line + "\\n");
}
export const localStorage = {
  _data: {},
  getItem(key) { return Object.prototype.hasOwnProperty.call(this._data, key) ? this._data[key] : null; },
  setItem(key, value) { this._data[key] = String(value); },
  removeItem(key) { delete this._data[key]; },
};
export function useState(initial) {
  let value = initial;
  return [value, (next) => { value = typeof next === "function" ? next(value) : next; }];
}
export function useNavigate() { return () => {}; }
export function useEffect() {}
export function useMemo(fn) { return fn(); }
export function useCallback(fn) { return fn; }
export function useRef(initial) { return { current: initial }; }
"""


def materialize_changed_modules(targets: List[ChangeTarget], files: List[CodeFile]) -> Dict[str, str]:
    """把前端变更函数提取成沙箱可以直接 import 的模块。"""
    by_path = {item.path: item.content for item in files}
    modules: Dict[str, str] = {}
    for target in targets:
        if target.kind != "script" or not target.module or not target.symbols:
            continue
        content = by_path.get(target.path, "")
        added = set(target.added_lines)
        chunks = [_CHANGED_PRELUDE]
        for start, _name, match_source in _script_entries(content, added):
            marked = _inject_marks(match_source, start, target.path, added)
            body = jsx_to_h(_strip_ts(marked))
            if body.startswith("function") or body.startswith("async function"):
                chunks.append("export " + body)
            else:
                chunks.append(f"export {body}")
        modules[target.module] = "\n".join(chunks) + "\n"
    return modules


def invocation_problems(test_files: Dict[str, str], targets: List[ChangeTarget]) -> List[str]:
    """用例必须调用变更函数，不能只读取源码。"""
    blob = "\n".join(test_files.values())
    problems: List[str] = []
    if not test_files:
        return ["没有可执行的测试文件"]
    if re.search(r"readSource\s*\(|readFileSync\s*\(|\.read_text\s*\(", blob) and "load_py(" not in blob and "/changed/" not in blob:
        problems.append("用例只读取了源码，没有执行变更代码")
    for target in targets:
        if not target.symbols and not target.added_lines:
            continue
        for symbol in target.symbols:
            if not re.search(rf"\b{re.escape(symbol)}\s*\(", blob):
                problems.append(f"用例没有调用 {target.path} 的变更函数 {symbol}")
        if target.kind == "python" and target.symbols:
            if "load_py(" not in blob or target.path not in blob:
                problems.append(f"Python 用例必须在 test_ 函数内 load_py(\"{target.path}\") 后再调用变更函数")
        if target.module and target.module not in blob and Path(target.module).name not in blob:
            problems.append(f"前端用例必须 import {target.module} 后再调用变更函数")
    return problems


def add_fallback(test_files: Dict[str, str], cases: List[TestCase], targets: List[ChangeTarget]) -> tuple[Dict[str, str], List[TestCase]]:
    """模型没有调用变更函数时，补上会真正执行的调用。"""
    files = dict(test_files)
    python_blocks: List[str] = []
    script_blocks: Dict[str, List[str]] = {}
    for target in targets:
        for symbol in target.symbols:
            if re.search(rf"\b{re.escape(symbol)}\s*\(", "\n".join(files.values())):
                continue
            if target.kind == "python":
                python_blocks.append(textwrap.dedent(f"""
                    def test_executes_{symbol}():
                        from load_py import load_py
                        fn = getattr(load_py({json.dumps(target.path)}), {json.dumps(symbol)})
                        assert callable(fn)
                        last_error = None
                        for args in [(), (0,), (1,), (-1,), ("",), ("x",), (True,), (False,), (None,)]:
                            try:
                                fn(*args)
                                return
                            except TypeError as exc:
                                last_error = exc
                        raise AssertionError("变更函数无法调用: %s" % last_error)
                """).strip())
            elif target.module:
                script_blocks.setdefault(target.module, []).append(symbol)
    if python_blocks:
        path = "tests/generated/test_changed_fallback.py"
        files[path] = "\n\n".join(python_blocks) + "\n"
        for block in python_blocks:
            name = _test_names(path, block)[0]
            cases.append(TestCase(
                name=name,
                description="直接调用变更函数，确认变更代码被执行",
                type=TestCaseType.UNIT,
                code=block,
                expected_result="变更函数被调用",
                file_path=path,
            ))
    for module, symbols in script_blocks.items():
        path = "tests/generated/changed-fallback.test.mjs"
        import_line = f'import * as changed from "../support/changed/{Path(module).name}";'
        tests = [import_line, 'import test from "node:test";', 'import assert from "node:assert/strict";']
        for symbol in symbols:
            tests.append(textwrap.dedent(f"""
                test("执行变更函数 {symbol}", () => {{
                  const fn = changed[{json.dumps(symbol)}];
                  assert.equal(typeof fn, "function");
                  fn();
                }});
            """).strip())
        files[path] = "\n".join(tests) + "\n"
        for symbol in symbols:
            cases.append(TestCase(
                name=f"执行变更函数 {symbol}",
                description="直接调用变更函数，确认变更代码被执行",
                type=TestCaseType.UNIT,
                code=files[path],
                expected_result="变更函数被调用",
                file_path=path,
            ))
    return files, cases


def missed_changed(file_map: Dict[str, dict]) -> Dict[str, List[int]]:
    missing: Dict[str, List[int]] = {}
    for path, info in file_map.items():
        total = int(info.get("changed_total") or 0)
        covered = int(info.get("changed_covered") or 0)
        if total and covered < total:
            missing[path] = [int(number) for number in info.get("changed_uncovered") or []]
    return missing


def build_prompt(
    files: List[CodeFile],
    skill: str,
    targets: List[ChangeTarget],
    uncovered: Optional[Dict[str, List[int]]] = None,
    feedback: str = "",
) -> str:
    sections = []
    for target in targets[:8]:
        module = f"\n可执行模块：import * as changed from \"../support/changed/{Path(target.module).name}\"\n导出函数：{', '.join(target.symbols)}\n" if target.module else ""
        symbols = "、".join(target.symbols) if target.symbols else "文件中的新增语句"
        excerpt = target.excerpt or "见差异"
        sections.append(
            f"### {target.path}\n必须调用：{symbols}{module}\n```diff\n{target.diff}\n```\n```\n{excerpt}\n```"
        )
    gap = ""
    if uncovered:
        lines = []
        for path, numbers in uncovered.items():
            if numbers:
                lines.append(f"- {path}: {', '.join(str(number) for number in numbers[:40])}")
            else:
                lines.append(f"- {path}: 变更语句尚未执行到")
        gap = "\n上一轮没有执行到这些变更行，请补会真正调用它们的用例：\n" + "\n".join(lines) + "\n"
    if feedback:
        gap += "\n上一轮没有通过执行检查：\n" + feedback + "\n"
    skill_body = (skill or "").strip()
    if len(skill_body) > 4000:
        skill_body = skill_body[:4000]
    return textwrap.dedent(f"""
        你是这个项目的测试执行代理。请只针对下面的变更代码写测试。
        每条用例都要在运行时调用变更函数，让新增或修改的语句真正执行，并对结果做断言。
        不要读取源码做字符串比较。禁止 readSource、readFileSync、read_text、open(、assert True。
        以下面的沙箱约定为准，不要运行 pytest、jest 或 npm。

        ## 测试执行技能
        {skill_body or "针对变更函数编写可执行用例，并在沙箱中调用。"}

        ## 沙箱约定
        - 沙箱里已有该项目导入的完整代码。这次变更的文件会按原相对路径覆盖同名旧文件。可以引用项目里的其他模块。
        - Python 用例写到 tests/generated/test_*.py。函数名以 test_ 开头，只用 assert。
        - 在 test_ 函数内部写 from load_py import load_py，再 load_py("相对路径")，然后调用变更函数。不要在模块顶层执行被测代码。
        - 前端变更函数已经提取成可执行模块。用例写到 tests/generated/*.test.mjs，使用 node:test 和 node:assert/strict。
        - 用 import * as changed from "../support/changed/模块名.mjs" 调用导出的函数。
        - 组件函数返回 {{type, props, children}}。要执行点击逻辑时调用 props.onClick()。
        - localStorage、useState、useNavigate 已在该模块中提供。
        - 不要依赖 node_modules、数据库或网络。
        - 每个变更函数、每个新增分支都要有一次真实调用。
        {gap}
        只输出一个 json 对象，不要写其他文字：
        {{
          "summary": "这些用例如何调用变更代码",
          "cases": [{{"name": "test_example", "description": "调用哪个变更函数的哪个分支", "type": "unit", "target": "函数名", "file_path": "tests/generated/test_example.py", "expected_result": "断言通过"}}],
          "files": [{{"path": "tests/generated/test_example.py", "content": "完整可执行测试文件"}}]
        }}

        ## 变更代码
        {chr(10).join(sections)}
    """).strip()


def skill_text() -> str:
    try:
        from .skill_catalog import read_skill

        return read_skill("test-execution").content
    except Exception:
        return ""


def execute_suite(
    sandbox_id: str,
    sources: List[CodeFile],
    test_files: Dict[str, str],
    extra_files: Optional[Dict[str, str]] = None,
    measured: Optional[dict] = None,
) -> dict:
    """把修改后的代码和生成的用例写入沙箱并执行。"""
    from .sandbox_service import sandbox_service

    for item in sources:
        ok, message = sandbox_service.write_file(sandbox_id, item.path, item.content)
        if not ok:
            raise RuntimeError(message)
    for path, content in (extra_files or {}).items():
        ok, message = sandbox_service.write_file(sandbox_id, path, content)
        if not ok:
            raise RuntimeError(message)
    sandbox_service.write_file(sandbox_id, "tests/support/load_py.py", LOAD_PY)
    sandbox_service.write_file(sandbox_id, "tests/support/load_source.mjs", LOAD_SOURCE_MJS)
    for path, content in test_files.items():
        safe = _safe_test_path(path)
        if safe:
            sandbox_service.write_file(sandbox_id, safe, content)
    payload = measured if measured is not None else [item.path for item in sources]
    sandbox_service.write_file(
        sandbox_id,
        "tests/measured.json",
        json.dumps(payload, ensure_ascii=False),
    )
    sandbox_service.write_file(sandbox_id, "tests/run_suite.py", RUNNER)
    execution = sandbox_service.execute_command(
        sandbox_id,
        [sandbox_service.python_executable(), "tests/run_suite.py"],
        timeout=120,
    )
    payload = _parse_runner_output(execution.stdout)
    if payload is None:
        raise RuntimeError((execution.stderr or execution.stdout or "沙箱没有返回测试结果")[:1000])
    payload["duration_ms"] = execution.duration_ms
    return payload


def _parse_runner_output(stdout: str) -> Optional[dict]:
    match = None
    for line in (stdout or "").splitlines():
        if line.startswith("OPSPILOT_RESULT "):
            match = line[len("OPSPILOT_RESULT "):]
    if not match:
        return None
    try:
        data = json.loads(match)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def coverage_from_files(file_map: Dict[str, dict]) -> CoverageInfo:
    changed_total = sum(int(item.get("changed_total") or 0) for item in file_map.values())
    changed_covered = sum(int(item.get("changed_covered") or 0) for item in file_map.values())
    if changed_total:
        total, covered = changed_total, changed_covered
    else:
        total = sum(int(item.get("lines_total") or 0) for item in file_map.values())
        covered = sum(int(item.get("lines_covered") or 0) for item in file_map.values())
    function_values = [float(item.get("functions_percent") or 0) for item in file_map.values() if "functions_percent" in item]
    branch_values = [float(item.get("branches_percent") or 0) for item in file_map.values() if "branches_percent" in item]
    return CoverageInfo(
        lines_total=total,
        lines_covered=covered,
        lines_percent=(covered / total * 100) if total else (100.0 if file_map else 0.0),
        branches_percent=sum(branch_values) / len(branch_values) if branch_values else 0.0,
        functions_percent=sum(function_values) / len(function_values) if function_values else 0.0,
        files=file_map,
    )


def uncovered_lines(file_map: Dict[str, dict]) -> Dict[str, List[int]]:
    missing: Dict[str, List[int]] = {}
    for path, info in file_map.items():
        percent = float(info.get("lines_percent") or 0)
        if percent >= 99.9:
            continue
        numbers = [int(number) for number in info.get("uncovered") or []]
        missing[path] = numbers
    return missing


def runner_imports_ok() -> bool:
    """供测试确认运行器源码本身可以编译。"""
    ast.parse(RUNNER)
    return True
