from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from html2md import cli
from html2md.extract import ExtractResult, Html2MdError


def sample_result() -> ExtractResult:
    return ExtractResult(
        markdown="# Example\n\nHello world.",
        captured_at="2026-04-15T22:00:00Z",
        source_url="https://example.com/start",
        final_url="https://example.com/posts/hello-world",
        title="Example",
        author="Jane Doe",
        published_at="2024-01-02",
    )


def test_fetch_prints_markdown_to_stdout(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "extract_from_url", lambda url: sample_result())

    exit_code = cli.main(["fetch", "https://example.com/start"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == "# Example\n\nHello world.\n"
    assert captured.err == ""


def test_convert_reads_stdin_and_prints_markdown(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "extract_from_html", lambda html, mode: sample_result())
    monkeypatch.setattr("sys.stdin", io.StringIO("<html><body>Example</body></html>"))

    exit_code = cli.main(["convert", "--stdin"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == "# Example\n\nHello world.\n"
    assert captured.err == ""


def test_frontmatter_is_prepended(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "extract_from_url", lambda url: sample_result())

    exit_code = cli.main(["fetch", "https://example.com/start", "--frontmatter"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    assert captured.out.startswith("---\n")
    assert 'title: "Example"' in captured.out
    assert "# Example" in captured.out


def test_json_output_contains_expected_fields(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "extract_from_url", lambda url: sample_result())

    exit_code = cli.main(["fetch", "https://example.com/start", "--json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert captured.err == ""
    assert payload["ok"] is True
    assert payload["source_url"] == "https://example.com/start"
    assert payload["final_url"] == "https://example.com/posts/hello-world"
    assert payload["title"] == "Example"
    assert payload["markdown"] == "# Example\n\nHello world."


def test_out_dir_uses_deterministic_filename(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "extract_from_url", lambda url: sample_result())

    exit_code = cli.main(["fetch", "https://example.com/start", "--out-dir", str(tmp_path)])

    captured = capsys.readouterr()
    output_path = tmp_path / "example-com-posts-hello-world.md"
    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""
    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8") == "# Example\n\nHello world.\n"


def test_failure_prints_clean_stderr_and_non_zero(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def raise_error(url: str) -> ExtractResult:
        raise Html2MdError("failed hard")

    monkeypatch.setattr(cli, "extract_from_url", raise_error)

    exit_code = cli.main(["fetch", "https://example.com/start"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == "html2md: failed hard\n"
