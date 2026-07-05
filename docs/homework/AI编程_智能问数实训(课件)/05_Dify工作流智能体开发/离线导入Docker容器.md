# 🐳 Dify 1.15.0 离线部署包

> 📦 **适用场景**：无网络或网络慢的环境，无需下载镜像，直接导入即用。

---

## 📋 包含内容

| 文件 | 说明 |
|------|------|
| `一键导入镜像.bat` | Windows 一键导入所有镜像的批处理脚本 |
| `docker-compose.yaml` | Dify 官方 Docker Compose 编排文件（完整版） |
| `.env` | Dify 环境变量配置文件 |
| `*.tar` | 10 个 Docker 镜像离线包（合计 ~2.1GB 压缩） |

### 🖼️ 镜像清单

| 镜像 | 版本 | 用途 |
|------|------|------|
| `langgenius/dify-api` | 1.15.0 | Dify 核心 API + Worker + Beat |
| `langgenius/dify-web` | 1.15.0 | Dify Web 前端 |
| `langgenius/dify-plugin-daemon` | 0.6.3-local | 插件守护进程 |
| `langgenius/dify-sandbox` | 0.2.15 | 代码沙箱（安全执行） |
| `semitechnologies/weaviate` | 1.27.0 | 向量数据库 |
| `postgres` | 15-alpine | 关系型数据库 |
| `redis` | 6-alpine | 缓存 & 消息队列 |
| `nginx` | latest | 反向代理 |
| `ubuntu/squid` | latest | SSRF 防护代理 |
| `busybox` | latest | 权限初始化工具 |

---

## 🚀 快速开始（3 步）

### 第一步：导入镜像

**方式 A — 一键导入（推荐）**：
双击运行 `一键导入镜像.bat`，等待 5-10 分钟完成。

**方式 B — 手动逐条导入**：
```bash
docker load -i busybox_latest.tar
docker load -i redis_6-alpine.tar
docker load -i postgres_15-alpine.tar
docker load -i nginx_latest.tar
docker load -i weaviate_1.27.0.tar
docker load -i squid_latest.tar
docker load -i dify-sandbox_0.2.15.tar
docker load -i dify-web_1.15.0.tar
docker load -i dify-plugin-daemon_0.6.3-local.tar
docker load -i dify-api_1.15.0.tar
```

### 第二步：准备项目目录

```bash
# 1. 创建 Dify 项目目录
mkdir E:\dify
cd E:\dify

# 2. 复制 docker-compose.yaml 和 .env 到当前目录
copy "E:\大数据项目实训\相关软件\docker-compose.yaml" .
copy "E:\大数据项目实训\相关软件\.env" .
```

### 第三步：启动 Dify

```bash
docker compose up -d
```

启动后访问 **http://localhost** 进入 Dify 控制台。

---

## ⚙️ 环境配置说明

`.env` 文件中已预设好默认值，以下是**可能需要修改**的关键参数：

```ini
# 数据库密码（生产环境请修改）
DB_PASSWORD=difyai123456

# 管理员初始化密码（首次登录后即失效）
INIT_PASSWORD=

# 协同编辑模式（需要时开启 profiles: collaboration）
ENABLE_COLLABORATION_MODE=true

# 插件调试端口
EXPOSE_PLUGIN_DEBUGGING_PORT=5003
```

---

## 🔧 常用管理命令

```bash
# 查看运行状态
docker compose ps

# 查看日志
docker compose logs -f

# 停止服务
docker compose down

# 停止并删除数据（危险！）
docker compose down -v
```

---

## ⚠️ 注意事项

1. **端口占用**：默认占用 80 (HTTP)、443 (HTTPS)、5003 (插件调试)，启动前请确保端口未被占用
2. **存储空间**：首次启动会在 `./volumes/` 下创建持久化数据，建议预留 **10GB+** 空间
3. **Docker Desktop**：Windows 需要先安装 Docker Desktop（已包含在本目录：`Docker Desktop Installer.exe`）
4. **首次启动**：数据库初始化需要 1-2 分钟，请耐心等待
5. **向量数据库**：Weaviate 启动时需分配内存，建议 Docker 分配 **8GB+** 内存

---

## 🐛 常见问题

| 问题 | 解决方案 |
|------|----------|
| 端口被占用 | 修改 `.env` 中的端口映射，或停止占用端口的程序 |
| 导入后镜像不显示 | 用 `docker images` 检查，确保 `docker load` 无报错 |
| 启动后页面打不开 | 等待 2 分钟让数据库初始化完成，再看 `docker compose logs api` |
| Weaviate 启动失败 | Docker 设置中增加内存限制至 8GB+ |
| 插件服务报错 | 确认 5003 端口未被占用 |

---

> 💡 **提示**：如果要在多台学生机上部署，只需复制整个 `相关软件` 文件夹，每台机器运行一次 `一键导入镜像.bat` 即可。
