# 系统架构

## 系统类型
前后端分离 Web 应用

## 架构概览

- `design/` 设计规范与 UI 拼接稿
- `web-client/` Vue 3 + Vite 前端系统
- `backend/gateway/` API 网关
- `backend/data_sync/` 数据同步服务
- `backend/strategy/` 策略管理服务
- `backend/backtest/` 回测服务
- `backend/trading/` 交易与模拟盘服务
- `backend/recommendation/` 智能荐股服务
- `backend/common/` 后端公共模块

## 仓库结构

```text
/
├─ web-client/            # 前端系统
├─ backend/
│  ├─ gateway/            # API 网关
│  ├─ data_sync/          # 数据同步服务
│  ├─ strategy/           # 策略管理服务
│  ├─ backtest/           # 回测服务
│  ├─ trading/            # 交易服务与模拟盘
│  ├─ recommendation/     # 智能荐股服务
│  └─ common/             # 后端公共代码
├─ docs/                  # 项目文档
├─ design/                # 设计规范
├─ AI_CONTEXT.md          # AI 上下文约束
└─ AGENTS.md              # AI 协作规则
```

## 前端架构

- 技术栈：Vue 3、Vite、TypeScript、Pinia、Vue Router、Tailwind CSS、Ant Design Vue
- 前端入口：`web-client/src/main.ts`
- 应用壳：`web-client/src/App.vue`
- 全局布局：`web-client/src/components/layout/MainLayout.vue`
- 页面容器：`web-client/src/views/`

## 布局原则

- 左侧导航 + 顶部导航属于全局布局
- 各业务页面只负责 `main` 区域内容
- 智能荐股页面是 `main` 内容的一部分，不是独立导航系统
