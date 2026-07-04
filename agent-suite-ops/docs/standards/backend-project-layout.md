# 企业级 FastAPI + LangGraph 后端骨架标准

## 1. 适用范围

本标准适用于三个独立 Agent 后端仓库。三个仓库使用相同分层规则，但不共享业务运行库、不互相 import。

## 2. 推荐仓库结构

以 `legal-consulting-agent` 为例，另外两个仓库只替换 Python 包名和领域模块：

```text
legal-consulting-agent/
├─ src/
│  └─ legal_consulting_agent/
│     ├─ main.py                    # 仅创建应用和组装依赖
│     ├─ api/
│     │  ├─ dependencies.py         # FastAPI依赖注入
│     │  ├─ error_handlers.py       # HTTP错误映射
│     │  └─ v1/
│     │     ├─ router.py
│     │     ├─ endpoints/           # 薄路由
│     │     └─ schemas/             # 请求/响应DTO
│     ├─ application/
│     │  ├─ commands/               # 改变状态的用例
│     │  ├─ queries/                # 只读用例
│     │  └─ services/               # 跨节点业务编排
│     ├─ domain/
│     │  ├─ entities/
│     │  ├─ value_objects/
│     │  ├─ policies/
│     │  └─ ports/                  # repository/gateway抽象
│     ├─ workflows/
│     │  ├─ graph.py                # 图装配
│     │  ├─ factory.py              # 唯一图构建入口，保留可选harness
│     │  ├─ state.py                # 显式状态Schema
│     │  ├─ routing.py              # 条件边
│     │  └─ nodes/                  # 单职责节点
│     ├─ prompts/
│     │  └─ <prompt-name>/v1/       # 模板、变量、输出Schema
│     ├─ infrastructure/
│     │  ├─ db/
│     │  │  ├─ base.py
│     │  │  ├─ session.py
│     │  │  ├─ models/
│     │  │  └─ repositories/
│     │  ├─ llm/                    # DeepSeek adapter
│     │  └─ integrations/           # MCP/飞书/检索/文件等
│     └─ core/
│        ├─ config.py               # Pydantic Settings唯一入口
│        ├─ security.py
│        ├─ errors.py
│        ├─ logging.py
│        └─ request_context.py
├─ migrations/                      # Alembic版本脚本
├─ tests/
│  ├─ unit/
│  ├─ integration/
│  ├─ contract/
│  ├─ evaluation/                   # Agent轨迹与质量评测
│  └─ e2e/
├─ scripts/                          # 可复现维护命令，不放业务逻辑
├─ docs/
├─ pyproject.toml
├─ alembic.ini
├─ .env.example
├─ Dockerfile
└─ README.md
```

该目录只在 `FOUND-010` 阶段创建；当前 DESIGN-002 仅确认标准。

## 3. 依赖方向

```text
api -> application -> domain
api -> workflows -> application/domain
infrastructure -> domain ports
composition root(main/dependencies) -> infrastructure implementations
```

- `domain` 不依赖 FastAPI、SQLAlchemy、LangGraph 或供应商 SDK。
- `api` 不直接访问 ORM、SQL、DeepSeek、MCP 或文件系统。
- `workflows/nodes` 不创建数据库会话，不直接读取环境变量。
- `infrastructure` 不返回第三方原始对象到 application/api。
- 事务边界由 application use case 控制，repository 不擅自提交。

## 4. FastAPI规范

- 大型应用使用 `APIRouter` 分文件组织，统一在版本 router 注册。
- 请求、响应、内部领域对象和 ORM Model 分离。
- `health/live` 只检查进程；`health/ready` 检查必要依赖。
- 列表接口必须定义分页、排序、筛选和最大页大小。
- 统一错误 envelope；500 不暴露栈、SQL、Prompt或内部路径。
- 使用依赖注入提供 Settings、身份、数据库会话和 use case。
- 长时 Agent 运行使用 run 资源和 SSE，不占用同步请求等待完整流程。

## 5. LangGraph规范

- 每个 graph 只有一个装配入口，节点与条件边可独立测试。
- 默认factory构建自定义LangGraph；只有模块ADR和评测通过后才允许factory改用Deep Agents，不影响API/领域契约。
- State 使用显式 TypedDict/Pydantic/dataclass Schema，禁止任意 dict 漂移。
- 每个 node 定义输入字段、输出字段、失败类型、重试和幂等语义。
- `thread_id`、checkpoint、run状态和业务会话的映射必须文档化。
- Checkpoint 只保存恢复所需状态，不保存秘密、大文件或完整数据库结果。
- 工具/模型输出先校验为内部 DTO，再进入下一节点。
- 不为“未来可能使用Deep Agents”预建空adapter、双实现或额外依赖；扩展点只保留在factory和稳定契约。

## 6. 配置与生命周期

- Pydantic Settings 是配置唯一入口；禁止模块级散落 `os.getenv`。
- Engine/sessionmaker、HTTP client和模型 client在应用生命周期中集中创建/关闭。
- SQLAlchemy Session/AsyncSession 每请求或每后台任务独立，不跨并发任务共享。
- 关键配置缺失时启动失败；不得回退到不安全默认值。

## 7. 官方依据

- FastAPI Bigger Applications: https://fastapi.tiangolo.com/tutorial/bigger-applications/
- FastAPI Settings: https://fastapi.tiangolo.com/advanced/settings/
- LangGraph Application Structure: https://docs.langchain.com/oss/python/langgraph/application-structure
- LangGraph Persistence: https://docs.langchain.com/oss/python/langgraph/persistence
- SQLAlchemy Session Basics: https://docs.sqlalchemy.org/en/20/orm/session_basics.html
- Alembic Tutorial: https://alembic.sqlalchemy.org/en/latest/tutorial.html
