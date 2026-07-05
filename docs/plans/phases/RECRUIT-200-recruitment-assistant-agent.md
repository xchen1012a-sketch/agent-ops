# RECRUIT-200 智能招聘 Agent 业务实现

## 状态

进行中。`RECRUIT-240 匹配与面试工作流` 第五切片 Prompt 输出 schema 校验边界已落地并通过本地质量门禁；下一步进入 RECRUIT-240 第六切片 Prompt-backed resume_parse 节点。

## 上一阶段

- `FOUND-010 企业级工程基础` 已完成（局部于招聘 Agent 子仓的骨架、配置、健康检查、空迁移基线）。
- 招聘 Agent 子仓已具备：`pyproject.toml`、`alembic.ini`、`migrations/env.py`、`migrations/versions/0001_initial_baseline.py`、空骨架目录（`api/application/domain/infrastructure/workflows/prompts/core`）和基础单元测试。
- 详细设计产出 `agents/recruitment-assistant-agent/docs/detailed-design.md`、`specification.md`、`architecture.md`、`api-contract.md`。
- 父仓 `LEGAL-100 法律咨询 Agent` 由 Codex 并行推进，互不依赖。

## 用户确认（2026-07-05）

1. Claude（本会话）负责 RECRUIT-200 智能招聘 Agent；Codex 负责并行 LEGAL-100，互不阻塞。
2. 整个 RECRUIT-200 模块先写整体计划书，再按循环工程分次推进。
3. 每批次必须落迁移 + 单元测试 + `ruff/mypy/pytest` 三件套；未跑真实 MySQL 时明确写"未验证"。
4. 不接真实 DeepSeek、ClamAV、文件存储、生产数据库；所有外部服务在 adapter 边界后置。
5. 不预置岗位模板、任务分类、评分规则 YAML 真源内容；表结构先建，种子数据等业务确认后再插入。
6. 公平性硬约束（ADR-0009）在任何批次都不可绕过：敏感属性清单、人工复核队列、admin 签字出报告。

## 目标

实现智能招聘助手 Agent 的业务能力，覆盖课件要求的简历/JD 结构化、证据化匹配、差距分析、面试问题、人工复核和报告导出。系统只辅助决策，不自动录用或淘汰，不基于敏感属性评分。

## 本阶段范围

- 模块：`agents/recruitment-assistant-agent`
- 数据库：`recruitment_agent_db`
- 子阶段：
  1. `RECRUIT-230 材料与结构化解析`（数据层 7 批）
  2. `RECRUIT-240 匹配与面试工作流`（10 个工作流切片）
  3. `RECRUIT-250 API、报告与人工复核`（5 个 API 切片）
  4. `RECRUIT-260 质量与验收`（4 个验收切片）

## 第一块：RECRUIT-230 材料与结构化解析

类比 `LEGAL-130`，按表批次推进；每批必须独立可测、独立可回滚。

### 第一批：身份与任务材料层

- 目标：建立招聘 Agent 持久化业务基础；不接真实 DeepSeek、ClamAV、文件存储、生产 DB。
- 输入：JWT 同步过来的用户镜像、用户创建的分析任务、上传材料元数据、Agent 运行审计。
- 输出表（5 张）：
  - `users`：统一认证用户镜像，不存密码、不存 refresh token。
  - `tasks`：招聘分析任务（含 `status`、`priority`、`review_status`）。
  - `materials`：简历/JD 材料元数据（含 `kind`、`file_hash`、`scan_status`、`original_deleted`）。
  - `agent_runs`：LangGraph 运行审计。
  - `node_runs`：节点运行审计。
- 输出代码：
  - 集中 StrEnum：`UserRole`、`UserStatus`、`TaskStatus`、`TaskPriority`、`ReviewStatus`、`MaterialKind`、`ScanStatus`、`RunStatus`。
  - frozen dataclass 实体：`UserMirror`、`RecruitTask`、`Material`、`AgentRun`、`NodeRun`。
  - repository Protocol + SQLAlchemy 实现。
  - application service：用户镜像、任务创建、材料登记、`create_agent_run`、`create_node_run`。
  - 通过 Alembic autogenerate 生成 1 条迁移 revision。
  - 相邻单元测试（不连真实 DB）。
- 约束：
  - `users` 表不存密码；role/status 来自 JWT claim。
  - `tasks.user_id` 必须引用已存在用户；`status` 默认 `uploaded`；`review_status` 默认 `pending`。
  - `materials.file_hash` 必须是 64 位十六进制（SHA-256），存小写。
  - `materials.original_deleted` 默认 `false`；本批不触发删除动作，只持久化字段。
  - repository 不自行 commit；事务边界由 application/use case 控制。
- 不做：
  - 简历/JD 结构化表、评分表、报告表、Prompt 版本表。
  - API/DTO、SSE、文件上传/杀毒、真实 DeepSeek/Qdrant/BGE/Redis。
  - 任何前端和其他 Agent 模块改动。
- 验收：单元测试通过；`ruff check`、`ruff format --check`、`mypy src`、`pytest --cov=recruitment_assistant_agent` 全过；`alembic heads` 单 head；如本地 MySQL 可用，补 `upgrade → downgrade → upgrade` 复验。

### 第一批执行记录（2026-07-05）

- 已新增集中枚举、5 个 frozen dataclass 实体、repository Protocol、SQLAlchemy ORM 和 repository、application service。
- 已新增手写 Alembic revision `ccc46fb6a333_recruit_identity_data_layer.py`（本地无 MySQL，未走 autogenerate；down_revision 为 `0001_initial_baseline`）。
- application service 校验 SHA-256、用户任务归属、文件大小非负、空 filename/mime 拒绝；`scan_status` 默认 `pending`，`original_deleted` 默认 `false`。
- 已通过 alembic offline SQL 模式验证 upgrade 与 downgrade 的 5 张表创建/删除顺序符合 FK 约束。
- 已调整预先存在的 `tests/unit/test_migrations.py`：从硬编码 "只有 1 个 revision" 改为 "单 head + 链式 down_revision" 不变量断言。
- 已修复 `tests/unit/test_logging.py` 的 import 排序（ruff I001 自动修复）。
- `uv run ruff check src tests`：通过。
- `uv run ruff format --check src tests`：通过，56 files already formatted。
- `uv run mypy src`：通过，42 source files 无错误。
- `uv run pytest --cov=recruitment_assistant_agent -q`：40 passed，总覆盖率 82%。
- `uv run alembic heads`：`ccc46fb6a333 (head)`，单 head。
- 真实 MySQL `upgrade -> downgrade -> upgrade`：未验证（本地未起 MySQL 容器）。

### 第二批：简历结构化层

- 目标：持久化简历解析的结构化结果，按版本可人工修正。
- 输出表（4 张）：
  - `resume_structures`（含 `version`、`raw_structured JSON`、`summary`、`total_years_exp`）。
  - `skill_evidence`（技能 + 证据片段 + 来源章节）。
  - `experience_evidence`（角色 + 脱敏公司 + 时长 + 证据）。
  - `education_evidence`（学位 + 专业 + 院校层次 + 毕业年份）。
- 约束：
  - 一次解析一个 `version`；同任务旧版本保留；最新版本由 `is_latest` 标记或查询时取最大 version（详细设计未给 `is_latest`，按 `version` 取最大）。
  - `evidence_snippet` 不可为空；强制证据可追溯。
  - 显式不允许字段：age、gender、marital_status、ethnicity、health、political_status、photo、id_card；解析阶段剔除，不入库。
  - `company_redacted` 可空，允许脱敏。
- 不做：解析节点、API、Prompt、报告、其他 Agent。
- 验收：同第一批 + 简历版本递增测试、证据片段非空测试、敏感字段未持久化测试。

### 第二批执行记录（2026-07-05）

- 已新增 3 个枚举（`Proficiency`、`Degree`、`SchoolTier`）到 `domain/value_objects/recruit_enums.py`。
- 已新增 4 个 frozen dataclass 实体（`ResumeStructure`、`SkillEvidence`、`ExperienceEvidence`、`EducationEvidence`）到 `domain/entities/recruit_data.py`。
- 已扩展 `RecruitDataRepository` Protocol：`create_resume_structure`、`get_latest_resume_structure_for_material`、`get_resume_structure`、`append_skill_evidence`、`append_experience_evidence`、`append_education_evidence`、`get_max_resume_version`。
- 已新增 4 个 ORM models（`ResumeStructureModel`、`SkillEvidenceModel`、`ExperienceEvidenceModel`、`EducationEvidenceModel`），并在 `MaterialModel` 上挂 `resume_structures` 反向关系。
- `resume_structures` 唯一索引 `uq_resume_structures_material_version (material_id, version)`；3 张 evidence 表均 `ondelete=CASCADE` + 索引 `(resume_structure_id)`。
- 已扩展 `SqlAlchemyRecruitDataRepository` 全部新方法及 `_to_*` 转换器。
- 已扩展 `RecruitDataService`：`create_resume_structure`（自动取 max+1 版本、强制 material.kind=resume、跨用户拒绝）、`get_latest_resume_structure_for_material`、3 个 evidence 追加方法（强制 `evidence_snippet` 非空、`duration_months >= 0`、`graduation_year >= 1900`）。
- 已新增手写 Alembic revision `bbb7c5d2e110_recruit_resume_structured.py`（本地无 MySQL，未走 autogenerate；down_revision 为 `ccc46fb6a333`）。
- 已通过 alembic offline SQL 验证 upgrade 与 downgrade 的 4 张表创建/删除顺序符合 FK 约束。
- 已扩展 `tests/unit/test_migrations.py`：单 head + 3 节点链式 down_revision 不变量。
- 已扩展 `tests/unit/test_recruit_data_models.py`：新增 4 项断言（4 张表注册、`resume_structures` 唯一索引与 FK、敏感属性列名禁用、evidence 表 CASCADE 与 `evidence_snippet NOT NULL`）。
- 已扩展 `tests/unit/test_recruit_data_service.py`：新增 10 项断言（版本递增、JD 拒绝、跨用户拒绝、负经验值拒绝、3 类 evidence 追加 + 空片段/负时长/早于 1900 年拒绝）。
- `uv run ruff check src tests`：通过。
- `uv run ruff format --check src tests`：通过，56 files already formatted。
- `uv run mypy src`：通过，42 source files 无错误。
- `uv run pytest --cov=recruitment_assistant_agent -q`：54 passed（比上批 +14），总覆盖率 80%。
- `uv run alembic heads`：`bbb7c5d2e110 (head)`，单 head。
- 真实 MySQL `upgrade -> downgrade -> upgrade`：未验证（本地未起 MySQL 容器）。

### 第三批：JD 结构化层

- 目标：持久化 JD 解析结果与岗位要求清单。
- 输出表（2 张）：`jd_structures`（含 `version`、`raw_structured`、`job_title`、`summary`）、`jd_requirements`（含 `requirement_type` must_have/nice_to_have、`category`、可选 `weight_hint`）。
- 约束：`weight_hint` 范围 0.00–1.00；不强制必填；权重真源在版本化 YAML，DB 只存人工提示。
- 不做：匹配节点、API、其他 Agent。
- 验收：同前 + JD 版本递增、必须/加分项分类约束。

### 第三批执行记录（2026-07-05）

- 已新增枚举 `RequirementType`（`must_have` / `nice_to_have`）到 `domain/value_objects/recruit_enums.py`。
- 已新增 2 个 frozen dataclass 实体（`JDStructure`、`JDRequirement`）到 `domain/entities/recruit_data.py`。
- 已扩展 `RecruitDataRepository` Protocol：`create_jd_structure`、`get_latest_jd_structure_for_material`、`append_jd_requirement`、`get_max_jd_version`。
- 已新增 2 个 ORM models（`JDStructureModel`、`JDRequirementModel`），并在 `MaterialModel` 上挂 `jd_structures` 反向关系。
- `jd_structures` 唯一索引 `uq_jd_structures_material_version (material_id, version)`；`jd_requirements.text` 列在 ORM 中以 `text_content` Python 属性暴露，避免与 `sqlalchemy.text` 同名 shadowing。
- `jd_requirements.weight_hint` 为 `Numeric(3, 2)`，约束 0.00–1.00 由 application service 校验。
- 已扩展 `SqlAlchemyRecruitDataRepository` 全部新方法及 `_to_jd_structure` / `_to_jd_requirement` 转换器。
- 已扩展 `RecruitDataService`：`create_jd_structure`（自动取 max+1 版本、强制 `material.kind=jd`）、`get_latest_jd_structure_for_material`、`append_jd_requirement`（强制 `text` 非空、`weight_hint` 在 0.00–1.00 之间）。
- 已新增手写 Alembic revision `ddd9e1f3a220_recruit_jd_structured.py`（down_revision=`bbb7c5d2e110`）。
- 已扩展 `tests/unit/test_migrations.py`：单 head + 4 节点链式 down_revision 不变量。
- 已扩展 `tests/unit/test_recruit_data_models.py`：新增 2 项断言（jd_structures 唯一索引与 FK、jd_requirements CASCADE 与 `text` NOT NULL、`weight_hint` Numeric(3,2)、Python 属性 `text_content` 别名）。
- 已扩展 `tests/unit/test_recruit_data_service.py`：新增 5 项断言（JD 版本递增、resume material 拒绝、JD 需求追加 + `weight_hint` 范围、空 text 拒绝）。
- `uv run ruff check src tests`：通过。
- `uv run ruff format --check src tests`：通过。
- `uv run mypy src`：通过，42 source files 无错误。
- `uv run pytest --cov=recruitment_assistant_agent -q`：61 passed（比上批 +7），总覆盖率 79%（新代码 100%；少量未变模块拉低整体值，下批补到 ≥80%）。
- `uv run alembic heads`：`ddd9e1f3a220 (head)`，单 head。
- 真实 MySQL `upgrade -> downgrade -> upgrade`：未验证（本地未起 MySQL 容器）。

### 第四批：匹配结果层

- 目标：持久化简历 vs JD 的逐项匹配与分项分数。
- 输出表（2 张）：
  - `match_results`（4 个分项分数 + `overall_score` + `tier` match/partial/no_evidence + `prompt_version` + `rule_version`）。
  - `match_items`（每条岗位要求 → 简历证据片段 + match/partial/no_evidence）。
- 约束：
  - `match_results` 唯一索引 `(resume_structure_id, jd_structure_id)`；同对简历/JD 只允许一条匹配结果。
  - `tier` 由评分规则真源决定，本批不实现规则引擎，只持久化字段。
  - `rule_version` 必填；标识计算该结果时使用的评分规则版本。
  - 普通用户视图不暴露 `*_score` 字段；API 投影由 RECRUIT-250 控制，本批只持久化。
- 不做：评分计算节点、报告生成、API、其他 Agent。
- 验收：同前 + 唯一索引测试、tier 枚举测试、rule_version 非空测试。

### 第四批执行记录（2026-07-05）

- 已新增 2 个枚举（`MatchTier` 共享于 `tier` 与 `match_status`、`SkillCategory` skill/experience/education/certification/soft_skill）到 `domain/value_objects/recruit_enums.py`。
- 已新增 2 个 frozen dataclass 实体（`MatchResult`、`MatchItem`）到 `domain/entities/recruit_data.py`。
- 已扩展 `RecruitDataRepository` Protocol：`create_match_result`、`get_match_result_for_pair`、`append_match_item`。
- 已新增 2 个 ORM models（`MatchResultModel`、`MatchItemModel`）。
- `match_results` 唯一约束 `uk_match_pair (resume_structure_id, jd_structure_id)`；4 个分项分数与 `overall_score` 均为 `Numeric(5, 2)` 且可空（允许部分匹配不评分）；`tier`、`prompt_version`、`rule_version` NOT NULL。
- `match_items.requirement` 与 `match_status` NOT NULL；`evidence_snippet` 可空（无证据时留空）；`skill_category` 可空枚举。
- 已扩展 `SqlAlchemyRecruitDataRepository`：3 个新方法 + `_to_match_result` / `_to_match_item` 转换器。
- 已扩展 `RecruitDataService`：`create_match_result`（强制 `rule_version` 非空、`*_score` ∈ [0, 100]、`resume_structure.task_id == jd_structure.task_id == task.id`、同对拒绝重复创建）、`get_match_result_for_pair`、`append_match_item`（强制 `requirement` 非空、ADR-0009 不变量：`match_status==no_evidence` 时 `evidence_snippet` 必须为空）。
- 已新增手写 Alembic revision `eee1f4a5b330_recruit_match_results.py`（down_revision=`ddd9e1f3a220`）。
- 已扩展 `tests/unit/test_migrations.py`：单 head + 5 节点链式 down_revision 不变量。
- 已扩展 `tests/unit/test_recruit_data_models.py`：新增 2 项断言（match_results 唯一约束 + 必填字段、match_items CASCADE + 必填字段）。
- 已扩展 `tests/unit/test_recruit_data_service.py`：新增 6 项断言（持久化、空 `rule_version` 拒绝、重复对拒绝、超范围分数拒绝、ADR-0009 无证据项拒绝填充 evidence_snippet、有证据项追加成功）。
- `uv run ruff check src tests`：通过。
- `uv run ruff format --check src tests`：通过，56 files already formatted。
- `uv run mypy src`：通过，42 source files 无错误。
- `uv run pytest --cov=recruitment_assistant_agent -q`：69 passed（比上批 +8），总覆盖率 79%。
- `uv run alembic heads`：`eee1f4a5b330 (head)`，单 head。
- 真实 MySQL `upgrade -> downgrade -> upgrade`：未验证（本地未起 MySQL 容器）。

### 第五批：差距与面试问题层

- 目标：持久化匹配差距和结构化面试问题。
- 输出表（2 张）：`gap_analyses`（差距描述 + 建议面试问题种子）、`interview_questions`（问题文本 + 分类 + 难度）。
- 约束：`interview_questions.category` ∈ skill_verification / experience_probe / behavioral / gap_probe；`difficulty` ∈ easy / medium / hard。
- 不做：问题生成节点、API、报告、其他 Agent。
- 验收：同前 + 分类/难度枚举测试。

### 第五批执行记录（2026-07-05）

- 已新增 2 个枚举（`QuestionCategory` skill_verification/experience_probe/behavioral/gap_probe、`QuestionDifficulty` easy/medium/hard）到 `domain/value_objects/recruit_enums.py`。
- 已新增 2 个 frozen dataclass 实体（`GapAnalysis`、`InterviewQuestion`）到 `domain/entities/recruit_data.py`。
- 已扩展 `RecruitDataRepository` Protocol：`append_gap_analysis`、`append_interview_question`。
- 已新增 2 个 ORM models（`GapAnalysisModel`、`InterviewQuestionModel`），并在 `MatchResultModel` 上挂 `gap_analyses` / `interview_questions` 反向关系。
- `gap_analyses.gap_description` NOT NULL、`suggested_question` 可空；`idx_gap_analyses_match (match_result_id)`；FK `fk_gap_match ondelete=CASCADE`。
- `interview_questions.question_text` 与 `category` NOT NULL、`difficulty` 可空；`idx_interview_questions_match (match_result_id)`；FK `fk_q_match ondelete=CASCADE`。
- 已扩展 `SqlAlchemyRecruitDataRepository`：2 个新方法 + `_to_gap_analysis` / `_to_interview_question` 转换器。
- 已扩展 `RecruitDataService`：`append_gap_analysis`（强制 `gap_description` 非空）、`append_interview_question`（强制 `question_text` 非空、`category` 枚举化、`difficulty` 可空枚举化）。
- 已新增手写 Alembic revision `fff2a5b6c440_recruit_gap_interview.py`（down_revision=`eee1f4a5b330`）。
- 已扩展 `tests/unit/test_migrations.py`：单 head + 6 节点链式 down_revision 不变量。
- 已扩展 `tests/unit/test_recruit_data_models.py`：新增 2 项断言（gap_analyses 与 interview_questions 表注册 + CASCADE FK + NOT NULL + 索引）。
- 已扩展 `tests/unit/test_recruit_data_service.py`：新增 6 项断言（gap_analysis 持久化、空 description 拒绝；interview_question 持久化 + 分类/难度覆盖、可选难度、空 text 拒绝）。
- `uv run ruff check src tests`：通过。
- `uv run ruff format --check src tests`：通过，56 files already formatted。
- `uv run mypy src`：通过，42 source files 无错误。
- `uv run pytest --cov=recruitment_assistant_agent -q`：76 passed（比上批 +7），总覆盖率 78%。
- `uv run alembic heads`：`fff2a5b6c440 (head)`，单 head。
- 真实 MySQL `upgrade -> downgrade -> upgrade`：未验证（本地未起 MySQL 容器）。

### 第六批：报告与人工覆盖层

- 目标：持久化招聘分析报告和 admin 人工覆盖记录。
- 输出表（2 张）：
  - `reports`（Markdown 内容 + 可选 PDF 路径 + 过期时间 + 创建人）。
  - `manual_overrides`（admin 修改字段路径 + 旧值 + 新值 + 原因 + admin id）。
- 约束：
  - `reports.expires_at` 必填；过期清理由 RECRUIT-250 的清理任务处理；本批不实现清理。
  - `manual_overrides.match_result_id` 必须引用已存在匹配结果；`reason` 不可为空。
- 不做：报告生成节点、PDF 导出、清理任务、API。
- 验收：同前 + 过期时间非空测试、覆盖原因非空测试。

### 第六批执行记录（2026-07-05）

- 已新增 2 个 frozen dataclass 实体（`Report`、`ManualOverride`）到 `domain/entities/recruit_data.py`，无需新增枚举（`Report.pdf_path` 与 `expires_at` 已直接表达，覆盖审计使用文本字段避免 schema 耦合）。
- 已扩展 `RecruitDataRepository` Protocol：`create_report`、`get_report_for_task`、`append_manual_override`。
- 已新增 2 个 ORM models（`ReportModel`、`ManualOverrideModel`），并在 `MatchResultModel` 上挂 `reports` / `manual_overrides` 反向关系。
- `reports.public_id` 唯一约束 `uk_reports_public_id`；FK `fk_reports_task` / `fk_reports_match` 均 `ondelete=CASCADE`；`fk_reports_creator` 不级联（保护 admin 用户行）；`content_markdown` / `expires_at` / `created_by` NOT NULL，`pdf_path` 可空。
- `manual_overrides` FK `fk_override_match ondelete=CASCADE`、`fk_override_admin` 不级联；`field_path` / `reason` / `admin_id` NOT NULL，`old_value` / `new_value` 可空（允许追加或删除字段的覆盖）。
- `reports` 三个索引：`idx_reports_task`、`idx_reports_match`、`idx_reports_expires`（支持过期清理范围查询）。
- `manual_overrides` 两个索引：`idx_manual_overrides_match`、`idx_manual_overrides_admin`。
- 已扩展 `SqlAlchemyRecruitDataRepository`：3 个新方法 + `_to_report` / `_to_manual_override` 转换器。
- 已扩展 `RecruitDataService`：`create_report`（强制 `content_markdown` 非空、`created_by > 0`、`expires_at` 必须晚于当前、`match_result.task_id == task.id`）、`get_report_for_task`、`append_manual_override`（强制 `field_path` 非空、`reason` 非空、`admin_id > 0`）。
- 已新增手写 Alembic revision `ggg3b8d2e550_recruit_reports_overrides.py`（down_revision=`fff2a5b6c440`）。
- 已扩展 `tests/unit/test_migrations.py`：单 head + 7 节点链式 down_revision 不变量。
- 已扩展 `tests/unit/test_recruit_data_models.py`：新增 2 项断言（reports 必填 + CASCADE + 唯一约束 + 三索引；manual_overrides 必填 + CASCADE + 双索引；FK ondelete 行为）。
- 已扩展 `tests/unit/test_recruit_data_service.py`：新增 10 项断言（report 持久化 + 过期/内容/创建人/跨任务校验、`get_report_for_task` 返回最新、manual_override 持久化 + 空 field_path/empty reason/invalid admin 拒绝）。
- `uv run ruff check src tests`：通过。
- `uv run ruff format --check src tests`：通过，56 files already formatted。
- `uv run mypy src`：通过，42 source files 无错误。
- `uv run pytest --cov=recruitment_assistant_agent -q`：88 passed（比上批 +12），总覆盖率 78%。
- `uv run alembic heads`：`ggg3b8d2e550 (head)`，单 head。
- 真实 MySQL `upgrade -> downgrade -> upgrade`：未验证（本地未起 MySQL 容器）。

### 第七批：Prompt 版本层

- 目标：持久化可审计的 Prompt 版本元数据，为工作流按版本加载模板提供真源。
- 输出表（1 张）：`prompt_versions`（`prompt_name` + `version` + `template_key` + `variables JSON` + `output_schema JSON` + `status` draft/active/retired + `created_by`）。
- 约束：
  - 仅管理员可创建（application service 校验）。
  - 新版本固定为 `draft`；激活/退役后置到 RECRUIT-250 admin API。
  - `template_key` 必须是安全相对 POSIX key（拒绝绝对路径、`..`、Windows 分隔符、盘符）。
  - 唯一索引 `(prompt_name, version)`。
- 不做：模板文件读写、激活 API、工作流加载、前端、其他 Agent。
- 验收：同前 + 安全 template_key 拒绝测试、管理员/普通用户权限测试。

### 第七批执行记录（2026-07-05）

- 已新增枚举 `PromptStatus`（`draft` / `active` / `retired`）到 `domain/value_objects/recruit_enums.py`。
- 已新增 frozen dataclass 实体 `PromptVersion`（`public_id` / `prompt_name` / `version` / `template_key` / `status` / `created_by` 必填，`variables` / `output_schema` 可空 JSON，`id` 可空）到 `domain/entities/recruit_data.py`。
- 已扩展 `RecruitDataRepository` Protocol：`create_prompt_version`、`get_prompt_version`、`get_active_prompt_version`。
- 已新增 ORM model `PromptVersionModel`：唯一约束 `uk_prompt_name_version (prompt_name, version)`、索引 `idx_prompt_versions_name_status (prompt_name, status)`、FK `fk_prompt_creator → users.id`、`status` 默认 `draft`、`prompt_name` / `version` / `template_key` / `created_by` NOT NULL、`variables` / `output_schema` JSON 可空。
- 已扩展 `SqlAlchemyRecruitDataRepository`：3 个新方法 + `_to_prompt_version` 转换器；`get_active_prompt_version` 按 `created_at` 倒序取首条。
- 已扩展 `RecruitDataService`：
  - `create_prompt_version`：非 admin → `ForbiddenError`；空 `prompt_name` / `version` → `ValueError`；不安全 `template_key` → `ValueError`；重复 `(prompt_name, version)` → `ValueError`；新版本固定 `status=draft`。
  - `get_prompt_version`、`get_active_prompt_version`：只读查询，校验入参非空。
- 新增私有 `_validate_template_key(key)`：拒绝空字符串、Windows `\`、绝对 `/`、盘符 `X:`、`..` 父级跳越、双斜杠空洞路径段。
- 已新增手写 Alembic revision `hhh5c9e3f660_recruit_prompt_versions.py`（down_revision=`ggg3b8d2e550`）。
- 已扩展 `tests/unit/test_migrations.py`：单 head + 8 节点链式 down_revision 不变量。
- 已扩展 `tests/unit/test_recruit_data_models.py`：新增 1 项断言（prompt_versions 唯一约束 + 必填字段 + 索引 + JSON 可空 + 默认 draft）。
- 已扩展 `tests/unit/test_recruit_data_service.py`：新增 8 项断言（draft 持久化 + variables/output_schema 注入；非 admin 拒绝；7 种不安全 template_key 拒绝；重复 `(prompt_name, version)` 拒绝；空 name/version 拒绝；`get_prompt_version` 命中；`get_active_prompt_version` 无 active 时返回 None）。
- `uv run ruff check src tests`：通过。
- `uv run ruff format --check src tests`：通过，56 files already formatted。
- `uv run mypy src`：通过，42 source files 无错误。
- `uv run pytest --cov=recruitment_assistant_agent -q`：96 passed（比上批 +8），总覆盖率 78%。
- `uv run alembic heads`：`hhh5c9e3f660 (head)`，单 head。
- 真实 MySQL `upgrade -> downgrade -> upgrade`：未验证（本地未起 MySQL 容器）。

### RECRUIT-230 整体完成情况

- 7 条 Alembic revision：`0001` 基线 + `ccc46fb6a333` / `bbb7c5d2e110` / `ddd9e1f3a220` / `eee1f4a5b330` / `fff2a5b6c440` / `ggg3b8d2e550` / `hhh5c9e3f660`，全部链式 down_revision 闭环，单 head。
- 16 张表：`users` / `tasks` / `materials` / `agent_runs` / `node_runs` / `resume_structures` / `skill_evidence` / `experience_evidence` / `education_evidence` / `jd_structures` / `jd_requirements` / `match_results` / `match_items` / `gap_analyses` / `interview_questions` / `reports` / `manual_overrides` / `prompt_versions`。
- 应用服务覆盖：用户镜像、任务/材料登记、Agent/Node 审计、Resume/JD 结构化与证据、Match 结果与逐项、Gap/Interview、Report/ManualOverride、PromptVersion。
- ADR-0009 公平性硬约束：`resume_structures` 表不含 11 类敏感属性列；`append_match_item` 拒绝在 `no_evidence` 项上填充证据片段；`create_prompt_version` 仅 admin 可创建。
- ADR-0007 统一认证：`users` 表只存镜像，无密码字段；role/status 来自 JWT claim。
- 数据层 7 批全部本地通过；RECRUIT-240 工作流阶段在下一循环启动。

### RECRUIT-230 整体验收

- 7 条 Alembic revision 各自可升级/回滚；`alembic heads` 单 head。
- ORM Model、API DTO（未实现）、领域对象、工作流 State（未实现）不混用。
- repository 不自行提交事务；事务边界由 application/use case 控制。
- `users` 表不存密码。
- 所有 `evidence_snippet`、`reason`、`summary`、`disclaimer` 类字段非空约束在 DB 层。
- 敏感属性不入库（schema 不含字段；解析节点剔除逻辑后置到 RECRUIT-240）。
- 评分规则、Prompt 模板、文件限制、敏感属性清单不在业务代码硬编码；类型化 Settings 或版本化 YAML 真源。
- `.env.example` 无真实密钥。

## 第二块：RECRUIT-240 匹配与面试工作流

类比 `LEGAL-140`，按切片推进；每切片不接真实 DeepSeek、ClamAV、文件存储，所有外部服务在 mock/adapter 边界。

### 第一切片：workflow/state/mock 节点边界

- 目标：在不接真实外部服务的条件下，先落地可测试的 LangGraph 工作流边界。
- 输入：`task_id`、`user_id`、`material_kind`、`prompt_version`、`workflow_version`；测试可显式注入 `mock_resume`/`mock_jd`/`mock_chunks`。
- 输出：`RecruitmentWorkflowState`、8 个节点纯函数、`build_recruitment_workflow_graph()` 和相邻单元测试。
- 节点：`file_safety`、`task_route`、`resume_parse`、`jd_parse`、`evidence_match`、`fairness_check`、`gap_question_gen`、`persist`。
- 约束：
  - 不调用真实外部服务；`resume_parse`/`jd_parse` 只消费 mock 输入。
  - `evidence_match` 使用确定性占位逻辑；`match`/`partial`/`no_evidence` 三档必须有无证据区分。
  - `fairness_check` 是 fail-closed：检测到敏感属性字段名出现在 state 中时设置 `FAIRNESS_VIOLATION` 中断。
  - `persist` 只暴露持久化边界，不写数据库。
- 不做：API/DTO、SSE、真实 LLM、文件存储、ClamAV、Qdrant、BGE、节点审计入库、取消/重试 runner、前端和其他 Agent。

### 第一切片执行记录（2026-07-05）

- 已新增 `RecruitmentWorkflowState` / `RecruitmentWorkflowUpdate` 及 Resume/JD/Match/Gap/Interview TypedDict 状态契约到 `workflows/recruitment_state.py`。
- 已新增 8 个纯函数节点到 `workflows/recruitment_nodes.py`：`file_safety`、`task_route`、`resume_parse`、`jd_parse`、`evidence_match`、`fairness_check`、`gap_question_gen`、`persist`。
- 已新增 `build_recruitment_workflow_graph()` 到 `workflows/recruitment_graph.py`，按 LangGraph 条件边执行；任一节点写入 `error_code` 后直接终止，不继续调用后续节点或持久化边界。
- `resume_parse` / `jd_parse` 只消费 `mock_resume` / `mock_jd`，不调用真实 DeepSeek、ClamAV、文件存储或数据库。
- `evidence_match` 使用确定性占位逻辑输出 `match` / `partial` / `no_evidence`；`no_evidence` 项不包含 `evidence_snippet`。
- `fairness_check` 对 11 类敏感属性字段名 fail-closed：`age`、`gender`、`marital_status`、`ethnicity`、`health`、`political_status`、`photo`、`id_card`、`hometown`、`religion`、`hukou`；命中后设置 `FAIRNESS_VIOLATION`、`task_status=failed`、`persisted=False`。
- `persist` 只暴露持久化边界，不写数据库；`simulate_db_unavailable=True` 时返回 `DB_UNAVAILABLE`。
- 已新增 `tests/unit/test_recruitment_workflow.py`：覆盖 unsupported material_kind、三档匹配、11 类敏感字段、全图 happy path、fairness violation 终止、DB unavailable 边界。
- 代码审查：首次发现失败路径继续执行与 `no_evidence` 空证据字段两个 HIGH 问题；已修复并复审通过，0 blocking findings。
- `uv run ruff check src tests`：通过。
- `uv run ruff format --check src tests`：通过，60 files already formatted。
- `uv run mypy src`：通过，45 source files 无错误。
- `uv run pytest tests/unit/test_recruitment_workflow.py`：18 passed。
- `uv run pytest`：114 passed，总覆盖率 81%。
- `uv run alembic heads`：`hhh5c9e3f660 (head)`，单 head。
- 真实 MySQL `upgrade -> downgrade -> upgrade`：未验证（本地未起 MySQL 容器）。

### 第二切片：workflow 审计映射

- 目标：把 workflow state / error code 映射到 `agent_runs` / `node_runs`。
- 输出：`RecruitmentWorkflowAuditService`、`WorkflowErrorMapping`、`map_workflow_error()`、节点 started/finished 审计写入边界。
- 失败映射：
  - 无错误 → `success`。
  - `PARSE_FAILED`、`LLM_TIMEOUT`、`DB_UNAVAILABLE`、`RATE_LIMITED` → `retrying` 且 `retryable=true`。
  - `INPUT_BLOCKED`、`FAIRNESS_VIOLATION`、`FILE_INFECTED` → `failed` 且 `retryable=false`。
- 审计最小化：metadata 只记录节点名、事件、retryable、tier、敏感属性标记；不记录完整 Prompt、简历原文、JD 原文。

### 第二切片执行记录（2026-07-05）

- 已新增 `application/services/workflow_audit_service.py`，提供 `RecruitmentWorkflowAuditService`、`WorkflowErrorMapping`、`map_workflow_error()`、`sanitize_workflow_error_code()`、`calculate_duration_ms()`、`build_node_finish_metadata()`。
- `start_run()` 通过 `RecruitDataService.create_agent_run()` 写入 run 审计，并复用 user-owned task 授权边界；`state.thread_id` 作为 task public id。
- `record_node_started()` 写入 `RunStatus.RUNNING` 节点审计，metadata 仅包含 `event` 与 `node_name`。
- `record_node_finished()` 将 workflow `error_code` 映射为 retry-aware `RunStatus`：无错误 → `success`；`PARSE_FAILED` / `LLM_TIMEOUT` / `DB_UNAVAILABLE` / `RATE_LIMITED` → `retrying`；`CANCELED` → `canceled`；其他 allowlist terminal 错误 → `failed`。
- 安全修复：未知 `error_code` 统一规范化为 `UNKNOWN_WORKFLOW_ERROR` 后持久化，避免把异常文本、候选人字段、Prompt 或 DB 详情写入审计表。
- 安全修复：metadata 不保存 `overall_tier` 原值，仅保存 `has_overall_tier`、`match_items_count`、`gaps_count`、`has_fairness_violation` 等紧凑计数/布尔标记；不记录完整 Prompt、简历/JD 原文或敏感属性明细。
- 已导出 `RecruitmentWorkflowAuditService`、`WorkflowErrorMapping`、`map_workflow_error` 到 `application/services/__init__.py`。
- 已新增 `tests/unit/test_workflow_audit_service.py`：覆盖 retryable/non-retryable/canceled/success 映射、run/node started、success finish metadata、retryable failure、公平性失败不泄漏敏感值、未知错误码清洗。
- 安全审查发现 2 个 MEDIUM（`overall_tier` 原值进入 metadata、未知 error_code 原样持久化），均已修复并补测试。
- `uv run ruff check src tests`：通过。
- `uv run ruff format --check src tests`：通过，62 files already formatted。
- `uv run mypy src`：通过，46 source files 无错误。
- `uv run pytest tests/unit/test_workflow_audit_service.py`：8 passed。
- `uv run pytest`：122 passed，总覆盖率 82%。
- `uv run alembic heads`：`hhh5c9e3f660 (head)`，单 head。
- 本切片不改数据库 schema；真实 MySQL `upgrade -> downgrade -> upgrade`：未验证（本地未起 MySQL 容器）。

### 第三切片：workflow runner 应用边界

- 目标：在不暴露 HTTP API、不接真实外部服务的条件下，提供顺序执行纯节点的应用层 runner。
- 输出：`RecruitmentWorkflowRunnerService`、`WorkflowNodeSpec`、`WorkflowRunResult`、`prepare_retry_state()`、`mark_canceled()`。
- 行为：按节点顺序记录 started/finished 审计；每个节点执行后合并 state；遇到 `error_code` 立即停止；取消入口在运行节点前标记 `CANCELED`；重试入口清理 `error_code` 和 `node_trace`。

### 第三切片执行记录（2026-07-05）

- 已新增 `application/services/workflow_runner_service.py`，提供 `RecruitmentWorkflowRunnerService`、`WorkflowNodeSpec`、`WorkflowRunResult`、`merge_workflow_update()`、`prepare_retry_state()`、`mark_canceled()`。
- runner 按 `file_safety → task_route → resume_parse → jd_parse → evidence_match → fairness_check → gap_question_gen → persist` 顺序执行纯节点；每个节点先创建 RUNNING 审计，完成后更新同一条 `node_runs` 为终态，避免遗留 RUNNING 行。
- runner 在成功、失败、retryable failure、取消入口均调用 `finish_run()` 更新同一条 `agent_runs` 终态；取消入口不执行任何节点并写入 `RunStatus.CANCELED`。
- 节点 handler 抛异常时不持久化原始异常文本，统一写入 `UNKNOWN_WORKFLOW_ERROR`、`persisted=False`，并更新当前 node/run 为失败终态。
- 已扩展数据层最小边界：`RecruitDataRepository.update_agent_run()` / `update_node_run()`、`RecruitDataService.finish_agent_run()` / `finish_node_run()`、SQLAlchemy repository 同名实现。
- 已新增/扩展 `tests/unit/test_workflow_runner_service.py` 与 `tests/unit/test_workflow_audit_service.py`，覆盖成功、非重试失败、重试失败、取消、异常净化、node/run 终态更新。
- 代码审查和安全审查先发现 AgentRun 未终态化、异常后 node audit 卡 RUNNING、start/finish 双行遗留 RUNNING；已全部修复并复审无 blocking findings。
- `uv run ruff check src tests`：通过。
- `uv run ruff format --check src tests`：通过，64 files already formatted。
- `uv run mypy src`：通过，47 source files 无错误。
- `uv run pytest`：128 passed，总覆盖率 81%。
- `uv run alembic heads`：`hhh5c9e3f660 (head)`，单 head。
- 本切片不改数据库 schema；真实 MySQL `upgrade -> downgrade -> upgrade`：未验证（本地未起 MySQL 容器）。

### 第四切片：Prompt 模板加载边界

- 目标：在不调用真实 LLM、不改 API、不改数据库的条件下，提供版本化 Prompt 模板安全加载与变量渲染边界。
- 输出：`PromptTemplateLoader`、`PromptRenderResult`、`PromptTemplateError`、`validate_template_key()`、`extract_required_variables()`。
- 行为：校验 `template_key` 为安全相对 POSIX key；从受控根读取 UTF-8 模板；按 `variables.required` 校验必填变量；渲染 `{variable}` 占位符。
- 复用法律 Agent 已验证的同名边界设计；不复制法律 Agent 文件，只在招聘 Agent 子仓内独立实现。

### 第四切片执行记录（2026-07-05）

- 已新增 `prompts/template_loader.py`，提供 `PromptTemplateLoader`、`PromptRenderResult`、`PromptTemplateError`、`validate_template_key()`、`extract_required_variables()`。
- `validate_template_key()` 仅允许安全相对 POSIX key，拒绝空 key、绝对路径、`..` / `.`、Windows 分隔符、盘符或 scheme、重复分隔符。
- `PromptTemplateLoader` 从受控根目录读取 UTF-8 模板，并用 resolved path + `is_relative_to()` 防止越界读取。
- `render()` 只支持简单 `{identifier}` 占位符；拒绝非法占位符、format spec、conversion、格式串错误，并统一抛出 `PromptTemplateError`。
- 已将 invalid UTF-8、malformed format string、嵌套 format spec / conversion 等异常统一包装为 `PromptTemplateError`，避免调用方收到底层异常细节。
- 已更新 `prompts/__init__.py` 导出 Prompt loader 公共边界。
- 已新增 `tests/unit/test_prompt_template_loader.py`，覆盖安全 key 允许/拒绝、变量元数据校验、模板读取渲染、缺失变量、越界路径、缺失模板、非法 UTF-8 与格式串异常包装。
- 代码审查先发现 invalid UTF-8 / format string 可能泄漏非 `PromptTemplateError`；已补回归并修复。安全复审无 blocking findings。
- `uv run ruff check src tests`：通过。
- `uv run ruff format --check src tests`：通过，66 files already formatted。
- `uv run mypy src`：通过，48 source files 无错误。
- `uv run pytest`：149 passed，总覆盖率 82%。
- `uv run alembic heads`：`hhh5c9e3f660 (head)`，单 head。
- 本切片不改数据库 schema、不调用真实 LLM、不接外部服务；真实 MySQL `upgrade -> downgrade -> upgrade`：未验证（本地未起 MySQL 容器）。

### 第五切片：Prompt 输出 schema 校验边界

- 目标：在不调用真实 LLM、不接 workflow 节点的条件下，对 Prompt / mock LLM 输出建立结构化校验边界。
- 输出：`PromptOutputValidator`、`PromptValidatedOutput`、`PromptOutputValidationError`、`parse_json_object_output()`。
- 行为：解析 raw JSON；要求顶层为 JSON object；校验 `output_schema.type == object`；校验 required 字段；按 properties 中的 `type` 校验。
- 不执行模型输出中的命令、SQL 或路径。

### 第五切片执行记录（2026-07-05）

- 已新增 `prompts/output_validator.py`，提供 `PromptOutputValidator`、`PromptValidatedOutput`、`PromptOutputValidationError`、`parse_json_object_output()`。
- 校验边界要求 raw output 为标准 JSON object，拒绝空值、数组、null、非法 JSON、`NaN` / `Infinity` 等非标准常量和超长输出。
- schema 子集限制为 object 根节点，支持 `string`、`array`、`number`、`boolean`、`null`、`object`，并递归校验 object `properties` / `required` 与 array `items`。
- 默认拒绝未知字段；required 字段必须在 properties 中声明；number 允许 int/finite float，拒绝 bool 和非有限 float。
- JSON 解析错误和模板 value format 错误不保留原始输出/候选人内容异常链。
- 已新增/更新 `tests/unit/test_prompt_output_validator.py`、`tests/unit/test_prompt_template_loader.py` 覆盖上述边界。
- 本地门禁：`uv run ruff check src tests`、`uv run ruff format --check src tests`、`uv run mypy src`、`uv run pytest`（180 passed，83% coverage）、`uv run alembic heads`（`hhh5c9e3f660 (head)`）均通过。
- 本切片不改数据库 schema、不调用真实 LLM、不接外部服务；为避免阻塞产品闭环，非阻塞 MEDIUM 级审查意见后续默认记录/顺手修，不再反复卡同一循环。

### 第六切片：Prompt-backed resume_parse 节点

- 目标：让 resume_parse 可通过 Prompt loader + mock LLM adapter + output validator 生成结构化简历。
- 输出：`ResumeParsePromptService`、`ResumeParseResult`、`make_prompt_resume_parse_node()`、graph 注入点。
- 行为：渲染 `recruit_resume_parse` Prompt；调用注入的 LLM adapter；通过 validator 校验；将 `summary`、`total_years_exp`、`skills`、`experiences`、`educations`、`soft_skills` 写入 state；显式剔除 11 类敏感属性；输出异常时降级到 `PARSE_FAILED`。

### 第七切片：Prompt-backed jd_parse 节点

- 目标：让 jd_parse 通过 Prompt loader + mock adapter + validator 生成结构化 JD。
- 输出：`JDParsePromptService`、`JDParseResult`、`make_prompt_jd_parse_node()`、graph 注入点。
- 行为：渲染 `recruit_jd_parse` Prompt；输出包含 `job_title`、`summary`、`requirements[]`；`requirements[].requirement_type` ∈ must_have/nice_to_have。

### 第八切片：Prompt-backed evidence_match 节点

- 目标：让 evidence_match 通过 Prompt loader + mock adapter + validator 生成结构化匹配结果。
- 输出：`EvidenceMatchPromptService`、`MatchResultData`、`make_prompt_evidence_match_node()`、graph 注入点。
- 行为：渲染 `recruit_evidence_match` Prompt；输出每条岗位要求的 `match`/`partial`/`no_evidence` + 简历证据片段；分项分数计算推迟到规则真源加载切片。
- 约束：无证据项不得填充候选人能力；证据片段必须来自简历（mock 简历输入）。

### 第九切片：Prompt-backed fairness_check 节点

- 目标：让 fairness_check 通过 Prompt loader + mock adapter + validator 输出结构化公平性判断。
- 输出：`FairnessCheckPromptService`、`FairnessCheckResult`、`make_prompt_fairness_check_node()`、graph 注入点。
- 行为：渲染 `recruit_fairness_check` Prompt；校验输出 `{fairness_passed: bool, violation_details: list[str] | null}`；fail-closed：模型输出非法或检测到敏感属性泄露时设置 `FAIRNESS_VIOLATION` 并中断。

### 第十切片：Prompt-backed gap_question_gen 节点 + 工作流装配

- 目标：让 gap_question_gen 通过 Prompt loader + mock adapter + validator 生成差距与面试问题；同时把 5 个 Prompt-backed 节点集中装配为一个可验证 graph factory。
- 输出：`GapQuestionPromptService`、`GapQuestionResult`、`make_prompt_gap_question_node()`、`RecruitmentPromptWorkflowFactory`、`RecruitmentPromptWorkflowPrompts`。
- 行为：集中组装 resume_parse/jd_parse/evidence_match/fairness_check/gap_question_gen 注入节点；执行 file_safety → task_route → resume_parse → jd_parse → evidence_match → fairness_check → gap_question_gen → persist 全链路。

### RECRUIT-240 后置切片

- 真实 DeepSeek adapter（独立切片，单独 ADR 决策是否使用 Deep Agents harness）。
- 评分规则 YAML 真源加载（影响 evidence_match 的分数计算，单独切片）。
- 文件安全校验 + ClamAV adapter（与 RECRUIT-250 文件上传 API 同切片）。

## 第三块：RECRUIT-250 API、报告与人工复核

### 第一切片：API/SSE 契约前置设计

- 目标：在写 endpoint 前先冻结 OpenAPI/SSE 事件契约。
- 输出：`docs/api-contract.md` 增补任务/材料/运行/报告/admin 复核/人工覆盖 6 类端点；SSE 事件枚举；错误码映射。
- 不做：endpoint 实现。

### 第二切片：任务与材料 API

- 目标：实现 `POST /v1/tasks`（multipart 上传）、`GET /v1/tasks/{id}`、`DELETE /v1/tasks/{id}`。
- 输出：`api/v1/endpoints/recruit_tasks.py`、`api/v1/schemas/recruit_tasks.py`、文件安全 adapter 边界（含 ClamAV 边界、文件大小/页数/类型校验）。
- 约束：上传后立即排队解析；不直接同步调用 LLM；杀毒失败返回 `FILE_INFECTED` 不可恢复。

### 第三切片：分析运行 API + SSE

- 目标：实现 `POST /v1/threads/{task_id}/runs`、`GET /v1/runs/{run_id}/events`（SSE）。
- 输出：`api/v1/endpoints/recruit_runs.py`、SSE 事件序列化器、运行状态查询。
- 约束：SSE 心跳来自 Redis（仍可用 mock）；取消信号通过 Redis pub/sub。

### 第四切片：admin 复核与人工覆盖 API

- 目标：实现 `GET /v1/admin/tasks/{id}`、`POST /v1/admin/tasks/{id}/review`、`POST /v1/admin/match-results/{id}/override`。
- 输出：admin 端点、权限依赖（仅 admin）、复核状态变更、人工覆盖记录。
- 约束：admin 签字是出报告的前置条件；普通用户访问未签字内容返回 `REVIEW_REQUIRED`。

### 第五切片：报告导出

- 目标：实现 `GET /v1/reports/{id}/export?format=pdf|md`。
- 输出：报告端点、Markdown → PDF 转换 adapter（占位，不接真实 wkhtmltopdf）。
- 约束：报告 `expires_at` 到期拒绝下载；PDF 临时生成，响应后删除。

## 第四块：RECRUIT-260 质量与验收

### 第一切片：公平性对抗样本测试集

- 目标：CI 跑 F1/F2/F3/F4 四个对抗样本，敏感属性替换后分数波动 < 5%。
- 输出：`tests/evaluation/test_fairness.py`、20 份脱敏样本（10 正常 + 5 对抗 + 5 边缘）。
- 约束：对抗样本失败阻断发布。

### 第二切片：结构化准确性测试集

- 目标：验证相同简历/JD 重复执行结果稳定；无证据项不被填充；引用片段可追溯到简历。
- 输出：`tests/evaluation/test_structural_accuracy.py`、轨迹评测脚本。

### 第三切片：恢复与性能测试

- 目标：验证取消/重试/失败恢复；性能基线（单任务端到端 < 30s on mock）。
- 输出：`tests/e2e/test_run_recovery.py`、`tests/e2e/test_performance_baseline.py`。

### 第四切片：CI/质量门禁汇总

- 目标：汇总 `ruff/mypy/pytest/alembic/契约/迁移/安全/依赖/镜像` 全套门禁证据。
- 输出：本阶段文件验证证据节、`docs/plans/current.md` 切到 RECRUIT-260 已完成、交付清单。
- 验证命令：见下文「验证命令」节。

## 不做事项

- 不自动决定录用或淘汰。
- 不基于性别、年龄、民族、婚育、照片、身份证号、籍贯、宗教信仰、政治面貌、健康、户籍评分。
- 不抓取候选人外部隐私。
- 不实现完整 ATS、职位发布、Offer、薪酬、审批系统。
- 不持久化原始简历/JD 文件；解析成功后立即删除（字段持久化，删除动作后置到 RECRUIT-240/250）。
- 不连接生产 MySQL、真实 DeepSeek、ClamAV、Qdrant、Redis、对象存储。
- 不在业务代码硬编码 Prompt、模型名、评分权重、文件限制、敏感属性清单。
- 不预置岗位模板、任务分类、评分规则 YAML 内容。
- 不修改法律 Agent、智能问数 Agent、前端、运维模块。
- 不修改用户全局 Claude/Codex 配置。

## 依赖与延期项

- 真实 DeepSeek 接入：延期到 RECRUIT-240 第十切片之后单独成片。
- 真实 ClamAV 接入：延期到 RECRUIT-250 第二切片文件上传时单独决策。
- 真实 Qdrant / Embedding：本阶段不引入；招聘 Agent 不做 RAG。
- 评分规则 YAML 真源内容：等业务确认权重细节后填入版本化文件；本阶段表结构先建。
- 20 份脱敏样本：RECRUIT-260 第一切片由 AI 生成草案，用户审阅后入库。
- 飞书接入：不在招聘 Agent 范围；数据查询 Agent 在 FEISHU-500 处理。

## 验收标准

### RECRUIT-230

- 7 条 Alembic revision 各自可升级/回滚；`alembic heads` 单 head。
- ORM Model、领域对象和工作流 State 不混用。
- repository 不自行提交事务；事务边界由 application/use case 控制。
- 路由不直接访问 ORM、SQL、DeepSeek 或文件系统。
- `users` 只作为统一认证用户镜像，不保存密码。
- 任务和材料具备用户隔离约束。
- run / node 审计支持 `pending`、`running`、`success`、`failed`、`retrying`、`canceled` 状态。
- `.env.example` 无真实密钥，关键配置缺失时快速失败。

### RECRUIT-240

- 工作流图、节点 I/O、状态 Schema 稳定可测。
- 5 个 Prompt-backed 节点（resume_parse/jd_parse/evidence_match/fairness_check/gap_question_gen）通过 mock adapter + validator 完整跑通。
- 公平性 fail-closed：检测到敏感属性字段名出现时设置 `FAIRNESS_VIOLATION` 中断。
- 无证据项不被填充为候选人能力。
- 审计 metadata 不记录完整 Prompt、简历原文、JD 原文。

### RECRUIT-250

- OpenAPI 契约冻结；前端可基于契约 mock 并行开发。
- 任务/材料/运行/报告/admin 端点全部实现并通过契约测试。
- SSE 事件序列正确；取消/重试信号可验证。
- admin 签字是出报告的前置条件；普通用户访问未签字内容返回 `REVIEW_REQUIRED`。

### RECRUIT-200 总体验收

- 课件六项招聘辅助能力（结构化、匹配、差距、面试问题、人工复核、报告导出）有 API 与测试证据。
- 公平性对抗样本 CI 阻断发布。
- Ruff、MyPy、Pytest、迁移、契约、安全扫描和镜像检查通过或明确记录未验证项。

## 验证命令

在 `agents/recruitment-assistant-agent` 下执行：

```powershell
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy src
uv run pytest --cov=recruitment_assistant_agent
uv run alembic heads
uv run alembic current
```

涉及迁移时补充（本地 MySQL 8.0.36 可用时）：

```powershell
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic upgrade head
```

没有真实 MySQL 时必须明确记录为"真实 DB 未验证"，不得写成通过。

## 停止条件

- 统一认证边界发生变化。
- 需要招聘 Agent 存储密码或跨库访问前端认证表。
- 用户要求自动录用/淘汰或敏感属性评分。
- 匹配规则无法解释或没有岗位要求依据。
- 需求扩大为完整招聘管理系统。
- 数据模型与 `agents/recruitment-assistant-agent/docs/detailed-design.md` 或 ADR-0007 / ADR-0009 冲突。
- 发现需要修改 API 主版本、数据库权限、跨 Agent 边界或部署架构。
- Codex 在 LEGAL-100 的并行工作与本仓产生冲突。

出现任一项时停止当前阶段并与用户对齐。

## 回滚方式

- 计划阶段：回滚 `current.md` 指向上一阶段（FOUND-010 或 LEGAL-100），删除或修订本阶段计划。
- 迁移阶段：每个 Alembic revision 必须提供 downgrade；失败时回退到上一 revision。
- 代码阶段：按 `agents/recruitment-assistant-agent` 模块独立回滚，不影响法律、智能问数、前端和运维模块。
- 工作流阶段：按版本切换回上一稳定图和 Prompt，不覆盖历史运行记录。
- 文件解析或报告能力异常时可单独关闭对应 adapter，保留任务查询和人工复核能力。
