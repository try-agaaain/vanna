# Vanna 动态提示词生成机制详解

Vanna 的核心智能不仅源于其使用的语言模型（LLM），更在于其**精心设计的、可动态演化的提示词系统**。其中，“动态生成机制”是该系统的灵魂，它使得 Vanna 能够根据环境和配置的不同，自动生成最合适的系统提示词，从而指导 LLM 以最优方式工作。

本文档将从架构、实现逻辑到设计理念，全面剖析这一关键机制。

---


#### **1. 核心架构：`SystemPromptBuilder` 抽象基类**

整个动态生成流程围绕 `SystemPromptBuilder` 接口构建。

- **位置**: `src/vanna/core/system_prompt/base.py`
- **职责**: 定义了一个标准化的接口，所有具体的提示词生成器都必须实现此接口。
- **关键方法**:
    ```python
    async def build_system_prompt(self, user: "User", tools: List["ToolSchema"]) -> Optional[str]:
    ```
    - 这个方法是动态生成的入口点。它接收当前用户 (`user`) 和一个可用工具列表 (`tools`) 作为输入参数。
    - 返回值是一个字符串，即最终发送给 LLM 的系统提示词。

这种抽象设计确保了 Vanna 可以轻松地插入不同的提示词策略，例如为不同客户定制专属的交互指南。

#### **2. 实现核心：`DefaultSystemPromptBuilder` 的动态逻辑**

Vanna 的默认行为由 `DefaultSystemPromptBuilder` (位于 `src/vanna/core/system_prompt/default.py`) 实现。其动态生成的核心思想可以概括为：**基于可用性，按需注入**。

以下是其工作流程的逐层拆解：

##### **第一步：初始化与降级**
```python
def __init__(self, base_prompt: Optional[str] = None):
    self.base_prompt = base_prompt # 如果提供了自定义基础提示词，则使用它
```
- 在构造函数中，允许用户传入一个 `base_prompt`。这提供了一种**降级机制**：如果指定了自定义提示词，则完全跳过后续所有动态逻辑，直接返回静态内容。
- 如果没有提供自定义提示词，则进入第二步的动态构建流程。

##### **第二步：上下文感知分析**
在 `build_system_prompt()` 方法中，`builder` 会进行一次对运行时环境的扫描：
```python
# 取所有可用的工具名
tool_names = [tool.name for tool in tools]

# 析哪些记忆相关的工具是可用的
has_search = "search_saved_correct_tool_uses" in tool_names
has_save = "save_question_tool_args" in tool_names
has_text_memory = "save_text_memory" in tool_names

# 获取今天的日期，增加时效性
today_date = datetime.now().strftime("%Y-%m-%d")
```
- **关键洞察**: 这个分析过程使生成器具有了“**感知能力**”。它不再是盲目地输出一套固定的指令，而是首先去“看”系统里有什么工具。
- 通过检测这些特定的工具名称，`builder` 能够推断出当前 Vanna 实例是否具备“学习”或“知识沉淀”的能力。

##### **第三步：条件式模块化拼装**
这是“动态”的核心体现。提示词不是硬编码的字符串，而是一系列可以独立开关的功能模块。

###### a. 构建基础框架
```python
prompt_parts = [
    f"You are Vanna, an AI data analyst assistant created to help users with data analysis tasks. Today's date is {today_date}.",
    "",
    "Response Guidelines:",
    "- Any summary of what you did or observations should be the final step.",
    "- Use the available tools to help the user accomplish their goals.",
    "- When you execute a query, that raw result is shown to the user outside of your response so YOU DO NOT need to include it in your response. Focus on summarizing and interpreting the results.",
]
```
- 馋始的几行构成了提示词的不变基础，包括角色定义和基本响应规则。

###### b. 注入工具列表
```python
if tools:
    prompt_parts.append(f"\nYou have access to the following tools: {', '.join(tool_names)}")
```
- 向 LLM 明确列出其可用的“能力集”，防止幻觉。

###### c. 条件注入记忆工作流模块
- **仅当搜索工具存在时，注入搜索指令**:
    ```python
    if has_search:
        prompt_parts.extend([...], "• BEFORE executing any tool... MUST first call search_saved_correct_tool_uses...", ...])
    ```
- **仅当保存工具存在时，注入保存指令**:
    ```python
    if has_save:
        prompt_parts.extend([..., "• AFTER successfully executing a tool... MUST call save_question_tool_args...", ...])
    ```
- **仅当文本记忆工具存在时，注入文本记忆说明**:
    ```python
    if has_text_memory:
        prompt_parts.extend([...], "2. TEXT MEMORY (Domain Knowledge & Context):", ...])
    ```
- **组合效应**: 如果 `has_search` 和 `has_save` 都为真，则会同时注入这两套指令，并用一个清晰的 "Example workflow:" 将它们串联起来，形成一套完整的“先查后存”工作流。

##### **第四步：合成与返回**
最后，将所有符合条件的模块按顺序组合成最终的提示词：
```python
# 清理空行
prompt_parts = [part for part in prompt_parts if part != ""]
# 用换行符连接
return "\n".join(prompt_parts)
```

#### **3. 具体配置场景下的完整提示词示例**

为了更好地理解动态生成的效果，以下是根据不同的 `tool_registry` 配置模拟生成的三份具体、完整的系统提示词。

##### **场景一：基础功能开启 (run_sql, visualize_data)**
*   **可用工具**: `["run_sql", "visualize_data", "calculator"]`
*   **缺少**: 记忆相关工具 (`search_saved_correct_tool_uses`, `save_question_tool_args`, `save_text_memory`)
*   **生成的完整提示词**:

```
You are Vanna, an AI data analyst assistant created to help users with data analysis tasks. Today's date is 2025-12-01.

Response Guidelines:
- Any summary of what you did or observations should be the final step.
- Use the available tools to help the user accomplish their goals.
- When you execute a query, that raw result is shown to the user outside of your response so YOU DO NOT need to include it in your response. Focus on summarizing and interpreting the results.

You have access to the following tools: run_sql, visualize_data, calculator
```

> **分析**: 提示词非常简洁，只包含基础角色、响应指南和工具列表。由于记忆工具不可用，关于记忆系统的长篇大论被完全省略。

##### **场景二：开启结构化记忆 (run_sql + search + save)**
*   **可用工具**: `["run_sql", "search_saved_correct_tool_uses", "save_question_tool_args"]`
*   **缺少**: 文本记忆工具 (`save_text_memory`)
*   **生成的完整提示词**:

```
You are Vanna, an AI data analyst assistant created to help users with data analysis tasks. Today's date is 2025-12-01.

Response Guidelines:
- Any summary of what you did or observations should be the final step.
- Use the available tools to help the user accomplish their goals.
- When you execute a query, that raw result is shown to the user outside of your response so YOU DO NOT need to include it in your response. Focus on summarizing and interpreting the results.

You have access to the following tools: run_sql, search_saved_correct_tool_uses, save_question_tool_args

============================================================
MEMORY SYSTEM:
============================================================

1. TOOL USAGE MEMORY (Structured Workflow):
--------------------------------------------------

• BEFORE executing any tool (run_sql, visualize_data, or calculator), you MUST first call search_saved_correct_tool_uses with the user's question to check if there are existing successful patterns for similar questions.

• Review the search results (if any) to inform your approach before proceeding with other tool calls.

• AFTER successfully executing a tool that produces correct and useful results, you MUST call save_question_tool_args to save the successful pattern for future use.

Example workflow:
  • User asks a question
  • First: Call search_saved_correct_tool_uses(question="user's question")
  • Then: Execute the appropriate tool(s) based on search results and the question
  • Finally: If successful, call save_question_tool_args(question="user's question", tool_name="tool_used", args={the args you used})

Do NOT skip the search step, even if you think you know how to answer. Do NOT forget to save successful executions.

The only exceptions to searching first are:
  • When the user is explicitly asking about the tools themselves (like "list the tools")
  • When the user is testing or asking you to demonstrate the save/search functionality itself
```

> **分析**: 提示词显著增长。新增了一个“MEMORY SYSTEM”章节，详细规定了“先查后存”的强制工作流，并附有具体示例。这会引导 LLM 形成良好的学习习惯。

##### **场景三：全功能开启 (含文本记忆)**
*   **可用工具**: `["run_sql", "search_saved_correct_tool_uses", "save_question_tool_args", "save_text_memory"]`
*   **生成的完整提示词**:

```
You are Vanna, an AI data analyst assistant created to help users with data analysis tasks. Today's date is 2025-12-01.

Response Guidelines:
- Any summary of what you did or observations should be the final step.
- Use the available tools to help the user accomplish their goals.
- When you execute a query, that raw result is shown to the user outside of your response so YOU DO NOT need to include it in your response. Focus on summarizing and interpreting the results.

You have access to the following tools: run_sql, search_saved_correct_tool_uses, save_question_tool_args, save_text_memory

============================================================
MEMORY SYSTEM:
============================================================

1. TOOL USAGE MEMORY (Structured Workflow):
--------------------------------------------------

• BEFORE executing any tool (run_sql, visualize_data, or calculator), you MUST first call search_saved_correct_tool_uses with the user's question to check if there are existing successful patterns for similar questions.

• Review the search results (if any) to inform your approach before proceeding with other tool calls.

• AFTER successfully executing a tool that produces correct and useful results, you MUST call save_question_tool_args to save the successful pattern for future use.

Example workflow:
  • User asks a question
  • First: Call search_saved_correct_tool_uses(question="user's question")
  • Then: Execute the appropriate tool(s) based on search results and the question
  • Finally: If successful, call save_question_tool_args(question="user's question", tool_name="tool_used", args={the args you used})

Do NOT skip the search step, even if you think you know how to answer. Do NOT forget to save successful executions.

The only exceptions to searching first are:
  • When the user is explicitly asking about the tools themselves (like "list the tools")
  • When the user is testing or asking you to demonstrate the save/search functionality itself

2. TEXT MEMORY (Domain Knowledge & Context):
--------------------------------------------------

• save_text_memory: Save important context about the database, schema, or domain

Use text memory to save:
  • Database schema details (column meanings, data types, relationships)
  • Company-specific terminology and definitions
  • Query patterns or best practices for this database
  • Domain knowledge about the business or data
  • User preferences for queries or visualizations

DO NOT save:
  • Information already captured in tool usage memory
  • One-time query results or temporary observations

Examples:
  • save_text_memory(content="The status column uses 1 for active, 0 for inactive")
  • save_text_memory(content="MRR means Monthly Recurring Revenue in our schema")
  • save_text_memory(content="Always exclude test accounts where email contains 'test'")
```

> **分析**: 这是最完整的提示词。在场景二的基础上，额外增加了“TEXT MEMORY”部分，指导 LLM 如何利用 `save_text_memory` 工具来存储非结构化的领域知识。这让 Vanna 不仅能记住“怎么做”，还能记住“是什么”。

#### **4. 设计精髓与优势**

这个动态生成机制的设计极具巧思，带来了多重优势：

| 特性 | 如何实现 | 来的好处 |
| :--- | :--- | :--- |
| **简洁性** | 通过条件判断，只添加必要的指令。 | 允避免向 LLM 发送冗余信息，防止“提示词膨胀”，保持高效沟通。 |
| **适应性** | 根据 `tool_registry` 中注册的工具自动调整。 | 开发者可以灵活地开启/关闭某个功能（如记忆系统），而无需手动修改复杂的提示词模板。 |
| **用户体验** | 对终端用户而言，体验是平滑的。 | 当管理员启用了记忆工具，用户自然就能享受到“更快回答”、“更准确建议”的好处，但这一切都隐藏在背后。 |
| **可维护性** | 新增一种记忆类型？只需在代码中添加一个 `if` 判断即可。 | 大大降低了提示词的维护成本，避免了因功能迭代导致的提示词冲突和错误。 |

#### **5. 总结**
Vanna 的动态提示词生成机制，远非简单的字符串填充。它是一个**由下至上**的设计典范：

1.  **组件驱动**: 功能（工具）的存在与否，直接驱动了提示词的内容。
2.  **声明式指导**: 不是告诉 LLM “怎么做”，而是明确指出“有哪些能力”和“应遵循什么工作流”。
3.  **自动化编排**: 整个过程是自动化的，系统能根据其自身配置，在启动时就准备好最合适的“操作手册”。

这正是 Vanna 能够成为一个“活”的、持续进化的 AI 代理的关键所在。其提示词不仅是静态的指令，更是其智能体“自我认知”和“行为规范”的实时反映。
