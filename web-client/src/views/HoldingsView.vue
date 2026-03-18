<script setup lang="ts">
import { ref } from 'vue'

// 模拟持仓数据
const holdings = ref([
  {
    id: 1,
    name: '贵州茅台',
    code: '600519.SH',
    quantity: 100,
    avgCost: 1850.00,
    currentPrice: 1880.50,
    marketValue: 188050.00,
    pl: 3050.00,
    plPercent: 1.65,
    sector: '白酒'
  },
  {
    id: 2,
    name: '宁德时代',
    code: '300750.SZ',
    quantity: 500,
    avgCost: 220.00,
    currentPrice: 215.50,
    marketValue: 107750.00,
    pl: -2250.00,
    plPercent: -2.05,
    sector: '新能源'
  },
  {
    id: 3,
    name: '招商银行',
    code: '600036.SH',
    quantity: 2000,
    avgCost: 35.50,
    currentPrice: 36.80,
    marketValue: 73600.00,
    pl: 2600.00,
    plPercent: 3.66,
    sector: '银行'
  },
  {
    id: 4,
    name: '美的集团',
    code: '000333.SZ',
    quantity: 300,
    avgCost: 55.00,
    currentPrice: 58.20,
    marketValue: 17460.00,
    pl: 960.00,
    plPercent: 5.82,
    sector: '家电'
  }
])

const totalStats = ref({
  totalMarketValue: 386860.00,
  totalCost: 378000.00,
  totalPL: 8860.00,
  totalPLPercent: 2.34
})

const selectedHolding = ref<{
  id: number
  name: string
  code: string
  quantity: number
  avgCost: number
  currentPrice: number
  marketValue: number
  pl: number
  plPercent: number
  sector: string
} | null>(null)
</script>

<template>
  <div class="min-h-screen bg-bgMain p-6">
    <div class="max-w-6xl mx-auto">
      <!-- Header -->
      <div class="flex justify-between items-center mb-6">
        <div>
          <h1 class="text-xl font-bold text-textMain">我的持仓</h1>
          <p class="text-sm text-textMute">查看和管理您的持仓股票</p>
        </div>
        <div class="flex gap-2">
          <button class="px-4 py-2 border border-border text-textMain text-sm font-bold rounded hover:bg-primary/5 transition-colors">
            导出持仓
          </button>
        </div>
      </div>

      <!-- Portfolio Summary -->
      <div class="grid grid-cols-4 gap-4 mb-6">
        <div class="bg-card p-4 rounded-lg shadow-sm border border-border">
          <p class="text-xs text-textMute mb-1">持仓市值</p>
          <p class="text-xl font-bold font-numeric text-textMain">{{ totalStats.totalMarketValue.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</p>
        </div>
        <div class="bg-card p-4 rounded-lg shadow-sm border border-border">
          <p class="text-xs text-textMute mb-1">总成本</p>
          <p class="text-xl font-bold font-numeric text-textMain">{{ totalStats.totalCost.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</p>
        </div>
        <div class="bg-card p-4 rounded-lg shadow-sm border border-border">
          <p class="text-xs text-textMute mb-1">总盈亏</p>
          <div class="flex items-baseline space-x-2">
            <p class="text-xl font-bold font-numeric" :class="totalStats.totalPL > 0 ? 'text-up' : 'text-down'">
              {{ totalStats.totalPL > 0 ? '+' : '' }}{{ totalStats.totalPL.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}
            </p>
          </div>
        </div>
        <div class="bg-card p-4 rounded-lg shadow-sm border border-border">
          <p class="text-xs text-textMute mb-1">收益率</p>
          <p class="text-xl font-bold font-numeric" :class="totalStats.totalPLPercent > 0 ? 'text-up' : 'text-down'">
            {{ totalStats.totalPLPercent > 0 ? '+' : '' }}{{ totalStats.totalPLPercent }}%
          </p>
        </div>
      </div>

      <!-- Holdings List -->
      <div class="bg-card rounded-lg shadow-sm border border-border overflow-hidden">
        <div class="px-4 py-3 border-b border-border flex justify-between items-center">
          <h3 class="font-bold text-sm text-textMain">持仓列表</h3>
          <div class="flex gap-2">
            <button class="px-3 py-1 text-xs text-textMute hover:text-primary">全部</button>
            <button class="px-3 py-1 text-xs text-textMute hover:text-primary">A股</button>
            <button class="px-3 py-1 text-xs text-textMute hover:text-primary">港股</button>
            <button class="px-3 py-1 text-xs text-textMute hover:text-primary">美股</button>
          </div>
        </div>
        
        <table class="w-full density-table">
          <thead class="bg-gray-50 dark:bg-gray-800 text-textMute">
            <tr>
              <th class="text-left">股票名称</th>
              <th class="text-left">代码</th>
              <th class="text-left">板块</th>
              <th class="text-right">持仓</th>
              <th class="text-right">成本价</th>
              <th class="text-right">现价</th>
              <th class="text-right">市值</th>
              <th class="text-right">盈亏</th>
              <th class="text-right">收益率</th>
              <th class="text-right">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr 
              v-for="holding in holdings"
              :key="holding.id"
              class="hover:bg-primary/5 cursor-pointer"
              :class="{ 'bg-primary/5': selectedHolding?.id === holding.id }"
              @click="selectedHolding = holding"
            >
              <td class="font-medium text-textMain">{{ holding.name }}</td>
              <td class="text-textMute">{{ holding.code }}</td>
              <td>
                <span class="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 text-textSub text-[11px] rounded">
                  {{ holding.sector }}
                </span>
              </td>
              <td class="text-right font-numeric text-textSub">{{ holding.quantity }}</td>
              <td class="text-right font-numeric text-textSub">{{ holding.avgCost.toFixed(2) }}</td>
              <td class="text-right font-numeric text-textSub">{{ holding.currentPrice.toFixed(2) }}</td>
              <td class="text-right font-numeric text-textSub">{{ holding.marketValue.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</td>
              <td 
                :class="[
                  'text-right font-numeric font-bold',
                  holding.pl > 0 ? 'text-up' : 'text-down'
                ]"
              >
                {{ holding.pl > 0 ? '+' : '' }}{{ holding.pl.toFixed(2) }}
              </td>
              <td 
                :class="[
                  'text-right font-numeric font-bold',
                  holding.plPercent > 0 ? 'text-up' : 'text-down'
                ]"
              >
                {{ holding.plPercent > 0 ? '+' : '' }}{{ holding.plPercent }}%
              </td>
              <td class="text-right">
                <button class="text-primary hover:underline text-xs mr-2">买</button>
                <button class="text-down hover:underline text-xs">卖</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Holding Detail Panel -->
      <div v-if="selectedHolding" class="mt-6 grid grid-cols-3 gap-4">
        <div class="col-span-2 bg-card rounded-lg shadow-sm border border-border p-4">
          <h3 class="font-bold text-sm text-textMain mb-4">持仓详情 - {{ selectedHolding.name }}</h3>
          <div class="grid grid-cols-4 gap-4 mb-4">
            <div class="text-center">
              <p class="text-xs text-textMute">持仓数量</p>
              <p class="text-lg font-bold font-numeric text-textMain">{{ selectedHolding.quantity }}</p>
            </div>
            <div class="text-center">
              <p class="text-xs text-textMute">成本价</p>
              <p class="text-lg font-bold font-numeric text-textMain">{{ selectedHolding.avgCost.toFixed(2) }}</p>
            </div>
            <div class="text-center">
              <p class="text-xs text-textMute">现价</p>
              <p class="text-lg font-bold font-numeric text-textMain">{{ selectedHolding.currentPrice.toFixed(2) }}</p>
            </div>
            <div class="text-center">
              <p class="text-xs text-textMute">盈亏</p>
              <p 
                class="text-lg font-bold font-numeric"
                :class="selectedHolding.pl > 0 ? 'text-up' : 'text-down'"
              >
                {{ selectedHolding.pl > 0 ? '+' : '' }}{{ selectedHolding.pl.toFixed(2) }}
              </p>
            </div>
          </div>
          <!-- Chart placeholder -->
          <div class="h-48 bg-gray-50 dark:bg-gray-800 rounded flex items-center justify-center text-textMute">
            持仓收益曲线图
          </div>
        </div>
        
        <div class="bg-card rounded-lg shadow-sm border border-border p-4">
          <h3 class="font-bold text-sm text-textMain mb-4">快速操作</h3>
          <div class="space-y-2">
            <button class="w-full px-4 py-2 bg-up text-white text-sm font-bold rounded hover:opacity-90 transition-opacity">
              买入
            </button>
            <button class="w-full px-4 py-2 bg-down text-white text-sm font-bold rounded hover:opacity-90 transition-opacity">
              卖出
            </button>
            <button class="w-full px-4 py-2 border border-border text-textMain text-sm font-bold rounded hover:bg-primary/5 transition-colors">
              查看详情
            </button>
            <button class="w-full px-4 py-2 border border-border text-textMain text-sm font-bold rounded hover:bg-primary/5 transition-colors">
              加入自选
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>