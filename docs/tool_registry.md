# Vanna Tool Registry 和可用工具文档

## 概述

Vanna 的核心能力之一是其 `ToolRegistry` 机制，该机制允许 LLM 安全、可靠地与外部系统（如数据库、文件系统）进行交互。LLM 不会直接执行操作，而是生成一个“工具调用”请求，该请求随后由 `ToolRegistry` 中注册的特定工具处理。

此设计实现了以下关键优势：
- **安全性**：通过在工具中注入依赖项（如 `SqlRunner`），可以实施细粒度的权限控制和审计。例如，`run_sql` 工具只能访问它被注入的特定数据库连接。
- **可扩展性**：新功能可以通过创建新的 `Tool` 类并将其添加到注册表中轻松集成。
- **解耦**：LLM 只需了解工具名称和参数，而具体的实现细节则完全隐藏在工具类中。

本文档详细梳理了所有可向 LLM 提供的可用工具及其设计模式。

## 可用工具列表

### 1. SQL 执行

#### `run_sql`
- **作用**: 在配置的数据库上执行 SQL 查询或修改语句。
- **设计要点**:
  - 这为通用工具，接受任何符合 `SqlRunner` 接口的实现作为依赖项。
  - 对于 `SELECT` 查询，它会将结果保存为 CSV 文件，并返回数据预览给 LLM。
  - 对于 `INSERT`, `UPDATE`, `DELETE` 查询，它返回受影响的行数。
- **参数** (`RunSqlToolArgs`):
  - `sql`: 要要执行的完整 SQL 字符串。

```python
{
  "tool_name": "run_sql",
  "arguments": {
    "sql": "SELECT * FROM users WHERE age > 30"
  }
}
```

---

### 2. Python 文件操作与包管理

#### `run_python_file`
- **作用**: 执行指定的 Python 本文件。
- **依赖**: 使用 `FileSystem` 实现来确保安全的文件系统访问。
- **参数** (`RunPythonFileArgs`):
  - `filename`: 要执行的 Python 文件名（相对于工作目录）。
  - `arguments`: （可选）传递给脚本的命令行参数。
  - `timeout_seconds`: （可选）命令超时时间（秒）。

```python
{
  "tool_name": "run_python_file",
  "arguments": {
    "filename": "data_analysis.py",
    "arguments": ["--output", "report.csv"]
  }
}
```

#### `pip_install`
- **作用**: 在工作环境中使用 pip 安装 Python 包。
- **依赖**: 同样使用 `FileSystem` 来启动安装过程。
- **参数** (`PipInstallArgs`):
  - `packages`: 安装的一个或多个包的列表（可以包含版本说明符）。
  - `upgrade`: （可选）是否在安装前升级 pip。
  - `extra_args`: （可选）额外传递给 pip 命令的参数。
  - `timeout_seconds`: （可选）命令超时时间（秒）。

```python
{
  "tool_name": "pip_install",
  "arguments": {
    "packages": ["requests", "pandas>=2.0"],
    "upgrade": true
  }
}
```

---

### 3. 文件系统操作

这些工具都依赖于 `FileSystem` 抽象接口，这使得它们可以在本地、远程或沙盒化的文件系统上运行。


#### `search_files`
- **作用**: 在用户隔离的空间内搜索文件名或内容。
- **参数** (`SearchFilesArgs`):
  - `query`: 用于搜索的文本。
  - `include_content`: （可选）是否在文件内容中搜索，默认为 `True`。
  - `max_results`: （可选）返回的最大匹配数，默认为 `20`。

#### `list_files`
- **作用**: 列出指定目录中的文件列表。
- **参数** (`ListFilesArgs`):
  - `directory`: （可选）要列出文件的目录，默认为当前目录 `.`。

#### `read_file`
- **作用**: 读取并返回指定文件的内容。
- **参数** (`ReadFileArgs`):
  - `filename`: 读取的文件名。

#### `write_file`
- **作用**: 将内容写入文件，如果文件已存在且未设置 `overwrite`，则失败。
- **参数** (`WriteFileArgs`):
  - `filename`: 写入的文件名。
  - `content`: 写入的字符串内容。
  - `overwrite`: （可选）是否覆盖现有文件，默认为 `False`。

#### `edit_file`
- **作用**: 对文件进行基于行的编辑。
- **参数** (`EditFileArgs`):
  - `filename`: 编辑的文件路径。
  - `edits`: 一个 `LineEdit` 对象列表，每个对象定义一次编辑操作。

    - `start_line`: 编辑范围的起始行号（从 1开始）。
    - `end_line`: （可选）编缉范围的结束行号（包含）。如果为 `None`，默认为 `start_line`。
      设置 `end_line = start_line - 1` 可以实现插入操作。
    - `new_content`: 替换的新内容（保留原有的换行符）。

```python
{
  "tool_name": "edit_file",
  "arguments": {
    "filename": "config.py",
    "edits": [
      {
        "start_line": 5,
        "end_line": 5,
        "new_content": "MAX_RETRIES = 5\n"
      },
      {
        "start_line": 10,
        "end_line": 9, // Insert before line 10
        "new_content": "# New feature enabled\nENABLE_FEATURE_X = True\n"
      }
    ]
  }
}
```

---

### 4. 数据可视化

#### `visualize_data`
- **作用**: 从 CSV 文件中读取数据，并自动生成最合适的图表。
- **依赖**:
  - `FileSystem`: 用于读取 CSV 文件。
  - `PlotlyChartGenerator`: 根据 DataFrame 特征自动选择和生成图表（直方图、条形图、散点图、热力图等）。
- **参数** (`VisualizeDataArgs`):
  - `filename`: 可视化的 CSV 文件名。
  - `title`: （可选）图表标题。

```python
{
  "tool_name": "visualize_data",
  "arguments": {
    "filename": "sales_data_2024.csv",
    "title": "Monthly Sales Trends"
  }
}
```

---

### 5. 代理记忆 (Agent Memory)


Vanna 的 AgentMemory 系统允许代理学习和记住成功的操作模式，从而提高后续任务的效率。

#### `save_question_tool_args`
- **作用**: 将成功的“问题-工具-参数”组合保存到记忆中，以便将来重用。
- **参数** (`SaveQuestionToolArgsParams`):
  - `question`: 用户提出的原始问题。
  - `tool_name`: 成功使用的工具名称。
  - `args`: 传给工具的成功参数。

#### `search_saved_correct_tool_uses`
- **作用**: 根据当前的问题，在记忆库中搜索相似的成功工具使用模式。
- **参数** (`SearchSavedCorrectToolUsesParams`):
  - `question`: 当前需要解决的问题。
  - `limit`: （可选）返回结果的最大数量，默认为 `10`。
  - `similarity_threshold`: （可选）返回结果的最小相似度阈值（0.0-1.0），默认为 `0.7`。
  - `tool_name_filter`: （可选）按特定工具名称过滤结果。

#### `save_text_memory`
- **作用**: 保存自由格式的文本记忆，用于记录重要的见解或上下文。
- **参数** (`SaveTextMemoryParams`):
  - `content`: 保存的文本内容。


### 6. LLM 服务实现

虽然不直接作为工具提供给 LLM 叫，但这些是支持 `send_message` 流程的核心服务：
- `OpenAILlmService`: 使用 OpenAI 的 Chat Completions API (gpt-* models)。
- `AzureOpenAILlmService`: 针持 Azure OpenAI Service 的部署模型。
- `AnthropicLlmService`: 支持 Anthropic 的 Messages API (claude-* models)。
- `GeminiLlmService`: 支持 Google Gemini 的 GenerateContent API。
- `OllamaLlmService`: 支持 Ollama 的本地模型推理。

---

## 总结

Vanna 通过精心设计的 `ToolRegistry` 和依赖注入模式，构建了一个强大、安全且可扩展的 AI 代理框架。LLM 过调用命名工具与世界交互，而具体的实现细节和安全保证则由独立的工具类处理。这种架构使 Vanna 能够无缝地集威多种后端服务，同时为最终用户提供一致的用户体验。