问题背景
[]
https://vanna.ai/diagrams/problem-solution.svg
## 1、流程图


1）整体流程是怎么样的？

2）

## 2、数据查询
1）查询内容太多怎么处理？Dual output是什么

每次SQL查询成功后，vanna仅保留前1000个字符，并将完整的查询结果保存为文件，最后附加文件路径以便绘制时获取完整数据，比如下面是SQL `SELECT name FROM sqlite_master WHERE type='table'` 的查询结果：
```txt
name
customers
sqlite_sequence
sales
orders

Results saved to file: query_results_08ea6061.csv

**IMPORTANT: FOR VISUALIZE_DATA USE FILENAME: query_results_08ea6061.csv**
```
也会记录一些关键的信息：
```
**Content:** Chiwen平台的运行记录存储在以T_Run开头的表中：T_RunProcessRecord和T_RunRecord。这些表可能包含系统中流程和运行的执行数据。 **Timestamp:** 2025-12-03T14:21:58.273841 **ID:** `ba94467c-37f7-46e6-bd47-a78627217a1d`
```
```
**Content:** 数据库“runcontroller”包含与审计日志（AbpAuditLogs、AbpAuditLogActions）、实体变更（AbpEntityChanges、AbpEntityPropertyChanges）、Quartz调度器（QRTZ_%表）、错误处理记录（T_Error%Record）、流程执行记录（T_Run%、T_ProcessCommandRecord）以及甘特图数据（T_GanttDataRecord）相关的表。 **Timestamp:** 2025-12-03T14:21:26.290732 **ID:** `cb281337-f2fc-47d7-8bf7-8489df2e3d8d`
```
## 2、内容记录

相似性搜索：

内置一个轻量级的相似性计算方式：
Jaccard + difflib

当匹配到记录后，将记录作为工具调用结果：
```txt
Found 1 similar tool usage pattern(s):

1. run_sql (similarity: 0.83)
   Question: 帮我查找销售最好的商品
   Args: {'sql': 'SELECT product_name, SUM(quantity * price) as total_sales FROM sales GROUP BY product_name ORDER BY total_sales DESC LIMIT 10'}
```

2）查询结果的图表是如何绘制的？

## 3、身份隔离
1）是怎么限定用户权限的？

## 4、和前端的交互方面


## 和sanic-web的对比

1、sanic-web每次查找前需要进行schema的匹配，匹配的准确性直接决定了后续查询的正确性（比如没有匹配出的表中没有目标数据表，则后续的查找是直接错误的）

2、sanic-web将可视化工具封装为mcp服务进行调用，可以提供更灵活的展现方式，vanna根据数据形式决定展示方式，不一定能以最佳的效果展示

## 不足
1、vanna会记录正确执行工具调用，不管是否重复存在过，当用户反复询问同一个问题时，这些问题都会被记录，在下次遇到相同的问题时，搜索出来的内容都是相同的，缺乏多样性。降低了参考意义。
- 可以在记录前增加过滤机制，避免重复的记录。使记忆库更有参考价值

2、

```txt
You are Vanna, an AI data analyst assistant created to help users with data analysis tasks. Today's date is 2025-12-03.
Response Guidelines:
- Any summary of what you did or observations should be the final step.
- Use the available tools to help the user accomplish their goals.
- When you execute a query, that raw result is shown to the user outside of your response so YOU DO NOT need to include it in your response. Focus on summarizing and interpreting the results.

You have access to the following tools: run_sql, save_question_tool_args, search_saved_correct_tool_uses, save_text_memory, visualize_data

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

## Relevant Context from Memory

The following domain knowledge and context from prior interactions may be relevant:

• 合同管理系统：T_Contract（合同信息），T_ContractClause（合同条款），T_ContractExecution（合同履行），T_ContractRenewal（合同续约）。
• 客户关系管理（CRM）模块包括：T_Customer（客户信息），T_CustomerInteraction（客户互动记录），T_CustomerContract（客户合同），T_CustomerFeedback（客户反馈）。
• 物流配送系统表：T_Shipment（发货单），T_ShipmentTracking（配送追踪），T_DeliveryAddress（送货地址），T_LogisticsProvider（物流商）。
• 销售数据分析表包括：T_Sales（销售记录），T_SalesTarget（销售目标），T_SalesPerformance（销售业绩），T_SalesRegion（销售地区）。
• 知识库文档管理：T_Document（文档），T_DocumentCategory（文档分类），T_DocumentVersion（文档版本），T_DocumentAccess（文档访问权限）。
```