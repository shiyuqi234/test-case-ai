"""OpenAPI / Swagger spec parser — extracts endpoints for test generation."""

from __future__ import annotations

import json
from typing import Any

import requests
import yaml


class OpenAPIParseError(Exception):
    """Raised when the OpenAPI spec cannot be fetched or parsed."""


def _resolve_ref(spec: dict, ref: str) -> dict:
    """Resolve a $ref pointer within an OpenAPI spec.

    Args:
        spec: The full OpenAPI spec dict.
        ref: The $ref value, e.g. '#/definitions/User'.

    Returns:
        The resolved schema dict, or a minimal dict if resolution fails.
    """
    if not ref.startswith("#/"):
        return {}
    path = ref[2:].split("/")
    current: Any = spec
    for part in path:
        current = current.get(part, {}) if isinstance(current, dict) else {}
    return current if isinstance(current, dict) else {}


def _extract_params(parameters: list[dict], spec: dict) -> str:
    """Format parameters into a human-readable string.

    Args:
        parameters: List of parameter objects from OpenAPI spec.
        spec: Full spec dict for $ref resolution.

    Returns:
        Human-readable parameter description.
    """
    parts = []
    for p in parameters:
        if "$ref" in p:
            p = _resolve_ref(spec, p["$ref"])
        name = p.get("name", "?")
        location = p.get("in", "?")
        required = "required" if p.get("required") else "optional"
        ptype = p.get("type", p.get("schema", {}).get("type", "any"))
        parts.append(f"{name} ({ptype}, {location}, {required})")
    return ", ".join(parts) if parts else "none"


def _extract_request_body(body: dict, spec: dict) -> str:
    """Format request body into a human-readable description.

    Args:
        body: Request body object (OpenAPI 3.x) or body parameter (Swagger 2.0).
        spec: Full spec dict for $ref resolution.

    Returns:
        Human-readable request body description.
    """
    if not body:
        return "none"

    # OpenAPI 3.x format: { "content": { "application/json": { "schema": {...} } } }
    if "content" in body:
        for media_type, content in body["content"].items():
            schema = content.get("schema", {})
            if "$ref" in schema:
                schema = _resolve_ref(spec, schema["$ref"])

            # Include example from schema or request body
            example = content.get("example") or schema.get("example")
            if example:
                example_str = f", example: {json.dumps(example)}"
            else:
                example_str = ""

            # Simplify: just show the required fields and example
            required = schema.get("required", [])
            props = schema.get("properties", {})
            field_descs = []
            for fname, fprop in props.items():
                ftype = fprop.get("type", "any")
                freq = "(required)" if fname in required else "(optional)"
                field_descs.append(f"{fname}: {ftype} {freq}")
            return f"{media_type}: {{{', '.join(field_descs)}}}{example_str}"
        return "request body present"

    # Swagger 2.0 body parameter
    schema = body.get("schema", {})
    if "$ref" in schema:
        schema = _resolve_ref(spec, schema["$ref"])
    required = schema.get("required", [])
    props = schema.get("properties", {})
    field_descs = []
    for fname, fprop in props.items():
        ftype = fprop.get("type", "any")
        freq = "(required)" if fname in required else "(optional)"
        field_descs.append(f"{fname}: {ftype} {freq}")
    return f"body: {{{', '.join(field_descs)}}}" if field_descs else "body (no schema details)"


def _extract_responses(responses: dict, spec: dict) -> str:
    """Format responses into a human-readable summary.

    Args:
        responses: Responses object from OpenAPI spec.
        spec: Full spec dict for $ref resolution.

    Returns:
        Human-readable response summary.
    """
    parts = []
    for code, resp in responses.items():
        description = resp.get("description", "")
        if "content" in resp:
            for media_type, mt_content in resp["content"].items():
                schema = mt_content.get("schema", {})
                if "$ref" in schema:
                    schema = _resolve_ref(spec, schema["$ref"])
                props = schema.get("properties", {})
                if props:
                    fields = ", ".join(
                        f"{k}: {v.get('type', 'any')}" for k, v in list(props.items())[:5]
                    )
                    parts.append(f"{code}: {description} (returns: {{{fields}}})")
                else:
                    parts.append(f"{code}: {description}")
        else:
            parts.append(f"{code}: {description}")
    return "; ".join(parts)


def fetch_spec(url: str, timeout: int = 30) -> dict:
    """Fetch and parse an OpenAPI/Swagger spec from a URL.

    Supports both JSON and YAML specs.

    Args:
        url: URL to the OpenAPI spec.
        timeout: Request timeout in seconds.

    Returns:
        Parsed spec dict.

    Raises:
        OpenAPIParseError: If the spec cannot be fetched or parsed.
    """
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise OpenAPIParseError(f"Failed to fetch spec from {url}: {e}") from e

    content_type = resp.headers.get("content-type", "").lower()
    text = resp.text

    try:
        if "yaml" in content_type or "x-yaml" in content_type:
            return yaml.safe_load(text)
        # Try JSON first, fall back to YAML
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return yaml.safe_load(text)
    except (yaml.YAMLError, ValueError) as e:
        raise OpenAPIParseError(f"Failed to parse spec from {url}: {e}") from e


def parse_endpoints(spec: dict) -> list[dict]:
    """Extract API endpoints from a parsed OpenAPI spec.

    Supports OpenAPI 3.x and Swagger 2.0.

    Args:
        spec: Parsed OpenAPI spec dict.

    Returns:
        List of endpoint dicts with keys: method, path, summary, parameters,
        request_body, responses.

    Raises:
        OpenAPIParseError: If the spec structure is unrecognized.
    """
    # Detect version
    is_v3 = spec.get("openapi", "").startswith("3.")
    is_v2 = spec.get("swagger", "").startswith("2.")

    if not is_v3 and not is_v2:
        raise OpenAPIParseError(
            "Unrecognized spec format. Expected 'openapi' (3.x) or 'swagger' (2.x) key."
        )

    paths = spec.get("paths", {})
    if not paths:
        raise OpenAPIParseError("No 'paths' found in spec.")

    http_methods = {"get", "post", "put", "patch", "delete", "options", "head"}
    endpoints = []

    for path_url, path_item in paths.items():
        for method in http_methods:
            operation = path_item.get(method)
            if not operation:
                continue

            summary = operation.get("summary", "")
            params_raw = operation.get("parameters", [])
            params = _extract_params(params_raw, spec)

            # Request body
            request_body_raw = operation.get("requestBody", {})
            request_body = _extract_request_body(request_body_raw, spec)

            # Responses
            responses_raw = operation.get("responses", {})
            responses = _extract_responses(responses_raw, spec)

            endpoints.append({
                "method": method.upper(),
                "path": path_url,
                "summary": summary,
                "parameters": params,
                "request_body": request_body,
                "responses": responses,
            })

    return endpoints


def get_base_url(spec: dict) -> str:
    """Extract the base URL from an OpenAPI spec.

    Args:
        spec: Parsed OpenAPI spec dict.

    Returns:
        Base URL string, or empty string if not found.
    """
    # OpenAPI 3.x: servers[0].url
    servers = spec.get("servers", [])
    if servers:
        url = servers[0].get("url", "")
        # Resolve template variables with their defaults
        for var, var_def in servers[0].get("variables", {}).items():
            default = var_def.get("default", var)
            url = url.replace(f"{{{var}}}", default)
        return url

    # Swagger 2.0: host + basePath + schemes
    host = spec.get("host", "")
    base_path = spec.get("basePath", "")
    schemes = spec.get("schemes", ["https"])
    if host:
        return f"{schemes[0]}://{host}{base_path}"

    return ""
