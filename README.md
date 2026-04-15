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

### Convert raw HTML from stdin

```bash
cat page.html | uv run html2md convert --stdin
cat page.html | uv run html2md convert --stdin --frontmatter
cat page.html | uv run html2md convert --stdin --json
cat page.html | uv run html2md convert --stdin --out-dir output/
```

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
