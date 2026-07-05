"""Unit tests for admin SQL audit API slice."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from data_query_agent.api.dependencies import (
    get_identity_thread_service,
    get_sql_audit_service,
)
from data_query_agent.domain.entities.audit import SqlAudit, SqlPolicyDecision
from data_query_agent.domain.entities.identity import UserMirror, UserRole
from data_query_agent.main import create_app


class FakeIdentityThreadService:
    """Fake identity service for admin SQL audit tests."""

    async def get_user_for_subject(self, *, external_subject: str) -> UserMirror | None:
        if external_subject == "missing":
            return None
        role = UserRole.ADMIN if external_subject == "admin" else UserRole.USER
        return UserMirror(
            id=99 if role is UserRole.ADMIN else 20,
            public_id=f"user-{external_subject}",
            external_subject=external_subject,
            role=role,
            display_name=None,
            created_at=_now(),
            updated_at=_now(),
            last_seen_at=_now(),
        )


class FakeSqlAuditService:
    """Fake audit service with admin-only full SQL records."""

    def __init__(self) -> None:
        self.audits = [
            _audit(
                public_id="audit-1",
                run_id=10,
                user_id=20,
                generated_sql="SELECT COUNT(*) FROM orders",
                row_count=1,
                result_summary="one aggregate row",
                minutes_ago=1,
            ),
            _audit(
                public_id="audit-2",
                run_id=11,
                user_id=21,
                generated_sql="SELECT SUM(amount) FROM orders",
                row_count=1,
                result_summary="one sum row",
                minutes_ago=2,
            ),
        ]

    async def list_admin_sql_audits(
        self,
        *,
        admin_user: UserMirror,
        limit: int = 50,
        offset: int = 0,
    ):
        assert admin_user.role is UserRole.ADMIN
        return tuple(self.audits[offset : offset + limit])


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_identity_thread_service] = lambda: FakeIdentityThreadService()
    app.dependency_overrides[get_sql_audit_service] = lambda: FakeSqlAuditService()
    return TestClient(app)


def test_admin_sql_audit_returns_full_sql_and_policy_details() -> None:
    client = _client()

    response = client.get("/v1/admin/sql-audit", headers={"X-User-Subject": "admin"})

    assert response.status_code == 200
    body = response.json()
    first = body["data"]["items"][0]
    assert body["error"] is None
    assert first["audit_id"] == "audit-1"
    assert first["generated_sql"] == "SELECT COUNT(*) FROM orders"
    assert first["decision"] == "allowed"
    assert first["policy_summary"] == "allowed select within whitelist"
    assert first["row_count"] == 1
    assert first["result_summary"] == "one aggregate row"


def test_admin_sql_audit_supports_pagination() -> None:
    client = _client()

    response = client.get(
        "/v1/admin/sql-audit?limit=1&offset=1",
        headers={"X-User-Subject": "admin"},
    )

    assert response.status_code == 200
    body = response.json()
    assert [item["audit_id"] for item in body["data"]["items"]] == ["audit-2"]
    assert body["data"]["limit"] == 1
    assert body["data"]["offset"] == 1


def test_non_admin_and_missing_user_cannot_access_sql_audit() -> None:
    client = _client()

    user_response = client.get("/v1/admin/sql-audit", headers={"X-User-Subject": "user"})
    missing_response = client.get(
        "/v1/admin/sql-audit",
        headers={"X-User-Subject": "missing"},
    )

    assert user_response.status_code == 403
    assert user_response.json()["error"]["code"] == "AUTH_FORBIDDEN"
    assert missing_response.status_code == 403
    assert missing_response.json()["error"]["code"] == "AUTH_FORBIDDEN"


def _audit(
    *,
    public_id: str,
    run_id: int,
    user_id: int,
    generated_sql: str,
    row_count: int,
    result_summary: str,
    minutes_ago: int,
) -> SqlAudit:
    now = _now() - timedelta(minutes=minutes_ago)
    return SqlAudit(
        id=minutes_ago,
        public_id=public_id,
        run_id=run_id,
        user_id=user_id,
        decision=SqlPolicyDecision.ALLOWED,
        sql_fingerprint=f"sha256:{public_id}",
        generated_sql=generated_sql,
        redacted_summary="aggregate query",
        policy_summary="allowed select within whitelist",
        row_count=row_count,
        result_summary=result_summary,
        created_at=now,
        expires_at=now + timedelta(days=90),
    )


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)
