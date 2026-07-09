# 🔧 环境准备与工具链搭建

> **前置说明**：本课程涉及 AI 编程、智能体开发和数据仓库实操，需要提前搭建完整的开发环境。以下步骤务必在第一次正式上课前完成，遇到问题随时在课堂上提出。

---

## 📋 目录

1. [注册国内大模型账号](#注册国内大模型账号)
2. [Git 安装与配置](#git-安装与配置)
3. [Node.js 环境搭建](#nodejs-环境搭建)
4. [Python 环境搭建（Miniconda）](#python-环境搭建miniconda)
5. [CC Switch 安装与配置](#cc-switch-安装与配置)
6. [Claude Code 安装与基本配置](#claude-code-安装与基本配置)
7. [环境验证清单](#环境验证清单)

---

# 注册国内大模型账号

在本课程中，我们将使用国产大模型作为 AI 编程的底层引擎。建议同时注册 **DeepSeek** 和 **Kimi**，以应对不同场景的需求。

## DeepSeek 注册与 API Key 获取

### 注册流程

1. 访问 DeepSeek 开发者平台：[https://platform.deepseek.com](https://platform.deepseek.com)
2. 点击右上角「注册」，支持 **手机号注册**
3. 注册后登录，进入「开发者控制台」

> 📖 官方文档参考：[DeepSeek API 文档](https://platform.deepseek.com/api-docs/)

### API Key 创建步骤

1. 登录控制台 → 左侧菜单 **「API Keys」**
2. 点击 **「创建 API Key」**
3. 输入名称（如 `课程实训`），点击确认
4. 系统会生成一个类似 `sk-xxxxxxxxxxxxxxxxxxxxxxxx` 的密钥

> ⚠️ **重要**：API Key 创建后**仅显示一次**，请**立即复制保存**到安全的地方！

### 充值说明

- DeepSeek API 为**按量计费**，需要先充值才能使用
- 建议第一次充值 **10~50 元**，日常开发消耗极低
- 充值入口：控制台 → 「充值」→ 选择金额 → 微信/支付宝支付

| 模型 | 输入价格（元/百万 tokens） | 输出价格（元/百万 tokens） |
|------|:------:|:------:|
| `deepseek-v4-flash` | **¥1**（缓存命中 ¥0.02） | **¥2** |
| `deepseek-v4-pro` | **¥3**（缓存命中 ¥0.025） | **¥6** |

> 📌 价格为 2026 年上半年限时折扣价。V4-Pro 标准价为输入 $1.74 / 输出 $3.48，目前享受 **2.5 折**优惠。预期下半年昇腾 950 量产后进一步大幅降价。

> 💡 普通编程对话约 0.01~0.05 元/次，日常开发 **10 元够用一个月**

### 模型说明

| 模型 | 参数规模 | 特点 |
|------|:------:|------|
| `deepseek-v4-flash` | 284B 总参 / 13B 激活 | 轻量高速，首字延迟 < 200ms，日常编程首选 |
| `deepseek-v4-pro` | 1.6T 总参 / 49B 激活 | 旗舰推理，Agent 编程能力接近 Claude Opus 4.6 |

> 📌 两个模型均支持 **1M（百万）token 上下文**，输出上限 384K tokens。
>
> 📌 **V4 多模态**：API 版本已支持图像/视频理解（视觉权重预计 2026 Q3 开源），无需再依赖 Kimi 处理图片。

> ⚠️ **注意**：老的 `deepseek-chat`（V3）和 `deepseek-reasoner`（R1）接口将于 **2026年7月24日弃用**，请直接使用 V4 系列。

---

## Kimi（月之暗面）注册与 API Key 获取

### 注册流程

1. 访问 Kimi 开放平台：[https://platform.moonshot.cn](https://platform.moonshot.cn)
2. 点击「注册」，使用**手机号注册**（比 DeepSeek 更简单，无需实名认证）
3. 登录后进入控制台

> 📖 官方文档参考：[Kimi API 文档](https://platform.moonshot.cn/docs)

### API Key 创建步骤

1. 控制台 → 左侧菜单 **「API Key 管理」**
2. 点击 **「新建密钥」**
3. 输入密钥名称，确认创建
4. 复制保存 API Key（格式：`sk-xxxxxxxxxxxxxxxxxxxxxxxx`）

### 新用户福利与充值

- 🎁 新注册用户赠送 **15 元体验金**，无需充值即可开始试用
- 体验金用完后再根据需要充值

### 模型说明

| 模型 | 特点 |
|------|------|
| `kimi-2`（K2-Thinking） | 超长上下文（百万字）、多模态、强推理 |
| `kimi-1.5` | 快速响应，适合日常对话和简单任务 |

> 💡 **推荐场景**：涉及图片理解、长文档分析时使用 Kimi；纯代码推理使用 DeepSeek。

---

## 两者对比与使用策略

| 对比维度 | DeepSeek V4 | Kimi (Moonshot) |
|----------|----------|-----------------|
| 🖼️ **多模态** | ✅ API 支持（视觉权重 Q3 开源） | ✅ 原生支持图片、文件理解 |
| 🧠 **推理能力** | ⭐⭐⭐⭐⭐ (V4-Pro 接近 Claude Opus) | ⭐⭐⭐⭐ (K2-Thinking) |
| 📏 **上下文长度** | **1M tokens** | 百万字级别 |
| 💰 **价格** | ¥1-6/百万 tokens（极低） | 中等 |
| ⚡ **速度** | Flash < 200ms / Pro 800-1500ms | 较快 |
| 🔑 **注册难度** | 需实名认证 | 手机号即可 |
| 🎁 **新用户福利** | 少量免费额度 | 送 15 元体验金 |
| 👨‍💻 **代码/Agent** | ⭐⭐⭐⭐⭐ (V4-Pro 极强) | ⭐⭐⭐⭐ |

### 🎯 本课程使用策略

```
日常编程 + Agent 任务 → 优先用 DeepSeek V4-Flash（便宜 + 高速）
复杂算法 + 架构设计 → 切换到 DeepSeek V4-Pro（极致推理能力）
图片分析 + 长文档   → DeepSeek V4 API 已支持，也可用 Kimi 备用
```

---

# Git 安装与配置

Git 是代码版本管理的基础工具，也是 Claude Code 和各类 AI 开发工具的前置依赖。

## 下载安装包（国内镜像加速）

> ⚠️ 官网 `https://git-scm.com` 在国内下载极慢，建议使用镜像：

| 镜像源 | 下载地址 |
|--------|----------|
| **华为云（推荐）** | [https://mirrors.huaweicloud.com/git-for-windows/](https://mirrors.huaweicloud.com/git-for-windows/) |
| **清华 TUNA** | [https://mirrors.tuna.tsinghua.edu.cn/git-for-windows/](https://mirrors.tuna.tsinghua.edu.cn/git-for-windows/) |

- 下载最新 64 位版本：`Git-2.4x.x-64-bit.exe`
- 官方文档：[https://git-scm.com/book/zh/v2](https://git-scm.com/book/zh/v2)

## Windows 安装步骤

> 以下步骤中标 ⚠️ 的为**关键配置**，请务必按说明选择！

| 步骤 | 选项 | 选择 |
|------|------|------|
| 1 | 安装路径 | 自定义，建议 `D:\Program Files\Git` |
| 2 | 选择组件 | ✅ 勾选 `Git Bash Here`、`Git GUI Here` |
| 3 | ⚠️ 默认编辑器 | **不要选 Vim！** 选择 **VS Code** 或 **Notepad++** |
| 4 | ⚠️ PATH 环境 | 选 **"Git from the command line and also from 3rd-party software"** |
| 5 | SSH 执行 | 选 **"Use bundled OpenSSH"**（默认） |
| 6 | HTTPS 传输 | 选 **"Use the OpenSSL library"**（默认） |
| 7 | ⚠️ 换行符 | 选 **"Checkout Windows-style, commit Unix-style line endings"** |
| 8 | 终端模拟器 | 推荐 **"Use MinTTY"** |
| 9 | 其余选项 | 保持默认 → Install |

### 验证安装

打开 Git Bash 或 CMD，输入：

```bash
git --version
# 输出: git version 2.49.0.windows.1  ✅
```

## 基本配置

```bash
# 配置用户名（替换为你的真实姓名）
git config --global user.name "张三"

# 配置邮箱（替换为你的真实邮箱）
git config --global user.email "zhangsan@example.com"

# 设置默认分支名为 main（GitHub 新标准）
git config --global init.defaultBranch main

# 查看所有配置
git config --global --list
```

## 生成 SSH Key（用于 GitHub / Gitee）

### 生成密钥（推荐 Ed25519 算法）

```bash
# 打开 Git Bash，执行：
ssh-keygen -t ed25519 -C "你的邮箱@example.com"

# 一路按 Enter 即可（使用默认路径和空密码）
```

> 生成后会在 `C:\Users\你的用户名\.ssh\` 目录下产生两个文件：
> - `id_ed25519` —— 私钥（**绝对不能泄露！**）
> - `id_ed25519.pub` —— 公钥（需要上传到代码托管平台）

### 复制公钥

```bash
cat ~/.ssh/id_ed25519.pub
# 复制输出的全部内容（以 ssh-ed25519 开头）
```

### 添加公钥到平台

| 平台 | 操作路径 |
|------|----------|
| **GitHub** | 登录 → Settings → SSH and GPG keys → New SSH Key → 粘贴保存 |
| **Gitee（码云）** | 登录 → 个人设置 → SSH 公钥 → 粘贴保存 |

### 测试连接

```bash
ssh -T git@github.com
# 成功: Hi username! You've successfully authenticated...

ssh -T git@gitee.com
# 成功: Hi username! You've successfully authenticated...
```

## 国内加速 GitHub 克隆

```bash
# 方法一：使用 ghproxy 代理（临时加速）
git clone https://ghproxy.com/https://github.com/用户/仓库.git

# 方法二：全局配置 URL 替换（一劳永逸）
git config --global url."https://ghproxy.com/https://github.com/".insteadOf "https://github.com/"

# 方法三（如果有梯子）：配置 HTTP 代理
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890
```

---

# Node.js 环境搭建

Claude Code 是基于 Node.js 的 CLI 工具，需要 Node.js ≥ 18 版本。本课程直接安装 **Node.js 22.x LTS**，不做多版本管理。

> 🎯 **为什么不用 nvm？** 课程实训只需要一个稳定的 Node 版本即可，直接安装最简单、最稳定，避免 nvm 符号链接和 PATH 混乱问题。你的讲师环境也是直接用 Node 22 原生安装。

## 下载 Node.js 安装包（使用国内镜像）

> ⚠️ 官网 `https://nodejs.org` 在国内下载极慢，建议使用国内镜像：

| 镜像源 | 下载地址 |
|--------|----------|
| **npmmirror（推荐）** | [https://npmmirror.com/mirrors/node/v22.x.x/](https://npmmirror.com/mirrors/node/) |
| **华为云** | [https://mirrors.huaweicloud.com/nodejs/](https://mirrors.huaweicloud.com/nodejs/) |

- 下载最新 **22.x LTS** 版本：`node-v22.x.x-x64.msi`（Windows 安装包）
- 官方文档：[https://nodejs.org/docs/latest-v22.x/api/](https://nodejs.org/docs/latest-v22.x/api/)

## Windows 安装步骤

1. 双击 `node-v22.x.x-x64.msi`
2. 一路 Next（全部保持默认）
3. ⚠️ 关键步骤！在 **「Custom Setup」** 页面，确认 **「Add to PATH」** 选项为 ✅（默认已勾选）
4. 点击 Install 完成

> 📌 默认安装路径：`C:\Program Files\nodejs\`，会自动加入系统 PATH。

### 验证安装

```bash
# 新开一个 CMD 或 PowerShell 窗口
node --version   # v22.x.x  ✅
npm --version    # 10.x.x   ✅
```

## 配置 npm 国内镜像

```bash
# 设置 npm 包镜像源为淘宝/阿里云 npmmirror
npm config set registry https://registry.npmmirror.com

# 验证
npm config get registry
# 输出: https://registry.npmmirror.com/  ✅

# 安装一个包测试速度
npm install -g npm-check-updates
```

### 在项目目录下也可以创建 `.npmrc` 文件

```ini
registry=https://registry.npmmirror.com
disturl=https://npmmirror.com/mirrors/node/
```

---

# Python 环境搭建（Miniconda）

本课程的数据仓库实训和 Dify 开发需要 Python 环境。使用 **Miniconda** 可以轻量、隔离地管理多个 Python 版本和依赖包。

## 为什么用 Miniconda？

| Anaconda | Miniconda (推荐) |
|----------|:---:|
| 安装体积 ~3GB | 安装体积 ~400MB |
| 预装 1500+ 包 | 仅含 conda + Python 核心 |
| 臃肿，很多用不上 | 按需安装，干净可控 |

## 下载 Miniconda（使用国内镜像）

> ⚠️ 官方下载地址 `https://repo.anaconda.com/miniconda/` 在国内很慢，建议使用国内镜像：

| 镜像站 | 下载地址 |
|--------|----------|
| **清华 TUNA（推荐）** | [https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/](https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/) |
| **中科大 USTC** | [https://mirrors.ustc.edu.cn/anaconda/miniconda/](https://mirrors.ustc.edu.cn/anaconda/miniconda/) |

- 选择对应系统的版本：
  - **Windows**：`Miniconda3-latest-Windows-x86_64.exe`
  - **macOS Intel**：`Miniconda3-latest-MacOSX-x86_64.pkg`
  - **macOS Apple Silicon**：`Miniconda3-latest-MacOSX-arm64.pkg`

> 📖 官方文档参考：[Conda 文档](https://docs.conda.io/en/latest/miniconda.html)

## Windows 安装步骤

1. 双击 `.exe` 安装包
2. 选择安装类型：**Just Me (recommended)**
3. 选择安装路径：建议 `C:\Users\你的用户名\Miniconda3`
4. ⚠️ **重要！** 勾选 **「Add Miniconda3 to my PATH environment variable」**
5. ⚠️ **重要！** 勾选 **「Register Miniconda3 as my default Python 3.x」**
6. 点击 Install 完成

### 验证安装

```bash
# 新开一个 CMD 或 PowerShell 窗口
conda --version
# 输出: conda 24.x.x  ✅

python --version
# 输出: Python 3.12.x  ✅
```

## 配置系统环境变量（确保命令行可执行 Python）

> ⚠️ 如果在安装时忘记勾选「Add Miniconda3 to my PATH」，或者安装后 `python` 命令提示"找不到"，需要手动配置系统环境变量。

### 检查 Python 是否已在 PATH 中

```bash
# 打开 CMD，输入：
where python
# 正常情况下应输出 Miniconda3 安装路径，如：
# C:\Users\你的用户名\Miniconda3\python.exe  ✅

where conda
# 正常输出：
# C:\Users\你的用户名\Miniconda3\Scripts\conda.exe  ✅
```

> 如果 `where python` 无输出或指向其他路径（如 Windows Store），说明需要手动配置环境变量。

### 手动添加 Miniconda 到系统 PATH

需要将以下 **3 个路径** 添加到系统环境变量的 `Path` 中（按实际安装路径调整）：

| 序号 | 需添加的路径 | 作用 |
|:----:|------|------|
| 1 | `C:\Users\你的用户名\Miniconda3` | 使 `python` 命令可用 |
| 2 | `C:\Users\你的用户名\Miniconda3\Scripts` | 使 `conda`、`pip` 命令可用 |
| 3 | `C:\Users\你的用户名\Miniconda3\Library\bin` | 使依赖的动态库可被找到 |

### Windows 操作步骤

1. **Win + R** → 输入 `sysdm.cpl` → 确定
2. 点击 **「高级」** 选项卡 → **「环境变量」**
3. 在 **「用户变量」**（或「系统变量」）中找到 `Path` 变量 → 双击编辑
4. 点击 **「新建」**，依次添加上述 3 个路径
5. ⚠️ 使用「上移」按钮将 3 个路径移到顶部，确保优先级高于其他 Python
6. 点击「确定」保存所有窗口
7. **重新打开 CMD**，再次执行 `where python` 验证

> 💡 **排序提示**：如果系统中安装了多个 Python（如 Windows Store 版），请务必将 Miniconda 的路径放在最前面，确保 `python` 命令指向 Miniconda。

### 验证配置成功

```bash
# 重新打开 CMD 后执行：
python --version   # Python 3.12.x  ✅
conda --version    # conda 24.x.x   ✅
pip --version      # pip 24.x.x     ✅

# 确认 Python 路径正确
where python
# 第一行必须是 Miniconda3 路径！✅
```

---

## 配置国内镜像源（关键步骤！）

> ⚠️ **安装完 Miniconda 后第一件事就是改镜像**，否则 `conda install` 会极慢或失败。

### 命令行一键配置（推荐）

```bash
# 添加清华大学镜像源
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/

# 设置通道优先级
conda config --set channel_priority strict

# 显示来源 URL（便于排查问题）
conda config --set show_channel_urls yes
```

### 验证镜像配置

```bash
conda config --show channels
```

输出应包含 `mirrors.tuna.tsinghua.edu.cn` 地址。

### 备选镜像源

```bash
# 中科大 USTC
conda config --add channels https://mirrors.ustc.edu.cn/anaconda/pkgs/main/

# 阿里云
conda config --add channels https://mirrors.aliyun.com/anaconda/pkgs/main/
```

## 本项目统一使用 base 环境

> 🎯 **课程约定**：为简化环境管理、方便脚本运行和课堂演示，本实训项目**统一使用 base 环境**，不创建额外的虚拟环境。所有 Python 包直接安装在 base 中。

```bash
# 确认当前在 base 环境（终端提示符前应有 (base) 标识）
conda activate base

# 查看 base 环境中的 Python 版本
python --version
```

> 💡 **为什么用 base？** 课程实训涉及大量脚本和 Dify 工作流调用，统一 base 环境可以避免每次手动激活环境、路径混乱等问题，降低初学者的认知负担。

## 配置 pip 国内镜像

```bash
# 确保在 base 环境
conda activate base

# 设置 pip 镜像为清华源
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 或使用阿里云
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

# 验证
pip config list
```

## 安装课程常用 Python 包

```bash
# 确保在 base 环境（终端提示符有 (base) 标识）
conda activate base

# 基础数据科学包
pip install numpy pandas matplotlib jupyter notebook

# 数据库连接
pip install pymysql sqlalchemy

# API 开发
pip install requests flask

# Dify 相关后续按需安装
```

---

# CC Switch 安装与配置

## 什么是 CC Switch？

**CC Switch**（GitHub: [farion1231/cc-switch](https://github.com/farion1231/cc-switch)）是一个开源跨平台桌面工具，用于给 Claude Code 一键切换 AI 模型提供商。

| 问题 | CC Switch 如何解决 |
|------|-------------------|
| Claude Code 默认连 `api.anthropic.com`（被墙） | 拦截并重定向到国内模型 API |
| 需要手动修改复杂配置文件 | 图形化界面一键切换 |
| 多个模型切换麻烦 | 预设模板快速配置 |

> 📖 官方仓库：[https://github.com/farion1231/cc-switch](https://github.com/farion1231/cc-switch)

## 安装 CC Switch

### Windows

1. 访问 [CC Switch Releases](https://github.com/farion1231/cc-switch/releases) 页面
2. 下载最新版 `.msi` 安装包或 `.exe` 安装程序
3. 双击安装，一路 Next
4. 安装完成后启动，任务栏右下角会出现 CC Switch 图标

### macOS

```bash
brew install --cask cc-switch
```

### Linux

从 Releases 下载 `.deb` / `.rpm` / `.AppImage`，使用对应包管理器安装。

## 配置 DeepSeek 模型

> 确保已完成 [DeepSeek 注册与 API Key 获取](#deepseek-注册与-api-key-获取)。

### 步骤操作

1. 点击任务栏 CC Switch 图标 → 打开管理界面
2. 点击右上角 **「+」** 按钮 → 选择 **DeepSeek** 预设
3. 填入以下信息：

| 配置项 | 值 |
|--------|-----|
| **Base URL** | `https://api.deepseek.com/anthropic` |
| **API Key** | 你在 DeepSeek 平台创建的 API Key（`sk-xxxxx`） |
| **主力模型** | `deepseek-v4-pro`（旗舰推理） |
| **轻量模型** | `deepseek-v4-flash`（日常编程首选） |

4. 点击保存 → **启用**

### 模型选择建议

| 场景 | 推荐模型 |
|------|----------|
| 日常代码编写 | `deepseek-v4-flash` — 便宜（¥2/百万输出）、首字 < 200ms |
| 复杂算法/架构 | `deepseek-v4-pro` — 1.6T 参数、强推理、强 Agent 能力 |
| 省钱模式 | `deepseek-v4-flash` — 输出成本仅为 Pro 的 1/3 |

## 配置 Kimi 模型（可选）

> 如果主要使用 DeepSeek，Kimi 可作为备用方案。配置方式与 DeepSeek 类似。

| 配置项 | 值 |
|--------|-----|
| **Base URL** | `https://api.moonshot.cn/anthropic` |
| **API Key** | 你在 Kimi 平台创建的 API Key（`sk-xxxxx`） |
| **主力模型** | `kimi-2` 或 `kimi-2-thinking` |

---

# Claude Code 安装与基本配置

## 什么是 Claude Code？

Claude Code 是 Anthropic 官方推出的 AI 编程 CLI（命令行）工具，可以在终端中与 AI 对话、编写代码、管理项目。

在本课程中，我们通过 CC Switch 将其底层模型切换为国产大模型，实现**国内免魔法免费/低成本使用**。

> 📖 官方文档：[https://docs.anthropic.com/en/docs/claude-code/overview](https://docs.anthropic.com/en/docs/claude-code/overview)

## 前置检查

在安装之前，请确认以下条件已满足：

```bash
# 1. Node.js ≥ 18
node --version  # 应为 v20.x 或 v18.x

# 2. npm 可用
npm --version   # 应为 10.x 或更高

# 3. npm 镜像正确
npm config get registry
# 应为 https://registry.npmmirror.com
```

## 通过 npm 安装（国内推荐方式）

```bash
# 全局安装，使用国内镜像加速
npm install -g @anthropic-ai/claude-code --registry=https://registry.npmmirror.com

# 验证安装
claude --version
# 输出版本号即成功 ✅
```

> ⚠️ 如果安装过程中提示权限错误（EACCES），请使用**管理员模式**打开 CMD/PowerShell 再执行。

## 设置环境变量（可选但推荐）

```bash
# 如果使用新版 Claude Code 遇到 "thinking type" 兼容性问题
# 在系统环境变量中添加：
变量名: CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING
变量值: 1
```

### Windows 设置环境变量的方法

1. Win + R → 输入 `sysdm.cpl` → 确定
2. 高级 → 环境变量
3. 用户变量 → 新建
4. 变量名：`CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING`
5. 变量值：`1`
6. 点击确定保存

## 验证全部配置

```bash
# 第一步：确认 CC Switch 正在运行，且已启用模型

# 第二步：在任意目录打开终端，输入：
claude

# 第三步：如果成功，会进入 Claude Code 交互界面
# 输入 /model 查看当前使用的模型
# 应返回你在 CC Switch 中配置的模型名称 ✅
```

### 基本使用命令

| 命令 | 功能 |
|------|------|
| `claude` | 启动 Claude Code 交互模式 |
| `claude "你的问题"` | 直接提问（不进入交互模式） |
| `claude --help` | 查看帮助 |
| `/help` | 交互模式中查看所有命令 |
| `/model` | 查看当前模型 |
| `/clear` | 清除对话历史 |
| `Ctrl + C` / `exit` | 退出 |

## 常见问题排查

| 现象 | 原因 | 解决方案 |
|------|------|----------|
| `Unable to connect to Anthropic services` | CC Switch 未启用或配置错误 | 检查 CC Switch 是否运行、模型是否已启用、重启终端 |
| 弹出 Anthropic 登录界面 | CC Switch 未正确拦截请求 | 检查 CC Switch 是否运行且模型已启用，重启终端再试 |
| `402 Insufficient Balance` | DeepSeek 账户余额不足 | 登录 DeepSeek 平台充值 |
| `401 Unauthorized` | API Key 无效 | 检查 Key 格式（`sk-` 开头），确认未过期 |
| `claude` 命令找不到 | PATH 未包含 npm 全局安装目录 | 重启终端，或将 `%APPDATA%\npm` 加入 PATH |
| `400 thinking type` 错误 | 新版 Claude Code 与第三方 API 不兼容 | 添加环境变量（见上节） |

---

# 环境验证清单

完成全部配置后，请逐项检查：

```bash
# ========== 基础工具 ==========
git --version          # ✅ git version 2.49.x
ssh -T git@github.com  # ✅ 认证成功

# ========== Node.js ==========
node --version         # ✅ v22.x.x
npm --version          # ✅ 10.x.x
npm config get registry  # ✅ https://registry.npmmirror.com

# ========== Python ==========
conda --version        # ✅ conda 24.x.x
python --version       # ✅ Python 3.12.x
where python           # ✅ 第一行必须是 Miniconda3 路径
pip config list        # ✅ 显示清华/阿里云镜像

# ========== AI 平台 ==========
# ✅ 已注册 DeepSeek 并获取 API Key
# ✅ 已注册 Kimi 并获取 API Key
# ✅ DeepSeek 账户已充值（建议 10-50 元）

# ========== AI 工具链 ==========
# ✅ CC Switch 已安装、已运行
# ✅ CC Switch 中已配置并启用模型
claude --version       # ✅ 输出版本号

# ========== 最终测试 ==========
# ✅ 执行 claude 进入交互模式，输入 /model 确认模型
```

> 🎉 全部通过后，你的开发环境就准备就绪了！继续完成以下验证练习。

---

## 📝 课后验证练习

请完成以下练习，并在下次课开始时演示：

1. **模型切换测试**：在 CC Switch 中分别切换到 DeepSeek 和 Kimi，在 Claude Code 中询问"请介绍一下你自己"，对比两者的回答。
3. **Python 环境测试**：在 CMD 中直接运行 `python -c "import numpy as np; print(np.__version__)"`，确保不报错且路径指向 Miniconda3。
4. **Node 全局包测试**：执行 `npm list -g --depth=0`，确认 `@anthropic-ai/claude-code` 在列表中。

---

> 💬 **遇到问题？** 欢迎在课堂上提出，或提前在群内交流。环境搭建是课程的"拦路虎"，一次性解决好，后续实训才能顺滑进行。
