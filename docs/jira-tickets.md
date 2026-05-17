# Jira 工单索引

> 本项目使用 [Atlassian Jira Cloud](https://hehuannie.atlassian.net) 作为工单管理系统。
> 工单详情请直接点击 Link 跳转 Jira 查看，本文件仅维护 key / 关系 / 链接。

- **看板地址**：<https://hehuannie.atlassian.net/jira/core/projects/TC/board>
- **项目 Key**：`TC`（Todo-Cli）
- **关联代码仓库**：[`Aiox123/Github-Action-Poc`](https://github.com/Aiox123/Github-Action-Poc)

---

## 工单列表

| Key | 类型 | 标题 | 关系 | 链接 |
|---|---|---|---|---|
| **TC-1** | 工作流 | todo-cli 项目主工单 | 父工单 | <https://hehuannie.atlassian.net/browse/TC-1> |
| **TC-2** | 任务 | 为 todo-cli 增加任务导出 / 导入命令（export / import） | Relates → TC-1 | <https://hehuannie.atlassian.net/browse/TC-2> |

---

## CI 评审闭环

GitHub Actions 工作流 [`Todo CLI - Test & Copilot Review`](../.github/workflows/todo-cli-ci.yml)
在 `workflow_dispatch` 触发时会：

1. 通过 Jira REST API 拉取指定工单（`jira_issue_key` 输入）
2. 让 Copilot CLI 结合 [`todo-cli/`](../todo-cli/) 项目代码评审工单
3. 把评审结果以中文评论形式写回该 Jira 工单

> 评审结果可直接在对应工单评论区查看，无需在仓库内冗余保存。
