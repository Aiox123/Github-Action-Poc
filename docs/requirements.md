# 需求沟通记录 — Iteration 2

> 文档版本：v1（初稿，随阶段推进追加"决策记录"与"产出记录"）
> 涉及仓库：`Aiox123/Github-Action-Poc`
> 关联分支：`main`

---

## 1. 总体目标

把 PoC 仓库内的 Python 项目 `todo-cli` 从"小玩具"升级为"较系统化"的工程示范，并打通
"需求工单 → 代码 → Copilot CI 评审"的完整闭环：

1. 重构 Python 项目，引入分层架构、REST API、工具链与完整测试；
2. 在仓库内引入"类 Jira 工单"机制，描述追加到项目的新需求；
3. 扩展 GitHub Actions 工作流：让 Copilot CLI 同时读取项目代码 + 工单，输出
   工单与代码不一致 / 工单不足之处 的评审报告。

---

## 2. 范围与非范围

### 2.1 In Scope
- `todo-cli/` 的目录与代码重构（领域 / 服务 / 仓储 / 接口分层）。
- 新增 REST API（FastAPI）与原有 CLI 共存。
- 测试：单元 + 集成，覆盖率目标 ≥ 80%。
- 工具链：`pyproject.toml`、`ruff`（lint）、`mypy`（类型检查可选）。
- 仓库内创建 `tickets/` 目录与 `TODO-002` 工单（Markdown 格式）。
- 在 `.github/workflows/todo-cli-ci.yml` 追加"工单 vs 代码"评审步骤。

### 2.2 Out of Scope
- 真正接入 Jira / 任何外部工单系统。
- 数据库（SQLite 仅"留口子"，本次仍用 JSON 文件存储）。
- 用户鉴权、多租户。
- 发布到 PyPI / Docker 镜像构建。

---

## 3. 各阶段需求详情与决策

### 阶段 ① — Python 项目复杂化、系统化
**目标**：从两个文件 (`storage.py` + `cli.py`) 升级为分层架构。

**决策（推荐方案被采纳）**：
- 包结构：
  ```
  todo-cli/
  ├── pyproject.toml
  ├── README.md
  ├── main.py                      # 兼容入口（调用 CLI）
  ├── todo/
  │   ├── __init__.py
  │   ├── config.py                # 应用配置（数据文件路径等）
  │   ├── models.py                # 领域模型（dataclass）
  │   ├── repositories/
  │   │   ├── __init__.py
  │   │   ├── base.py              # TodoRepository ABC
  │   │   └── json_repo.py         # JSON 文件实现
  │   ├── services.py              # 业务逻辑（TodoService）
  │   ├── cli.py                   # argparse CLI（重构为调用 service）
  │   └── api.py                   # FastAPI HTTP 接口
  └── tests/
      ├── unit/
      │   ├── test_models.py
      │   ├── test_json_repo.py
      │   └── test_services.py
      └── integration/
          ├── test_cli.py
          └── test_api.py
  ```
- 依赖管理：`pyproject.toml`（runtime + dev extras）。
- Lint：`ruff`。
- 类型检查：保留 `mypy` 配置项但 CI 暂不强制 fail（可后续打开）。

### 阶段 ② — 完善后推送到仓库
- 本地通过 `pytest`、`ruff check .` 后，单次 commit 推送到 `main`。
- 触发现有 `Todo CLI - Test & Copilot Review` 工作流验证。

### 阶段 ③ — 创建类 Jira 工单
**决策（推荐方案被采纳）**：
- 目录：`tickets/`。
- 命名：`<PREFIX>-<编号>-<slug>.md`，本次为 `TODO-002-add-due-date-and-priority.md`。
- 模板包含字段：
  - `ID`, `Title`, `Status`, `Priority`, `Assignee`, `Reporter`, `Created`
  - `Background` 背景
  - `Acceptance Criteria` 验收标准
  - `Technical Notes` 技术说明
  - `Affected Files` 涉及文件
  - `Out of Scope` 不在范围内
- **本工单刻意保留瑕疵**，用于验证 Copilot CLI 评审能力（详见阶段 ⑤ 期望发现项）。

### 阶段 ④ — 工单推送到仓库
- 单次 commit 推送，避免与代码改动混在一起，方便日志追溯。

### 阶段 ⑤ — 工作流追加 Copilot 评审工单
**决策（推荐方案被采纳）**：
- 在已有 `.github/workflows/todo-cli-ci.yml` 中新增 step（不开新工作流）。
- 触发路径追加 `tickets/**`。
- 新 step 让 Copilot CLI 同时读取：
  - `todo-cli/` 下的 Python 源码与测试；
  - `tickets/` 下的工单 Markdown。
- 输出 `ticket-review.md`，包含三类发现：
  1. 工单中与现有代码 **不一致 / 已过时** 的描述；
  2. 工单中 **缺失** 的必要细节（边界、错误处理、向后兼容、配置等）；
  3. 落地风险与建议。
- 同步发布到 Job Summary，并作为 Artifact 上传。

**期望 Copilot 至少识别出（用于自检）**：
- 工单提到旧接口 `storage.list()`，实际项目已被 `services.TodoService.list()` 取代；
- "按今天到期过滤"未说明时区处理；
- "支持优先级排序"未指明排序稳定性 / 二级排序键；
- 未提到 CLI 是否要新增 `--priority`, `--due` 参数与现有 `list`/`add` 子命令的兼容；
- 未提到 REST API 是否同步暴露新字段。

---

## 4. 产出物清单（最终状态）

| 类别 | 路径 | 状态 | 备注 |
|---|---|---|---|
| 需求文档 | `docs/requirements.md` | ✅ 完成 | 本文件，随阶段追加 |
| Python 项目重构 | `todo-cli/todo/{config,models,services,cli,api}.py` + `todo-cli/todo/repositories/` | ✅ 完成 | 分层架构 + FastAPI REST API + CLI |
| 项目元数据 | `todo-cli/pyproject.toml` | ✅ 完成 | runtime + dev extras、ruff、coverage 阈值 80% |
| 测试套件 | `todo-cli/tests/{unit,integration}/` | ✅ 完成 | 29 测试，本地覆盖率 96.23% |
| 工单模板说明 | `tickets/README.md` | ✅ 完成 | 命名规范 + 标准字段 |
| TODO-002 工单 | `tickets/TODO-002-add-due-date-and-priority.md` | ✅ 完成 | 含故意瑕疵，供 Copilot 评审验证 |
| 工作流文件 | `.github/workflows/todo-cli-ci.yml` | ✅ 完成 | pytest+cov、ruff、Copilot 代码评审、Copilot 工单评审 |
| Copilot 代码评审产物 | `copilot-review` artifact / `todo-cli/copilot-review.md` | ✅ CI 产出 | 不入仓 |
| Copilot 工单评审产物 | `ticket-review` artifact / `ticket-review.md` | ✅ CI 产出 | 不入仓 |
| Git 忽略 | `.gitignore` | ✅ 完成 | 排除 env / pycache / artifacts |

### 关键 commit 历史
- `67ebfbf` — feat: add todo-cli Python project and Copilot CI workflow
- `a79c4a0` — fix(ci): specify cache-dependency-path for setup-python
- `053349c` — feat(todo-cli): refactor into layered architecture with CLI + REST API（阶段 ①②）
- `58b435f` — docs(tickets): add TODO-002 ticket for due-date and priority feature（阶段 ③④）
- `bd5a1d7` — feat(ci): add Copilot CLI ticket-vs-code review step（阶段 ⑤）

---

## 5. 验收标准

- [x] 本地 `pytest` 全绿，`ruff check .` 无错误（29 passed / coverage 96.23%）。
- [x] `main` 分支推送后 `Todo CLI - Test & Copilot Review` 工作流被触发（CI Run #3 已成功 49s）。
- [ ] Actions 运行产物含 `copilot-review`（代码评审）与 `ticket-review`（工单评审）两份 artifact。
      → 待 commit `bd5a1d7` 触发的新一轮 CI 验证。
- [ ] `ticket-review.md` 至少识别出 §3 阶段 ⑤ 期望发现项中的 **3 项及以上**。
      → 需 CI 跑完后下载 artifact 检查。
- [x] 本文档随每个阶段更新产出记录与决策追加。

---

## 6. 风险与待办

| 风险 | 影响 | 缓解 |
|---|---|---|
| Copilot CLI 评审输出质量不稳定 | 工单评审可能漏判 | 通过细化 prompt + 在工单内显式埋点提高命中率 |
| FastAPI 引入额外依赖增大 CI 时长 | CI 略变慢 | 仅加载必要依赖，使用 pip 缓存 |
| 重构改动较大易破坏现有 CI | 流水线可能短暂红 | 分阶段本地验证后再 push |
| Workflow 中 Copilot CLI 可能未生成 `ticket-review.md` | artifact 为空 | 已加 `if-no-files-found: warn` 与 Job Summary 兜底提示 |
| PAT 仍在本地 `env` 文件中存在泄露风险 | 安全 | 已在 `.gitignore` 排除；建议尽快撤销并重发 |

---

## 7. 决策记录（按时间追加）

- **2026-05-17** 完成 阶段 ①②：todo-cli 重构为分层架构 + FastAPI REST API，本地 29 测试全过（commit `053349c`）。
- **2026-05-17** 完成 阶段 ③④：创建 `tickets/README.md` 与 `TODO-002`（含故意瑕疵，commit `58b435f`）。
- **2026-05-17** 完成 阶段 ⑤：workflow 追加 `Copilot CLI - review tickets against code` step，输出 `ticket-review.md` 到 Job Summary 与 artifact（commit `bd5a1d7`）。
