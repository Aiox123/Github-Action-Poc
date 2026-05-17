# Tickets

本目录用 Markdown 文件模拟"类 Jira 工单"。

## 命名规范
`<PROJECT_PREFIX>-<编号>-<英文 slug>.md`

例如：`TODO-002-add-due-date-and-priority.md`

## 标准字段
每张工单建议包含：
- **ID / Title / Status / Priority / Assignee / Reporter / Created**
- **Background**：需求背景
- **Acceptance Criteria**：可验证的验收点（建议编号）
- **Technical Notes**：技术方案 / 影响面
- **Affected Files**：预计涉及的源文件
- **Out of Scope**：明确不做的事情

CI 中的 Copilot CLI 评审会读取本目录下所有工单，
对照 `todo-cli/` 真实代码寻找：
1. 工单与现有代码不一致 / 已过时的描述；
2. 工单中缺失的必要细节；
3. 落地风险与建议。

参见：`.github/workflows/todo-cli-ci.yml` 中的 **Ticket review** 步骤。
