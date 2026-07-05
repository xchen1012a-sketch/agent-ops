"""Central recruitment domain enums used by ORM, services, and workflow state."""

from __future__ import annotations

from enum import StrEnum


class UserRole(StrEnum):
    """Roles trusted from the unified auth JWT claims."""

    USER = "user"
    ADMIN = "admin"


class UserStatus(StrEnum):
    """User mirror lifecycle states."""

    ACTIVE = "active"
    DISABLED = "disabled"


class TaskStatus(StrEnum):
    """Recruitment analysis task lifecycle states."""

    UPLOADED = "uploaded"
    PARSING = "parsing"
    PARSED = "parsed"
    MATCHING = "matching"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskPriority(StrEnum):
    """Recruitment task urgency levels."""

    NORMAL = "normal"
    URGENT = "urgent"


class ReviewStatus(StrEnum):
    """Admin human-review lifecycle states for a recruitment task."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"


class MaterialKind(StrEnum):
    """Material kinds accepted by the recruitment Agent."""

    RESUME = "resume"
    JD = "jd"


class ScanStatus(StrEnum):
    """File safety scan lifecycle states."""

    PENDING = "pending"
    CLEAN = "clean"
    INFECTED = "infected"
    FAILED = "failed"


class RunStatus(StrEnum):
    """Shared Agent and node execution states."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELED = "canceled"


class Proficiency(StrEnum):
    """Skill proficiency buckets reported by resume parsing."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class Degree(StrEnum):
    """Highest education degree captured by resume parsing."""

    HIGH_SCHOOL = "high_school"
    ASSOCIATE = "associate"
    BACHELOR = "bachelor"
    MASTER = "master"
    PHD = "phd"
    OTHER = "other"


class SchoolTier(StrEnum):
    """Coarse school tier classification; sensitive details are not captured."""

    TIER1 = "tier1"
    TIER2 = "tier2"
    TIER3 = "tier3"
    OVERSEAS = "overseas"
    OTHER = "other"


class RequirementType(StrEnum):
    """JD requirement classification used by evidence matching."""

    MUST_HAVE = "must_have"
    NICE_TO_HAVE = "nice_to_have"


class MatchTier(StrEnum):
    """Match tier shared by overall result and per-item match status."""

    MATCH = "match"
    PARTIAL = "partial"
    NO_EVIDENCE = "no_evidence"


class SkillCategory(StrEnum):
    """Skill bucket used by match items to group evidence."""

    SKILL = "skill"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    CERTIFICATION = "certification"
    SOFT_SKILL = "soft_skill"


class QuestionCategory(StrEnum):
    """Interview question classification."""

    SKILL_VERIFICATION = "skill_verification"
    EXPERIENCE_PROBE = "experience_probe"
    BEHAVIORAL = "behavioral"
    GAP_PROBE = "gap_probe"


class QuestionDifficulty(StrEnum):
    """Interview question difficulty."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class PromptStatus(StrEnum):
    """Lifecycle states for versioned prompt templates.

    Only ``active`` templates are loaded by workflow nodes; ``draft`` is the
    initial state for newly created versions and ``retired`` blocks future
    use while preserving historical references.
    """

    DRAFT = "draft"
    ACTIVE = "active"
    RETIRED = "retired"
