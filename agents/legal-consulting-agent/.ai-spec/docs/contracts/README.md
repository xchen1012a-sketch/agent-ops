# contracts

这里存放 API、DTO、事件、数据库、外部服务契约。

## 更新规则

- 只有 L3/L4 任务或契约变化时更新。
- 前端不得从后端临时代码里猜字段。
- 后端 API 变更必须同步契约。
- 外部服务接入必须记录 mock 与真实服务边界。

## 建议文件

```text
docs/contracts/
├── api-baseline.md
├── openapi-policy.md
├── events.md
└── external-services.md
```
