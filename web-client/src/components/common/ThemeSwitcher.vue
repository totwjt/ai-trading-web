<script setup lang="ts">
import { useTheme } from '@/composables/useTheme'
import Icon from '@/components/common/Icon.vue'

const { mode, scheme, themes, setMode, setScheme, toggleMode } = useTheme()

const schemeList = Object.entries(themes).map(([key, value]) => ({
  key: key as 'default' | 'ocean' | 'forest',
  name: value.name
}))
</script>

<template>
  <div class="flex items-center gap-3">
    <select
      :value="scheme"
      @change="setScheme(($event.target as HTMLSelectElement).value as any)"
      class="text-xs border border-border rounded px-2 py-1 bg-card text-textMain"
    >
      <option v-for="s in schemeList" :key="s.key" :value="s.key">
        {{ s.name }}
      </option>
    </select>

    <button
      @click="toggleMode"
      class="p-1.5 rounded border border-border bg-card hover:bg-primary/5"
    >
      <Icon :icon="mode === 'light' ? 'dark_mode' : 'light_mode'" :size="16" />
    </button>
  </div>
</template>
