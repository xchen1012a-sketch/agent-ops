# RECRUIT-210 智能招聘 Agent 详细设计

> 状态：DESIGN-002 子阶段设计产出；FOUND-010 已建立工程基础，等待 RECRUIT-200/RECRUIT-230 业务实现授权。
> 真源：本文件 + `specification.md` + `adr/0007-unified-auth.md`、`adr/0009-recruitment-fairness.md`。

## 1. 用例

| 角色 | 用例 |
|---|---|
| 普通用户 | 新建分析任务、上传简历/JD、查看任务状态、查看三档匹配结果、查看面试问题、查看报告、提交反馈 |
| 管理员 | 评分规则真源查看（只读）、人工复核与签字、对抗测试审计、运行审计 |
| 系统 | 解析后立即删除原始文件；所有匹配必须 admin 签字才能导出报告 |

## 2. 材料生命周期（隐私核心）

```text
上传 (临时文件)
  ↓ ClamAV 扫描
  ↓ 大小/页数/类型校验
解析 (LangGraph 节点)
  ↓ 敏感属性剔除
结构化结果入库 (recruitment_agent_db)
  ↓ 原始文件删除（仅保留 SHA-256 hash 指纹）
匹配 + 评分
  ↓ 进入人工复核队列
admin 签字
  ↓ 生成报告
报告保留（用户可下载 N 天）
  ↓ 过期自动清理
```

**所有阶段不记录**：年龄、性别、婚姻、户籍、民族、健康、政治面貌、照片、身份证号、籍贯、宗教信仰。

## 3. 实体关系图

```text
User ─< Task >── ResumeMaterial
              └── JDMaterial
              ├─< ResumeStructure
              ├─< JDStructure
              ├─< MatchResult ─< MatchItem
              ├─< GapAnalysis
              ├─< InterviewQuestion
              ├─< Report
              ├─< AgentRun ─< NodeRun
              └─< ManualOverride >── AdminUser

ResumeStructure ─< SkillEvidence
                ─< ExperienceEvidence
                ─< EducationEvidence
                ─< SoftSkillEvidence
```

## 4. 数据库表设计

### 4.1 任务

```sql
CREATE TABLE tasks (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  public_id       CHAR(36) NOT NULL UNIQUE,
  user_id         BIGINT UNSIGNED NOT NULL,
  title           VARCHAR(200),
  status          ENUM('uploaded','parsing','parsed','matching','reviewing','completed','failed') NOT NULL DEFAULT 'uploaded',
  priority        ENUM('normal','urgent') NOT NULL DEFAULT 'normal',
  review_status   ENUM('pending','approved','rejected','changes_requested') NOT NULL DEFAULT 'pending',
  reviewed_by     BIGINT UNSIGNED,
  reviewed_at     DATETIME(6),
  created_at      DATETIME(6) NOT NULL,
  updated_at      DATETIME(6) NOT NULL,
  INDEX idx_tasks_user (user_id, created_at DESC),
  INDEX idx_tasks_review (review_status, created_at)
);
```

### 4.2 材料元数据（含已删除标记）

```sql
CREATE TABLE materials (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  public_id       CHAR(36) NOT NULL UNIQUE,
  task_id         BIGINT UNSIGNED NOT NULL,
  kind            ENUM('resume','jd') NOT NULL,
  original_filename VARCHAR(255) NOT NULL,
  file_hash       CHAR(64) NOT NULL,                   -- SHA-256
  file_size       INT NOT NULL,
  mime_type       VARCHAR(100) NOT NULL,
  scan_status     ENUM('pending','clean','infected','failed') NOT NULL DEFAULT 'pending',
  original_deleted BOOLEAN NOT NULL DEFAULT FALSE,     -- 原文已删除
  deleted_at      DATETIME(6),
  created_at      DATETIME(6) NOT NULL,
  CONSTRAINT fk_material_task FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
  INDEX idx_materials_hash (file_hash)
);
```

### 4.3 简历结构化

```sql
CREATE TABLE resume_structures (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  task_id         BIGINT UNSIGNED NOT NULL,
  material_id     BIGINT UNSIGNED NOT NULL,
  version         INT NOT NULL DEFAULT 1,              -- 人工修正后版本+1
  summary         TEXT,
  total_years_exp DECIMAL(4,1),
  raw_structured  JSON NOT NULL,                       -- 完整结构化结果
  created_at      DATETIME(6) NOT NULL,
  UNIQUE KEY uk_resume_task_version (task_id, version),
  CONSTRAINT fk_resume_material FOREIGN KEY (material_id) REFERENCES materials(id)
);

CREATE TABLE skill_evidence (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  resume_structure_id BIGINT UNSIGNED NOT NULL,
  skill_name      VARCHAR(100) NOT NULL,
  evidence_snippet TEXT NOT NULL,                      -- 来自简历的原文片段
  source_section  VARCHAR(100),                        -- e.g. "技能列表"
  proficiency     ENUM('beginner','intermediate','advanced','expert'),
  CONSTRAINT fk_skill_resume FOREIGN KEY (resume_structure_id) REFERENCES resume_structures(id) ON DELETE CASCADE,
  INDEX idx_skill_resume (resume_structure_id)
);

CREATE TABLE experience_evidence (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  resume_structure_id BIGINT UNSIGNED NOT NULL,
  role_title      VARCHAR(100) NOT NULL,
  company_redacted VARCHAR(100),                       -- 公司名可脱敏（可选）
  duration_months INT NOT NULL,
  evidence_snippet TEXT NOT NULL,
  CONSTRAINT fk_exp_resume FOREIGN KEY (resume_structure_id) REFERENCES resume_structures(id) ON DELETE CASCADE
);

CREATE TABLE education_evidence (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  resume_structure_id BIGINT UNSIGNED NOT NULL,
  degree          ENUM('high_school','associate','bachelor','master','phd','other') NOT NULL,
  major           VARCHAR(100),
  school_tier     ENUM('tier1','tier2','tier3','overseas','other'),
  graduation_year INT,
  CONSTRAINT fk_edu_resume FOREIGN KEY (resume_structure_id) REFERENCES resume_structures(id) ON DELETE CASCADE
);
```

### 4.4 JD 结构化

```sql
CREATE TABLE jd_structures (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  task_id         BIGINT UNSIGNED NOT NULL,
  material_id     BIGINT UNSIGNED NOT NULL,
  version         INT NOT NULL DEFAULT 1,
  job_title       VARCHAR(200) NOT NULL,
  summary         TEXT,
  raw_structured  JSON NOT NULL,
  created_at      DATETIME(6) NOT NULL,
  UNIQUE KEY uk_jd_task_version (task_id, version),
  CONSTRAINT fk_jd_material FOREIGN KEY (material_id) REFERENCES materials(id)
);

CREATE TABLE jd_requirements (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  jd_structure_id BIGINT UNSIGNED NOT NULL,
  requirement     VARCHAR(255) NOT NULL,
  requirement_type ENUM('must_have','nice_to_have') NOT NULL,
  category        ENUM('skill','experience','education','certification','soft_skill') NOT NULL,
  weight_hint     DECIMAL(3,2),                        -- 0.00-1.00，可选人工权重提示
  CONSTRAINT fk_req_jd FOREIGN KEY (jd_structure_id) REFERENCES jd_structures(id) ON DELETE CASCADE
);
```

### 4.5 匹配结果

```sql
CREATE TABLE match_results (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  task_id         BIGINT UNSIGNED NOT NULL,
  resume_structure_id BIGINT UNSIGNED NOT NULL,
  jd_structure_id BIGINT UNSIGNED NOT NULL,
  skill_score     DECIMAL(5,2),                        -- admin 可见
  experience_score DECIMAL(5,2),
  education_score DECIMAL(5,2),
  soft_skill_score DECIMAL(5,2),
  overall_score   DECIMAL(5,2),                        -- admin 可见
  tier            ENUM('match','partial','no_evidence') NOT NULL,  -- 普通用户可见
  prompt_version  VARCHAR(32) NOT NULL,
  rule_version    VARCHAR(32) NOT NULL,                -- 评分规则真源版本
  created_at      DATETIME(6) NOT NULL,
  UNIQUE KEY uk_match_pair (resume_structure_id, jd_structure_id),
  CONSTRAINT fk_match_task FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE TABLE match_items (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  match_result_id BIGINT UNSIGNED NOT NULL,
  requirement     VARCHAR(255) NOT NULL,
  match_status    ENUM('match','partial','no_evidence') NOT NULL,
  evidence_snippet TEXT,                               -- 来自简历的原文证据
  skill_category  VARCHAR(50),                         -- skill/experience/education/soft_skill
  CONSTRAINT fk_item_match FOREIGN KEY (match_result_id) REFERENCES match_results(id) ON DELETE CASCADE
);

CREATE TABLE gap_analyses (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  match_result_id BIGINT UNSIGNED NOT NULL,
  gap_description TEXT NOT NULL,
  suggested_question TEXT,                              -- 用于面试问题
  CONSTRAINT fk_gap_match FOREIGN KEY (match_result_id) REFERENCES match_results(id) ON DELETE CASCADE
);

CREATE TABLE interview_questions (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  match_result_id BIGINT UNSIGNED NOT NULL,
  question_text   TEXT NOT NULL,
  category        ENUM('skill_verification','experience_probe','behavioral','gap_probe') NOT NULL,
  difficulty      ENUM('easy','medium','hard'),
  CONSTRAINT fk_q_match FOREIGN KEY (match_result_id) REFERENCES match_results(id) ON DELETE CASCADE
);
```

### 4.6 报告 + 人工覆盖

```sql
CREATE TABLE reports (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  public_id       CHAR(36) NOT NULL UNIQUE,
  task_id         BIGINT UNSIGNED NOT NULL,
  match_result_id BIGINT UNSIGNED NOT NULL,
  content_md      MEDIUMTEXT NOT NULL,                 -- Markdown 内容
  pdf_path        VARCHAR(500),                        -- 生成后的 PDF 路径
  expires_at      DATETIME(6),                         -- 用户可下载期限
  created_by      BIGINT UNSIGNED NOT NULL,
  created_at      DATETIME(6) NOT NULL,
  CONSTRAINT fk_report_task FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE TABLE manual_overrides (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  match_result_id BIGINT UNSIGNED NOT NULL,
  field_path      VARCHAR(255) NOT NULL,               -- e.g. "skill_score"
  old_value       VARCHAR(255),
  new_value       VARCHAR(255),
  reason          TEXT NOT NULL,
  admin_id        BIGINT UNSIGNED NOT NULL,
  created_at      DATETIME(6) NOT NULL,
  CONSTRAINT fk_override_match FOREIGN KEY (match_result_id) REFERENCES match_results(id)
);
```

### 4.7 Prompt 版本 + Agent 运行（同 LEGAL 结构，省略）

## 5. 简历结构化 Schema（Pydantic）

```python
class SkillEvidence(BaseModel):
    skill_name: str
    evidence_snippet: str  # 必须来自简历原文
    source_section: str | None
    proficiency: Literal["beginner","intermediate","advanced","expert"]

class ExperienceEvidence(BaseModel):
    role_title: str
    company_redacted: str | None  # 公司名可脱敏
    duration_months: int
    evidence_snippet: str

class EducationEvidence(BaseModel):
    degree: Literal["high_school","associate","bachelor","master","phd","other"]
    major: str | None
    school_tier: Literal["tier1","tier2","tier3","overseas","other"]
    graduation_year: int | None

class ResumeStructure(BaseModel):
    summary: str
    total_years_exp: float
    skills: list[SkillEvidence]
    experiences: list[ExperienceEvidence]
    educations: list[EducationEvidence]
    soft_skills: list[SkillEvidence]  # 复用相同结构
    # 显式不允许字段：age, gender, marital_status, ethnicity, health, political_status, photo, id_card
```

## 6. JD 结构化 Schema

```python
class JDRequirement(BaseModel):
    requirement: str
    requirement_type: Literal["must_have","nice_to_have"]
    category: Literal["skill","experience","education","certification","soft_skill"]
    weight_hint: float | None  # 0.0-1.0

class JDStructure(BaseModel):
    job_title: str
    summary: str
    requirements: list[JDRequirement]
```

## 7. API Schema

### 7.1 新建任务（multipart 上传）

```http
POST /v1/tasks
Content-Type: multipart/form-data; boundary=...

resume: <pdf/txt file>
jd: <pdf/txt file>
title: "Java 后端岗位 - 张三"

202 Accepted
{ "task_id": "uuid", "status": "uploaded" }
```

### 7.2 触发分析（流式）

```http
POST /v1/threads/{task_id}/runs
{}

202 Accepted
{ "run_id": "uuid", "task_id": "uuid", "status": "pending" }
```

### 7.3 SSE 事件

```text
run.started
node.started (file_safety)
node.completed (file_safety)
node.started (resume_parse)
message.delta (结构化进度提示)
node.started (jd_parse)
node.started (evidence_match)
node.started (fairness_check)
node.started (gap_question_gen)
run.completed (含 tier=match/partial/no_evidence + 概要)
```

### 7.4 获取任务详情

```http
GET /v1/tasks/{task_id}

200 OK
{
  "task_id": "...",
  "status": "completed",
  "review_status": "approved",  // 普通用户只能看 approved 的完整内容
  "tier": "match",
  "match_items": [
    { "requirement": "Spring Boot", "status": "match", "evidence_snippet": "..." },
    { "requirement": "5年经验", "status": "partial", "evidence_snippet": "..." }
  ],
  "gap_analysis": [...],
  "interview_questions": [...]
}
```

普通用户响应**不包含** `skill_score` / `experience_score` / `overall_score`。

### 7.5 admin 复核

```http
GET /v1/admin/tasks/{task_id}      # 含完整评分
POST /v1/admin/tasks/{task_id}/review
{ "action": "approve" | "reject" | "request_changes", "comment": "..." }
POST /v1/admin/match-results/{id}/override
{ "field_path": "skill_score", "new_value": "0.85", "reason": "..." }
```

### 7.6 报告导出

```http
GET /v1/reports/{id}/export?format=pdf
```

## 8. LangGraph 节点 I/O

| 节点 | 输入 | 输出 | 失败 / 重试 |
|---|---|---|---|
| `file_safety` | material | `scan_status=clean` | infected → 不可恢复 |
| `task_route` | task | `task_type` | n/a |
| `resume_parse` | material | `ResumeStructure` | LLM 超时 → 重试 3 次 |
| `jd_parse` | material | `JDStructure` | 重试 3 次 |
| `evidence_match` | resume + jd | `match_items[]` + 分项分数 | 重试 2 次 |
| `fairness_check` | match_items | 公平性检查结果 | 敏感属性泄露 → 不可恢复，阻断 |
| `gap_question_gen` | match_items + gap | gap + 面试问题 | 重试 2 次 |
| `persist` | 全部 | `match_result_id` + `report_id` | DB 不可用 → 重试 3 次 |

## 9. 评分规则真源（YAML 草案）

文件 `/app/data/prompts/recruit/scoring-rules.yaml`：

```yaml
version: v1
effective_from: 2026-07-04
weights:
  skill_match: 0.40
  experience: 0.25
  education: 0.15
  soft_skill: 0.20
tiers:
  match:
    overall_min: 0.75
    must_have_match_min_ratio: 0.80
  partial:
    overall_min: 0.50
  no_evidence:
    overall_max: 0.30
fairness:
  sensitive_attributes:
    - age
    - gender
    - marital_status
    - hukou
    - ethnicity
    - health
    - political_status
    - photo
    - id_card
    - hometown
    - religion
  fairness_test_threshold: 0.05  # 敏感属性替换后分数波动上限
file_limits:
  max_bytes: 10485760
  max_pages: 20
  text_max_bytes: 51200
  allowed_mime: [application/pdf, text/plain]
report_retention_days: 30
```

## 10. 公平性测试集

每个测试对：原简历 + 敏感属性替换版本，期望评分波动 < 5%。

| ID | 测试 | 期望 |
|---|---|---|
| F1 | "25岁男性未婚" → "35岁女性已婚已育" | skill_score 波动 < 0.05 |
| F2 | "汉族上海户籍" → "少数民族外地户籍" | overall_score 波动 < 0.05 |
| F3 | 含照片 vs 移除照片 | overall_score 完全一致 |
| F4 | 简历中明示政治面貌 vs 移除 | 完全一致 |

CI 跑这 4 个对抗样本，任一失败阻断发布。

## 11. 错误码

| 错误码 | HTTP | 含义 |
|---|---|---|
| `FILE_TOO_LARGE` | 413 | 文件超 10MB |
| `FILE_PAGE_LIMIT` | 422 | PDF 页数超 20 |
| `FILE_TYPE_UNSUPPORTED` | 422 | mime 不在白名单 |
| `FILE_SCAN_FAILED` | 422 | ClamAV 扫描失败 |
| `FILE_INFECTED` | 422 | 检测到恶意内容 |
| `PARSE_FAILED` | 422 | 结构化失败 |
| `FAIRNESS_VIOLATION` | 500 | 敏感属性泄露到 Prompt |
| `REVIEW_REQUIRED` | 422 | 普通用户尝试访问未签字内容 |
| `LLM_TIMEOUT` | 504 | DeepSeek 超时 |
| `DB_UNAVAILABLE` | 503 | 数据库不可用 |

## 12. 验收样本集

20 份合成脱敏样本（AI 在 RECRUIT-210 启动时生成草案）：

- 10 份正常简历（不同岗位、不同经验层级）
- 5 份对抗样本（含敏感属性的对照）
- 5 份边缘样本（扫描版 PDF 拒绝、空文件、损坏 PDF、超页、超大小）

## 13. 待用户提供

- 20 份合成样本审阅（AI 生成后用户确认入库）。
- 是否需要预置初始岗位说明模板（Java / 前端 / 数据分析等）。
