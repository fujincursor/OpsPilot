"""用户服务。用户保存在数据库中。"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from ..db import DocumentDict
from ..models.user import User, UserCreate, UserRole
from ..api.middleware.auth import get_password_hash, verify_password


class UserService:
    """用户服务。用户保存在数据库中。"""

    _users: DocumentDict | None = None
    _initialized: bool = False

    @classmethod
    def _init_default_users(cls) -> None:
        """从数据库加载用户，并补齐缺失的默认账号。"""
        if cls._initialized:
            return

        cls._users = DocumentDict("users", model=User, key_type=str)
        existing_names = {user.username for user in cls._users.values()}

        admin_user = User(
            id="admin-001",
            username="admin",
            email="admin@opspilot.example.com",
            role=UserRole.ADMIN,
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            created_at=datetime.utcnow(),
        )
        if admin_user.username not in existing_names:
            cls._users[admin_user.id] = admin_user

        operator_user = User(
            id="operator-001",
            username="operator",
            email="operator@opspilot.example.com",
            role=UserRole.OPERATOR,
            hashed_password=get_password_hash("operator123"),
            is_active=True,
            created_at=datetime.utcnow(),
        )
        if operator_user.username not in existing_names:
            cls._users[operator_user.id] = operator_user

        viewer_user = User(
            id="viewer-001",
            username="viewer",
            email="viewer@opspilot.example.com",
            role=UserRole.VIEWER,
            hashed_password=get_password_hash("viewer123"),
            is_active=True,
            created_at=datetime.utcnow(),
        )
        if viewer_user.username not in existing_names:
            cls._users[viewer_user.id] = viewer_user

        reviewer_user = User(
            id="reviewer-001",
            username="reviewer",
            email="reviewer@opspilot.example.com",
            role=UserRole.REVIEWER,
            hashed_password=get_password_hash("reviewer123"),
            is_active=True,
            created_at=datetime.utcnow(),
        )
        if reviewer_user.username not in existing_names:
            cls._users[reviewer_user.id] = reviewer_user

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
