# 系统架构

系统类型
前后端分离 Web应用

架构
design
设计规范

Web Frontend
Vue3 + Vite

data_sync
股票数据同步

strategy_service
策略生成服务

backtest_service
回测服务

trade_service
模拟交易服务

ai-service
智能荐股

/
│
├─ web-client                # 前端系统
├─ gateway-service           # API网关
├─ data-sync-service         # 数据同步服务
├─ strategy-service          # 策略管理服务
├─ backtest-service          # 回测服务
├─ trading-service           # 交易服务&模拟盘
├─ ai-service                # AI分析服务