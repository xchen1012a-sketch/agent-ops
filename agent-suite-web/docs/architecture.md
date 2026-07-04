# 前端架构

## 分层

```text
app shell
  -> router
  -> module views
      -> module components
      -> module store
      -> module API client
  -> shared presentation components
  -> infrastructure (HTTP/SSE/auth/config)
```

三个业务模块各自维护页面、组件、状态和 API client。共享层只包含无业务语义的展示组件和基础设施，不允许建立万能 store 或万能 service。

## API 路由

- `/api/legal/v1/*`
- `/api/recruitment/v1/*`
- `/api/data/v1/*`

开发代理和生产反向代理使用相同路径前缀，前端不硬编码服务容器地址。

## 状态原则

- 服务端会话与运行状态以 API 为真源。
- 前端只缓存展示状态和未提交输入。
- 每个运行以 `run_id` 关联 SSE、停止、重试和详情。
- 页面刷新后通过 API 恢复会话，不依赖内存状态伪造完成结果。

## 安全

- Token 传输、刷新和退出策略在详细设计阶段确认。
- Markdown 必须经过安全渲染，禁止直接注入 HTML。
- 文件上传必须在客户端做基础类型/大小提示，但服务端仍是最终校验边界。

