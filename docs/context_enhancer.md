# Vanna ToolContextEnricher 机制文档

## 概述

`ToolContextEnricher` 是 Vanna 框架中的一个关键扩展点，它允许在工具执行前动态地向 `ToolContext` 添加额外的上下文数据。这为开发者提供了将用户、会话或环境信息无缝注入到工具执行流程中的能力，使得每个工具都能获得更丰富、更个性化的上下文。

---

## 核心概念

### **`ToolContext`**

`ToolContext` 是传递给每个工具执行的上下文对象。它包含了工具执行所需的关键信息：
- `user`: 当前请求用户的 `User` 对象。
- `conversation_id`: 关联对话的 ID。
- `request_id`: 本次请求的唯一 ID。
- `agent_memory`: 可接访问代理的记忆系统（`AgentMemory`）。
- `observability_provider`: 用于记录指标和分布式追踪的可观察性提供者。
- `metadata`: 一个通用字典，供 `ToolContextEnricher` 等加自定义数据。

### **`ToolContextEnricher` 接口**

`ToolContextEnricher` 是一个抽象基类，定义了一个必须实现的方法：
```python
from vanna.core.enricher.base import ToolContextEnricher
from vanna.core.tool.models import ToolContext

class ToolContextEnricher(ABC):
    async def enrich_context(self, context: ToolContext) -> ToolContext:
        """Enrich the tool execution context with additional data."""
        return context
```

此方法接收一个 `ToolContext` 实例，并返回一个（通常是原地修改后的）增强版本。

---

## 工作机制

`ToolContextEnricher` 在工作流中的具体作用位置如下：

1.  **初始化**: 用户发送消息后，系统通过 `UserResolver` 解析出用户身份。
2.  **创建上下文**: 创建一个初始的 `ToolContext` 对象，其中包含从上一步得到的 `user`、`conversation_id` 等基本信.
3.  **执行增强**: Agent 环遍历其配置的所有 `context_enrichers` 列表，依次调用它们的 `enrich_context` 方法。
4.  **传递执行**: 最终生成的、已增强的 `ToolContext` bject 将传递给 `ToolRegistry.execute()` 方法，进而传递给具体的工具实现。

这一过程确保了所有工具在执行时都能访问到由所有 `enricher` 注入的数据。

---

## 示例分析

Vanna 的源码中提供了明确的示例来展示其用法。

### **`extensibility_example.py` 中的 `UserPreferencesEnricher`**

这个例子是理解 `ToolContextEnricher` 机制最直接的方式：

```python
from vanna.core.enricher.base import ToolContextEnricher


class UserPreferencesEnricher(ToolContextEnricher):
    async def enrich_context(self, context: ToolContext) -> ToolContext:
        # 1. 获取用户偏好（例如，从数据库）
        prefs = await self.db.get_user_preferences(context.user.id)

        # 2. 将偏好数据注入到 context.metadata 字典中
        context.metadata["preferences"] = prefs
        context.metadata["timezone"] = prefs.get("timezone", "UTC")

        # 3. 返回增强后的上下文
        return context
```

#### **关键步骤解释**:
1.  **数据获取**: `enrich_context` 方法可以利用传入的 `context` (特别是 `context.user`) 来获取外部数据，如数据库查询、API 用或缓存读取。
2.  **数据注入**: 议的做法是将新数据添加到 `context.metadata` 字典中。这是一个安全的、专为扩展而设的空间。
3.  **工具使用**: 在后续的工具（如 `run_sql`, `visualize_data`）中，可以通过 `context.metadata` 访问这些信息。例如，一个可视化工具可以根据用户的 `theme` 好设置图表颜色。

### **其他常见应用场景**

| 场景 | 实现方式 |
| :--- | :--- |
| **行级安全 (RLS)** | 查询数据库时，根据 `context.metadata["organization_id"]` 自动过滤数据。 |
| **个性化响应** | 根据 `context.metadata["language"]` 决定以何种语言生成报告。 |
| **会话状态管理** | 将临时状态（如购物车ID、当前任务进度）存储在 `metadata` 中，供多步骤任务共享。 |
| **审计与日志** | 将完整的用户权限列表写入 `metadata`，便于在审计日志中记录决策依据。 |

---

## 与 LlmContextEnhancer 的区别

Vanna 中还有另一个名为 `LlmContextEnhancer` 的组件，它容易与 `ToolContextEnricher` 混淆，但二者的作用域截然不同：

| 特性 | `ToolContextEnricher` | `LlmContextEnhancer` |
| :--- | :--- | :--- |
| **目标** | 强**工具执行**的上下文 (`ToolContext`) | 强**LLM请求**的上下文 (系统提示词和消息) |
| **时机** | 在 `ToolRegistry.execute()` 之前 | 在构建 LLM 请求 (`LlmRequest`) 之前 |
| **作用对象** | `ToolContext` 对象 | `system_prompt` 和 `messages` 列表 |
| **主要用途** | 为工具提供运行时数据 | 为 LLM 提供记忆、RAG 结果等附加信息 |

简而言之，`ToolContextEnricher` 关注的是“**工具能做什么**”，而 `LlmContextEnhancer` 关注的是“**LLM 知道什么**”。

---

## 总结

`ToolContextEnricher` 是 Vanna 架构中实现“关注点分离”和“依赖注入”的典范。它将通用的上下文准备逻辑从具体的工具实现中剥离出来，使得工具本身可以保持专注和简洁。同时，它为框架的定制化和集成现有业务系统（如用户管理系统、CRM）提供了强大且优雅的途径。通过合理使用 `ToolContextEnricher`，可以极大地提升 AI 代理的智能化水平和用户体验。