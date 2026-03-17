<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

// 侧边栏菜单项
const menuItems = computed(() => [
  { path: '/', name: '首页', icon: 'home' },
  { path: '/recommendation', name: '智能荐股', icon: 'smart_toy' },
  { path: '/backtest', name: '策略回测', icon: 'assessment' },
  { path: '/simulation', name: '模拟交易', icon: 'swap_horiz' },
  { path: '/holdings', name: '我的持仓', icon: 'inventory' }
])

// 用户信息
const userInfo = ref({
  name: '量化交易员',
  level: 'LV.5 资深用户',
  avatar: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAUFRuvDVoYwMUzc9WD6lbtldY6E2S3YU40H94c5xFAL7OKTWcd6QzPLNF-sF6b-J5-KFJAfin_7dzq0ZLEkrxaaqz1XQI1fIwB_4QgQrJXWQsfoVx10pixf2Akf7YyWxIDqe9vcPERa0dFSOqZc01gi-sDWoDRc8R9aFLACUfuHPfEUCHlve-WAXyhnpGIvwIi1aCJIdywpuj1Yn_rCCPXY3f0yKZA6bwW6vZbG7BYu-hCQlkT4S8Ya5p_-UHLozijfzB-FcTyFdUF'
})


</script>

<template>
  <div class="min-h-screen flex flex-col">
    <!-- Header -->
    <header class="h-14 bg-white border-b flex items-center justify-between px-4 z-50 shrink-0">
      <div class="flex items-center space-x-8">
        <div class="flex items-center space-x-2">
          <div class="bg-primary p-1 rounded">
            <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
            </svg>
          </div>
          <span class="text-xl font-bold text-gray-800 tracking-tight">AI Trading Pro</span>
        </div>
        <!-- Global Search -->
        <div class="relative w-96">
          <input 
            class="w-full h-9 bg-gray-100 border-none rounded-full px-10 text-sm focus:ring-2 focus:ring-primary/20 transition-all" 
            placeholder="搜索股票代码 / 名称 / 简拼" 
            type="text"
          />
          <svg class="w-4 h-4 absolute left-3 top-2.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
          </svg>
        </div>
      </div>
      <div class="flex items-center space-x-6 text-gray-600">
        <div class="flex items-center space-x-1 cursor-pointer hover:text-primary transition-colors">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
          </svg>
        </div>
      </div>
    </header>

    <div class="flex flex-1 overflow-hidden">
      <!-- Sidebar -->
      <aside class="w-48 bg-white border-r flex flex-col shrink-0">
        <nav class="flex-1 py-4">
          <router-link 
            v-for="item in menuItems"
            :key="item.path"
            :to="item.path"
            class="flex items-center px-6 py-3 space-x-3 text-sm font-medium transition-all"
            :class="route.path === item.path ? 'sidebar-item-active' : 'text-gray-600 hover:bg-gray-50 hover:text-primary'"
          >
            <span class="material-symbols-outlined text-lg">{{ item.icon }}</span>
            <span>{{ item.name }}</span>
          </router-link>
        </nav>
        <div class="p-4 border-t mt-auto space-y-4">
          <router-link 
            to="/settings"
            class="flex items-center px-2 py-2 space-x-3 text-sm text-gray-500 hover:text-primary transition-colors"
          >
            <span class="material-symbols-outlined text-lg">settings</span>
            <span>设置</span>
          </router-link>
          <div class="flex items-center space-x-3 px-2 pt-2 cursor-pointer group">
            <img 
              :src="userInfo.avatar" 
              alt="Avatar" 
              class="w-8 h-8 rounded-full border border-gray-200"
            />
            <div class="text-xs flex-1">
              <p class="font-medium text-gray-700 leading-none">{{ userInfo.name }}</p>
              <p class="text-xxs text-gray-400 mt-1">{{ userInfo.level }}</p>
            </div>
            <svg class="w-4 h-4 text-gray-400 group-hover:text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
            </svg>
          </div>
        </div>
      </aside>

      <!-- Main Content -->
      <main class="flex-1 overflow-y-auto bg-bgMain custom-scrollbar">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style scoped>
.sidebar-item-active {
  background-color: #EFF6FF;
  color: #0066FF;
  border-right: 4px solid #0066FF;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #D1D5DB;
  border-radius: 10px;
}
</style>