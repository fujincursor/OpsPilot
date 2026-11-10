# M3: 知识库与系统理解模块

## 1. 模块概述

知识库与系统理解模块负责构建和维护项目的知识体系，使 AI Agent 能够深入理解项目上下文，提供更准确的分析和建议。

### 1.1 核心功能

- 知识库智能检索
- 上下文理解增强
- 知识关联分析
- 知识图谱构建（规划中）

### 1.2 模块定位

```
知识库与系统理解
      │
      ├─ 智能检索 → 语义搜索 + 关键词匹配
      │
      ├─ 上下文增强 → 为 Agent 提供背景知识
      │
      └─ 知识关联 → 发现相关知识和案例
```

## 2. 智能检索

### 2.1 检索架构

```
┌──────────────────────────────────────────────────────────┐
│                     查询处理层                            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐         │
│  │ 查询理解   │  │ 查询扩展   │  │ 意图识别   │         │
│  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘         │
└─────────┼───────────────┼───────────────┼───────────────┘
          │               │               │
          ▼               ▼               ▼
┌──────────────────────────────────────────────────────────┐
│                     检索执行层                            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐         │
│  │ 向量检索   │  │ 关键词检索 │  │ 混合检索   │         │
│  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘         │
└─────────┼───────────────┼───────────────┼───────────────┘
          │               │               │
          ▼               ▼               ▼
┌──────────────────────────────────────────────────────────┐
│                     结果处理层                            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐         │
│  │ 结果融合   │  │ 重排序     │  │ 摘要生成   │         │
│  └────────────┘  └────────────┘  └────────────┘         │
└──────────────────────────────────────────────────────────┘
```

### 2.2 向量检索

基于语义相似度的检索：

```python
async def vector_search(query: str, project_id: str, top_k: int = 5):
    # 1. 将查询转换为向量
    query_vector = await embed_text(query)
    
    # 2. 在向量库中搜索
    results = await vector_db.search(
        collection=f"project_{project_id}",
        vector=query_vector,
        top_k=top_k,
        metric="cosine"
    )
    
    # 3. 返回结果
    return results
```

### 2.3 关键词检索

基于关键词匹配的检索：

```python
async def keyword_search(query: str, project_id: str, top_k: int = 5):
    # 1. 提取关键词
    keywords = extract_keywords(query)
    
    # 2. 全文搜索
    results = await full_text_search(
        project_id=project_id,
        keywords=keywords,
        top_k=top_k
    )
    
    return results
```

### 2.4 混合检索

结合向量和关键词检索：

```python
async def hybrid_search(query: str, project_id: str, top_k: int = 5):
    # 并行执行两种检索
    vector_results, keyword_results = await asyncio.gather(
        vector_search(query, project_id, top_k * 2),
        keyword_search(query, project_id, top_k * 2)
    )
    
    # 融合结果
    merged = merge_results(
        vector_results, 
        keyword_results,
        vector_weight=0.7,
        keyword_weight=0.3
    )
    
    # 重排序
    reranked = await rerank(query, merged, top_k)
    
    return reranked
```

## 3. 上下文增强

### 3.1 上下文构建

为 Agent 构建丰富的上下文：

```python
async def build_context(requirement: str, project_id: str) -> Context:
    # 1. 检索相关知识
    knowledge = await hybrid_search(requirement, project_id, top_k=5)
    
    # 2. 检索历史案例
    similar_cases = await search_similar_cases(requirement, project_id)
    
    # 3. 获取项目信息
    project_info = await get_project_info(project_id)
    
    # 4. 构建上下文
    context = Context(
        knowledge=knowledge,
        similar_cases=similar_cases,
        project_info=project_info,
        timestamp=datetime.now()
    )
    
    return context
```

### 3.2 上下文注入

将上下文注入到 Agent 提示词中：

```python
def inject_context(prompt: str, context: Context) -> str:
    context_section = f"""
## 项目背景
{context.project_info.description}

## 相关知识
{format_knowledge(context.knowledge)}

## 历史案例
{format_cases(context.similar_cases)}
"""
    return prompt.replace("{context}", context_section)
```

### 3.3 上下文压缩

当上下文过长时进行压缩：

```python
async def compress_context(context: Context, max_tokens: int) -> Context:
    current_tokens = count_tokens(context)
    
    if current_tokens <= max_tokens:
        return context
    
    # 按重要性排序并截断
    context.knowledge = prioritize_and_truncate(
        context.knowledge, 
        max_tokens // 3
    )
    context.similar_cases = prioritize_and_truncate(
        context.similar_cases,
        max_tokens // 3
    )
    
    return context
```

## 4. 知识关联分析

### 4.1 相似案例发现

```python
async def find_similar_cases(requirement: str, project_id: str) -> List[Case]:
    # 向量相似度搜索历史需求
    similar = await vector_search(
        query=requirement,
        collection=f"requirements_{project_id}",
        top_k=5
    )
    
    # 获取完整案例信息
    cases = []
    for item in similar:
        case = await get_case_details(item.id)
        cases.append(case)
    
    return cases
```

### 4.2 知识关联

```python
async def find_related_knowledge(document_id: str) -> List[Document]:
    # 获取文档向量
    doc_vector = await get_document_vector(document_id)
    
    # 搜索相关文档
    related = await vector_db.search(
        vector=doc_vector,
        top_k=10,
        exclude=[document_id]
    )
    
    return related
```

### 4.3 标签推荐

```python
async def recommend_tags(content: str, existing_tags: List[str]) -> List[str]:
    # 提取关键词
    keywords = extract_keywords(content)
    
    # 匹配已有标签
    matched = match_existing_tags(keywords, existing_tags)
    
    # 生成新标签建议
    suggested = await generate_tag_suggestions(content, matched)
    
    return matched + suggested
```

## 5. 知识检索 Skill

### 5.1 Skill 定义

`knowledge-retrieval` Skill 提供知识检索能力：

```markdown
# knowledge-retrieval Skill

## 功能
- 搜索项目知识库
- 检索历史案例
- 获取相关文档

## 使用场景
- 分析需求时查询背景知识
- 设计方案时参考历史实现
- 解决问题时查找解决方案
```

### 5.2 Skill 调用

Agent 调用 knowledge-retrieval Skill：

```python
# Lead Agent 调用
result = await call_skill(
    skill="knowledge-retrieval",
    params={
        "query": "数据库连接池配置",
        "project_id": "proj_123",
        "top_k": 5
    }
)
```

## 6. 搜索 API

### 6.1 基础搜索

```http
POST /api/v1/knowledge/search
Content-Type: application/json

{
  "project_id": "proj_123",
  "query": "如何优化 API 响应时间",
  "top_k": 5,
  "search_type": "hybrid"
}
```

### 6.2 高级搜索

```http
POST /api/v1/knowledge/search/advanced
Content-Type: application/json

{
  "project_id": "proj_123",
  "query": "性能优化",
  "filters": {
    "document_type": ["md", "pdf"],
    "tags": ["性能", "优化"],
    "date_range": {
      "start": "2024-01-01",
      "end": "2024-12-31"
    }
  },
  "options": {
    "include_similar_cases": true,
    "include_related_docs": true,
    "highlight": true
  }
}
```

### 6.3 案例搜索

```http
POST /api/v1/knowledge/cases/search
Content-Type: application/json

{
  "project_id": "proj_123",
  "query": "登录失败 500 错误",
  "status": ["resolved"],
  "top_k": 5
}
```

## 7. 知识质量评估

### 7.1 评估指标

| 指标 | 说明 | 目标 |
|------|------|------|
| **覆盖度** | 知识覆盖项目各方面的程度 | > 80% |
| **新鲜度** | 文档更新的及时性 | < 30天 |
| **准确性** | 知识内容的正确性 | > 95% |
| **可检索性** | 能被有效检索的比例 | > 90% |

### 7.2 质量报告

```http
GET /api/v1/knowledge/quality-report?project_id={project_id}
```

响应：
```json
{
  "project_id": "proj_123",
  "report_date": "2024-01-15",
  "metrics": {
    "coverage": {
      "score": 0.85,
      "details": {
        "architecture": 0.9,
        "api": 0.8,
        "deployment": 0.85
      }
    },
    "freshness": {
      "score": 0.75,
      "stale_documents": 5,
      "avg_age_days": 25
    },
    "retrievability": {
      "score": 0.92,
      "indexed_ratio": 0.95
    }
  },
  "recommendations": [
    "更新 5 个过期文档",
    "补充部署相关文档"
  ]
}
```

## 8. 最佳实践

### 8.1 提高检索效果

1. **优化查询**
   - 使用清晰、具体的查询词
   - 包含关键技术术语
   - 避免过于宽泛的描述

2. **丰富知识库**
   - 定期更新文档
   - 添加案例和经验总结
   - 维护标签体系

3. **调整参数**
   - 根据场景选择检索类型
   - 调整 top_k 获取合适数量
   - 设置合理的相似度阈值

### 8.2 知识维护

1. **定期审查**
   - 检查过期文档
   - 验证内容准确性
   - 更新变更内容

2. **结构优化**
   - 合理组织文档结构
   - 使用一致的格式
   - 添加适当的元数据

## 9. 常见问题

### Q1: 搜索结果不相关怎么办？

1. 优化查询表述
2. 使用更具体的关键词
3. 添加过滤条件
4. 检查文档质量

### Q2: 如何提高知识覆盖度？

1. 分析知识盲区
2. 补充缺失文档
3. 整理历史经验
4. 导入外部知识

### Q3: 上下文太长影响分析怎么办？

系统会自动：
1. 压缩上下文
2. 保留最相关内容
3. 按重要性排序

也可以手动调整 top_k 参数。

---

*文档版本: 1.0*
*所属模块: M3 - 知识库与系统理解*
