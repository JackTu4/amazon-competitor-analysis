# Amazon 智能竞品分析系统

> 输入一个目标商品（名称或 ASIN），自动发现竞品、采集商品与评论、用 LLM 完成对比分析，生成带来源的 Markdown 报告。

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.1.0-009688?logo=fastapi&logoColor=white)
![Vue](https://img.shields.io/badge/Vue-3.5-4FC08D?logo=vue.js&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-RQ-DC382D?logo=redis&logoColor=white)

## 项目简介

做 Amazon 竞品分析时，运营需要在搜索结果、商品详情页、评论区、第三方评测之间反复切换，人工整理一份报告通常要几十分钟。

这个项目把这条链路做成一个可复跑的 Agent 工作流：用户只输入目标商品，系统自动完成「找竞品 → 核验商品身份 → 采集商品与评论 → LLM 对比分析 → 生成 Markdown 报告」，并提供 Web 界面、异步任务队列和一套 10 案例的离线评估。

适合的场景：跨境电商运营、市场分析、选品调研。当前定位是可演示、可评估的 MVP，不是生产级 SaaS。

## 核心能力

- **自动竞品发现**：根据目标商品生成多组搜索词，调用 Tavily 搜索候选竞品，再按 ASIN 格式、品牌差异、品类关键词、来源链接做核验，自动选出最多 3 个竞品。
- **多工具 Agent**：每个竞品由一个 LLM Agent 分析，可调用本地知识库检索、网页搜索（可按 ASIN 读取 Amazon 商品页）、评论采集分析三类工具。
- **评论分析**：通过 Bright Data 采集 Amazon 评论，输出评分、痛点、优点、改进建议和总结；目标商品评论在竞品发现阶段后台预热，减少等待。
- **并行与失败隔离**：最多 3 个竞品并行分析，单个竞品异常不会影响其他竞品；报告末尾会列出未完成分析的竞品及原因。
- **带来源的报告**：Markdown 报告包含目标商品、竞品核心指标对比、价格差异、评论分析、数据说明和来源链接；价格差异无法可靠计算时输出 `null`，不编造。
- **异步任务与持久化**：FastAPI 接收请求后写入 MySQL 并入队 Redis，RQ Worker 在后台执行 3–14 分钟的分析；任务状态、商品明细、来源、报告都落库，前端按任务 ID 轮询。
- **Web 界面**：Vue 3 + Vite，支持提交任务、查看状态、渲染和下载 Markdown 报告；可选 `X-API-Key` 鉴权。
- **离线评估**：10 个案例（7 正向 + 3 负向），支持批量复跑，输出成功率、竞品有效性、耗时、token 消耗等指标，结果写入 `evals/results/`。

## 系统架构

```text
Vue 3 + Vite
     │  POST /api/analysis
     ▼
FastAPI ──────────────► MySQL
     │                   projects / products / sources / reports
     │  enqueue
     ▼
Redis (RQ queue)
     │
     ▼
RQ Worker (Docker / Linux)
     │
     ▼
AnalysisWorkflow
     ├─ 1. discover_competitors   Tavily 搜索 + 解析 + ASIN/品牌/品类核验
     ├─ 2. competitor_analysis    每个竞品一个 Agent，3 路并行
     │        └─ 工具：search_knowledge / search_web / analyze_product_reviews
     └─ 3. generate_report        Markdown 报告 + 失败竞品说明
              │
              ▼
     LLM（OpenAI 兼容接口）
```

更完整的架构与数据流见 `docs/architecture-data-flow.html` / `.pdf`。

### 一次分析的完整流程

1. 用户提交目标商品名称或 ASIN。
2. `find_target_asin` 搜索并核验目标商品，得到可靠的 ASIN、标题和品牌。
3. `run_discovery` 生成搜索词，调用 Tavily 找候选竞品，解析商品信息并按规则过滤、去重、核验，选出最多 3 个竞品。
4. `analysis_task` 用线程池并行分析竞品；每个 Agent 先检索本地知识库，再按需搜索网页，必要时采集目标商品评论。
5. Agent 输出结构化的 `CompetitorAnalysis` JSON，后端校验目标 ASIN、标题、品牌，缺失字段用发现阶段的核验结果兜底。
6. `generate_markdown` 生成报告；任务状态、商品、来源、报告写入 MySQL。
7. 前端轮询任务状态，完成后渲染报告并支持下载。

### 设计取舍

- **竞品发现和核验分开**：搜索负责召回，LLM 解析候选商品，ASIN/品牌/品类由规则核验，降低「模型编一个不存在的 ASIN」的概率。
- **单竞品失败隔离**：最多 3 个竞品并行执行，任何一路超时或解析失败都不阻断其他竞品，报告里保留失败原因。
- **HTTP 与重任务解耦**：一次分析要调用搜索、抓取和多轮 LLM，放在同步接口里容易超时，所以用 Redis + RQ 异步执行。
- **评估与业务解耦**：`evals/` 直接复用真实工作流和数据库，但把指标、评分和报告独立出来，方便改 prompt/工具后对比同一批案例。

## 技术栈

| 层次 | 技术 |
| --- | --- |
| 前端 | Vue 3、Vite、markdown-it、DOMPurify |
| API | FastAPI、Uvicorn、Pydantic |
| Agent / LLM | OpenAI 兼容接口（Qwen / DeepSeek 等均可）、Function Calling |
| 工具 | Tavily 搜索、Bright Data 评论采集、BeautifulSoup 网页解析、本地 Embedding 知识库 |
| 数据 | MySQL 8 + SQLAlchemy 2 + PyMySQL |
| 异步任务 | Redis + RQ |
| 部署 | Docker（Worker）、docker compose |
| 测试 / 评估 | pytest、自建 10 案例离线评估 |

## 快速开始

### 1. 环境要求

- Python 3.10+（Docker Worker 使用 3.11）
- Node.js 18+
- MySQL 8.0+
- Redis 6+（或使用 Docker 启动）
- Docker（Windows 下跑 RQ Worker 推荐使用）

### 2. 配置环境变量

```bash
git clone <your-repo-url>
cd <your-repo-dir>

cp .env.example .env
```

至少填写以下变量：

```dotenv
# LLM（OpenAI 兼容接口）
OPENAI_API_KEY=sk-...
OPENAI_API_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL_NAME=qwen3.7-flash
EMBEDDING_MODEL=text-embedding-v3

# 搜索与评论采集
TAVILY_API_KEY=...
BRIGHTDATA_API_KEY=...
BRIGHTDATA_DATASET_ID=...

# MySQL
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=...
DB_NAME=competitor_analysis

# Redis
REDIS_URL=redis://127.0.0.1:6379/0

# true: 不调用外部 API，生成模拟报告，适合先跑通链路
# false: 真实调用 LLM / 搜索 / 抓取
MOCK_MODE=false

# 可选：设置后 /api 接口需要 X-API-Key
API_KEY=
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### 3. 安装 Python 依赖

```bash
python -m venv .venv

# Windows Git Bash
source .venv/Scripts/activate

# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
```

### 4. 初始化 MySQL

```bash
python scripts/init_db.py
```

脚本会自动创建 `competitor_analysis` 库以及 `projects`、`products`、`sources`、`reports` 四张表。数据库用户需要有 `CREATE DATABASE` 权限。

### 5. 启动 Redis 与 RQ Worker

Windows 下 RQ Worker 依赖 Linux 的 fork 机制，推荐用 Docker 跑 Worker：

```bash
# 只创建一次
docker network create agent-network 2>/dev/null || true

# 启动一个 Redis，宿主机 6379 端口可访问
docker run -d --name agent-redis --network agent-network -p 6379:6379 redis:7-alpine

# 构建并启动 Worker
docker compose up -d --build worker
```

说明：

- `compose.yaml` 只定义了 Worker 服务；MySQL、Redis、FastAPI 和前端需要按上面的步骤分别准备或启动。
- `compose.yaml` 里 Worker 使用 `redis://agent-redis:6379/0`，宿主机上的 FastAPI 使用 `.env` 的 `REDIS_URL`，两者要指向同一个 Redis 实例。
- Worker 容器的 `DB_HOST` 已覆盖为 `host.docker.internal`；MySQL 需要允许来自 Docker 的连接。如果连不上，把 `compose.yaml` 里的 `DB_HOST` 改成宿主机的局域网 IP。
- 如果本机已经有 Redis，可以跳过 `docker run`，但要把 `compose.yaml` 里的 `REDIS_URL` 改成 Worker 能访问到的地址（例如 `redis://host.docker.internal:6379/0`），并保证 `.env` 的 `REDIS_URL` 指向同一个实例。

### 6. 启动后端

```bash
uvicorn backend.app.main:app --reload --port 8000
```

- Swagger：<http://127.0.0.1:8000/docs>
- 健康检查：<http://127.0.0.1:8000/health>

### 7. 启动前端

```bash
cd frontend
npm install

# 可选：与根目录 .env 的 API_KEY 保持一致
cp .env.example .env

npm run dev
```

打开 <http://127.0.0.1:5173>，输入目标商品即可。

### 8. Mock 模式

把 `.env` 的 `MOCK_MODE=true` 后重启 Worker，系统不会调用 LLM / 搜索 / 抓取，而是直接生成一份模拟 Markdown 报告。

适合先验证「前端 → API → Redis → Worker → MySQL → 报告」这条链路是否通。

## API 一览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/api/analysis` | 创建分析任务，body：`{"target_product": "Samsung 980 1TB NVMe SSD"}` |
| `GET` | `/api/analysis/{task_id}` | 查询任务状态：`pending` / `running` / `completed` / `failed` |
| `GET` | `/api/analysis/{task_id}/report` | 获取 Markdown 报告 |
| `GET` | `/api/analysis/{task_id}/products` | 获取目标商品、竞品和来源明细 |
| `GET` | `/health` | 健康检查（不鉴权） |

如果 `.env` 设置了 `API_KEY`，`/api` 请求需要带上：

```http
X-API-Key: <your-api-key>
```

示例：

```bash
# 如果设置了 API_KEY，再加一行 -H "X-API-Key: <your-api-key>"
curl -X POST http://127.0.0.1:8000/api/analysis \
  -H "Content-Type: application/json" \
  -d '{"target_product": "Samsung 980 1TB NVMe SSD"}'
```

## 测试

```bash
pytest                 # 默认：纯单元测试，不连 MySQL/Redis
pytest -m integration  # 需要本地 MySQL、Redis 和 .env
pytest -m llm          # 需要真实 LLM / 抓取接口，会产生费用
pytest -m ""           # 全部
```

## 离线评估

`evals/` 是一套与业务代码分离的 10 案例评估，覆盖 7 个正向案例和 3 个负向案例（无品牌、纯中文、虚构型号），用来回答「改完 prompt / 工具后，系统是变好还是变坏」。

### 运行

```bash
python -m evals.selftest          # 纯函数自检，不花钱、不连数据库
python -m evals.preflight         # 检查 .env、数据库表、案例配置
python -m evals.run_all --force   # 跑完 10 个案例，约 40–100 分钟
python -m evals.summarize         # 生成 summary.csv 和 report.md
```

只跑单个案例：

```bash
python -m evals.run_eval --case case-01 --force
```

结果在 `evals/results/`：

- `summary.csv`：逐案例指标
- `report.md`：汇总、逐案例、结论和边界说明
- `case-XX.json`：每个案例的完整结果（本地生成，默认不提交到 Git）

### 最近一次结果（2026-10-29）

| 指标 | 结果 |
| --- | --- |
| 案例数 | 10（正向 7 / 负向 3） |
| 成败判定 | 9/10；正向 6/7，负向 3/3 |
| 竞品有效性（正向均值） | 0.925 |
| 信息完整度（正向均值） | 0.790 |
| 目标字段准确率（正向均值） | 0.286（口径未校正，见下） |
| 平均耗时 | 全部 10 个案例均值 335.3 秒；正向均值 426.0 秒、中位数 340.9 秒 |
| 单次正向分析调用量 | 22.1 次 LLM 调用；约 82k prompt + 44.6k completion tokens；7.7 次 Tavily 搜索；1 个 Bright Data 任务 |
| 成本 | 未计（`evals/pricing.json` 单价未填，`$0.0000` 是占位符） |

**口径说明**：目标字段准确率 0.286 不能当作「字段抽取准确率 28.6%」引用。这一轮 7 个正向案例的目标 ASIN 与人工预期 0/7 命中，其中 3 个案例的目标价格/评分/评论数全为空；价格字段还存在 CNY/USD 未换算的问题。详细分析见 `evals/results/report.md` 的「结论」和「这份评估不能证明什么」。

## 目录结构

```text
.
├── app/                        # Agent、工作流、工具、报告生成
│   ├── agent/                  # 竞品发现、解析、核验、分析 Agent
│   ├── tools/                  # Tavily、Amazon 页面、评论采集、知识库
│   ├── workflow/               # discover → analyze → report 三段式工作流
│   ├── reporter/               # Markdown 报告生成
│   ├── data/                   # 本地知识库、向量库、评论缓存
│   └── models/                 # Pydantic 数据模型
├── backend/                    # FastAPI + MySQL + Redis/RQ
│   ├── app/db/                 # SQLAlchemy 模型与 CRUD
│   ├── app/queue/              # RQ 队列配置
│   ├── app/services/           # 任务、结果、报告、工作流服务
│   ├── app/workers/            # RQ Worker
│   └── app/routers.py          # /api 路由
├── frontend/                   # Vue 3 + Vite 前端
├── evals/                      # 10 案例离线评估
│   ├── cases.json              # 案例与预期值
│   ├── framework.py            # 指标与评分
│   ├── run_all.py / run_eval.py
│   ├── preflight.py / selftest.py
│   └── summarize.py            # 生成 CSV 和 Markdown 报告
├── docs/                       # 架构图、评估手册
├── scripts/                    # 初始化数据库、手工调试脚本
├── tests/                      # pytest 单元 / 集成 / LLM 测试
├── compose.yaml                # Worker 服务
├── docker/worker.Dockerfile
├── requirements.txt
├── main.py                     # 命令行单次分析入口（示例输入写在文件里）
└── .env.example
```

## 已知边界与后续计划

- **目标商品定位仍是主要短板**：最近一次评估中目标 ASIN 与人工标签 0/7 命中，部分案例解析到了同系列的不同 listing，另有 3 个案例的目标价格/评分/评论数为空。下一步是记录完整商品 URL、校正币种、修复评分容差的浮点边界，再重新跑同一批案例。
- **成本未量化**：`evals/pricing.json` 的单价还是 0，当前只能比较 token 数和调用次数；要报「单次分析成本」必须先填真实单价。
- **评估规模有限**：10 个案例是抽样检查，不是统计意义上的 benchmark；价格和评论数会随 Amazon 页面变化，隔几周重跑可能不一致。
- **外部依赖**：搜索、商品页面和评论采集依赖 Tavily / Bright Data / Amazon，可能受配额、反爬和网络影响。
- **部署形态**：当前 Worker 以 Docker / Linux 为主，Windows 原生 RQ Worker 未做适配；生产环境还需要补鉴权、限流、监控和重试策略。
- **还没有覆盖**：高并发、任务优先级、失败自动重试、多用户隔离、定时监控、竞品价格历史。

## 说明

- `.env` 存放真实 API Key，已在 `.gitignore` 中忽略；仓库只保留 `.env.example` 占位符。
- 评估结果和失败分析是项目的一部分，报告里的数字都可以在 `evals/results/summary.csv` 和 `report.md` 中找到。
- 如需开源，建议补充一个 `LICENSE`（例如 MIT）。
