<script setup lang="ts">
import { useTheme } from '@/composables/useTheme'
import Icon from '@/components/common/Icon.vue'

const { mode, scheme, themes, setScheme, toggleMode } = useTheme()

const schemeList = Object.entries(themes).map(([key, value]) => ({
  key: key as 'default' | 'ocean' | 'forest',
  name: value.name
}))
</script>

<template>
  <div class="flex items-center gap-2">
    <!-- 主题预设选择 -->
    <div class="relative">
      <select
        :value="scheme"
        @change="setScheme(($event.target as HTMLSelectElement).value as any)"
        class="appearance-none pl-7 pr-6 py-1 text-xs border border-border rounded bg-card text-textMain cursor-pointer hover:border-primary transition-colors"
      >
        <option v-for="s in schemeList" :key="s.key" :value="s.key">
          {{ s.name }}
        </option>
      </select>
      <Icon icon="theme" :size="12" class="absolute left-2 top-1/2 -translate-y-1/2 text-textMute pointer-events-none" />
    </div>

    <!-- 亮暗模式切换 -->
    <button
      @click="toggleMode"
      class="p-1 rounded border border-border bg-card hover:bg-primary/5"
      :title="mode === 'light' ? '切换到深色模式' : '切换到浅色模式'"
    >
      <Icon :icon="mode === 'light' ? 'dark_mode' : 'light_mode'" :size="14" />
    </button>
  </div>
</template>
