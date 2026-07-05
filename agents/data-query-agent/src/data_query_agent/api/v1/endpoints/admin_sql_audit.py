"""Admin-only SQL audit endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query

from data_query_agent.api.dependencies import (
    CurrentSubjectDep,
    IdentityThreadServiceDep,
    SqlAuditServiceDep,
)
from data_query_agent.api.v1.schemas.admin_sql_audit import (
    AdminSqlAuditItem,
    AdminSqlAuditListData,
    AdminSqlAuditListEnvelope,
)
from data_query_agent.core.errors import ForbiddenError
from data_query_agent.domain.entities.identity import UserRole

router = APIRouter()


@router.get("/admin/sql-audit", response_model=AdminSqlAuditListEnvelope)
async def list_admin_sql_audit(
    subject: CurrentSubjectDep,
    identity_service: IdentityThreadServiceDep,
    audit_service: SqlAuditServiceDep,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> AdminSqlAuditListEnvelope:
    """List full SQL audit records for admin user mirrors only."""
    user = await identity_service.get_user_for_subject(external_subject=subject)
    if user is None or user.id is None or user.role is not UserRole.ADMIN:
        raise ForbiddenError("admin role required for SQL audit access")
    audits = await audit_service.list_admin_sql_audits(
        admin_user=user,
        limit=limit,
        offset=offset,
    )
    return AdminSqlAuditListEnvelope(
        data=AdminSqlAuditListData(
            items=[AdminSqlAuditItem.from_entity(audit) for audit in audits],
            limit=limit,
            offset=offset,
        )
    )
