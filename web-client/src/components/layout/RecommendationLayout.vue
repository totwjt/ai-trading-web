<script setup lang="ts">
// 智能选股专用布局组件
</script>

<template>
  <div class="min-h-screen flex flex-col bg-slate-50">
    <!-- Header - 智能选股专用头部 -->
    <header class="bg-white border-b border-slate-200 sticky top-0 z-50">
      <div class="max-w-[1600px] mx-auto px-6 py-4 flex items-center justify-between">
        <div class="flex items-center gap-4">
          <span class="material-symbols-outlined text-primary text-3xl">analytics</span>
          <div>
            <h1 class="text-xl font-bold tracking-tight">智能选股中心 
              <span class="ml-2 text-xs font-normal text-slate-400 border border-slate-200 px-1 rounded">PRO TERMINAL</span>
            </h1>
            <p class="text-xs text-slate-500">基于AI深度学习的实时新闻驱动型股票推荐系统 • 实时更新</p>
          </div>
        </div>
        <div class="flex items-center gap-6">
          <div class="flex items-center gap-2 text-xs font-medium border-r border-slate-200 pr-6">
            <span class="w-2 h-2 bg-green-500 rounded-full"></span>
            数据连接中: 实时
          </div>
          <div class="flex gap-4">
            <button class="flex items-center gap-1 px-3 py-1.5 bg-primary text-white text-xs font-bold rounded">
              <span class="material-symbols-outlined text-sm">refresh</span>
              手动刷新
            </button>
            <button class="flex items-center gap-1 px-3 py-1.5 border border-slate-200 text-slate-600 text-xs font-bold rounded hover:bg-slate-50">
              <span class="material-symbols-outlined text-sm">filter_list</span>
              筛选条件
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="flex-1 max-w-[1600px] mx-auto w-full p-6">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
</style>