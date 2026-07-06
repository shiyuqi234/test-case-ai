"""Tests for the FastAPI web module."""

from unittest import mock

import pytest

from test_case_ai.web import app

# Skip all tests if fastapi is not installed (graceful for CI without [web] deps)
pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402, I001

client = TestClient(app)

# Short mock YAML used across tests
MOCK_YAML = "name: Test\ntests:\n  - id: t1\n    method: GET\n    path: /test\n    expect:\n      status_code: 200"  # noqa: E501
MOCK_PETSTORE_YAML = (
    "name: Petstore\n"
    "tests:\n"
    "  - id: list_pets\n"
    "    method: GET\n"
    "    path: /pets\n"
    "    expect:\n"
    "      status_code: 200"
)


class TestIndex:
    """Tests for the GET / endpoint."""

    def test_index_returns_html(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_index_contains_expected_content(self):
        response = client.get("/")
        html = response.text
        assert "Test Case AI" in html
        assert "generate-btn" in html
        assert "yaml-output" in html
        assert "desc-input" in html
        assert "openapi-url-input" in html


class TestApiGenerateDesc:
    """Tests for POST /api/generate with input_type=desc."""

    def test_generate_desc_success(self):
        with mock.patch("test_case_ai.web.generate") as mock_gen:
            mock_gen.return_value = MOCK_YAML

            payload = {
                "input_type": "desc",
                "description": "GET /api/test returns a list",
                "provider": "anthropic",
                "api_key": "test-key",
            }
            response = client.post("/api/generate", json=payload)
            data = response.json()

            assert response.status_code == 200
            assert data["success"] is True
            assert "name: Test" in data["yaml"]
            assert "tests:" in data["yaml"]
            mock_gen.assert_called_once()

    def test_generate_desc_with_openai_provider(self):
        with mock.patch("test_case_ai.web.generate") as mock_gen:
            mock_gen.return_value = MOCK_YAML

            payload = {
                "input_type": "desc",
                "description": "GET /x",
                "provider": "openai",
                "api_key": "sk-oai",
                "model": "gpt-4o",
                "base_url": "https://api.example.com",
            }
            response = client.post("/api/generate", json=payload)
            data = response.json()

            assert data["success"] is True
            call_kwargs = mock_gen.call_args[1]
            assert call_kwargs["provider"] == "openai"
            assert call_kwargs["api_key"] == "sk-oai"
            assert call_kwargs["model"] == "gpt-4o"
            assert call_kwargs["base_url"] == "https://api.example.com"

    def test_generate_desc_error_missing_api_key(self):
        with mock.patch("test_case_ai.web.generate") as mock_gen:
            mock_gen.side_effect = ValueError("ANTHROPIC_API_KEY is required")

            payload = {
                "input_type": "desc",
                "description": "GET /test",
                "provider": "anthropic",
                "api_key": "",
            }
            response = client.post("/api/generate", json=payload)
            data = response.json()

            assert response.status_code == 200
            assert data["success"] is False
            assert "ANTHROPIC_API_KEY" in data["error"]

    def test_generate_desc_invalid_yaml_error(self):
        with mock.patch("test_case_ai.web.generate") as mock_gen:
            mock_gen.side_effect = ValueError("LLM returned invalid YAML")

            payload = {
                "input_type": "desc",
                "description": "GET /test",
                "provider": "anthropic",
                "api_key": "test-key",
            }
            response = client.post("/api/generate", json=payload)
            data = response.json()

            assert data["success"] is False
            assert "invalid YAML" in data["error"]

    def test_generate_desc_empty_model_uses_default(self):
        with mock.patch("test_case_ai.web.generate") as mock_gen:
            mock_gen.return_value = MOCK_YAML

            payload = {
                "input_type": "desc",
                "description": "GET /test",
                "provider": "anthropic",
                "api_key": "test-key",
                "model": "",
            }
            response = client.post("/api/generate", json=payload)
            data = response.json()

            assert data["success"] is True
            assert mock_gen.call_args[1]["model"] == ""


class TestApiGenerateOpenapi:
    """Tests for POST /api/generate with input_type=openapi."""

    def test_generate_openapi_success(self):
        with mock.patch("test_case_ai.openapi_parser.fetch_spec") as mock_fetch, \
             mock.patch("test_case_ai.openapi_parser.parse_endpoints") as mock_parse, \
             mock.patch("test_case_ai.openapi_parser.get_base_url") as mock_get_url, \
             mock.patch("test_case_ai.web.generate_from_openapi") as mock_gen:
            mock_fetch.return_value = {"openapi": "3.0.0", "paths": {}}
            mock_parse.return_value = [
                {
                    "method": "GET", "path": "/pets", "summary": "List pets",
                    "parameters": "none", "request_body": "none",
                    "responses": "200: OK",
                }
            ]
            mock_get_url.return_value = "https://petstore.example.com/v1"
            mock_gen.return_value = MOCK_PETSTORE_YAML

            payload = {
                "input_type": "openapi",
                "openapi_url": "https://example.com/openapi.json",
                "provider": "anthropic",
                "api_key": "test-key",
            }
            response = client.post("/api/generate", json=payload)
            data = response.json()

            assert response.status_code == 200
            assert data["success"] is True
            assert "name: Petstore" in data["yaml"]
            mock_fetch.assert_called_once_with("https://example.com/openapi.json")
            mock_gen.assert_called_once()

    def test_generate_openapi_with_explicit_base_url(self):
        with mock.patch("test_case_ai.openapi_parser.fetch_spec") as mock_fetch, \
             mock.patch("test_case_ai.openapi_parser.parse_endpoints") as mock_parse, \
             mock.patch("test_case_ai.web.generate_from_openapi") as mock_gen:
            mock_fetch.return_value = {"openapi": "3.0.0", "paths": {}}
            mock_parse.return_value = []
            mock_gen.return_value = MOCK_YAML

            payload = {
                "input_type": "openapi",
                "openapi_url": "https://example.com/openapi.json",
                "provider": "anthropic",
                "api_key": "test-key",
                "base_url": "https://custom.example.com",
            }
            response = client.post("/api/generate", json=payload)
            data = response.json()

            assert data["success"] is True
            call_kwargs = mock_gen.call_args[1]
            assert call_kwargs["base_url"] == "https://custom.example.com"

    def test_generate_openapi_with_deepseek_provider(self):
        with mock.patch("test_case_ai.openapi_parser.fetch_spec") as mock_fetch, \
             mock.patch("test_case_ai.openapi_parser.parse_endpoints") as mock_parse, \
             mock.patch("test_case_ai.openapi_parser.get_base_url") as mock_get_url, \
             mock.patch("test_case_ai.web.generate_from_openapi") as mock_gen:
            mock_fetch.return_value = {"openapi": "3.0.0", "paths": {}}
            mock_parse.return_value = []
            mock_get_url.return_value = ""
            mock_gen.return_value = MOCK_YAML

            payload = {
                "input_type": "openapi",
                "openapi_url": "https://example.com/openapi.json",
                "provider": "deepseek",
                "api_key": "ds-key",
                "model": "deepseek-chat",
            }
            response = client.post("/api/generate", json=payload)
            data = response.json()

            assert data["success"] is True
            call_kwargs = mock_gen.call_args[1]
            assert call_kwargs["provider"] == "deepseek"
            assert call_kwargs["api_key"] == "ds-key"

    def test_generate_openapi_fetch_error(self):
        from test_case_ai.openapi_parser import OpenAPIParseError

        with mock.patch("test_case_ai.openapi_parser.fetch_spec") as mock_fetch:
            mock_fetch.side_effect = OpenAPIParseError("Failed to fetch spec: 404")

            payload = {
                "input_type": "openapi",
                "openapi_url": "https://example.com/notfound",
                "provider": "anthropic",
                "api_key": "test-key",
            }
            response = client.post("/api/generate", json=payload)
            data = response.json()

            assert data["success"] is False
            assert "404" in data["error"]

    def test_generate_openapi_parse_error(self):
        from test_case_ai.openapi_parser import OpenAPIParseError

        with mock.patch("test_case_ai.openapi_parser.fetch_spec") as mock_fetch:
            mock_fetch.return_value = {"some": "junk"}
            with mock.patch(
                "test_case_ai.openapi_parser.parse_endpoints"
            ) as mock_parse:
                mock_parse.side_effect = OpenAPIParseError(
                    "Unrecognized spec format"
                )

                payload = {
                    "input_type": "openapi",
                    "openapi_url": "https://example.com/bad.json",
                    "provider": "anthropic",
                    "api_key": "test-key",
                }
                response = client.post("/api/generate", json=payload)
                data = response.json()

                assert data["success"] is False
                assert "Unrecognized spec" in data["error"]


class TestApiGenerateDefaults:
    """Tests for default request values."""

    def test_default_input_type_is_desc(self):
        with mock.patch("test_case_ai.web.generate") as mock_gen:
            mock_gen.return_value = MOCK_YAML

            # Omit input_type entirely
            response = client.post("/api/generate", json={
                "description": "GET /test",
                "api_key": "test-key",
            })
            data = response.json()
            assert data["success"] is True

    def test_default_provider_is_anthropic(self):
        with mock.patch("test_case_ai.web.generate") as mock_gen:
            mock_gen.return_value = MOCK_YAML

            response = client.post("/api/generate", json={
                "description": "GET /test",
                "api_key": "test-key",
            })
            data = response.json()
            assert data["success"] is True
            assert mock_gen.call_args[1]["provider"] == "anthropic"
