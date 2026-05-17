"""Fetch a Jira issue and serialize it to Markdown for Copilot CLI.

Auth: $JIRA_EMAIL + $JIRA_API_TOKEN (Basic Auth).
Issue: $JIRA_ISSUE_KEY (e.g. TC-1).
Base : $JIRA_BASE_URL (default https://hehuannie.atlassian.net).

Writes ./jira-issue.md to the current working directory (repo root in CI).
"""

from __future__ import annotations

import base64
import os
import sys
from pathlib import Path

import requests


def must_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        sys.exit(f"environment variable {name} is required")
    return value


def auth_headers(email: str, token: str) -> dict[str, str]:
    b64 = base64.b64encode(f"{email}:{token}".encode()).decode()
    return {
        "Authorization": f"Basic {b64}",
        "Accept": "application/json",
    }


def adf_to_text(node: dict | list | None, indent: int = 0) -> str:
    """Render a (subset of) Atlassian Document Format to plain Markdown."""
    if node is None:
        return ""
    if isinstance(node, list):
        return "".join(adf_to_text(n, indent) for n in node)
    if not isinstance(node, dict):
        return ""

    ntype = node.get("type")
    content = node.get("content", [])

    if ntype == "doc":
        return adf_to_text(content, indent)
    if ntype == "paragraph":
        inner = adf_to_text(content, indent)
        return ("  " * indent) + inner + "\n\n"
    if ntype == "heading":
        level = node.get("attrs", {}).get("level", 2)
        inner = adf_to_text(content, indent)
        return ("#" * level) + " " + inner + "\n\n"
    if ntype == "bulletList":
        out = []
        for li in content:
            out.append(("  " * indent) + "- " + adf_to_text(li.get("content"), indent + 1).lstrip())
        return "".join(out)
    if ntype == "orderedList":
        out = []
        for i, li in enumerate(content, 1):
            out.append(("  " * indent) + f"{i}. " + adf_to_text(li.get("content"), indent + 1).lstrip())
        return "".join(out)
    if ntype == "listItem":
        return adf_to_text(content, indent)
    if ntype == "codeBlock":
        lang = node.get("attrs", {}).get("language", "")
        inner = adf_to_text(content, 0)
        return f"```{lang}\n{inner.rstrip()}\n```\n\n"
    if ntype == "blockquote":
        inner = adf_to_text(content, indent)
        return "\n".join("> " + line for line in inner.splitlines()) + "\n\n"
    if ntype == "hardBreak":
        return "\n"
    if ntype == "rule":
        return "\n---\n\n"
    if ntype == "text":
        text = node.get("text", "")
        marks = node.get("marks", [])
        for m in marks:
            mt = m.get("type")
            if mt == "strong":
                text = f"**{text}**"
            elif mt == "em":
                text = f"*{text}*"
            elif mt == "code":
                text = f"`{text}`"
            elif mt == "link":
                href = m.get("attrs", {}).get("href", "")
                text = f"[{text}]({href})"
        return text
    # Fallback: recurse into children
    return adf_to_text(content, indent)


def main() -> int:
    base_url = os.environ.get("JIRA_BASE_URL", "https://hehuannie.atlassian.net").rstrip("/")
    email = must_env("JIRA_EMAIL")
    token = must_env("JIRA_API_TOKEN")
    key = must_env("JIRA_ISSUE_KEY")

    url = f"{base_url}/rest/api/3/issue/{key}"
    params = {"fields": "summary,description,status,priority,labels,assignee,reporter,issuetype,parent,subtasks"}
    r = requests.get(url, headers=auth_headers(email, token), params=params, timeout=30)
    if not r.ok:
        print(f"[FAIL] GET {url} -> {r.status_code}", file=sys.stderr)
        print(r.text[:500], file=sys.stderr)
        return 1

    data = r.json()
    f = data.get("fields", {})

    def name_of(obj):
        return obj.get("displayName") or obj.get("name") if isinstance(obj, dict) else (obj or "")

    summary = f.get("summary", "")
    status = name_of(f.get("status")) or ""
    priority = name_of(f.get("priority")) or "-"
    issuetype = name_of(f.get("issuetype")) or ""
    assignee = name_of(f.get("assignee")) or "Unassigned"
    reporter = name_of(f.get("reporter")) or ""
    labels = ", ".join(f.get("labels") or []) or "-"
    parent_key = (f.get("parent") or {}).get("key") if isinstance(f.get("parent"), dict) else None
    subtasks = [st.get("key") for st in (f.get("subtasks") or []) if isinstance(st, dict)]

    description_adf = f.get("description")
    description_md = adf_to_text(description_adf).strip() if description_adf else "_(no description)_"

    md = [
        f"# Jira Issue {key}: {summary}",
        "",
        f"- URL: {base_url}/browse/{key}",
        f"- Issue Type: {issuetype}",
        f"- Status: {status}",
        f"- Priority: {priority}",
        f"- Assignee: {assignee}",
        f"- Reporter: {reporter}",
        f"- Labels: {labels}",
    ]
    if parent_key:
        md.append(f"- Parent: {parent_key}")
    if subtasks:
        md.append(f"- Subtasks: {', '.join(subtasks)}")
    md += ["", "## Description", "", description_md, ""]

    out = Path("jira-issue.md")
    out.write_text("\n".join(md), encoding="utf-8")
    print(f"[OK] wrote {out} ({out.stat().st_size} bytes) for {key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
