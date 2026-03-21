# AI Trading Web CSS / UI Prompt

用于本项目 UI 与样式优化时的统一提示词。目标不是“重做一版视觉稿”，而是在现有产品目录、布局架构和设计规范内做可落地优化。

## 一次性完整提示词

```text
你正在维护 AI Trading Web 项目，请严格按以下规则优化 UI / CSS：

【项目目录约束】
1. 前端工程目录固定为 `web-client/`
2. 所有前端源码修改必须落在 `web-client/src/`
3. 不要把前端文件创建到仓库根目录的 `src/`
4. 若涉及后端联调，荐股服务目录使用 `backend/recommendation/`，不要写成 `backend/ai/`

【布局架构约束】
1. 全局布局基于 `design/ui/stitch/首页+nav-bar+left-bar/code.html`
2. 所有页面都属于 `MainLayout` 的 `main` 内容区域
3. 页面只能优化 main 内容，不允许新增独立导航、独立侧边栏或重复头部
4. 智能荐股页 `design/ui/stitch/智能荐股router-main/code.html` 只是页面内容，不是独立站点

【设计规范约束】
1. 必须遵循 `design/UI_RULES.md`
2. 使用语义化颜色，例如 `primary`、`up`、`down`、`textMain`
3. 数字类信息必须优先使用 `font-numeric`
4. 表格和高密度数据区优先使用交易场景的紧凑布局
5. 不要随意引入新的十六进制颜色，除非先抽象为主题变量

【目录理解约束】
1. 可复用组件优先放在 `web-client/src/components/`
2. 页面级内容优先修改 `web-client/src/views/`
3. 路由相关修改放在 `web-client/src/router/`
4. 主题、样式常量优先收敛到 `web-client/src/config/` 或 `web-client/src/assets/`
5. 若新增代码，必须符合当前项目已有目录，不允许凭空创建未约定模块

【视觉优化约束】
1. 保持专业交易产品风格，强调数据可读性和操作效率
2. 顶部导航高度保持紧凑
3. 左侧导航宽度保持紧凑，不要牺牲 main 区域
4. 数据区优先级高于装饰区，避免大面积无效留白
5. 卡片、图表、表格、筛选栏之间建立清晰层级，但不要堆砌阴影和颜色

【输出要求】
1. 先说明将修改哪些 `web-client/src/` 文件
2. 明确说明是否触及 `MainLayout` 或仅调整某个 View 的 main 内容
3. 说明使用了哪些现有设计规则或主题变量
4. 若删除了冗余颜色、冗余装饰或重复结构，要明确列出
5. 若需求与当前目录或布局规则冲突，必须先指出冲突，不能直接实现
```

## 使用建议

- 适用于：页面视觉优化、卡片重排、表格密度优化、筛选栏整理、主题收敛
- 不适用于：全新产品定义、重构后端接口、脱离 `MainLayout` 的独立页面设计
- 每次使用前，先同步阅读：
  - `AI_CONTEXT.md`
  - `design/UI_RULES.md`
  - 目标页面对应的 `web-client/src/views/*.vue`
