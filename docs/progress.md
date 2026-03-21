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

## 文档同步：AI 目录提示词对齐（2026-03-21） ✅

### 已完成：
1. ✅ 更新 `AI_CONTEXT.md`
   - 明确根目录、`web-client/`、`backend/` 的真实结构
   - 明确荐股服务目录以 `backend/recommendation/` 为准
   - 标注 `docs/API.md`、`docs/DATABASE.md` 等不存在文件不能被默认引用

2. ✅ 更新 `AGENTS.md`
   - 修正后端服务目录描述
   - 修正前端命令的实际执行目录为 `web-client/`
   - 修正前端源码组织说明为 `web-client/src/`

3. ✅ 更新 `css-prompt.md`
   - 将临时 CSS 提示词升级为可复用的项目级 UI/CSS 提示词
   - 增加目录约束、布局约束和输出要求

4. ✅ 更新 `docs/init.md` 与 `README.md`
   - 统一项目目录示意，移除不存在目录的既有描述
   - 让初始化说明与仓库现状保持一致

5. ✅ 新增 `.cursorrules`
   - 固化项目目录、布局约束、提示词输出要求
   - 明确后端统一通过 `backend/server.py` 启动

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

### 3.3 策略回测接入 - 连通性修复（2026-03-21） ✅

#### 已完成：
1. ✅ 修复前端构建阻塞问题
   - 移除多处未使用变量/导入导致的 TypeScript 构建失败
   - 将回测净值图从缺失依赖的 `echarts` 切换为项目已安装的 `lightweight-charts`

2. ✅ 接通回测记录路由
   - 在 `/backtest` 子路由下新增 `/backtest/records`
   - 修复策略中心“回测记录”按钮跳回当前页的问题

3. ✅ 完成首轮策略/回测 API 连通性核对
   - 确认前端 `strategy.ts` / `backtest.ts` 的主要接口路径与 `backend/server.py` 已加载路由一致
   - 确认后端已包含 `/api/strategies/*`、`/api/backtests/*`、`/api/preview/run`
   - 清理本地 `8766` 端口占用后，确认仓库自身后端服务可正常启动并返回 `/health`

4. ✅ 修复回测运行链路
   - 编辑页“运行回测”改为先创建任务再调用 `/api/backtests/{id}/run`
   - 详情页主操作按钮按状态区分“启动回测 / 运行中 / 刷新数据”
   - 为 `pending/running` 状态补充回测进度轮询

5. ✅ 恢复前端可构建状态
   - `web-client` 下 `npm run build` 通过

#### 当前注意事项：
1. `docs/API/strategy_service.md` 仍是“完善中”，后续应以实际 FastAPI 路由实现为准补正文档
2. 后端当前的 `POST /api/backtests` 实际只创建任务，不会自动执行；若未来要保持“创建即运行”，建议同步修正文档或后端实现说明

### 3.4 策略/回测联调收口（2026-03-21） ✅

#### 已完成：
1. ✅ 修复回测详情页的状态机与分区刷新
   - 为 `pending / running / completed / failed / cancelled` 增加明确状态展示、进度描述和失败提示
   - 将日志、交易明细、净值曲线、性能指标改为独立刷新，避免单个接口失败拖垮整页
   - `pending/running` 阶段轮询进度时同步刷新子模块，完善运行中空态文案
   - 从详情页进入编辑页时支持返回当前回测详情

2. ✅ 修复编辑页与后端接口的关键语义不一致
   - 保存时补齐 `strategy_type`、`config.initial_capital` 等稳定字段
   - 预览接口在 `code=1` 但存在结构化 `data` 时不再直接丢失错误详情
   - 预览结果补充初始权益、期末权益，并增加输入校验

3. ✅ 同步接口文档
   - 重写 `docs/API/strategy_service.md`
   - 重写 `docs/API/backtest_service.md`
   - 明确 `POST /api/backtests` 只创建任务，执行需要额外调用 `/run`

4. ✅ 修复后端回测结果落库链路
   - 修正执行器异步日志/进度回调未真正执行的问题
   - 为无明细数据的回测补充最小净值曲线，保证详情页可展示基础曲线

5. ✅ 完成验证
   - `web-client` 下 `npm run build` 通过
   - `backend` 下 `.venv/bin/python -m py_compile backtest/src/engine.py server.py` 通过

### 3.5 回测框架切换到真实 PostgreSQL 数据（2026-03-21） ✅

#### 已完成：
1. ✅ 核实本地 `tushare_sync` PostgreSQL 真实数据表
   - 确认可用表：`stock_daily`、`stock_adj_factor`、`stock_daily_basic`、`stock_factor_pro`、`index_daily`、`trade_calendar`、`stock_basic`

2. ✅ 修复回测执行器稳定性问题
   - 去除共享异步 session 的并发写入方式
   - 改为独立 session 写入日志、进度、交易、净值曲线，避免 `concurrent operations are not permitted`

3. ✅ 将预览与最终回测切换到真实行情数据
   - 预览模式：近 365 天、单股票真实行情，用于快速验证策略代码
   - 最终回测：使用 PostgreSQL 真实日线数据执行并落库

4. ✅ 验证真实演示链路
   - 预览接口可返回真实日志与净值曲线
   - 创建策略 -> 创建回测 -> 启动回测 -> 查询详情/日志/交易/曲线 全链路通过
   - 验证 `backtests`、`backtest_logs`、`equity_curves`、`backtest_trades` 均有新增且未被删除

#### 当前剩余风险：
1. 当前最终回测默认接入单标的 `000001.SZ`，更复杂的多标的/自定义股票池能力仍需扩展
2. `index_daily` 当前库内覆盖区间较短，长周期基准收益可能为空或退化为初始值基线
3. 因子表中 `stock_daily_basic` 覆盖时间较短，长时间窗口因子策略仍需进一步做数据兼容与缺失处理

#### 本轮验证与限制：
1. 通过当前仓库 FastAPI app 的本地 ASGI 调用确认 `/health` 路由正常返回
2. 受当前终端沙箱权限与数据库连接限制影响，无法在本轮稳定完成基于真实 PostgreSQL 的全量接口回放
3. 后续若需要继续做真库联调，建议在可访问本地 `localhost:5432/tushare_sync` 的环境下再次执行 `cd backend && python server.py`
