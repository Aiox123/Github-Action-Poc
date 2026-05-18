"""Post PR information back to a Jira issue as a comment.

After Copilot CLI implements code based on a Jira ticket, this script
posts the resulting PR details (URL, changed files, branch info) back
to the original Jira issue as a comment.

Env (required):
  JIRA_EMAIL
  JIRA_API_TOKEN
  JIRA_ISSUE_KEY
  PR_URL          - the Pull Request URL
  PR_TITLE        - the Pull Request title
  CHANGED_FILES   - comma-separated list of changed files

Env (optional):
  JIRA_BASE_URL   (default https://hehuannie.atlassian.net)
  GITHUB_RUN_URL  - CI run link (footer)
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


def main() -> int:
    base_url = os.environ.get("JIRA_BASE_URL", "https://hehuannie.atlassian.net").rstrip("/")
    email = must_env("JIRA_EMAIL")
    token = must_env("JIRA_API_TOKEN")
    key = must_env("JIRA_ISSUE_KEY")
    pr_url = must_env("PR_URL")
    pr_title = os.environ.get("PR_TITLE", pr_url).strip()
    changed_files = os.environ.get("CHANGED_FILES", "").strip()
    run_url = os.environ.get("GITHUB_RUN_URL", "").strip()

    # ---------- 构建 Markdown 评论正文 ----------
    lines: list[str] = [
        f"## 🔧 Copilot CLI 自动实现（{key}）\n",
        "### PR 信息",
        f"- **链接**: [{pr_title}]({pr_url})",
        f"- **目标分支**: main ← feature/{key}\n",
    ]

    if changed_files:
        lines.append("### 变更文件")
        for f in changed_files.split(","):
            f = f.strip()
            if f:
                lines.append(f"- `{f}`")
        lines.append("")

    lines.append("---")
    lines.append("_本评论由 GitHub Actions 自动生成。_")
    if run_url:
        lines.append(f"\n[查看此次 CI 执行记录]({run_url})")

    full_md = "\n".join(lines)

    # ---------- 转换 & POST ----------
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
        print(f"[OK] PR comment posted to {key} (id={cid})")
        print(f"     {base_url}/browse/{key}?focusedCommentId={cid}")
        return 0

    print(f"[FAIL] POST comment -> {r.status_code}", file=sys.stderr)
    print(r.text[:1000], file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
