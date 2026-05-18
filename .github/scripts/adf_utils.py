"""Common helpers shared by .github/scripts/jira_post_*.py.

Provides:
  - must_env(name): assert env var existence
  - auth_headers(email, token): Basic-auth headers for Jira REST
  - inline_to_adf(text): inline Markdown -> list of ADF text nodes
  - markdown_to_adf(md): subset Markdown -> ADF doc

Kept dependency-free (stdlib only) so any CI step can import it after
installing requests in the calling script.
"""

from __future__ import annotations

import base64
import os
import re
import sys

# --------------- env / auth ---------------


def must_env(name: str) -> str:
    """Return env var or exit with error."""
    value = os.environ.get(name, "").strip()
    if not value:
        sys.exit(f"environment variable {name} is required")
    return value


def auth_headers(email: str, token: str) -> dict[str, str]:
    """Build Jira Basic-auth headers (Content-Type=application/json)."""
    b64 = base64.b64encode(f"{email}:{token}".encode()).decode()
    return {
        "Authorization": f"Basic {b64}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


# --------------- Markdown -> ADF (subset) ---------------

LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def inline_to_adf(text: str) -> list[dict]:
    """Convert one line of inline Markdown to a list of ADF text nodes."""
    if not text:
        return []

    cursor = 0
    pattern = re.compile(
        r"(?P<code>`[^`]+`)"
        r"|(?P<bold>\*\*[^*]+\*\*)"
        r"|(?P<link>\[[^\]]+\]\([^)]+\))"
        r"|(?P<italic>(?<!\*)\*[^*]+\*(?!\*))"
    )
    nodes: list[dict] = []
    for m in pattern.finditer(text):
        start, end = m.span()
        if start > cursor:
            nodes.append({"type": "text", "text": text[cursor:start]})
        if m.group("code"):
            inner = m.group("code")[1:-1]
            nodes.append({"type": "text", "text": inner, "marks": [{"type": "code"}]})
        elif m.group("bold"):
            inner = m.group("bold")[2:-2]
            nodes.append({"type": "text", "text": inner, "marks": [{"type": "strong"}]})
        elif m.group("link"):
            lm = LINK.match(m.group("link"))
            if lm:
                nodes.append({
                    "type": "text",
                    "text": lm.group(1),
                    "marks": [{"type": "link", "attrs": {"href": lm.group(2)}}],
                })
        elif m.group("italic"):
            inner = m.group("italic")[1:-1]
            nodes.append({"type": "text", "text": inner, "marks": [{"type": "em"}]})
        cursor = end
    if cursor < len(text):
        nodes.append({"type": "text", "text": text[cursor:]})
    return nodes or [{"type": "text", "text": text}]


def markdown_to_adf(md: str) -> dict:
    """Convert a (subset of) Markdown into an ADF doc."""
    content: list[dict] = []
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        # blank line - skip
        if not line.strip():
            i += 1
            continue

        # heading
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            level = min(len(m.group(1)), 6)
            content.append({
                "type": "heading",
                "attrs": {"level": level},
                "content": inline_to_adf(m.group(2)),
            })
            i += 1
            continue

        # horizontal rule
        if re.match(r"^---+$", line.strip()):
            content.append({"type": "rule"})
            i += 1
            continue

        # fenced code block
        if line.strip().startswith("```"):
            lang = line.strip()[3:].strip()
            code_lines: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing ```
            node: dict = {
                "type": "codeBlock",
                "content": [{"type": "text", "text": "\n".join(code_lines)}],
            }
            if lang:
                node["attrs"] = {"language": lang}
            content.append(node)
            continue

        # bullet list
        if re.match(r"^\s*[-*]\s+", line):
            items: list[dict] = []
            while i < len(lines) and re.match(r"^\s*[-*]\s+", lines[i].rstrip() or ""):
                item_text = re.sub(r"^\s*[-*]\s+", "", lines[i].rstrip())
                items.append({
                    "type": "listItem",
                    "content": [{
                        "type": "paragraph",
                        "content": inline_to_adf(item_text),
                    }],
                })
                i += 1
            content.append({"type": "bulletList", "content": items})
            continue

        # ordered list
        if re.match(r"^\s*\d+\.\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\s*\d+\.\s+", lines[i].rstrip() or ""):
                item_text = re.sub(r"^\s*\d+\.\s+", "", lines[i].rstrip())
                items.append({
                    "type": "listItem",
                    "content": [{
                        "type": "paragraph",
                        "content": inline_to_adf(item_text),
                    }],
                })
                i += 1
            content.append({"type": "orderedList", "content": items})
            continue

        # paragraph (collect consecutive non-blank, non-special lines)
        para_lines = [line]
        i += 1
        while i < len(lines):
            nxt = lines[i].rstrip()
            if not nxt.strip():
                break
            if re.match(r"^(#{1,6}\s|\s*[-*]\s|\s*\d+\.\s|```|---+$)", nxt):
                break
            para_lines.append(nxt)
            i += 1
        para_text = " ".join(para_lines)
        content.append({"type": "paragraph", "content": inline_to_adf(para_text)})

    if not content:
        content = [{"type": "paragraph", "content": [{"type": "text", "text": "(empty)"}]}]
    return {"type": "doc", "version": 1, "content": content}
