# 当前阶段

- 阶段：`FOUND-010`
- 名称：企业级工程基础
- 状态：✅ **工程基线全部完成，等待用户授权进入 LEGAL-100**
- 阶段文件：`docs/plans/phases/FOUND-010-enterprise-foundation.md`（含完整验证证据 section）
- 已完成的设计产出（DESIGN-002）：
  - 5 项关键决策（ADR-0007~0012）
  - 4 个模块 specification.md 同步更新
  - 5 份模块详细设计：
    - `agent-suite-ops/docs/runbooks/deployment-design.md`（OPS-610）
    - `agent-suite-web/docs/detailed-design.md`（WEB-410）
    - `agents/legal-consulting-agent/docs/detailed-design.md`（LEGAL-110）
    - `agents/recruitment-assistant-agent/docs/detailed-design.md`（RECRUIT-210）
    - `agents/data-query-agent/docs/detailed-design.md`（DATA-310）
- 已完成的工程基线（FOUND-010）：
  1. ✅ 兼容版本矩阵和许可证检查（pyproject.toml / package.json 锁版本）
  2. ✅ 三个后端同构骨架（FastAPI + LangGraph factory + Settings + live/ready）
  3. ✅ 前端应用壳（Vite + Vue 3 + Element Plus + Pinia + Vue Router + SSE 客户端 + 安全 Markdown）
  4. ✅ 迁移基线（Alembic init + 空 schema + 单一 head + 离线 upgrade/downgrade 校验）
  5. ✅ Docker 和健康检查（4 个镜像均非 root UID 1001 + tini PID 1 + HEALTHCHECK）
  6. ✅ 工程门禁证据（详见阶段文件「验证证据」section，2026-07-05）
- 已知技术债（不阻塞 LEGAL-100 启动）：
  - 后端 3 类依赖漏洞（asyncmy / chromadb / ecdsa）— 见各仓库 README
  - 前端 6 个依赖漏洞（vite / vitest / esbuild / echarts）— major 升级纳入 WEB-400
  - Playwright E2E、Lighthouse 视觉回归 — 纳入 WEB-400
- 代码状态：工程基线就绪，可启动业务实现（LEG-100/RECRUIT-200/DATA-300）
- Git 状态：所有改动停留在工作区，未提交（按规范等待用户授权）
- 仍待用户提供的输入（业务阶段启动前需提供）：
  - 课件法律知识库样本（用于 LEGAL-120）
  - 是否认可 20 份合成脱敏样本作为招聘验收基线（用于 RECRUIT-210）
  - 是否需要预置的初始岗位说明模板
- 下一步候选：
  - **方案 A**：用户授权 Git 提交 FOUND-010 工作区改动
  - **方案 B**：用户授权进入 LEGAL-100（法律咨询 Agent 业务实现）
  - **方案 C**：用户授权进入 RECRUIT-200 或 DATA-300
