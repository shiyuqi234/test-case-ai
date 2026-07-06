"""Core generator: calls LLM APIs and produces test-sprint-lite YAML."""

import os
import re

import yaml

from .prompts import SYSTEM_PROMPT, build_desc_prompt, build_openapi_prompt

# Provider configuration
PROVIDERS = {
    "anthropic": {
        "default_model": "claude-sonnet-5",
        "env_var": "ANTHROPIC_API_KEY",
        "label": "Anthropic Claude",
    },
    "deepseek": {
        "default_model": "deepseek-chat",
        "env_var": "DEEPSEEK_API_KEY",
        "label": "DeepSeek",
    },
    "openai": {
        "default_model": "gpt-4o",
        "env_var": "OPENAI_API_KEY",
        "label": "OpenAI",
    },
}


def _extract_yaml(text: str) -> str:
    """Extract YAML block from LLM response, stripping markdown fences."""
    match = re.search(r"```(?:yaml)?\s*\n?(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def _validate_yaml(yaml_str: str) -> dict:
    """Validate that the YAML string is parseable and has the expected structure.

    Raises:
        ValueError: If YAML is invalid or missing required fields.
    """
    data = None
    errors = []

    # Try original first
    try:
        data = yaml.safe_load(yaml_str)
    except yaml.YAMLError as e:
        errors.append(f"original: {e}")

    # If failed, try auto-fixing common issues
    if data is None:
        fixed = _fix_common_yaml_issues(yaml_str)
        try:
            data = yaml.safe_load(fixed)
        except yaml.YAMLError as e:
            errors.append(f"after auto-fix: {e}")

    if data is None:
        preview = yaml_str[:800] + ("..." if len(yaml_str) > 800 else "")
        msg = "LLM returned invalid YAML"
        if errors:
            msg += " — " + "; ".join(errors)
        msg += f"\n\nRaw output (first 800 chars):\n{preview}"
        raise ValueError(msg)

    if not isinstance(data, dict):
        raise ValueError("LLM returned unexpected output type, expected a YAML mapping")

    if "tests" not in data:
        raise ValueError("Generated YAML is missing the 'tests' field")
    if not isinstance(data["tests"], list):
        raise ValueError("'tests' field must be a list")
    if len(data["tests"]) == 0:
        raise ValueError("Generated YAML contains no test cases")

    return data


def _fix_common_yaml_issues(yaml_str: str) -> str:
    """Attempt to fix common YAML issues in LLM output.

    - Replace unescaped double quotes inside double-quoted scalar values
    """
    import re

    # Pattern: a line like "  field: "value with "unescaped" quotes""
    # Strategy: find lines where a YAML value starts and ends with double quotes
    # but contains interior double quotes that aren't escaped.
    fixed_lines = []
    for line in yaml_str.split("\n"):
        # Match: leading spaces + key + ": " + double-quoted value
        m = re.match(r'^(\s+)([\w.]+:\s*)"(.+)"$', line)
        if m and '"' in m.group(3):
            # Interior unescaped double quotes found
            indent = m.group(1)
            key = m.group(2)
            inner = m.group(3)
            # Escape interior double quotes
            inner_escaped = inner.replace('"', '\\"')
            fixed_lines.append(f'{indent}{key}"{inner_escaped}"')
        else:
            fixed_lines.append(line)

    return "\n".join(fixed_lines)


def _get_api_key(provider: str, api_key: str = "") -> str:
    """Resolve API key from argument or environment variable.

    Raises:
        ValueError: If no API key is available.
    """
    config = PROVIDERS.get(provider, PROVIDERS["anthropic"])
    key = api_key or os.getenv(config["env_var"], "")
    if not key:
        raise ValueError(
            f"{config['env_var']} is required for {config['label']}. "
            f"Set it as an environment variable or pass `api_key`."
        )
    return key


def _call_deepseek(user_prompt: str, system_prompt: str, model: str, api_key: str) -> str:
    """Call DeepSeek API (OpenAI-compatible) and return response text."""
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    response = client.chat.completions.create(
        model=model,
        max_tokens=4096,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content or ""


def _call_openai(user_prompt: str, system_prompt: str, model: str, api_key: str) -> str:
    """Call OpenAI API and return response text."""
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        max_tokens=4096,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content or ""


def _call_anthropic(user_prompt: str, system_prompt: str, model: str, api_key: str) -> str:
    """Call Anthropic Claude API and return response text."""
    from anthropic import Anthropic

    client = Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text


_LLM_CALLS = {
    "anthropic": _call_anthropic,
    "deepseek": _call_deepseek,
    "openai": _call_openai,
}


def _call_llm(provider: str, user_prompt: str, model: str, api_key: str) -> str:
    """Dispatch to the correct LLM provider and return the response text."""
    call_fn = _LLM_CALLS.get(provider, _LLM_CALLS["anthropic"])
    return call_fn(user_prompt, SYSTEM_PROMPT, model, api_key)


def generate(
    description: str,
    base_url: str = "",
    api_key: str = "",
    model: str = "",
    provider: str = "anthropic",
) -> str:
    """Generate test cases from a natural language API description.

    Args:
        description: Natural language API description.
        base_url: Optional base URL.
        api_key: API key. Falls back to provider-specific env var.
        model: Model name. Falls back to provider default.
        provider: One of "anthropic", "deepseek", "openai".

    Returns:
        YAML string of generated test cases.
    """
    config = PROVIDERS.get(provider, PROVIDERS["anthropic"])
    model = model or config["default_model"]
    api_key = _get_api_key(provider, api_key)
    user_prompt = build_desc_prompt(description, base_url)

    raw = _call_llm(provider, user_prompt, model, api_key)
    yaml_str = _extract_yaml(raw)
    _validate_yaml(yaml_str)
    return yaml_str


def generate_from_openapi(
    endpoints: list[dict],
    base_url: str = "",
    api_key: str = "",
    model: str = "",
    provider: str = "anthropic",
) -> str:
    """Generate test cases from parsed OpenAPI endpoints.

    Args:
        endpoints: List of parsed endpoint dicts from openapi_parser.
        base_url: Base URL for the API.
        api_key: API key. Falls back to provider-specific env var.
        model: Model name. Falls back to provider default.
        provider: One of "anthropic", "deepseek", "openai".

    Returns:
        YAML string of generated test cases.
    """
    config = PROVIDERS.get(provider, PROVIDERS["anthropic"])
    model = model or config["default_model"]
    api_key = _get_api_key(provider, api_key)
    user_prompt = build_openapi_prompt(endpoints, base_url)

    raw = _call_llm(provider, user_prompt, model, api_key)
    yaml_str = _extract_yaml(raw)
    _validate_yaml(yaml_str)
    return yaml_str
