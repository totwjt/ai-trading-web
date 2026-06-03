# 剩余任务清单

> 生成日期: 2026-06-03（最终更新）
> 基于 `docs/progress.md`、`AI_CONTEXT.md`、`docs/plan.md` 及代码库实际状态整理

---

## 目录

- [T1] 实盘模拟前后端联调验证 ✅
- [T2] WebSocket trading 主题对接 ✅
- [T3] WebSocket backtest.{id} 主题完善 ✅
- [T4] My Holdings 侧边栏入口恢复 ✅
- [T5] 前端单元测试建设 ✅
- [T6] API 集成测试 🔶
- [T7] Docker 生产部署验证 ✅
- [T8] 文档补齐 ✅
- [T9] 回测多标的支持扩展 ✅
- [T10] 风控系统前端页面对接 ❌ 忽略

---

## T1: 实盘模拟前后端联调验证

**状态**: ✅ 已完成

**完成情况**:
- [x] 后端 `/api/trading/simulations/` 路由确认可访问，返回真实数据
- [x] 修复 `api/simulation.ts` 中 `normalizeHolding` 字段映射：`cost_price→avgCost`, `profit_loss→pl`, `profit_loss_percent→plPercent`, `symbol→code`
- [x] 修复 `normalizeTrade` 字段映射：`timestamp→time`, `symbol→stockCode`, `name→stockName`, `trade_type→direction`，自动计算 `amount`
- [x] `npm run build` 通过

---

## T2: WebSocket trading 主题对接

**状态**: ✅ 已完成

**完成情况**:
- [x] `TradingView.vue` 已订阅 `trading` 主题
- [x] 页面加载时订阅，页面离开时取消订阅
- [x] `useWebSocket.ts` 包含 `TradingHandler` 类型定义

---

## T3: WebSocket backtest.{id} 主题完善

**状态**: ✅ 已完成

**完成情况**:
- [x] `BacktestDetail.vue` 增加 `ws.subscribe(['backtest.{id}'])`
- [x] 注册 `ws.onEvent('backtest.{id}', ...)` 实时更新 status/progress
- [x] WS 状态变更时自动停止轮询并刷新全量数据
- [x] 页面卸载时取消订阅和事件清理
- [x] `npm run build` 通过

---

## T4: My Holdings 侧边栏入口恢复

**状态**: ✅ 已完成 (2026-06-03)

**完成情况**:
- [x] 取消 `MainLayout.vue` 中 holdings 菜单项的注释
- [x] `npm run build` 通过

---

## T5: 前端单元测试建设

**状态**: ✅ 已完成

**完成情况**:
- [x] `tests/simulation.test.ts` — 23 个测试覆盖 `normalizeSimulation` / `normalizeHolding` / `normalizeTrade`：
  - camelCase / snake_case 输入
  - 字段优先级（camelCase 优先）
  - null/undefined 默认值
  - 额外字段保留
  - `lastTradeDateTime` 兼容
  - `symbol`/`ts_code` fallback
  - `amount` 自动计算
- [x] `tests/utils.test.ts` — 补充基础工具函数测试
- [x] `npm run test` — **全部 23 个测试通过**

---

## T6: API 集成测试

**状态**: 🔶 基础框架已搭建

**完成情况**:
- [x] 创建 `backend/tests/` 目录
- [x] `conftest.py` — ASGI Transport fixture
- [x] `test_health.py` — 基础健康检查测试
- [x] `test_simulation_api.py` — 模拟 API 测试框架

**待办**:
- [ ] 激活 `.venv` 后安装 `pytest` + `httpx` 运行测试
- [ ] 覆盖更多路由

---

## T7: Docker 生产部署验证

**状态**: ✅ 已完成

**完成情况**:
- [x] `backend/Dockerfile` 构建成功：`docker build backend/` → `ai-trading-backend:test` (389MB)
- [x] `WEB_CLIENT Dockerfile` 存在且结构正确（多阶段构建 + nginx）
- [x] `deploy/nginx.conf` 存在 (55行)
- [x] `.env.deploy` 存在

**注意事项**:
- 构建使用私有仓库 `192.168.66.26:8000` 基础镜像，在 Harbor 可访问环境下 `docker compose build` 即可

---

## T8: 文档补齐

**状态**: ✅ 已完成

**完成情况**:
- [x] `docs/API/strategy_service.md` ✅ 之前已完成
- [x] `docs/API/backtest_service.md` ✅ 之前已完成
- [x] `docs/DATABASE.md` ✅ 已创建：
  - 10 张表完整结构
  - 枚举类型
  - 关系图
  - 迁移管理说明

---

## T9: 回测多标的支持扩展

**状态**: ✅ 已实现

**完成情况**（检查代码确认已实现）:
- [x] `BacktestParams` 已定义 `symbols: string[]`
- [x] `EditStrategy.vue` 已有 `symbolInput` 输入框 + `parseSymbols()`
- [x] `buildBacktestParams()` 已包含 `symbols: parseSymbols(symbolInput.value)`
- [x] `buildStrategyPayload().config.symbols` 已包含
- [x] 后端引擎 `_resolve_symbols()` 已支持多标的
- [x] `DEFAULT_BACKTEST_SYMBOLS` 已配置默认股票池

---

## T10: 风控系统前端页面对接

**状态**: ❌ 已忽略（无后端 risk API，仅 WebSocket push）
