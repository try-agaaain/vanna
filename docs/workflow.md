# Vanna 工作流程文档

## 概述

Vanna 是一个基于大语言模型（LLM）的智能数据分析师代理。其核心工作流程是一个精心设计的循环，它将自然语言查询与安全的工具执行相结合，并通过记忆和上下文增强来提供连贯、准确的回答。

此文档详细梳理了从用户提问到最终结果返回的完整流程。

## 核心工作流程步骤

### 1. 初始化 (Initialization)
- **组件注册**：`Agent` 实例化时，会注入多个核心组件：
  - `UserResolver`: 负责从请求上下文（如 cookies、headers）解析出认证用户。
  - `ToolRegistry`: 理和执行所有可用的工具（如 `run_sql`, `visualize_data`）。
  - `LlmService`: 处责与底层语言模型（如 Claude, GPT）通信。
  - `ConversationStore`: 存储和检索对话历史。
  - `SystemPromptBuilder`: 动态生成系统提示词。

### 2. 接收消息 (Receive Message)
- 用户端通过 `send_message` 方法发送一个用户查询。该方法接受两个关键参数：
  - `request_context`: 包含会话信息的 `RequestContext` 对象。
  - `message`: 用户输入的自然语言问题，例如 "Show me sales data for last quarter"。

### 3. 预前处理 (Pre-processing)
- **用户解析**：使用 `UserResolver` 从 `request_context` 中提取用户信息（ID、权限等）。
- **工作流处理器 (Workflow Handler)**：在任何 LLM 用了之前，先由 `WorkflowHandler` 检查消息。这是一个强大的扩展点，用于处理命令式交互：
  - 如果消息是 `/help`，则直接返回帮助文档，**跳过** 后面的所有 LLM 步骤。
  - 如果消息是 `/status`，则检查并返回当前系统的配置状态。
  - 如果消息为空或标记为 `starter_ui_request`，则返回一个启动UI界面（如欢迎卡片、按钮）。
- **生命周期钩子 (Lifecycle Hooks)**：调用 `before_message` 钩子，可用于日志记录、配额检查等。

### 4. 构建LLM请求 (Build LLM Request)
- **加载对话历史**：从 `ConversationStore` 加载与当前 `conversation_id` 关联的历史消息。
- **过滤对话**：应用 `ConversationFilter` （如基于 token 的截断）来管理上下文长度。
- **构建系统提示**：
  - 使用 `SystemPromptBuilder` 生成基础系统提示。
  - 通过 `LlmContextEnhancer` 进一步增强提示，例如动态添加数据库 schema 或用户的偏好设置。
  - **关键特性**：如果检测到 `search_saved_correct_tool_uses` 和 `save_question_tool_args` 工具，则自动生成内存工作流说明，指示 LLM 在执行任务前“先搜索”，成功后“再保存”。
- **准备最终请求**：将用户消息、对话历史、工具列表和系统提示组合成 `LlmRequest` 对象。

### 5. 执行工具循环 (Execute Tool Loop)
这是 Vanna 核心的推理过程，最多重复 `max_tool_iterations` 次。
1.  **发送给LLM**：将 `LlmRequest` 发送给 LLM 服务。
2.  **LLM 返回决策**：LLM 分析请求后，返回一个响应 (`LlmResponse`)。这通常包含：
    - **文本回复**：直接回答用户的问题。
    - **工具调用**：一个或多个要执行的工具（如 `run_sql(tool_name="run_sql", arguments={"sql": "..."}))`）。
3.  **中间件 (Middleware)**：响应经过 `LlmMiddleware` 链行转换，例如缓存响应以供将来使用。
4.  **执衎工具**：对于每个工具调用：
    - **验证权限**：`ToolRegistry` 查看用户是否有权使用该工具。
    - **执行**：调用工具的具体实现。
    - **结果处理**：工具返回一个 `ToolResult`，其中可能包含：
      - 成功/失败标志。
      - 给 LLM 的文本结果。
      - 可送前端的 UI 组件（如 `DataFrameComponent` 表格）。
5.  **更新对话**：将 LLM 的原始消息和每个工具的结果作为新消息（`role: "tool"`）添加回对话历史中。
6.  **重建请求**：将更新后的完整对话历史重新构建成一个新的 `LlmRequest`。
7.  **循環**：回到第 1 步，将新的对话历史（包含了工具执行结果）再次发送给 LLM，让它决定下一步行动。这个循环持续进行，直到 LLM 返回一个不包含工具调用的纯文本响应，或者达到最大迭代次数。

### 6. 返回结果 (Return Result)
- 将最终结果（文本和/或 UI 组件）作为一个异步生成器 (`AsyncGenerator`) 流式传输回客户端。
- **鉺理钩子 (Lifecycle Hooks)**：调用 `after_message` 钩子，用于后续处理。
- **保寉对话**：如果启用了 `auto_save_conversations`，则将更新后的对话历史保存回 `ConversationStore`。

## 关键架构特点

*   **可扩展性**：通过多种接口（Hook、Middleware、Enricher ）提供了高度的定制能力。
*   **安全性**：内置了严格的权限控制，确保用户只能访问被授权的工具和数据。
*   **可观测性**：集成了 `ObservabilityProvider` 来跟踪性能指标、创建分布式追踪和收集遥测数据。
*   **审计日志**：通过 `AuditLogger` 记录关键事件，如工具调用、访问检查和 AI 响应，用于合规性和调试。
*   **错误恢复**：通过 `ErrorRecoveryStrategy` 处理工具和 LLM 错误，支持重试、降级等功能。

---

此流程清晰地展示了 Vanna 如何利用 LLM 的推理能力，并将其与安全的工具执行、持久化的记忆系统和丰富的 UI 反馈相结合，从而构建一个强大且健壮的AI代理。
