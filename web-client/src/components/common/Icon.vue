<script setup lang="ts">
import { computed } from 'vue'
import { Icon } from '@iconify/vue'

interface Props {
  icon: string
  size?: string | number
  color?: string
}

const props = withDefaults(defineProps<Props>(), {
  size: 24,
  color: 'currentColor'
})

// 图标映射表 - 本地化图标
const iconMap: Record<string, string> = {
  // 导航图标
  'home': 'mdi:home',
  'smart_toy': 'mdi:robot',
  'assessment': 'mdi:chart-timeline-variant',
  'swap_horiz': 'mdi:swap-horizontal',
  'inventory': 'mdi:package-variant',
  'settings': 'mdi:cog',
  
  // 操作图标
  'refresh': 'mdi:refresh',
  'filter_list': 'mdi:filter',
  'add_circle': 'mdi:plus-circle',
  'analytics': 'mdi:chart-areaspline',
  'search': 'mdi:magnify',
  'notification': 'mdi:bell',
  
  // 状态图标
  'arrow_up': 'mdi:arrow-up',
  'arrow_down': 'mdi:arrow-down',
  'check': 'mdi:check',
  'close': 'mdi:close'
}

// 获取实际的图标名称
const resolvedIcon = computed(() => {
  return iconMap[props.icon] || props.icon
})
</script>

<template>
  <Icon 
    :icon="resolvedIcon" 
    :width="size" 
    :height="size" 
    :style="{ color: color }"
  />
</template>