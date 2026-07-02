"""CLI entry point for test-case-ai (tai)."""

from __future__ import annotations

import argparse
import os
import sys

from .generator import generate, generate_from_openapi
from .openapi_parser import OpenAPIParseError, fetch_spec, get_base_url, parse_endpoints


def cmd_generate(args: argparse.Namespace) -> None:
    """Handle the 'generate' subcommand."""
    api_key = args.api_key or os.getenv("ANTHROPIC_API_KEY", "")

    try:
        if args.openapi:
            # OpenAPI spec mode
            spec = fetch_spec(args.openapi)
            base_url = args.base_url or get_base_url(spec)
            endpoints = parse_endpoints(spec)
            if args.verbose:
                print(f"Parsed {len(endpoints)} endpoint(s) from {args.openapi}", file=sys.stderr)
                for ep in endpoints:
                    print(f"  {ep['method']} {ep['path']}", file=sys.stderr)
            result = generate_from_openapi(
                endpoints, base_url=base_url, api_key=api_key, model=args.model
            )
        elif args.desc:
            # Natural language description mode
            result = generate(
                args.desc, base_url=args.base_url, api_key=api_key, model=args.model
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


def main() -> None:
    """Main CLI entry point for `tai`."""
    parser = argparse.ArgumentParser(
        prog="tai",
        description="AI-powered test case generator using Claude API. "
        "Generates test-sprint-lite compatible YAML.",
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
        "--api-key",
        type=str,
        default="",
        metavar="KEY",
        help="Anthropic API key (or set ANTHROPIC_API_KEY env var)",
    )
    gen_parser.add_argument(
        "--model",
        type=str,
        default="claude-sonnet-5",
        metavar="MODEL",
        help="Claude model to use (default: claude-sonnet-5)",
    )
    gen_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print extra diagnostic info to stderr",
    )
    gen_parser.set_defaults(func=cmd_generate)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
