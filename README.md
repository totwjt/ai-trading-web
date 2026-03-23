# AI Trading Web

AI 股票交易平台 - 前后端分离架构

## 项目结构

```
ai-trading-web/
├── web-client/          # 前端项目 (Vue 3 + Vite)
├── backend/             # 后端服务 (Python)
├── docs/                # 文档
├── design/              # 设计规范
│   └── ui/stitch/       # UI 设计文件
│       ├── 首页+nav-bar+left-bar/  # 主结构（全局导航）
│       └── 智能荐股router-main/    # 智能荐股页面内容
├── AGENTS.md            # AI 协作规则
├── css-prompt.md        # UI/CSS 优化提示词
└── AI_CONTEXT.md        # AI 上下文配置
```

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

## 技术栈

### 前端 (web-client)
- Vue 3.4.21 (Composition API)
- Vite 5.2.10
- TypeScript 5.4.5
- Tailwind CSS 3.4.4
- Pinia (状态管理)
- Vue Router 4.3.2
- Ant Design Vue 4.1.2 (UI 组件)

### 后端 (backend)
- Python 3.9+
- FastAPI (API 框架)
- SQLAlchemy (ORM)
- Redis (缓存)
- PostgreSQL (数据库)

## 快速开始

### 前端开发

```bash
cd web-client
npm install
npm run dev
```

### 后端开发

```bash
cd backend
source .venv/bin/activate  # 激活虚拟环境
python server.py
```

**注意**：必须先激活虚拟环境 `.venv`，直接运行 `python server.py` 会因缺少依赖而失败。

## 开发命令

### 前端
- `npm run dev` - 启动开发服务器
- `npm run build` - 构建生产版本
- `npm run test` - 运行测试
- `npm run lint` - 代码检查
- `npm run format` - 代码格式化

### 后端
- `cd backend && source .venv/bin/activate && python server.py` - 启动统一后端服务（必须激活虚拟环境）
- `pytest` - 运行测试

## 文档

- [AI 上下文配置](./AI_CONTEXT.md)
- [项目架构](./docs/ARCHITECTURE.md)
- [UI 设计规范](./design/UI_RULES.md)
- [API 文档](./docs/API/)
- [开发计划](./docs/plan.md)

## 许可证

MIT License
