# feishu-to-dify

飞书 **企业自建应用机器人** 与 **Dify 工作流** 的对接中间层，基于 Python FastAPI 实现。

用户通过飞书单聊或群聊 @ 机器人提问，本服务将消息转发至 Dify 工作流（SSE 流式），并通过飞书 **CardKit 流式卡片** 实时展示回复。

> 本项目对接的是可双向收发的 **应用机器人**，不是「自定义 Webhook 机器人」（仅单向推送、无法接收用户消息）。

## 功能

- 飞书 **长连接** 收消息（默认，无需公网 URL）
- Dify 工作流 `response_mode=streaming` 转发
- CardKit 卡片流式更新（打字机效果）
- 消息去重、错误处理、`/health` 健康检查

## 文档

| 文档 | 说明 |
|------|------|
| **[完整使用指南](docs/使用指南.md)** | 从零部署：飞书后台、Dify、本地运行、联调、排错 |
| [需求文档](docs/需求文档.md) | 架构与接口设计说明 |

## 快速开始

```bash
git clone <your-repo-url>
cd feishu-to-dify

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env   # macOS / Linux
```

编辑 `.env`，填入飞书 App ID/Secret 与 Dify API Key，然后：

```bash
python -m app.main
```

访问 `http://localhost:8000/health`，应返回 `{"status":"ok","feishu_mode":"websocket"}`。

详细步骤见 **[docs/使用指南.md](docs/使用指南.md)**。

## 环境变量（摘要）

| 变量 | 必填 | 说明 |
|------|------|------|
| `FEISHU_APP_ID` | 是 | 飞书自建应用 App ID |
| `FEISHU_APP_SECRET` | 是 | 飞书自建应用 App Secret |
| `DIFY_API_KEY` | 是 | Dify 工作流应用 API Key |
| `DIFY_API_BASE` | 否 | 默认 `http://localhost/v1` |
| `DIFY_INPUT_KEY` | 否 | 工作流输入变量名，默认 `query` |

完整说明见 [使用指南 · 配置说明](docs/使用指南.md#6-配置说明)。

## 项目结构

```
app/
├── main.py                 # FastAPI 入口 + 长连接 lifespan
├── config.py               # 环境变量
├── services/
│   ├── bridge.py           # 消息编排
│   ├── dify_client.py      # Dify SSE 客户端
│   ├── feishu_api.py       # 飞书 Open API
│   ├── feishu_card.py      # CardKit 流式卡片
│   ├── feishu_message.py   # 消息解析
│   └── feishu_ws_runner.py # lark-oapi 长连接
└── utils/
```

## 测试

```bash
pytest
```

## 安全说明

- **切勿** 将 `.env`、真实 App Secret、Dify API Key 提交到 GitHub。
- 仓库仅保留 [`.env.example`](.env.example) 作为模板（占位符，无真实密钥）。
- 若密钥曾泄露，请在飞书后台重置 App Secret，并在 Dify 中轮换 API Key。

## 参考

- [飞书长连接接收事件](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/event-subscription-guide/long-connection-mode)
- [CardKit 流式更新](https://open.feishu.cn/document/cardkit-v1/streaming-updates-openapi-overview)
- [Dify 工作流 API](https://docs.dify.ai/)

## License

MIT（可按需修改）
