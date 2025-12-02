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

2）查询结果的图表是如何绘制的？

## 3、身份隔离
1）是怎么限定用户权限的？

## 4、和前端的交互方面
