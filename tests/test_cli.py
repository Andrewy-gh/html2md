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
    assert captured.out.startswith("---\n")
    assert 'title: "Example"' in captured.out
    assert "# Example" in captured.out
    assert captured.err == ""


def test_url_argument_defaults_to_fetch(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    seen_url = ""

    def extract(url: str) -> ExtractResult:
        nonlocal seen_url
        seen_url = url
        return sample_result()

    monkeypatch.setattr(cli, "extract_from_url", extract)

    exit_code = cli.main(["https://example.com/start"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert seen_url == "https://example.com/start"
    assert captured.out.startswith("---\n")
    assert 'source_url: "https://example.com/start"' in captured.out
    assert "# Example" in captured.out
    assert captured.err == ""


def test_url_argument_with_file_writes_frontmatter_markdown(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "extract_from_url", lambda url: sample_result())

    output_path = tmp_path / "job.md"
    exit_code = cli.main(["https://example.com/start", str(output_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""
    content = output_path.read_text(encoding="utf-8")
    assert content.startswith("---\n")
    assert 'source_url: "https://example.com/start"' in content
    assert "# Example" in content


def test_convert_reads_stdin_and_prints_markdown(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "extract_from_html", lambda html, mode: sample_result())
    monkeypatch.setattr("sys.stdin", io.StringIO("<html><body>Example</body></html>"))

    exit_code = cli.main(["convert", "--stdin"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.startswith("---\n")
    assert 'title: "Example"' in captured.out
    assert "# Example" in captured.out
    assert captured.err == ""


def test_nofm_omits_frontmatter(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "extract_from_url", lambda url: sample_result())

    exit_code = cli.main(["fetch", "https://example.com/start", "--nofm"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == "# Example\n\nHello world.\n"
    assert captured.err == ""


def test_nofrontmatter_omits_frontmatter(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "extract_from_url", lambda url: sample_result())

    exit_code = cli.main(["fetch", "https://example.com/start", "--nofrontmatter"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == "# Example\n\nHello world.\n"
    assert captured.err == ""


def test_url_argument_prints_frontmatter_by_default(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "extract_from_url", lambda url: sample_result())

    exit_code = cli.main(["https://example.com/start"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    assert captured.out.startswith("---\n")
    assert 'source_url: "https://example.com/start"' in captured.out
    assert "# Example" in captured.out


def test_url_argument_with_file_can_omit_frontmatter(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "extract_from_url", lambda url: sample_result())

    output_path = tmp_path / "job.md"
    exit_code = cli.main(["https://example.com/start", str(output_path), "--nofm"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""

    content = output_path.read_text(encoding="utf-8")
    assert content == "# Example\n\nHello world.\n"


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
    assert payload["markdown"].startswith("---\n")
    assert 'source_url: "https://example.com/start"' in payload["markdown"]
    assert "# Example" in payload["markdown"]


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
    content = output_path.read_text(encoding="utf-8")
    assert content.startswith("---\n")
    assert 'source_url: "https://example.com/start"' in content
    assert "# Example" in content


def test_json_out_dir_writes_file_and_prints_json(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "extract_from_url", lambda url: sample_result())

    exit_code = cli.main(
        ["fetch", "https://example.com/start", "--json", "--out-dir", str(tmp_path)]
    )

    captured = capsys.readouterr()
    output_path = tmp_path / "example-com-posts-hello-world.json"
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert captured.err == ""
    assert output_path.exists()
    assert json.loads(output_path.read_text(encoding="utf-8")) == payload
    assert payload["ok"] is True
    assert payload["path"] == str(output_path.resolve())
    assert payload["markdown"].startswith("---\n")
    assert "# Example" in payload["markdown"]


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
