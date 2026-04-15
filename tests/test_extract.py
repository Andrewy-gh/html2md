from __future__ import annotations

from html2md.extract import extract_from_html


def test_convert_html_to_markdown_with_metadata() -> None:
    html = """
    <html>
      <head>
        <title>Example Article</title>
        <meta name="author" content="Jane Doe" />
        <meta property="article:published_time" content="2024-01-02" />
      </head>
      <body>
        <article>
          <h1>Example Article</h1>
          <p>Hello <strong>world</strong>.</p>
          <ul>
            <li>One</li>
            <li>Two</li>
          </ul>
        </article>
      </body>
    </html>
    """

    result = extract_from_html(html, mode="convert")

    assert result.title == "Example Article"
    assert result.author == "Jane Doe"
    assert result.published_at == "2024-01-02"
    assert "# Example Article" in result.markdown
    assert "- One" in result.markdown
    assert "Hello **world**." in result.markdown
