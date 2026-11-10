"""用户服务 - 内存存储模拟实现"""

from datetime import datetime
from typing import Dict, Optional
from uuid import uuid4

from ..models.user import User, UserCreate, UserRole
from ..api.middleware.auth import get_password_hash, verify_password


class UserService:
    """用户服务（内存存储）"""

    _users: Dict[str, User] = {}
    _initialized: bool = False

    @classmethod
    def _init_default_users(cls) -> None:
        """初始化默认用户"""
        if cls._initialized:
            return

        admin_user = User(
            id="admin-001",
            username="admin",
            email="admin@opspilot.example.com",
            role=UserRole.ADMIN,
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            created_at=datetime.utcnow(),
        )
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
        cls._users[viewer_user.id] = viewer_user

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
