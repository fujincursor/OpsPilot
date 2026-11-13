"""SQLite 关系库。

服务仍通过 DocumentDict 读写业务对象。对象按表保存，请求结束时只回写有改动的对象。
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from pathlib import Path
from typing import Any, Callable
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from . import store
from .schema import Base


def database_path() -> Path:
    backend_dir = Path(__file__).resolve().parents[1]
    data_dir = backend_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    default_path = data_dir / "opspilot.db"

    raw = os.getenv("DATABASE_URL", "").strip()
    if raw.startswith("sqlite:///"):
        path_part = raw.removeprefix("sqlite:///")
        if path_part in {"", "./opspilot.db", "opspilot.db"} or path_part.startswith("./"):
            return default_path
        path = Path(path_part)
        if not path.is_absolute():
            path = (backend_dir / path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    return default_path


def _table_names(path: Path) -> set[str]:
    if not path.exists() or path.stat().st_size == 0:
        return set()
    connection = sqlite3.connect(path)
    try:
        rows = connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return {row[0] for row in rows}
    finally:
        connection.close()


def _retire_legacy(path: Path) -> None:
    """旧 JSON 库只改名，不读取、不复制其中的业务记录。"""
    names = _table_names(path)
    if "records" not in names or "users" in names:
        return
    target = path.with_name("opspilot.legacy.db")
    if target.exists():
        stamp = int(path.stat().st_mtime)
        target = path.with_name(f"opspilot.legacy.{stamp}.db")
    try:
        path.rename(target)
    except PermissionError as exc:
        raise RuntimeError("opspilot.db 正被占用，请先停止后端后再启动，以便换成空的关系库") from exc


def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def init_database():
    path = database_path()
    _retire_legacy(path)
    engine = create_engine(
        f"sqlite:///{path.as_posix()}",
        connect_args={"check_same_thread": False},
    )
    event.listen(engine, "connect", _enable_foreign_keys)
    Base.metadata.create_all(engine)
    store.bind(engine)
    from .seeds import seed_if_empty

    seed_if_empty(engine)
    return engine


_engine = init_database()
_lock = threading.Lock()
_registry: list["DocumentDict"] = []


def _fingerprint(value: Any) -> str:
    if isinstance(value, BaseModel):
        payload = value.model_dump(mode="json")
    elif isinstance(value, list):
        payload = [
            item.model_dump(mode="json") if isinstance(item, BaseModel) else item
            for item in value
        ]
    else:
        payload = value
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)


class DocumentDict(dict):
    """带关系表持久化的字典。赋值和删除会立即写入，原地修改在请求结束时写入。"""

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
        self._fingerprints: dict[str, str] = {}
        with _lock:
            loaded = store.load_all(collection, model, loader, key_type)
        for key, value in loaded:
            super().__setitem__(key, value)
            self._fingerprints[str(key)] = _fingerprint(value)
        _registry.append(self)

    def __setitem__(self, key: Any, value: Any) -> None:
        super().__setitem__(key, value)
        with _lock:
            store.save(self.collection, key, value)
        self._fingerprints[str(key)] = _fingerprint(value)

    def __delitem__(self, key: Any) -> None:
        super().__delitem__(key)
        with _lock:
            store.remove(self.collection, key)
        self._fingerprints.pop(str(key), None)

    def pop(self, key: Any, *args: Any) -> Any:
        if key in self:
            value = super().pop(key)
            with _lock:
                store.remove(self.collection, key)
            self._fingerprints.pop(str(key), None)
            return value
        if args:
            return args[0]
        raise KeyError(key)

    def flush_dirty(self) -> None:
        for key, value in list(self.items()):
            fingerprint = _fingerprint(value)
            if self._fingerprints.get(str(key)) == fingerprint:
                continue
            with _lock:
                store.save(self.collection, key, value)
            self._fingerprints[str(key)] = fingerprint


def flush_dirty() -> None:
    """把请求过程中原地改过的对象写回关系表。"""
    for document_store in list(_registry):
        document_store.flush_dirty()


def flush_registered() -> None:
    flush_dirty()


def session() -> Session:
    return store.session()
