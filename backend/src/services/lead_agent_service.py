"""Lead Agent 模拟服务

模拟 DeerFlow 2.0 架构中的 Lead Agent 功能：
- 需求分析与分类
- 关键词提取
- 优先级建议
"""

import re
from typing import List, Tuple

from ..models.requirement import (
    RequirementType,
    RequirementPriority,
    RequirementAnalysis,
)


class LeadAgentService:
    """Lead Agent 模拟服务

    负责分析需求文本，提取关键信息，进行智能分类。
    当前为规则引擎实现，后续可接入 LLM 进行智能分析。
    """

    BUG_KEYWORDS = [
        "bug", "错误", "异常", "报错", "崩溃", "crash", "error", "exception",
        "失败", "故障", "问题", "修复", "fix", "无法", "不能", "不工作",
        "500", "404", "超时", "timeout", "卡死", "挂了", "宕机", "down",
        "内存泄漏", "memory leak", "死循环", "无响应", "慢", "性能问题"
    ]

    FEATURE_KEYWORDS = [
        "新增", "添加", "实现", "开发", "feature", "功能", "需求",
        "优化", "改进", "升级", "enhance", "支持", "增加", "扩展",
        "集成", "对接", "接入", "新功能", "重构", "refactor", "设计"
    ]

    QUESTION_KEYWORDS = [
        "怎么", "如何", "什么", "为什么", "能否", "是否", "请问",
        "咨询", "疑问", "question", "how", "what", "why", "?", "？",
        "帮助", "help", "文档", "说明", "解释", "教程"
    ]

    CRITICAL_KEYWORDS = [
        "紧急", "urgent", "critical", "严重", "生产", "production",
        "线上", "阻塞", "blocker", "P0", "立即", "马上", "尽快",
        "全站", "全部用户", "所有", "宕机", "瘫痪", "数据丢失"
    ]

    HIGH_KEYWORDS = [
        "重要", "important", "高优先级", "high", "P1", "关键",
        "核心", "主要", "影响大", "多用户", "频繁"
    ]

    LOW_KEYWORDS = [
        "低优先级", "low", "P3", "次要", "可选", "有空", "不急",
        "小问题", "建议", "优化建议", "nice to have", "后续"
    ]

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        """预编译正则表达式以提升性能"""
        self._bug_pattern = self._create_pattern(self.BUG_KEYWORDS)
        self._feature_pattern = self._create_pattern(self.FEATURE_KEYWORDS)
        self._question_pattern = self._create_pattern(self.QUESTION_KEYWORDS)
        self._critical_pattern = self._create_pattern(self.CRITICAL_KEYWORDS)
        self._high_pattern = self._create_pattern(self.HIGH_KEYWORDS)
        self._low_pattern = self._create_pattern(self.LOW_KEYWORDS)

    def _create_pattern(self, keywords: List[str]) -> re.Pattern:
        """创建关键词匹配的正则表达式"""
        escaped = [re.escape(kw) for kw in keywords]
        pattern = "|".join(escaped)
        return re.compile(pattern, re.IGNORECASE)

    def analyze_requirement(self, text: str) -> RequirementAnalysis:
        """分析需求文本

        综合分析需求文本，返回类型、优先级、关键词和置信度。

        Args:
            text: 需求文本（标题 + 描述）

        Returns:
            RequirementAnalysis: 分析结果
        """
        req_type, type_confidence = self.classify_type(text)
        priority, priority_confidence = self.suggest_priority(text)
        keywords = self.extract_keywords(text)

        overall_confidence = (type_confidence + priority_confidence) / 2

        return RequirementAnalysis(
            type=req_type,
            priority=priority,
            keywords=keywords,
            confidence=round(overall_confidence, 2)
        )

    def classify_type(self, text: str) -> Tuple[RequirementType, float]:
        """根据关键词分类需求类型

        Args:
            text: 需求文本

        Returns:
            Tuple[RequirementType, float]: (需求类型, 置信度)
        """
        text_lower = text.lower()

        bug_matches = len(self._bug_pattern.findall(text_lower))
        feature_matches = len(self._feature_pattern.findall(text_lower))
        question_matches = len(self._question_pattern.findall(text_lower))

        total_matches = bug_matches + feature_matches + question_matches

        if total_matches == 0:
            return RequirementType.FEATURE, 0.5

        scores = {
            RequirementType.BUG: bug_matches,
            RequirementType.FEATURE: feature_matches,
            RequirementType.QUESTION: question_matches,
        }

        max_type = max(scores, key=scores.get)
        confidence = scores[max_type] / total_matches if total_matches > 0 else 0.5

        confidence = min(0.95, 0.5 + confidence * 0.45)

        return max_type, confidence

    def suggest_priority(self, text: str) -> Tuple[RequirementPriority, float]:
        """建议需求优先级

        Args:
            text: 需求文本

        Returns:
            Tuple[RequirementPriority, float]: (优先级, 置信度)
        """
        text_lower = text.lower()

        critical_matches = len(self._critical_pattern.findall(text_lower))
        high_matches = len(self._high_pattern.findall(text_lower))
        low_matches = len(self._low_pattern.findall(text_lower))

        if critical_matches > 0:
            confidence = min(0.95, 0.7 + critical_matches * 0.05)
            return RequirementPriority.CRITICAL, confidence

        if high_matches > low_matches:
            confidence = min(0.9, 0.6 + high_matches * 0.05)
            return RequirementPriority.HIGH, confidence

        if low_matches > high_matches:
            confidence = min(0.85, 0.6 + low_matches * 0.05)
            return RequirementPriority.LOW, confidence

        return RequirementPriority.MEDIUM, 0.6

    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """提取关键词

        从文本中提取与运维相关的关键词。

        Args:
            text: 需求文本
            max_keywords: 最大关键词数量

        Returns:
            List[str]: 关键词列表
        """
        all_keywords = (
            self.BUG_KEYWORDS +
            self.FEATURE_KEYWORDS +
            self.QUESTION_KEYWORDS +
            self.CRITICAL_KEYWORDS +
            self.HIGH_KEYWORDS +
            self.LOW_KEYWORDS
        )

        text_lower = text.lower()
        found_keywords = []

        for keyword in all_keywords:
            if keyword.lower() in text_lower and keyword not in found_keywords:
                found_keywords.append(keyword)
                if len(found_keywords) >= max_keywords:
                    break

        tech_pattern = r'\b(API|SDK|DB|SQL|HTTP|HTTPS|TCP|UDP|DNS|CDN|K8s|Docker|Redis|MySQL|PostgreSQL|MongoDB|Kafka|RabbitMQ|Nginx|Jenkins|GitLab|GitHub|CI/CD|AWS|Azure|GCP|CPU|内存|磁盘|网络|日志|监控|告警|部署|发布|回滚|配置|权限|安全)\b'
        tech_matches = re.findall(tech_pattern, text, re.IGNORECASE)

        for match in tech_matches:
            if match not in found_keywords:
                found_keywords.append(match)
                if len(found_keywords) >= max_keywords:
                    break

        return found_keywords[:max_keywords]


lead_agent_service = LeadAgentService()
