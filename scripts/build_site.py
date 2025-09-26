#!/usr/bin/env python3
"""Generate a static site for the chapters collection."""
from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

import markdown

BASE_DIR = Path(__file__).resolve().parent.parent
CHAPTERS_DIR = BASE_DIR / "chapters"
OUTPUT_DIR = BASE_DIR / "site"
ASSETS_DIR = OUTPUT_DIR / "assets"

NAVIGATION_LINK = '<nav class="breadcrumbs"><a href="index.html">ホームに戻る</a></nav>'
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang=\"ja\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{title} | 貨幣論教科書</title>
  <link rel=\"stylesheet\" href=\"assets/style.css\" />
</head>
<body>
<header class=\"site-header\">
  <h1><a href=\"index.html\">貨幣論教科書</a></h1>
  <p class=\"tagline\">古典から現代までの貨幣論を学ぶ</p>
</header>
<main class=\"container\">
  {nav}
  <article class=\"content\">
  {content}
  </article>
</main>
<footer class=\"site-footer\">
  <p>&copy; {year} 貨幣論プロジェクト</p>
</footer>
</body>
</html>
"""

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang=\"ja\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>貨幣論教科書 | 章一覧</title>
  <link rel=\"stylesheet\" href=\"assets/style.css\" />
</head>
<body>
<header class=\"site-header\">
  <h1>貨幣論教科書</h1>
  <p class=\"tagline\">古典から現代までの貨幣論を学ぶ</p>
</header>
<main class=\"container\">
  <section>
    <h2>章一覧</h2>
    <ul class=\"chapter-list\">
      {items}
    </ul>
  </section>
</main>
<footer class=\"site-footer\">
  <p>&copy; {year} 貨幣論プロジェクト</p>
</footer>
</body>
</html>
"""

MD_EXTENSIONS = ["extra", "toc", "tables", "codehilite"]

LINK_PATTERN = re.compile(r'href=\"([^\"]+?)\.md(#[^\"]*)?\"')


def clean_output_dir() -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Chapter:
    source: Path
    title: str
    output_name: str


def load_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def extract_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return re.sub(r"^#+\\s*", "", stripped)
    return fallback


def convert_links(html: str) -> str:
    def _replace(match: re.Match[str]) -> str:
        href = match.group(1)
        anchor = match.group(2) or ""
        if href.startswith("http://") or href.startswith("https://"):
            return match.group(0)
        
        # Handle chapters/ prefix - remove it since all HTML files are in root
        if href.startswith("chapters/"):
            href = href[9:]  # Remove "chapters/" prefix
        
        # Handle other directory prefixes (glossary/, references/, etc.)
        if "/" in href:
            href = href.split("/")[-1]  # Get just the filename
            
        return f'href="{href}.html{anchor}"'

    return LINK_PATTERN.sub(_replace, html)


def render_chapter(chapter: Chapter, year: int) -> str:
    md_text = load_markdown(chapter.source)
    html_body = markdown.markdown(md_text, extensions=MD_EXTENSIONS, output_format="html5")
    html_body = convert_links(html_body)
    return HTML_TEMPLATE.format(title=chapter.title, nav=NAVIGATION_LINK, content=html_body, year=year)


def build_chapters() -> List[Chapter]:
    chapters: List[Chapter] = []
    if not CHAPTERS_DIR.exists():
        raise FileNotFoundError(f"Chapters directory not found: {CHAPTERS_DIR}")

    # Build chapters from chapters/ directory
    for md_file in sorted(CHAPTERS_DIR.glob("*.md")):
        text = load_markdown(md_file)
        title = extract_title(text, md_file.stem)
        output_name = f"{md_file.stem}.html"
        chapter = Chapter(source=md_file, title=title, output_name=output_name)
        chapters.append(chapter)
    
    # Build additional files from glossary/ and references/ directories
    additional_dirs = [BASE_DIR / "glossary", BASE_DIR / "references"]
    for dir_path in additional_dirs:
        if dir_path.exists():
            for md_file in sorted(dir_path.glob("*.md")):
                text = load_markdown(md_file)
                title = extract_title(text, md_file.stem)
                output_name = f"{md_file.stem}.html"
                chapter = Chapter(source=md_file, title=title, output_name=output_name)
                chapters.append(chapter)
    
    return chapters


def write_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def copy_static_assets() -> None:
    source_assets = BASE_DIR / "assets"
    if source_assets.exists():
        target_assets = ASSETS_DIR / "uploads"
        shutil.copytree(source_assets, target_assets, dirs_exist_ok=True)

    figures_dir = BASE_DIR / "figures"
    if figures_dir.exists():
        target_figures = ASSETS_DIR / "figures"
        shutil.copytree(figures_dir, target_figures, dirs_exist_ok=True)

    stylesheet = ASSETS_DIR / "style.css"
    stylesheet.write_text(
        """
:root {
  color-scheme: light;
  --text-color: #1a1a1a;
  --background-color: #fafafa;
  --accent-color: #0070f3;
  --border-color: #e0e0e0;
}

body {
  margin: 0;
  font-family: \"Hiragino Sans\", \"Noto Sans JP\", \"Yu Gothic\", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
  color: var(--text-color);
  background-color: var(--background-color);
  line-height: 1.7;
}

.site-header, .site-footer {
  text-align: center;
  padding: 2rem 1rem;
  background-color: white;
  border-bottom: 1px solid var(--border-color);
}

.site-footer {
  border-top: 1px solid var(--border-color);
  border-bottom: none;
}

.site-header a {
  text-decoration: none;
  color: inherit;
}

.container {
  max-width: 960px;
  margin: 0 auto;
  padding: 2rem 1.5rem 4rem;
  background-color: white;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
}

.chapter-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1rem;
}

.chapter-list li {
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 1rem;
  background-color: #fff;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.chapter-list li:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
}

.chapter-list a {
  text-decoration: none;
  color: var(--text-color);
  font-weight: 600;
}

.breadcrumbs {
  margin-bottom: 1.5rem;
  font-size: 0.95rem;
}

.content h1 {
  font-size: 2.2rem;
  margin-top: 0;
}

.content img {
  max-width: 100%;
  height: auto;
}

pre code {
  display: block;
  padding: 1rem;
  background-color: #1e1e1e;
  color: #f4f4f4;
  overflow-x: auto;
  border-radius: 8px;
}

code {
  font-family: \"Fira Code\", \"Source Code Pro\", monospace;
  background-color: rgba(0, 112, 243, 0.1);
  padding: 0.1rem 0.3rem;
  border-radius: 4px;
}
        """.strip()
    )


def render_index_from_readme(chapters: Iterable[Chapter], year: int) -> str:
    readme_path = BASE_DIR / "README.md"
    if readme_path.exists():
        readme_content = load_markdown(readme_path)
        html_content = markdown.markdown(readme_content, extensions=MD_EXTENSIONS, output_format="html5")
        html_content = convert_links(html_content)
        return HTML_TEMPLATE.format(
            title="貨幣論教科書", 
            nav="", 
            content=html_content, 
            year=year
        )
    else:
        # Fallback to original chapter list if README.md doesn't exist
        items_html = "\n      ".join(
            f'<li><a href="{chapter.output_name}">{chapter.title}</a></li>'
            for chapter in chapters
        )
        return INDEX_TEMPLATE.format(items=items_html, year=year)


def main() -> None:
    if not CHAPTERS_DIR.exists():
        raise SystemExit("chapters directory does not exist")

    clean_output_dir()
    copy_static_assets()

    chapters = build_chapters()
    from datetime import datetime

    year = datetime.utcnow().year

    for chapter in chapters:
        html = render_chapter(chapter, year)
        target_path = OUTPUT_DIR / chapter.output_name
        write_file(target_path, html)

    index_html = render_index_from_readme(chapters, year)
    write_file(OUTPUT_DIR / "index.html", index_html)


if __name__ == "__main__":
    main()
