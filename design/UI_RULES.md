# UI_RULES.md
AI交易平台 Web UI 规范（TailwindCSS 设计系统）

---

# 0 在写任何页面时可参照 design/ 的设计文件
包括code.html、screen.png

# 1 设计原则

交易系统 UI 设计优先级

```
信息密度 > 响应速度 > 可读性 > 美观
```

设计目标

```
专业交易终端
高密度数据展示
低视觉噪音
毫秒级识别涨跌
```

界面类型

```
Desktop Trading Terminal
高密度表格
多窗口布局
实时行情
```

---

# 2 Tailwind 全局主题变量

TW config

```js
tailwind.config = {
  theme: {
    extend: {

      colors: {

        primary: '#0066FF',

        up: '#FF0000',
        down: '#00B050',

        border: '#E5E7EB',

        bgMain: '#F9FAFB',

        card: '#FFFFFF',

        textMain: '#1F2937',
        textSub: '#6B7280',
        textMute: '#9CA3AF'

      },

      fontSize: {

        xxs: '0.7rem',

      }

    }
  }
}
```

---

# 3 颜色语义系统

交易平台颜色必须严格语义化。

### 主色

```
primary
#0066FF
```

用途

```
主按钮
选中状态
品牌色
高亮标签
```

示例

```
bg-primary
text-primary
border-primary
```

---

### 上涨

```
up
#FF0000
```

用途

```
股票上涨
盈利
涨幅
正收益
```

示例

```
text-up
bg-up
```

---

### 下跌

```
down
#00B050
```

用途

```
股票下跌
亏损
跌幅
负收益
```

示例

```
text-down
bg-down
```

---

### 边框

```
border
#E5E7EB
```

用途

```
卡片边框
表格分割
UI边界
```

---

### 主背景

```
bgMain
#F9FAFB
```

用途

```
主页面背景
交易面板背景
```

---

### 卡片背景

```
card
#FFFFFF
```

用途

```
面板
模块
浮窗
```

---

### 文字颜色

主文字

```
textMain
#1F2937
```

副文字

```
textSub
#6B7280
```

辅助

```
textMute
#9CA3AF
```

---

# 4 字体系统

交易系统使用双字体系统

### UI字体

```
PingFang SC
Microsoft YaHei
sans-serif
```

示例

```
font-sans
```

---

### 数字字体

```
Helvetica Neue
Arial
sans-serif
```

class

```
font-numeric
```

用途

```
价格
涨跌幅
资产
数量
订单
收益率
```

---

# 5 字号系统

| 名称 | 大小 | 用途 |
|---|---|---|
| text-xxs | 0.7rem | 行情辅助 |
| text-xs | 0.75rem | 表格 |
| text-sm | 0.875rem | 普通文字 |
| text-base | 1rem | 默认 |
| text-lg | 1.125rem | 标题 |
| text-xl | 1.25rem | 大标题 |
| text-2xl | 1.5rem | 资产数字 |

---

# 6 圆角系统

交易平台圆角必须统一。

```
rounded
rounded-md
rounded-lg
rounded-xl
rounded-full
```

使用规范

```
卡片       rounded-lg
浮窗       rounded-xl
按钮       rounded
标签       rounded
头像       rounded-full
```

---

# 7 阴影系统

```
shadow-sm
shadow
shadow-md
shadow-lg
shadow-xl
shadow-2xl
```

使用规则

```
卡片 shadow-sm
浮窗 shadow-2xl
```

---

# 8 表格系统（高密度）

交易平台表格必须高密度。

class

```
density-table
```

CSS

```
.density-table th,
.density-table td {

  padding: 6px 8px;

  font-size: 12px;

  border-bottom: 1px solid #F3F4F6;

}
```

适用

```
持仓列表
策略列表
行情列表
订单列表
```

---

# 9 滚动条系统

```
custom-scrollbar
```

CSS

```
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #D1D5DB;
  border-radius: 10px;
}
```

---

# 10 图表区域规范

图表容器

```
chart-container
```

高度

```
400px
```

示例

```
<div class="chart-container">
  <canvas></canvas>
</div>
```

---

# 11 Sidebar 规范

宽度

```
w-48
```

选中状态

```
sidebar-item-active
```

CSS

```
.sidebar-item-active {

  background-color: #EFF6FF;

  color: #0066FF;

  border-right: 4px solid #0066FF;

}
```

---

# 12 卡片组件规范

标准卡片

```
bg-white
rounded-lg
shadow-sm
border border-gray-100
```

示例

```
<div class="bg-white rounded-lg shadow-sm border border-gray-100 p-4">
```

---

# 13 交易按钮规范

买入

```
bg-up
text-white
font-bold
```

卖出

```
bg-down
text-white
font-bold
```

示例

```
<button class="bg-up text-white py-2 rounded text-sm font-bold">
买入
</button>
```

---

# 14 Hover 规范

```
hover:bg-gray-50
hover:text-primary
hover:opacity-90
```

---

# 15 行情高亮

选中股票

```
bg-blue-50/30
```

hover

```
hover:bg-blue-50
```

---

# 16 信息标签

推荐标签

```
bg-primary/10
text-primary
```

示例

```
<span class="bg-primary/10 text-primary text-xs px-2 py-1 rounded">
```

---

# 17 AI组件规范

AI模块类型

```
消息面
AI荐股
回测
策略分析
```

统一卡片结构

```
Header
Content
Chart
```

---

# 18 浮动面板规范

示例

```
Backtest Panel
```

class

```
fixed
bottom-6
right-6
w-80
shadow-2xl
rounded-xl
```

---

# 19 Layout系统

整体布局

```
Header
Sidebar
Main
RightPanel
FloatingPanel
```

结构

```
Header
 └ MainLayout
      ├ Sidebar
      ├ MainContent
      └ RightPanel
```

---

# 20 AI生成UI规则

AI生成界面必须遵循

禁止

```
随机颜色
自定义style
inline css
```

必须

```
使用Tailwind class
使用UI变量
使用组件结构
```

---

# 21 Canvas图表规范

K线

```
canvas
```

指标

```
MA
MACD
KDJ
BOLL
```

辅助

```
volume
sparkline
equity curve
```

---

# 推荐AI工程结构

```
/AI_RULES/

UI_RULES.md
COMPONENT_RULES.md
PAGE_RULES.md
```

作用

```
UI_RULES        视觉系统
COMPONENT_RULES 组件结构
PAGE_RULES      页面结构
```