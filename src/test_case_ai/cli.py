"""CLI entry point for test-case-ai (tai)."""

from __future__ import annotations

import argparse
import os
import sys

from .generator import PROVIDERS, generate, generate_from_openapi
from .openapi_parser import OpenAPIParseError, fetch_spec, get_base_url, parse_endpoints


def cmd_generate(args: argparse.Namespace) -> None:
    """Handle the 'generate' subcommand."""
    api_key = args.api_key or os.getenv(PROVIDERS[args.provider]["env_var"], "")

    try:
        if args.openapi:
            # OpenAPI spec mode
            spec = fetch_spec(args.openapi)
            base_url = args.base_url or get_base_url(spec)
            endpoints = parse_endpoints(spec)
            if args.verbose:
                print(
                    f"Parsed {len(endpoints)} endpoint(s) from {args.openapi}",
                    file=sys.stderr,
                )
                for ep in endpoints:
                    print(f"  {ep['method']} {ep['path']}", file=sys.stderr)
            result = generate_from_openapi(
                endpoints, base_url=base_url, api_key=api_key,
                model=args.model, provider=args.provider,
            )
        elif args.desc:
            # Natural language description mode
            result = generate(
                args.desc, base_url=args.base_url, api_key=api_key,
                model=args.model, provider=args.provider,
            )
        else:
            print("Error: must provide either --desc or --openapi", file=sys.stderr)
            sys.exit(1)

    except OpenAPIParseError as e:
        print(f"Error parsing OpenAPI spec: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

    # Output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result)
            f.write("\n")
        print(f"Generated test cases saved to: {args.output}", file=sys.stderr)
    else:
        print(result)


def cmd_web(args: argparse.Namespace) -> None:
    """Handle the 'web' subcommand — start the FastAPI web UI."""
    import uvicorn

    from .web import app

    print(f"Starting web UI at http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop.")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


def main() -> None:
    """Main CLI entry point for `tai`."""
    parser = argparse.ArgumentParser(
        prog="tai",
        description="AI-powered test case generator. "
        "Generates test-sprint-lite compatible YAML via Claude, DeepSeek, or OpenAI.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate subcommand
    gen_parser = subparsers.add_parser(
        "generate", aliases=["gen"], help="Generate test cases"
    )
    input_group = gen_parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--desc", "-d",
        type=str,
        metavar="DESCRIPTION",
        help="Natural language API description (e.g. 'POST /api/login with username/password')",
    )
    input_group.add_argument(
        "--openapi", "-s",
        type=str,
        metavar="URL",
        help="URL to an OpenAPI / Swagger spec (e.g. https://petstore.swagger.io/v2/swagger.json)",
    )
    gen_parser.add_argument(
        "--output", "-o",
        type=str,
        metavar="FILE",
        help="Output YAML file path (default: stdout)",
    )
    gen_parser.add_argument(
        "--base-url",
        type=str,
        default="",
        metavar="URL",
        help="Base URL for the API (auto-detected from OpenAPI spec if omitted)",
    )
    gen_parser.add_argument(
        "--provider", "-p",
        type=str,
        default="anthropic",
        choices=list(PROVIDERS.keys()),
        metavar="PROVIDER",
        help="LLM provider: anthropic, deepseek, openai (default: anthropic)",
    )
    gen_parser.add_argument(
        "--model",
        type=str,
        default="",
        metavar="MODEL",
        help="Model name (default: provider-dependent, e.g. claude-sonnet-5 / deepseek-chat)",
    )
    gen_parser.add_argument(
        "--api-key",
        type=str,
        default="",
        metavar="KEY",
        help="API key (or set ANTHROPIC_API_KEY / DEEPSEEK_API_KEY / OPENAI_API_KEY env var)",
    )
    gen_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print extra diagnostic info to stderr",
    )
    gen_parser.set_defaults(func=cmd_generate)

    # Web subcommand
    web_parser = subparsers.add_parser(
        "web", help="Start web-based GUI"
    )
    web_parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        metavar="HOST",
        help="Host to bind the web server (default: 127.0.0.1)",
    )
    web_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        metavar="PORT",
        help="Port to bind the web server (default: 8000)",
    )
    web_parser.set_defaults(func=cmd_web)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
