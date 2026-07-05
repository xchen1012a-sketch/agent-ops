"""Unit tests for RECRUIT-230 ORM metadata."""

from __future__ import annotations

from recruitment_assistant_agent.infrastructure.db.base import Base
from recruitment_assistant_agent.infrastructure.db.models import (
    AgentRunModel,
    EducationEvidenceModel,
    ExperienceEvidenceModel,
    GapAnalysisModel,
    InterviewQuestionModel,
    JDRequirementModel,
    JDStructureModel,
    ManualOverrideModel,
    MatchItemModel,
    MatchResultModel,
    MaterialModel,
    NodeRunModel,
    PromptVersionModel,
    RecruitTaskModel,
    ReportModel,
    ResumeStructureModel,
    SkillEvidenceModel,
    UserModel,
)


def test_recruit_230_tables_are_registered() -> None:
    tables = Base.metadata.tables

    assert {
        "users",
        "tasks",
        "materials",
        "agent_runs",
        "node_runs",
        "resume_structures",
        "skill_evidence",
        "experience_evidence",
        "education_evidence",
        "jd_structures",
        "jd_requirements",
        "match_results",
        "match_items",
        "gap_analyses",
        "interview_questions",
        "reports",
        "manual_overrides",
        "prompt_versions",
    }.issubset(tables.keys())


def test_user_model_does_not_store_password_fields() -> None:
    columns = set(UserModel.__table__.columns.keys())

    assert "password" not in columns
    assert "password_hash" not in columns
    assert "refresh_token" not in columns


def test_task_foreign_keys_enforce_ownership_path() -> None:
    task_fks = {
        fk.constraint.name
        for column in RecruitTaskModel.__table__.columns
        for fk in column.foreign_keys
    }

    assert {"fk_tasks_user", "fk_tasks_reviewer"}.issubset(task_fks)


def test_task_indexes_match_detailed_design() -> None:
    indexes = {index.name for index in RecruitTaskModel.__table__.indexes}

    assert {"idx_tasks_user_time", "idx_tasks_review"}.issubset(indexes)


def test_material_foreign_key_and_hash_index() -> None:
    material_fks = {
        fk.constraint.name
        for column in MaterialModel.__table__.columns
        for fk in column.foreign_keys
    }
    indexes = {index.name for index in MaterialModel.__table__.indexes}
    file_hash_column = MaterialModel.__table__.columns["file_hash"]

    assert "fk_materials_task" in material_fks
    assert {"idx_materials_hash", "idx_materials_task"}.issubset(indexes)
    # SHA-256 char(64)
    assert file_hash_column.type.length == 64


def test_run_and_node_run_tables_have_audit_indexes() -> None:
    run_indexes = {index.name for index in AgentRunModel.__table__.indexes}
    node_indexes = {index.name for index in NodeRunModel.__table__.indexes}

    assert {"idx_runs_thread", "idx_runs_status"}.issubset(run_indexes)
    assert "idx_node_runs_run" in node_indexes


def test_node_run_metadata_column_is_json_alias() -> None:
    """``metadata`` is a Python reserved-ish name; ORM uses ``metadata_json`` attr."""
    columns = set(NodeRunModel.__table__.columns.keys())

    assert "metadata" in columns
    assert "metadata_json" not in columns


def test_resume_structure_fks_and_unique_version() -> None:
    fks = {
        fk.constraint.name
        for column in ResumeStructureModel.__table__.columns
        for fk in column.foreign_keys
    }
    constraints = {c.name for c in ResumeStructureModel.__table__.constraints}
    indexes = {index.name for index in ResumeStructureModel.__table__.indexes}

    assert {"fk_resume_structures_task", "fk_resume_structures_material"}.issubset(fks)
    assert "uq_resume_structures_material_version" in constraints
    assert "idx_resume_structures_material_version" in indexes


def test_resume_structure_does_not_persist_sensitive_attributes() -> None:
    """ADR-0009: 11 sensitive attributes must NOT be columns on resume_structures."""
    columns = set(ResumeStructureModel.__table__.columns.keys())
    forbidden = {
        "age",
        "gender",
        "marital_status",
        "ethnicity",
        "health",
        "political_status",
        "photo",
        "id_card",
        "hometown",
        "religion",
        "hukou",
    }
    assert not (columns & forbidden)


def test_evidence_tables_cascade_on_resume_structure_delete() -> None:
    for model in (
        SkillEvidenceModel,
        ExperienceEvidenceModel,
        EducationEvidenceModel,
    ):
        fks = {
            (fk.constraint.name, fk.ondelete)
            for column in model.__table__.columns
            for fk in column.foreign_keys
        }
        assert any(name.startswith("fk_") and delete == "CASCADE" for name, delete in fks), (
            f"{model.__name__} must cascade on delete"
        )


def test_evidence_snippet_columns_are_non_nullable() -> None:
    for model in (
        SkillEvidenceModel,
        ExperienceEvidenceModel,
        EducationEvidenceModel,
    ):
        snippet = model.__table__.columns["evidence_snippet"]
        assert snippet.nullable is False, f"{model.__name__}.evidence_snippet must be NOT NULL"


def test_jd_structure_fks_and_unique_version() -> None:
    fks = {
        fk.constraint.name
        for column in JDStructureModel.__table__.columns
        for fk in column.foreign_keys
    }
    constraints = {c.name for c in JDStructureModel.__table__.constraints}
    indexes = {index.name for index in JDStructureModel.__table__.indexes}

    assert {"fk_jd_structures_task", "fk_jd_structures_material"}.issubset(fks)
    assert "uq_jd_structures_material_version" in constraints
    assert "idx_jd_structures_material_version" in indexes


def test_jd_requirement_cascade_and_text_non_nullable() -> None:
    fks = {
        (fk.constraint.name, fk.ondelete)
        for column in JDRequirementModel.__table__.columns
        for fk in column.foreign_keys
    }
    text_column = JDRequirementModel.__table__.columns["text"]
    type_column = JDRequirementModel.__table__.columns["requirement_type"]
    weight_column = JDRequirementModel.__table__.columns["weight_hint"]

    assert any(
        name == "fk_jd_requirements_structure" and delete == "CASCADE" for name, delete in fks
    )
    assert text_column.nullable is False
    assert type_column.nullable is False
    # Numeric(3, 2) -> precision 3, scale 2
    assert weight_column.type.precision == 3
    assert weight_column.type.scale == 2
    # Python attribute is renamed to avoid shadowing sqlalchemy.text in class body
    assert "text_content" in JDRequirementModel.__dict__


def test_match_result_unique_pair_and_required_fields() -> None:
    constraints = {c.name for c in MatchResultModel.__table__.constraints}
    fks = {
        fk.constraint.name
        for column in MatchResultModel.__table__.columns
        for fk in column.foreign_keys
    }
    tier_col = MatchResultModel.__table__.columns["tier"]
    rule_col = MatchResultModel.__table__.columns["rule_version"]
    prompt_col = MatchResultModel.__table__.columns["prompt_version"]

    assert "uk_match_pair" in constraints
    assert "fk_match_task" in fks
    assert tier_col.nullable is False
    assert rule_col.nullable is False
    assert prompt_col.nullable is False


def test_match_items_cascade_and_required_fields() -> None:
    fks = {
        (fk.constraint.name, fk.ondelete)
        for column in MatchItemModel.__table__.columns
        for fk in column.foreign_keys
    }
    req_col = MatchItemModel.__table__.columns["requirement"]
    status_col = MatchItemModel.__table__.columns["match_status"]

    assert any(name == "fk_item_match" and delete == "CASCADE" for name, delete in fks)
    assert req_col.nullable is False
    assert status_col.nullable is False


def test_gap_analyses_cascade_and_required_fields() -> None:
    fks = {
        (fk.constraint.name, fk.ondelete)
        for column in GapAnalysisModel.__table__.columns
        for fk in column.foreign_keys
    }
    desc_col = GapAnalysisModel.__table__.columns["gap_description"]
    suggested_col = GapAnalysisModel.__table__.columns["suggested_question"]
    indexes = {index.name for index in GapAnalysisModel.__table__.indexes}

    assert any(name == "fk_gap_match" and delete == "CASCADE" for name, delete in fks)
    assert desc_col.nullable is False
    assert suggested_col.nullable is True
    assert "idx_gap_analyses_match" in indexes


def test_interview_questions_cascade_and_required_fields() -> None:
    fks = {
        (fk.constraint.name, fk.ondelete)
        for column in InterviewQuestionModel.__table__.columns
        for fk in column.foreign_keys
    }
    question_col = InterviewQuestionModel.__table__.columns["question_text"]
    category_col = InterviewQuestionModel.__table__.columns["category"]
    difficulty_col = InterviewQuestionModel.__table__.columns["difficulty"]
    indexes = {index.name for index in InterviewQuestionModel.__table__.indexes}

    assert any(name == "fk_q_match" and delete == "CASCADE" for name, delete in fks)
    assert question_col.nullable is False
    assert category_col.nullable is False
    assert difficulty_col.nullable is True
    assert "idx_interview_questions_match" in indexes


def test_reports_required_fields_and_cascades() -> None:
    fks = {
        (fk.constraint.name, fk.ondelete)
        for column in ReportModel.__table__.columns
        for fk in column.foreign_keys
    }
    constraints = {c.name for c in ReportModel.__table__.constraints}
    indexes = {index.name for index in ReportModel.__table__.indexes}
    content_col = ReportModel.__table__.columns["content_markdown"]
    pdf_col = ReportModel.__table__.columns["pdf_path"]
    expires_col = ReportModel.__table__.columns["expires_at"]
    created_by_col = ReportModel.__table__.columns["created_by"]

    assert any(name == "fk_reports_task" and delete == "CASCADE" for name, delete in fks)
    assert any(name == "fk_reports_match" and delete == "CASCADE" for name, delete in fks)
    assert ("fk_reports_creator", None) in fks
    assert "uk_reports_public_id" in constraints
    assert {"idx_reports_task", "idx_reports_match", "idx_reports_expires"}.issubset(indexes)
    assert content_col.nullable is False
    assert pdf_col.nullable is True
    assert expires_col.nullable is False
    assert created_by_col.nullable is False


def test_manual_overrides_required_fields_and_cascades() -> None:
    fks = {
        (fk.constraint.name, fk.ondelete)
        for column in ManualOverrideModel.__table__.columns
        for fk in column.foreign_keys
    }
    indexes = {index.name for index in ManualOverrideModel.__table__.indexes}
    field_col = ManualOverrideModel.__table__.columns["field_path"]
    old_col = ManualOverrideModel.__table__.columns["old_value"]
    new_col = ManualOverrideModel.__table__.columns["new_value"]
    reason_col = ManualOverrideModel.__table__.columns["reason"]
    admin_col = ManualOverrideModel.__table__.columns["admin_id"]

    assert any(name == "fk_override_match" and delete == "CASCADE" for name, delete in fks)
    assert ("fk_override_admin", None) in fks
    assert {"idx_manual_overrides_match", "idx_manual_overrides_admin"}.issubset(indexes)
    assert field_col.nullable is False
    assert old_col.nullable is True
    assert new_col.nullable is True
    assert reason_col.nullable is False
    assert admin_col.nullable is False


def test_prompt_versions_unique_pair_and_required_fields() -> None:
    constraints = {c.name for c in PromptVersionModel.__table__.constraints}
    fks = {
        fk.constraint.name
        for column in PromptVersionModel.__table__.columns
        for fk in column.foreign_keys
    }
    indexes = {index.name for index in PromptVersionModel.__table__.indexes}
    name_col = PromptVersionModel.__table__.columns["prompt_name"]
    version_col = PromptVersionModel.__table__.columns["version"]
    template_col = PromptVersionModel.__table__.columns["template_key"]
    status_col = PromptVersionModel.__table__.columns["status"]
    creator_col = PromptVersionModel.__table__.columns["created_by"]
    variables_col = PromptVersionModel.__table__.columns["variables"]
    output_schema_col = PromptVersionModel.__table__.columns["output_schema"]

    assert "uk_prompt_name_version" in constraints
    assert "fk_prompt_creator" in fks
    assert "idx_prompt_versions_name_status" in indexes
    assert name_col.nullable is False
    assert version_col.nullable is False
    assert template_col.nullable is False
    assert status_col.nullable is False
    assert creator_col.nullable is False
    assert variables_col.nullable is True
    assert output_schema_col.nullable is True
