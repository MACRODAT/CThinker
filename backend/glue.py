"""
glue.py — GLUE wiki engine for CThink
Handles all vault/wiki operations: ingest, query, lint, git, thread linking.
Optimised for small LLMs (gemma 4b / 7-8b): short prompts, chunked I/O.
"""

import os
import re
import json
import datetime
import subprocess
import asyncio
import httpx
import shutil
from pathlib import Path
from typing import Optional

VAULT_BASE = Path(__file__).parent / "vault"

# ── Vault helpers ──────────────────────────────────────────────────────────────

def vault_path(vault_id: str) -> Path:
    return VAULT_BASE / vault_id

def wiki_path(vault_id: str) -> Path:
    return vault_path(vault_id) / "wiki"

def raw_path(vault_id: str) -> Path:
    return vault_path(vault_id) / "raw"

def index_path(vault_id: str) -> Path:
    return vault_path(vault_id) / "index.md"

def log_path(vault_id: str) -> Path:
    return vault_path(vault_id) / "log.md"

def agents_path(vault_id: str) -> Path:
    return vault_path(vault_id) / "Agents.md"

def today() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

# ── List vaults ────────────────────────────────────────────────────────────────

def list_vaults() -> list[str]:
    if not VAULT_BASE.exists():
        return []
    return [d.name for d in VAULT_BASE.iterdir() if d.is_dir() and not d.name.startswith(".")]

# ── Bootstrap a new vault ──────────────────────────────────────────────────────

def init_vault(vault_id: str):
    vp = vault_path(vault_id)
    dirs = [
        vp / "raw" / "inbox",
        vp / "raw" / "library",
        vp / "raw" / "assets",
        vp / "wiki" / "sources",
        vp / "wiki" / "concepts",
        vp / "wiki" / "entities",
        vp / "wiki" / "syntheses",
        vp / "wiki" / "queries",
        vp / "wiki" / "meta",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    if not index_path(vault_id).exists():
        index_path(vault_id).write_text(
            "# Index\n\n## Sources\n\n## Concepts\n\n## Entities\n\n## Syntheses\n\n## Queries\n",
            encoding="utf-8"
        )
    if not log_path(vault_id).exists():
        log_path(vault_id).write_text(
            f"# Log\n\n## [{today()}] schema | Vault initialised\n- Vault `{vault_id}` created.\n",
            encoding="utf-8"
        )
    _git_init(vault_id)


# ── Git helpers ────────────────────────────────────────────────────────────────

def _git(vault_id: str, *args) -> str:
    vp = str(vault_path(vault_id))
    try:
        r = subprocess.run(["git"] + list(args), cwd=vp, capture_output=True, text=True, timeout=15)
        return (r.stdout + r.stderr).strip()
    except FileNotFoundError:
        return "[GIT_NOT_FOUND]"
    except Exception as e:
        return f"[GIT_ERR:{e}]"

def _git_init(vault_id: str):
    vp = vault_path(vault_id)
    if not (vp / ".git").exists():
        _git(vault_id, "init")
        _git(vault_id, "config", "user.email", "cthinker@local")
        _git(vault_id, "config", "user.name", "CThinker")

def git_status(vault_id: str) -> dict:
    status = _git(vault_id, "status", "--short")
    log = _git(vault_id, "log", "--oneline", "-20")
    return {"status": status, "log": log}

def git_stage(vault_id: str, paths: list[str]) -> str:
    """Stage specific wiki files for commit."""
    results = []
    for p in paths:
        results.append(_git(vault_id, "add", p))
    return "\n".join(results)

def git_stage_all(vault_id: str) -> str:
    """Stage all changes."""
    return _git(vault_id, "add", "-A")

def git_commit(vault_id: str, message: str) -> str:
    _git(vault_id, "add", "-A")
    return _git(vault_id, "commit", "-m", message)

def git_diff(vault_id: str, filepath: str = None) -> str:
    if filepath:
        return _git(vault_id, "diff", "--cached", filepath)
    return _git(vault_id, "diff", "--cached")

def git_log(vault_id: str, n: int = 20) -> str:
    return _git(vault_id, "log", "--oneline", f"-{n}")

def git_show(vault_id: str, ref: str) -> str:
    return _git(vault_id, "show", ref, "--stat")

def git_diff_unstaged(vault_id: str) -> str:
    return _git(vault_id, "diff")

def git_revert(vault_id: str, ref: str) -> str:
    """Revert a specific commit."""
    return _git(vault_id, "revert", "--no-edit", ref)

def git_discard(vault_id: str, filepath: str) -> str:
    """Discard unstaged changes to a specific file."""
    return _git(vault_id, "checkout", "--", filepath)

def git_diff_full(vault_id: str) -> str:
    """Combined diff: staged + unstaged."""
    staged = _git(vault_id, "diff", "--cached")
    unstaged = _git(vault_id, "diff")
    parts = []
    if staged.strip():
        parts.append(f"=== STAGED ===\n{staged}")
    if unstaged.strip():
        parts.append(f"=== UNSTAGED ===\n{unstaged}")
    return "\n\n".join(parts) if parts else "(no changes)"


# ── File I/O helpers ───────────────────────────────────────────────────────────

def read_file(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")

def write_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def append_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(content)

# ── Index operations ───────────────────────────────────────────────────────────

def read_index(vault_id: str) -> str:
    return read_file(index_path(vault_id))

def update_index_entry(vault_id: str, category: str, page_rel: str, summary: str):
    """Add or update a line in index.md under the given category."""
    idx = read_index(vault_id)
    entry = f"- [[{page_rel}]] — {summary}"
    header = f"## {category}"
    if header not in idx:
        idx += f"\n{header}\n{entry}\n"
    else:
        # Find if entry already exists; update or append
        lines = idx.split("\n")
        new_lines = []
        in_section = False
        inserted = False
        for line in lines:
            if line.strip() == header:
                in_section = True
            elif line.startswith("## ") and in_section:
                if not inserted:
                    new_lines.append(entry)
                    inserted = True
                in_section = False
            if in_section and page_rel in line:
                new_lines.append(entry)
                inserted = True
                continue
            new_lines.append(line)
        if not inserted:
            new_lines.append(entry)
        idx = "\n".join(new_lines)
    write_file(index_path(vault_id), idx)

def remove_index_entry(vault_id: str, page_rel: str):
    """Remove a page from index.md."""
    idx = read_index(vault_id)
    lines = idx.split("\n")
    new_lines = [l for l in lines if page_rel not in l]
    write_file(index_path(vault_id), "\n".join(new_lines))

def append_log(vault_id: str, operation: str, label: str, body: str):
    entry = f"\n## [{today()}] {operation} | {label}\n{body}\n"
    append_file(log_path(vault_id), entry)


# ── Wiki CRUD (no LLM — fast, deterministic) ──────────────────────────────────

def list_wiki_pages(vault_id: str, category: str = None) -> list[dict]:
    """List all wiki pages, optionally filtered by subfolder/category."""
    wp = wiki_path(vault_id)
    if not wp.exists():
        return []
    
    if category:
        folder = wp / category
        if not folder.exists():
            return []
        pages = list(folder.rglob("*.md"))
    else:
        pages = list(wp.rglob("*.md"))
    
    result = []
    for p in sorted(pages):
        rel = str(p.relative_to(vault_path(vault_id))).replace("\\", "/")
        stat = p.stat()
        result.append({
            "path": rel,
            "name": p.stem,
            "category": p.parent.name,
            "size": stat.st_size,
            "modified": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })
    return result


def read_wiki_page(vault_id: str, page_rel: str) -> dict:
    """Read a specific wiki page by relative path."""
    p = vault_path(vault_id) / page_rel
    if not p.exists():
        return {"error": f"Page not found: {page_rel}"}
    content = read_file(p)
    links = re.findall(r"\[\[([^\]]+)\]\]", content)
    return {"path": page_rel, "content": content, "links": links}


def write_wiki_page(vault_id: str, page_rel: str, content: str) -> dict:
    """Create or overwrite a wiki page."""
    p = vault_path(vault_id) / page_rel
    is_new = not p.exists()
    write_file(p, content)
    git_stage(vault_id, [page_rel])
    return {"status": "created" if is_new else "updated", "path": page_rel}


def update_wiki_section(vault_id: str, page_rel: str, section: str, new_content: str) -> dict:
    """Update a specific ## Section in a page, preserving the rest."""
    p = vault_path(vault_id) / page_rel
    if not p.exists():
        return {"error": f"Page not found: {page_rel}"}
    
    content = read_file(p)
    # Find the section header and replace its content until the next ## or end
    pattern = re.compile(
        rf"(## {re.escape(section)}\n)(.*?)(?=\n## |\Z)",
        re.DOTALL
    )
    match = pattern.search(content)
    if not match:
        # Section not found — append it
        content += f"\n## {section}\n{new_content}\n"
    else:
        content = content[:match.start(2)] + new_content + "\n" + content[match.end(2):]
    
    write_file(p, content)
    git_stage(vault_id, [page_rel])
    return {"status": "section_updated", "path": page_rel, "section": section}


def delete_wiki_page(vault_id: str, page_rel: str) -> dict:
    """Delete a wiki page and remove from index."""
    p = vault_path(vault_id) / page_rel
    if not p.exists():
        return {"error": f"Page not found: {page_rel}"}
    p.unlink()
    remove_index_entry(vault_id, page_rel)
    git_stage(vault_id, [page_rel, "index.md"])
    return {"status": "deleted", "path": page_rel}


def search_wiki(vault_id: str, keywords: list[str]) -> list[dict]:
    """Multi-keyword full-text search across wiki pages. Ranked by hit count."""
    results = []
    for page in _collect_wiki_pages(vault_id):
        content_lower = page["content"].lower()
        hits = sum(1 for kw in keywords if kw.lower() in content_lower)
        if hits > 0:
            # Build snippet around first keyword found
            snippet = ""
            for kw in keywords:
                if kw.lower() in content_lower:
                    snippet = _snippet(page["content"], kw)
                    break
            results.append({
                "path": page["path"],
                "hits": hits,
                "snippet": snippet,
            })
    results.sort(key=lambda x: x["hits"], reverse=True)
    return results[:15]


# ── LLM call helper ────────────────────────────────────────────────────────────

async def _llm(db, system: str, prompt: str, max_tokens: int = 800) -> str:
    """
    Lightweight LLM call tuned for small models (gemma 4b / 7-8b).
    Short system prompt, constrained output.
    """
    from models import Setting
    s_url = db.query(Setting).filter(Setting.key == "ollama_server").first()
    s_mod = db.query(Setting).filter(Setting.key == "ollama_model").first()
    server = (s_url.value if s_url else "http://localhost:11434").rstrip("/")
    model = s_mod.value if s_mod else "gemma3:4b"

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{server}/api/generate",
                json={
                    "model": model,
                    "system": system,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": max_tokens, "temperature": 0.3, "top_p": 0.9},
                },
                timeout=180.0,
            )
            return resp.json().get("response", "").strip()
    except Exception as e:
        return f"[LLM_ERR:{e}]"


# ── INGEST ─────────────────────────────────────────────────────────────────────

SYS_INGEST = """You are a wiki maintainer. Read the source and produce a compact wiki page.
OUTPUT ONLY valid markdown with these sections:
# Title
## Summary
(3-5 bullets)
## Details
(key claims, evidence, dates)
## Links
- Related: 
- Entities: 
- Concepts: 
- Sources: 
## Sources
Keep it under 400 words. No preamble."""

SYS_UPDATE_PAGE = """You are a wiki editor. Merge new information into the existing page.
Keep existing content. Add new claims under ## Details. Update ## Links if needed.
OUTPUT the full updated page only. Under 500 words. No preamble."""

async def ingest_source(db, vault_id: str, filename: str) -> dict:
    """
    Ingest a file from raw/inbox into the wiki.
    1. Read source -> summarise -> write wiki/sources/ page
    2. Update index + log
    3. Git stage the changes
    Returns dict with pages_created, pages_updated, summary_preview.
    """
    inbox = raw_path(vault_id) / "inbox" / filename
    if not inbox.exists():
        return {"error": f"File not found in inbox: {filename}"}

    raw_content = read_file(inbox)
    if len(raw_content) > 6000:
        raw_content = raw_content[:6000] + "\n...[truncated]"

    # 1. Generate source summary page
    prompt = f"SOURCE FILE: {filename}\n\nCONTENT:\n{raw_content}"
    summary_md = await _llm(db, SYS_INGEST, prompt, max_tokens=600)

    # Extract title from first H1
    title_match = re.search(r"^#\s+(.+)$", summary_md, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else Path(filename).stem
    slug = re.sub(r"[^\w\-]", "-", title.lower())[:40]
    page_name = f"{today()}-{slug}.md"
    page_path = wiki_path(vault_id) / "sources" / page_name

    # Add frontmatter
    frontmatter = f"---\ntype: source\nstatus: active\ncreated: {today()}\nsource_file: {filename}\n---\n\n"
    write_file(page_path, frontmatter + summary_md)

    # 2. Move source to library
    lib_dest = raw_path(vault_id) / "library" / filename
    lib_dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(inbox), str(lib_dest))

    # 3. Update index
    one_liner = re.sub(r"[#\n\-\*]", " ", summary_md)[:100].strip()
    update_index_entry(vault_id, "Sources", f"wiki/sources/{page_name}", one_liner)

    # 4. Append log
    append_log(vault_id, "ingest", title,
               f"- Source: `{filename}`\n- Wiki page: `wiki/sources/{page_name}`\n- Summary: {one_liner}")

    # 5. Git stage
    git_stage(vault_id, [f"wiki/sources/{page_name}", "index.md", "log.md"])

    return {
        "status": "ok",
        "page": str(page_path.relative_to(vault_path(vault_id))),
        "title": title,
        "preview": summary_md[:300],
    }


async def ingest_text(db, vault_id: str, title: str, content: str) -> dict:
    """Ingest raw text (no file) directly into wiki/sources/."""
    slug = re.sub(r"[^\w\-]", "-", title.lower())[:40]
    page_name = f"{today()}-{slug}.md"
    page_path = wiki_path(vault_id) / "sources" / page_name

    prompt = f"SOURCE TITLE: {title}\n\nCONTENT:\n{content[:5000]}"
    summary_md = await _llm(db, SYS_INGEST, prompt, max_tokens=600)

    frontmatter = f"---\ntype: source\nstatus: active\ncreated: {today()}\n---\n\n"
    write_file(page_path, frontmatter + summary_md)

    one_liner = re.sub(r"[#\n\-\*]", " ", summary_md)[:100].strip()
    update_index_entry(vault_id, "Sources", f"wiki/sources/{page_name}", one_liner)
    append_log(vault_id, "ingest", title,
               f"- Direct text ingest\n- Wiki page: `wiki/sources/{page_name}`")
    git_stage(vault_id, [f"wiki/sources/{page_name}", "index.md", "log.md"])

    return {"status": "ok", "page": f"wiki/sources/{page_name}", "preview": summary_md[:300]}


async def ingest_url(db, vault_id: str, url: str) -> dict:
    """Fetch a URL, extract text, summarize, and add to wiki/sources/."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, timeout=15.0, follow_redirects=True)
            html = resp.text

        # Strip HTML to plain text
        text = re.sub(r'<(script|style|noscript)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        import html as html_mod
        text = html_mod.unescape(text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        if len(text) < 50:
            return {"error": "Page content too short or blocked."}

        # Truncate for LLM
        text = text[:5000]

        # Extract title from <title> tag
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else url.split("/")[-1][:40]

        prompt = f"SOURCE URL: {url}\nTITLE: {title}\n\nCONTENT:\n{text}"
        summary_md = await _llm(db, SYS_INGEST, prompt, max_tokens=600)

        slug = re.sub(r"[^\w\-]", "-", title.lower())[:40]
        page_name = f"{today()}-{slug}.md"
        page_path = wiki_path(vault_id) / "sources" / page_name

        frontmatter = f"---\ntype: source\nstatus: active\ncreated: {today()}\nsource_url: {url}\n---\n\n"
        write_file(page_path, frontmatter + summary_md)

        one_liner = re.sub(r"[#\n\-\*]", " ", summary_md)[:100].strip()
        update_index_entry(vault_id, "Sources", f"wiki/sources/{page_name}", one_liner)
        append_log(vault_id, "ingest", title,
                   f"- URL ingest: `{url}`\n- Wiki page: `wiki/sources/{page_name}`")
        git_stage(vault_id, [f"wiki/sources/{page_name}", "index.md", "log.md"])

        return {"status": "ok", "page": f"wiki/sources/{page_name}", "title": title, "preview": summary_md[:300]}

    except Exception as e:
        return {"error": f"URL ingest failed: {str(e)}"}


# ── QUERY ──────────────────────────────────────────────────────────────────────

SYS_QUERY = """You are a wiki assistant. Answer using only the wiki pages provided.
Be concise. Cite page filenames like [source: filename]. Under 350 words."""

def _collect_wiki_pages(vault_id: str) -> list[dict]:
    """Return list of {path, content} for all wiki pages."""
    pages = []
    for p in wiki_path(vault_id).rglob("*.md"):
        rel = str(p.relative_to(vault_path(vault_id))).replace("\\", "/")
        content = read_file(p)
        pages.append({"path": rel, "content": content})
    return pages

def query_by_keyword(vault_id: str, keyword: str) -> list[dict]:
    """Full-text search across wiki pages."""
    kw = keyword.lower()
    results = []
    for page in _collect_wiki_pages(vault_id):
        if kw in page["content"].lower():
            snippet = _snippet(page["content"], kw)
            results.append({"path": page["path"], "snippet": snippet})
    return results

def query_by_category(vault_id: str, category: str) -> list[dict]:
    """List all pages in a wiki subfolder (sources/concepts/entities/...)."""
    folder = wiki_path(vault_id) / category
    if not folder.exists():
        return []
    return [
        {"path": str(p.relative_to(vault_path(vault_id))).replace("\\", "/"), "title": p.stem}
        for p in folder.glob("*.md")
    ]

def query_by_date(vault_id: str, date_prefix: str) -> list[dict]:
    """Find pages whose filename starts with a date prefix (e.g. '2026-04')."""
    results = []
    for page in _collect_wiki_pages(vault_id):
        fname = Path(page["path"]).name
        if fname.startswith(date_prefix):
            results.append({"path": page["path"], "title": fname})
    return results

def follow_node(vault_id: str, page_rel: str) -> dict:
    """Read a wiki page and return its content + outbound links."""
    p = vault_path(vault_id) / page_rel
    content = read_file(p)
    links = re.findall(r"\[\[([^\]]+)\]\]", content)
    return {"path": page_rel, "content": content, "links": links}

def query_recent(vault_id: str, n: int = 10) -> list[dict]:
    """Get the N most recently modified wiki pages."""
    pages = list_wiki_pages(vault_id)
    pages.sort(key=lambda p: p.get("modified", ""), reverse=True)
    return pages[:n]

def query_backlinks(vault_id: str, page_rel: str) -> list[dict]:
    """Find all wiki pages that link to a given page."""
    # Extract the page name for matching [[page-name]] links
    page_name = Path(page_rel).stem
    results = []
    for page in _collect_wiki_pages(vault_id):
        if page["path"] == page_rel:
            continue
        links = re.findall(r"\[\[([^\]]+)\]\]", page["content"])
        for link in links:
            if page_name in link or page_rel in link:
                results.append({"path": page["path"], "link_text": link})
                break
    return results


def _snippet(content: str, keyword: str, window: int = 200) -> str:
    idx = content.lower().find(keyword.lower())
    if idx < 0:
        return content[:window]
    start = max(0, idx - 80)
    end = min(len(content), idx + window)
    return "..." + content[start:end] + "..."

async def query_wiki(db, vault_id: str, question: str, save: bool = False) -> dict:
    """
    Answer a question from the wiki.
    1. Read index to find relevant pages.
    2. Load top matching pages.
    3. LLM synthesises answer.
    4. Optionally save to wiki/queries/.
    """
    idx = read_index(vault_id)
    
    # Multi-keyword search: split question into words, search for each
    words = [w for w in question.lower().split() if len(w) > 3][:5]
    if words:
        hits = search_wiki(vault_id, words)[:5]
    else:
        hits = query_by_keyword(vault_id, question.split()[0])[:5]
    
    # Collect content of hit pages (truncated for small LLMs)
    context_parts = []
    for h in hits:
        page = vault_path(vault_id) / h["path"]
        content = read_file(page)[:800]
        context_parts.append(f"=== {h['path']} ===\n{content}")
    
    context = "\n\n".join(context_parts) if context_parts else idx[:1500]
    prompt = f"QUESTION: {question}\n\nWIKI PAGES:\n{context}"
    answer = await _llm(db, SYS_QUERY, prompt, max_tokens=400)
    
    result = {"question": question, "answer": answer, "pages_used": [h["path"] for h in hits]}
    
    if save or True:
        slug = re.sub(r"[^\w\-]", "-", question.lower())[:40]
        page_name = f"{today()}-{slug}.md"
        page_path = wiki_path(vault_id) / "queries" / page_name
        md = f"# Q: {question}\n\n## Answer\n{answer}\n\n## Pages Used\n"
        md += "\n".join([f"- [[{p}]]" for p in result["pages_used"]])
        write_file(page_path, f"---\ntype: query\ncreated: {today()}\n---\n\n" + md)
        update_index_entry(vault_id, "Queries", f"wiki/queries/{page_name}", question[:80])
        append_log(vault_id, "query", question[:60],
                   f"- Saved: `wiki/queries/{page_name}`\n- Pages: {', '.join(result['pages_used'][:3])}")
        git_stage(vault_id, [f"wiki/queries/{page_name}", "index.md", "log.md"])
        result["saved_to"] = f"wiki/queries/{page_name}"
    
    return result


# ── LINT ───────────────────────────────────────────────────────────────────────

SYS_LINT = """You are a wiki auditor. Given a list of wiki issues, write a concise lint report.
Group by issue type. Suggest fixes. Markdown format. Under 400 words."""

async def lint_wiki(db, vault_id: str) -> dict:
    """
    Full wiki health check:
    - Orphan pages (no inbound links)
    - Thin pages (< 200 chars)
    - Broken links (page referenced but doesn't exist)
    - Mentioned concepts/entities without own page
    - Pages missing ## Links section
    Writes report to wiki/meta/lint-YYYY-MM-DD.md
    """
    pages = _collect_wiki_pages(vault_id)
    all_paths = {p["path"] for p in pages}
    all_stems = {Path(p["path"]).stem for p in pages}
    
    issues = {
        "orphans": [],      # pages with no inbound links
        "thin": [],         # pages under 200 chars
        "broken_links": [], # [[links]] to nonexistent pages
        "no_links_section": [],  # pages missing ## Links
        "missing_pages": set(),  # concepts/entities mentioned but no page
    }
    
    # Build inbound link map
    inbound = {p["path"]: [] for p in pages}
    for page in pages:
        links = re.findall(r"\[\[([^\]]+)\]\]", page["content"])
        for link in links:
            # Try to find matching page
            matched = False
            for path in all_paths:
                if link in path or Path(path).stem == link:
                    inbound[path].append(page["path"])
                    matched = True
                    break
            if not matched and link not in all_stems:
                issues["broken_links"].append({"from": page["path"], "link": link})
                issues["missing_pages"].add(link)
    
    for page in pages:
        # Skip meta and index files
        if "meta/" in page["path"] or page["path"] in ("index.md", "log.md"):
            continue
        if not inbound.get(page["path"]):
            issues["orphans"].append(page["path"])
        if len(page["content"]) < 200:
            issues["thin"].append(page["path"])
        if "## Links" not in page["content"]:
            issues["no_links_section"].append(page["path"])
    
    issues["missing_pages"] = list(issues["missing_pages"])
    
    # Count issues
    issue_count = (len(issues["orphans"]) + len(issues["thin"]) + 
                   len(issues["broken_links"]) + len(issues["no_links_section"]) +
                   len(issues["missing_pages"]))
    
    # Build report
    report_lines = [f"# Lint Report — {today()}", f"\nTotal issues: {issue_count}\n"]
    
    if issues["orphans"]:
        report_lines.append("## Orphan Pages (no inbound links)")
        for o in issues["orphans"]:
            report_lines.append(f"- [[{o}]]")
    
    if issues["thin"]:
        report_lines.append("\n## Thin Pages (< 200 chars)")
        for t in issues["thin"]:
            report_lines.append(f"- [[{t}]]")
    
    if issues["broken_links"]:
        report_lines.append("\n## Broken Links")
        for bl in issues["broken_links"][:20]:
            report_lines.append(f"- `{bl['from']}` → [[{bl['link']}]]")
    
    if issues["missing_pages"]:
        report_lines.append("\n## Missing Pages (mentioned but don't exist)")
        for mp in issues["missing_pages"][:20]:
            report_lines.append(f"- [[{mp}]]")
    
    if issues["no_links_section"]:
        report_lines.append("\n## Pages Missing ## Links Section")
        for nl in issues["no_links_section"][:20]:
            report_lines.append(f"- [[{nl}]]")
    
    if issue_count == 0:
        report_lines.append("\n✅ Wiki is healthy! No issues found.")
    
    report_md = "\n".join(report_lines)
    
    # Write report
    report_path = f"wiki/meta/lint-{today()}.md"
    write_file(vault_path(vault_id) / report_path, report_md)
    
    # Update index + log
    update_index_entry(vault_id, "Meta", report_path, f"Lint report: {issue_count} issues")
    append_log(vault_id, "lint", f"{issue_count} issues",
               f"- Report: `{report_path}`\n- Orphans: {len(issues['orphans'])}\n- Thin: {len(issues['thin'])}\n- Broken: {len(issues['broken_links'])}")
    git_stage(vault_id, [report_path, "index.md", "log.md"])
    
    return {
        "status": "ok",
        "report_path": report_path,
        "issue_count": issue_count,
        "issues": {k: v if not isinstance(v, set) else list(v) for k, v in issues.items()},
        "preview": report_md[:500],
    }


# ── Thread ↔ Wiki Integration ─────────────────────────────────────────────────

def log_message_to_wiki(vault_id: str, thread_id: str, who: str, what: str):
    """Append a message to a per-thread log page in wiki/meta/thread-{id}.md."""
    page_rel = f"wiki/meta/thread-{thread_id}.md"
    p = vault_path(vault_id) / page_rel
    
    if not p.exists():
        header = f"# Thread {thread_id} — Message Log\n\n"
        write_file(p, header)
    
    # Truncate message to keep file manageable
    msg_short = what[:500]
    timestamp = now_iso()
    entry = f"\n**[{timestamp}] {who}**: {msg_short}\n"
    append_file(p, entry)
    
    # Don't stage every message — too noisy. Staging done at commit time.


def get_wiki_context(db, vault_id: str, topic: str) -> str:
    """
    Read index + search wiki for topic-relevant pages.
    Returns a compact context string for LLM injection.
    Optimised: max 3 pages, each truncated to 800 chars.
    """
    if not vault_path(vault_id).exists():
        return ""
    
    # 1. Quick keyword search
    words = [w for w in topic.lower().split() if len(w) > 3][:4]
    if not words:
        return ""
    
    hits = search_wiki(vault_id, words)[:3]
    if not hits:
        return ""
    
    parts = []
    for h in hits:
        page = vault_path(vault_id) / h["path"]
        content = read_file(page)[:800]
        parts.append(f"[{h['path']}]: {content}")
    
    return "\n---\n".join(parts)


# ── Raw/Inbox helpers ──────────────────────────────────────────────────────────

def list_inbox(vault_id: str) -> list[dict]:
    """List files in raw/inbox waiting for ingest."""
    inbox = raw_path(vault_id) / "inbox"
    if not inbox.exists():
        return []
    return [
        {"name": f.name, "size": f.stat().st_size}
        for f in inbox.iterdir()
        if f.is_file()
    ]

def list_library(vault_id: str) -> list[dict]:
    """List files that have been ingested (raw/library)."""
    lib = raw_path(vault_id) / "library"
    if not lib.exists():
        return []
    return [
        {"name": f.name, "size": f.stat().st_size}
        for f in lib.iterdir()
        if f.is_file()
    ]

# ── Automated Integration ──────────────────────────────────────────────────────

SYS_FORMAT_GLUE = """You are a keyword extractor for an Obsidian-style wiki.
Identify key concepts, entities, and important terms in the text.
Wrap these terms in [[double brackets]]. 
Also automatically wrap all bold (**text**) and italic (*text*) terms in [[double brackets]], stripping the formatting markers inside.
Output ONLY the final formatted markdown. No preamble."""

async def apply_obsidian_formatting(db, text: str) -> str:
    """Uses LLM to wrap important keywords/bold/emphasis in [[ ]] for easy wiki search."""
    if not text.strip():
        return text
    from models import Setting
    formatted = await _llm(db, SYS_FORMAT_GLUE, f"TEXT TO FORMAT:\n{text}", max_tokens=1000)
    if "[LLM_ERR" in formatted:
        return text
    return formatted

async def update_glue_topic(db, vault_id: str, thread_id: str, topic: str, agent_name: str, content: str, add_step_cb=None):
    """
    Automated Glue update for a thread post:
    1. Slugify topic -> wiki/concepts/{slug}.md
    2. Format content with [[keywords]]
    3. Append to topic page with attribution
    """
    slug = re.sub(r"[^\w\-]", "-", topic.lower())[:40]
    page_rel = f"wiki/concepts/{slug}.md"
    p = vault_path(vault_id) / page_rel
    
    # 1. Formatting
    formatted_content = await apply_obsidian_formatting(db, content)
    
    if add_step_cb:
        status = "Wiki concepts synchronized successfully." if formatted_content.strip() != content.strip() else "Synchronized (no new keywords detected)."
        pretty_log = (
            f"### 💠 Glue Wiki Synchronization\n"
            f"---\n"
            f"**Status**: {status}\n"
            f"**Topic**: [[{topic}]]\n\n"
            f"**Original**:\n{content}\n\n"
            f"**Obsidian-Linked**:\n{formatted_content}\n"
            f"---"
        )
        add_step_cb("glue_reformat", pretty_log, {
            "report": status,
            "prompt_keywords_parsing": content,
            "parsed_prompt_keywords": formatted_content,
            "topic": topic
        })
    
    # 2. Attribution
    timestamp = today()
    agent_link = f"[[{agent_name}]]"
    thread_log_rel = f"wiki/meta/thread-{thread_id}.md"
    thread_link = f"[[{thread_log_rel}|Thread {thread_id}]]"
    
    entry = f"\n### {timestamp} | {agent_link}\n> {formatted_content}\n\n_Ref: {thread_link}_\n"
    
    # 3. Write/Update Page
    if not p.exists():
        header = f"---\ntype: concept\ntopic: {topic}\ncreated: {timestamp}\n---\n\n# {topic}\n\n## Discussion\n"
        write_file(p, header + entry)
        update_index_entry(vault_id, "Concepts", page_rel, f"Automated capture from Thread {thread_id}")
    else:
        orig = read_file(p)
        if "## Discussion" not in orig:
            if "## Links" in orig:
                orig = orig.replace("## Links", f"## Discussion\n\n## Links")
            else:
                orig += "\n## Discussion\n"
        
        orig += entry
        write_file(p, orig)
    
    git_stage(vault_id, [page_rel, "index.md"])
    # Also log message to the general thread log
    log_message_to_wiki(vault_id, thread_id, agent_name, content)

