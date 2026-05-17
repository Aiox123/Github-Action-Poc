"""Post the Copilot ticket-review report back to a Jira issue as a comment.

Reads the local Markdown file (default: ticket-review.md) and converts it
into a minimal Atlassian Document Format (ADF) doc, then POSTs to
/rest/api/3/issue/{key}/comment.

Env:
  JIRA_BASE_URL  (default https://hehuannie.atlassian.net)
  JIRA_EMAIL
  JIRA_API_TOKEN
  JIRA_ISSUE_KEY
  GITHUB_RUN_URL (optional - included as a footer link)
  REVIEW_FILE    (optional, default 'ticket-review.md')
"""

from __future__ import annotations

import base64
import json
import os
import re
import sys
from pathlib import Path

import requests

MAX_TEXT_LEN = 30000  # rough safety cap on comment body


def must_env(name: str) -> str:
    v = os.environ.get(name, "").strip()
    if not v:
        sys.exit(f"environment variable {name} is required")
    return v


def auth_headers(email: str, token: str) -> dict[str, str]:
    b64 = base64.b64encode(f"{email}:{token}".encode()).decode()
    return {
        "Authorization": f"Basic {b64}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


# --------------- Markdown -> ADF (subset) ---------------

INLINE_CODE = re.compile(r"`([^`]+)`")
BOLD = re.compile(r"\*\*([^*]+)\*\*")
ITALIC = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")
LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def inline_to_adf(text: str) -> list[dict]:
    """Convert one line of inline Markdown to a list of ADF text nodes."""
    if not text:
        return []

    tokens: list[tuple[str, str, dict]] = []
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
            node = {
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
        content = [{"type": "paragraph", "content": [{"type": "text", "text": "(empty review)"}]}]
    return {"type": "doc", "version": 1, "content": content}


# --------------- main ---------------

def main() -> int:
    base_url = os.environ.get("JIRA_BASE_URL", "https://hehuannie.atlassian.net").rstrip("/")
    email = must_env("JIRA_EMAIL")
    token = must_env("JIRA_API_TOKEN")
    key = must_env("JIRA_ISSUE_KEY")
    review_file = Path(os.environ.get("REVIEW_FILE", "ticket-review.md"))
    run_url = os.environ.get("GITHUB_RUN_URL", "").strip()

    if not review_file.is_file():
        sys.exit(f"review file not found: {review_file}")

    body_md = review_file.read_text(encoding="utf-8")
    if len(body_md) > MAX_TEXT_LEN:
        body_md = body_md[:MAX_TEXT_LEN] + "\n\n_...(truncated)_"

    header = f"## 🤖 Copilot CLI Ticket Review for {key}\n\n"
    footer_lines = ["\n---\n", "_Auto-generated by GitHub Actions._"]
    if run_url:
        footer_lines.append(f"\n[View CI run]({run_url})")
    footer = "\n".join(footer_lines)

    full_md = header + body_md.strip() + "\n" + footer

    adf = markdown_to_adf(full_md)
    payload = {"body": adf}

    url = f"{base_url}/rest/api/3/issue/{key}/comment"
    r = requests.post(
        url,
        headers=auth_headers(email, token),
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        timeout=30,
    )

    if r.status_code in (200, 201):
        cid = (r.json() or {}).get("id", "?")
        print(f"[OK] comment posted to {key} (id={cid})")
        print(f"     {base_url}/browse/{key}?focusedCommentId={cid}")
        return 0

    print(f"[FAIL] POST comment -> {r.status_code}", file=sys.stderr)
    print(r.text[:1000], file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
