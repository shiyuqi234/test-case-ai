"""Prompt templates for Claude API test case generation."""

SYSTEM_PROMPT = """You are a senior SDET (Software Development Engineer in Test).
Your job is to generate comprehensive, production-quality API test cases.

## Output Format
You MUST output valid YAML in the test-sprint-lite format. The structure is:

```yaml
name: <suite name>
base_url: <base URL>
tests:
  - id: <unique_id>
    name: <human-readable test name>
    method: GET|POST|PUT|PATCH|DELETE
    path: /api/endpoint
    timeout: 5
    retry: 0
    headers: {}
    params: {}
    json: null
    expect:
      status_code: 200
      text_contains: null
      json:
        field.name: expected_value
```

## Test Case Coverage Rules
For each API endpoint, generate test cases covering these categories:

1. **Happy Path** (至少 2 个): 正常请求，验证 200/201 + 关键返回字段
2. **Boundary / Edge** (至少 2 个): 边界值、空值、最大/最小长度、特殊字符
3. **Error / Negative** (至少 2 个): 缺少必填字段、无效类型、不存在的资源 (404)、无权限 (401/403)
4. **Data Validation** (至少 1 个): 验证返回数据的结构和类型

## Dotted Path Notation
For nested JSON assertions, use dot notation:
- `user.name` for `{"user": {"name": "..."}}`
- `data.items.0.id` for `{"data": {"items": [{"id": ...}]}}`

## Rules
- Each test `id` must be unique and snake_case
- Always set reasonable `timeout` (default 5) and `retry` (default 0, set 1 for GET)
- Include meaningful `name` that describes what the test verifies
- Output ONLY the YAML block, no extra text
- Every test must have an `expect` block with at least `status_code`
"""


def build_desc_prompt(description: str, base_url: str = "") -> str:
    """Build a user prompt for natural language API description.

    Args:
        description: Natural language description of the API.
        base_url: Optional base URL for the API.

    Returns:
        Formatted user prompt string.
    """
    base_url_line = f"\nBase URL: {base_url}" if base_url else ""
    return f"""Generate comprehensive test cases for the following API:

Description: {description}{base_url_line}

Include test cases for:
- Happy path (successful requests)
- Boundary/edge cases (extreme values, empty inputs, long strings)
- Error cases (missing fields, invalid types, auth errors, not found)
- Data validation (check response structure and field types)

Output only the YAML block."""


def build_openapi_prompt(endpoints: list[dict], base_url: str = "") -> str:
    """Build a user prompt from parsed OpenAPI endpoints.

    Args:
        endpoints: List of parsed endpoint dicts with keys:
            method, path, summary, parameters, request_body, responses
        base_url: Base URL for the API.

    Returns:
        Formatted user prompt string.
    """
    lines = ["Generate comprehensive test cases for the following API endpoints:"]
    if base_url:
        lines.append(f"\nBase URL: {base_url}")

    for ep in endpoints:
        lines.append("\n---")
        lines.append(f"{ep['method']} {ep['path']}")
        if ep.get("summary"):
            lines.append(f"  Summary: {ep['summary']}")
        if ep.get("parameters"):
            lines.append(f"  Parameters: {ep['parameters']}")
        if ep.get("request_body"):
            lines.append(f"  Request Body: {ep['request_body']}")
        if ep.get("responses"):
            lines.append(f"  Expected Responses: {ep['responses']}")

    lines.append("\n---")
    lines.append(
        "\nFor each endpoint, generate tests covering happy path, "
        "boundary cases, and error scenarios."
    )
    lines.append("Output only the YAML block.")
    return "\n".join(lines)
