from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from html import unescape
from typing import Literal
from urllib.error import URLError
from urllib.request import Request, urlopen

from markdownify import markdownify
from trafilatura import extract as trafilatura_extract
from trafilatura.metadata import extract_metadata

USER_AGENT = "html2md/0.1 (+terminal automation)"
FETCH_TIMEOUT_SECONDS = 30


class Html2MdError(Exception):
    """Base exception for CLI-facing failures."""


class FetchError(Html2MdError):
    """Raised when a remote fetch fails."""


class ExtractionError(Html2MdError):
    """Raised when markdown extraction fails."""


@dataclass(slots=True)
class ExtractResult:
    markdown: str
    captured_at: str
    source_url: str | None = None
    final_url: str | None = None
    title: str | None = None
    author: str | None = None
    published_at: str | None = None


def fetch_html(url: str, timeout: int = FETCH_TIMEOUT_SECONDS) -> tuple[str, str]:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.1",
        },
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            html = response.read().decode(charset, errors="replace")
            return html, response.geturl()
    except (URLError, ValueError) as exc:
        raise FetchError(f"failed to fetch {url}: {exc}") from exc


def extract_from_url(url: str) -> ExtractResult:
    html, final_url = fetch_html(url)
    return extract_from_html(
        html,
        mode="fetch",
        source_url=url,
        final_url=final_url,
    )


def extract_from_html(
    html: str,
    *,
    mode: Literal["fetch", "convert"],
    source_url: str | None = None,
    final_url: str | None = None,
) -> ExtractResult:
    if not html.strip():
        raise ExtractionError("no HTML input received")

    captured_at = utc_now()
    metadata = extract_metadata(html, default_url=final_url or source_url)

    if mode == "fetch":
        markdown = trafilatura_to_markdown(html, url=final_url or source_url)
        if not markdown:
            markdown = html_to_markdown(html)
    else:
        markdown = html_to_markdown(html)
        if not markdown:
            markdown = trafilatura_to_markdown(html, url=final_url or source_url)

    if not markdown:
        raise ExtractionError("unable to extract markdown from HTML")

    return ExtractResult(
        markdown=markdown,
        captured_at=captured_at,
        source_url=source_url,
        final_url=final_url,
        title=clean_metadata(getattr(metadata, "title", None)),
        author=clean_metadata(getattr(metadata, "author", None)),
        published_at=clean_metadata(getattr(metadata, "date", None)),
    )


def trafilatura_to_markdown(html: str, *, url: str | None) -> str | None:
    markdown = trafilatura_extract(
        html,
        url=url,
        output_format="markdown",
        include_links=True,
        include_formatting=True,
        include_tables=True,
    )
    return normalize_markdown(markdown)


def html_to_markdown(html: str) -> str | None:
    markdown = markdownify(
        html,
        heading_style="ATX",
        bullets="-",
        strip=["script", "style", "noscript"],
    )
    return normalize_markdown(markdown)


def normalize_markdown(markdown: str | None) -> str | None:
    if not markdown:
        return None

    lines = [line.rstrip() for line in markdown.replace("\r\n", "\n").split("\n")]
    collapsed: list[str] = []
    blank_streak = 0

    for line in lines:
        if line.strip():
            collapsed.append(unescape(line))
            blank_streak = 0
            continue

        blank_streak += 1
        if blank_streak <= 1:
            collapsed.append("")

    normalized = "\n".join(collapsed).strip()
    return normalized or None


def clean_metadata(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = " ".join(value.split())
    return cleaned or None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00",
        "Z",
    )
