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
uv run html2md https://example.com
uv run html2md fetch https://example.com
cat page.html | uv run html2md convert --stdin
```

To run `html2md` from any terminal location, install it on your PATH:

```bash
uv tool install --editable .
html2md doctor
html2md https://example.com
```

## Fetch Wrappers

The repo includes small Bash and PowerShell wrappers for fetch-style automation:

```bash
scripts/html2md-fetch.sh https://example.com
```

```powershell
.\scripts\html2md-fetch.ps1 https://example.com
```

Both wrappers default to this command template:

```bash
html2md ${url}
```

Set `HTML2MD_FETCH_COMMAND` when the installed command needs a different shape, such as:

```bash
HTML2MD_FETCH_COMMAND='html2md fetch ${url}' scripts/html2md-fetch.sh https://example.com
```

```powershell
$env:HTML2MD_FETCH_COMMAND = 'html2md fetch ${url}'
.\scripts\html2md-fetch.ps1 https://example.com
```

## CLI

### Fetch a URL

```bash
uv run html2md https://example.com
uv run html2md fetch https://example.com
uv run html2md fetch https://example.com --frontmatter
uv run html2md fetch https://example.com --json
uv run html2md fetch https://example.com --out article.md
uv run html2md fetch https://example.com --out-dir output/
uv run html2md fetch https://example.com --json --out-dir output/
```

Use `fetch` when you want the tool to retrieve a live page and clean it up like article content.

### Convert raw HTML from stdin

```bash
cat page.html | uv run html2md convert --stdin
cat page.html | uv run html2md convert --stdin --frontmatter
cat page.html | uv run html2md convert --stdin --json
cat page.html | uv run html2md convert --stdin --out-dir output/
cat page.html | uv run html2md convert --stdin --json --out-dir output/
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

## Automation Summary

| Command | Reads from | Default stdout | `--json` stdout | stderr on failure | Writes files |
| --- | --- | --- | --- | --- | --- |
| `html2md fetch <url>` | URL argument | Markdown | One JSON object | Plain error line | Only with `--out` or `--out-dir` |
| `html2md convert --stdin` | stdin HTML | Markdown | One JSON object | Plain error line | Only with `--out` or `--out-dir` |
| `html2md doctor` | nothing | Readiness text | One JSON object | Plain error line if command fails | Never |

### Output Destination Rules

- if neither `--out` nor `--out-dir` is given, final output is written to stdout
- if `--out FILE` is given, final output is written only to that file
- if `--out-dir DIR` is given, final output is written only to a deterministic file in that directory
- in plain Markdown mode, writing to disk leaves stdout empty on success
- in `--json` mode, writing to disk still prints one JSON object to stdout and includes `path`
- in `--json` mode with `--out` or `--out-dir`, the same JSON payload is both written to disk and printed to stdout
- normal successful runs do not print log noise to stderr

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

### Example JSON With `--out-dir`

```bash
uv run html2md fetch https://example.com --json --out-dir output/
```

stdout:

```json
{
  "ok": true,
  "source_url": "https://example.com",
  "final_url": "https://example.com",
  "title": "Example Domain",
  "captured_at": "2026-04-16T00:44:09Z",
  "path": "/absolute/path/to/output/example-com.json",
  "markdown": "This domain is for use in documentation examples without needing permission. Avoid use in operations.\n\nLearn more"
}
```

written file:

- `output/example-com.json`
- contains the same JSON object that was printed to stdout

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
