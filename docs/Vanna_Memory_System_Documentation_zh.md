# Vanna 内存系统文档

## 概述

Vanna 实现了一个复杂的内存系统，使AI代理能够从过去的交互中学习并持续改进。该系统基于 `AgentMemory` 接口构建，为不同的存储后端提供了统一的抽象，同时支持两种不同类型的内存：

1. **结构化内存** - 用于存储数据库模式（DDL）、SQL查询和工具使用模式等结构化数据
2. **非结构化内存** - 用于存储自由格式的文本内容和洞察

## 记忆系统工作流程示例

为了更好地理解Vanna内存系统的工作原理，我们通过一个具体的案例来说明整个过程。假设我们有一个销售数据分析系统，用户反复提出类似的问题。

## 记忆系统工作流程示例：销售数据分析场景

假设我们有一个销售数据分析系统，让我们通过一个具体案例来说明Vanna内存系统的完整工作流程。

### 第一次查询："上个月各产品的销售额是多少？"

**1. 查询阶段 (Query Phase)**
- 用户提出问题："上个月各产品的销售额是多少？"
- Vanna的`search_saved_correct_tool_uses`工具被调用，搜索记忆库中是否有类似问题
- 由于是第一次查询，没有找到匹配的记忆项

**2. 执行阶段 (Execution Phase)**
- LLM分析问题并决定需要执行SQL查询
- 调用`run_sql`工具生成并执行以下SQL：
```sql
SELECT p.product_name, SUM(s.amount) as total_sales
FROM sales s
JOIN products p ON s.product_id = p.id
WHERE s.sale_date >= date_trunc('month', current_date - interval '1 month')
  AND s.sale_date < date_trunc('month', current_date)
GROUP BY p.product_name
ORDER BY total_sales DESC;
```
- 查询成功执行，返回结果

**3. 学习阶段 (Learning Phase)**
- 系统识别到这是一个成功的查询模式，调用`save_question_tool_args`工具保存结构化记忆
- 保存的结构化记忆内容如下：
```python
{
    "memory_id": "mem-001-sql",
    "question": "上个月各产品的销售额是多少？",
    "tool_name": "run_sql",
    "args": {
        "sql": "SELECT p.product_name, SUM(s.amount) as total_sales..."
    },
    "timestamp": "2025-12-01T10:30:00Z",
    "success": true
}
```

**4. 文本洞察记忆 (Text Memory)**
- LLM在分析结果后发现一个重要洞察："电子产品类别的销售额占总销售额的65%"
- 调用`save_text_memory`工具保存这一非结构化洞察：
```python
{
    "memory_id": "mem-002-text",
    "content": "在对销售数据的分析中发现，电子产品类别的销售额占总销售额的65%，是主要收入来源。",
    "timestamp": "2025-12-01T10:35:00Z"
}
```

### 第二次查询："最近一个月最畅销的产品是什么？"

**1. 查询阶段 (Query Phase)**
- 用户提出新问题："最近一个月最畅销的产品是什么？"
- 再次调用`search_saved_correct_tool_uses`工具搜索记忆库
- 系统通过语义相似性算法（如Jaccard相似度或向量嵌入）比较问题
- 发现与之前的问题"上个月各产品的销售额是多少？"有85%的相似度
- 返回之前存储的SQL查询作为参考

**2. 执行优化阶段 (Execution Optimization)**
- LLM收到之前的查询模式作为上下文提示
- 基于之前的成功模式，快速生成优化后的SQL查询：
```sql
SELECT p.product_name, SUM(s.amount) as total_sales
FROM sales s
JOIN products p ON s.product_id = p.id
WHERE s.sale_date >= date_trunc('month', current_date - interval '1 month')
  AND s.sale_date < date_trunc('month', current_date)
GROUP BY p.product_name
ORDER BY total_sales DESC
LIMIT 1; -- 只需要最畅销的产品
```
- 执行查询并返回结果

**3. 学习强化阶段 (Learning Reinforcement)**
- 再次调用`save_question_tool_args`保存新的查询模式
- 同时更新相关文本记忆，添加新的洞察："手机产品连续三个月位居销量榜首"

### 第三次查询："为什么我们的销售额这么高？"

**1. 多重记忆检索 (Multiple Memory Retrieval)**
- 用户提出开放式问题："为什么我们的销售额这么高？"
- 系统同时执行两种记忆搜索：
  - `search_saved_correct_tool_uses`: 查找相关SQL查询模式
  - `search_text_memories`: 搜索相关的文本洞察
- 检索到多个相关记忆：
  - SQL查询模式显示电子产品是主要收入来源
  - 文本记忆指出手机产品连续三个月销量第一
  - 其他文本记忆提到"Q3推出了新的营销活动"

**2. 综合分析阶段 (Synthesis Phase)**
- LLM整合从结构化和非结构化内存中检索到的信息
- 生成全面的回答：
"根据数据分析，销售额高的主要原因有三个：
1. 电子产品类别贡献了65%的销售额，特别是手机产品连续三个月位居销量榜首；
2. Q3推出的'暑期促销'活动显著提升了转化率；
3. 新增的线上销售渠道带来了30%的新客户。"

### 数据库模式记忆示例

除了查询记忆，Vanna还存储数据库模式信息。例如：

**DDL记忆存储：**
```python
# 当首次连接到数据库时，系统会提取并存储DDL
{
    "collection": "ddl",
    "page_content": "CREATE TABLE products (\n    id INTEGER PRIMARY KEY,\n    product_name VARCHAR(100),\n    category VARCHAR(50),\n    price DECIMAL(10,2)\n);\n\nCREATE TABLE sales (\n    id INTEGER PRIMARY KEY,\n    product_id INTEGER,\n    amount DECIMAL(10,2),\n    sale_date DATE,\n    FOREIGN KEY (product_id) REFERENCES products(id)\n);"
}
```

**当用户问："有哪些产品表？"时：**
- 系统调用`get_related_ddl()`搜索与"产品"相关的DDL
- 返回`products`表的结构定义
- LLM可以基于此信息回答："我们有两个相关表：`products`表存储产品基本信息，`sales`表存储销售记录，两者通过product_id关联。"

## 结构化内存实现

Vanna中的结构化内存旨在存储和检索遵循特定模式的明确定义的数据结构。这包括：

### 1. 工具使用内存 (`ToolMemory`)

这是结构化内存的主要形式，它以结构化记录的形式存储成功的“问题-工具-参数”组合。

**数据结构 (src/vanna/capabilities/agent_memory/models.py):**
```python
class ToolMemory(BaseModel):
    memory_id: Optional[str] = None
    question: str
    tool_name: str
    args: Dict[str, Any]
    timestamp: Optional[str] = None
    success: bool = True
    metadata: Optional[Dict[str, Any]] = None
```

**关键特性：**
- 存储触发操作的原始用户问题
- 记录使用的特定工具（例如"run_sql"、"visualize_data"）
- 将传递给工具的所有参数作为字典捕获
- 包含有关执行成功和时间戳的元数据
- 基于语义相似性启用检索类似过去解决方案

### 2. 数据库模式内存（旧版实现）

在旧版实现中，Vanna使用DDL（数据定义语言）语句分别存储数据库模式信息。

**实现细节 (src/vanna/legacy/pgvector/pgvector.py):**
- 为不同类型的数据使用专用集合：
  - `sql_collection`：存储问题-SQL对
  - `ddl_collection`：存储数据库模式的DDL语句
  - `documentation_collection`：存储文档片段
- 每个集合都作为向量嵌入进行存储，用于语义搜索
- DDL语句通过`add_ddl()`方法添加
- 使用`get_related_ddl()`根据查询相似性检索相关DDL

### 3. 训练计划项

训练系统使用结构化内存按类型跟踪不同类型的训练数据：

```python
class TrainingPlanItem:
    ITEM_TYPE_SQL = "sql"
    ITEM_TYPE_DDL = "ddl"
    ITEM_TYPE_IS = "is"  # 信息模式
```

这允许Vanna按类型组织训练数据并相应地处理每个数据。

## 非结构化内存实现

Vanna中的非结构化内存旨在存储不符合预定义结构的自由格式文本内容。

### 1. 文本内存 (`TextMemory`)

这是非结构化内存的核心实现。

**数据结构 (src/vanna/capabilities/agent_memory/models.py):**
```python
class TextMemory(BaseModel):
    memory_id: Optional[str] = None
    content: str
    timestamp: Optional[str] = None
```

**关键特性：**
- 专注于存储原始文本内容的简单结构
- 没有预定义的字段或模式约束
- 足够灵活以存储任何类型的文本信息
- 通过时间戳进行时间顺序组织

### 2. 文本内存的用例

文本内存用于各种用途，包括：
- 存储分析过程中发现的重要见解
- 保存复杂发现的摘要
- 在对话中保留上下文信息
- 记录关于数据模式的观察

## 内存接口和操作

两种内存类型都通过抽象的`AgentMemory`接口访问（src/vanna/capabilities/agent_memory/base.py）：

```python
class AgentMemory(ABC):
    @abstractmethod
    async def save_tool_usage(self, ...) -> None:
        """保存结构化工具使用模式"""

    @abstractmethod
    async def save_text_memory(self, ...) -> TextMemory:
        """保存非结构化文本内存"""

    @abstractmethod
    async def search_similar_usage(self, ...) -> List[ToolMemorySearchResult]:
        """通过相似性搜索结构化内存"""

    @abstractmethod
    async def search_text_memories(self, ...) -> List[TextMemorySearchResult]:
        """通过相似性搜索非结构化文本内存"""
```

## 内存工作流程

内存系统通过持续学习循环运行：

1. **查询**：当新问题到达时，Vanna使用`search_saved_correct_tool_uses`在其内存中搜索类似的过去问题
2. **执行**：如果没有找到合适的内存，则LLM正常处理请求
3. **学习**：成功完成后，解决方案会通过以下方式保存到内存中：
   - `save_question_tool_args`用于结构化工具使用模式
   - `save_text_memory`用于非结构化见解和观察
4. **重用**：未来类似的查询可以利用新存储的知识

## 存储实现

Vanna支持两种内存类型的多种存储后端：

### 1. 内存实现
- 只在运行时持久存在的临时存储
- 使用Python列表进行数据存储
- 快速但非持久性
- 适用于开发和测试

### 2. 向量数据库实现
- 使用外部数据库的持久性存储
- 支持的后端包括ChromaDB、Milvus、Pinecone、Weaviate、Qdrant、OpenSearch
- 使用向量嵌入进行高效的语义搜索
- 适合需要可扩展性的生产环境

## 两种内存类型的关键区别

| 方面 | 结构化内存 | 非结构化内存 |
|------|-------------------|-------------------|
| **目的** | 存储可执行模式和工具使用 | 存储见解和观察 |
| **结构** | 具有特定字段的预定义模式 | 自由格式文本，结构最少 |
| **内容** | 问题-工具-参数组合、DDL | 摘要、发现、上下文笔记 |
| **检索** | 问题/模式的语义搜索 | 文本内容的语义搜索 |
| **主要用途** | 自动化重复任务 | 保存知识和上下文 |

## 与工具的集成

内存操作本身也作为工具实现，创建了一个自我强化的学习系统：

- `save_question_tool_args`：保存结构化工具使用模式
- `search_saved_correct_tool_uses`：检索类似的过去解决方案
- `save_text_memory`：存储非结构化见解

这种设计允许LLM像其他任何功能一样读写内存，从而实现自主学习和持续改进。