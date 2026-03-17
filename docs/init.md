Node       22.22.1
pnpm       9.x
vite       5.2.x
vue        3.4.x
typescript 5.4.x

推荐 package.json:

vue 3.4.21
vite 5.2.10

typescript 5.4.5

ant-design-vue 4.1.2
@ant-design/icons-vue 7.0.0

tailwindcss 3.4.4
@tailwindcss/forms 0.5.7
@tailwindcss/container-queries 0.1.1

pinia 2.1.7
vue-router 4.3.2

axios 1.6.8

lightweight-charts 4.2.0
chart.js 4.4.2

dayjs 1.11.10
lodash-es 4.17.21
clsx 2.1.1

Tailwind 全局主题变量
tailwind.config = {
  theme: {
    extend: {

      colors: {

        primary: '#0066FF',

        up: '#FF0000',
        down: '#00B050',

        border: '#E5E7EB',

        bgMain: '#F9FAFB',

        card: '#FFFFFF',

        textMain: '#1F2937',
        textSub: '#6B7280',
        textMute: '#9CA3AF'

      },

      fontSize: {

        xxs: '0.7rem',

      }

    }
  }
}

参考目录结构：
ai-trading-web
│
├─ AI_CONTEXT.md
├─ README.md
│
├─ docs
│   ├─ ARCHITECTURE.md
│   ├─ DATABASE.md
│   └─ API.md
│
├─ design
│   └─ ui
│       └─ UI_RULES.md
├─ agents
│   └─ AGENTS.md
│
├─ skills
│   └─ SKILLS.md
│
├─ web-client                # 前端系统
│   ├─ src/
│   ├─ package.json
│   └─ vite.config.ts
│
└─ backend                   # 后端服务 (Python)
    ├─ gateway/              # API 网关
    ├─ data_sync/            # 数据同步服务
    ├─ strategy/             # 策略管理服务
    ├─ backtest/             # 回测服务
    ├─ trading/              # 交易服务
    └─ ai/                   # AI 分析服务