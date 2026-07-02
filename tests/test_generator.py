"""Tests for the generator module."""

from unittest import mock

import pytest

from test_case_ai.generator import _extract_yaml, _validate_yaml, generate, generate_from_openapi


class TestExtractYaml:
    def test_extract_fenced_yaml_block(self):
        text = '```yaml\nname: Test\nbase_url: https://api.example.com\ntests: []\n```'
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
        text = '```yaml\nname: First\ntests: []\n```\n```yaml\nname: Second\ntests: []\n```'
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


class TestGenerate:
    def test_missing_api_key_raises(self):
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY is required"):
            generate("POST /api/login", api_key="")

    def test_generate_returns_yaml(self, monkeypatch, sample_yaml):
        """Test that generate() returns valid YAML with a mocked API key."""
        # We test only the prompt-building and validation path by mocking
        # the client and verifying the pipeline works end-to-end
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        with mock.patch("test_case_ai.generator.Anthropic") as mock_anthropic:
            mock_client = mock.MagicMock()
            mock_anthropic.return_value = mock_client

            mock_message = mock.MagicMock()
            mock_message.content = [mock.MagicMock()]
            mock_message.content[0].text = sample_yaml
            mock_client.messages.create.return_value = mock_message

            result = generate("POST /api/login", base_url="https://api.example.com")

            assert "name:" in result
            assert "tests:" in result
            mock_client.messages.create.assert_called_once()

    def test_generate_passes_description_to_api(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        desc = "POST /api/order, body: {item_id, quantity}"

        with mock.patch("test_case_ai.generator.Anthropic") as mock_anthropic:
            mock_client = mock.MagicMock()
            mock_anthropic.return_value = mock_client

            mock_message = mock.MagicMock()
            mock_message.content = [
                mock.MagicMock()
            ]
            mock_message.content[0].text = (
                'name: Order Tests\nbase_url: https://api.example.com\n'
                'tests:\n  - id: create_order\n    method: POST\n    path: /api/order\n'
                '    expect:\n      status_code: 201\n'
            )
            mock_client.messages.create.return_value = mock_message

            generate(desc, base_url="https://api.example.com")

            call_args = mock_client.messages.create.call_args
            kwargs = call_args[1]
            assert kwargs["system"] is not None
            user_content = kwargs["messages"][0]["content"]
            assert "POST /api/order" in user_content
            assert "item_id, quantity" in user_content

    def test_generate_with_explicit_api_key(self, sample_yaml):
        with mock.patch("test_case_ai.generator.Anthropic") as mock_anthropic:
            mock_client = mock.MagicMock()
            mock_anthropic.return_value = mock_client

            mock_message = mock.MagicMock()
            mock_message.content = [mock.MagicMock()]
            mock_message.content[0].text = sample_yaml
            mock_client.messages.create.return_value = mock_message

            generate("POST /api/login", api_key="explicit-key")
            mock_anthropic.assert_called_once_with(api_key="explicit-key")

    def test_generate_raises_on_invalid_response(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        with mock.patch("test_case_ai.generator.Anthropic") as mock_anthropic:
            mock_client = mock.MagicMock()
            mock_anthropic.return_value = mock_client

            mock_message = mock.MagicMock()
            mock_message.content = [mock.MagicMock()]
            mock_message.content[0].text = "not: valid: yaml: [unclosed"
            mock_client.messages.create.return_value = mock_message

            with pytest.raises(ValueError):
                generate("GET /test")


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

        with mock.patch("test_case_ai.generator.Anthropic") as mock_anthropic:
            mock_client = mock.MagicMock()
            mock_anthropic.return_value = mock_client

            mock_message = mock.MagicMock()
            mock_message.content = [
                mock.MagicMock()
            ]
            mock_message.content[0].text = (
                'name: Users API\nbase_url: https://api.example.com\n'
                'tests:\n  - id: list_users\n    method: GET\n    path: /users\n'
                '    expect:\n      status_code: 200\n'
            )
            mock_client.messages.create.return_value = mock_message

            result = generate_from_openapi(endpoints, base_url="https://api.example.com")

            assert "tests:" in result
            assert mock_client.messages.create.called
