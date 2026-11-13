"""沙箱会执行修改后的代码，并统计真实行覆盖率。"""

import tempfile
from pathlib import Path
from uuid import uuid4

from src.models.codegen import CodeFile, FileAction
from src.models.test import TestCaseType
from src.services.sandbox_service import sandbox_service
from src.services.test_execution import (
    added_line_numbers,
    change_focus,
    coverage_from_files,
    execute_suite,
    invocation_problems,
    materialize_changed_modules,
    missed_changed,
    parse_suite,
    runner_imports_ok,
    suite_from_payload,
)


SOURCE = '''def choose(value):
    if value > 0:
        return "yes"
    return "no"
'''

TESTS = '''def test_positive():
    from load_py import load_py
    assert load_py("sample.py").choose(1) == "yes"

def test_non_positive():
    from load_py import load_py
    assert load_py("sample.py").choose(-1) == "no"
'''


def test_runner_source_compiles():
    assert runner_imports_ok()


def test_parse_suite_keeps_generated_files():
    payload = parse_suite('''说明
```json
{"summary":"覆盖 choose","cases":[{"name":"test_positive","description":"正数","type":"unit","target":"choose","file_path":"tests/generated/test_sample.py"}],"files":[{"path":"tests/generated/test_sample.py","content":"def test_positive():\\n    assert True\\n"}]}
```''')
    summary, cases, files = suite_from_payload(payload)
    assert summary == "覆盖 choose"
    assert cases[0].name == "test_positive"
    assert cases[0].type == TestCaseType.UNIT
    assert "def test_positive" in files["tests/generated/test_sample.py"]


def test_sandbox_runs_modified_python_and_reports_coverage():
    sandbox = sandbox_service.create_sandbox(uuid4())
    try:
        source = CodeFile(path="sample.py", content=SOURCE, language="python", action=FileAction.MODIFY)
        outcome = execute_suite(
            sandbox.sandbox_id,
            [source],
            {"tests/generated/test_sample.py": TESTS},
        )
    finally:
        sandbox_service.cleanup_sandbox(sandbox.sandbox_id)

    names = {item["name"]: item["status"] for item in outcome["cases"]}
    assert names["test_positive"] == "passed"
    assert names["test_non_positive"] == "passed"
    coverage = coverage_from_files(outcome["files"])
    assert coverage.files["sample.py"]["lines_percent"] == 100
    assert coverage.lines_percent == 100


OLD_SAMPLE = '''def choose(value):
    return "no"
'''


def test_changed_python_lines_run_only_when_called():
    source = CodeFile(path="sample.py", content=SOURCE, language="python", action=FileAction.MODIFY)
    targets = change_focus([source], {"sample.py": OLD_SAMPLE})
    assert targets[0].symbols == ["choose"]
    added = targets[0].added_lines
    assert added
    problems = invocation_problems(
        {"tests/generated/test_sample.py": 'def test_read():\n    assert "choose" in open("sample.py", encoding="utf-8").read()\n'},
        targets,
    )
    assert problems
    sandbox = sandbox_service.create_sandbox(uuid4())
    try:
        outcome = execute_suite(
            sandbox.sandbox_id,
            [source],
            {"tests/generated/test_sample.py": TESTS},
            measured={"files": ["sample.py"], "changed_lines": {"sample.py": added}},
        )
    finally:
        sandbox_service.cleanup_sandbox(sandbox.sandbox_id)
    info = outcome["files"]["sample.py"]
    assert info["changed_covered"] == info["changed_total"]
    assert missed_changed(outcome["files"]) == {}
    assert added_line_numbers(OLD_SAMPLE, SOURCE) == added


HOME_OLD = '''export function Home() {
  return (
    <button type="button">首页</button>
  )
}
'''

HOME_NEW = '''export function logout() {
  localStorage.removeItem("auth_token")
}

export function Home() {
  return (
    <button type="button" onClick={logout}>退出登录</button>
  )
}
'''

HOME_TEST = '''import test from "node:test";
import assert from "node:assert/strict";
import * as changed from "../support/changed/Home_tsx.mjs";

test("logout clears token", () => {
  changed.localStorage.setItem("auth_token", "x");
  changed.logout();
  assert.equal(changed.localStorage.getItem("auth_token"), null);
  const tree = changed.Home();
  assert.equal(tree.type, "button");
  assert.equal(tree.children[0], "退出登录");
  tree.props.onClick();
});
'''


def test_changed_tsx_is_executed_in_sandbox():
    source = CodeFile(path="Home.tsx", content=HOME_NEW, language="tsx", action=FileAction.MODIFY)
    targets = change_focus([source], {"Home.tsx": HOME_OLD})
    assert "logout" in targets[0].symbols
    assert "Home" in targets[0].symbols
    modules = materialize_changed_modules(targets, [source])
    module_path = targets[0].module
    assert "h(" in modules[module_path]
    assert invocation_problems({"tests/generated/home.test.mjs": HOME_TEST}, targets) == []
    sandbox = sandbox_service.create_sandbox(uuid4())
    try:
        outcome = execute_suite(
            sandbox.sandbox_id,
            [source],
            {"tests/generated/home.test.mjs": HOME_TEST},
            extra_files=modules,
            measured={
                "files": ["Home.tsx"],
                "changed_lines": {"Home.tsx": targets[0].added_lines},
            },
        )
    finally:
        sandbox_service.cleanup_sandbox(sandbox.sandbox_id)
    names = {item["name"]: item["status"] for item in outcome["cases"]}
    assert names["logout clears token"] == "passed", names
    assert missed_changed(outcome["files"]) == {}


def test_workspace_is_copied_before_changed_files_overlay():
    origin = Path(tempfile.mkdtemp())
    (origin / "kept.py").write_text("KEEP = 1\n", encoding="utf-8")
    nested = origin / "pkg"
    nested.mkdir()
    (nested / "sample.py").write_text("OLD = True\n", encoding="utf-8")
    sandbox = sandbox_service.create_sandbox(uuid4())
    try:
        copied = sandbox_service.seed_workspace(sandbox.sandbox_id, origin)
        assert copied == 2
        source = CodeFile(path="pkg/sample.py", content=SOURCE, language="python", action=FileAction.MODIFY)
        tests = TESTS.replace('load_py("sample.py")', 'load_py("pkg/sample.py")')
        outcome = execute_suite(
            sandbox.sandbox_id,
            [source],
            {"tests/generated/test_sample.py": tests},
        )
        root = Path(sandbox.working_directory)
        assert (root / "kept.py").read_text(encoding="utf-8") == "KEEP = 1\n"
        assert "def choose" in (root / "pkg" / "sample.py").read_text(encoding="utf-8")
        names = {item["name"]: item["status"] for item in outcome["cases"]}
        assert names["test_positive"] == "passed"
        assert names["test_non_positive"] == "passed"
    finally:
        sandbox_service.cleanup_sandbox(sandbox.sandbox_id)
        import shutil
        shutil.rmtree(origin, ignore_errors=True)
