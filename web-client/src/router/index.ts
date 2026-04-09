import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { useUserStore } from '@/stores/userStore'

const router = createRouter({
  history: createWebHistory('/'),
  routes: [
    {
      path: '/login',
      name: '登录',
      component: () => import('@/views/LoginView.vue'),
      meta: { title: '登录', requiresAuth: false, layout: 'simple' }
    },
    {
      path: '/',
      name: '首页',
      component: () => import('@/views/HomeView.vue'),
      meta: { title: '首页', icon: 'home', requiresAuth: true }
    },
    {
      path: '/recommendation',
      name: '智能荐股',
      component: () => import('@/views/RecommendationView.vue'),
      meta: { title: '智能荐股', icon: 'smart_toy', requiresAuth: true }
    },
    {
      path: '/backtest',
      name: '策略回测',
      component: () => import('@/views/BacktestView.vue'),
      meta: { title: '策略回测', icon: 'assessment', requiresAuth: true },
      children: [
        {
          path: '',
          name: '策略中心',
          component: () => import('@/views/backtest/StrategyCenter.vue'),
          meta: { title: '策略中心', requiresAuth: true }
        },
        {
          path: 'records',
          name: '回测记录',
          component: () => import('@/views/backtest/BacktestList.vue'),
          meta: { title: '回测记录', requiresAuth: true }
        }
      ]
    },
    {
      path: '/backtest/edit/:id?',
      name: '编辑策略',
      component: () => import('@/views/backtest/EditStrategy.vue'),
      meta: { title: '编辑策略', hideSidebar: true, requiresAuth: true }
    },
    {
      path: '/backtest/detail/:id',
      name: '回测详情',
      component: () => import('@/views/backtest/BacktestDetail.vue'),
      meta: { title: '回测详情', hideSidebar: true, requiresAuth: true }
    },
    {
      path: '/simulation',
      name: '模拟交易',
      component: () => import('@/views/SimulationView.vue'),
      meta: { title: '模拟交易', icon: 'swap_horiz', requiresAuth: true },
      children: [
        {
          path: '',
          name: '模拟列表',
          component: () => import('@/views/simulation/SimulationList.vue'),
          meta: { title: '模拟列表', requiresAuth: true }
        }
      ]
    },
    {
      path: '/simulation/detail/:id',
      name: '模拟详情',
      component: () => import('@/views/simulation/SimulationDetail.vue'),
      meta: { title: '模拟详情', hideSidebar: true, requiresAuth: true }
    },
    {
      path: '/holdings',
      name: '我的持仓',
      component: () => import('@/views/HoldingsView.vue'),
      meta: { title: '我的持仓', icon: 'inventory', requiresAuth: true }
    },
    {
      path: '/trading',
      name: '股票交易',
      component: () => import('@/views/TradingView.vue'),
      meta: { title: '股票交易', icon: 'trending_up', requiresAuth: true }
    },
    {
      path: '/trading-terminal',
      name: '交易终端',
      component: () => import('@/views/TradingTerminalView.vue'),
      meta: { title: '交易终端', icon: 'analytics', requiresAuth: true }
    },
    {
      path: '/risk-control',
      name: '风控系统',
      component: () => import('@/views/RiskControlView.vue'),
      meta: { title: '风控系统', icon: 'security', requiresAuth: true }
    },
    {
      path: '/settings',
      name: '设置',
      component: () => import('@/views/SettingsView.vue'),
      meta: { title: '设置', icon: 'settings', requiresAuth: true }
    }
  ]
})

router.beforeEach((to) => {
  const authStore = useAuthStore()
  const userStore = useUserStore()
  const requiresAuth = to.meta.requiresAuth !== false
  const requiredPermission = typeof to.meta.permission === 'string' ? to.meta.permission : ''
  const allowUidCompatAccess = !authStore.isAuthenticated && userStore.hasUser

  if (requiresAuth && !authStore.isAuthenticated && !allowUidCompatAccess) {
    return {
      path: '/login',
      query: {
        redirect: to.fullPath
      }
    }
  }

  if (to.path === '/login' && authStore.isAuthenticated) {
    return '/'
  }

  if (requiredPermission && !authStore.hasPermission(requiredPermission)) {
    return '/'
  }

  return true
})

export default router
