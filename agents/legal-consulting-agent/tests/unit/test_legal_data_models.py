"""Unit tests for LEGAL-130 ORM metadata."""

from __future__ import annotations

from legal_consulting_agent.infrastructure.db.base import Base
from legal_consulting_agent.infrastructure.db.models import (
    AgentRunModel,
    ConsultationRecordModel,
    FeedbackModel,
    HighRiskReviewModel,
    KnowledgeMaterialModel,
    LegalCategoryModel,
    LegalMessageModel,
    LegalSessionModel,
    NodeRunModel,
    PromptVersionModel,
    UserModel,
)


def test_legal_130_tables_are_registered() -> None:
    tables = Base.metadata.tables

    assert {
        "users",
        "legal_categories",
        "sessions",
        "messages",
        "agent_runs",
        "node_runs",
        "consultation_records",
        "feedbacks",
        "high_risk_reviews",
        "prompt_versions",
        "knowledge_materials",
    }.issubset(tables.keys())


def test_user_model_does_not_store_password_fields() -> None:
    columns = set(UserModel.__table__.columns.keys())

    assert "password" not in columns
    assert "password_hash" not in columns
    assert "refresh_token" not in columns


def test_session_and_message_foreign_keys_enforce_ownership_path() -> None:
    session_fks = {
        fk.constraint.name
        for column in LegalSessionModel.__table__.columns
        for fk in column.foreign_keys
    }
    message_fks = {
        fk.constraint.name
        for column in LegalMessageModel.__table__.columns
        for fk in column.foreign_keys
    }

    assert {"fk_sessions_user", "fk_sessions_category"}.issubset(session_fks)
    assert "fk_messages_session" in message_fks


def test_run_and_node_run_tables_have_audit_indexes() -> None:
    run_indexes = {index.name for index in AgentRunModel.__table__.indexes}
    node_indexes = {index.name for index in NodeRunModel.__table__.indexes}
    category_columns = set(LegalCategoryModel.__table__.columns.keys())

    assert {"idx_runs_thread", "idx_runs_status"}.issubset(run_indexes)
    assert "idx_node_runs_run" in node_indexes
    assert {"code", "display_name", "sort_order"}.issubset(category_columns)


def test_consultation_record_constraints_match_detailed_design() -> None:
    foreign_keys = {
        fk.constraint.name
        for column in ConsultationRecordModel.__table__.columns
        for fk in column.foreign_keys
    }
    indexes = {index.name for index in ConsultationRecordModel.__table__.indexes}
    unique_constraints = {
        constraint.name
        for constraint in ConsultationRecordModel.__table__.constraints
        if constraint.name is not None
    }

    assert {
        "fk_consultation_user",
        "fk_consultation_session",
        "fk_consultation_category",
        "fk_consultation_question",
        "fk_consultation_answer",
    } == foreign_keys
    assert {
        "idx_consultation_user_time",
        "idx_consultation_category_time",
    }.issubset(indexes)
    assert "uk_consultation_answer" in unique_constraints


def test_feedback_constraints_match_detailed_design() -> None:
    foreign_keys = {
        fk.constraint.name
        for column in FeedbackModel.__table__.columns
        for fk in column.foreign_keys
    }
    indexes = {index.name for index in FeedbackModel.__table__.indexes}
    named_constraints = {
        constraint.name
        for constraint in FeedbackModel.__table__.constraints
        if constraint.name is not None
    }

    assert {"fk_feedback_message", "fk_feedback_user"} == foreign_keys
    assert "idx_feedback_message" in indexes
    assert {"ck_feedback_rating", "uk_feedback_user_message"}.issubset(named_constraints)


def test_high_risk_review_constraints_match_detailed_design() -> None:
    foreign_keys = {
        fk.constraint.name
        for column in HighRiskReviewModel.__table__.columns
        for fk in column.foreign_keys
    }
    indexes = {index.name for index in HighRiskReviewModel.__table__.indexes}

    assert {
        "fk_review_message",
        "fk_review_user",
        "fk_review_reviewer",
    } == foreign_keys
    assert "idx_reviews_status" in indexes
    assert HighRiskReviewModel.__table__.columns["reviewed_by"].nullable is True


def test_prompt_version_constraints_match_detailed_design() -> None:
    foreign_keys = {
        fk.constraint.name
        for column in PromptVersionModel.__table__.columns
        for fk in column.foreign_keys
    }
    named_constraints = {
        constraint.name
        for constraint in PromptVersionModel.__table__.constraints
        if constraint.name is not None
    }

    assert foreign_keys == {"fk_prompt_creator"}
    assert "uk_prompt_name_version" in named_constraints
    assert PromptVersionModel.__table__.columns["template_key"].nullable is False


def test_knowledge_material_constraints_match_detailed_design() -> None:
    foreign_keys = {
        fk.constraint.name
        for column in KnowledgeMaterialModel.__table__.columns
        for fk in column.foreign_keys
    }
    indexes = {index.name for index in KnowledgeMaterialModel.__table__.indexes}

    assert foreign_keys == {"fk_material_category", "fk_material_uploader"}
    assert {"idx_material_status", "idx_material_hash"}.issubset(indexes)
    assert KnowledgeMaterialModel.__table__.columns["category_id"].nullable is True
    assert {"created_at", "updated_at"}.issubset(KnowledgeMaterialModel.__table__.columns.keys())
