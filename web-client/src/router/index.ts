import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory('/'),
  routes: [
    // 使用 MainLayout 的路由（完整导航）
    {
      path: '/',
      component: () => import('@/components/layout/MainLayout.vue'),
      children: [
        {
          path: '',
          name: 'home',
          component: () => import('@/views/HomeView.vue'),
          meta: { title: '首页', icon: 'home' }
        },
        {
          path: 'backtest',
          name: 'backtest',
          component: () => import('@/views/BacktestView.vue'),
          meta: { title: '策略回测', icon: 'assessment' }
        },
        {
          path: 'simulation',
          name: 'simulation',
          component: () => import('@/views/SimulationView.vue'),
          meta: { title: '模拟交易', icon: 'swap_horiz' }
        },
        {
          path: 'holdings',
          name: 'holdings',
          component: () => import('@/views/HoldingsView.vue'),
          meta: { title: '我的持仓', icon: 'inventory' }
        },
        {
          path: 'settings',
          name: 'settings',
          component: () => import('@/views/SettingsView.vue'),
          meta: { title: '设置', icon: 'settings' }
        }
      ]
    },
    // 使用 RecommendationLayout 的路由（智能选股专用布局）
    {
      path: '/recommendation',
      component: () => import('@/components/layout/RecommendationLayout.vue'),
      children: [
        {
          path: '',
          name: 'recommendation',
          component: () => import('@/views/RecommendationView.vue'),
          meta: { title: '智能荐股', icon: 'smart_toy' }
        }
      ]
    }
  ]
})

export default router
