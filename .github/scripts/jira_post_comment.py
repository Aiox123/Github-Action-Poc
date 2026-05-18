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

import json
import os
import sys
from pathlib import Path

import requests

# 公共工具从同目录 adf_utils 导入
sys.path.insert(0, str(Path(__file__).resolve().parent))
from adf_utils import auth_headers, markdown_to_adf, must_env  # noqa: E402

MAX_TEXT_LEN = 30000  # rough safety cap on comment body


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
        body_md = body_md[:MAX_TEXT_LEN] + "\n\n_...（内容过长已截断）_"

    header = f"## 🤖 Copilot CLI 工单评审（{key}）\n\n"
    footer_lines = ["\n---\n", "_本评论由 GitHub Actions 自动生成。_"]
    if run_url:
        footer_lines.append(f"\n[查看此次 CI 执行记录]({run_url})")
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
