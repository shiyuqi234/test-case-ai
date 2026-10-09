# test-case-ai

[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![test-sprint-lite](https://img.shields.io/badge/compatible-test--sprint--lite-orange)](https://github.com/shiyuqi234/test-sprint-lite)
[![CI](https://github.com/shiyuqi234/test-case-ai/actions/workflows/test.yml/badge.svg)](https://github.com/shiyuqi234/test-case-ai/actions/workflows/test.yml)

> 🤖 AI-powered test case generator — describe an API in natural language or point to an OpenAPI spec, and LLM generates production-quality YAML test cases. Supports Anthropic Claude, DeepSeek, and OpenAI.

**English** | [中文](#chinese)

---

## What is this?

**test-case-ai** bridges the gap between API documentation and automated testing. Instead of manually writing YAML test cases for [test-sprint-lite](https://github.com/shiyuqi234/test-sprint-lite), you describe what the API does — AI handles the rest.

**Two ways to use it:**
- 🖥 **CLI mode** — `tai generate` for terminal/pipeline usage
- 🌐 **Web UI mode** — `tai web` for an interactive browser-based experience

## Quick Start

```bash
# Install (CLI only)
pip install git+https://github.com/shiyuqi234/test-case-ai.git

# Or install with Web UI support
pip install "git+https://github.com/shiyuqi234/test-case-ai.git#egg=test-case-ai[web]"

# Set your API key (choose one)
export ANTHROPIC_API_KEY="sk-ant-..."      # for Claude
export DEEPSEEK_API_KEY="sk-..."           # for DeepSeek
export OPENAI_API_KEY="sk-..."             # for OpenAI

# --- CLI mode ---
tai generate --desc "POST /api/login, body: {username, password}, returns {token}" -o login.yaml
tai generate --provider deepseek --desc "GET /api/users" -o users.yaml
tai generate --openapi https://petstore.swagger.io/v2/swagger.json -o petstore.yaml

# --- Web UI mode ---
tai web                          # → opens http://127.0.0.1:8000 in your browser
tai web --port 9090              # custom port

# Pipe directly to test-sprint-lite
tai generate --desc "GET /api/users" | tsp run --file -
```

## Features

| Feature | Description |
|---|---|
| 🗣 **Natural Language** | Describe APIs in plain English — `POST /api/order with item_id and quantity` |
| 📐 **OpenAPI Spec** | Point to any Swagger/OpenAPI spec URL — auto-parses endpoints, params, schemas |
| 🧠 **Multi-Provider** | Anthropic Claude / DeepSeek / OpenAI — switch with `--provider` flag |
| 🌐 **Web UI** | `tai web` launches an interactive browser interface — presets, card view, history |
| 🔗 **tsp Compatible** | Outputs YAML that test-sprint-lite runs directly — no conversion needed |
| 📦 **Single CLI** | One `tai` command, argparse-based, familiar to anyone who uses `tsp` |

## Usage

### CLI Mode

```bash
tai generate --desc "DESCRIPTION" [OPTIONS]
tai generate --openapi URL [OPTIONS]
```

| Flag | Short | Description |
|---|---|---|
| `--desc` | `-d` | Natural language API description |
| `--openapi` | `-s` | URL to an OpenAPI / Swagger spec |
| `--output` | `-o` | Write output to file (default: stdout) |
| `--base-url` | | API base URL (auto-detected for OpenAPI) |
| `--provider` | `-p` | LLM provider: `anthropic` (default), `deepseek`, `openai` |
| `--api-key` | | API key (or set `PROVIDER_API_KEY` env var) |
| `--model` | | Model name (default: provider-dependent) |
| `--verbose` | `-v` | Print diagnostic info to stderr |

### Web UI Mode

```bash
tai web [OPTIONS]
```

| Flag | Short | Description |
|---|---|---|
| `--host` | | Host to bind (default: `127.0.0.1`) |
| `--port` | `-p` | Port to bind (default: `8000`) |

The Web UI provides:

- **Preset scenarios** — one-click fill for Login, CRUD, Order, Search, File Upload demos
- **Test case cards** — color-coded view with happy path / error / boundary classifications
- **Statistics dashboard** — test counts, category breakdown, generation time
- **YAML source view** — toggle between card view and raw YAML
- **History panel** — click to revisit past generations
- **Copy & Download** — one-click copy to clipboard or download as `.yaml`

## Example Output

```yaml
name: Login API Tests
base_url: https://api.example.com
tests:
  - id: login_success
    name: Verify successful login with valid credentials
    method: POST
    path: /api/login
    timeout: 5
    retry: 0
    headers:
      Content-Type: application/json
    json:
      username: testuser
      password: pass123
    expect:
      status_code: 200
      json:
        token: ""
        user.id: 1

  - id: login_missing_password
    name: Verify login fails when password is missing
    method: POST
    path: /api/login
    timeout: 5
    retry: 0
    headers:
      Content-Type: application/json
    json:
      username: testuser
    expect:
      status_code: 400

  - id: login_empty_body
    name: Verify login fails with empty request body
    method: POST
    path: /api/login
    timeout: 5
    retry: 0
    headers:
      Content-Type: application/json
    json: {}
    expect:
      status_code: 400
```

## How It Works

```
                ┌──────────────────────────────────┐
                │  tai web          tai generate    │
                │  (browser)        (terminal)      │
                └────────┬──────────┬───────────────┘
                         │          │
                         ▼          ▼
                    User Input (--desc / --openapi)
                              │
                              ▼
                       Prompt Builder ──── System prompt + API context
                              │
                              ▼
                  ┌─────────────────────────┐
                  │  Claude / DeepSeek /    │
                  │  OpenAI API             │
                  │  Generates test cases   │
                  └───────────┬─────────────┘
                              │
                              ▼
                       YAML Validator ─── Ensures valid tsp format
                       (auto-fix common      │
                        YAML issues)         ▼
                                    Output ─── stdout / file / browser
                                    (ready for `tsp run`)
```

Generated tests cover:
- ✅ **Happy Path** — normal requests, expected responses
- 🔲 **Boundary Cases** — edge values, empty inputs, max lengths
- ❌ **Error Scenarios** — missing fields, invalid types, auth failures
- 📊 **Data Validation** — response structure and field type checks

## Quantitative Evaluation

> Measured with DeepSeek `deepseek-chat` on 3 real OpenAPI specs; generated cases were executed by [test-sprint-lite](https://github.com/shiyuqi234/test-sprint-lite) against the live APIs.

| Spec | Endpoints | Generated cases | First-run pass rate | Generation time |
|---|---:|---:|---:|---:|
| Petstore v2 | 4 | 22 | 54.5% | 10.0s |
| Petstore v3 | 4 | 33 | 45.5% | 14.2s |
| httpbin | 5 | 38 | 92.1% | 10.2s |
| **Total** | **13** | **93** | **66.7%** | **34.4s** |

- 13 endpoints covered, 93 cases generated in a single run, **100% YAML parseable**.
- Average **2.65 s per endpoint** (vs. 8–15 min of manual authoring).
- Failure root causes across 32 failed cases: **AI assertion errors 50%**, target-API defects 41%, executor-tool defects 9% — reinforcing the "AI generates + human reviews" workflow.
- 注：httpbin 的 92.1% 是修复 [test-sprint-lite](https://github.com/shiyuqi234/test-sprint-lite) 的 `deep_get` 数组索引缺陷后复测的值（数组路径断言用例 +1 转绿）；Petstore v2/v3 因第三方 mock 服务临时返回 502 未复测。

---

<a name="chinese"></a>
## 中文说明

### 这是什么？

**test-case-ai** 是一个基于大语言模型的智能测试用例生成工具。输入 API 的自然语言描述或 OpenAPI Spec，自动生成 [test-sprint-lite](https://github.com/shiyuqi234/test-sprint-lite) 兼容的 YAML 测试用例。支持 Anthropic Claude、DeepSeek、OpenAI 三种 LLM Provider。

**两种使用方式：**
- 🖥 **命令行模式** — `tai generate`，适合终端和 CI/CD 流水线
- 🌐 **网页模式** — `tai web`，启动本地 Web 服务，浏览器可视化操作

### 安装与使用

```bash
# 安装（仅命令行）
pip install git+https://github.com/shiyuqi234/test-case-ai.git

# 或安装命令行 + 网页版
pip install "git+https://github.com/shiyuqi234/test-case-ai.git#egg=test-case-ai[web]"

# 设置 API Key（三选一）
export ANTHROPIC_API_KEY="sk-ant-..."      # Claude
export DEEPSEEK_API_KEY="sk-..."           # DeepSeek
export OPENAI_API_KEY="sk-..."             # OpenAI

# --- 命令行模式 ---
tai generate --desc "POST /api/login, body: {username, password}, returns {token}" -o login.yaml
tai generate --provider deepseek --desc "GET /api/users" -o users.yaml
tai generate --openapi https://petstore.swagger.io/v2/swagger.json -o petstore.yaml

# --- 网页模式 ---
tai web                          # 启动，浏览器自动打开 http://127.0.0.1:8000
tai web --port 9090              # 自定义端口

# 与 tsp 联动
tai generate --desc "GET /api/users" | tsp run --file -
```

### 网页版功能

| 功能 | 说明 |
|---|---|
| 🎯 **预设场景** | 一键填入登录/CRUD/下单/搜索/文件上传等常见场景 |
| 🃏 **用例卡片** | 彩色分类卡片展示（绿色=正常流程 / 红色=异常 / 黄色=边界） |
| 📊 **统计面板** | 用例总数、分类统计、生成耗时 |
| 📄 **YAML 源码** | 卡片视图和 YAML 源码一键切换 |
| 📜 **历史记录** | 右侧面板记录每次生成，点击可回溯 |

### CLI 参数

| 参数 | 简写 | 说明 |
|---|---|---|
| `--desc` | `-d` | 自然语言 API 描述 |
| `--openapi` | `-s` | OpenAPI / Swagger spec URL |
| `--output` | `-o` | 输出文件路径（默认 stdout） |
| `--base-url` | | API 基地址（OpenAPI 模式下自动检测） |
| `--provider` | `-p` | LLM 提供商：`anthropic`（默认）、`deepseek`、`openai` |
| `--api-key` | | API Key（也可设环境变量 `PROVIDER_API_KEY`） |
| `--model` | | 模型名称（留空则用 Provider 默认模型） |
| `--verbose` | `-v` | 输出诊断信息到 stderr |

### 网页模式参数

| 参数 | 简写 | 说明 |
|---|---|---|
| `--host` | | 绑定地址（默认 `127.0.0.1`） |
| `--port` | `-p` | 绑定端口（默认 `8000`） |

### 技术栈

| 层 | 选型 |
|---|---|
| LLM | Anthropic Claude / DeepSeek / OpenAI（三 Provider 可切换） |
| CLI | argparse + uvicorn |
| Web 后端 | FastAPI |
| Web 前端 | 纯 HTML + CSS + JS（零构建、零依赖） |
| 输入 | OpenAPI spec URL / 自然语言描述 |
| 输出 | test-sprint-lite 兼容 YAML |
| 测试 | 74 个 pytest + mock |
| 打包 | pyproject.toml + CLI entry_point `tai` |

### 项目结构

```
test-case-ai/
├── pyproject.toml
├── README.md
├── .github/workflows/test.yml
├── src/test_case_ai/
│   ├── __init__.py
│   ├── cli.py            # argparse CLI（generate + web 子命令）
│   ├── generator.py      # LLM 调用 + YAML 生成与自动修复
│   ├── openapi_parser.py # OpenAPI / Swagger 解析
│   ├── prompts.py        # Prompt 模板
│   ├── web.py            # FastAPI Web 应用
│   └── templates/
│       └── index.html    # Web UI 前端页面
└── tests/
    ├── conftest.py
    ├── test_cli.py
    ├── test_generator.py
    ├── test_openapi_parser.py
    └── test_web.py
```

## License

MIT — see [LICENSE](LICENSE) for details.
