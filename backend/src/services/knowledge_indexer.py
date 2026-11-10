"""知识文档处理：解析、分块、向量化。"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
from typing import Iterable

import yaml

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
LOCAL_EMBEDDING_MODEL = "local-hash-256"
EMBEDDING_DIMENSION = 256
_TOKEN_PATTERN = re.compile(r"[\u4e00-\u9fff]|[a-zA-Z0-9_]+")


def parse_document(content: str | None, file_type: str | None) -> str:
    """按文件类型把上传内容整理成可分块的纯文本。"""
    text = (content or "").replace("\x00", "").strip()
    if not text:
        raise ValueError("文档内容为空，无法解析")

    kind = (file_type or "").lower().lstrip(".")
    if kind == "json":
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return text
        return json.dumps(parsed, ensure_ascii=False, indent=2)
    if kind in {"yaml", "yml"}:
        try:
            parsed = yaml.safe_load(text)
        except yaml.YAMLError:
            return text
        if parsed is None:
            return text
        return yaml.safe_dump(parsed, allow_unicode=True, sort_keys=False).strip()
    return text


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """按固定长度和重叠切分文本。"""
    normalized = re.sub(r"\n{3,}", "\n\n", text).strip()
    if len(normalized) <= chunk_size:
        return [normalized]

    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(len(normalized), start + chunk_size)
        piece = normalized[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(normalized):
            break
        start = max(0, end - overlap)
    return chunks


def _usable_api_key(*names: str) -> str:
    for name in names:
        value = os.getenv(name, "").strip().strip('"').strip("'")
        if not value:
            continue
        lowered = value.lower()
        if "your-" in lowered or lowered.endswith("api-key") or "xxx" in lowered:
            continue
        return value
    return ""


def _local_embed(text: str) -> list[float]:
    vector = [0.0] * EMBEDDING_DIMENSION
    tokens = _TOKEN_PATTERN.findall(text.lower())
    if not tokens:
        return vector
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "little") % EMBEDDING_DIMENSION
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    return _normalize(vector)


def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def embed_texts(texts: Iterable[str]) -> tuple[str, list[list[float]]]:
    """把文本转成同一空间中的向量。没有可用的嵌入接口时使用本地哈希向量。"""
    items = list(texts)
    api_key = _usable_api_key("EMBEDDING_API_KEY", "OPENAI_API_KEY")
    if api_key:
        try:
            return _remote_embed(items, api_key)
        except Exception:
            pass
    return LOCAL_EMBEDDING_MODEL, [_local_embed(text) for text in items]


def _remote_embed(texts: list[str], api_key: str) -> tuple[str, list[list[float]]]:
    import httpx

    base_url = os.getenv("EMBEDDING_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    response = httpx.post(
        f"{base_url}/embeddings",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": model, "input": texts},
        timeout=60.0,
    )
    response.raise_for_status()
    payload = response.json()
    ordered = sorted(payload["data"], key=lambda item: item["index"])
    vectors = [_normalize(item["embedding"]) for item in ordered]
    if len(vectors) != len(texts):
        raise ValueError("嵌入接口返回的向量数量与文本数量不一致")
    return model, vectors


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return sum(a * b for a, b in zip(left, right))
