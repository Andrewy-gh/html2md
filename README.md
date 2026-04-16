# html2md

Small Unix-style HTML-to-Markdown CLI for terminal workflows and automation.

`html2md` uses `trafilatura` as the primary extraction engine for fetched pages, keeps stdin conversion simple, and can emit either plain Markdown or a single JSON object for bots and shell pipelines.

## Requirements

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/) for environment management and execution

## Quick Start

```bash
uv sync
uv run html2md doctor
uv run html2md fetch https://example.com
cat page.html | uv run html2md convert --stdin
```

## CLI

### Fetch a URL

```bash
uv run html2md fetch https://example.com
uv run html2md fetch https://example.com --frontmatter
uv run html2md fetch https://example.com --json
uv run html2md fetch https://example.com --out article.md
uv run html2md fetch https://example.com --out-dir output/
```

Use `fetch` when you want the tool to retrieve a live page and clean it up like article content.

### Convert raw HTML from stdin

```bash
cat page.html | uv run html2md convert --stdin
cat page.html | uv run html2md convert --stdin --frontmatter
cat page.html | uv run html2md convert --stdin --json
cat page.html | uv run html2md convert --stdin --out-dir output/
```

Use `convert --stdin` when you already have HTML and want a terminal-friendly Markdown conversion without temp files.

### Doctor

```bash
uv run html2md doctor
uv run html2md doctor --json
```

## Output Behavior

- Default mode writes Markdown to stdout.
- `--json` writes one JSON object to stdout.
- `--frontmatter` prepends YAML frontmatter to Markdown output.
- `--out FILE` writes the final output to a specific file.
- `--out-dir DIR` writes to a deterministic filename based on the URL or available metadata.
- Errors go to stderr in plain-text mode and return a non-zero exit status.
- Metadata fields are omitted when unavailable instead of being guessed.

Example JSON fields:

- `ok`
- `source_url`
- `final_url`
- `title`
- `author`
- `published_at`
- `captured_at`
- `path`
- `markdown`

## Automation Notes

`html2md` is designed to behave like a small Unix CLI:

- stdout is reserved for final output only
- stderr is reserved for errors
- successful commands exit `0`
- failed commands exit non-zero
- `--json` emits exactly one JSON object

That makes it safe to use in shell pipelines, bots, and agent tools.

## Command Contract

### `html2md fetch <url>`

- input: one URL argument
- output: Markdown by default, or one JSON object with `--json`
- metadata: includes `source_url`, `final_url`, and any metadata trafilatura can extract
- failure mode: exits non-zero, prints a plain error to stderr, or prints a single error JSON object with `--json`

### `html2md convert --stdin`

- input: raw HTML on stdin
- output: Markdown by default, or one JSON object with `--json`
- metadata: includes only metadata present in the provided HTML
- failure mode: exits non-zero, prints a plain error to stderr, or prints a single error JSON object with `--json`

### `html2md doctor`

- input: no stdin required
- output: a small readiness report, plain text by default or one JSON object with `--json`
- purpose: confirms the installed CLI and runtime dependencies are wired correctly

## Fetch vs Convert

These subcommands are intentionally not identical.

- `fetch` is URL-first and optimized for article extraction. It fetches the page, follows redirects, and prefers trafilatura's cleaned content.
- `convert --stdin` is HTML-first and optimized for terminal workflows. It converts the HTML you already have without requiring a temp file or another network hop.
- In practice, `fetch` is better for live web pages, while `convert --stdin` is better for saved HTML, piped HTML, and agent-generated HTML snapshots.

### Example JSON

```json
{
  "ok": true,
  "source_url": "https://example.com/start",
  "final_url": "https://example.com/posts/hello-world",
  "title": "Example",
  "author": "Jane Doe",
  "published_at": "2024-01-02",
  "captured_at": "2026-04-15T22:00:00Z",
  "markdown": "# Example\n\nHello world."
}
```

### Example Failure JSON

```json
{
  "ok": false,
  "error": "failed to fetch https://example.invalid: <reason>"
}
```

### Frontmatter Example

```bash
uv run html2md fetch https://example.com --frontmatter
```

```md
---
title: "Example Domain"
captured_at: "2026-04-15T22:17:05Z"
source_url: "https://example.com"
final_url: "https://example.com"
---

This domain is for use in documentation examples without needing permission.
```

### Deterministic `--out-dir` Naming

- fetched URLs use a slug based on the final URL, like `example-com-posts-hello-world.md`
- stdin conversions fall back to title-derived names when available
- otherwise stdin output uses `stdin.md` or `stdin.json`

## Development

```bash
uv sync
uv run ruff check .
uv run mypy src
uv run pytest
```
