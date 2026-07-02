"""Tests for the CLI module."""

from unittest import mock

import pytest

from test_case_ai.cli import main


def _run_cli(*args):
    """Run the CLI with given arguments and return exit code + stdout/stderr."""
    with mock.patch("sys.argv", ["tai"] + list(args)):
        with mock.patch("sys.stdout") as mock_stdout, \
             mock.patch("sys.stderr") as mock_stderr:
            try:
                main()
                return 0, mock_stdout, mock_stderr
            except SystemExit as e:
                return e.code, mock_stdout, mock_stderr


class TestCLIHelp:
    def test_no_args_shows_help(self, capsys):
        with mock.patch("sys.argv", ["tai"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "usage" in captured.out.lower() or "test case" in captured.out.lower()

    def test_generate_help(self):
        with mock.patch("sys.argv", ["tai", "generate", "--help"]):
            with pytest.raises(SystemExit):
                main()


class TestCLIGenerate:
    def test_requires_input_source(self, capsys):
        with mock.patch("sys.argv", ["tai", "generate"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code != 0

    def test_desc_mode_calls_generator(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        with mock.patch("sys.argv", ["tai", "generate", "--desc", "POST /api/login"]):
            with mock.patch("test_case_ai.cli.generate") as mock_gen:
                mock_gen.return_value = "name: Test\ntests: []"
                try:
                    main()
                except SystemExit:
                    pass
                mock_gen.assert_called_once()
                call_kwargs = mock_gen.call_args[1]
                assert call_kwargs["api_key"] == "test-key"

    def test_openapi_mode_calls_fetch_and_generate(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        with mock.patch("sys.argv", [
            "tai", "generate", "--openapi", "https://example.com/openapi.json"
        ]):
            with mock.patch("test_case_ai.cli.fetch_spec") as mock_fetch, \
                 mock.patch("test_case_ai.cli.parse_endpoints") as mock_parse, \
                 mock.patch("test_case_ai.cli.generate_from_openapi") as mock_gen:
                mock_fetch.return_value = {"openapi": "3.0.0", "paths": {}}
                mock_parse.return_value = []
                mock_gen.return_value = "name: Test\ntests: []"
                try:
                    main()
                except SystemExit:
                    pass
                mock_fetch.assert_called_once()
                mock_gen.assert_called_once()

    def test_output_flag_writes_file(self, tmp_path, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        output_file = tmp_path / "test_output.yaml"

        with mock.patch("sys.argv", [
            "tai", "generate", "--desc", "GET /test", "-o", str(output_file)
        ]):
            with mock.patch("test_case_ai.cli.generate") as mock_gen:
                mock_gen.return_value = (
                    "name: Test\n"
                    "tests:\n"
                    "  - id: t1\n"
                    "    method: GET\n"
                    "    path: /test\n"
                    "    expect:\n"
                    "      status_code: 200"
                )
                try:
                    main()
                except SystemExit:
                    pass
                assert output_file.exists()
                content = output_file.read_text()
                assert "name: Test" in content
                assert "tests:" in content

    def test_desc_mutually_exclusive_with_openapi(self, capsys):
        with mock.patch("sys.argv", [
            "tai", "generate", "--desc", "GET /test", "--openapi", "http://example.com"
        ]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code != 0

    def test_verbose_flag(self, monkeypatch, capsys):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        with mock.patch("sys.argv", [
            "tai", "generate", "--openapi", "https://example.com/openapi.json", "--verbose"
        ]):
            with mock.patch("test_case_ai.cli.fetch_spec") as mock_fetch, \
                 mock.patch("test_case_ai.cli.parse_endpoints") as mock_parse, \
                 mock.patch("test_case_ai.cli.generate_from_openapi") as mock_gen:
                mock_fetch.return_value = {"openapi": "3.0.0", "paths": {}}
                mock_parse.return_value = [{"method": "GET", "path": "/test"}]
                mock_gen.return_value = "name: Test\ntests: []"
                try:
                    main()
                except SystemExit:
                    pass
                stderr = capsys.readouterr().err
                assert "1 endpoint" in stderr

    def test_openapi_parse_error_exits(self, monkeypatch, capsys):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        with mock.patch("sys.argv", [
            "tai", "generate", "--openapi", "https://example.com/bad.json"
        ]):
            with mock.patch("test_case_ai.cli.fetch_spec") as mock_fetch:
                from test_case_ai.openapi_parser import OpenAPIParseError
                mock_fetch.side_effect = OpenAPIParseError("bad spec")
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1


class TestCLIProviderFlag:
    """Tests for the --provider flag."""

    def test_deepseek_provider_passes_env_var(self, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-ds-key")

        with mock.patch("sys.argv", [
            "tai", "generate", "--desc", "GET /test", "--provider", "deepseek"
        ]):
            with mock.patch("test_case_ai.cli.generate") as mock_gen:
                mock_gen.return_value = "name: Test\ntests: []"
                try:
                    main()
                except SystemExit:
                    pass
                mock_gen.assert_called_once()
                call_kwargs = mock_gen.call_args[1]
                assert call_kwargs["api_key"] == "test-ds-key"
                assert call_kwargs["provider"] == "deepseek"

    def test_deepseek_openapi_mode(self, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-ds-key")

        with mock.patch("sys.argv", [
            "tai", "generate", "--openapi", "https://example.com/api.json",
            "--provider", "deepseek",
        ]):
            with mock.patch("test_case_ai.cli.fetch_spec") as mock_fetch, \
                 mock.patch("test_case_ai.cli.parse_endpoints") as mock_parse, \
                 mock.patch("test_case_ai.cli.generate_from_openapi") as mock_gen:
                mock_fetch.return_value = {"openapi": "3.0.0", "paths": {}}
                mock_parse.return_value = []
                mock_gen.return_value = "name: Test\ntests: []"
                try:
                    main()
                except SystemExit:
                    pass
                call_kwargs = mock_gen.call_args[1]
                assert call_kwargs["provider"] == "deepseek"

    def test_openai_provider(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-oai-key")

        with mock.patch("sys.argv", [
            "tai", "generate", "--desc", "GET /test", "--provider", "openai"
        ]):
            with mock.patch("test_case_ai.cli.generate") as mock_gen:
                mock_gen.return_value = "name: Test\ntests: []"
                try:
                    main()
                except SystemExit:
                    pass
                call_kwargs = mock_gen.call_args[1]
                assert call_kwargs["provider"] == "openai"
