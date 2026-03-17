# AI_CONTEXT

项目名称
AI股票交易平台 Web端

项目目标
为用户提供策略开发、策略回测、模拟交易、持仓管理和智能选股能力。

系统模块

user
用户系统

market
股票市场数据展示

strategy
策略生成与策略管理

backtest
策略回测系统

portfolio
用户持仓与资产

simulator
模拟交易系统

## 布局架构（重要）

### 主结构
- **文件**: `design/ui/stitch/首页+nav-bar+left-bar/code.html`
- **包含**: 左侧导航 + 头部导航 + 首页 main 内容
- **用途**: 全局布局，所有页面共用

### 页面结构
- **所有页面**都是 **main 内容**（在主结构的 main 区域内显示）
- **必须**使用主结构的导航（左侧导航 + 头部导航）
- **不能**有自己的独立导航

### 智能荐股页面
- **文件**: `design/ui/stitch/智能荐股router-main/code.html`
- **理解**: 这是 **main 内容的一部分**，不是独立页面
- **注意**: 它的头部（"智能选股中心"）是**页面标题**，不是独立导航
- **路由**: `/recommendation`

### 项目路由
```
/              -> 首页 (使用 MainLayout)
/recommendation -> 智能荐股 (使用 MainLayout)
/backtest       -> 策略回测 (使用 MainLayout)
/simulation     -> 模拟交易 (使用 MainLayout)
/holdings       -> 我的持仓 (使用 MainLayout)
/settings       -> 设置 (使用 MainLayout)
```

### 组件结构
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

文档索引

架构
docs/ARCHITECTURE.md

数据库
docs/DATABASE.md

API规范
docs/API.md

领域模型
docs/DOMAIN.md

UI设计规范
design/UI_RULES.md

docs/plan.md
当前项目进度
docs/progress.md

AI能力
skills/SKILLS.md

Agent角色
agents/AGENTS.md

临时、项目初期

初始化版本
docs/init.md

# 重要提示：
涉及到后端API能力功能时必须构建单元测试
在必要时可以新增本项目skill，来提升AI识别效率

AI工作规则

1 任何任务开始前读取 AI_CONTEXT.md

2 如果任务涉及 API
   读取 docs/API.md

3 如果任务涉及数据库
   读取 docs/DATABASE.md

4 不允许假设数据库结构

5 不允许创建未定义模块

6 如果需求存在以下情况
   - 信息缺失
   - 接口不明确
   - 数据结构未定义

   必须暂停执行并向用户提问

7 任何需求必须达到 100% 明确后才允许开始实现

8 通常项目会按照docs/plan.md来按照步骤开发

9 在每次确定完成一个阶段后，完善 docs/progress.md记录当前完成的步骤，然后git提交代码（add+commit+push），remote：git@github.com:totwjt/ai-trading-web.git