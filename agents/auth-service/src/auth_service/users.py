"""In-memory user store for the course MVP auth service.

Two seeded users cover the frontend's admin/user roles. Passwords are hashed
at startup; `update_password` re-hashes on change. State is process-local and
resets on restart — acceptable for MVP/demo.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from auth_service.passwords import hash_password


@dataclass
class User:
    user_id: str
    public_id: str
    email: str
    display_name: str
    role: str
    status: str
    created_at: str
    updated_at: str
    password_hash: str


@dataclass
class UserStore:
    _by_email: dict[str, User] = field(default_factory=dict)
    _by_public_id: dict[str, User] = field(default_factory=dict)

    def add(self, user: User) -> None:
        self._by_email[user.email.lower()] = user
        self._by_public_id[user.public_id] = user

    def find_by_email(self, email: str) -> User | None:
        return self._by_email.get(email.lower())

    def find_by_public_id(self, public_id: str) -> User | None:
        return self._by_public_id.get(public_id)

    def update_password(self, public_id: str, new_password: str) -> None:
        user = self._by_public_id.get(public_id)
        if user is not None:
            user.password_hash = hash_password(new_password)


def build_default_store() -> UserStore:
    store = UserStore()
    now = "2026-07-05T00:00:00Z"
    store.add(
        User(
            user_id="admin-001",
            public_id="00000000-0000-4000-8000-000000000001",
            email="admin@suite.local",
            display_name="管理员",
            role="admin",
            status="active",
            created_at=now,
            updated_at=now,
            password_hash=hash_password("Admin@123"),
        )
    )
    store.add(
        User(
            user_id="user-001",
            public_id="00000000-0000-4000-8000-000000000002",
            email="user@suite.local",
            display_name="普通用户",
            role="user",
            status="active",
            created_at=now,
            updated_at=now,
            password_hash=hash_password("User@12345"),
        )
    )
    return store
