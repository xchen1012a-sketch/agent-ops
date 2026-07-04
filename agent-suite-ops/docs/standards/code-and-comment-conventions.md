# 代码与注释规范

## 1. 通用原则

- 标识符、API、数据库和文件名使用英文；业务解释和注释使用简洁中文，可保留必要英文术语。
- 命名表达业务含义，不使用拼音、无意义缩写、`data1`、`handleStuff`、`common2` 等名称。
- 函数和类保持单一职责；超过约50行函数或复杂分支必须说明并优先拆分。
- 禁止复制粘贴业务逻辑、注释掉的旧代码、调试输出和无期限临时开关。
- 类型优先于注释：能由类型、Schema、名称表达的内容不重复写注释。

## 2. Python规范

- Python使用snake_case；类/异常使用PascalCase；常量使用UPPER_SNAKE_CASE。
- 全量类型标注；边界使用Pydantic，领域内部不滥用dict/Any。
- import按标准库、第三方、本项目分组；禁止星号导入。
- 异步链路不得调用阻塞I/O；第三方client封装在adapter。
- 异常使用语义化类型和稳定错误码；禁止裸 `except` 和吞异常。
- router薄、use case定义事务、repository只访问数据库、node只处理节点职责。

## 3. Docstring规范

采用Google-style语义，以下对象必须写docstring：

- 对外模块、公开类、公开函数/方法。
- LangGraph节点、工具、adapter和复杂领域策略。
- 有重要副作用、幂等、事务或安全约束的内部函数。

Docstring写“用途、边界、参数、返回、异常和副作用”，不复述函数名。简单私有函数若名称和类型已清楚，可不写。

示例格式：

```text
"""校验并执行只读查询。

Args:
    candidate: 已通过结构化Schema校验的SQL候选。
    context: 包含用户、会话和超时配置的执行上下文。

Returns:
    经过行数和字段限制的查询结果。

Raises:
    SqlPolicyViolation: SQL不符合白名单策略。
    QueryTimeoutError: 查询超过配置时限。

Security:
    仅使用shop_db只读账号；调用方不得绕过AST校验。
"""
```

## 4. 行内注释

应注释：为什么这样做、业务不变量、安全边界、并发/幂等原因、框架陷阱和临时兼容原因。

不应注释：代码逐行翻译、显而易见赋值、已过期设计、个人讨论或大段需求原文。

TODO格式：`TODO(ISSUE-ID): 具体动作与移除条件`。没有关联事项和移除条件的TODO不得进入主分支。

## 5. LangGraph注释

- graph装配处说明节点顺序、条件边和中断/恢复点。
- node docstring说明读取/写入的State字段、失败类别、重试和幂等语义。
- Prompt文件头记录名称、版本、输入变量、输出Schema和变更原因。
- 禁止在注释中粘贴真实Prompt输入、用户数据或模型密钥。

## 6. SQL与迁移注释

- 迁移说明业务原因、锁表/回填风险和回滚前提。
- 复杂查询说明数据粒度、指标口径和去重依据。
- 禁止用注释掩盖错误字段或保留失效SQL。

## 7. Vue与TypeScript规范

- 组件PascalCase；composable使用`useXxx`；变量/函数camelCase。
- 使用Composition API和`<script setup lang="ts">`。
- Props/Emits显式类型；禁止组件直接猜测API字段。
- 组件注释说明非直观交互、可访问性、性能或SSE状态原因，不描述模板表面结构。
- 业务页面、store、API client和展示组件分离。

## 8. 自动门禁

- Python：Ruff格式/规则、MyPy、Pytest、docstring规则和安全扫描。
- Vue：ESLint、Prettier、vue-tsc、Vitest和关键Playwright E2E。
- 注释与文档必须随行为变化更新；失真注释视为缺陷。

