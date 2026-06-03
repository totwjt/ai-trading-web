# 数据库文档

## 概述

项目使用 PostgreSQL 作为主数据库，通过 SQLAlchemy (异步) 进行 ORM 操作。

- **数据库**: PostgreSQL
- **ORM**: SQLAlchemy (async, asyncpg driver)
- **连接 URL**: `postgresql+asyncpg://postgres@localhost:5432/tushare_sync` (可通过 `DATABASE_URL` 环境变量覆盖)
- **基类**: `common.database.Base` (`DeclarativeBase`)

## 数据库配置

配置文件: `backend/common/database.py`

```python
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres@localhost:5432/tushare_sync")
```

配置参数:
- 连接池大小: 10
- 最大溢出: 20
- 自动重连: `pool_pre_ping=True`

## 表结构

### 1. trading 模块 - `backend/trading/models.py`

#### users - 用户表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, autoincrement | 主键 |
| uid | String(64) | NOT NULL, UNIQUE, INDEX | 用户唯一标识 |
| created_at | DateTime | default=now | 创建时间 |
| updated_at | DateTime | default=now, onupdate | 更新时间 |

#### terminals - 终端表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, autoincrement | 主键 |
| uid | String(64) | FK -> users.uid, NOT NULL, INDEX | 用户ID |
| terminal_id | String(128) | NOT NULL, UNIQUE, INDEX | 终端唯一标识 |
| mac_address | String(32) | NOT NULL | 终端MAC地址 |
| account_name | String(128) | NOT NULL | 终端账号名称 |
| terminal_name | String(128) | nullable | 终端显示名称 |
| terminal_city | String(32) | default='北京' | 终端展示城市 |
| active | Boolean | NOT NULL, default=True | 是否启用 |
| created_at | DateTime | default=now | 创建时间 |
| updated_at | DateTime | default=now, onupdate | 更新时间 |

索引: `idx_terminal_uid_terminal_id` (uid, terminal_id)

#### watchlist - 自选股票表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, autoincrement | 主键 |
| ts_code | String(20) | NOT NULL, INDEX | 股票代码 |
| name | String(50) | NOT NULL | 股票名称 |
| added_at | DateTime | default=now | 添加时间 |

索引: `idx_user_ts_code` (ts_code)

#### pending_orders - 挂单表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, autoincrement | 主键 |
| uid | String(64) | FK -> users.uid, NOT NULL, INDEX | 用户ID |
| stock_code | String(20) | NOT NULL, INDEX | 股票代码 |
| stock_name | String(64) | NOT NULL | 股票名称 |
| order_price | Float | NOT NULL | 挂单价格 |
| order_quantity | Integer | NOT NULL | 挂单数量 |
| scheduled_at | DateTime | NOT NULL, INDEX | 计划挂单时间 |
| status | String(16) | NOT NULL, default='pending' | 状态: pending/success/triggered/cancelled |
| created_at | DateTime | default=now | 创建时间 |
| updated_at | DateTime | default=now, onupdate | 更新时间 |

索引:
- `idx_pending_orders_uid_status` (uid, status)
- `idx_pending_orders_uid_scheduled` (uid, scheduled_at)

#### pending_order_configs - 挂单配置表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, autoincrement | 主键 |
| uid | String(64) | FK -> users.uid, UNIQUE, INDEX | 用户ID |
| enabled | Boolean | NOT NULL, default=True | 是否启用挂单 |
| default_delay_minutes | Integer | NOT NULL, default=10 | 默认挂单延迟(分钟) |
| auto_submit | Boolean | NOT NULL, default=False | 是否自动提交 |
| created_at | DateTime | default=now | 创建时间 |
| updated_at | DateTime | default=now, onupdate | 更新时间 |

### 2. backtest 模块 - `backend/backtest/src/models.py`

#### strategies - 策略表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, autoincrement | 主键 |
| name | String(100) | NOT NULL | 策略名称 |
| strategy_type | String(50) | nullable | 策略类型 |
| user_id | Integer | default=1 | 用户ID (目前写死) |
| status | Enum(StrategyStatus) | default=PAUSED | 策略状态 (running/paused/stopped/error) |
| sta | Boolean | default=False | 策略是否在交易中运行 |
| code | Text | NOT NULL | 策略Python代码 |
| config | JSON | default={} | 策略配置 |
| description | Text | nullable | 策略描述 |
| created_at | DateTime | server_default=now | 创建时间 |
| updated_at | DateTime | server_default=now, onupdate | 更新时间 |

关系: backtests (一对多，级联删除)

#### backtests - 回测记录表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, autoincrement | 主键 |
| strategy_id | Integer | FK -> strategies.id, NOT NULL | 策略ID |
| user_id | Integer | default=1 | 用户ID |
| status | Enum(BacktestStatus) | default=PENDING | 状态 (pending/running/completed/failed/cancelled) |
| start_date | String(10) | NOT NULL | 开始日期 |
| end_date | String(10) | NOT NULL | 结束日期 |
| initial_capital | Float | default=1000000.0 | 初始资金 |
| frequency | String(10) | default='1d' | 数据频率 |
| final_equity | Float | nullable | 期末权益 |
| total_return | Float | nullable | 总收益率(%) |
| benchmark_return | Float | nullable | 基准收益率(%) |
| annual_return | Float | nullable | 年化收益率(%) |
| max_drawdown | Float | nullable | 最大回撤(%) |
| sharpe_ratio | Float | nullable | 夏普比率 |
| win_rate | Float | nullable | 胜率(%) |
| profit_loss_ratio | Float | nullable | 盈亏比 |
| metrics | JSON | default={} | 扩展性能指标 |
| error_message | Text | nullable | 错误信息 |
| progress | Integer | default=0 | 进度(0-100) |
| execution_time | Float | nullable | 执行时间(秒) |
| created_at | DateTime | server_default=now | 创建时间 |
| started_at | DateTime | nullable | 开始时间 |
| completed_at | DateTime | nullable | 完成时间 |

关系: strategy, trades, logs, equity_curve (一对多，级联删除)

索引:
- `idx_backtests_strategy_id` (strategy_id)
- `idx_backtests_user_id` (user_id)
- `idx_backtests_status` (status)
- `idx_backtests_created_at` (created_at)

#### backtest_trades - 回测交易明细表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, autoincrement | 主键 |
| backtest_id | Integer | FK -> backtests.id, NOT NULL | 关联回测ID |
| trade_time | String(30) | NOT NULL | 成交时间 |
| symbol | String(20) | NOT NULL | 股票代码 |
| name | String(50) | nullable | 股票名称 |
| direction | Enum(TradeDirection) | NOT NULL | 方向 (buy/sell) |
| price | Float | NOT NULL | 成交价格 |
| quantity | Integer | NOT NULL | 成交数量 |
| amount | Float | NOT NULL | 成交金额 |
| commission | Float | default=0.0 | 手续费 |
| profit | Float | nullable | 盈亏 |

关系: backtest

索引:
- `idx_trades_backtest_id` (backtest_id)
- `idx_trades_symbol` (symbol)

#### backtest_logs - 回测系统日志表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, autoincrement | 主键 |
| backtest_id | Integer | FK -> backtests.id, NOT NULL | 关联回测ID |
| log_time | String(30) | NOT NULL | 日志时间 |
| level | Enum(LogLevel) | NOT NULL | 级别 (DEBUG/INFO/WARNING/ERROR/SUCCESS) |
| message | Text | NOT NULL | 日志内容 |

关系: backtest

索引: `idx_logs_backtest_id` (backtest_id)

#### equity_curves - 净值曲线数据点表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, autoincrement | 主键 |
| backtest_id | Integer | FK -> backtests.id, NOT NULL | 关联回测ID |
| date | String(10) | NOT NULL | 日期 |
| equity | Float | NOT NULL | 策略权益 |
| benchmark | Float | NOT NULL | 基准权益 |
| returns | Float | default=0.0 | 日收益率(%) |

关系: backtest

索引:
- `idx_equity_backtest_id` (backtest_id)
- `idx_equity_date` (date)

### 3. recommendation 模块 - `backend/recommendation/models.py`

此模块定义 WebSocket 消息模型 (dataclass)，非 SQLAlchemy 模型。

| 模型 | 说明 |
|------|------|
| StockInfo | 股票信息 (code, name, score) |
| News | 新闻信息 (title, content, publish_time, source, url) |
| Analysis | 分析结果 (利好版块, 利好股票, 分析因素, 详细分析) |
| RecommendationMessage | 完整荐股消息 (news + analysis) |
| WSMessage | WebSocket 传输格式 (type, payload, timestamp, message_id) |

## 枚举类型

### BacktestStatus
- `PENDING` - 等待中
- `RUNNING` - 运行中
- `COMPLETED` - 已完成
- `FAILED` - 失败
- `CANCELLED` - 已取消

### StrategyStatus
- `RUNNING` - 运行中
- `PAUSED` - 已暂停
- `STOPPED` - 已停止
- `ERROR` - 错误

### TradeDirection
- `BUY` - 买入
- `SELL` - 卖出

### LogLevel
- `DEBUG`
- `INFO`
- `WARNING`
- `ERROR`
- `SUCCESS`

## 初始化

数据库表在应用启动时自动创建:

```python
from common.database import init_db

async def startup():
    await init_db()  # 调用 Base.metadata.create_all
```
