# Vanna 组件系统文档

## 概述

Vanna 实现了一个双层UI组件系统，包含**丰富组件（Rich Components）**和**简单组件（Simple Components）**，用于向用户界面呈现工具执行结果和状态更新。这个系统通过 `UiComponent` 类进行协调，允许工具返回两种不同复杂度的表示形式。

## 前端技术栈

Vanna的前端实现采用了现代化的Web技术栈，主要基于Web Components技术，具体包括：

### 1. 核心技术

- **Web Components**: 使用原生Web Components标准构建可重用的UI组件
- **Lit**: Google开发的轻量级库，用于构建快速、轻量级的Web Components
- **TypeScript**: 提供类型安全和更好的开发体验
- **Vite**: 现代化的前端构建工具，提供快速的开发服务器和优化的构建

### 2. 主要组件架构

前端组件系统由以下几个核心部分组成：

#### vanna-chat (主聊天组件)
- 负责管理整个聊天界面
- 处理与后端的通信（SSE, WebSocket）
- 协调其他组件的显示和交互
- 实现主题切换功能

#### rich-component-system.ts (丰富组件系统)
- 组件注册表（ComponentRegistry）管理所有丰富组件
- 组件渲染器为每种组件类型提供专门的渲染逻辑
- 支持多种组件类型：卡片、表格、图表、进度条等

#### 各类组件渲染器
- **CardComponentRenderer**: 渲染可折叠的卡片组件
- **DataFrameComponentRenderer**: 渲染表格数据，支持排序、搜索和导出
- **ChartComponentRenderer**: 渲染Plotly图表
- **ButtonComponentRenderer**: 渲染交互式按钮
- **NotificationComponentRenderer**: 渲染通知消息

### 3. 样式系统

- **CSS Variables**: 使用CSS自定义属性实现主题化
- **vanna-design-tokens.js**: 定义设计令牌，包括颜色、间距、字体等
- **响应式设计**: 支持不同屏幕尺寸的适配

## 数据流与组件传递机制

### 1. 组件创建与序列化

当后端工具执行时，会创建相应的UI组件并将其封装在ToolResult中：

```python
# 在run_sql.py中
async def execute(self, context: ToolContext, args: RunSqlToolArgs) -> ToolResult:
    # 执行SQL查询...
    df = await self.sql_runner.run_sql(args, context)

    # 创建DataFrameComponent显示结果
    dataframe_component = DataFrameComponent.from_records(
        records=df.to_dict("records"),
        title="Query Results",
        description=f"SQL query returned {len(df)} rows with {len(df.columns)} columns",
    )

    # 创建UiComponent包装丰富和简单组件
    ui_component = UiComponent(
        rich_component=dataframe_component,
        simple_component=SimpleTextComponent(text=result),
    )

    return ToolResult(
        success=True,
        result_for_llm=result,
        ui_component=ui_component,
        metadata=metadata,
    )
```

组件通过`serialize_for_frontend()`方法序列化为JSON格式：

```python
def serialize_for_frontend(self) -> Dict[str, Any]:
    payload = {
        "id": self.id,
        "type": self.type.value,
        "lifecycle": self.lifecycle.value,
        "timestamp": self.timestamp,
        "visible": self.visible,
        "interactive": self.interactive,
        "children": self.children,
        "data": {
            "title": getattr(self, "title", None),
            "description": getattr(self, "description", None),
            "rows": getattr(self, "rows", []),
            # ... 其他组件特定字段
        }
    }
    return payload
```

### 2. 流式传输协议

Vanna通过三种主要协议将组件数据流式传输到前端：

#### Server-Sent Events (SSE) - 主要机制

```python
@app.post("/api/vanna/v2/chat_sse")
async def chat_sse(chat_request: ChatRequest) -> StreamingResponse:
    async def generate() -> AsyncGenerator[str, None]:
        async for chunk in chat_handler.handle_stream(chat_request):
            chunk_json = chunk.model_dump_json()
            yield f"data: {chunk_json}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
```

#### WebSocket - 实时双向通信

```python
@app.websocket("/api/vanna/v2/chat_websocket")
async def chat_websocket(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        async for chunk in chat_handler.handle_stream(chat_request):
            await websocket.send_json(chunk.model_dump())
    except WebSocketDisconnect:
        pass
```

### 3. 前端接收与解析

前端通过`api-client.ts`处理流式响应：

```typescript
export class VannaApiClient {
  /**
   * Send message using Server-Sent Events (SSE) streaming
   */
  async *streamChat(request: ChatRequest): AsyncGenerator<ChatStreamChunk, void, unknown> {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
        ...this.customHeaders,
      },
      body: JSON.stringify(request),
    });

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim();
          if (data === '[DONE]') {
            return;
          }

          try {
            const chunk = JSON.parse(data) as ChatStreamChunk;
            yield chunk;
          } catch (e) {
            console.warn('Failed to parse SSE chunk:', data, e);
          }
        }
      }
    }
  }
}
```

### 4. 组件渲染流程

前端接收到数据后，通过`ComponentManager`处理组件生命周期：

```typescript
export class ComponentManager {
  private components: Map<string, RichComponent> = new Map();
  private elements: Map<string, HTMLElement> = new Map();
  private registry: ComponentRegistry = new ComponentRegistry();
  private container: HTMLElement;

  processUpdate(update: ComponentUpdate): void {
    switch (update.operation) {
      case 'create':
        this.createComponent(update);
        break;
      case 'update':
        this.updateComponent(update);
        break;
      case 'replace':
        this.replaceComponent(update);
        break;
      case 'remove':
        this.removeComponent(update);
        break;
    }
  }

  private createComponent(update: ComponentUpdate): void {
    if (!update.component) return;

    const component = this.normalizeComponent(update.component);
    const element = this.registry.render(component);
    this.components.set(component.id, component);
    this.elements.set(component.id, element);

    // 将组件添加到容器中
    this.positionComponent(element);
  }
}
```

## 具体示例：图表组件的数据传递与解析

### 1. 后端生成图表组件

在`visualize_data.py`工具中：

```python
class VisualizeDataTool(BaseTool):
    async def execute(self, context: ToolContext, args: VisualizeDataToolArgs) -> ToolResult:
        # 读取CSV文件
        csv_content = context.tool_memory.get(args.filename)
        df = pd.read_csv(io.StringIO(csv_content))

        # 生成Plotly图表配置
        chart_dict = self.plotly_generator.generate_chart(df, args.title)

        # 创建ChartComponent
        chart_component = ChartComponent(
            chart_type="plotly",
            data=chart_dict,
            title=args.title,
            config={
                "data_shape": {"rows": row_count, "columns": col_count},
                "source_file": args.filename,
            },
        )

        return ToolResult(
            success=True,
            result_for_llm=result,
            ui_component=UiComponent(
                rich_component=chart_component,
                simple_component=SimpleTextComponent(text=result),
            ),
        )
```

### 2. 图表组件序列化

`ChartComponent`继承自`RichComponent`，其数据结构被序列化为JSON：

```json
{
  "id": "comp-123",
  "type": "chart",
  "lifecycle": "create",
  "timestamp": "2025-12-01T10:30:00Z",
  "visible": true,
  "interactive": true,
  "children": [],
  "data": {
    "chart_type": "plotly",
    "data": [
      {
        "x": ["A", "B", "C"],
        "y": [1, 2, 3],
        "type": "bar"
      }
    ],
    "layout": {
      "title": "Sales by Category"
    },
    "config": {
      "data_shape": {"rows": 3, "columns": 3},
      "source_file": "sales.csv"
    }
  }
}
```

### 3. 前端图表渲染

`ChartComponentRenderer`负责渲染图表组件：

```typescript
export class ChartComponentRenderer extends BaseComponentRenderer {
  render(component: RichComponent): HTMLElement {
    const container = document.createElement('div');
    container.className = 'rich-component rich-chart';
    container.dataset.componentId = component.id;

    // 从组件数据中提取Plotly配置
    const { data: plotlyData, layout, title, config = {} } = component.data;

    // 创建plotly-chart web component
    const chartElement = document.createElement('plotly-chart') as any;

    // 设置主题
    const vannaChat = document.querySelector('vanna-chat');
    if (vannaChat) {
      chartElement.theme = vannaChat.getAttribute('theme') || 'dark';
    }

    // 包装在带有标题的容器中
    if (title) {
      container.innerHTML = `
        <div class="chart-header">
          <h3 class="chart-title">${title}</h3>
        </div>
        <div class="chart-content"></div>
      `;
      container.querySelector('.chart-content')?.appendChild(chartElement);
    } else {
      container.appendChild(chartElement);
    }

    // 在元素加入DOM后设置数据
    requestAnimationFrame(() => {
      chartElement.data = plotlyData; // Plotly traces (array)
      chartElement.layout = layout; // Plotly layout (object)
      chartElement.config = config;
    });

    return container;
  }
}
```

### 4. plotly-chart Web Component

实际的图表渲染由`plotly-chart.ts`组件完成：

```typescript
@customElement('plotly-chart')
export class PlotlyChart extends LitElement {
  @property({ type: Object }) data: any[] = [];
  @property({ type: Object }) layout: any = {};
  @property({ type: Object }) config: any = {};
  @property({ reflect: true }) theme: 'light' | 'dark' = 'light';

  render() {
    return html`<div class="plotly-container"></div>`;
  }

  updated() {
    this.renderPlotly();
  }

  private renderPlotly() {
    const plotlyContainer = this.shadowRoot?.querySelector('.plotly-container');
    if (plotlyContainer) {
      // 应用主题样式
      const themedLayout = this.applyTheme(this.layout);

      // 使用Plotly.js渲染图表
      Plotly.newPlot(plotlyContainer, this.data, themedLayout, this.config);
    }
  }

  private applyTheme(layout: any) {
    const defaultColors = this.theme === 'dark' ?
      { background: '#1a1a2e', text: '#ffffff', grid: '#2d3748' } :
      { background: '#ffffff', text: '#1a202c', grid: '#e2e8f0' };

    return {
      ...layout,
      paper_bgcolor: defaultColors.background,
      plot_bgcolor: defaultColors.background,
      font: { color: defaultColors.text },
      xaxis: { gridcolor: defaultColors.grid },
      yaxis: { gridcolor: defaultColors.grid }
    };
  }
}
```

## 总结

Vanna的前端组件系统具有以下特点：

1. **现代化技术栈**: 使用Web Components + Lit + TypeScript构建可重用、类型安全的UI组件
2. **分层架构**: 明确分离组件管理、渲染和具体实现
3. **流式通信**: 通过SSE和WebSocket实现实时、低延迟的数据传输
4. **灵活渲染**: 支持丰富组件和简单组件，适应不同设备和网络条件
5. **主题化支持**: 通过CSS变量实现深色/浅色主题切换
6. **可扩展性**: 组件注册表模式便于添加新的组件类型

这种架构设计使得Vanna能够提供丰富的交互式用户体验，同时保持系统的灵活性和可维护性。