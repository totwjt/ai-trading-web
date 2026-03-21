<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Icon from '@/components/common/Icon.vue'

const route = useRoute()
const router = useRouter()

// 模拟详情数据
const simulation = ref({
  id: 1,
  name: '趋势先行A模拟',
  strategyName: '趋势先行A (大盘股)',
  status: 'running',
  statusText: '运行中',
  initialCapital: 1000000,
  currentCapital: 1124800,
  totalReturn: 12.48,
  todayReturn: 1.24,
  todayPL: 13840,
  holdingsValue: 824500,
  holdingsCount: 3,
  winRate: 68.5,
  tradeCount: 142,
  startDate: '2024-01-15',
  lastTradeTime: '10:32:15'
})

// 返回列表
const goBack = () => {
  router.push('/simulation')
}

onMounted(() => {
  // 后续根据 route.params.id 获取详情数据
  const id = route.params.id
  console.log('Simulation Detail ID:', id)
})
</script>

<template>
  <div class="min-h-screen bg-bgMain">
    <!-- 页面内容待设计实现 -->
    <div class="flex items-center justify-center h-[calc(100vh-120px)]">
      <div class="text-center">
        <Icon icon="mdi:chart-timeline-variant" :size="64" class="mx-auto text-primary/30 mb-4" />
        <h2 class="text-xl font-bold text-textMain mb-2">模拟交易详情页</h2>
        <p class="text-sm text-textMute mb-4">页面设计待后续实现...</p>
        <button 
          class="bg-primary text-white px-4 py-2 rounded text-sm font-semibold hover:opacity-90 flex items-center gap-2 mx-auto transition-opacity"
          @click="goBack"
        >
          <Icon icon="mdi:arrow-left" :size="16" />
          返回列表
        </button>
      </div>
    </div>
  </div>
</template>
