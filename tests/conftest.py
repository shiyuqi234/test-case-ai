"""Shared test fixtures for test-case-ai."""

import pytest

# Sample valid YAML output from Claude
SAMPLE_YAML = """name: Login API Tests
base_url: https://api.example.com
tests:
  - id: login_success
    name: Verify successful login
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
    name: Verify login fails without password
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
      json:
        error: ""

  - id: login_empty_body
    name: Verify login fails with empty body
    method: POST
    path: /api/login
    timeout: 5
    retry: 0
    headers:
      Content-Type: application/json
    json: {}
    expect:
      status_code: 400
"""


SAMPLE_OPENAPI_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "Petstore", "version": "1.0.0"},
    "servers": [{"url": "https://petstore.example.com/v1"}],
    "paths": {
        "/pets": {
            "get": {
                "summary": "List all pets",
                "parameters": [
                    {"name": "limit", "in": "query", "required": False,
                     "schema": {"type": "integer"}}
                ],
                "responses": {
                    "200": {"description": "A list of pets"},
                },
            },
            "post": {
                "summary": "Create a pet",
                "requestBody": {
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
                },
                "responses": {
                    "201": {"description": "Pet created"},
                    "400": {"description": "Invalid input"},
                },
            },
        },
        "/pets/{petId}": {
            "get": {
                "summary": "Get a pet by ID",
                "parameters": [
                    {"name": "petId", "in": "path", "required": True,
                     "schema": {"type": "integer"}},
                ],
                "responses": {
                    "200": {"description": "Pet found"},
                    "404": {"description": "Pet not found"},
                },
            },
        },
    },
}


@pytest.fixture
def sample_openapi_spec():
    """Return a sample OpenAPI 3.0 spec dict."""
    return SAMPLE_OPENAPI_SPEC


@pytest.fixture
def sample_yaml():
    """Return a sample valid YAML string."""
    return SAMPLE_YAML


# Mock Claude API response class
class MockContent:
    def __init__(self, text: str):
        self.text = text


class MockMessage:
    def __init__(self, text: str):
        self.content = [MockContent(text)]


class MockMessages:
    def create(self, **kwargs):
        return MockMessage(SAMPLE_YAML)
