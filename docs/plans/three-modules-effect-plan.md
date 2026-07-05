# 三 Agent 模块效果落地计划

> 目标:让法律 / 招聘 / 问数三个 Agent 在**现有架构**下跑出真实效果(真 LLM 回答、真数据查询、真匹配分析),达到作业可演示水平。**不改架构**,只补齐"配置中心 ↔ adapter ↔ 真实外部服务"这条断链。
>
> 状态:**计划/待执行**。本文据 `docs/homework/` 作业要求 + 项目真实代码核查编写。

---

## 1. 现状盘点(只读核查证据)

### 1.1 已就绪

| 项 | 证据 |
|---|---|
| 前端三模块页面 + 招聘接线 | `agent-suite-web/src/views/{legal,recruitment,data}/*` |
| 前端 API 配置中心 UI | `views/admin/ApiConfigAdminPage.vue`(list/update 三域 key) |
| 三域 admin_api_config 端点 | 法律/数据/招聘均有 `api/v1/endpoints/admin_api_config.py`,支持 `deepseek/embedding/...` 等 api_type |
| 配置加密存储 + 遮挡显示 | `AgentApiConfigCryptoDep` + `api_key_hint` |
| 认证服务 | `agents/auth-service`(8/8 smoke 通过) |
| 数据字典 / SQL 安全(sqlglot) / query execution adapter | `current.md` DATA-300 完成 |
| shop_db 真实业务数据 | `docs/homework/AI编程_智能问数实训(课件)/shop_db_export.sql`(12 表,含 2 大宽表) |
| NL2SQL prompt 模板 | 课件 `06_智能问数/Dify_SQL语句封装_SYSTEM提示词_*.md` |

### 1.2 核心断点 🎯

**配置中心存了 key(DB),但 LLM/DB adapter 不读 config repo**——三域 adapter 各自为政:

| 域 | LLM adapter 实现 | key 读取方式 | 问题 |
|---|---|---|---|
| 法律 | ❌ **`infrastructure/llm/` 空目录**(仅 `__init__.py`) | — | 连 adapter 都没写 |
| 招聘 | ❌ **`infrastructure/llm/__init__.py` 仅 docstring** | — | 连 adapter 都没写;`start_run` 全 mock |
| 问数 | ✅ `deepseek_adapter.py` 已写 | 从 `settings.deepseek_api_key`(env)读,**不读 config repo** | 配置中心 key 不生效;`fake_llm_adapter` + `fake_query_adapter` 兜底 |

**这就是"接不接通还没验证"的根因——代码层面就没接通。**

---

## 2. 三域差距与动作

### 2.1 法律咨询 Agent

| 缺口 | 动作 | 文件 |
|---|---|---|
| 无 DeepSeek adapter | 写真 adapter(HTTP 调 DeepSeek chat completions,流式) | 新增 `infrastructure/llm/deepseek_adapter.py` |
| adapter 不读 config repo | adapter 从 `AgentApiConfigRepo` 读 key/base_url/model(运行时注入,非 env) | `application/services/` 装配处 |
| RAG 知识库空 | 写 ingest 脚本,把法律文档切块 → BGE-M3 embedding → 入 qdrant | 新增 `scripts/ingest_knowledge.py` |
| 检索链路 | workflow 接真 qdrant 检索(若 `legal_nodes.py` 已接,补数据) | `workflows/legal_nodes.py` |
| 高风险复核等业务流 | 现有,无需动 | — |

**阻塞项**:法律知识库文档(劳动法/合同法/民法典等)、qdrant 部署、BGE-M3 模型下载。

### 2.2 智能招聘 Agent

| 缺口 | 动作 | 文件 |
|---|---|---|
| LLM adapter 空壳 | 写 DeepSeek adapter(同法律) | 新增 `infrastructure/llm/deepseek_adapter.py` |
| `start_run` 全 mock | 接真 langgraph workflow:简历解析 → JD 解析 → 证据匹配 → 公平性 → 面试问题生成 | `application/services/recruit_task_api_service.py:300-325` |
| Prompt 模板 | 定义 resume_parse/jd_parse/evidence_match/gap_question 的 prompt 版本 | `domain/prompts/` 或 config |
| adapter 读 config repo | 同法律 | 装配处 |

**阻塞项**:DeepSeek key(配置中心填)。

### 2.3 智能问数 Agent

| 缺口 | 动作 | 文件 |
|---|---|---|
| adapter 读 env 不读 config repo | 改 `deepseek_adapter` 从 `AgentApiConfigRepo` 读 key | `infrastructure/llm/deepseek_adapter.py:67-72` |
| fake → 真 adapter 切换 | 默认走真 adapter,fake 仅作 fallback(环境变量 `USE_FAKE_LLM=true` 时启用) | `application/` 装配处 + `infrastructure/db/fake_query_adapter.py` |
| MySQL shop_db 未导入 | 起 MySQL 8.0,导入 `shop_db_export.sql` | 外部 |
| NL2SQL prompt 对齐课件 | 把课件 `Dify_SQL语句封装_SYSTEM提示词_宽表版.md`(Schema 注入 + Few-Shot + 错误自修正)迁到项目 prompt 模板 | `domain/prompts/` 或 `application/prompts/` |
| 数据字典对齐 shop_db | 把 shop_db 12 张表元数据写入数据字典(若现有字典为空或样例) | 数据字典表/种子 |
| MCP ↔ sqlglot 已替代 | 现有 sqlglot 做安全,无需 MCP server | — |
| 飞书集成 | 现有 `feishu_events` 端点 + fake,接通时配真飞书 app | `infrastructure/feishu/` |

**阻塞项**:DeepSeek key、MySQL 实例。

---

## 3. 推进顺序(分阶段,每阶段可独立验证)

### 阶段 0:配置中心接通(三域共享,前置)
- 写一个共享的"adapter 配置加载器":从 `AgentApiConfigRepo` 读 key/base_url/model,缓存,变更后失效
- 三域 adapter 统一走这个加载器,不再各自读 env
- **验证**:配置中心 UI 改 key → adapter 行为变(单测覆盖)

### 阶段 1:问数真问答(最有演示价值)
- MySQL 起 + 导入 shop_db
- NL2SQL prompt 迁移
- 数据字典对齐 shop_db
- fake → 真 adapter 切换(留 fallback)
- **验证**:浏览器问"上月销售额最高的 5 个品类" → 真实 SQL + 真实结果

### 阶段 2:招聘真匹配
- 写 DeepSeek adapter(招聘专用或共享)
- 接真 langgraph workflow 替换 mock `start_run`
- **验证**:贴简历+JD → 真实匹配证据 + 面试问题

### 阶段 3:法律真问答 + RAG
- 写 DeepSeek adapter
- 法律文档入库 qdrant
- 接真检索链路
- **验证**:问"拖欠工资怎么办" → 带法律条文引用的回答

### 阶段 4:端到端 + 报告产出
- 三域全跑通,截图取证
- 配实训报告(对照 `实训报告大纲.html`)

---

## 4. 阻塞项清单(用户需提供)

| # | 项 | 影响域 | 何时需要 |
|---|---|---|---|
| 1 | DeepSeek API key | 三域 | 阶段 0 后 |
| 2 | MySQL 8.0 实例 | 问数 | 阶段 1 |
| 3 | qdrant 部署 | 法律 | 阶段 3 |
| 4 | BGE-M3 embedding 模型 | 法律 | 阶段 3 |
| 5 | 法律知识库文档(劳动法/合同法/民法典等) | 法律 | 阶段 3 |

---

## 5. 工作量估计(纯代码层,不含外部准备)

| 阶段 | 内容 | 估时 |
|---|---|---|
| 0 | 配置加载器 + 三域 adapter 接通 | 2-3h |
| 1 | 问数真问答(prompt 迁移 + fake→真 + 字典对齐) | 2-3h |
| 2 | 招聘真匹配(adapter + workflow) | 3-4h |
| 3 | 法律真问答 + RAG(adapter + ingest + 检索) | 4-6h |
| 4 | 端到端 + 截图 | 1-2h |
| **合计** | | **12-18h**(2-3 个工作日) |

---

## 6. 可立即独立做的(不依赖外部)

- 阶段 0 配置加载器(adapter 接通)
- 阶段 1 prompt 迁移 + 数据字典对齐 shop_db(代码层)
- 阶段 1 fake→真 adapter 切换开关(代码层)
- 阶段 2 招聘 adapter + workflow(代码层,DeepSeek 到了就能跑)
- 阶段 3 法律 adapter + ingest 脚本(脚本能先写,入库等文档)

外部准备期间可并行推进以上,环境齐了直接联调。

---

## 7. 风险与回滚

- **风险 A**:adapter 接通后单测覆盖不足,改 key 行为不生效。**对策**:加"配置加载器"单测 + 集成测试(改 key → adapter 调用变化)。
- **风险 B**:问数 fake→真 切换后,真 SQL 准确率低。**对策**:留 `USE_FAKE_LLM` 开关,演示时可回退。
- **风险 C**:法律 RAG 入库慢/模型下载慢。**对策**:ingest 脚本支持增量 + 小文档先跑通。
- **回滚**:每阶段独立 commit,失败则 `git revert` 该阶段,不影响其它。

---

## 8. 待执行时确认的细节

- 法律 `workflows/legal_nodes.py` 是否已写 DeepSeek 调用框架(只差 adapter),还是连调用层都待补
- 数据域 fake/真 adapter 的切换开关现状(grep 未命中,可能用 env 或未实现)
- 招聘 prompt 版本管理是否已有 `domain/prompts/` 目录
- 三域 admin_api_config 的 `extra` 字段是否够装 DeepSeek 的 `temperature`/`max_tokens` 等

执行阶段 0 时逐一确认。
