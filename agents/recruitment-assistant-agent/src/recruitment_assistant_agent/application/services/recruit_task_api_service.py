"""MVP task/material service for recruitment API endpoints."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from uuid import uuid4

from recruitment_assistant_agent.core.errors import AppError, InputBlockedError
from recruitment_assistant_agent.domain.value_objects.recruit_enums import (
    MaterialKind,
    ReviewStatus,
    RunStatus,
    ScanStatus,
    TaskPriority,
    TaskStatus,
)


class RecruitmentTaskNotFoundError(AppError):
    """Raised when a recruitment task cannot be found."""

    code = "TASK_NOT_FOUND"
    http_status = 404


class RecruitmentRunNotFoundError(AppError):
    """Raised when a recruitment run cannot be found."""

    code = "RUN_NOT_FOUND"
    http_status = 404


class RecruitmentReportNotFoundError(AppError):
    """Raised when a recruitment report cannot be found."""

    code = "REPORT_NOT_FOUND"
    http_status = 404


class RecruitmentReviewRequiredError(AppError):
    """Raised when report access requires admin approval first."""

    code = "REVIEW_REQUIRED"
    http_status = 409


class RecruitmentReportExpiredError(AppError):
    """Raised when a recruitment report has expired."""

    code = "REPORT_EXPIRED"
    http_status = 410


@dataclass(frozen=True, slots=True)
class RecruitmentMaterialRecord:
    material_id: str
    kind: MaterialKind
    scan_status: ScanStatus
    original_deleted: bool
    content_hash: str
    size_chars: int


@dataclass(frozen=True, slots=True)
class RecruitmentTaskRecord:
    task_id: str
    title: str | None
    priority: TaskPriority
    status: TaskStatus
    review_status: ReviewStatus
    materials: tuple[RecruitmentMaterialRecord, ...]
    latest_run_id: str | None
    created_at: datetime
    deleted: bool = False


@dataclass(frozen=True, slots=True)
class RecruitmentTaskListResult:
    items: list[RecruitmentTaskRecord]
    page: int
    page_size: int
    total: int


@dataclass(frozen=True, slots=True)
class RecruitmentReviewRecord:
    task_id: str
    review_status: ReviewStatus
    review_note: str | None
    reviewed_by: str
    reviewed_at: datetime


@dataclass(frozen=True, slots=True)
class RecruitmentManualOverrideRecord:
    override_id: str
    match_result_id: str
    field_path: str
    old_value: str | None
    new_value: str
    reason: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class RecruitmentRunEventRecord:
    event_id: str
    run_id: str
    sequence: int
    event_type: str
    timestamp: datetime
    payload: dict[str, str]


@dataclass(frozen=True, slots=True)
class RecruitmentRunRecord:
    run_id: str
    task_id: str
    thread_id: str
    status: RunStatus
    error_code: str | None
    node_trace: tuple[str, ...]
    created_at: datetime
    completed_at: datetime | None


@dataclass(frozen=True, slots=True)
class RecruitmentReportRecord:
    report_id: str
    task_id: str
    status: str
    format_available: tuple[str, ...]
    content_markdown: str
    created_at: datetime
    expires_at: datetime


class RecruitmentTaskApiService:
    """Small in-memory task service for the course MVP API slice."""

    def __init__(self) -> None:
        self._tasks: dict[str, RecruitmentTaskRecord] = {}
        self._runs: dict[str, RecruitmentRunRecord] = {}
        self._events: dict[str, tuple[RecruitmentRunEventRecord, ...]] = {}
        self._reviews: dict[str, RecruitmentReviewRecord] = {}
        self._overrides: dict[str, RecruitmentManualOverrideRecord] = {}
        self._reports: dict[str, RecruitmentReportRecord] = {}

    def create_task(
        self,
        *,
        title: str | None,
        priority: TaskPriority,
        resume_text: str | None,
        jd_text: str | None,
    ) -> RecruitmentTaskRecord:
        materials = tuple(
            material
            for material in (
                _material_record(MaterialKind.RESUME, resume_text),
                _material_record(MaterialKind.JD, jd_text),
            )
            if material is not None
        )
        task = RecruitmentTaskRecord(
            task_id=f"task_{uuid4().hex}",
            title=title,
            priority=priority,
            status=TaskStatus.UPLOADED,
            review_status=ReviewStatus.PENDING,
            materials=materials,
            latest_run_id=None,
            created_at=datetime.now(UTC),
        )
        self._tasks[task.task_id] = task
        return task

    def list_tasks(
        self,
        *,
        page: int,
        page_size: int,
        status: TaskStatus | None,
        review_status: ReviewStatus | None,
    ) -> RecruitmentTaskListResult:
        visible_tasks = [task for task in self._tasks.values() if not task.deleted]
        if status is not None:
            visible_tasks = [task for task in visible_tasks if task.status == status]
        if review_status is not None:
            visible_tasks = [task for task in visible_tasks if task.review_status == review_status]
        ordered = sorted(visible_tasks, key=lambda task: task.created_at, reverse=True)
        start = (page - 1) * page_size
        return RecruitmentTaskListResult(
            items=ordered[start : start + page_size],
            page=page,
            page_size=page_size,
            total=len(ordered),
        )

    def get_task(self, task_id: str) -> RecruitmentTaskRecord:
        task = self._tasks.get(task_id)
        if task is None or task.deleted:
            raise RecruitmentTaskNotFoundError("Recruitment task not found")
        return task

    def delete_task(self, task_id: str) -> None:
        task = self.get_task(task_id)
        self._tasks[task_id] = replace(task, deleted=True, status=TaskStatus.FAILED)

    def review_task(
        self,
        *,
        task_id: str,
        review_status: ReviewStatus,
        review_note: str | None,
        reviewed_by: str,
    ) -> RecruitmentReviewRecord:
        task = self.get_task(task_id)
        reviewed_at = datetime.now(UTC)
        review = RecruitmentReviewRecord(
            task_id=task.task_id,
            review_status=review_status,
            review_note=review_note,
            reviewed_by=reviewed_by,
            reviewed_at=reviewed_at,
        )
        self._tasks[task.task_id] = replace(task, review_status=review_status)
        self._reviews[task.task_id] = review
        return review

    def get_task_review(self, task_id: str) -> RecruitmentReviewRecord | None:
        self.get_task(task_id)
        return self._reviews.get(task_id)

    def create_manual_override(
        self,
        *,
        match_result_id: str,
        field_path: str,
        new_value: str,
        reason: str,
    ) -> RecruitmentManualOverrideRecord:
        if not _is_allowed_override_field(field_path):
            raise InputBlockedError("Unsupported override field path")
        previous_override = self._overrides.get(match_result_id)
        override = RecruitmentManualOverrideRecord(
            override_id=f"override_{uuid4().hex}",
            match_result_id=match_result_id,
            field_path=field_path,
            old_value=previous_override.new_value if previous_override else None,
            new_value=new_value,
            reason=reason,
            created_at=datetime.now(UTC),
        )
        self._overrides[match_result_id] = override
        return override

    def create_report(self, task_id: str) -> RecruitmentReportRecord:
        task = self.get_task(task_id)
        if task.review_status != ReviewStatus.APPROVED:
            raise RecruitmentReviewRequiredError(
                "Admin review is required before report generation"
            )
        now = datetime.now(UTC)
        report = RecruitmentReportRecord(
            report_id=f"report_{uuid4().hex}",
            task_id=task.task_id,
            status="ready",
            format_available=("md", "pdf"),
            content_markdown=_report_markdown(task),
            created_at=now,
            expires_at=now + REPORT_TTL,
        )
        self._reports[report.report_id] = report
        return report

    def get_report(self, report_id: str) -> RecruitmentReportRecord:
        report = self._reports.get(report_id)
        if report is None:
            raise RecruitmentReportNotFoundError("Recruitment report not found")
        if report.expires_at <= datetime.now(UTC):
            raise RecruitmentReportExpiredError("Recruitment report has expired")
        return report

    def export_report(self, report_id: str, report_format: str) -> tuple[str, bytes, str]:
        report = self.get_report(report_id)
        if report_format == "md":
            return (
                "text/markdown; charset=utf-8",
                report.content_markdown.encode("utf-8"),
                f"{report.report_id}.md",
            )
        if report_format == "pdf":
            return "application/pdf", _mock_pdf_bytes(report), f"{report.report_id}.pdf"
        raise InputBlockedError("Unsupported report export format")

    def start_run(
        self,
        *,
        task_id: str,
        prompt_version: str,
        workflow_version: str,
    ) -> RecruitmentRunRecord:
        task = self.get_task(task_id)
        now = datetime.now(UTC)
        run = RecruitmentRunRecord(
            run_id=f"run_{uuid4().hex}",
            task_id=task.task_id,
            thread_id=f"thread_{uuid4().hex}",
            status=RunStatus.SUCCESS,
            error_code=None,
            node_trace=DEFAULT_NODE_TRACE,
            created_at=now,
            completed_at=now,
        )
        self._runs[run.run_id] = run
        self._events[run.run_id] = _run_events(
            run=run,
            prompt_version=prompt_version,
            workflow_version=workflow_version,
        )
        self._tasks[task.task_id] = replace(
            task,
            status=TaskStatus.COMPLETED,
            latest_run_id=run.run_id,
        )
        return run

    def get_run(self, run_id: str) -> RecruitmentRunRecord:
        run = self._runs.get(run_id)
        if run is None:
            raise RecruitmentRunNotFoundError("Recruitment run not found")
        return run

    def list_run_events(self, run_id: str) -> tuple[RecruitmentRunEventRecord, ...]:
        self.get_run(run_id)
        return self._events.get(run_id, ())

    def cancel_run(self, run_id: str) -> RecruitmentRunRecord:
        run = self.get_run(run_id)
        if run.status == RunStatus.CANCELED:
            return run
        canceled = replace(
            run,
            status=RunStatus.CANCELED,
            error_code="CANCELED",
            completed_at=datetime.now(UTC),
        )
        self._runs[run_id] = canceled
        self._events[run_id] = _bounded_events(
            (*self._events.get(run_id, ()), _run_event(canceled, 99, "run.canceled"))
        )
        return canceled


DEFAULT_NODE_TRACE = (
    "file_safety",
    "task_route",
    "resume_parse",
    "jd_parse",
    "evidence_match",
    "fairness_check",
    "gap_question_gen",
    "persist",
)
MAX_EVENTS_PER_RUN = 32
REPORT_TTL = timedelta(days=7)
MATCH_ITEM_OVERRIDE_FIELD_PATTERN = re.compile(
    r"^match_items\[(0|[1-9]\d*)\]\.(match_status|evidence_snippet)$"
)


def _report_markdown(task: RecruitmentTaskRecord) -> str:
    title = task.title or task.task_id
    return "\n".join(
        (
            "# Recruitment Analysis Report",
            "",
            f"- Task: {title}",
            f"- Task ID: {task.task_id}",
            f"- Status: {task.status.value}",
            f"- Review: {task.review_status.value}",
            "",
            "## MVP Summary",
            "This report is generated from the mock recruitment workflow for coursework demonstration.",
            "",
        )
    )


def _mock_pdf_bytes(report: RecruitmentReportRecord) -> bytes:
    return f"%PDF-1.4\n% Mock recruitment report {report.report_id}\n".encode()


def _material_record(
    kind: MaterialKind,
    text: str | None,
) -> RecruitmentMaterialRecord | None:
    if text is None or not text.strip():
        return None
    encoded = text.encode("utf-8")
    return RecruitmentMaterialRecord(
        material_id=f"mat_{uuid4().hex}",
        kind=kind,
        scan_status=ScanStatus.CLEAN,
        original_deleted=True,
        content_hash=sha256(encoded).hexdigest(),
        size_chars=len(text),
    )


def _run_events(
    *,
    run: RecruitmentRunRecord,
    prompt_version: str,
    workflow_version: str,
) -> tuple[RecruitmentRunEventRecord, ...]:
    started = _run_event(
        run,
        1,
        "run.started",
        {"prompt_version": prompt_version, "workflow_version": workflow_version},
    )
    node_events = tuple(
        _run_event(run, index + 2, "node.completed", {"node_name": node_name})
        for index, node_name in enumerate(run.node_trace)
    )
    completed = _run_event(run, len(node_events) + 2, "run.completed")
    return (started, *node_events, completed)


def _bounded_events(
    events: tuple[RecruitmentRunEventRecord, ...],
) -> tuple[RecruitmentRunEventRecord, ...]:
    return events[-MAX_EVENTS_PER_RUN:]


def _is_allowed_override_field(field_path: str) -> bool:
    return (
        field_path == "overall_tier"
        or MATCH_ITEM_OVERRIDE_FIELD_PATTERN.fullmatch(field_path) is not None
    )


def _run_event(
    run: RecruitmentRunRecord,
    sequence: int,
    event_type: str,
    payload: dict[str, str] | None = None,
) -> RecruitmentRunEventRecord:
    return RecruitmentRunEventRecord(
        event_id=f"evt_{uuid4().hex}",
        run_id=run.run_id,
        sequence=sequence,
        event_type=event_type,
        timestamp=datetime.now(UTC),
        payload=payload or {},
    )


_recruitment_task_api_service = RecruitmentTaskApiService()


def get_recruitment_task_api_service() -> RecruitmentTaskApiService:
    """Return the process-local MVP task service."""
    return _recruitment_task_api_service
