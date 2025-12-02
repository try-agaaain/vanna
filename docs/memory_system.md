# Vanna 记忆系统文档

## 概述

Vanna 的记忆系统（`AgentMemory`）是其能够实现持续学习和自我改进的核心机制。该系统通过记录成功的“问题-工具-参数”组合以及重要的文本洞察，使得后续的查询能够更快、更准确地得到解决。


### 核心概念

1.  **`AgentMemory` 接口**: 这是一个抽象接口，定义了所有记忆存储后端必须实现的方法，如 `save_tool_usage`, `search_similar_usage`, `save_text_memory` 等。这确保了上层逻辑与底层存储技术完全解耦。
2.  **多种实现**: Vanna 提供了多种 `AgentMemory` 的具体实现，从简单的内存存储到强大的云向量数据库，满足不同环境的需求。
3.  **两种记忆类型**:
    - **工具使用记忆 (`ToolMemory`)**: 结构化存储用户的问题、使用的工具及其参数。用于加速重复性任务。
    - **文本记忆 (`TextMemory`)**: 存储自由格式的文本内容，用于记录重要观察、总结或上下文信息。
4.  **工具驱动**: 对记忆系统的操作本身也是通过专门的 `Tool` 实现的（如 `save_question_tool_args`），这意味着 LLM 可以像调用任何其他功能一样安全地读写记忆。

---

## AgentMemory 接口

`AgentMemory` 是一个异步接口，定义了所有内存操作：

```python
from vanna.capabilities.agent_memory import AgentMemory, ToolMemory, TextMemory
from vanna.core.tool import ToolContext

class AgentMemory(ABC):
    @abstractmethod
    async def save_tool_usage(
        self,
        question: str,
        tool_name: str,
        args: Dict[str, Any],
        context: ToolContext,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """保存成功的工具使用模式."""

    @abstractmethod
    async def search_similar_usage(
        self,
        question: str,
        context: ToolContext,
        *,
        limit: int = 10,
        similarity_threshold: float = 0.7,
        tool_name_filter: Optional[str] = None,
    ) -> List[ToolMemorySearchResult]:
        """根据问题搜索相似的成功工具使用模式."""

    @abstractmethod
    async def save_text_memory(self, content: str, context: ToolContext) -> TextMemory:
        """保存自由格式的文本记忆."""

    # ... 其他方法 (get_recent_memories, delete_by_id, clear_memories )
```

---

## 内存实现

Vanna 附带了一个名为 `DemoAgentMemory` 的内置内存实现。它是一个依赖最少、易于部署的解决方案，特别适用于演示和测试。

### `DemoAgentMemory`

- **位置**: `/src/vanna/integrations/local/agent_memory/in_memory.py`
- **存储**: 所有数据都存储在 Python 的 `List` 中，因此程序重启后会丢失。
- **检索**: 使用基于字符串相似度的简单算法，而不是计算密集型的向量嵌入。
  - **Jaccard 相似度**: 比较两个问题词干集合的交集与并集。
  - **Difflib Ratio**: 使用标准库的 `SequenceMatcher` 计算字符串序列的匹配比例。
  - 最终得分是这两种方法的较高者。
- **适用场景**: 开发、本地测试和演示。不适用于生产环境，因为缺乏持久性和可扩展性。

---

## 外量数据库实现

对于生产环境，Vanna 支持将记忆存储在外部向量数据库中，这些数据库能提供持久化、高性能的语义搜索能力。

### **通用架构**

所有向量数据库实现在设计上非常相似，体现了良好的模块化原则：

1.  **初始化** (`__init__`): 接收数据库连接参数（URL、API Key等）、集合名称和维度大小。
2.  **客户端管理** (`_get_client`): 惰性地创建并返回数据库客户端实例，避免每次操作都重新连接。
3.  **嵌入创建** (`_create_embedding`): 将问题或文本转换为向量。目前代码中的实现是一个占位符，使用 MD5 码生成伪随机向量。在实际应用中，这里应集成 Sentence Transformers 或 OpenAI Embeddings API 。
4.  **核心操作**:
    - `save_tool_usage`: 将 `question` 作为向量，并将结构化的工具使用数据（`tool_name`, `args`, `timestamp` ）作为元数据（metadata）存储。
    - `search_similar_usage`: 将输入的 `question` 向量化，然后在数据库中执行近邻向量搜索（ANN Search），并应用过滤器（例如只查找 `success=True` 且 `tool_name` 匹配的结果）。

### **支持的向量数据库**

Vanna 提供了对以下流行向量数据库的集成：

| 数据库 | 类名 | 特点 |
| :--- | :--- | :--- |
| **ChromaDB** | `ChromaAgentMemory` | 本地优先，易于设置，适合中小规模应用。 |
| **Milvus** | `MilvusAgentMemory` | 高性能，分布式，适合大规模生产环境。 |
| **Pinecone** | `PineconeAgentMemory` | 全全托管的云服务，开箱即用，无需运维。 |
| **Weaviate** | `WeaviateAgentMemory` | 支持混合搜索（向量 + 关键字），功能丰富。 |
| **Qdrant** | `QdrantAgentMemory` | 性能优异，内存占用低，支持本地和云部署。 |
| **OpenSearch** | `OpenSearchAgentMemory` | 在已有 OpenSearch 埽础设施上的理想选择，支持 kNN 搜索。 |
| **Marqo** | `MarqoAgentMemory` | 开箱即用的语义搜索，内置多模态模型。 |
| **FAISS** | `FAISSAgentMemory` | Meta 开源的高效相似性搜索库，纯 CPU 运行。 |

每个实现都在其文件头提供了详细的使用说明和安装指南。

---

## 记忆系统的工作流程

记忆系统主要通过以下三个工具与 LLM 交互：

### 1. `search_saved_correct_tool_uses`
- **作用**: 在开始新任务前，让 LLM 查询记忆库，寻找处理类似问题的成功先例。
- **触发**: 当 `WorkflowHandler` 测到 `search_saved_correct_tool_uses` 工具可用时，会在系统提示中自动添加一条指令，引导 LLM “先搜索，再执行”。
- **优势**: 大大程度上避免了重复发明轮子，使代理能够利用历史经验。

### 2. `save_question_tool_args`
- **作用**: 当 LLM 成功完成一个复杂的多步骤任务后，由工作流决定是否调用此工具，将本次成功的模式保存下来。
- **好处**: 本次的解决方案就成为了下一次 `search_saved_correct_tool_uses` 的结果，实现了知识的积累和传承。

### 3. `save_text_memory`
- **作用**: 用于保存关键的文本摘要、发现或上下文信息。例如，LLM 在分析数据后可以主动调用此工具：“我已分析完毕，发现销售额在夏季达到峰值”，然后将其作为一个文本记忆保存，供未来的对话参考。

### 完整循环
1.  **查询** (`search_saved...`): 新问题提出时，系统首先尝试从记忆中找到解决方案。
2.  **执行**: 如果没有找到足够的记忆，LLM 利常进行推理和工具调用。
3.  **学习** (`save_question_tool_args`): 任务成功完成后，新的解决方案被提炼并存入记忆。
4.  **复用**: 下一次遇到相同或类似问题时，第一步就能直接命中之前学到的方案。


这种“查询-执行-学习”的闭环，正是 Vanna 代理智能性的来源。

---

## 总结

Vanna 的记忆系统是一个强大而灵活的设计。它通过清晰的接口分离了“做什么”（`AgentMemory` 接口）和“如何做”（各种实现）。开发者可以根据自己的需求，从零依赖的内存存储无缝切换到企业级的向量数据库，而无需修改任何业务逻辑。这套系统是构建真正智能、能够持续学习的 AI 代理的关键基石。