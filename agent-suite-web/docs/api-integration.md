# 前端 API 集成约定

## 调用模式

- 普通 CRUD：JSON HTTP。
- Agent 运行：先创建 run，再订阅 SSE。
- 停止和重试：使用显式 run 操作接口。
- 大文件：使用 multipart，字段名以服务 OpenAPI 为准。

## 错误映射

前端按稳定 `error.code` 映射用户提示，不解析后端自然语言栈信息。未知错误展示 `request_id`，便于排查。

## 契约生成

详细实现阶段从三个 Agent OpenAPI 生成或校验 TypeScript 类型。生成文件不得手改，生成命令必须记录。

当前文档不固定具体生成工具，待 `FOUND-010` 详细设计确认。

