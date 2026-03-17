# 项目完成步骤

## Phase 1: 架构初始化，确定技术栈 ✅

### 已完成：
1. ✅ 创建项目初始化结构
   - package.json (Vue 3.4.21 + Vite 5.2.10 + TypeScript 5.4.5)
   - vite.config.ts (路径别名配置)
   - tsconfig.json (TypeScript 配置)

2. ✅ 配置 Tailwind CSS
   - tailwind.config.js (包含主题变量)
   - postcss.config.js
   - src/assets/main.css (自定义样式)

3. ✅ 创建基础目录结构
   - src/components/{common,features}
   - src/composables, src/stores, src/types, src/utils, src/views

4. ✅ 初始化路由配置
   - vue-router 4.3.2 配置
   - 基础路由页面 (HomeView, AboutView)

5. ✅ 创建主页面布局
   - App.vue (RouterView)
   - main.ts (入口文件，Pinia + Ant Design Vue)

6. ✅ 前后端分离架构
   - web-client/ 前端目录
   - backend/ 后端目录 (Python)
   - .gitignore 配置
   - 更新文档反映新结构

### 项目结构：
```
ai-trading-web/
├── web-client/          # 前端 (Vue 3 + Vite)
├── backend/             # 后端 (Python)
├── docs/                # 文档
├── design/              # 设计规范
└── ...
```

## Phase 2: 根据UI图生成每个路由空页面 ✅

### 已完成：
1. ✅ 分析设计文件，确定页面路由
   - 首页 (Home) - 智能选股中心（路由：`/`）
   - 智能荐股 (Recommendation) - AI精选股票（路由：`/recommendation`，导航栏中"智能选股"的内容页面）
   - 策略回测 (Backtest) - 策略回测管理（路由：`/backtest`）
   - 模拟交易 (Simulation) - 模拟交易账户（路由：`/simulation`）
   - 我的持仓 (Holdings) - 持仓管理（路由：`/holdings`）
   - 设置 (Settings) - 用户设置（路由：`/settings`）

2. ✅ 创建页面组件
   - HomeView.vue - 首页组件，包含资产摘要、K线图、策略管理（交易仪表板）
   - RecommendationView.vue - 智能荐股组件，包含统计数据、筛选标签、推荐列表（路由：`/recommendation`）
   - BacktestView.vue - 策略回测组件，包含策略列表、详情面板
   - SimulationView.vue - 模拟交易组件，包含账户信息、持仓、下单面板
   - HoldingsView.vue - 持仓管理组件，包含持仓列表、盈亏统计
   - SettingsView.vue - 设置组件，包含个人资料、外观、通知、交易设置

3. ✅ 更新路由配置
   - 添加所有页面路由配置
   - 设置路由元信息（标题、图标）

4. ✅ 创建主布局组件
   - MainLayout.vue - 包含头部、侧边栏导航、主内容区域
   - 侧边栏菜单：首页、智能选股、策略回测、模拟交易、我的持仓
   - 用户信息展示和设置入口

5. ✅ 验证构建成功
   - TypeScript 类型检查通过
   - Vite 构建成功
   - 所有页面组件可正常访问

### 项目结构更新：
```
web-client/src/
├── components/
│   └── layout/
│       ├── MainLayout.vue      # 主布局组件（完整导航：左侧导航 + 头部导航）
│       └── SimpleLayout.vue    # 简单布局（仅主内容，用于未来扩展）
├── views/
│   ├── HomeView.vue            # 首页（使用 MainLayout）
│   ├── RecommendationView.vue  # 智能荐股（使用 MainLayout）
│   ├── BacktestView.vue        # 策略回测（使用 MainLayout）
│   ├── SimulationView.vue      # 模拟交易（使用 MainLayout）
│   ├── HoldingsView.vue        # 我的持仓（使用 MainLayout）
│   └── SettingsView.vue        # 设置（使用 MainLayout）
└── router/
    └── index.ts                # 路由配置
```

## 布局架构确认 ✅

### 架构理解（AI 初始化时必须理解）：
1. **主结构**：`设计/ui/stitch/首页+nav-bar+left-bar`
   - 包含：左侧导航 + 头部导航 + 首页 main 内容
   - 用途：全局布局，所有页面共用

2. **页面结构**：
   - 所有页面都是 **main 内容**（在主结构的 main 区域内显示）
   - 必须使用主结构的导航（左侧导航 + 头部导航）
   - 不能有自己的独立导航

3. **智能荐股页面**：
   - 文件：`设计/ui/stitch/智能荐股router-main`
   - 理解：这是 **main 内容的一部分**，不是独立页面
   - 注意：它的头部（"智能选股中心"）是**页面标题**，不是独立导航
   - 路由：`/recommendation`

### 项目路由配置：
```
/              -> 首页 (使用 MainLayout)
/recommendation -> 智能荐股 (使用 MainLayout)
/backtest       -> 策略回测 (使用 MainLayout)
/simulation     -> 模拟交易 (使用 MainLayout)
/holdings       -> 我的持仓 (使用 MainLayout)
/settings       -> 设置 (使用 MainLayout)
```

### 组件结构：
```
App.vue
└── MainLayout.vue (全局导航：左侧导航 + 头部导航)
    └── RouterView
        ├── HomeView.vue (首页)
        ├── RecommendationView.vue (智能荐股 - main 内容)
        ├── BacktestView.vue (策略回测 - main 内容)
        ├── SimulationView.vue (模拟交易 - main 内容)
        ├── HoldingsView.vue (我的持仓 - main 内容)
        └── SettingsView.vue (设置 - main 内容)
```

### 页面优化 ✅
1. **修复页面高度问题**：
   - MainLayout 使用 `h-screen` 替代 `min-h-screen`
   - 添加 `overflow-hidden` 防止滚动条

2. **修正路由 name 规范**：
   - 所有路由 name 使用中文（首页、智能荐股、策略回测等）
   - 移除英文路由名

3. **优化左下角用户栏**：
   - 去掉独立的设置栏
   - 设置连接放到用户栏上
   - 用户栏右侧 icon 换成设置图标
   - 点击用户栏跳转到设置页面

4. **迁移到 Iconify 并本地化图标**：
   - 安装 @iconify/vue 依赖
   - 移除 Google Fonts Material Symbols
   - 创建 Icon 组件，使用本地化图标映射
   - 更新所有页面使用 Icon 组件
   - 图标映射表包含所有常用图标

### 文档更新：
- ✅ AI_CONTEXT.md - 添加布局架构说明
- ✅ AGENTS.md - 添加布局规则
- ✅ README.md - 添加布局架构说明
- ✅ 进度文档 - 确认架构理解

### 下一步：
- Phase 3: 业务模块开发（用户模块、智能荐股、策略回测、实盘模拟）

## Phase 3: 业务模块开发

### 3.1 智能荐股模块 - WebSocket 实时推送 ✅

#### 已完成：
1. ✅ 创建 Python WebSocket 服务器 (`backend/ai/websocket_server.py`)
   - 端口：8765
   - 支持消息类型：recommendation, heartbeat, system, subscribe
   - 广播消息给所有连接的客户端

2. ✅ 创建 WebSocket 消息模型 (`backend/ai/models.py`)
   - News, Analysis, RecommendationMessage 数据结构
   - WSMessage 传输格式
   - MessageType 消息类型常量

3. ✅ 创建 Python 客户端示例 (`backend/ai/websocket_client.py`)
   - RecommendationWebSocketClient 类
   - 供其他咨询项目接入使用

4. ✅ 前端 WebSocket 工具类 (`web-client/src/utils/websocket.ts`)
   - WebSocketClient 类
   - 自动重连、心跳机制
   - 与 Vue 生命周期集成

5. ✅ 更新 RecommendationView.vue
   - 添加 WebSocket 连接
   - 实时接收推送数据
   - 显示连接状态

6. ✅ 目录结构调整
   - `backend/ai/` 作为 AI 模块目录
   - 统一 `backend/requirements.txt`

#### 启动方式：
```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m recommendation.websocket_server

# 前端
cd web-client
npm run dev
```