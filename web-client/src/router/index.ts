import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory('/'),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomeView.vue'),
      meta: { title: '首页', icon: 'home' }
    },
    {
      path: '/recommendation',
      name: 'recommendation',
      component: () => import('@/views/RecommendationView.vue'),
      meta: { title: '智能选股', icon: 'smart_toy' }
    },
    {
      path: '/backtest',
      name: 'backtest',
      component: () => import('@/views/BacktestView.vue'),
      meta: { title: '策略回测', icon: 'assessment' }
    },
    {
      path: '/simulation',
      name: 'simulation',
      component: () => import('@/views/SimulationView.vue'),
      meta: { title: '模拟交易', icon: 'swap_horiz' }
    },
    {
      path: '/holdings',
      name: 'holdings',
      component: () => import('@/views/HoldingsView.vue'),
      meta: { title: '我的持仓', icon: 'inventory' }
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/views/SettingsView.vue'),
      meta: { title: '设置', icon: 'settings' }
    }
  ]
})

export default router
