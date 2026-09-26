# 伯恩斯情绪工具集 · Web 版（burns_tools_web）

把单机桌面版 [burns-tools](https://github.com/Jong-L/burns-tools)（PySide6 + SQLite，Windows 单用户）搬到浏览器上的全栈版本。工具设计参考《伯恩斯新情绪疗法》（David Burns, *Feeling Good*）中的认知行为疗法（CBT）自助练习，帮助用户记录和矫正消极思维、对抗拖延。

Web 版与桌面版的差别只有三处：**从单机变多用户、从桌面窗口变网页、数据从本地文件变成服务端数据库**。工具本身的字段、打分规则、交互逻辑（例如三列/六列的字段差异、反驳"但是"法的链式解锁）与桌面版逐条一致，依据是 [docs/data-layer-spec.md](docs/data-layer-spec.md)——它同时是数据表结构的权威定义和老库的迁移映射方案。

> **当前状态**：部署链路已跑通（nginx + systemd + Next.js SSR），但**工具功能尚未实现**——前端还是多语言脚手架（一个计数器示例页），后端只有 `/api/health`。详见文末「进度与后续计划」。

---

## 一、包含哪些工具

| 工具 | tool_id | 做什么 | 关键规则 |
| :-- | :-- | :-- | :-- |
| 消极思维日志 | `thought_journal` | 用三列法 / 六列法记录引发情绪的事件与下意识思维，标注其中的认知扭曲，并写下理性回应 | 认知扭曲固定 11 项（非此即彼、以偏概全、心理过滤…）；同一项不可重复添加；理性回应为空的记录打「未回应」徽标并排在最前 |
| 消极思维计数器 | `thought_counter` | 记录每天消极思维出现的次数 | 一天一条记录，保存是**覆盖**不是累加；计数不可为负；折线图窗口固定 7 / 30 / 90 / 180 / 365 天，缺数据补 0 |
| 每日活动计划表 | `daily_activity_plan` | 按固定时间段制定一天的活动计划，记录实际做了什么，并给掌控感 / 愉悦感打分 | 固定 14 个时间段（上午 8-9 … 晚上 9-12）；掌控型分数 M、休闲活动分数 P 均为 **0–5 整数或留空**；缺的槽位补空行 |
| 反拖延症表 | `anti_procrastination_table` | 把任务拆成小步骤，对比「预计」与「实际」的难度和满足程度，减轻畏难情绪 | 四个百分比均为 **0–100 整数或留空**；活动名与四个百分比全空的行不保存；有数据时按「实际均值 − 预计均值」±10 个百分点给出两段洞察文案 |
| 反驳"但是"法 | `but_rebuttal_tool` | 针对每个"但是……"的借口写下更实际、更理性的反驳，让拖延没有落脚点 | **链式解锁**：第 1 行左列恒可写，之后每行左列需上一行右列非空，右列需本行左列非空；末尾始终保留一个空行；完成轮数 ≥3 时提示"抓一个反驳马上行动" |

### 工具举例：消极思维日志的两种模板

| 模板 | type 值 | 包含的列 |
| :-- | :-- | :-- |
| 三列法 | `three_column` | 下意识思维、认知扭曲、理性回应 |
| 六列法 | `six_column` | 情况、情绪、下意识思维、认知扭曲、理性回应、结果 |

新建时弹模板选择框，默认选三列。两种模板共用同一套认知扭曲选项与添加逻辑。

---

## 二、技术选型与架构

### 2.1 选型一览

| 层 | 选型 | 为什么这么选 |
| :-- | :-- | :-- |
| 前端框架 | **Next.js 16（App Router）+ React 19** | 需要 SEO——工具介绍页要被搜索引擎收录，所以要服务端渲染（SSR）；Next 同时提供文件路由、中间件和构建打包，一个框架覆盖前端与渲染服务 |
| 前端语言路由 | `app/[lang]/` 动态段 + `proxy.js` | 用路径前缀区分语言（`/zh`、`/en`），比纯前端路由省事，也让 `/zh` 这类地址可直接分享 |
| 前端文案 | `data/zh.json` / `data/en.json` + `data/index.js` 注册中心 | 界面文案与组件分离，加语言只需加一个 JSON 文件 |
| 后端 | **FastAPI + Uvicorn**（Python `uv` 管理依赖） | 类型标注直接生成 OpenAPI 文档；生态成熟，便于实现 JWT 用户系统 |
| 数据库 | **SQLite（WAL 模式）** | 数据量小、单机部署；结构与约束按 [docs/data-layer-spec.md](docs/data-layer-spec.md) 设计，必要时可平移迁移到 PostgreSQL |
| 部署 | **nginx 反向代理 + systemd** | 浏览器只跟 nginx 一个域通信，前端用相对路径 `/api/xxx`，无跨域问题 |

### 2.2 请求链路

```
浏览器
  │
  └─ nginx :80
       ├─ /      →  Next.js SSR（127.0.0.1:3000，systemd 守护）  页面 / 语言路由
       └─ /api   →  FastAPI（127.0.0.1:8000）                     数据 API
                        └─ SQLite  burns_tools.db
```

- 前端页面走 SSR，`proxy.js` 负责语言重定向：`/` → `/zh`，未知语言（如 `/fr`）也回落到 `/zh`。
- `/api` 已由 nginx 转发到 8000 端口，后端起来即通；后端未启动时访问 `/api` 返回 502 属正常现象，不是配置错误。
- 开发期前端在 `localhost:3100` 直连后端 8000，后端已放开对应的 CORS。

### 2.3 数据归属

Web 版是**多用户服务**：所有业务数据都带 `user_id`，一个账号只能读写自己的记录；`user_id` 只从服务端会话（JWT）取，绝不接受请求体里传来的用户标识。

桌面版是单用户单库（`MyAppData\burns_tools_data\burns_tools.db`），迁移到 Web 版时整体归属给认领账号，字段级映射与脏数据检查 SQL 见数据层规格的第 4 节。

---

## 三、目录结构

```
burns_tools_web/
├── frontend/                    Next.js 16 前端
│   ├── app/
│   │   ├── [lang]/
│   │   │   ├── layout.jsx       服务端设置 <html lang> 与标题（SEO）
│   │   │   ├── page.jsx         首页服务端组件：按 lang 取文案
│   │   │   └── App.jsx          页面交互（客户端组件）
│   │   ├── useLang.jsx          语言上下文：读取 [lang]、切换语言并保留后续路径
│   │   └── globals.css
│   ├── data/                    界面文案数据
│   │   ├── index.js             文案注册中心（语言列表、默认语言、取用函数）
│   │   └── zh.json / en.json    各语言的页面文案
│   └── proxy.js                 语言重定向（Next.js 16 中的 middleware）
│
├── backend/                     FastAPI 后端（uv 项目，src 布局）
│   ├── src/backend/main.py      应用入口：CORS + /api/health
│   ├── pyproject.toml           依赖：fastapi、uvicorn[standard]
│   └── README.md
│
├── docs/
│   └── data-layer-spec.md       数据层规格：表结构、各工具读写方法、业务规则、迁移映射
│
├── deploy/                      部署脚本与配置（nginx 站点、systemd unit、远程执行脚本）
└── 部署流程.md                   服务器部署全流程记录（含踩过的坑与排查备忘）
```

---

## 四、本地开发

### 环境要求

- Node.js 18.18+（服务器实测 v24.21.0）
- Python 3.13+ 与 [uv](https://docs.astral.sh/uv/)

### 启动前端

```bash
cd frontend
npm ci
npm run dev        # http://localhost:3100 会自动跳到 /zh
```

### 启动后端

```bash
cd backend
uv sync
uv run uvicorn backend.main:app --reload --port 8000
curl http://127.0.0.1:8000/api/health    # {"status":"ok"}
```

生产构建与部署（nginx 站点配置、systemd 守护、更新流程、常见故障排查）见 `部署流程.md`。

---

## 五、进度与后续计划

| 状态 | 事项 |
| :-- | :-- |
| ✅ | 前端多语言骨架：`/zh`、`/en`、语言切换、未知语言回落、文案与组件分离 |
| ✅ | 后端 FastAPI 骨架与 CORS 配置 |
| ✅ | 生产部署链路：nginx 反代 + systemd 守护 Next.js SSR，公网已验证 |
| ✅ | 数据层设计：多用户表结构、完整性约束、迁移映射（[docs/data-layer-spec.md](docs/data-layer-spec.md)） |
| ⬜ | 用户系统：注册 / 登录 / JWT 鉴权 |
| ⬜ | 数据层落地：按规格实现 SQLite 存储层与单元测试 |
| ⬜ | 5 个工具的数据 API |
| ⬜ | 5 个工具的前端页面（工具介绍页走 ISR 保证 SEO；用户数据页客户端拉取） |
| ⬜ | 老库数据迁移与读接口对拍 |
| ⬜ | 域名 + HTTPS（可选） |