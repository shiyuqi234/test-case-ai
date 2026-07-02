"""Tests for the OpenAPI parser module."""

import json
from unittest import mock

import pytest

from test_case_ai.openapi_parser import (
    OpenAPIParseError,
    _extract_params,
    _extract_request_body,
    _extract_responses,
    _resolve_ref,
    fetch_spec,
    get_base_url,
    parse_endpoints,
)


class TestResolveRef:
    def test_resolves_reference(self):
        spec = {
            "definitions": {
                "User": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                }
            }
        }
        result = _resolve_ref(spec, "#/definitions/User")
        assert result["type"] == "object"
        assert "properties" in result

    def test_returns_empty_on_non_local_ref(self):
        result = _resolve_ref({}, "http://external.com/schema.json")
        assert result == {}

    def test_returns_empty_on_missing_ref(self):
        result = _resolve_ref({}, "#/definitions/NotFound")
        assert result == {}


class TestExtractParams:
    def test_formats_parameters(self):
        params = [
            {"name": "limit", "in": "query", "required": False, "type": "integer"},
            {"name": "petId", "in": "path", "required": True, "type": "integer"},
        ]
        result = _extract_params(params, {})
        assert "limit" in result
        assert "integer" in result
        assert "required" in result
        assert "optional" in result

    def test_resolves_param_refs(self):
        spec = {
            "parameters": {
                "petIdParam": {
                    "name": "petId",
                    "in": "path",
                    "required": True,
                    "type": "integer",
                }
            }
        }
        params = [{"$ref": "#/parameters/petIdParam"}]
        result = _extract_params(params, spec)
        assert "petId" in result
        assert "required" in result

    def test_empty_params(self):
        assert _extract_params([], {}) == "none"


class TestExtractRequestBody:
    def test_none_body(self):
        assert _extract_request_body({}, {}) == "none"

    def test_openapi_v3_body(self):
        body = {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "required": ["name"],
                        "properties": {
                            "name": {"type": "string"},
                            "tag": {"type": "string"},
                        },
                    }
                }
            }
        }
        result = _extract_request_body(body, {})
        assert "application/json" in result
        assert "name: string" in result
        assert "(required)" in result
        assert "tag: string" in result
        assert "(optional)" in result

    def test_empty_body_dict(self):
        assert _extract_request_body(None, {}) == "none"


class TestExtractResponses:
    def test_formats_responses(self):
        responses = {
            "200": {"description": "Success"},
            "404": {"description": "Not found"},
        }
        result = _extract_responses(responses, {})
        assert "200: Success" in result
        assert "404: Not found" in result


class TestFetchSpec:
    def test_fetches_json_spec(self):
        spec_data = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }
        mock_response = mock.MagicMock()
        mock_response.headers = {"content-type": "application/json"}
        mock_response.text = json.dumps(spec_data)
        mock_response.raise_for_status = mock.MagicMock()

        with mock.patch("test_case_ai.openapi_parser.requests.get", return_value=mock_response):
            result = fetch_spec("https://example.com/openapi.json")
            assert result["openapi"] == "3.0.0"

    def test_fetches_yaml_spec(self):
        mock_response = mock.MagicMock()
        mock_response.headers = {"content-type": "text/yaml"}
        mock_response.text = "openapi: 3.0.0\ninfo:\n  title: Test\n  version: 1.0.0\npaths: {}"
        mock_response.raise_for_status = mock.MagicMock()

        with mock.patch("test_case_ai.openapi_parser.requests.get", return_value=mock_response):
            result = fetch_spec("https://example.com/openapi.yaml")
            assert result["openapi"] == "3.0.0"

    def test_raises_on_http_error(self):
        import requests as req_lib
        mock_response = mock.MagicMock()
        mock_response.raise_for_status.side_effect = req_lib.HTTPError("404 Not Found")

        with mock.patch("test_case_ai.openapi_parser.requests.get", return_value=mock_response):
            with pytest.raises(OpenAPIParseError, match="Failed to fetch"):
                fetch_spec("https://example.com/notfound")


class TestParseEndpoints:
    def test_parses_openapi_v3(self, sample_openapi_spec):
        endpoints = parse_endpoints(sample_openapi_spec)
        assert len(endpoints) == 3  # GET /pets, POST /pets, GET /pets/{petId}

        methods_paths = {(ep["method"], ep["path"]) for ep in endpoints}
        assert ("GET", "/pets") in methods_paths
        assert ("POST", "/pets") in methods_paths
        assert ("GET", "/pets/{petId}") in methods_paths

    def test_parses_swagger_v2(self):
        spec = {
            "swagger": "2.0",
            "info": {"title": "Test", "version": "1.0"},
            "host": "api.example.com",
            "basePath": "/v2",
            "paths": {
                "/users": {
                    "get": {
                        "summary": "List users",
                        "responses": {"200": {"description": "OK"}},
                    },
                },
            },
        }
        endpoints = parse_endpoints(spec)
        assert len(endpoints) == 1
        assert endpoints[0]["method"] == "GET"
        assert endpoints[0]["path"] == "/users"

    def test_skips_non_http_methods(self):
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0"},
            "paths": {
                "/users": {
                    "x-custom": {},
                    "parameters": [],
                },
            },
        }
        endpoints = parse_endpoints(spec)
        assert endpoints == []

    def test_raises_on_unrecognized_format(self):
        spec = {"info": {"title": "Test"}}
        with pytest.raises(OpenAPIParseError, match="Unrecognized spec"):
            parse_endpoints(spec)

    def test_raises_on_no_paths(self):
        spec = {"openapi": "3.0.0", "info": {"title": "Test", "version": "1.0"}}
        with pytest.raises(OpenAPIParseError, match="No 'paths'"):
            parse_endpoints(spec)


class TestGetBaseUrl:
    def test_openapi_v3(self):
        spec = {"servers": [{"url": "https://api.example.com/v2"}]}
        assert get_base_url(spec) == "https://api.example.com/v2"

    def test_openapi_v3_with_variables(self):
        spec = {
            "servers": [{
                "url": "https://{subdomain}.example.com/{basePath}",
                "variables": {
                    "subdomain": {"default": "api"},
                    "basePath": {"default": "v1"},
                },
            }],
        }
        assert get_base_url(spec) == "https://api.example.com/v1"

    def test_swagger_v2(self):
        spec = {"host": "api.example.com", "basePath": "/v1", "schemes": ["http"]}
        assert get_base_url(spec) == "http://api.example.com/v1"

    def test_empty_when_no_servers_or_host(self):
        assert get_base_url({}) == ""
