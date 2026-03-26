# AI_CONTEXT

## 项目名称
AI 股票交易平台 Web 端

## 项目目标
为用户提供策略开发、策略回测、模拟交易、持仓管理和智能荐股能力。

## 当前仓库目录要求

### 根目录
```text
ai-trading-web/
├── AI_CONTEXT.md
├── AGENTS.md
├── README.md
├── css-prompt.md
├── docs/
├── design/
├── web-client/
└── backend/
```

### 前端目录
- 前端工程固定在 `web-client/`
- 包管理与构建文件在 `web-client/package.json`、`web-client/vite.config.ts`
- 前端源码固定在 `web-client/src/`

```text
web-client/src/
├── api/
├── assets/
├── components/
│   ├── backtest/
│   ├── common/
│   ├── features/
│   └── layout/
├── composables/
├── config/
├── router/
├── stores/
├── types/
├── utils/
├── views/
├── App.vue
└── main.ts
```

### 后端目录
- 后端代码固定在 `backend/`
- 已存在的服务目录：
  - `backend/gateway/`
  - `backend/data_sync/`
  - `backend/strategy/`
  - `backend/backtest/`
  - `backend/trading/`
  - `backend/recommendation/`
- 当前仓库中的荐股能力以 `backend/recommendation/` 为准，不要写成 `backend/ai/`
- 根目录下存在启动文件和公共模块：
  - `backend/server.py` - 统一后端入口
  - `backend/common/` - 公共模块
- 当前后端统一启动入口为 `backend/server.py`
- 标准启动方式：
  - `cd backend`
  - `python server.py`
- WebSocket 服务端口：`8766`（与 HTTP API 共用端口）
  - Socket.IO 路径：`/socket.io`
  - 使用 `python-socketio` 实现 Pub/Sub
  - WebSocket Pub/Sub 主题：
    - `recommendation` - 智能荐股推送
    - `zixuan` - 自选股实时行情
    - `trading` - 交易记录推送
    - `backtest.{id}` - 回测进度/结果

### WebSocket Pub/Sub 架构

### 技术选型
- 后端：`python-socketio` (端口 8766，HTTP/WebSocket 共用)
- 前端：`socket.io-client`
- 通信模式：订阅/发布 (Room 机制)

### Topic 列表

| Topic | 用途 | 开发进度 | 说明 |
|-------|------|---------|------|
| `zixuan` | 自选股票实时行情 | ✅ 已完成 | TradingView 页面使用 |
| `recommendation` | 智能荐股推送 | ✅ 已完成 | RecommendationView 页面使用 |
| `trading` | 交易记录实时推送 | 🔧 待对接 | 仅静态数据，需对接后端 |
| `backtest.{id}` | 回测进度/结果 | 🔧 待完善 | 使用统一 WebSocket 服务 |
| `risk` | 风控警报 | ✅ 已完成 | 外部项目通过 push_to_topic 推送 |
| `market` | 市场行情广播 | ⬜ 待开发 | 首页/市场概览预留 |
| `news` | 资讯快讯 | ⬜ 待开发 | 首页新闻预留 |
| `system` | 系统通知 | ⬜ 待开发 | 通用通知预留 |

### 前端架构：全局连接 + 页面独立订阅

```
App.vue (全局 WebSocket 连接)
    └── MainLayout.vue
        └── RouterView
            ├── HomeView.vue (订阅: market, news)
            ├── RecommendationView.vue (订阅: recommendation)
            ├── TradingView.vue (订阅: zixuan, trading)
            ├── BacktestView.vue (订阅: backtest.{id})
            └── ...

特点：
1. 全局单例 WebSocket 连接，避免重复连接
2. 每个页面独立订阅所需 topic
3. 页面离开时取消订阅（连接保持）
4. 消息仅用于实时显示，不做本地持久化存储
```

### 前端使用方式

```typescript
import { useWebSocket } from '@/composables/useWebSocket'

const ws = useWebSocket()

onMounted(() => {
  ws.subscribe(['zixuan'])  // 直接订阅，无需等待连接

  ws.onZixuan((data) => {
    watchlist.value = data
  })
})

onUnmounted(() => {
  ws.unsubscribe(['zixuan'])  // 离开页面时取消订阅
})
```

### 外部服务推送

外部服务（包括 7 个外部项目）通过 `push_from_external` 事件推送：

```python
# 外部服务使用统一客户端
from common.socketio_client import UnifiedSocketIOClient

client = UnifiedSocketIOClient(url="http://localhost:8766", client_type="external_system")
await client.connect()
await client.push_to_topic('zixuan', stock_data)  # 推送自选行情
await client.push_to_topic('recommendation', news_data)  # 推送荐股
```

### 外部服务订阅

外部服务可以订阅 `risk` 等 topic 接收实时推送：

```python
import socketio

sio = socketio.Client()

@sio.event
def connect():
    sio.emit('subscribe', {'topics': ['risk']})

@sio.on('risk')
def on_risk(data):
    print(f"收到风控警报: {data}")

sio.connect('http://192.168.66.186:8766', transports=['polling'])
sio.wait()
```

**测试脚本位置：**
- `test/test.py` - 纯订阅客户端
- `test/test_push.py` - 订阅+推送测试
- `backend/test_risk_push.py` - 推送测试服务
- `backend/test_risk_receive.py` - 接收测试服务

## 系统模块
- `user` 用户系统
- `market` 股票市场数据展示
- `strategy` 策略生成与策略管理
- `backtest` 策略回测系统
- `portfolio` 用户持仓与资产
- `simulator` 模拟交易系统
- `recommendation` 智能荐股系统 ✅ WebSocket 已完成
- `trading` 股票交易（自选股管理、条件检索、实时行情）✅ 自选行情 WebSocket 已完成

## 布局架构（重要）

### 主结构
- 文件：`design/ui/stitch/首页+nav-bar+left-bar/code.html`
- 包含：左侧导航 + 头部导航 + 首页 main 内容
- 用途：全局布局，所有页面共用

### 页面结构
- 所有页面都是主结构 `main` 区域中的内容
- 所有业务页面必须复用全局导航
- 不允许为单个页面再创建独立导航框架

### 智能荐股页面
- 文件：`design/ui/stitch/智能荐股router-main/code.html`
- 该设计稿只是 `main` 内容，不是独立站点
- “智能选股中心”是页面标题，不是页面级导航
- 路由：`/recommendation`

### 项目路由
```text
/               -> 首页
/recommendation -> 智能荐股
/backtest       -> 策略回测
/simulation     -> 模拟交易
/trading        -> 股票交易
/holdings       -> 我的持仓
/settings       -> 设置
```

### 页面组件结构
```text
App.vue
└── MainLayout.vue
    └── RouterView
        ├── HomeView.vue
        ├── RecommendationView.vue
        ├── BacktestView.vue
        ├── SimulationView.vue
        ├── TradingView.vue
        ├── HoldingsView.vue
        └── SettingsView.vue
```

## 文档索引

### 已存在文档
- 架构：`docs/ARCHITECTURE.md`
- UI 规则：`design/UI_RULES.md`
- 初始化说明：`docs/init.md`
- 开发计划：`docs/plan.md`
- 进度记录：`docs/progress.md`
- 回测说明：`docs/backtest.md`
- API 文档目录：`docs/API/`

### 当前仓库中不存在的文档
- `docs/DATABASE.md`
- `docs/API.md`
- `skills/SKILLS.md`
- `agents/AGENTS.md`

如果任务依赖这些文件，必须先确认是否需要新建文档或向用户澄清，不能假设它们已经存在。

## AI 提示词更新基线

以后凡是为本项目编写提示词、规则或 AI 协作文档，必须同时满足以下要求：

1. 明确前端工作目录是 `web-client/`，不是仓库根目录
2. 明确前端源码目录是 `web-client/src/`
3. 明确后端荐股服务目录使用 `backend/recommendation/`
4. 涉及布局时，必须说明所有页面都挂载在 `MainLayout` 的 `main` 内容区域
5. 涉及 UI 时，必须引用 `design/UI_RULES.md`
6. 涉及 API 时，优先查看 `docs/API/` 下已有文档，而不是引用不存在的 `docs/API.md`
7. 涉及数据库时，不能假设 `docs/DATABASE.md` 已存在；若缺失，必须向用户确认
8. 不允许在提示词中引用当前仓库不存在的目录作为既有事实
9. 涉及后端启动命令时，统一使用 `cd backend` 后执行 `python server.py`

## AI 工作规则

1. 任何任务开始前读取 `AI_CONTEXT.md`
2. UI 相关任务必须读取 `design/UI_RULES.md`
3. API 相关任务优先读取 `docs/API/` 下对应文档
4. 数据库结构不能假设；若没有明确文档或模型定义，必须先确认
5. 不允许创建未定义模块或凭空扩展服务边界
6. 如果存在信息缺失、接口不明确、数据结构未定义，必须先澄清
7. 通常按照 `docs/plan.md` 的阶段推进
8. 完成明确阶段后，更新 `docs/progress.md`
9. 新增 AI 提示词时，要同步校验是否符合本文件的目录要求

## 策略回测补充约束（2026-03-21）

1. `编译运行 / 预览` 的目标是快速验证策略代码是否可执行，不是最终回测结果
2. 预览模式允许缩短到近 365 天、少量股票，以便尽快返回日志和结果
3. `运行回测` 才是最终回测框架，应基于真实数据源执行，并将结果落库保留
4. 行情与因子数据源来自本地 PostgreSQL `tushare_sync`，禁止在回测过程中调用外部行情 API
5. 当前 PostgreSQL 中已经确认存在以下候选表：
   - `public.stock_daily`：股票日线 OHLCV
   - `public.stock_adj_factor`：复权因子
   - `public.stock_daily_basic`：估值与市值基础因子
   - `public.stock_factor_pro`：日线 + 复权价格 + 技术指标/因子
   - `public.index_daily`：指数日线（含 `000300.SH`）
   - `public.trade_calendar`：交易日历
   - `public.stock_basic`：股票基础信息
6. 若实现与这些真实表结构不一致，必须先按库表结构修正，不能继续依赖随机样本数据作为最终回测输入
