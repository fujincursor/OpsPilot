"""Sandbox 环境服务

提供安全隔离的代码执行环境，支持：
- 代码运行和测试
- Lint 检查
- 文件操作
"""

import asyncio
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from ..models.codegen import (
    CodeFile,
    LintResult,
    LintError,
    SandboxInfo,
    SandboxExecuteResult,
)


class SandboxService:
    """Sandbox 环境服务

    提供安全隔离的代码执行环境。
    当前使用本地临时目录模拟沙箱，后续可替换为 Docker 容器或远程沙箱服务。
    """

    DEFAULT_TIMEOUT = 30
    MAX_TIMEOUT = 300
    SANDBOX_EXPIRY_HOURS = 24

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

        return sandbox_info

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
        if not sandbox:
            return SandboxExecuteResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=f"Sandbox {sandbox_id} not found or expired",
                duration_ms=0,
            )

        timeout = min(timeout, self.MAX_TIMEOUT)

        cwd = sandbox.working_directory
        if working_directory:
            cwd = os.path.join(sandbox.working_directory, working_directory.lstrip('/'))
            if not os.path.exists(cwd):
                os.makedirs(cwd, exist_ok=True)

        start_time = time.time()

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=self._get_sandbox_env(),
            )

            duration_ms = int((time.time() - start_time) * 1000)

            return SandboxExecuteResult(
                success=result.returncode == 0,
                exit_code=result.returncode,
                stdout=result.stdout[:10000],
                stderr=result.stderr[:10000],
                duration_ms=duration_ms,
            )

        except subprocess.TimeoutExpired:
            duration_ms = int((time.time() - start_time) * 1000)
            return SandboxExecuteResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return SandboxExecuteResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration_ms=duration_ms,
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
        sandbox = self.get_sandbox(sandbox_id)
        if not sandbox:
            return SandboxExecuteResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=f"Sandbox {sandbox_id} not found or expired",
                duration_ms=0,
            )

        timeout = min(timeout, self.MAX_TIMEOUT)

        cwd = sandbox.working_directory
        if working_directory:
            cwd = os.path.join(sandbox.working_directory, working_directory.lstrip('/'))
            if not os.path.exists(cwd):
                os.makedirs(cwd, exist_ok=True)

        start_time = time.time()

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self._get_sandbox_env(),
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                duration_ms = int((time.time() - start_time) * 1000)
                return SandboxExecuteResult(
                    success=False,
                    exit_code=-1,
                    stdout="",
                    stderr=f"Command timed out after {timeout} seconds",
                    duration_ms=duration_ms,
                )

            duration_ms = int((time.time() - start_time) * 1000)

            return SandboxExecuteResult(
                success=process.returncode == 0,
                exit_code=process.returncode or 0,
                stdout=stdout.decode('utf-8', errors='replace')[:10000],
                stderr=stderr.decode('utf-8', errors='replace')[:10000],
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return SandboxExecuteResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration_ms=duration_ms,
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

        file_path = os.path.join(sandbox.working_directory, file.path.lstrip('/'))

        try:
            result = subprocess.run(
                [self.python_executable(), "-m", "py_compile", file_path],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                error_output = result.stderr or result.stdout
                error = self._parse_python_error(file.path, error_output)
                if error:
                    errors.append(error)

        except subprocess.TimeoutExpired:
            warnings.append(LintError(
                file=file.path,
                line=0,
                message="Lint check timed out",
                severity="warning",
            ))

        except FileNotFoundError:
            pass

        except Exception as e:
            warnings.append(LintError(
                file=file.path,
                line=0,
                message=f"Lint check failed: {str(e)}",
                severity="warning",
            ))

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

        file_path = os.path.join(sandbox.working_directory, file.path.lstrip('/'))

        try:
            result = subprocess.run(
                ["node", "--check", file_path],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                errors.append(LintError(
                    file=file.path,
                    line=0,
                    code="SyntaxError",
                    message=result.stderr[:500] if result.stderr else "Syntax error",
                    severity="error",
                ))

        except FileNotFoundError:
            pass

        except Exception as e:
            warnings.append(LintError(
                file=file.path,
                line=0,
                message=f"Lint check failed: {str(e)}",
                severity="warning",
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

        try:
            if os.path.exists(sandbox_path):
                shutil.rmtree(sandbox_path)

            sandbox.status = "destroyed"
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

    def _get_sandbox_env(self) -> Dict[str, str]:
        """获取沙箱环境变量"""
        env = os.environ.copy()

        env['SANDBOX'] = '1'
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONUTF8'] = '1'
        env['LC_ALL'] = 'C.UTF-8'
        env['LANG'] = 'C.UTF-8'

        return env

    def python_executable(self) -> str:
        """沙箱里的 Python 使用当前服务的解释器，避免系统 PATH 里没有 python。"""
        return sys.executable

    def execute_command(
        self,
        sandbox_id: str,
        args: List[str],
        timeout: int = DEFAULT_TIMEOUT,
    ) -> SandboxExecuteResult:
        """在沙箱目录中执行参数列表，不经过 shell。"""
        sandbox = self.get_sandbox(sandbox_id)
        if not sandbox:
            return SandboxExecuteResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=f"Sandbox {sandbox_id} not found or expired",
                duration_ms=0,
            )

        timeout = min(timeout, self.MAX_TIMEOUT)
        start_time = time.time()
        try:
            result = subprocess.run(
                args,
                cwd=sandbox.working_directory,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=self._get_sandbox_env(),
                encoding="utf-8",
                errors="replace",
            )
            duration_ms = int((time.time() - start_time) * 1000)
            return SandboxExecuteResult(
                success=result.returncode == 0,
                exit_code=result.returncode,
                stdout=(result.stdout or "")[:10000],
                stderr=(result.stderr or "")[:10000],
                duration_ms=duration_ms,
            )
        except subprocess.TimeoutExpired:
            duration_ms = int((time.time() - start_time) * 1000)
            return SandboxExecuteResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
                duration_ms=duration_ms,
            )
        except Exception as exc:
            duration_ms = int((time.time() - start_time) * 1000)
            return SandboxExecuteResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(exc),
                duration_ms=duration_ms,
            )


sandbox_service = SandboxService()
