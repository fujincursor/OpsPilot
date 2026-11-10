# M2: 知识库前置维护模块

## 1. 模块概述

知识库前置维护模块确保在处理运维需求之前，系统已具备足够的项目知识。这是 OpsPilot 智能分析的基础。

### 1.1 核心功能

- 文档上传与管理
- 文档索引与处理
- 知识就绪检查
- 索引状态监控

### 1.2 模块定位

```
知识库前置维护
      │
      ├─ 文档上传 → 解析 → 索引 → 可检索
      │
      ├─ 知识就绪检查 → 阻止无知识时创建需求
      │
      └─ 为后续 Agent 分析提供知识支撑
```

## 2. 文档管理

### 2.1 支持的文档类型

| 类型 | 扩展名 | 说明 |
|------|--------|------|
| **Markdown** | .md | 技术文档、README |
| **PDF** | .pdf | 规范文档、报告 |
| **Word** | .docx | 需求文档 |
| **Text** | .txt | 纯文本 |
| **Code** | .py, .js, .java 等 | 代码文件 |
| **Config** | .yaml, .json | 配置文件 |

### 2.2 文档数据模型

```python
class Document:
    id: str                    # 文档 ID
    project_id: str            # 所属项目
    name: str                  # 文档名称
    type: DocumentType         # 文档类型
    content: str               # 原始内容
    size: int                  # 文件大小
    status: DocumentStatus     # 处理状态
    index_status: IndexStatus  # 索引状态
    created_at: datetime       # 创建时间
    indexed_at: datetime       # 索引时间
    metadata: dict             # 元数据
```

### 2.3 文档状态流转

```
上传 → pending → processing → indexed
                      │
                      └─→ failed (处理失败)
```

| 状态 | 说明 |
|------|------|
| `pending` | 等待处理 |
| `processing` | 处理中 |
| `indexed` | 已索引 |
| `failed` | 处理失败 |

## 3. 文档上传

### 3.1 上传 API

```http
POST /api/v1/knowledge/documents
Content-Type: multipart/form-data

file: (binary)
project_id: proj_123
tags: ["架构", "API"]
```

响应：
```json
{
  "id": "doc_abc123",
  "name": "architecture.md",
  "status": "pending",
  "message": "文档已上传，正在处理"
}
```

### 3.2 批量上传

```http
POST /api/v1/knowledge/documents/batch
Content-Type: multipart/form-data

files: [(binary), (binary), ...]
project_id: proj_123
```

### 3.3 上传限制

| 限制项 | 值 |
|--------|-----|
| 单文件最大 | 50MB |
| 批量最大数量 | 20 |
| 支持的编码 | UTF-8 |

## 4. 文档处理

### 4.1 处理流程

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  上传    │───▶│  解析    │───▶│  分块    │───▶│  向量化  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
                                                      │
┌──────────┐    ┌──────────┐    ┌──────────┐         │
│  可检索  │◀───│  存储    │◀───│  索引    │◀────────┘
└──────────┘    └──────────┘    └──────────┘
```

### 4.2 文档解析

不同类型文档的解析策略：

| 类型 | 解析方式 |
|------|----------|
| Markdown | 标题结构解析 |
| PDF | PyPDF2/pdfplumber |
| Word | python-docx |
| Code | AST 解析 + 注释提取 |
| Config | YAML/JSON 解析 |

### 4.3 分块策略

```python
# 分块配置
chunk_config = {
    "chunk_size": 1000,      # 每块字符数
    "chunk_overlap": 200,     # 重叠字符数
    "separator": "\n\n",      # 分隔符
    "length_function": len    # 长度函数
}
```

### 4.4 向量化

使用嵌入模型将文本转换为向量：

```python
# 嵌入配置
embedding_config = {
    "model": "text-embedding-ada-002",
    "dimension": 1536,
    "batch_size": 100
}
```

## 5. 知识就绪检查

### 5.1 检查机制

知识就绪检查中间件会在创建需求前验证知识库状态：

```python
class KnowledgeCheckMiddleware:
    async def check_readiness(self, project_id: str) -> bool:
        # 检查文档数量
        doc_count = await get_document_count(project_id)
        if doc_count < MIN_DOCUMENTS:
            return False
        
        # 检查索引状态
        indexed_count = await get_indexed_count(project_id)
        if indexed_count / doc_count < MIN_INDEX_RATIO:
            return False
        
        return True
```

### 5.2 就绪条件

| 条件 | 默认值 | 说明 |
|------|--------|------|
| 最少文档数 | 1 | 至少有一个文档 |
| 索引比例 | 80% | 80% 文档已索引 |
| 无处理中 | - | 无正在处理的文档 |

### 5.3 检查 API

```http
GET /api/v1/knowledge/readiness?project_id={project_id}
```

响应：
```json
{
  "ready": true,
  "details": {
    "total_documents": 10,
    "indexed_documents": 9,
    "processing_documents": 1,
    "failed_documents": 0,
    "index_ratio": 0.9
  }
}
```

### 5.4 绕过检查

项目设置中可以配置是否强制检查：

```yaml
project_settings:
  knowledge_required: true  # 设为 false 可绕过检查
```

## 6. 索引管理

### 6.1 索引操作

#### 重建索引

```http
POST /api/v1/knowledge/reindex
Content-Type: application/json

{
  "project_id": "proj_123",
  "document_ids": ["doc_1", "doc_2"]  // 可选，不传则全部重建
}
```

#### 删除索引

```http
DELETE /api/v1/knowledge/documents/{document_id}/index
```

### 6.2 索引状态查询

```http
GET /api/v1/knowledge/index-status?project_id={project_id}
```

响应：
```json
{
  "project_id": "proj_123",
  "total_documents": 10,
  "index_stats": {
    "pending": 1,
    "processing": 0,
    "indexed": 8,
    "failed": 1
  },
  "last_updated": "2024-01-15T10:30:00Z"
}
```

### 6.3 失败处理

索引失败的文档会记录失败原因：

```json
{
  "id": "doc_failed",
  "status": "failed",
  "error": {
    "code": "PARSE_ERROR",
    "message": "无法解析 PDF 文件",
    "details": "PDF 文件已损坏或加密"
  }
}
```

## 7. 文档搜索

### 7.1 搜索 API

```http
POST /api/v1/knowledge/search
Content-Type: application/json

{
  "project_id": "proj_123",
  "query": "如何配置数据库连接",
  "top_k": 5,
  "filters": {
    "type": ["md", "txt"],
    "tags": ["配置"]
  }
}
```

响应：
```json
{
  "results": [
    {
      "document_id": "doc_1",
      "document_name": "database-config.md",
      "content": "数据库连接配置说明...",
      "score": 0.95,
      "metadata": {
        "section": "配置说明",
        "line_start": 10,
        "line_end": 25
      }
    }
  ],
  "total": 3,
  "query_time_ms": 45
}
```

### 7.2 搜索参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `query` | string | 必填 | 搜索查询 |
| `top_k` | int | 5 | 返回数量 |
| `threshold` | float | 0.7 | 相似度阈值 |
| `filters` | object | - | 过滤条件 |

## 8. 使用场景

### 8.1 新项目初始化

```
1. 创建项目
2. 上传项目文档（README、架构文档、API 文档等）
3. 等待索引完成
4. 知识就绪后开始创建需求
```

### 8.2 知识更新

```
1. 上传新文档或更新文档
2. 系统自动重新索引
3. 新知识立即可用于分析
```

### 8.3 知识检索增强

```
1. 用户提交需求
2. Lead Agent 检索相关知识
3. 结合知识生成更准确的分析
```

## 9. 最佳实践

### 9.1 文档组织

1. **分类清晰**
   - 架构文档放一起
   - API 文档放一起
   - 运维手册放一起

2. **命名规范**
   - 使用有意义的文件名
   - 包含版本或日期

3. **内容质量**
   - 保持文档更新
   - 使用标准格式

### 9.2 索引优化

1. **合理分块**
   - 代码类文档按函数/类分块
   - 文档类按章节分块

2. **元数据丰富**
   - 添加标签
   - 填写描述

3. **定期维护**
   - 删除过期文档
   - 重建损坏索引

## 10. 常见问题

### Q1: 文档上传后多久可以搜索？

取决于文档大小和系统负载，通常：
- 小文档（<1MB）：几秒
- 大文档（>10MB）：几分钟

### Q2: 索引失败如何处理？

1. 检查失败原因
2. 修复文档问题（编码、格式等）
3. 重新上传或手动触发重建索引

### Q3: 如何提高搜索准确性？

1. 使用更精确的关键词
2. 添加过滤条件
3. 提高文档质量
4. 丰富文档元数据

---

*文档版本: 1.0*
*所属模块: M2 - 知识库前置维护*
