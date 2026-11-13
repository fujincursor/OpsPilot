"""本机 Qdrant 中的知识分块。"""

from __future__ import annotations

from uuid import UUID

from ..config import get_settings

COLLECTION = "opspilot_chunks"


class VectorStoreUnavailable(RuntimeError):
    """Qdrant 没有启动，或当前无法完成向量读写。"""


def upsert_chunks(points: list[dict]) -> None:
    """写入或覆盖一批分块。points 含 id、vector 和 payload。"""
    if not points:
        return

    def write():
        client = _client()
        _ensure_collection(client, len(points[0]["vector"]))
        from qdrant_client.models import PointStruct

        client.upsert(
            collection_name=COLLECTION,
            points=[
                PointStruct(id=str(item["id"]), vector=item["vector"], payload=item["payload"])
                for item in points
            ],
        )

    _call(write)


def delete_document(document_id: UUID) -> None:
    """删除一篇文档的全部分块。"""

    def remove():
        client = _client()
        if not _collection_exists(client):
            return
        from qdrant_client.models import Filter, FieldCondition, FilterSelector, MatchValue

        client.delete(
            collection_name=COLLECTION,
            points_selector=FilterSelector(
                filter=Filter(must=[
                    FieldCondition(key="document_id", match=MatchValue(value=str(document_id))),
                ])
            ),
        )

    _call(remove)


def search(vector: list[float], knowledge_base_ids: list[str], model_name: str, limit: int) -> list[dict]:
    """按知识库和向量模型过滤后做余弦检索。"""
    if not knowledge_base_ids:
        return []

    def query():
        client = _client()
        if not _collection_exists(client):
            return []
        from qdrant_client.models import FieldCondition, Filter, MatchAny, MatchValue

        query_filter = Filter(must=[
            FieldCondition(key="knowledge_base_id", match=MatchAny(any=knowledge_base_ids)),
            FieldCondition(key="embedding_model", match=MatchValue(value=model_name)),
        ])
        response = client.query_points(
            collection_name=COLLECTION,
            query=vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        )
        return [
            {"id": str(point.id), "score": float(point.score or 0), "payload": point.payload or {}}
            for point in response.points
        ]

    return _call(query)


def _client():
    from qdrant_client import QdrantClient

    settings = get_settings()
    _ensure_reachable(settings.qdrant_url)
    return QdrantClient(
        url=settings.qdrant_url,
        timeout=3,
        prefer_grpc=False,
        check_compatibility=False,
    )


def _ensure_reachable(url: str) -> None:
    import socket
    from urllib.parse import urlparse

    parsed = urlparse(url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (443 if parsed.scheme == "https" else 6333)
    probe = socket.socket()
    probe.settimeout(2)
    try:
        probe.connect((host, port))
    except OSError as exc:
        raise VectorStoreUnavailable(f"Qdrant 未启动或无法连接（{url}）：{exc}") from exc
    finally:
        probe.close()


def _collection_exists(client) -> bool:
    try:
        return bool(client.collection_exists(COLLECTION))
    except Exception:
        names = {item.name for item in client.get_collections().collections}
        return COLLECTION in names


def _ensure_collection(client, dimension: int) -> None:
    if _collection_exists(client):
        info = client.get_collection(COLLECTION)
        vectors = info.config.params.vectors
        size = vectors.size if hasattr(vectors, "size") else vectors["size"]
        if int(size) != dimension:
            raise VectorStoreUnavailable(
                f"Qdrant 集合 {COLLECTION} 的维度是 {size}，当前嵌入维度是 {dimension}"
            )
        return
    from qdrant_client.models import Distance, VectorParams

    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
    )


def _call(action):
    try:
        return action()
    except VectorStoreUnavailable:
        raise
    except Exception as exc:
        url = get_settings().qdrant_url
        raise VectorStoreUnavailable(f"Qdrant 未启动或无法连接（{url}）：{exc}") from exc
