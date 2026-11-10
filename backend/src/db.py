"""SQLite 文档存储。

业务对象以 JSON 写入本地数据库，服务重启后可以重新加载。
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import DateTime, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


def _database_url() -> str:
    backend_dir = Path(__file__).resolve().parents[1]
    data_dir = backend_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    default_path = data_dir / "opspilot.db"

    raw = os.getenv("DATABASE_URL", "").strip()
    if raw.startswith("sqlite:///"):
        path_part = raw.removeprefix("sqlite:///")
        if path_part in {"", "./opspilot.db", "opspilot.db"} or path_part.startswith("./"):
            return f"sqlite:///{default_path.as_posix()}"
        path = Path(path_part)
        if not path.is_absolute():
            path = (backend_dir / path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{path.as_posix()}"
    return f"sqlite:///{default_path.as_posix()}"


class Base(DeclarativeBase):
    pass


class StoredRecord(Base):
    __tablename__ = "records"

    collection: Mapped[str] = mapped_column(String(64), primary_key=True)
    record_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


_engine = create_engine(
    _database_url(),
    connect_args={"check_same_thread": False},
)
Base.metadata.create_all(_engine)
_lock = threading.Lock()
_registry: list["DocumentDict"] = []


def _dump_value(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [_dump_value(item) for item in value]
    raise TypeError(f"无法持久化的数据类型: {type(value)!r}")


def _upsert(collection: str, record_id: str, value: Any) -> None:
    payload = json.dumps(_dump_value(value), ensure_ascii=False)
    with _lock:
        with Session(_engine) as session:
            row = session.get(StoredRecord, (collection, record_id))
            if row is None:
                row = StoredRecord(
                    collection=collection,
                    record_id=record_id,
                    payload=payload,
                    updated_at=datetime.utcnow(),
                )
                session.add(row)
            else:
                row.payload = payload
                row.updated_at = datetime.utcnow()
            session.commit()


def _delete(collection: str, record_id: str) -> None:
    with _lock:
        with Session(_engine) as session:
            row = session.get(StoredRecord, (collection, record_id))
            if row is not None:
                session.delete(row)
                session.commit()


def _load_rows(collection: str) -> list[tuple[str, Any]]:
    with _lock:
        with Session(_engine) as session:
            rows = session.scalars(
                select(StoredRecord).where(StoredRecord.collection == collection)
            ).all()
            return [(row.record_id, json.loads(row.payload)) for row in rows]


def flush_registered() -> None:
    """把已注册集合中的当前对象再次写入数据库。"""
    for store in list(_registry):
        store.flush()


class DocumentDict(dict):
    """带数据库持久化的字典。赋值和删除会立即写入。"""

    def __init__(
        self,
        collection: str,
        *,
        model: type[BaseModel] | None = None,
        loader: Callable[[Any], Any] | None = None,
        key_type: Callable[[str], Any] = UUID,
    ):
        super().__init__()
        self.collection = collection
        self.model = model
        self.loader = loader
        self.key_type = key_type
        for record_id, payload in _load_rows(collection):
            super().__setitem__(self.key_type(record_id), self._load_value(payload))
        _registry.append(self)

    def _load_value(self, payload: Any) -> Any:
        if self.loader is not None:
            return self.loader(payload)
        if self.model is None:
            raise TypeError(f"集合 {self.collection} 缺少模型")
        return self.model.model_validate(payload)

    def __setitem__(self, key: Any, value: Any) -> None:
        super().__setitem__(key, value)
        _upsert(self.collection, str(key), value)

    def __delitem__(self, key: Any) -> None:
        super().__delitem__(key)
        _delete(self.collection, str(key))

    def pop(self, key: Any, *args: Any) -> Any:
        if key in self:
            value = super().pop(key)
            _delete(self.collection, str(key))
            return value
        if args:
            return args[0]
        raise KeyError(key)

    def flush(self) -> None:
        for key, value in list(self.items()):
            _upsert(self.collection, str(key), value)
