# Vanna 提示词设计文档

## 概述

Vanna 的提示词系统是其智能行为的核心，通过精心设计的系统提示词（System Prompt）来指导大语言模型（LLM）的行为。该系统不仅提供基本的响应指南，还集成了动态的记忆工作流和上下文增强机制，使 Vanna 能够从过往成功经验中学习并持续改进。

## 系统提示词结构

Vanna 的系统提示词由 `DefaultSystemPromptBuilder` 类动态生成，包含以下几个关键部分：

### 1. 基础角色定义

```text
You are Vanna, an AI data analyst assistant created to help users with data analysis tasks. Today's date is {today_date}.
```

这部分定义了 Vanna 的核心身份和角色——一个专业的数据分析师助手，并提供了当前日期作为上下文信息。

### 2. 响应指南

- 任何总结或观察应在最后一步进行
- 使用可用工具帮助用户实现目标
- 当执行查询时，原始结果会直接显示给用户，因此您无需在响应中包含这些结果，而应专注于总结和解释结果

### 3. 工具访问权限

系统会自动列出所有可用的工具，例如：

```text
You have access to the following tools: run_sql, visualize_data, calculator, search_saved_correct_tool_uses, save_question_tool_args
```

这确保了 LLM 对其能力范围有清晰的认识。

## 记忆系统工作流

Vanna 的核心创新在于其记忆系统工作流，它通过特定的工具调用来实现知识的积累和重用。

### 1. 工具使用记忆 (Tool Usage Memory)

当 `search_saved_correct_tool_uses` 和/或 `save_question_tool_args` 工具可用时，系统会自动添加相应的指令：

#### 搜索现有模式
- 在执行任何工具（如 run_sql、visualize_data 或 calculator）之前，必须首先调用 `search_saved_correct_tool_uses` 来检查是否存在类似问题的成功模式
- 审查搜索结果以指导后续操作

#### 保存成功执行
- 在成功执行产生正确且有用结果的工具后，必须调用 `save_question_tool_args` 来保存成功的模式以供将来使用

#### 工作流示例
```
• 用户提出问题
• 首先：调用 search_saved_correct_tool_uses(question="用户的提问")
• 然后：根据搜索结果和问题执行适当的工具
• 最后：如果成功，调用 save_question_tool_args(question="用户的提问", tool_name="使用的工具", args={使用的参数})
```

**重要例外**：
- 当用户明确询问工具本身时（如 "列出工具"）
- 当用户要求测试或演示保存/搜索功能时

### 2. 文本记忆 (Text Memory)

当 `save_text_memory` 工具可用时，系统会启用文本记忆功能：

#### 适用场景
- 数据库模式细节（列含义、数据类型、关系）
- 公司特定术语和定义
- 查询模式或数据库最佳实践
- 业务或数据领域的专业知识
- 用户对查询或可视化的偏好

#### 禁止保存的内容
- 已在工具使用记忆中捕获的信息
- 一次性查询结果或临时观察

#### 使用示例
- `save_text_memory(content="状态列使用1表示活跃，0表示非活跃")`
- `save_text_memory(content="MRR在我们的模式中指月经常性收入")`
- `save_text_memory(content="始终排除电子邮件包含'test'的测试账户")`

## 上下文增强机制

Vanna 通过两个关键组件来动态增强上下文信息：LlmContextEnhancer 和 ToolContextEnricher。

### 1. LLM 上下文增强器 (LlmContextEnhancer)

`LlmContextEnhancer` 负责在 LLM 调用之前向系统提示词和用户消息添加额外的上下文。其主要功能包括：

#### 主要接口方法
- `enhance_system_prompt()`: 在首次 LLM 请求前，基于用户的初始消息向系统提示词添加相关上下文
- `enhance_user_messages()`: 在每次 LLM 请求前，可能修改或向用户消息添加上下文

#### DefaultLlmContextEnhancer 实现

该默认实现在 `/src/vanna/core/enhancer/default.py` 中定义，其工作流程如下：

1. 接收原始系统提示词、用户消息和用户对象
2. 使用 `AgentMemory` 搜索与用户消息相关的文本记忆
3. 将找到的相关记忆作为上下文片段添加到系统提示词中
4. 返回增强后的系统提示词

```python
# 示例：增强后的系统提示词会包含
## Relevant Context from Memory

The following domain knowledge and context from prior interactions may be relevant:

• The status column uses 1 for active, 0 for inactive
• MRR means Monthly Recurring Revenue in our schema
```

### 2. 工具上下文丰富器 (ToolContextEnricher)

`ToolContextEnricher` 负责在工具执行前向 `ToolContext` 添加额外数据。其主要特点：

#### 主要功能
- 向 `context.metadata` 字典添加数据
- 可以添加用户偏好、会话状态、时区、用户历史或配置等信息
- 工具可以访问这些丰富的元数据来定制其行为

#### 典型应用场景
- `UserPreferencesEnricher`: 从数据库获取用户偏好并注入上下文
- `SessionEnricher`: 注入当前会话状态
- `TemporalEnricher`: 添加时区和当前日期等时间上下文

```python
# 工具可以通过以下方式访问丰富后的上下文
async def run_sql(self, sql: str, context: ToolContext) -> ToolResult:
    # 访问用户偏好
    timezone = context.metadata.get("timezone", "UTC")
    preferences = context.metadata.get("preferences", {})
```

## 动态生成机制

`DefaultSystemPromptBuilder` 采用条件式构建策略：

1. **工具检测**：首先扫描可用工具列表，确定哪些记忆功能可用
2. **按需注入**：仅在相关工具存在时才注入对应的记忆工作流说明
3. **避免冗余**：不会为不可用的功能添加无关指令

这种设计确保了系统提示词的简洁性和相关性，避免了信息过载。

## 设计优势

- **可扩展性**：通过工具注册机制，可以轻松添加新的记忆类型
- **上下文感知**：提示词内容根据用户权限和可用工具动态调整
- **知识沉淀**：通过记忆系统实现组织知识的积累和传承
- **持续优化**：随着时间推移，Vanna 能够更快地回答常见问题
- **安全性**：严格的权限控制确保用户只能访问授权的工具和数据
- **灵活性**：通过增强器和丰富器模式，可以灵活地注入各种上下文信息而不修改核心逻辑

---

此提示词设计使 Vanna 不仅仅是一个简单的问答机器人，而是一个能够学习、适应并不断进化的企业级智能数据分析平台.