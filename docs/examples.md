# Vanna 示例项目文档

## 概述

本文档详细介绍了 Vanna 代码库中的两个关键示例，展示了其在实际应用中的高级用法。

---

## 1. `transform_args_example.py`: 自定义参数转换与行级安全（RLS）


### **目的**

该示例演示了如何通过继承 `ToolRegistry` 类并重写 `transform_args` 方法，在工具执行前对参数进行动态转换。这为实现用户级别的安全性、验证和数据隔离提供了强大的机制。


### **核心概念**


`ToolRegistry.transform_args()` 是一个生命周期钩子方法。它在 LLM 生成的“工具调用”被转发给具体工具执行之前被调用。此方法允许我们：
- **修改参数**: 在不影响原始工具逻辑的情况下，根据上下文动态更改传入的参数。
- **拒绝执行**: 如果某些条件不满足（如权限不足），可以直接返回一个 `ToolRejection`，阻止工具执行，并向 LLM 返回一个友好的错误信息。


### **实现细节**


#### a) `RLSToolRegistry`

这是自定义注册表的核心类：
```python
from vanna.core import ToolRegistry
from vanna.core.tool import Tool, ToolContext, ToolRejection


class RLSToolRegistry(ToolRegistry):
    async def transform_args(
        self,
        tool: Tool,
        args,
        user: User,
        context: ToolContext,
    ) -> Union[SQLExecutionArgs, ToolRejection]:
        """Apply row-level security transformation to SQL queries."""
```

该方法接收待执行的工具 (`tool`)、其参数 (`args`) 和当前用户信息 (`user`)。它可以返回一个新的 `args` 对象或一个 `ToolRejection`。

#### b) 行级安全 (RLS) 实现

该示例展示了三种常见的应用场景：

1.  **访问控制 (拒绝)**:
    ```python
    if "restricted_table" in original_query.lower():
        return ToolRejection(reason="Access to 'restricted_table' is not permitted")
    ```
    当检测到用户查询包含“restricted_table”时，直接拒绝执行，保护敏感数据。

2.  **自动过滤 (修改)**:
    ```python
    # 获取用户的组织ID
    user_org_id = user.metadata.get("organization_id")

    # 将WHERE子句中添加 organization_id = {user_org_id} 的过滤条件
    transformed_query = ...
    return args.model_copy(update={"query": transformed_query})
    ```
    此示例会自动为查询 `users` 表的 SQL 语句追加 `WHERE organization_id = <user_org_id>`，确保每个用户只能看到自己组织的数据，实现了透明的 RLS。

3.  **输入验证 (拒绝)**:
    ```python
    if not args.database:
        return ToolRejection(reason="Database parameter is required")
    ```
    在执行前强制校验必要参数是否提供。


### **使用场景**


此模式非常适合于多租户 SaaS 应用、需要严格数据隔离的系统以及任何需要对 LLM 调用进行精细化权限控制的场景。它使得 LLM 可以在不知道底层安全规则的情况下工作，而所有安奎策略都由注册表在后台统一处理。


---

## 2. `chromadb_gpu_example.py`: ChromaDB 向量数据库与 GPU 加速

### **目的**


该示例展示了如何将 Vanna 的记忆系统与 ChromaDB 向量数据库集成，并利用 GPU 进行加速，以提升大规模记忆检索的性能和准确性。


### **核心概念**


Vanna 使用向量数据库来存储和搜索记忆。文本内容（如问题、工具调用）首先通过嵌入模型（embedding model）转换为高维向量，然后存储在向量数据库中。搜索时，新问题也被转换为向量，并在数据库中寻找最相似的向量（即最近邻搜索，ANN）。


### **实现细节**


#### a) 内置的智能设备选择

Vanna 提供了一个 `get_device()` 工具函数，它能自动检测可用的计算资源：
- 优先选择 `cuda` (NVIDIA GPU)
- 其次选择 `mps` (Apple Silicon)
- 最后退回到 `cpu`


这简化了部署，无需手动配置。

#### b) 四种使用模式

| 示例 | 描述 | 依赖 |
| :--- | :--- | :--- |
| **Example 1** | `默认嵌入`<br>使用 ChromaDB 内建的轻量级嵌入函数。| 无额外依赖。<br>适合快速测试和 CPU 件。|
| **Example 2** | `自动GPU检测`<br>使用 `create_sentence_transformer_embedding_function()` 自动生成一个支持 GPU 的嵌入器。| 要安装 `sentence-transformers`<br>(含 PyTorch)。|
| **Example 3** | `显式CUDA请求`<br>强制指定 `device="cuda"` 来使用 GPU。| 要 CUDA 支持和 `sentence-transformers`。|
| **Example 4** | `自定义大模型`<br>换用更大、更精确的模型 `all-mpnet-base-v2` 来提高搜索质量。| 要 `sentence-transformers`。|
| **Example 5** | `手功配置`<br>手动创建 `SentenceTransformerEmbeddingFunction` 并传递给 `ChromaAgentMemory`，提供了最高的灵活性。| 要 `sentence-transformers` 和 `chromadb`。|

#### c) 关键代码片段

```python
# 创建支持 GPU 的嵌入函数（自动检测设备）
embedding_fn = create_sentence_transformer_embedding_function()

# 创建内存实例，并注入嵌入函数
memory = ChromaAgentMemory(
    persist_directory="./chroma_memory_gpu",
    embedding_function=embedding_fn # 使能 GPU 加速
)
```

通过将 `embedding_function` 注入 `ChromaAgentMemory`，Vanna 即可无缝地将强大的嵌入模型与高效的向量数据库结合使用。

### **使用场景**


当你的应用有大量历史对话和复杂的记忆需求时，应使用外部向量数据库（如 ChromaDB）。如果性能是关键，或者你有可用的 GPU 资源，启用 GPU 加速可以显著缩短嵌入生成时间，从而加快整个代理的响应速度。这对于生产环境的大规模部署至关重要。


---

## 总结

这两个示例共同揭示了 Vanna 框架的强大和灵活性：
- `transform_args_example.py` 展示了框架层面的安全性和可扩展性，允许开发者在工具执行链中插入自定义逻辑。
- `chromadb_gpu_example.py` 展示了性能优化和与现代 AI 术栈（向量数据库、GPU）的深度集成能力。

它们都是构建企业级、高性能、安全的 AI 代理不可或缺的最佳实践。