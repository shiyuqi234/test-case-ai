"""Tests for the generator module."""

from unittest import mock

import pytest

from test_case_ai.generator import (
    _extract_yaml,
    _get_api_key,
    _validate_yaml,
    generate,
    generate_from_openapi,
)


class TestExtractYaml:
    def test_extract_fenced_yaml_block(self):
        text = (
            '```yaml\nname: Test\nbase_url: https://api.example.com\ntests: []\n```'
        )
        result = _extract_yaml(text)
        assert result == 'name: Test\nbase_url: https://api.example.com\ntests: []'

    def test_extract_fenced_block_without_lang(self):
        text = '```\nname: Test\ntests: []\n```'
        result = _extract_yaml(text)
        assert result == 'name: Test\ntests: []'

    def test_extract_no_fences_returns_original(self):
        text = 'name: Test\ntests: []'
        result = _extract_yaml(text)
        assert result == text

    def test_extract_multiple_fence_blocks_returns_first(self):
        text = (
            '```yaml\nname: First\ntests: []\n```\n'
            '```yaml\nname: Second\ntests: []\n```'
        )
        result = _extract_yaml(text)
        assert 'First' in result
        assert 'Second' not in result


class TestValidateYaml:
    def test_valid_yaml_passes(self):
        yaml_str = (
            'name: Test\nbase_url: https://api.example.com\n'
            'tests:\n  - id: t1\n    method: GET\n    path: /test\n'
            '    expect:\n      status_code: 200'
        )
        data = _validate_yaml(yaml_str)
        assert data['name'] == 'Test'
        assert len(data['tests']) == 1

    def test_invalid_yaml_raises(self):
        with pytest.raises(ValueError, match="invalid YAML"):
            _validate_yaml('name: Test\ntests: [unclosed')

    def test_missing_tests_raises(self):
        with pytest.raises(ValueError, match="missing the 'tests' field"):
            _validate_yaml('name: Test\nbase_url: https://api.example.com')

    def test_tests_not_list_raises(self):
        with pytest.raises(ValueError, match="'tests' field must be a list"):
            _validate_yaml('name: Test\ntests: "not_a_list"')

    def test_empty_tests_raises(self):
        with pytest.raises(ValueError, match="no test cases"):
            _validate_yaml('name: Test\ntests: []')


class TestGetApiKey:
    def test_returns_env_var(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key")
        key = _get_api_key("anthropic")
        assert key == "env-key"

    def test_explicit_key_overrides_env(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key")
        key = _get_api_key("anthropic", api_key="explicit-key")
        assert key == "explicit-key"

    def test_raises_when_missing(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY is required"):
            _get_api_key("anthropic")

    def test_deepseek_env_var(self, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "ds-key")
        key = _get_api_key("deepseek")
        assert key == "ds-key"


# Shared helper to mock any provider's LLM call
def _mock_llm_response(provider: str, yaml_text: str):
    """Return a mock set up for the given provider that returns yaml_text."""
    if provider == "anthropic":
        patcher = mock.patch("anthropic.Anthropic")
    else:
        patcher = mock.patch("openai.OpenAI")
    return patcher


def _setup_mock_client(mock_sdk_class, provider: str, yaml_text: str):
    """Configure a mock SDK client to return the given YAML text."""
    mock_client = mock.MagicMock()
    mock_sdk_class.return_value = mock_client

    if provider == "anthropic":
        mock_message = mock.MagicMock()
        mock_message.content = [mock.MagicMock()]
        mock_message.content[0].text = yaml_text
        mock_client.messages.create.return_value = mock_message
    else:
        mock_response = mock.MagicMock()
        mock_response.choices = [mock.MagicMock()]
        mock_response.choices[0].message.content = yaml_text
        mock_client.chat.completions.create.return_value = mock_response

    return mock_client


class TestGenerateAnthropic:
    """Tests for the Anthropic provider."""

    def test_missing_api_key_raises(self):
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY is required"):
            generate("POST /api/login", provider="anthropic", api_key="")

    def test_generate_returns_yaml(self, monkeypatch, sample_yaml):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        with mock.patch("anthropic.Anthropic") as mock_sdk:
            mock_client = _setup_mock_client(mock_sdk, "anthropic", sample_yaml)

            result = generate(
                "POST /api/login",
                base_url="https://api.example.com",
                provider="anthropic",
            )

            assert "name:" in result
            assert "tests:" in result
            mock_client.messages.create.assert_called_once()

    def test_generate_passes_system_prompt(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        desc = "POST /api/order, body: {item_id, quantity}"

        with mock.patch("anthropic.Anthropic") as mock_sdk:
            mock_client = _setup_mock_client(
                mock_sdk, "anthropic",
                'name: Test\nbase_url: https://api.example.com\n'
                'tests:\n  - id: t1\n    method: POST\n    path: /api/order\n'
                '    expect:\n      status_code: 201\n',
            )

            generate(desc, base_url="https://api.example.com", provider="anthropic")

            call_kwargs = mock_client.messages.create.call_args[1]
            assert call_kwargs["system"] is not None
            user_content = call_kwargs["messages"][0]["content"]
            assert "POST /api/order" in user_content
            assert "item_id, quantity" in user_content

    def test_generate_with_explicit_api_key(self, sample_yaml):
        with mock.patch("anthropic.Anthropic") as mock_sdk:
            _setup_mock_client(mock_sdk, "anthropic", sample_yaml)

            generate("POST /api/login", api_key="explicit-key", provider="anthropic")
            mock_sdk.assert_called_once_with(api_key="explicit-key")


class TestGenerateDeepSeek:
    """Tests for the DeepSeek provider."""

    def test_missing_api_key_raises(self):
        with pytest.raises(ValueError, match="DEEPSEEK_API_KEY is required"):
            generate("POST /api/login", provider="deepseek", api_key="")

    def test_generate_returns_yaml(self, monkeypatch, sample_yaml):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-ds-key")

        with mock.patch("openai.OpenAI") as mock_sdk:
            mock_client = _setup_mock_client(mock_sdk, "deepseek", sample_yaml)

            result = generate(
                "POST /api/login",
                base_url="https://api.example.com",
                provider="deepseek",
            )

            assert "name:" in result
            assert "tests:" in result
            mock_client.chat.completions.create.assert_called_once()

    def test_uses_deepseek_base_url(self, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-ds-key")

        with mock.patch("openai.OpenAI") as mock_sdk:
            _setup_mock_client(
                mock_sdk, "deepseek",
                'name: Test\ntests:\n  - id: t1\n    method: GET\n    path: /test\n'
                '    expect:\n      status_code: 200\n',
            )

            generate("GET /test", provider="deepseek")
            call_kwargs = mock_sdk.call_args[1]
            assert call_kwargs["base_url"] == "https://api.deepseek.com"

    def test_uses_system_message(self, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-ds-key")

        with mock.patch("openai.OpenAI") as mock_sdk:
            mock_client = _setup_mock_client(
                mock_sdk, "deepseek",
                'name: Test\ntests:\n  - id: t1\n    method: GET\n    path: /test\n'
                '    expect:\n      status_code: 200\n',
            )

            generate("GET /test", provider="deepseek")
            call_kwargs = mock_client.chat.completions.create.call_args[1]
            messages = call_kwargs["messages"]
            assert messages[0]["role"] == "system"
            assert messages[1]["role"] == "user"

    def test_uses_default_model(self, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-ds-key")

        with mock.patch("openai.OpenAI") as mock_sdk:
            mock_client = _setup_mock_client(
                mock_sdk, "deepseek",
                'name: Test\ntests:\n  - id: t1\n    method: GET\n    path: /test\n'
                '    expect:\n      status_code: 200\n',
            )

            generate("GET /test", provider="deepseek")
            call_kwargs = mock_client.chat.completions.create.call_args[1]
            assert call_kwargs["model"] == "deepseek-chat"


class TestGenerateProviderSelection:
    """Tests for provider selection logic."""

    def test_anthropic_is_default(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        with mock.patch("anthropic.Anthropic") as mock_sdk:
            _setup_mock_client(
                mock_sdk, "anthropic",
                'name: Test\ntests:\n  - id: t1\n    method: GET\n    path: /test\n'
                '    expect:\n      status_code: 200\n',
            )
            generate("GET /test")  # no provider specified
            # Should still work with Anthropic

    def test_openai_provider(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-oai-key")

        with mock.patch("openai.OpenAI") as mock_sdk:
            mock_client = _setup_mock_client(
                mock_sdk, "openai",
                'name: Test\ntests:\n  - id: t1\n    method: GET\n    path: /test\n'
                '    expect:\n      status_code: 200\n',
            )

            result = generate("GET /test", provider="openai")
            assert "tests:" in result
            call_kwargs = mock_client.chat.completions.create.call_args[1]
            assert call_kwargs["model"] == "gpt-4o"


class TestGenerateFromOpenapi:
    def test_yields_yaml(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        endpoints = [{
            "method": "GET",
            "path": "/users",
            "summary": "List users",
            "parameters": "none",
            "request_body": "none",
            "responses": "200: OK",
        }]

        with mock.patch("anthropic.Anthropic") as mock_sdk:
            _setup_mock_client(
                mock_sdk, "anthropic",
                'name: Users API\nbase_url: https://api.example.com\n'
                'tests:\n  - id: list_users\n    method: GET\n    path: /users\n'
                '    expect:\n      status_code: 200\n',
            )

            result = generate_from_openapi(
                endpoints, base_url="https://api.example.com", provider="anthropic",
            )

            assert "tests:" in result

    def test_with_deepseek_provider(self, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-ds-key")
        endpoints = [{
            "method": "GET",
            "path": "/users",
            "summary": "List users",
            "parameters": "none",
            "request_body": "none",
            "responses": "200: OK",
        }]

        with mock.patch("openai.OpenAI") as mock_sdk:
            _setup_mock_client(
                mock_sdk, "deepseek",
                'name: Users API\nbase_url: https://api.example.com\n'
                'tests:\n  - id: list_users\n    method: GET\n    path: /users\n'
                '    expect:\n      status_code: 200\n',
            )

            result = generate_from_openapi(
                endpoints, base_url="https://api.example.com", provider="deepseek",
            )

            assert "tests:" in result
