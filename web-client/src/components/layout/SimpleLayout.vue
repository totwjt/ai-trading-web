<script setup lang="ts">
// 简单布局组件 - 仅包含主内容区域
// 用于不需要全局导航的页面或弹窗页面
</script>

<template>
  <div class="min-h-screen bg-bgMain">
    <div class="route-transition-stage">
      <RouterView v-slot="{ Component, route: currentRoute }">
        <Transition name="route-switch" mode="out-in">
          <component :is="Component" :key="currentRoute.fullPath" />
        </Transition>
      </RouterView>
    </div>
  </div>
</template>

<style scoped>
</style>
