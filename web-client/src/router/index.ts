import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory('/'),
  routes: [
    {
      path: '/',
      name: '首页',
      component: () => import('@/views/HomeView.vue'),
      meta: { title: '首页', icon: 'home' }
    },
    {
      path: '/recommendation',
      name: '智能荐股',
      component: () => import('@/views/RecommendationView.vue'),
      meta: { title: '智能荐股', icon: 'smart_toy' }
    },
    {
      path: '/backtest',
      name: '策略回测',
      component: () => import('@/views/BacktestView.vue'),
      meta: { title: '策略回测', icon: 'assessment' },
      children: [
        {
          path: '',
          name: '策略中心',
          component: () => import('@/views/backtest/StrategyCenter.vue'),
          meta: { title: '策略中心' }
        },
        {
          path: 'records',
          name: '回测记录',
          component: () => import('@/views/backtest/BacktestList.vue'),
          meta: { title: '回测记录' }
        }
      ]
    },
    {
      path: '/backtest/edit/:id?',
      name: '编辑策略',
      component: () => import('@/views/backtest/EditStrategy.vue'),
      meta: { title: '编辑策略', hideSidebar: true }
    },
    {
      path: '/backtest/detail/:id',
      name: '回测详情',
      component: () => import('@/views/backtest/BacktestDetail.vue'),
      meta: { title: '回测详情', hideSidebar: true }
    },
    {
      path: '/simulation',
      name: '模拟交易',
      component: () => import('@/views/SimulationView.vue'),
      meta: { title: '模拟交易', icon: 'swap_horiz' },
      children: [
        {
          path: '',
          name: '模拟列表',
          component: () => import('@/views/simulation/SimulationList.vue'),
          meta: { title: '模拟列表' }
        }
      ]
    },
    {
      path: '/simulation/detail/:id',
      name: '模拟详情',
      component: () => import('@/views/simulation/SimulationDetail.vue'),
      meta: { title: '模拟详情', hideSidebar: true }
    },
    {
      path: '/holdings',
      name: '我的持仓',
      component: () => import('@/views/HoldingsView.vue'),
      meta: { title: '我的持仓', icon: 'inventory' }
    },
    {
      path: '/trading',
      name: '股票交易',
      component: () => import('@/views/TradingView.vue'),
      meta: { title: '股票交易', icon: 'trending_up' }
    },
    {
      path: '/trading-terminal',
      name: '交易终端',
      component: () => import('@/views/TradingTerminalView.vue'),
      meta: { title: '交易终端', icon: 'analytics' }
    },
    {
      path: '/risk-control',
      name: '风控系统',
      component: () => import('@/views/RiskControlView.vue'),
      meta: { title: '风控系统', icon: 'security' }
    },
    {
      path: '/settings',
      name: '设置',
      component: () => import('@/views/SettingsView.vue'),
      meta: { title: '设置', icon: 'settings' }
    }
  ]
})

export default router
