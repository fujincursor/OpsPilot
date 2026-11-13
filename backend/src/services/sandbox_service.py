"""Sandbox 环境服务

提供安全隔离的代码执行环境，支持：
- 代码运行和测试
- Lint 检查
- 文件操作

文件先写在本机临时目录，命令通过 docker run 在 opspilot-sandbox 容器里执行。
"""

import asyncio
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from ..models.codegen import (
    CodeFile,
    LintResult,
    LintError,
    SandboxInfo,
    SandboxExecuteResult,
)


@dataclass
class SandboxRuntime:
    """一次沙箱执行要传给 docker run 的限制。"""

    image: str = "opspilot-sandbox"
    memory_mb: int = 512
    cpu: float = 1.0
    network_policy: str = "disabled"
    run_as_non_root: bool = True
    read_only_root: bool = True
    disable_privileged: bool = True


class SandboxService:
    """Sandbox 环境服务

    工作文件放在本机临时目录，执行时挂载进 opspilot-sandbox 容器。
    """

    DEFAULT_TIMEOUT = 30
    MAX_TIMEOUT = 300
    SANDBOX_EXPIRY_HOURS = 24
    CONTAINER_IMAGE = "opspilot-sandbox"

    LINTER_COMMANDS = {
        "python": ["python", "-m", "py_compile"],
        "javascript": ["node", "--check"],
        "typescript": ["tsc", "--noEmit"],
    }

    FORMATTER_COMMANDS = {
        "python": ["black", "--quiet"],
        "javascript": ["prettier", "--write"],
        "typescript": ["prettier", "--write"],
    }

    def __init__(self):
        self._sandboxes: Dict[str, SandboxInfo] = {}
        self._runtimes: Dict[str, SandboxRuntime] = {}
        self._base_temp_dir = tempfile.gettempdir()
        self._sandbox_prefix = "opspilot_sandbox_"

    def create_sandbox(
        self,
        project_id: UUID,
        working_directory: Optional[str] = None,
    ) -> SandboxInfo:
        """创建沙箱环境

        Args:
            project_id: 项目 ID
            working_directory: 工作目录（可选）

        Returns:
            SandboxInfo: 沙箱信息
        """
        sandbox_id = f"{self._sandbox_prefix}{uuid4().hex[:12]}"

        sandbox_path = os.path.join(self._base_temp_dir, sandbox_id)
        os.makedirs(sandbox_path, exist_ok=True)

        work_dir = working_directory or "/workspace"
        workspace_path = os.path.join(sandbox_path, "workspace")
        os.makedirs(workspace_path, exist_ok=True)

        sandbox_info = SandboxInfo(
            sandbox_id=sandbox_id,
            project_id=project_id,
            status="active",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=self.SANDBOX_EXPIRY_HOURS),
            working_directory=workspace_path,
        )

        self._sandboxes[sandbox_id] = sandbox_info
        self._runtimes[sandbox_id] = self._runtime_for(project_id)
        return sandbox_info

    def seed_workspace(self, sandbox_id: str, source: Optional[Path] = None) -> int:
        """把已导入的项目工作区整份复制进沙箱。变更文件随后再覆盖同路径。"""
        sandbox = self.get_sandbox(sandbox_id)
        if sandbox is None:
            return 0
        if source is None:
            from .workspace_service import workspace_service

            if not workspace_service.is_ready(sandbox.project_id):
                return 0
            source = workspace_service.directory(sandbox.project_id)
        root = Path(source)
        if not root.is_dir():
            return 0
        destination = Path(sandbox.working_directory)
        copied = 0
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(root)
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            copied += 1
        return copied

    def get_sandbox(self, sandbox_id: str) -> Optional[SandboxInfo]:
        """获取沙箱信息

        Args:
            sandbox_id: 沙箱 ID

        Returns:
            SandboxInfo: 沙箱信息，不存在返回 None
        """
        sandbox = self._sandboxes.get(sandbox_id)

        if sandbox and sandbox.status == "active":
            if sandbox.expires_at and datetime.utcnow() > sandbox.expires_at:
                self.cleanup_sandbox(sandbox_id)
                return None

        return sandbox

    def execute_in_sandbox(
        self,
        sandbox_id: str,
        command: str,
        timeout: int = DEFAULT_TIMEOUT,
        working_directory: Optional[str] = None,
    ) -> SandboxExecuteResult:
        """在沙箱中执行命令

        Args:
            sandbox_id: 沙箱 ID
            command: 要执行的命令
            timeout: 超时时间（秒）
            working_directory: 工作目录（相对于沙箱根目录）

        Returns:
            SandboxExecuteResult: 执行结果
        """
        sandbox = self.get_sandbox(sandbox_id)
        if not sandbox or sandbox.status != "active":
            return SandboxExecuteResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=f"Sandbox {sandbox_id} not found or expired",
                duration_ms=0,
            )

        return self._run_container(
            sandbox,
            ["sh", "-c", command],
            timeout,
            relative_workdir=working_directory,
        )

    async def execute_in_sandbox_async(
        self,
        sandbox_id: str,
        command: str,
        timeout: int = DEFAULT_TIMEOUT,
        working_directory: Optional[str] = None,
    ) -> SandboxExecuteResult:
        """在沙箱中异步执行命令

        Args:
            sandbox_id: 沙箱 ID
            command: 要执行的命令
            timeout: 超时时间（秒）
            working_directory: 工作目录

        Returns:
            SandboxExecuteResult: 执行结果
        """
        return await asyncio.to_thread(
            self.execute_in_sandbox,
            sandbox_id,
            command,
            timeout,
            working_directory,
        )

    def write_file(
        self,
        sandbox_id: str,
        path: str,
        content: str,
        create_dirs: bool = True,
    ) -> Tuple[bool, str]:
        """写入文件到沙箱

        Args:
            sandbox_id: 沙箱 ID
            path: 文件路径（相对于工作目录）
            content: 文件内容
            create_dirs: 是否自动创建目录

        Returns:
            Tuple[bool, str]: (是否成功, 错误消息或完整路径)
        """
        sandbox = self.get_sandbox(sandbox_id)
        if not sandbox:
            return False, f"Sandbox {sandbox_id} not found or expired"

        full_path = os.path.join(sandbox.working_directory, path.lstrip('/'))

        normalized_path = os.path.normpath(full_path)
        if not normalized_path.startswith(sandbox.working_directory):
            return False, "Path traversal detected"

        try:
            if create_dirs:
                dir_path = os.path.dirname(full_path)
                os.makedirs(dir_path, exist_ok=True)

            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return True, full_path

        except Exception as e:
            return False, str(e)

    def read_file(
        self,
        sandbox_id: str,
        path: str,
    ) -> Tuple[bool, str]:
        """从沙箱读取文件

        Args:
            sandbox_id: 沙箱 ID
            path: 文件路径（相对于工作目录）

        Returns:
            Tuple[bool, str]: (是否成功, 文件内容或错误消息)
        """
        sandbox = self.get_sandbox(sandbox_id)
        if not sandbox:
            return False, f"Sandbox {sandbox_id} not found or expired"

        full_path = os.path.join(sandbox.working_directory, path.lstrip('/'))

        normalized_path = os.path.normpath(full_path)
        if not normalized_path.startswith(sandbox.working_directory):
            return False, "Path traversal detected"

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return True, content

        except FileNotFoundError:
            return False, f"File not found: {path}"

        except Exception as e:
            return False, str(e)

    def write_files(
        self,
        sandbox_id: str,
        files: List[CodeFile],
    ) -> Tuple[int, List[str]]:
        """批量写入文件到沙箱

        Args:
            sandbox_id: 沙箱 ID
            files: 代码文件列表

        Returns:
            Tuple[int, List[str]]: (成功数量, 错误列表)
        """
        success_count = 0
        errors = []

        for file in files:
            success, result = self.write_file(
                sandbox_id=sandbox_id,
                path=file.path,
                content=file.content,
            )
            if success:
                success_count += 1
            else:
                errors.append(f"{file.path}: {result}")

        return success_count, errors

    def run_linter(
        self,
        sandbox_id: str,
        files: List[CodeFile],
    ) -> LintResult:
        """运行语法检查

        Args:
            sandbox_id: 沙箱 ID
            files: 要检查的代码文件列表

        Returns:
            LintResult: 检查结果
        """
        sandbox = self.get_sandbox(sandbox_id)
        if not sandbox:
            return LintResult(
                passed=False,
                errors=[LintError(
                    file="",
                    line=0,
                    message=f"Sandbox {sandbox_id} not found or expired",
                )],
                error_count=1,
            )

        all_errors = []
        all_warnings = []

        for file in files:
            file_errors, file_warnings = self._lint_file(sandbox, file)
            all_errors.extend(file_errors)
            all_warnings.extend(file_warnings)

        return LintResult(
            passed=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings,
            error_count=len(all_errors),
            warning_count=len(all_warnings),
        )

    def _lint_file(
        self,
        sandbox: SandboxInfo,
        file: CodeFile,
    ) -> Tuple[List[LintError], List[LintError]]:
        """检查单个文件

        Args:
            sandbox: 沙箱信息
            file: 代码文件

        Returns:
            Tuple[List[LintError], List[LintError]]: (错误列表, 警告列表)
        """
        errors = []
        warnings = []

        language = file.language

        if language == "python":
            errors, warnings = self._lint_python_file(sandbox, file)
        elif language in ("javascript", "typescript"):
            errors, warnings = self._lint_js_file(sandbox, file)
        else:
            pass

        return errors, warnings

    def _lint_python_file(
        self,
        sandbox: SandboxInfo,
        file: CodeFile,
    ) -> Tuple[List[LintError], List[LintError]]:
        """检查 Python 文件

        使用 Python 内置语法检查。
        """
        errors = []
        warnings = []

        relative = file.path.lstrip("/\\").replace("\\", "/")
        result = self.execute_command(
            sandbox.sandbox_id,
            [self.python_executable(), "-m", "py_compile", relative],
            timeout=10,
        )
        if result.success:
            return errors, warnings
        if result.exit_code == -1 and "timed out" in (result.stderr or ""):
            warnings.append(LintError(
                file=file.path,
                line=0,
                message="Lint check timed out",
                severity="warning",
            ))
            return errors, warnings
        error = self._parse_python_error(file.path, result.stderr or result.stdout)
        if error:
            errors.append(error)
        return errors, warnings

    def _parse_python_error(self, file_path: str, error_output: str) -> Optional[LintError]:
        """解析 Python 错误输出"""
        import re

        line_match = re.search(r'line (\d+)', error_output)
        line_num = int(line_match.group(1)) if line_match else 0

        error_match = re.search(r'(SyntaxError|IndentationError|TabError):\s*(.+)', error_output)
        if error_match:
            error_code = error_match.group(1)
            message = error_match.group(2).strip()
        else:
            error_code = "SyntaxError"
            message = error_output.strip()[-200:]

        return LintError(
            file=file_path,
            line=line_num,
            column=0,
            code=error_code,
            message=message,
            severity="error",
        )

    def _lint_js_file(
        self,
        sandbox: SandboxInfo,
        file: CodeFile,
    ) -> Tuple[List[LintError], List[LintError]]:
        """检查 JavaScript/TypeScript 文件

        使用 Node.js 语法检查。
        """
        errors = []
        warnings = []

        relative = file.path.lstrip("/\\").replace("\\", "/")
        result = self.execute_command(
            sandbox.sandbox_id,
            ["node", "--check", relative],
            timeout=10,
        )
        if result.success:
            return errors, warnings
        if result.exit_code == -1 and "timed out" in (result.stderr or ""):
            warnings.append(LintError(
                file=file.path,
                line=0,
                message="Lint check timed out",
                severity="warning",
            ))
            return errors, warnings
        errors.append(LintError(
            file=file.path,
            line=0,
            code="SyntaxError",
            message=(result.stderr or result.stdout or "Syntax error")[:500],
            severity="error",
        ))
        return errors, warnings

    def cleanup_sandbox(self, sandbox_id: str) -> bool:
        """清理沙箱环境

        Args:
            sandbox_id: 沙箱 ID

        Returns:
            bool: 是否清理成功
        """
        sandbox = self._sandboxes.get(sandbox_id)
        if not sandbox:
            return False

        sandbox_path = os.path.join(self._base_temp_dir, sandbox_id)
        self._remove_container(sandbox_id)

        try:
            if os.path.exists(sandbox_path):
                shutil.rmtree(sandbox_path)

            sandbox.status = "destroyed"
            self._runtimes.pop(sandbox_id, None)
            return True

        except Exception:
            return False

    def cleanup_expired_sandboxes(self) -> int:
        """清理所有过期的沙箱

        Returns:
            int: 清理的沙箱数量
        """
        now = datetime.utcnow()
        expired_ids = []

        for sandbox_id, sandbox in self._sandboxes.items():
            if sandbox.expires_at and now > sandbox.expires_at:
                expired_ids.append(sandbox_id)

        for sandbox_id in expired_ids:
            self.cleanup_sandbox(sandbox_id)

        return len(expired_ids)

    def list_sandboxes(
        self,
        project_id: Optional[UUID] = None,
        status: Optional[str] = None,
    ) -> List[SandboxInfo]:
        """列出沙箱

        Args:
            project_id: 项目 ID（可选）
            status: 状态筛选（可选）

        Returns:
            List[SandboxInfo]: 沙箱列表
        """
        sandboxes = list(self._sandboxes.values())

        if project_id:
            sandboxes = [s for s in sandboxes if s.project_id == project_id]

        if status:
            sandboxes = [s for s in sandboxes if s.status == status]

        return sandboxes

    def python_executable(self) -> str:
        """容器里的 Python 使用镜像自带的 python。"""
        return "python"

    def probe_execution(
        self,
        memory_mb: int,
        cpu: float,
        network_policy: str,
        run_as_non_root: bool,
    ) -> Tuple[bool, str]:
        """用一次短命容器确认镜像能按当前限制启动。"""
        runtime = SandboxRuntime(
            memory_mb=memory_mb or 512,
            cpu=cpu or 1,
            network_policy=network_policy or "disabled",
            run_as_non_root=run_as_non_root,
            read_only_root=True,
            disable_privileged=True,
        )
        docker = self._docker_bin()
        if docker is None:
            return False, "未找到 docker，无法创建容器"
        command = self._docker_argv(runtime, None, ["python", "--version"], "/tmp")
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30,
                encoding="utf-8",
                errors="replace",
            )
        except subprocess.TimeoutExpired:
            return False, "沙箱容器启动超时"
        text = (completed.stdout or completed.stderr or "").strip()
        first = text.splitlines()[0][:300] if text else "无输出"
        return completed.returncode == 0, first

    def execute_command(
        self,
        sandbox_id: str,
        args: List[str],
        timeout: int = DEFAULT_TIMEOUT,
    ) -> SandboxExecuteResult:
        """在容器中执行参数列表，不经过宿主机 shell。"""
        sandbox = self.get_sandbox(sandbox_id)
        if not sandbox or sandbox.status != "active":
            return SandboxExecuteResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=f"Sandbox {sandbox_id} not found or expired",
                duration_ms=0,
            )
        return self._run_container(sandbox, args, timeout)

    def _runtime_for(self, project_id: UUID) -> SandboxRuntime:
        runtime = SandboxRuntime(image=self.CONTAINER_IMAGE)
        try:
            from .project_service import project_service

            project = project_service.get(project_id)
        except Exception:
            project = None
        sandbox = getattr(project, "sandbox", None) if project else None
        if sandbox is None:
            return runtime

        def field(name: str, default):
            if isinstance(sandbox, dict):
                return sandbox.get(name, default)
            return getattr(sandbox, name, default)

        try:
            runtime.memory_mb = max(int(field("memory_mb", 512) or 512), 64)
        except (TypeError, ValueError):
            runtime.memory_mb = 512
        try:
            runtime.cpu = float(field("cpu", 1) or 1)
        except (TypeError, ValueError):
            runtime.cpu = 1
        if runtime.cpu <= 0:
            runtime.cpu = 1
        runtime.network_policy = str(field("network_policy", "disabled") or "disabled")
        runtime.run_as_non_root = bool(field("run_as_non_root", True))
        runtime.read_only_root = bool(field("read_only_root", True))
        runtime.disable_privileged = bool(field("disable_privileged", True))
        return runtime

    def _docker_bin(self) -> Optional[str]:
        found = shutil.which("docker")
        if found:
            return found
        candidate = os.path.join(
            os.environ.get("ProgramFiles", r"C:\Program Files"),
            "Docker",
            "Docker",
            "resources",
            "bin",
            "docker.exe",
        )
        if os.path.isfile(candidate):
            return candidate
        return None

    def _container_workdir(self, sandbox: SandboxInfo, relative_workdir: Optional[str]) -> str:
        if not relative_workdir:
            return "/workspace"
        host_sub = os.path.join(sandbox.working_directory, relative_workdir.lstrip("/\\"))
        os.makedirs(host_sub, exist_ok=True)
        relative = relative_workdir.strip("/\\").replace("\\", "/")
        return f"/workspace/{relative}"

    def _container_args(self, sandbox: SandboxInfo, args: List[str]) -> List[str]:
        root = os.path.normcase(os.path.abspath(sandbox.working_directory))
        converted: List[str] = []
        for arg in args:
            if arg == sys.executable:
                converted.append("python")
                continue
            if os.path.isabs(arg):
                absolute = os.path.normcase(os.path.abspath(arg))
                if absolute == root or absolute.startswith(root + os.sep):
                    relative = os.path.relpath(arg, sandbox.working_directory).replace("\\", "/")
                    converted.append("/workspace" if relative == "." else relative)
                    continue
            converted.append(arg)
        return converted

    def _docker_argv(
        self,
        runtime: SandboxRuntime,
        sandbox: Optional[SandboxInfo],
        args: List[str],
        workdir: str,
    ) -> List[str]:
        docker = self._docker_bin()
        command = [
            docker or "docker",
            "run",
            "--rm",
            "--pull",
            "never",
            "--entrypoint",
            "",
            "--memory",
            f"{runtime.memory_mb}m",
            "--cpus",
            str(runtime.cpu),
            "-e",
            "SANDBOX=1",
            "-e",
            "PYTHONIOENCODING=utf-8",
            "-e",
            "PYTHONUTF8=1",
            "-e",
            "LC_ALL=C.UTF-8",
            "-e",
            "LANG=C.UTF-8",
            "-e",
            "PYTHONDONTWRITEBYTECODE=1",
        ]
        if sandbox is not None:
            command.extend(["--name", sandbox.sandbox_id])
            command.extend(["-v", f"{os.path.abspath(sandbox.working_directory)}:/workspace"])
        command.extend(["-w", workdir])
        if runtime.network_policy == "disabled":
            command.extend(["--network", "none"])
        if runtime.run_as_non_root:
            command.extend(["--user", "65534:65534"])
        if runtime.read_only_root:
            command.extend(["--read-only", "--tmpfs", "/tmp:rw,nosuid,size=64m"])
        if runtime.disable_privileged:
            command.extend(["--cap-drop", "ALL", "--security-opt", "no-new-privileges"])
        command.append(runtime.image)
        if sandbox is None:
            command.extend(args)
        else:
            command.extend(self._container_args(sandbox, args))
        return command

    def _remove_container(self, sandbox_id: str) -> None:
        docker = self._docker_bin()
        if docker is None:
            return
        try:
            subprocess.run(
                [docker, "rm", "-f", sandbox_id],
                capture_output=True,
                text=True,
                timeout=20,
            )
        except (subprocess.TimeoutExpired, OSError):
            return

    def _failed(self, started: float, message: str) -> SandboxExecuteResult:
        return SandboxExecuteResult(
            success=False,
            exit_code=-1,
            stdout="",
            stderr=message,
            duration_ms=int((time.time() - started) * 1000),
        )

    def _run_container(
        self,
        sandbox: SandboxInfo,
        args: List[str],
        timeout: int,
        relative_workdir: Optional[str] = None,
    ) -> SandboxExecuteResult:
        started = time.time()
        timeout = min(timeout, self.MAX_TIMEOUT)
        docker = self._docker_bin()
        if docker is None:
            return self._failed(started, "未找到 docker，无法在容器中执行")
        self._remove_container(sandbox.sandbox_id)
        runtime = self._runtimes.get(sandbox.sandbox_id) or SandboxRuntime(image=self.CONTAINER_IMAGE)
        workdir = self._container_workdir(sandbox, relative_workdir)
        command = self._docker_argv(runtime, sandbox, args, workdir)
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="replace",
            )
        except subprocess.TimeoutExpired as exc:
            self._remove_container(sandbox.sandbox_id)
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            if isinstance(stdout, bytes):
                stdout = stdout.decode("utf-8", errors="replace")
            if isinstance(stderr, bytes):
                stderr = stderr.decode("utf-8", errors="replace")
            return SandboxExecuteResult(
                success=False,
                exit_code=-1,
                stdout=(stdout or "")[:10000],
                stderr=((stderr or "") + f"\nCommand timed out after {timeout} seconds")[:10000],
                duration_ms=int((time.time() - started) * 1000),
            )
        except OSError as exc:
            return self._failed(started, str(exc))
        return SandboxExecuteResult(
            success=completed.returncode == 0,
            exit_code=completed.returncode,
            stdout=(completed.stdout or "")[:10000],
            stderr=(completed.stderr or "")[:10000],
            duration_ms=int((time.time() - started) * 1000),
        )


sandbox_service = SandboxService()
