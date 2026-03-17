# AI Trading Web

AI 股票交易平台 - 前后端分离架构

## 项目结构

```
ai-trading-web/
├── web-client/          # 前端项目 (Vue 3 + Vite)
├── backend/             # 后端服务 (Python)
├── docs/                # 文档
├── design/              # 设计规范
├── agents/              # AI 代理配置
├── skills/              # AI 技能配置
└── AI_CONTEXT.md        # AI 上下文配置
```

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
cd backend/gateway
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## 开发命令

### 前端
- `npm run dev` - 启动开发服务器
- `npm run build` - 构建生产版本
- `npm run test` - 运行测试
- `npm run lint` - 代码检查
- `npm run format` - 代码格式化

### 后端
- `uvicorn main:app --reload` - 启动开发服务器
- `pytest` - 运行测试

## 文档

- [AI 上下文配置](./AI_CONTEXT.md)
- [项目架构](./docs/ARCHITECTURE.md)
- [UI 设计规范](./design/UI_RULES.md)
- [API 文档](./docs/API/)
- [开发计划](./docs/plan.md)

## 许可证

MIT License
