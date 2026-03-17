<script setup lang="ts">
import { ref } from 'vue'

// 模拟策略数据
const strategies = ref([
  {
    id: 1,
    name: '中证500增强A1',
    type: '指数增强',
    status: '运行中',
    returns: '+12.4%',
    winRate: '68.5%',
    maxDrawdown: '4.2%',
    sharpe: 1.85
  },
  {
    id: 2,
    name: '均线回归Alpha',
    type: '量化多因子',
    status: '暂停',
    returns: '-2.1%',
    winRate: '52.3%',
    maxDrawdown: '8.7%',
    sharpe: 0.92
  },
  {
    id: 3,
    name: '高频套利V2',
    type: '高频交易',
    status: '运行中',
    returns: '+4.8%',
    winRate: '81.0%',
    maxDrawdown: '1.5%',
    sharpe: 2.34
  }
])

const selectedStrategy = ref<{
  id: number
  name: string
  type: string
  status: string
  returns: string
  winRate: string
  maxDrawdown: string
  sharpe: number
} | null>(null)
</script>

<template>
  <div class="min-h-screen bg-bgMain p-6">
    <div class="max-w-6xl mx-auto">
      <!-- Header -->
      <div class="flex justify-between items-center mb-6">
        <div>
          <h1 class="text-xl font-bold text-textMain">策略回测</h1>
          <p class="text-sm text-textMute">回测历史数据，验证策略有效性</p>
        </div>
        <button class="px-4 py-2 bg-primary text-white text-sm font-bold rounded hover:bg-blue-600 transition-colors">
          新建回测
        </button>
      </div>

      <!-- Strategy List -->
      <div class="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
        <div class="px-4 py-3 border-b flex justify-between items-center">
          <h3 class="font-bold text-sm">策略列表</h3>
          <div class="flex gap-2">
            <button class="px-3 py-1 text-xs text-textMute hover:text-primary">全部</button>
            <button class="px-3 py-1 text-xs text-textMute hover:text-primary">运行中</button>
            <button class="px-3 py-1 text-xs text-textMute hover:text-primary">暂停</button>
          </div>
        </div>
        
        <table class="w-full density-table">
          <thead class="bg-gray-50 text-textMute">
            <tr>
              <th class="text-left">策略名称</th>
              <th class="text-left">类型</th>
              <th class="text-center">状态</th>
              <th class="text-right">累计收益</th>
              <th class="text-right">胜率</th>
              <th class="text-right">最大回撤</th>
              <th class="text-right">Sharpe</th>
              <th class="text-right">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr 
              v-for="strategy in strategies"
              :key="strategy.id"
              class="hover:bg-gray-50 cursor-pointer"
              :class="{ 'bg-blue-50/30': selectedStrategy?.id === strategy.id }"
              @click="selectedStrategy = strategy"
            >
              <td class="font-medium">{{ strategy.name }}</td>
              <td class="text-textMute">{{ strategy.type }}</td>
              <td class="text-center">
                <span 
                  :class="[
                    'px-2 py-0.5 text-xs rounded-full',
                    strategy.status === '运行中' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                  ]"
                >
                  {{ strategy.status }}
                </span>
              </td>
              <td 
                :class="[
                  'text-right font-numeric font-bold',
                  strategy.returns.startsWith('+') ? 'text-up' : 'text-down'
                ]"
              >
                {{ strategy.returns }}
              </td>
              <td class="text-right font-numeric">{{ strategy.winRate }}</td>
              <td class="text-right font-numeric">{{ strategy.maxDrawdown }}</td>
              <td class="text-right font-numeric">{{ strategy.sharpe }}</td>
              <td class="text-right">
                <button class="text-primary hover:underline text-xs">查看</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Strategy Detail Panel -->
      <div v-if="selectedStrategy" class="mt-6 grid grid-cols-3 gap-4">
        <div class="col-span-2 bg-white rounded-lg shadow-sm border border-gray-100 p-4">
          <h3 class="font-bold text-sm mb-4">策略详情 - {{ selectedStrategy.name }}</h3>
          <div class="grid grid-cols-4 gap-4 mb-4">
            <div class="text-center">
              <p class="text-xs text-textMute">累计收益</p>
              <p class="text-lg font-bold font-numeric" :class="selectedStrategy.returns.startsWith('+') ? 'text-up' : 'text-down'">
                {{ selectedStrategy.returns }}
              </p>
            </div>
            <div class="text-center">
              <p class="text-xs text-textMute">胜率</p>
              <p class="text-lg font-bold font-numeric">{{ selectedStrategy.winRate }}</p>
            </div>
            <div class="text-center">
              <p class="text-xs text-textMute">最大回撤</p>
              <p class="text-lg font-bold font-numeric">{{ selectedStrategy.maxDrawdown }}</p>
            </div>
            <div class="text-center">
              <p class="text-xs text-textMute">Sharpe比率</p>
              <p class="text-lg font-bold font-numeric">{{ selectedStrategy.sharpe }}</p>
            </div>
          </div>
          <!-- Chart placeholder -->
          <div class="h-48 bg-gray-50 rounded flex items-center justify-center text-textMute">
            策略收益曲线图
          </div>
        </div>
        
        <div class="bg-white rounded-lg shadow-sm border border-gray-100 p-4">
          <h3 class="font-bold text-sm mb-4">操作</h3>
          <div class="space-y-2">
            <button class="w-full px-4 py-2 bg-primary text-white text-sm font-bold rounded hover:bg-blue-600 transition-colors">
              编辑策略
            </button>
            <button class="w-full px-4 py-2 border border-gray-200 text-textMain text-sm font-bold rounded hover:bg-gray-50 transition-colors">
              查看详细报告
            </button>
            <button class="w-full px-4 py-2 border border-gray-200 text-textMain text-sm font-bold rounded hover:bg-gray-50 transition-colors">
              导出数据
            </button>
            <button class="w-full px-4 py-2 border border-red-200 text-red-600 text-sm font-bold rounded hover:bg-red-50 transition-colors">
              删除策略
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>