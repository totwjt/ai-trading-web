<script setup lang="ts">
import { ref } from 'vue'

// 模拟推荐数据
const recommendations = ref([
  {
    id: 1,
    name: '科大讯飞',
    code: '002230.SZ',
    score: 98,
    reason: 'AI语音技术领先，教育业务增长强劲',
    sectors: ['人工智能', '教育信息化']
  },
  {
    id: 2,
    name: '中微公司',
    code: '688012.SH',
    score: 96,
    reason: '半导体设备国产化龙头，订单饱满',
    sectors: ['半导体设备', '国产替代']
  },
  {
    id: 3,
    name: '贵州茅台',
    code: '600519.SH',
    score: 91,
    reason: '高端白酒龙头，抗周期性强',
    sectors: ['白酒', '核心资产']
  },
  {
    id: 4,
    name: '宁德时代',
    code: '300750.SZ',
    score: 93,
    reason: '动力电池全球龙头，技术领先',
    sectors: ['新能源', '锂电池']
  }
])

const selectedStock = ref<{
  id: number
  name: string
  code: string
  score: number
  reason: string
  sectors: string[]
} | null>(null)
</script>

<template>
  <div class="min-h-screen bg-bgMain p-6">
    <div class="max-w-6xl mx-auto">
      <!-- Header -->
      <div class="flex justify-between items-center mb-6">
        <div>
          <h1 class="text-xl font-bold text-textMain">智能选股</h1>
          <p class="text-sm text-textMute">AI深度学习模型精选优质股票</p>
        </div>
        <div class="flex gap-2">
          <button class="px-4 py-2 bg-primary text-white text-sm font-bold rounded hover:bg-blue-600 transition-colors">
            刷新推荐
          </button>
          <button class="px-4 py-2 border border-gray-200 text-textMain text-sm font-bold rounded hover:bg-gray-50 transition-colors">
            筛选条件
          </button>
        </div>
      </div>

      <!-- Filter Tabs -->
      <div class="flex gap-2 mb-4">
        <button class="px-4 py-1.5 text-xs font-bold bg-primary text-white rounded">全部</button>
        <button class="px-4 py-1.5 text-xs font-bold bg-white border border-gray-200 text-textSub hover:border-primary hover:text-primary rounded transition-all">高评分</button>
        <button class="px-4 py-1.5 text-xs font-bold bg-white border border-gray-200 text-textSub hover:border-primary hover:text-primary rounded transition-all">低估值</button>
        <button class="px-4 py-1.5 text-xs font-bold bg-white border border-gray-200 text-textSub hover:border-primary hover:text-primary rounded transition-all">高成长</button>
        <button class="px-4 py-1.5 text-xs font-bold bg-white border border-gray-200 text-textSub hover:border-primary hover:text-primary rounded transition-all">技术面</button>
      </div>

      <!-- Stock List -->
      <div class="grid grid-cols-2 gap-4">
        <div 
          v-for="stock in recommendations"
          :key="stock.id"
          class="bg-white rounded-lg shadow-sm border border-gray-100 p-4 cursor-pointer hover:border-primary/50 transition-colors"
          :class="{ 'border-primary bg-blue-50/30': selectedStock?.id === stock.id }"
          @click="selectedStock = stock"
        >
          <div class="flex justify-between items-start mb-3">
            <div>
              <h3 class="font-bold text-textMain">{{ stock.name }}</h3>
              <p class="text-xs text-textMute">{{ stock.code }}</p>
            </div>
            <div class="text-right">
              <p class="text-lg font-bold font-numeric text-up">{{ stock.score }}</p>
              <p class="text-xs text-textMute">AI评分</p>
            </div>
          </div>
          <p class="text-xs text-textSub mb-3">{{ stock.reason }}</p>
          <div class="flex gap-2">
            <span 
              v-for="sector in stock.sectors"
              :key="sector"
              class="px-2 py-0.5 bg-primary/10 text-primary text-[11px] font-bold rounded"
            >
              {{ sector }}
            </span>
          </div>
        </div>
      </div>

      <!-- Stock Detail Panel -->
      <div v-if="selectedStock" class="mt-6 bg-white rounded-lg shadow-sm border border-gray-100 p-4">
        <div class="flex justify-between items-center mb-4">
          <div>
            <h3 class="font-bold text-lg">{{ selectedStock.name }}</h3>
            <p class="text-sm text-textMute">{{ selectedStock.code }}</p>
          </div>
          <button class="px-4 py-2 bg-primary text-white text-sm font-bold rounded hover:bg-blue-600 transition-colors">
            加入自选
          </button>
        </div>
        
        <!-- Chart placeholder -->
        <div class="h-48 bg-gray-50 rounded flex items-center justify-center text-textMute mb-4">
          股票K线图
        </div>
        
        <div class="grid grid-cols-4 gap-4 text-center">
          <div>
            <p class="text-xs text-textMute">AI评分</p>
            <p class="text-lg font-bold font-numeric text-up">{{ selectedStock.score }}</p>
          </div>
          <div>
            <p class="text-xs text-textMute">建议仓位</p>
            <p class="text-lg font-bold font-numeric">15%</p>
          </div>
          <div>
            <p class="text-xs text-textMute">目标涨幅</p>
            <p class="text-lg font-bold font-numeric text-up">+8.5%</p>
          </div>
          <div>
            <p class="text-xs text-textMute">止损位</p>
            <p class="text-lg font-bold font-numeric text-down">-5.0%</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>