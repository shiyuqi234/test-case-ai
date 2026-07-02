# test-case-ai

[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![test-sprint-lite](https://img.shields.io/badge/compatible-test--sprint--lite-orange)](https://github.com/shiyuqi234/test-sprint-lite)

> 🤖 AI-powered test case generator — describe an API in natural language or point to an OpenAPI spec, and Claude generates production-quality test cases in YAML.

**English** | [中文](#chinese)

---

## What is this?

**test-case-ai** bridges the gap between API documentation and automated testing. Instead of manually writing YAML test cases for [test-sprint-lite](https://github.com/shiyuqi234/test-sprint-lite), you describe what the API does — Claude handles the rest.

## Quick Start

```bash
# Install
pip install git+https://github.com/shiyuqi234/test-case-ai.git

# Set your API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Generate test cases from natural language
tai generate --desc "POST /api/login, body: {username, password}, returns {token}" -o login.yaml

# Generate from an OpenAPI spec
tai generate --openapi https://petstore.swagger.io/v2/swagger.json -o petstore.yaml

# Pipe directly to test-sprint-lite
tai generate --desc "GET /api/users" | tsp run --file -
```

## Features

| Feature | Description |
|---|---|
| 🗣 **Natural Language** | Describe APIs in plain English — `POST /api/order with item_id and quantity` |
| 📐 **OpenAPI Spec** | Point to any Swagger/OpenAPI spec URL — auto-parses endpoints, params, schemas |
| 🧠 **Claude-Powered** | Uses Claude API to reason about edge cases, boundaries, and error scenarios |
| 🔗 **tsp Compatible** | Outputs YAML that test-sprint-lite runs directly — no conversion needed |
| 📦 **Single CLI** | One `tai` command, argparse-based, familiar to anyone who uses `tsp` |

## Usage

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
| `--api-key` | | Anthropic API key (or set `ANTHROPIC_API_KEY`) |
| `--model` | | Claude model (default: `claude-sonnet-5`) |
| `--verbose` | `-v` | Print diagnostic info to stderr |

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
User Input (--desc / --openapi)
         │
         ▼
   Prompt Builder ──── System prompt + API context
         │
         ▼
   Claude API ─────── Generates comprehensive test cases
         │
         ▼
   YAML Validator ─── Ensures valid test-sprint-lite format
         │
         ▼
   Output ─────────── stdout or file (ready for `tsp run`)
```

Generated tests cover:
- ✅ **Happy Path** — normal requests, expected responses
- 🔲 **Boundary Cases** — edge values, empty inputs, max lengths
- ❌ **Error Scenarios** — missing fields, invalid types, auth failures
- 📊 **Data Validation** — response structure and field type checks

---

<a name="chinese"></a>
## 中文说明

### 这是什么？

**test-case-ai** 是一个基于 Claude API 的智能测试用例生成工具。输入 API 的自然语言描述或 OpenAPI Spec，自动生成 [test-sprint-lite](https://github.com/shiyuqi234/test-sprint-lite) 兼容的 YAML 测试用例。

### 安装与使用

```bash
pip install git+https://github.com/shiyuqi234/test-case-ai.git
export ANTHROPIC_API_KEY="sk-ant-..."

# 自然语言生成
tai generate --desc "POST /api/login, body: {username, password}, returns {token}" -o login.yaml

# OpenAPI spec 生成
tai generate --openapi https://petstore.swagger.io/v2/swagger.json -o petstore.yaml

# 与 tsp 联动
tai generate --desc "GET /api/users" | tsp run --file -
```

### 技术栈

| 层 | 选型 |
|---|---|
| LLM | Claude API (anthropic SDK) |
| CLI | argparse |
| 输入 | OpenAPI spec URL / 自然语言描述 |
| 输出 | test-sprint-lite 兼容 YAML |
| 测试 | pytest + mock |
| 打包 | pyproject.toml + CLI entry_point `tai` |

### 项目结构

```
test-case-ai/
├── pyproject.toml
├── README.md
├── .github/workflows/test.yml
├── src/test_case_ai/
│   ├── __init__.py
│   ├── cli.py            # argparse CLI
│   ├── generator.py      # Claude API 调用 + YAML 生成
│   ├── openapi_parser.py # OpenAPI spec 解析
│   └── prompts.py        # Prompt 模板
└── tests/
    ├── conftest.py
    ├── test_cli.py
    ├── test_generator.py
    └── test_openapi_parser.py
```

## License

MIT — see [LICENSE](LICENSE) for details.
