# Vanna 工作流程与架构详解

Vanna 是一个先进的 AI 数据分析助手框架，其设计采用了模块化和可扩展的架构。以下是根据代码库分析得出的核心工作流程和组件说明。

---


### **1. 核心架构概览**
Vanna 的核心是一个名为 `Agent`（位于 `src/vanna/core/agent/agent.py`）的中心协调者。它整合了多个解耦的组件，共同完成从接收用户查询到返回结果的全过程。

主要模块包括：
- **LLM Service (语言模型服务)**: 负责与大语言模型（如 Claude, Gemini）进行通信。
- **Tool Registry (工具注册表)**: 理所有可用的工具（如 SQL 查询、数据可视化）。
- **Conversation Store (对话存储)**: 存储和管理用户的对话历史。
- **Workflow Handler (工作流处理器)**: 处理确定性的、非 LLM 的工作流（如命令行指令）。
- **System Prompt Builder (系统提示构建器)**: 动态生成发送给 LLM 的系统提示。
- **其他增强器**: 如上下文增强器、中间件等，用于在主流程中注入额外功能。

#### **2. 主要工作过程 (Data Flow)**
当用户发起一个查询时，Vanna 遵循以下步骤：

1.  **用户身份解析 (`UserResolver`)**
    *   当 Web 请求到达时，`UserResolver` 组件（如 `JwtUserResolver`）会解析请求上下文（`RequestContext`），从中提取用户信息（如 ID、权限、所属组），并创建一个 `User` 对象。

2.  **对话加载 (`ConversationStore`)**
    *   基于用户的唯一标识和会话ID，`Agent` 从 `ConversationStore` 中加载或创建一个 `Conversation` 对象。该对象包含了该会话的所有消息历史。

3.  **工作流处理 (`WorkflowHandler`)**
    *   这是**第一个也是最快捷的执行路径**。`Agent` 会先将用户的新消息交给 `WorkflowHandler`。
    *   如果消息匹配某种模式（例如以 `/help` 开头的命令），`WorkflowHandler` 可以直接返回结果，**完全绕过 LLM 的调用**，从而提高效率并节省成本。
    *   在默认实现 `DefaultWorkflowHandler` 中，支持 `/help`, `/status`, `/memories`, `/delete [id]` 等命令。

4.  **系统提示构建 (`SystemPromptBuilder`)**
    *   如果消息需要由 LLM 处理，下一步是构建一个动态的系统提示。
    *   `DefaultSystemPromptBuilder` 会检查当前可用的工具集。如果存在 `search_saved_correct_tool_uses` 和 `save_question_tool_args` 这类“记忆”工具，它会在系统提示中自动加入一套强制的工作流指南，要求 LLM：
        *   **先搜索**: 在执行任何工具前，必须先调用 `search_saved_correct_tool_uses` 来查找过去成功的模式。
        *   **后保存**: 成功执行工具后，必须调用 `save_question_tool_args` 将本次成功经验保存下来，供未来使用。

5.  **上下文增强 (`LlmContextEnhancer`)**
    *   默认的 `DefaultLlmContextEnhancer` 会利用 `AgentMemory` 来进一步丰富上下文。
    *   它会基于用户的初始问题，在长期记忆中搜索相关的文本知识（如数据库 schema 解释、业务术语定义），并将这些信息添加到系统提示中，帮助 LLM 更好地理解背景。

6.  **LLM 通信**
    *   构建好系统提示和用户消息后，`Agent` 会通过 `LlmService` 接口向配置的 LLM 发送请求 (`LlmRequest`)。
    *   LLM 返回一个包含 `tool_calls` 或最终文本内容的 `LlmResponse`。

7.  **工具执行 (Tool Execution)**
    *   如果 LLM 的响应是调用工具（`is_tool_call()` 返回 `True`），`Agent` 会通过 `ToolRegistry` 查找并执行相应的工具。
    *   `ToolRegistry` 在执行前会进行严格的权限检查（基于用户组和工具所需的组）。
    *   执行过程中还可能应用 `LifecycleHook` 和 `LlmMiddleware` 进行日志记录、审计或错误恢复。

8.  **结果返回与迭代**
    *   工具执行的结果（`ToolResult`）会被格式化，并作为新的消息（role="tool"）重新发回给 LLM。
    *   LLM 会结合新信息生成最终的回答，或者决定是否需要调用另一个工具。
    *   这个循环（LLM -> Tool -> LLM）可能会持续多次，直到 LLM 直接输出最终的自然语言回答。

9.  **结果呈现**
    *   最终结果被封装成 `UiComponent`（如 `RichTextComponent` 用于富文本，`DataframeComponent` 用于表格），并通过 API 流式传输或一次性返回给前端。

#### **3. 关键特性：记忆系统 (Memory System)**
Vanna 的一大亮点是其内置的记忆系统，使其具备了学习能力。
*   **结构化记忆 (Tool Usage Memory)**:
    *   `save_question_tool_args`: 保存 "问题 -> 成功使用的工具及其参数" 的映射。
    *   `search_saved_correct_tool_uses`: 检索过去的成功模式。
    *   系统提示强制 LLM 遵循 "先查再做，做成就存" 的流程，避免重复犯错。
*   **文本记忆 (Text Memory)**:
    *   `save_text_memory`: 保存关于数据库、领域知识、用户偏好的纯文本信息。这为 LLM 提供了额外的上下文，而无需将其编码进提示词。
*   **管理员视图**:
    *   理员可以使用 `/memories` 命令查看所有近期记忆，并用 `/delete [id]` 删除特定记忆，便于调试和维护。

#### **4. 可扩展性设计**
Vanna 的接口设计使得扩展非常方便：
*   **生命周期钩子 (`LifecycleHook`)**: 允许在关键节点（如消息处理前后、工具执行前后）插入自定义逻辑，如日志记录、配额检查。
*   **中间件 (`LlmMiddleware`)**: 可以拦截 LLM 请求和响应，实现缓存、内容过滤等功能。
*   **上下文丰富器 (`ToolContextEnricher`)**: 可以在工具执行前，向 `ToolContext` 注入额外的数据，如用户偏好、会话状态。