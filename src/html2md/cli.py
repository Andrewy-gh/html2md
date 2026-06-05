from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from html2md import __version__
from html2md.extract import ExtractResult, Html2MdError, extract_from_html, extract_from_url
from html2md.output import (
    build_json_payload,
    derive_output_path,
    render_markdown,
    serialize_json,
    write_text,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="html2md",
        description="Reliable HTML-to-Markdown conversion for terminal workflows.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch_parser = subparsers.add_parser("fetch", help="Fetch a URL and emit Markdown.")
    add_output_arguments(fetch_parser)
    fetch_parser.add_argument("url", help="URL to fetch and convert")

    convert_parser = subparsers.add_parser("convert", help="Convert HTML input to Markdown.")
    add_output_arguments(convert_parser)
    convert_parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read raw HTML from stdin",
    )

    doctor_parser = subparsers.add_parser("doctor", help="Check runtime readiness.")
    doctor_parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")

    return parser


def add_output_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--nofm",
        "--nofrontmatter",
        dest="frontmatter",
        action="store_false",
        default=True,
        help="Omit YAML frontmatter from Markdown output",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a single JSON object instead of plain Markdown",
    )
    destination = parser.add_mutually_exclusive_group()
    destination.add_argument("--out", type=Path, help="Write output to a file")
    destination.add_argument("--out-dir", type=Path, help="Write output to a directory")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    raw_args = list(argv) if argv is not None else sys.argv[1:]
    args = parser.parse_args(normalize_args(raw_args))

    try:
        if args.command == "fetch":
            result = extract_from_url(args.url)
            return emit_result(result, args)

        if args.command == "convert":
            if not args.stdin:
                raise Html2MdError("convert requires --stdin")
            html = sys.stdin.read()
            result = extract_from_html(html, mode="convert")
            return emit_result(result, args)

        if args.command == "doctor":
            return run_doctor(json_mode=args.json)
    except Html2MdError as exc:
        return report_error(str(exc), json_mode=getattr(args, "json", False))

    return report_error("unknown command", json_mode=getattr(args, "json", False))


def normalize_args(argv: list[str]) -> list[str]:
    if argv and argv[0].startswith(("http://", "https://")):
        if len(argv) >= 2 and not argv[1].startswith("-"):
            return ["fetch", argv[0], "--out", argv[1], *argv[2:]]
        return ["fetch", *argv]
    return argv


def emit_result(result: ExtractResult, args: argparse.Namespace) -> int:
    markdown = render_markdown(result, frontmatter=args.frontmatter)
    destination = resolve_destination(result, args)

    if args.json:
        payload = build_json_payload(
            ok=True,
            result=result,
            path=destination,
            markdown=markdown,
        )
        content = serialize_json(payload)
    else:
        content = markdown
        if not content.endswith("\n"):
            content += "\n"

    if destination:
        write_text(destination, content)

    if args.json or destination is None:
        sys.stdout.write(content)

    return 0


def resolve_destination(result: ExtractResult, args: argparse.Namespace) -> Path | None:
    out_path = getattr(args, "out", None)
    if isinstance(out_path, Path):
        return out_path

    out_dir = getattr(args, "out_dir", None)
    if isinstance(out_dir, Path):
        return derive_output_path(result, out_dir, json_mode=bool(args.json))

    return None


def run_doctor(*, json_mode: bool) -> int:
    payload = {
        "ok": True,
        "python": sys.version.split()[0],
        "html2md": __version__,
        "checks": {
            "trafilatura": "ok",
            "markdownify": "ok",
        },
    }

    if json_mode:
        sys.stdout.write(serialize_json(payload))
    else:
        sys.stdout.write("html2md doctor: ok\n")
        sys.stdout.write(f"python: {payload['python']}\n")
        sys.stdout.write(f"html2md: {payload['html2md']}\n")
        sys.stdout.write("trafilatura: ok\n")
        sys.stdout.write("markdownify: ok\n")

    return 0


def report_error(message: str, *, json_mode: bool) -> int:
    if json_mode:
        payload = build_json_payload(
            ok=False,
            result=None,
            path=None,
            markdown=None,
            error=message,
        )
        sys.stdout.write(serialize_json(payload))
    else:
        sys.stderr.write(f"html2md: {message}\n")
    return 1
