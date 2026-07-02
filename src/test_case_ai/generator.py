"""Core generator: calls Claude API and produces test-sprint-lite YAML."""

import os
import re

import yaml
from anthropic import Anthropic

from .prompts import SYSTEM_PROMPT, build_desc_prompt, build_openapi_prompt


def _extract_yaml(text: str) -> str:
    """Extract YAML block from Claude's response, stripping markdown fences.

    Args:
        text: Raw response text from Claude.

    Returns:
        Clean YAML string.
    """
    # Try to extract ```yaml ... ``` block first
    match = re.search(r"```(?:yaml)?\s*\n?(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Fallback: return the whole text if no fences found
    return text.strip()


def _validate_yaml(yaml_str: str) -> dict:
    """Validate that the YAML string is parseable and has the expected structure.

    Args:
        yaml_str: YAML string to validate.

    Returns:
        Parsed YAML dict.

    Raises:
        ValueError: If YAML is invalid or missing required fields.
    """
    try:
        data = yaml.safe_load(yaml_str)
    except yaml.YAMLError as e:
        raise ValueError(f"Claude returned invalid YAML: {e}") from e

    if not isinstance(data, dict):
        raise ValueError("Claude returned unexpected output type, expected a YAML mapping")

    if "tests" not in data:
        raise ValueError("Generated YAML is missing the 'tests' field")
    if not isinstance(data["tests"], list):
        raise ValueError("'tests' field must be a list")
    if len(data["tests"]) == 0:
        raise ValueError("Generated YAML contains no test cases")

    return data


def generate(description: str, base_url: str = "", api_key: str = "",
             model: str = "claude-sonnet-5") -> str:
    """Generate test cases from a natural language API description.

    Args:
        description: Natural language description of the API.
        base_url: Optional base URL for the API.
        api_key: Anthropic API key. Reads ANTHROPIC_API_KEY env var if empty.
        model: Claude model to use.

    Returns:
        YAML string of generated test cases.

    Raises:
        ValueError: If API key is missing or response is invalid.
    """
    api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY is required. Set it as an environment variable "
            "or pass `api_key` to this function."
        )

    client = Anthropic(api_key=api_key)
    user_prompt = build_desc_prompt(description, base_url)

    message = client.messages.create(
        model=model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = message.content[0].text
    yaml_str = _extract_yaml(raw)
    _validate_yaml(yaml_str)  # raise if invalid
    return yaml_str


def generate_from_openapi(endpoints: list[dict], base_url: str = "",
                          api_key: str = "", model: str = "claude-sonnet-5") -> str:
    """Generate test cases from parsed OpenAPI endpoints.

    Args:
        endpoints: List of parsed endpoint dicts from openapi_parser.
        base_url: Base URL for the API.
        api_key: Anthropic API key. Reads ANTHROPIC_API_KEY env var if empty.
        model: Claude model to use.

    Returns:
        YAML string of generated test cases.
    """
    api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY is required. Set it as an environment variable "
            "or pass `api_key` to this function."
        )

    client = Anthropic(api_key=api_key)
    user_prompt = build_openapi_prompt(endpoints, base_url)

    message = client.messages.create(
        model=model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = message.content[0].text
    yaml_str = _extract_yaml(raw)
    _validate_yaml(yaml_str)
    return yaml_str
