"""Code Generation Agent 服务

基于 DeerFlow 2.0 架构的代码生成智能体，负责：
- 根据方案设计生成代码
- 格式化和规范化代码
- 应用修复建议
"""

import re
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID

from ...models.solution import (
    Solution,
    BugFixSolution,
    FeatureDesignSolution,
    SolutionType,
    APIEndpoint,
    DatabaseChange,
    ArchitectureComponent,
)
from ...models.codegen import CodeFile, FileAction, LintError


class CodeGenAgentService:
    """Code Generation Agent 服务

    负责根据方案设计自动生成代码。
    当前为基于模板的规则引擎实现，后续可接入 LLM 进行智能生成。
    """

    AGENT_NAME = "CodeGenAgent"

    LANGUAGE_FILE_EXTENSIONS = {
        "python": ".py",
        "javascript": ".js",
        "typescript": ".ts",
        "go": ".go",
        "java": ".java",
        "rust": ".rs",
        "sql": ".sql",
    }

    PYTHON_MODEL_TEMPLATE = '''"""${model_name} 数据模型"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ${class_name}Base(BaseModel):
    """${model_name} 基础模型"""
${fields}


class ${class_name}Create(${class_name}Base):
    """创建 ${model_name} 请求模型"""
    pass


class ${class_name}Update(BaseModel):
    """更新 ${model_name} 请求模型"""
${optional_fields}


class ${class_name}(${class_name}Base):
    """${model_name} 完整模型"""
    id: UUID = Field(default_factory=uuid4, description="${model_name} ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")

    class Config:
        from_attributes = True


class ${class_name}Response(BaseModel):
    """${model_name} 列表响应模型"""
    items: List[${class_name}]
    total: int
    page: int = 1
    page_size: int = 20
'''

    PYTHON_SERVICE_TEMPLATE = '''"""${model_name} 管理服务"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from ..models.${module_name} import (
    ${class_name},
    ${class_name}Create,
    ${class_name}Update,
)


class ${class_name}Service:
    """${model_name} 管理服务

    负责 ${model_name} 的 CRUD 操作。
    当前使用内存存储，后续可替换为数据库实现。
    """

    def __init__(self):
        self._items: Dict[UUID, ${class_name}] = {}

    def create(self, data: ${class_name}Create) -> ${class_name}:
        """创建 ${model_name}

        Args:
            data: 创建数据

        Returns:
            创建的 ${model_name}
        """
        item = ${class_name}(**data.model_dump())
        self._items[item.id] = item
        return item

    def get(self, item_id: UUID) -> Optional[${class_name}]:
        """获取 ${model_name}

        Args:
            item_id: ${model_name} ID

        Returns:
            ${model_name} 对象，不存在返回 None
        """
        return self._items.get(item_id)

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> List[${class_name}]:
        """获取 ${model_name} 列表

        Args:
            page: 页码
            page_size: 每页数量

        Returns:
            ${model_name} 列表
        """
        items = list(self._items.values())
        items.sort(key=lambda x: x.created_at, reverse=True)

        start = (page - 1) * page_size
        end = start + page_size

        return items[start:end]

    def count(self) -> int:
        """统计 ${model_name} 数量"""
        return len(self._items)

    def update(
        self,
        item_id: UUID,
        data: ${class_name}Update,
    ) -> Optional[${class_name}]:
        """更新 ${model_name}

        Args:
            item_id: ${model_name} ID
            data: 更新数据

        Returns:
            更新后的 ${model_name}，不存在返回 None
        """
        item = self._items.get(item_id)
        if not item:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(item, field):
                setattr(item, field, value)

        item.updated_at = datetime.utcnow()
        return item

    def delete(self, item_id: UUID) -> bool:
        """删除 ${model_name}

        Args:
            item_id: ${model_name} ID

        Returns:
            是否删除成功
        """
        if item_id in self._items:
            del self._items[item_id]
            return True
        return False


${module_name}_service = ${class_name}Service()
'''

    PYTHON_ROUTE_TEMPLATE = '''"""${model_name} 管理 API"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from ...models.${module_name} import (
    ${class_name},
    ${class_name}Create,
    ${class_name}Update,
    ${class_name}Response,
)
from ...services.${module_name}_service import ${module_name}_service

router = APIRouter()


@router.post(
    "/${route_path}",
    response_model=${class_name},
    status_code=201,
)
async def create_${module_name}(
    data: ${class_name}Create,
) -> ${class_name}:
    """
    创建 ${model_name}

    - **data**: ${model_name} 数据
    """
    return ${module_name}_service.create(data)


@router.get(
    "/${route_path}",
    response_model=${class_name}Response,
)
async def list_${module_name}s(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
) -> ${class_name}Response:
    """
    获取 ${model_name} 列表

    - **page**: 页码
    - **page_size**: 每页数量
    """
    items = ${module_name}_service.list(page=page, page_size=page_size)
    total = ${module_name}_service.count()

    return ${class_name}Response(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/${route_path}/{item_id}",
    response_model=${class_name},
)
async def get_${module_name}(
    item_id: UUID,
) -> ${class_name}:
    """
    获取 ${model_name} 详情

    - **item_id**: ${model_name} ID
    """
    item = ${module_name}_service.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="${model_name} not found")
    return item


@router.put(
    "/${route_path}/{item_id}",
    response_model=${class_name},
)
async def update_${module_name}(
    item_id: UUID,
    data: ${class_name}Update,
) -> ${class_name}:
    """
    更新 ${model_name}

    - **item_id**: ${model_name} ID
    - **data**: 更新数据
    """
    item = ${module_name}_service.update(item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="${model_name} not found")
    return item


@router.delete("/${route_path}/{item_id}", status_code=204)
async def delete_${module_name}(item_id: UUID):
    """
    删除 ${model_name}

    - **item_id**: ${model_name} ID
    """
    if not ${module_name}_service.delete(item_id):
        raise HTTPException(status_code=404, detail="${model_name} not found")
'''

    BUGFIX_PATCH_TEMPLATE = '''"""Bug 修复补丁

修复问题: ${bug_title}
根因分析: ${root_cause}
"""

${fix_code}
'''

    def __init__(self):
        pass

    def generate_code(
        self,
        solution: Solution,
    ) -> List[CodeFile]:
        """根据方案生成代码

        Args:
            solution: 方案对象

        Returns:
            List[CodeFile]: 生成的代码文件列表
        """
        if solution.type == SolutionType.BUGFIX:
            return self._generate_bugfix_code(solution)
        elif solution.type == SolutionType.FEATURE_DESIGN:
            return self._generate_feature_code(solution)
        else:
            return []

    def _generate_bugfix_code(self, solution: BugFixSolution) -> List[CodeFile]:
        """生成 Bug 修复代码"""
        files = []

        if hasattr(solution, 'affected_files') and solution.affected_files:
            for file_path in solution.affected_files:
                fix_content = self._generate_bugfix_content(solution, file_path)
                files.append(CodeFile(
                    path=file_path,
                    content=fix_content,
                    language=self._detect_language(file_path),
                    action=FileAction.MODIFY,
                ))

        if hasattr(solution, 'test_cases') and solution.test_cases:
            test_file = self._generate_test_file(solution)
            if test_file:
                files.append(test_file)

        return files

    def _generate_bugfix_content(
        self,
        solution: BugFixSolution,
        file_path: str,
    ) -> str:
        """生成 Bug 修复内容"""
        fix_steps = getattr(solution, 'fix_steps', [])
        root_cause = getattr(solution, 'root_cause', '')

        content = f'''# Bug 修复补丁
# 文件: {file_path}
# 根因: {root_cause}
# 修复步骤:
'''
        for i, step in enumerate(fix_steps, 1):
            content += f"# {i}. {step}\n"

        content += '''
# TODO: 根据上述分析实现具体修复代码
# 当前为占位实现，需要根据实际代码进行修改

def apply_fix():
    """应用修复"""
    pass
'''
        return content

    def _generate_test_file(self, solution: BugFixSolution) -> Optional[CodeFile]:
        """生成测试文件"""
        test_cases = getattr(solution, 'test_cases', [])
        if not test_cases:
            return None

        content = '''"""Bug 修复测试用例"""

import pytest


class TestBugFix:
    """Bug 修复测试"""

'''
        for i, test_case in enumerate(test_cases, 1):
            test_name = self._to_snake_case(test_case[:50])
            content += f'''    def test_case_{i}_{test_name}(self):
        """测试: {test_case}"""
        # TODO: 实现测试逻辑
        assert True

'''
        return CodeFile(
            path="tests/test_bugfix.py",
            content=content,
            language="python",
            action=FileAction.CREATE,
        )

    def _generate_feature_code(
        self,
        solution: FeatureDesignSolution,
    ) -> List[CodeFile]:
        """生成功能代码"""
        files = []

        entities = self._extract_entities_from_solution(solution)

        for entity in entities:
            model_file = self._generate_model_file(entity, solution)
            if model_file:
                files.append(model_file)

            service_file = self._generate_service_file(entity, solution)
            if service_file:
                files.append(service_file)

            route_file = self._generate_route_file(entity, solution)
            if route_file:
                files.append(route_file)

        if hasattr(solution, 'database_changes') and solution.database_changes:
            migration_file = self._generate_migration_file(solution)
            if migration_file:
                files.append(migration_file)

        return files

    def _extract_entities_from_solution(
        self,
        solution: FeatureDesignSolution,
    ) -> List[str]:
        """从方案中提取实体名称"""
        entities = []

        if hasattr(solution, 'api_design'):
            for endpoint in solution.api_design:
                path_parts = endpoint.path.strip('/').split('/')
                if path_parts:
                    entity = path_parts[0].rstrip('s')
                    if entity and entity not in entities and not entity.startswith('{'):
                        entities.append(entity)

        if not entities:
            title = solution.title.replace('[功能设计]', '').strip()
            match = re.search(r'(\w+)(?:管理|列表|功能|服务)', title)
            if match:
                entities.append(match.group(1).lower())

        if not entities:
            entities = ['resource']

        return entities

    def _generate_model_file(
        self,
        entity: str,
        solution: FeatureDesignSolution,
    ) -> CodeFile:
        """生成模型文件"""
        class_name = self._to_pascal_case(entity)
        model_name = entity

        fields = self._extract_fields_from_solution(entity, solution)
        fields_code = self._generate_fields_code(fields)
        optional_fields_code = self._generate_optional_fields_code(fields)

        content = self.PYTHON_MODEL_TEMPLATE
        content = content.replace('${model_name}', model_name)
        content = content.replace('${class_name}', class_name)
        content = content.replace('${fields}', fields_code)
        content = content.replace('${optional_fields}', optional_fields_code)

        return CodeFile(
            path=f"models/{entity}.py",
            content=content,
            language="python",
            action=FileAction.CREATE,
        )

    def _generate_service_file(
        self,
        entity: str,
        solution: FeatureDesignSolution,
    ) -> CodeFile:
        """生成服务文件"""
        class_name = self._to_pascal_case(entity)
        module_name = entity

        content = self.PYTHON_SERVICE_TEMPLATE
        content = content.replace('${model_name}', entity)
        content = content.replace('${class_name}', class_name)
        content = content.replace('${module_name}', module_name)

        return CodeFile(
            path=f"services/{entity}_service.py",
            content=content,
            language="python",
            action=FileAction.CREATE,
        )

    def _generate_route_file(
        self,
        entity: str,
        solution: FeatureDesignSolution,
    ) -> CodeFile:
        """生成路由文件"""
        class_name = self._to_pascal_case(entity)
        module_name = entity
        route_path = f"{entity}s"

        content = self.PYTHON_ROUTE_TEMPLATE
        content = content.replace('${model_name}', entity)
        content = content.replace('${class_name}', class_name)
        content = content.replace('${module_name}', module_name)
        content = content.replace('${route_path}', route_path)

        return CodeFile(
            path=f"api/routes/{entity}s.py",
            content=content,
            language="python",
            action=FileAction.CREATE,
        )

    def _generate_migration_file(
        self,
        solution: FeatureDesignSolution,
    ) -> CodeFile:
        """生成数据库迁移文件"""
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')

        content = f'''"""数据库迁移脚本

生成时间: {datetime.utcnow().isoformat()}
关联方案: {solution.title}
"""

# 升级脚本
def upgrade():
'''
        for change in solution.database_changes:
            content += f"    # {change.change_type}: {change.table_name}\n"
            content += f"    # {change.description}\n"
            if change.sql_migration:
                for line in change.sql_migration.strip().split('\n'):
                    content += f"    # {line}\n"
            content += "\n"

        content += '''    pass


# 降级脚本
def downgrade():
    pass
'''
        return CodeFile(
            path=f"migrations/{timestamp}_feature_migration.py",
            content=content,
            language="python",
            action=FileAction.CREATE,
        )

    def _extract_fields_from_solution(
        self,
        entity: str,
        solution: FeatureDesignSolution,
    ) -> List[Dict[str, Any]]:
        """从方案中提取字段定义"""
        fields = [
            {"name": "name", "type": "str", "description": f"{entity} 名称", "required": True},
            {"name": "description", "type": "str", "description": "描述", "required": False},
        ]

        if hasattr(solution, 'api_design'):
            for endpoint in solution.api_design:
                if endpoint.request_body and isinstance(endpoint.request_body, dict):
                    for field_name, field_type in endpoint.request_body.items():
                        if field_name not in ['...', 'id'] and not any(f['name'] == field_name for f in fields):
                            fields.append({
                                "name": field_name,
                                "type": self._map_type(field_type),
                                "description": field_name,
                                "required": True,
                            })

        return fields

    def _generate_fields_code(self, fields: List[Dict[str, Any]]) -> str:
        """生成字段定义代码"""
        lines = []
        for field in fields:
            field_type = field['type']
            if not field.get('required', True):
                field_type = f"Optional[{field_type}]"
            default = '...' if field.get('required', True) else 'None'
            lines.append(
                f"    {field['name']}: {field_type} = Field({default}, description=\"{field['description']}\")"
            )
        return '\n'.join(lines) if lines else "    pass"

    def _generate_optional_fields_code(self, fields: List[Dict[str, Any]]) -> str:
        """生成可选字段定义代码"""
        lines = []
        for field in fields:
            lines.append(
                f"    {field['name']}: Optional[{field['type']}] = Field(None, description=\"{field['description']}\")"
            )
        return '\n'.join(lines) if lines else "    pass"

    def generate_file(
        self,
        solution: Solution,
        file_spec: Dict[str, Any],
    ) -> CodeFile:
        """生成单个文件

        Args:
            solution: 方案对象
            file_spec: 文件规格

        Returns:
            CodeFile: 生成的代码文件
        """
        path = file_spec.get('path', 'generated_file.py')
        language = file_spec.get('language', self._detect_language(path))
        action = FileAction(file_spec.get('action', 'create'))
        template = file_spec.get('template', '')

        content = self._render_template(template, solution, file_spec)

        return CodeFile(
            path=path,
            content=content,
            language=language,
            action=action,
        )

    def format_code(self, code: str, language: str) -> str:
        """格式化代码

        Args:
            code: 原始代码
            language: 编程语言

        Returns:
            str: 格式化后的代码
        """
        if language == "python":
            return self._format_python_code(code)
        elif language in ("javascript", "typescript"):
            return self._format_js_code(code)
        else:
            return code

    def _format_python_code(self, code: str) -> str:
        """格式化 Python 代码"""
        lines = code.split('\n')
        formatted_lines = []

        for line in lines:
            stripped = line.rstrip()
            formatted_lines.append(stripped)

        while formatted_lines and not formatted_lines[-1]:
            formatted_lines.pop()

        if formatted_lines:
            formatted_lines.append('')

        return '\n'.join(formatted_lines)

    def _format_js_code(self, code: str) -> str:
        """格式化 JavaScript/TypeScript 代码"""
        lines = code.split('\n')
        formatted_lines = []

        for line in lines:
            stripped = line.rstrip()
            formatted_lines.append(stripped)

        while formatted_lines and not formatted_lines[-1]:
            formatted_lines.pop()

        if formatted_lines:
            formatted_lines.append('')

        return '\n'.join(formatted_lines)

    def apply_fix(
        self,
        code: str,
        fix_suggestion: Dict[str, Any],
    ) -> Tuple[str, bool]:
        """应用修复建议

        Args:
            code: 原始代码
            fix_suggestion: 修复建议

        Returns:
            Tuple[str, bool]: (修复后的代码, 是否成功)
        """
        fix_type = fix_suggestion.get('type', '')
        line_number = fix_suggestion.get('line', 0)
        replacement = fix_suggestion.get('replacement', '')
        pattern = fix_suggestion.get('pattern', '')

        lines = code.split('\n')

        try:
            if fix_type == 'replace_line' and 0 < line_number <= len(lines):
                lines[line_number - 1] = replacement
                return '\n'.join(lines), True

            elif fix_type == 'insert_after' and 0 < line_number <= len(lines):
                lines.insert(line_number, replacement)
                return '\n'.join(lines), True

            elif fix_type == 'delete_line' and 0 < line_number <= len(lines):
                del lines[line_number - 1]
                return '\n'.join(lines), True

            elif fix_type == 'regex_replace' and pattern:
                fixed_code = re.sub(pattern, replacement, code)
                return fixed_code, True

            else:
                return code, False

        except Exception:
            return code, False

    def _detect_language(self, file_path: str) -> str:
        """检测文件语言"""
        ext_to_lang = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.go': 'go',
            '.java': 'java',
            '.rs': 'rust',
            '.sql': 'sql',
            '.sh': 'bash',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.json': 'json',
            '.md': 'markdown',
        }

        for ext, lang in ext_to_lang.items():
            if file_path.endswith(ext):
                return lang

        return 'text'

    def _to_pascal_case(self, text: str) -> str:
        """转换为 PascalCase"""
        words = re.split(r'[_\-\s]+', text)
        return ''.join(word.capitalize() for word in words)

    def _to_snake_case(self, text: str) -> str:
        """转换为 snake_case"""
        text = re.sub(r'[^\w\s]', '', text)
        words = text.lower().split()
        return '_'.join(words)[:30]

    def _map_type(self, type_str: Any) -> str:
        """映射类型字符串到 Python 类型"""
        if isinstance(type_str, str):
            type_mapping = {
                'string': 'str',
                'integer': 'int',
                'number': 'float',
                'boolean': 'bool',
                'array': 'List',
                'object': 'Dict',
                'uuid': 'UUID',
            }
            return type_mapping.get(type_str.lower(), 'str')
        return 'Any'

    def _render_template(
        self,
        template: str,
        solution: Solution,
        context: Dict[str, Any],
    ) -> str:
        """渲染模板"""
        result = template

        result = result.replace('${solution_id}', str(solution.id))
        result = result.replace('${solution_title}', solution.title)

        for key, value in context.items():
            result = result.replace(f'${{{key}}}', str(value))

        return result


codegen_agent_service = CodeGenAgentService()
