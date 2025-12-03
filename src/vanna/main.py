# All imports at the top
from vanna import Agent
from vanna.core.registry import ToolRegistry
from vanna.core.user import UserResolver, User, RequestContext
from vanna.tools import RunSqlTool, VisualizeDataTool
from vanna.tools.agent_memory import SaveQuestionToolArgsTool, SearchSavedCorrectToolUsesTool, SaveTextMemoryTool
from vanna.servers.fastapi import VannaFastAPIServer
# from vanna.integrations.anthropic import AnthropicLlmService
from vanna.integrations.openai import OpenAILlmService
from vanna.integrations.sqlite import SqliteRunner
from vanna.integrations.mysql import MySQLRunner
from vanna.integrations.local.agent_memory import DemoAgentMemory
from vanna.integrations.faiss import FAISSAgentMemory
import asyncio  
from vanna.core.tool import ToolContext

# Configure your LLM
llm = OpenAILlmService(
    model="qwen-plus",
    api_key="sk-f21c88c445d246faa1399f2ccd9a0631",  # Or use os.getenv("ANTHROPIC_API_KEY")
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# Configure your database
db_tool = RunSqlTool(
    sql_runner=SqliteRunner(database_path="./your_database.db")
)

mysql_tool = RunSqlTool(
    sql_runner=MySQLRunner(
        host="118.178.84.138",
        database="runcontroller",
        user="root",
        password="secureRootPassword123",
        port=33306
    ),
)
#   MYSQL_HOST: "118.178.84.138"
#   MYSQL_PORT: "33306"
#   MYSQL_USER: "root"
#   MYSQL_DATABASE: "runcontroller"

# Configure your agent memory
# agent_memory = DemoAgentMemory(max_items=1000)
# 本地文件存储  
agent_memory = FAISSAgentMemory(  
    persist_path="./faiss_index",  
    dimension=384,  
    metric="cosine"  
)
# Configure user authentication
class SimpleUserResolver(UserResolver):
    async def resolve_user(self, request_context: RequestContext) -> User:
        user_email = request_context.get_cookie('vanna_email') or 'guest@example.com'
        group = 'admin' if user_email == 'admin@example.com' else 'user'
        return User(id=user_email, email=user_email, group_memberships=[group])

user_resolver = SimpleUserResolver()

# Create your agent
tools = ToolRegistry()
# tools.register_local_tool(db_tool, access_groups=['admin', 'user'])
tools.register_local_tool(mysql_tool, access_groups=['admin', 'user'])
tools.register_local_tool(SaveQuestionToolArgsTool(), access_groups=['admin'])
tools.register_local_tool(SearchSavedCorrectToolUsesTool(), access_groups=['admin', 'user'])
tools.register_local_tool(SaveTextMemoryTool(), access_groups=['admin', 'user'])
tools.register_local_tool(VisualizeDataTool(), access_groups=['admin', 'user'])

from vanna import Agent, AgentConfig  
  
# 创建自定义配置  
config = AgentConfig(  
    max_tool_iterations=20,  # 设置最大工具迭代次数  
    stream_responses=True,  
    temperature=0.01
)  


async def populate_memory_directly():  
    context = ToolContext(  
        user=User(id="system", email="system@example.com", group_memberships=["admin"]),  
        conversation_id="initialization",  
        request_id="init-001",  
        agent_memory=agent_memory  
    )  
      
    # 直接保存工具使用模式  
    await agent_memory.save_tool_usage(  
        question="帮我查找销售最好的商品",  
        tool_name="mysql_tool",  
        args={"sql": "SELECT product_name, SUM(quantity * price) as total_sales FROM sales GROUP BY product_name ORDER BY total_sales DESC LIMIT 10"},  
        context=context,  
        success=True  
    )  
      
    # 直接保存文本内存  
    await agent_memory.save_text_memory(  
        content="Chiwen平台的运行记录存储在以T_Run开头的表中：T_RunProcessRecord和T_RunRecord。这些表可能包含系统中流程和运行的执行数据。",  
        context=context  
    )  
      
    # 保存文本内存 - 1  
    await agent_memory.save_text_memory(  
        content="用户信息表 T_User 包含用户ID、用户名、邮箱、创建时间等基本信息。联系方式存储在 T_UserContact 表中，包括电话号码、地址、QQ等多种联系方式。",  
        context=context  
    )  
      
    # 保存文本内存 - 2  
    await agent_memory.save_text_memory(  
        content="订单管理系统中，T_Order 表存储订单基本信息，T_OrderDetail 表存储订单行项目，T_OrderStatus 表记录订单状态变更历史。",  
        context=context  
    )  
      
    # 保存文本内存 - 3  
    await agent_memory.save_text_memory(  
        content="库存系统包括 T_Inventory 表（当前库存），T_InventoryLog 表（库存变动日志），T_InventoryAdjustment 表（库存调整记录）。",  
        context=context  
    )  
      
    # 保存文本内存 - 4  
    await agent_memory.save_text_memory(  
        content="财务模块的主要表有：T_Invoice（发票表），T_Payment（付款表），T_Expense（费用表），T_Budget（预算表）。",  
        context=context  
    )  
      
    # 保存文本内存 - 5  
    await agent_memory.save_text_memory(  
        content="员工管理系统中，T_Employee 表存储员工基本信息，T_Department 表存储部门信息，T_EmployeeDepartment 存储员工与部门的关系。",  
        context=context  
    )  
      
    # 保存文本内存 - 6  
    await agent_memory.save_text_memory(  
        content="产品信息由多个表管理：T_Product（产品基本信息），T_ProductCategory（产品分类），T_ProductAttribute（产品属性），T_ProductImage（产品图片）。",  
        context=context  
    )  
      
    # 保存文本内存 - 7  
    await agent_memory.save_text_memory(  
        content="销售数据分析表包括：T_Sales（销售记录），T_SalesTarget（销售目标），T_SalesPerformance（销售业绩），T_SalesRegion（销售地区）。",  
        context=context  
    )  
      
    # 保存文本内存 - 8  
    await agent_memory.save_text_memory(  
        content="项目管理系统的核心表：T_Project（项目信息），T_ProjectTask（项目任务），T_ProjectTeam（项目团队成员），T_ProjectSchedule（项目进度）。",  
        context=context  
    )  
      
    # 保存文本内存 - 9  
    await agent_memory.save_text_memory(  
        content="客户关系管理（CRM）模块包括：T_Customer（客户信息），T_CustomerInteraction（客户互动记录），T_CustomerContract（客户合同），T_CustomerFeedback（客户反馈）。",  
        context=context  
    )  
      
    # 保存文本内存 - 10  
    await agent_memory.save_text_memory(  
        content="供应链管理表：T_Supplier（供应商信息），T_PurchaseOrder（采购订单），T_ReceivingRecord（收货记录），T_SupplierPerformance（供应商绩效）。",  
        context=context  
    )  
      
    # 保存文本内存 - 11  
    await agent_memory.save_text_memory(  
        content="生产制造模块包含：T_Production（生产单），T_ProductionLine（生产线），T_QualityInspection（质量检验），T_DefectLog（缺陷日志）。",  
        context=context  
    )  
      
    # 保存文本内存 - 12  
    await agent_memory.save_text_memory(  
        content="人力资源系统中的考勤记录：T_Attendance（考勤记录），T_Leave（请假记录），T_Overtime（加班记录），T_Salary（工资记录）。",  
        context=context  
    )  
      
    # 保存文本内存 - 13  
    await agent_memory.save_text_memory(  
        content="市场营销数据表：T_Campaign（营销活动），T_Lead（潜在客户），T_Promotion（促销活动），T_Advertisement（广告投放）。",  
        context=context  
    )  
      
    # 保存文本内存 - 14  
    await agent_memory.save_text_memory(  
        content="物流配送系统表：T_Shipment（发货单），T_ShipmentTracking（配送追踪），T_DeliveryAddress（送货地址），T_LogisticsProvider（物流商）。",  
        context=context  
    )  
      
    # 保存文本内存 - 15  
    await agent_memory.save_text_memory(  
        content="质量管理体系：T_QualityStandard（质量标准），T_QualityCertification（质量认证），T_QualityAudit（质量审计），T_NonConformance（不符合报告）。",  
        context=context  
    )  
      
    # 保存文本内存 - 16  
    await agent_memory.save_text_memory(  
        content="资产管理模块：T_Asset（资产信息），T_AssetMaintenance（资产维护），T_AssetDepreciation（资产折旧），T_AssetTransfer（资产转移）。",  
        context=context  
    )  
      
    # 保存文本内存 - 17  
    await agent_memory.save_text_memory(  
        content="合同管理系统：T_Contract（合同信息），T_ContractClause（合同条款），T_ContractExecution（合同履行），T_ContractRenewal（合同续约）。",  
        context=context  
    )  
      
    # 保存文本内存 - 18  
    await agent_memory.save_text_memory(  
        content="知识库文档管理：T_Document（文档），T_DocumentCategory（文档分类），T_DocumentVersion（文档版本），T_DocumentAccess（文档访问权限）。",  
        context=context  
    )  
      
    # 保存文本内存 - 19  
    await agent_memory.save_text_memory(  
        content="系统日志和审计：T_SystemLog（系统日志），T_AuditLog（审计日志），T_UserActivity（用户活动），T_ErrorLog（错误日志）。",  
        context=context  
    )  
      
    # 保存文本内存 - 20  
    await agent_memory.save_text_memory(  
        content="报表和仪表板数据：T_Report（报表定义），T_ReportData（报表数据），T_Dashboard（仪表板），T_DashboardWidget（仪表板小部件）。",  
        context=context  
    )  
  
asyncio.run(populate_memory_directly())

# 使用配置创建 Agent  
agent = Agent(  
    llm_service=llm,  
    tool_registry=tools,  
    user_resolver=user_resolver,  
    agent_memory=agent_memory,  
    config=config  # 传入自定义配置  
)

# Run the server
server = VannaFastAPIServer(agent)
server.run(host="0.0.0.0", port=2714)