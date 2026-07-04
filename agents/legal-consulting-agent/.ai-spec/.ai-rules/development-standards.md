# 强制开发规范

## 1. 禁止硬编码

以下内容不得直接散落在业务代码、组件、路由、工作流节点、Prompt 或 SQL 字符串中：

- 密钥、Token、密码、证书和真实连接串。
- 服务地址、API 前缀、端口、模型名、超时、重试次数、并发数和限流阈值。
- 数据库名、租户信息、文件路径、对象存储桶和环境差异配置。
- 业务枚举、指标口径、权限矩阵、SQL 表/字段白名单和展示字典。
- Prompt 模板、系统指令、Few-Shot 示例和输出 Schema。
- 跨仓 API 响应字段猜测、错误码映射和协议常量。

正确归属：

- 敏感项：部署 Secret 或未跟踪的本地环境变量。
- 非敏感配置：类型化 Settings 和 .env.example。
- 业务规则：领域配置、数据库真源或版本化规则文件。
- Prompt：prompts/ 中按名称、版本、变量和输出 Schema 管理。
- API：OpenAPI/JSON Schema 真源和生成/校验后的客户端类型。
- SQL 安全策略：独立 policy 模块和版本化白名单，不依赖 Prompt。

允许的代码常量仅限真正稳定且无环境/业务差异的协议级常量，并须使用语义化名称集中管理。

## 2. 遵守开源框架规范

- FastAPI：使用依赖注入、Pydantic v2 Schema、清晰 router/service/repository 边界；路由不得直接堆业务和 SQL。
- LangGraph：显式状态 Schema、节点输入输出、条件边、checkpoint、重试和幂等语义；不得自行实现一套隐式工作流引擎。
- Deep Agents：仅作为LangGraph之上的可选harness；按模块需求和同一评测集决策，不提前安装、不维护双实现、不允许绕过工具/沙箱/SQL安全边界。
- SQLAlchemy 2：使用 2.x 风格、显式会话/事务边界；数据库变更只通过 Alembic 迁移。
- Vue 3：Composition API、TypeScript 和模块化组件；页面不得直接散落请求细节和复杂状态转换。
- Element Plus：遵循官方组件 API、主题和可访问性方式；不得修改依赖源码。
- DeepSeek/LangChain：通过官方集成或适配层调用；模型输出必须结构化校验，不能直接执行命令、SQL 或路径。

引入或升级依赖前必须核对官方文档、维护状态、许可证、版本兼容性和安全公告。禁止复制来源不明的代码或依赖废弃 API。

## 3. 模块与跨仓边界

- 三个 Agent 不互相 import、不互调私有接口、不共享业务数据库和业务运行库。
- 前端只依赖公开 OpenAPI/SSE 契约。
- 运维仓只负责编排、网关、环境模板和运维文档，不承载业务逻辑。
- 外部服务必须经 adapter 封装；核心逻辑可脱离真实 DeepSeek、MySQL 和飞书测试。
- 不创建万能 utils、common、manager 或跨域 service。

## 4. 配置与命名

- Python 使用 snake_case，Vue 组件使用 PascalCase，普通目录和配置使用 kebab-case。
- 同一概念全仓只使用一个名称；不使用拼音、无意义缩写或临时命名。
- .env.example 只包含占位值和说明，不包含真实秘密。
- 配置启动时完成类型、范围和必填校验；缺失关键配置必须快速失败。

## 5. 强制质量门禁

进入提交或阶段验收前至少满足：

- Python：Ruff、MyPy、Pytest、迁移检查和安全/依赖扫描。
- Vue：ESLint、Prettier、vue-tsc、单元测试、构建和关键 E2E。
- API：OpenAPI 契约检查、错误响应和 SSE 事件兼容性检查。
- Agent：节点状态、结构化输出、失败/重试/取消、幂等和轨迹评测。
- 数据库：迁移可升级/回滚、权限最小化、无真实生产数据。
- Docker：非 root、健康检查、最小镜像、固定可追踪版本和 Secret 外置。

未执行的验证必须明确写为“未验证”，不得写成通过。

## 6. 后端工程结构

- FastAPI 后端统一采用 src layout；应用包按 api、application、domain、workflows、prompts、infrastructure、core 分层。
- api 只处理协议/鉴权/DTO/错误映射；application 管理用例和事务；domain 不依赖框架；infrastructure 实现数据库与外部服务 adapter。
- LangGraph 的 graph、state、routing、nodes 分离；node 不直接读取环境变量或创建数据库会话。
- 每个Agent通过唯一graph factory构建编译图；默认自定义LangGraph，Deep Agents接入不得改变公开API和领域契约。
- ORM Model、API DTO、领域对象和工作流 State 必须分离并显式转换。
- 完整目录和数据库规范以 agent-suite-ops/docs/standards/ 为跨仓标准；独立仓实现时将适用规则同步到本仓文档。

## 7. 代码与注释

- 代码标识符、API、数据库和文件名使用英文；业务注释使用简洁中文并保留必要技术术语。
- 公共模块/类/函数、LangGraph节点、adapter和复杂策略使用Google-style语义docstring。
- 注释解释原因、业务不变量、安全、并发、幂等和框架陷阱，不逐行翻译代码。
- TODO必须使用 TODO(ISSUE-ID): 动作与移除条件；禁止提交无责任项的TODO、注释掉代码和调试输出。
- Python全量类型标注，禁止裸except、吞异常、星号导入和业务层Any/dict漂移。
- Vue使用Composition API和TypeScript；Props/Emits显式类型，页面不直接猜测API字段。

## 8. 开发顺序

- 先确认领域模型、数据库逻辑模型、OpenAPI/SSE和Agent State/节点契约。
- 后端基础与首个垂直切片先行；前端只在OpenAPI冻结后使用契约生成的Mock并行开发。
- 前端不得直接依赖数据库字段；每个功能按迁移、repository、use case、workflow、API、页面、契约/E2E的垂直切片完成。

## 9. 变更流程

1. 先对齐总体计划和模块真源规格。
2. 再确认当前阶段的范围、接口、数据和验收标准。
3. 仅实现 current 指向的阶段。
4. 发现计划外需求、API/DB/权限变化或框架冲突时停止并报告。
5. 验证通过后记录证据，用户确认后再推进下一阶段。
