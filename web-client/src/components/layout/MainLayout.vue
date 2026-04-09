<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Icon from '@/components/common/Icon.vue'
import ThemeSwitcher from '@/components/common/ThemeSwitcher.vue'
import { useAuthStore } from '@/stores/authStore'
import { useUserStore } from '@/stores/userStore'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const userStore = useUserStore()

// 侧边栏菜单项
const menuItems = computed(() => [
  { path: '/', name: '首页', icon: 'home' },
  { path: '/recommendation', name: '智能荐股', icon: 'smart_toy' },
  { path: '/backtest', name: '策略回测', icon: 'assessment' },
  { path: '/simulation', name: '模拟交易', icon: 'swap_horiz' },
  { path: '/holdings', name: '我的持仓', icon: 'inventory' },
  { path: '/trading', name: '股票交易', icon: 'trending_up' },
  { path: '/trading-terminal', name: '交易终端', icon: 'analytics' },
  { path: '/risk-control', name: '风控系统', icon: 'shield' }
])

const userInfo = computed(() => ({
  name: authStore.user?.username || '未登录',
  level: authStore.permissions.includes('user:manage') ? '管理员' : '普通用户',
  avatar: 'user-secret'
}))

// 判断是否显示侧边栏
const showSidebar = computed(() => {
  return !route.meta.hideSidebar
})

const logout = async () => {
  authStore.clearSession()
  userStore.setUid('')
  await router.replace('/login')
}

</script>

<template>
  <div class="h-screen flex flex-col overflow-hidden">
    <!-- Header - 48px 高度 -->
    <header class="h-12 bg-card border-b border-border flex items-center justify-between px-4 z-50 shrink-0">
      <div class="flex items-center space-x-6">
        <!-- Logo 点击跳转首页 -->
        <div
          class="flex items-center space-x-2 cursor-pointer hover:opacity-80 transition-opacity"
          @click="router.push('/')"
        >
          <div class="bg-primary p-1 rounded">
            <Icon icon="mdi:chart-line" :size="20" class="text-white" />
          </div>
          <span class="text-lg font-bold text-textMain tracking-tight">华璟智璇 量化交易系统</span>
        </div>
        <!-- Global Search -->
        <div class="relative w-80">
          <input
            class="w-full h-8 bg-gray-100 dark:bg-gray-800 border-none rounded-full px-9 text-xs bg-card text-textMain focus:ring-2 focus:ring-primary/20 transition-all"
            placeholder="搜索股票代码 / 名称 / 简拼"
            type="text"
          />
          <svg class="w-3.5 h-3.5 absolute left-3 top-2 text-textMute" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
          </svg>
        </div>
      </div>
      <div class="flex items-center space-x-4 text-textSub">
        <ThemeSwitcher />
        <div class="flex items-center space-x-1 cursor-pointer hover:text-primary transition-colors">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
          </svg>
        </div>
        <button
          type="button"
          class="h-8 px-3 rounded border border-border text-xs text-textSub hover:text-primary hover:border-primary/40 transition-colors"
          @click="logout"
        >
          退出
        </button>
      </div>
    </header>

    <div class="flex flex-1 overflow-hidden">
      <!-- Sidebar - 176px 宽度 -->
      <aside v-if="showSidebar" class="w-44 bg-card border-r border-border flex flex-col shrink-0">
        <nav class="flex-1 py-2">
          <router-link
            v-for="item in menuItems"
            :key="item.path"
            :to="item.path"
            class="flex items-center px-3 py-2 space-x-2 text-xs font-medium transition-all"
            :class="route.path === item.path ? 'sidebar-item-active' : 'text-textSub hover:bg-primary/5 hover:text-primary'"
          >
            <Icon :icon="item.icon" :size="16" />
            <span>{{ item.name }}</span>
          </router-link>
        </nav>
        <div class="p-2 border-t border-border">
          <!-- 用户栏（包含设置 icon） -->
          <router-link
            to="/settings"
            class="flex items-center space-x-2 px-2 py-2 cursor-pointer group hover:bg-primary/5 rounded transition-colors"
          >
            <Icon
              :icon="userInfo.avatar"
              :size="24"
              class="text-textSub"
            />
            <div class="text-xs flex-1">
              <p class="font-medium text-textMain leading-none">{{ userInfo.name }}</p>
              <p class="text-xxs text-textMute mt-0.5">{{ userInfo.level }}</p>
            </div>
            <!-- 设置 icon -->
            <Icon icon="settings" :size="14" class="text-textMute group-hover:text-primary" />
          </router-link>
        </div>
      </aside>

      <!-- Main Content -->
      <main class="flex-1 overflow-y-auto bg-bgMain custom-scrollbar">
        <RouterView />
      </main>
    </div>
  </div>
</template>
