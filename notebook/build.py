"""Generate a static website from the notes, linked by topic clusters."""

from __future__ import annotations

import html
import shutil
from pathlib import Path

import markdown

from notebook.config import NOTES_DIR
from notebook.store import list_notes, Note
from notebook.wiki import SKIP_FILES

SITE_DIR = Path("site")

CSS = """\
:root {
  --bg: #1a1b26;
  --surface: #24283b;
  --border: #3b4261;
  --text: #c0caf5;
  --text-muted: #565f89;
  --accent: #7aa2f7;
  --accent-hover: #89b4fa;
  --heading: #bb9af7;
  --link: #7dcfff;
  --link-hover: #73daca;
  --tag-bg: #292e42;
  --code-bg: #292e42;
  --sidebar-bg: #1f2335;
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.7;
}
a { color: var(--link); text-decoration: none; }
a:hover { color: var(--link-hover); text-decoration: underline; }

.layout {
  display: grid;
  grid-template-columns: 260px 1fr 240px;
  min-height: 100vh;
}
@media (max-width: 900px) {
  .layout { grid-template-columns: 1fr; }
  .sidebar, .related { display: none; }
}
@media (min-width: 901px) and (max-width: 1200px) {
  .layout { grid-template-columns: 220px 1fr; }
  .related { display: none; }
}

.sidebar {
  background: var(--sidebar-bg);
  border-right: 1px solid var(--border);
  padding: 1.5rem 1rem;
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
}
.sidebar h2 {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--text-muted);
  margin: 1.5rem 0 0.5rem 0;
}
.sidebar h2:first-child { margin-top: 0; }
.sidebar ul { list-style: none; }
.sidebar li { margin: 0.2rem 0; }
.sidebar a {
  display: block;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.9rem;
  color: var(--text);
}
.sidebar a:hover { background: var(--border); text-decoration: none; }
.sidebar a.active { background: var(--accent); color: var(--bg); font-weight: 600; }
.site-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--accent);
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--border);
}

main {
  padding: 2rem 3rem;
  max-width: 800px;
}
main h1 { color: var(--heading); font-size: 1.8rem; margin-bottom: 1rem; }
main h2 { color: var(--heading); font-size: 1.3rem; margin: 1.5rem 0 0.5rem; }
main h3 { color: var(--heading); font-size: 1.1rem; margin: 1.2rem 0 0.4rem; }
main p { margin: 0.6rem 0; }
main ul, main ol { margin: 0.6rem 0 0.6rem 1.5rem; }
main li { margin: 0.2rem 0; }
main code {
  background: var(--code-bg);
  padding: 0.15em 0.4em;
  border-radius: 3px;
  font-size: 0.9em;
}
main pre {
  background: var(--code-bg);
  padding: 1rem;
  border-radius: 6px;
  overflow-x: auto;
  margin: 0.8rem 0;
}
main pre code { background: none; padding: 0; }
main hr { border: none; border-top: 1px solid var(--border); margin: 1.5rem 0; }
main blockquote {
  border-left: 3px solid var(--accent);
  padding-left: 1rem;
  color: var(--text-muted);
  margin: 0.8rem 0;
}

.related {
  background: var(--sidebar-bg);
  border-left: 1px solid var(--border);
  padding: 1.5rem 1rem;
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
}
.related h2 {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}
.related ul { list-style: none; }
.related li { margin: 0.3rem 0; }
.related a {
  font-size: 0.85rem;
  color: var(--text);
}
.related a:hover { color: var(--link-hover); }
.related .score {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-left: 0.3rem;
}
.cluster-tag {
  display: inline-block;
  background: var(--tag-bg);
  border: 1px solid var(--border);
  padding: 0.1rem 0.6rem;
  border-radius: 12px;
  font-size: 0.8rem;
  color: var(--text-muted);
  margin: 0.2rem 0.2rem 0.2rem 0;
}
"""

md = markdown.Markdown(extensions=["fenced_code", "tables", "toc"])


def note_to_slug(note: Note) -> str:
    return note.path.stem


def slug_to_html(slug: str) -> str:
    return f"{slug}.html"


def render_markdown(content: str) -> str:
    md.reset()
    return md.convert(content)


def rewrite_md_links(html_content: str) -> str:
    """Rewrite .md links to .html for the static site."""
    import re
    return re.sub(r'href="([^"]+)\.md"', r'href="\1.html"', html_content)


def build_page(title: str, body: str, sidebar: str, related: str, slug: str, site_title: str = "Semantic Notebook") -> str:
    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} — {html.escape(site_title)}</title>
<style>{CSS}</style>
</head>
<body>
<div class="layout">
<nav class="sidebar">
{sidebar}
</nav>
<main>
{body}
</main>
<aside class="related">
{related}
</aside>
</div>
</body>
</html>
"""


def build_sidebar(clusters: list, all_notes: list[Note], active_slug: str = "", site_title: str = "Semantic Notebook") -> str:
    lines = [f'<div class="site-title"><a href="index.html">{html.escape(site_title)}</a></div>']

    if clusters:
        for cluster in clusters:
            lines.append(f"<h2>{html.escape(cluster.label)}</h2>")
            lines.append("<ul>")
            for nid, title in zip(cluster.note_ids, cluster.note_titles):
                slug = Path(nid).stem
                active = ' class="active"' if slug == active_slug else ""
                lines.append(f'<li><a href="{slug_to_html(slug)}"{active}>{html.escape(title)}</a></li>')
            lines.append("</ul>")
    else:
        lines.append("<h2>All Notes</h2><ul>")
        for note in all_notes:
            slug = note_to_slug(note)
            active = ' class="active"' if slug == active_slug else ""
            lines.append(f'<li><a href="{slug_to_html(slug)}"{active}>{html.escape(note.title)}</a></li>')
        lines.append("</ul>")

    return "\n".join(lines)


def build_related_panel(note: Note, all_notes: list[Note]) -> str:
    try:
        from notebook.linker import find_related
        related = find_related(note.rel_path, n=5)
    except Exception:
        related = []

    if not related:
        return "<h2>Related Notes</h2><p style='font-size:0.85rem;color:var(--text-muted)'>None found</p>"

    lines = ["<h2>Related Notes</h2>", "<ul>"]
    for r in related:
        title = r.get("metadata", {}).get("title", r["id"])
        score = r.get("score", 0)
        slug = Path(r["id"]).stem
        lines.append(
            f'<li><a href="{slug_to_html(slug)}">{html.escape(title)}</a>'
            f'<span class="score">{score:.0%}</span></li>'
        )
    lines.append("</ul>")
    return "\n".join(lines)


def build_index_page(clusters: list, all_notes: list[Note], sidebar: str, site_title: str = "Semantic Notebook") -> str:
    lines = [f"<h1>{html.escape(site_title)}</h1>"]
    lines.append(f"<p>{len(all_notes)} notes across {len(clusters)} topics.</p>")

    if clusters:
        for cluster in clusters:
            lines.append(f'<h2>{html.escape(cluster.label)}</h2>')
            lines.append("<ul>")
            for nid, title in zip(cluster.note_ids, cluster.note_titles):
                slug = Path(nid).stem
                lines.append(f'<li><a href="{slug_to_html(slug)}">{html.escape(title)}</a></li>')
            lines.append("</ul>")
    else:
        lines.append("<ul>")
        for note in all_notes:
            slug = note_to_slug(note)
            lines.append(f'<li><a href="{slug_to_html(slug)}">{html.escape(note.title)}</a></li>')
        lines.append("</ul>")

    body = "\n".join(lines)
    related = "<h2>Topics</h2><ul>"
    for c in clusters:
        related += f'<li><span class="cluster-tag">{html.escape(c.label)}</span></li>'
    related += "</ul>"

    return build_page("Home", body, sidebar, related, slug="index", site_title=site_title)


def build_site(title: str = "Semantic Notebook"):
    notes = list_notes()
    notes = [n for n in notes if n.path.name not in SKIP_FILES]

    # Get clusters
    try:
        from notebook.clusters import get_clusters
        clusters = get_clusters()
    except Exception:
        clusters = []

    # Prepare output dir
    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
    SITE_DIR.mkdir(parents=True)

    # Build sidebar (shared)
    sidebar_html = build_sidebar(clusters, notes, site_title=title)

    # Index page
    index_html = build_index_page(clusters, notes, sidebar_html, site_title=title)
    (SITE_DIR / "index.html").write_text(index_html, encoding="utf-8")

    # Individual note pages
    for note in notes:
        slug = note_to_slug(note)
        note_sidebar = build_sidebar(clusters, notes, active_slug=slug, site_title=title)
        body_html = render_markdown(note.content)
        body_html = rewrite_md_links(body_html)
        related_html = build_related_panel(note, notes)

        page_html = build_page(note.title, body_html, note_sidebar, related_html, slug, site_title=title)
        (SITE_DIR / slug_to_html(slug)).write_text(page_html, encoding="utf-8")

    return {"pages": len(notes) + 1, "clusters": len(clusters)}
