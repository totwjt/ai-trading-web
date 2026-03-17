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
design/ui/UI_RULES.md

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

9 在每次确定完成一个阶段后，完善 docs/progress.md记录当前完成的步骤，然后git提交代码，remote：git@github.com:totwjt/ai-trading-web.git