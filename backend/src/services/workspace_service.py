"""每个被维护项目的代码工作目录。GitHub 克隆和本地上传都落在这里。"""

from __future__ import annotations

import hashlib
import io
import shutil
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Callable, List
from uuid import UUID

from ..models.project import Project

_DATA_ROOT = Path(__file__).resolve().parents[2] / "data" / "workspaces"
_MAX_ZIP_BYTES = 50 * 1024 * 1024
_GIT_HTTP = ["-c", "http.version=HTTP/1.1"]


class WorkspaceError(RuntimeError):
    """代码导入失败。"""


class WorkspaceService:
    """按项目保存一份源代码，供方案和代码生成读取。"""

    def directory(self, project_id: UUID) -> Path:
        return _DATA_ROOT / str(project_id)

    def is_ready(self, project_id: UUID) -> bool:
        project = self._project(project_id)
        path = self.directory(project_id)
        return bool(project and project.code_status == "ready" and path.is_dir() and any(path.iterdir()))

    def contains(self, project_id: UUID, relative: str) -> bool:
        path = self._safe_file(project_id, relative)
        return path is not None and path.is_file()

    def import_git(self, project_id: UUID, repo_url: str, branch: str = "") -> Project:
        url = (repo_url or "").strip()
        if not url.startswith(("https://", "http://", "git@")):
            raise WorkspaceError("请填写 http(s) 或 git@ 开头的仓库地址")
        branch = (branch or "").strip()

        def fill(staging: Path) -> tuple[str, str]:
            command = ["git", *_GIT_HTTP, "clone", "--depth", "1"]
            if branch:
                command.extend(["--branch", branch])
            command.extend([url, str(staging)])
            last_detail = "git clone 失败"
            for attempt in range(2):
                self._clear_dir(staging)
                try:
                    completed = subprocess.run(
                        command,
                        capture_output=True,
                        text=True,
                        timeout=55,
                        check=False,
                    )
                except subprocess.TimeoutExpired:
                    last_detail = "连接 GitHub 超时"
                    continue
                if completed.returncode == 0:
                    break
                last_detail = (completed.stderr or completed.stdout or "git clone 失败").strip()
                if attempt == 0 and _transient_git_error(last_detail):
                    continue
                raise WorkspaceError(_git_error_message(last_detail))
            else:
                raise WorkspaceError(_git_error_message(last_detail))
            sha = self._git(staging, ["rev-parse", "HEAD"])
            current_branch = self._git(staging, ["rev-parse", "--abbrev-ref", "HEAD"])
            return sha, current_branch

        sha, current_branch = self._replace(project_id, fill)
        return self._save(
            project_id,
            code_origin="git",
            code_status="ready",
            code_branch=current_branch,
            code_revision=sha,
            code_message="已从 GitHub 克隆到项目工作目录",
            repo_url=url,
        )

    def import_zip(self, project_id: UUID, payload: bytes, filename: str = "source.zip") -> Project:
        if not payload:
            raise WorkspaceError("上传的压缩包是空的")
        if len(payload) > _MAX_ZIP_BYTES:
            raise WorkspaceError("压缩包超过 50MB")
        digest = hashlib.sha256(payload).hexdigest()[:16]

        def fill(staging: Path) -> tuple[str, str]:
            try:
                archive = zipfile.ZipFile(io.BytesIO(payload))
            except zipfile.BadZipFile as exc:
                raise WorkspaceError("请上传 zip 压缩包") from exc
            with archive:
                for info in archive.infolist():
                    self._check_zip_name(info.filename)
                archive.extractall(staging)
            self._flatten(staging)
            if not any(staging.rglob("*")):
                raise WorkspaceError("压缩包里没有源代码文件")
            return digest, ""

        revision, _branch = self._replace(project_id, fill)
        return self._save(
            project_id,
            code_origin="upload",
            code_status="ready",
            code_branch="",
            code_revision=revision,
            code_message=f"已上传 {filename}",
        )

    def context_for_prompt(self, project_id: UUID, *texts: str) -> tuple[str, List[str]]:
        """取出和需求最接近的已导入源码，作为方案修改依据。"""
        if not self.is_ready(project_id):
            return "服务器上还没有这个项目的源代码。不要写出具体文件路径。", []
        from .code_locator import locate_code

        _summary, locations = locate_code(self.directory(project_id), [text for text in texts if text])
        paths: List[str] = []
        sections: List[str] = []
        for location in locations:
            if location.path in paths:
                continue
            excerpt = self.read_excerpt(project_id, location.path, location.line)
            if not excerpt:
                continue
            paths.append(location.path)
            sections.append(
                f"### {location.path}:{location.line}\n{location.reason}\n```\n{excerpt}\n```"
            )
            if len(paths) >= 6:
                break
        if not sections:
            return "已搜索服务器上已上传的源代码，没有定位到与这条需求对应的文件。不要编造文件路径。", []
        return (
            "以下内容来自该项目已导入到服务端的本地源代码，是这次方案修改文件和改法的唯一依据。"
            "修复步骤必须对应下面源码中的函数、调用或分支，不要改写知识库文档里出现、但这里没有的文件。\n\n"
            + "\n\n".join(sections)
        ), paths

    def align_solution(self, project_id: UUID, solution, located_paths: List[str]) -> None:
        """没有真实代码时，不把猜测的文件当成结论。"""
        if not self.is_ready(project_id):
            if hasattr(solution, "affected_files"):
                solution.affected_files = []
            if hasattr(solution, "fix_steps"):
                solution.fix_steps = [
                    "项目尚未导入源代码，还不能确定要修改的文件。请先在项目设置中从 GitHub 克隆或上传源代码。"
                ]
            notice = "当前项目还没有导入源代码，下面如果出现具体文件，不能当作已经核对过的结论。"
            if notice not in (solution.content or ""):
                solution.content = f"{notice}\n\n{solution.content or ''}".strip()
            return
        kept = [path for path in (solution.affected_files or []) if self.contains(project_id, path)]
        for path in located_paths:
            if path not in kept and self.contains(project_id, path):
                kept.append(path)
        solution.affected_files = kept

    def read_excerpt(self, project_id: UUID, relative: str, line: int, before: int = 30, after: int = 90) -> str:
        """读取命中行附近的源码，而不是文件开头。"""
        path = self._safe_file(project_id, relative)
        if path is None or not path.is_file() or path.stat().st_size > 1_000_000:
            return ""
        try:
            rows = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            return ""
        if not rows:
            return ""
        center = min(max(line, 1), len(rows))
        start = max(1, center - before)
        end = min(len(rows), center + after)
        return "\n".join(f"{number}|{rows[number - 1]}" for number in range(start, end + 1))

    def read_text(self, project_id: UUID, relative: str, limit: int = 12000) -> str:
        path = self._safe_file(project_id, relative)
        if path is None or not path.is_file() or path.stat().st_size > 1_000_000:
            return ""
        try:
            return path.read_text(encoding="utf-8", errors="ignore")[:limit]
        except OSError:
            return ""

    def remove(self, project_id: UUID) -> None:
        path = self.directory(project_id)
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)

    def _replace(self, project_id: UUID, fill: Callable[[Path], tuple[str, str]]) -> tuple[str, str]:
        final = self.directory(project_id)
        final.parent.mkdir(parents=True, exist_ok=True)
        staging = final.with_name(final.name + ".incoming")
        if staging.exists():
            shutil.rmtree(staging)
        staging.mkdir(parents=True)
        try:
            revision, branch = fill(staging)
        except Exception:
            shutil.rmtree(staging, ignore_errors=True)
            raise
        backup = final.with_name(final.name + ".previous")
        if backup.exists():
            shutil.rmtree(backup, ignore_errors=True)
        if final.exists():
            final.rename(backup)
        staging.rename(final)
        shutil.rmtree(backup, ignore_errors=True)
        return revision, branch

    def _save(self, project_id: UUID, **fields) -> Project:
        from .project_service import project_service

        project = project_service.get(project_id)
        if project is None:
            raise WorkspaceError("项目不存在")
        for key, value in fields.items():
            setattr(project, key, value)
        project.code_updated_at = datetime.utcnow()
        project.updated_at = datetime.utcnow()
        project_service._projects[project.id] = project
        return project

    def _project(self, project_id: UUID):
        from .project_service import project_service

        return project_service.get(project_id)

    def _safe_file(self, project_id: UUID, relative: str) -> Path | None:
        raw = (relative or "").replace("\\", "/").strip()
        if not raw or raw.startswith("/") or ".." in raw.split("/"):
            return None
        root = self.directory(project_id).resolve()
        path = (root / raw).resolve()
        if path != root and root not in path.parents:
            return None
        return path

    @staticmethod
    def _git(cwd: Path, args: list[str]) -> str:
        completed = subprocess.run(
            ["git", *_GIT_HTTP, *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if completed.returncode != 0:
            raise WorkspaceError((completed.stderr or "无法读取 Git 版本").strip()[-300:])
        return completed.stdout.strip()

    @staticmethod
    def _check_zip_name(name: str) -> None:
        relative = name.replace("\\", "/").strip()
        if not relative or relative.startswith("/") or ":" in relative[:3]:
            raise WorkspaceError(f"压缩包包含不允许的路径: {name}")
        parts = [part for part in relative.split("/") if part not in ("", ".")]
        if any(part == ".." for part in parts):
            raise WorkspaceError(f"压缩包包含不允许的路径: {name}")

    @staticmethod
    def _flatten(staging: Path) -> None:
        children = [item for item in staging.iterdir() if item.name != "__MACOSX"]
        if len(children) != 1 or not children[0].is_dir():
            return
        nested = children[0]
        for item in nested.iterdir():
            item.rename(staging / item.name)
        nested.rmdir()


    @staticmethod
    def _clear_dir(path: Path) -> None:
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            return
        for child in path.iterdir():
            if child.is_dir():
                shutil.rmtree(child, ignore_errors=True)
            else:
                child.unlink(missing_ok=True)


def _transient_git_error(detail: str) -> bool:
    lowered = detail.lower()
    return any(
        word in lowered
        for word in (
            "connection was reset",
            "recv failure",
            "could not connect",
            "failed to connect",
            "timed out",
            "connection timed out",
            "early eof",
            "rpc failed",
            "the requested url returned error: 5",
        )
    )


def _git_error_message(detail: str) -> str:
    fatal = ""
    for line in detail.splitlines():
        if line.lower().startswith("fatal:"):
            fatal = line.split(":", 1)[-1].strip()
            break
    text = fatal or detail.strip()
    if _transient_git_error(text) or detail == "连接 GitHub 超时":
        return "连接 GitHub 失败，网络被重置或暂时无法访问。请再点一次同步，或改用上传压缩包。"
    return (text or "git clone 失败")[-500:]


workspace_service = WorkspaceService()
