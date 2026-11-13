"""用户服务。用户保存在数据库中。"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from ..db import DocumentDict
from ..models.user import User, UserCreate
from ..api.middleware.auth import get_password_hash, verify_password


class UserService:
    """用户服务。用户保存在数据库中。"""

    _users: DocumentDict | None = None
    _initialized: bool = False

    @classmethod
    def _init_default_users(cls) -> None:
        """从关系库加载用户。测试账号在空库初始化时写入，这里不再补插。"""
        if cls._initialized:
            return
        cls._users = DocumentDict("users", model=User, key_type=str)
        cls._initialized = True

    @classmethod
    def get_by_id(cls, user_id: str) -> Optional[User]:
        """根据 ID 获取用户"""
        cls._init_default_users()
        return cls._users.get(user_id)

    @classmethod
    def get_by_username(cls, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        cls._init_default_users()
        for user in cls._users.values():
            if user.username == username:
                return user
        return None

    @classmethod
    def get_by_email(cls, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        cls._init_default_users()
        for user in cls._users.values():
            if user.email == email:
                return user
        return None

    @classmethod
    def authenticate(cls, username: str, password: str) -> Optional[User]:
        """验证用户凭据

        Args:
            username: 用户名或邮箱
            password: 密码

        Returns:
            验证成功返回用户对象，否则返回 None
        """
        cls._init_default_users()

        user = cls.get_by_username(username)
        if not user:
            user = cls.get_by_email(username)

        if not user:
            return None

        if not user.is_active:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user

    @classmethod
    def create(cls, user_data: UserCreate) -> User:
        """创建新用户"""
        cls._init_default_users()

        user = User(
            id=str(uuid4()),
            username=user_data.username,
            email=user_data.email,
            role=user_data.role,
            hashed_password=get_password_hash(user_data.password),
            is_active=True,
            created_at=datetime.utcnow(),
        )
        cls._users[user.id] = user
        return user

    @classmethod
    def list_all(cls) -> list[User]:
        """获取所有用户"""
        cls._init_default_users()
        return list(cls._users.values())
