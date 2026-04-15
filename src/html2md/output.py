from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from html2md.extract import ExtractResult


def render_markdown(result: ExtractResult, *, frontmatter: bool) -> str:
    if not frontmatter:
        return result.markdown

    metadata = markdown_metadata(result)
    if not metadata:
        return result.markdown

    header_lines = ["---"]
    header_lines.extend(f"{key}: {yaml_quote(value)}" for key, value in metadata.items())
    header_lines.append("---")
    header_lines.append("")
    header_lines.append(result.markdown)
    return "\n".join(header_lines)


def markdown_metadata(result: ExtractResult) -> dict[str, str]:
    data: dict[str, str] = {}

    for key, value in (
        ("title", result.title),
        ("author", result.author),
        ("published_at", result.published_at),
        ("captured_at", result.captured_at),
        ("source_url", result.source_url),
        ("final_url", result.final_url),
    ):
        if value:
            data[key] = value

    return data


def build_json_payload(
    *,
    ok: bool,
    result: ExtractResult | None,
    path: Path | None,
    markdown: str | None,
    error: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"ok": ok}

    if error:
        payload["error"] = error

    if result:
        for key, value in (
            ("source_url", result.source_url),
            ("final_url", result.final_url),
            ("title", result.title),
            ("author", result.author),
            ("published_at", result.published_at),
            ("captured_at", result.captured_at),
        ):
            if value:
                payload[key] = value

    if path is not None:
        payload["path"] = str(path.resolve())

    if markdown:
        payload["markdown"] = markdown

    return payload


def serialize_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write_text(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def derive_output_path(
    result: ExtractResult,
    out_dir: Path,
    *,
    json_mode: bool,
) -> Path:
    stem = derive_output_stem(result)
    suffix = ".json" if json_mode else ".md"
    return out_dir / f"{stem}{suffix}"


def derive_output_stem(result: ExtractResult) -> str:
    url = result.final_url or result.source_url
    if url:
        return slugify_url(url)
    if result.title:
        return slugify(result.title)
    return "stdin"


def slugify_url(url: str) -> str:
    parsed = urlparse(url)
    parts = [parsed.netloc, *[segment for segment in parsed.path.split("/") if segment]]
    slug = slugify("-".join(parts))
    return slug or "document"


def slugify(value: str) -> str:
    lowered = value.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return slug or "document"


def yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)
