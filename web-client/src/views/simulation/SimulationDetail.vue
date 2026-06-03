<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Icon from '@/components/common/Icon.vue'
import {
  getSimulation,
  getHoldings,
  getTrades,
  pauseSimulation as pauseSimAPI,
  resumeSimulation as resumeSimAPI,
  stopSimulation as stopSimAPI,
} from '@/api/simulation'
import type { SimulationItem, HoldingItem, TradeRecord } from '@/api/simulation'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const error = ref('')
const operating = ref(false)

const simulation = ref<SimulationItem>({
  id: 0,
  name: '',
  strategy_name: '',
  strategyName: '',
  status: '',
  status_text: '',
  statusText: '',
  initial_capital: 0,
  initialCapital: 0,
  current_capital: 0,
  currentCapital: 0,
  total_return: 0,
  totalReturn: 0,
  today_return: 0,
  todayReturn: 0,
  today_pl: 0,
  todayPL: 0,
  holdings_value: 0,
  holdingsValue: 0,
  holdings_count: 0,
  holdingsCount: 0,
  win_rate: 0,
  winRate: 0,
  trade_count: 0,
  tradeCount: 0,
  start_date: '',
  startDate: '',
  last_trade_time: '',
  lastTradeTime: '',
  available_capital: 0,
  availableCapital: 0,
  frozen_capital: 0,
  frozenCapital: 0,
})

const holdings = ref<HoldingItem[]>([])
const trades = ref<TradeRecord[]>([])

async function loadDetail() {
  const id = Number(route.params.id)
  if (!id) {
    error.value = '无效的模拟ID'
    loading.value = false
    return
  }

  loading.value = true
  error.value = ''
  try {
    const [simData, holdingsData, tradesData] = await Promise.all([
      getSimulation(id),
      getHoldings(id),
      getTrades(id, { page: 1, page_size: 50 }),
    ])
    simulation.value = simData
    holdings.value = holdingsData
    trades.value = tradesData.items
  } catch (e: any) {
    error.value = e.message || '加载详情失败'
    console.error('加载模拟详情失败:', e)
  } finally {
    loading.value = false
  }
}

const formatMoney = (value: number) => {
  return (value || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const getReturnColor = (value: number) => {
  return (value || 0) > 0 ? 'text-up' : (value || 0) < 0 ? 'text-down' : 'text-textSub'
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'running':
      return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
    case 'paused':
      return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
    case 'completed':
      return 'bg-gray-100 text-textSub dark:bg-gray-800'
    default:
      return 'bg-gray-100 text-textSub'
  }
}

const goBack = () => {
  router.push('/simulation')
}

const handlePause = async () => {
  operating.value = true
  try {
    await pauseSimAPI(simulation.value.id)
    simulation.value.status = 'paused'
    simulation.value.statusText = '已暂停'
  } catch (e: any) {
    console.error('暂停失败:', e)
    error.value = e.message || '暂停失败'
  } finally {
    operating.value = false
  }
}

const handleResume = async () => {
  operating.value = true
  try {
    await resumeSimAPI(simulation.value.id)
    simulation.value.status = 'running'
    simulation.value.statusText = '运行中'
  } catch (e: any) {
    console.error('恢复失败:', e)
    error.value = e.message || '恢复失败'
  } finally {
    operating.value = false
  }
}

const handleStop = async () => {
  operating.value = true
  try {
    await stopSimAPI(simulation.value.id)
    simulation.value.status = 'completed'
    simulation.value.statusText = '已完成'
  } catch (e: any) {
    console.error('停止失败:', e)
    error.value = e.message || '停止失败'
  } finally {
    operating.value = false
  }
}

onMounted(() => {
  loadDetail()
})
</script>

<template>
  <div class="h-full flex flex-col bg-bgMain overflow-hidden">
    <!-- 页面标题栏 -->
    <div class="px-6 py-3 border-b border-border bg-card shrink-0">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-4">
          <button 
            class="flex items-center gap-1 text-textSub hover:text-primary transition-colors"
            @click="goBack"
          >
            <Icon icon="mdi:arrow-left" :size="18" />
            <span class="text-sm">返回</span>
          </button>
          <div class="h-6 w-px bg-border"></div>
          <div>
            <div class="flex items-center gap-2">
              <h1 class="text-lg font-bold text-textMain">{{ simulation.name }}</h1>
              <span 
                :class="[
                  'inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold',
                  getStatusColor(simulation.status)
                ]"
              >
                {{ simulation.statusText }}
              </span>
            </div>
            <p class="text-xs text-textMute mt-0.5">策略: {{ simulation.strategyName }}</p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button 
            v-if="simulation.status === 'running'"
            class="px-3 py-1.5 border border-yellow-500 text-yellow-600 rounded text-xs font-semibold hover:bg-yellow-50 transition-colors disabled:opacity-50"
            @click="handlePause"
            :disabled="operating"
          >
            {{ operating ? '操作中...' : '暂停模拟' }}
          </button>
          <button 
            v-if="simulation.status === 'paused'"
            class="px-3 py-1.5 bg-green-500 text-white rounded text-xs font-semibold hover:bg-green-600 transition-colors disabled:opacity-50"
            @click="handleResume"
            :disabled="operating"
          >
            {{ operating ? '操作中...' : '恢复模拟' }}
          </button>
          <button 
            class="px-3 py-1.5 bg-red-500 text-white rounded text-xs font-semibold hover:bg-red-600 transition-colors disabled:opacity-50"
            @click="handleStop"
            :disabled="operating"
          >
            结束模拟
          </button>
        </div>
      </div>
    </div>

    <!-- 页面内容 (可滚动) -->
    <div class="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-4">
      <!-- 错误提示 -->
      <div v-if="error" class="p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
        {{ error }}
        <button class="ml-2 underline" @click="loadDetail">重试</button>
      </div>

      <!-- 加载中 -->
      <div v-if="loading" class="flex items-center justify-center py-20">
        <Icon icon="mdi:loading" :size="32" class="text-primary animate-spin" />
        <span class="ml-2 text-textSub">加载中...</span>
      </div>

      <template v-if="!loading">
      <!-- 上：持仓股票列表 (固定高度，可滚动) -->
      <div class="bg-card rounded-xl border border-border shadow-sm overflow-hidden flex flex-col" style="max-height: 280px;">
        <div class="px-6 py-3 border-b border-border flex items-center justify-between shrink-0">
          <div class="flex items-center gap-3">
            <h2 class="font-bold text-sm text-textMain">持仓股票</h2>
            <span class="text-xs text-textMute">共 {{ holdings.length }} 只</span>
          </div>
          <div class="flex items-center gap-4 text-xs text-textMute">
            <span>持仓市值: <span class="font-numeric font-semibold text-textMain">{{ formatMoney(simulation.holdingsValue) }}</span></span>
          </div>
        </div>
        <div class="overflow-y-auto flex-1">
          <table class="w-full">
          <thead>
            <tr class="bg-gray-50/50 dark:bg-gray-800/50 text-textMute text-[11px] uppercase tracking-wider">
              <th class="px-6 py-3 font-semibold text-left">股票名称</th>
              <th class="px-6 py-3 font-semibold text-left">代码</th>
              <th class="px-6 py-3 font-semibold text-right">持仓数量</th>
              <th class="px-6 py-3 font-semibold text-right">成本价</th>
              <th class="px-6 py-3 font-semibold text-right">现价</th>
              <th class="px-6 py-3 font-semibold text-right">市值</th>
              <th class="px-6 py-3 font-semibold text-right">持仓盈亏</th>
              <th class="px-6 py-3 font-semibold text-right">盈亏率</th>
              <th class="px-6 py-3 font-semibold text-right">权重</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-border">
            <tr 
              v-for="holding in holdings"
              :key="holding.id"
              class="hover:bg-primary/5 transition-colors"
            >
              <td class="px-6 py-3.5">
                <span class="font-bold text-sm text-textMain">{{ holding.name }}</span>
              </td>
              <td class="px-6 py-3.5">
                <span class="font-numeric text-xs text-textMute">{{ holding.code }}</span>
              </td>
              <td class="px-6 py-3.5 text-right font-numeric text-sm text-textSub">
                {{ holding.quantity }}
              </td>
              <td class="px-6 py-3.5 text-right font-numeric text-sm text-textSub">
                {{ holding.avgCost.toFixed(2) }}
              </td>
              <td class="px-6 py-3.5 text-right font-numeric text-sm font-medium text-textMain">
                {{ holding.currentPrice.toFixed(2) }}
              </td>
              <td class="px-6 py-3.5 text-right font-numeric text-sm font-medium text-textMain">
                {{ formatMoney(holding.marketValue) }}
              </td>
              <td class="px-6 py-3.5 text-right">
                <span class="font-numeric text-sm font-bold" :class="getReturnColor(holding.pl)">
                  {{ holding.pl > 0 ? '+' : '' }}{{ formatMoney(holding.pl) }}
                </span>
              </td>
              <td class="px-6 py-3.5 text-right">
                <span class="font-numeric text-sm font-bold" :class="getReturnColor(holding.plPercent)">
                  {{ holding.plPercent > 0 ? '+' : '' }}{{ holding.plPercent.toFixed(2) }}%
                </span>
              </td>
              <td class="px-6 py-3.5 text-right">
                <span class="font-numeric text-sm text-textSub">{{ holding.weight.toFixed(1) }}%</span>
              </td>
            </tr>
          </tbody>
        </table>
        </div>
        
        <!-- 空状态 -->
        <div v-if="holdings.length === 0" class="py-12 text-center">
          <Icon icon="mdi:package-variant" :size="48" class="mx-auto text-textMute mb-3" />
          <p class="text-textSub text-sm">暂无持仓</p>
        </div>
      </div>

      <!-- 下：账户信息 + 交易记录 -->
      <div class="grid grid-cols-12 gap-6">
        <!-- 左侧：账户信息 -->
        <div class="col-span-4">
          <div class="bg-card rounded-xl border border-border shadow-sm overflow-hidden">
            <div class="px-6 py-4 border-b border-border">
              <h2 class="font-bold text-sm text-textMain">账户信息</h2>
            </div>
            <div class="p-6 space-y-4">
              <!-- 总资产 -->
              <div class="p-4 bg-primary/5 rounded-lg">
                <p class="text-xs text-textMute mb-1">总资产 (CNY)</p>
                <p class="text-2xl font-bold font-numeric text-textMain">
                  {{ formatMoney(simulation.currentCapital) }}
                </p>
                <div class="flex items-center gap-2 mt-1">
                  <span class="text-xs font-semibold" :class="getReturnColor(simulation.totalReturn)">
                    {{ simulation.totalReturn > 0 ? '+' : '' }}{{ simulation.totalReturn.toFixed(2) }}%
                  </span>
                  <span class="text-xs text-textMute">累计收益</span>
                </div>
              </div>

              <!-- 账户明细 -->
              <div class="space-y-3">
                <div class="flex justify-between items-center">
                  <span class="text-xs text-textMute">初始资金</span>
                  <span class="font-numeric text-sm font-medium text-textSub">
                    {{ formatMoney(simulation.initialCapital) }}
                  </span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-xs text-textMute">可用资金</span>
                  <span class="font-numeric text-sm font-medium text-textMain">
                    {{ formatMoney(simulation.availableCapital) }}
                  </span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-xs text-textMute">持仓市值</span>
                  <span class="font-numeric text-sm font-medium text-textMain">
                    {{ formatMoney(simulation.holdingsValue) }}
                  </span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-xs text-textMute">冻结资金</span>
                  <span class="font-numeric text-sm font-medium text-textSub">
                    {{ formatMoney(simulation.frozenCapital) }}
                  </span>
                </div>
              </div>

              <div class="border-t border-border pt-4 space-y-3">
                <div class="flex justify-between items-center">
                  <span class="text-xs text-textMute">今日盈亏</span>
                  <span class="font-numeric text-sm font-bold" :class="getReturnColor(simulation.todayPL)">
                    {{ simulation.todayPL > 0 ? '+' : '' }}{{ formatMoney(simulation.todayPL) }}
                  </span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-xs text-textMute">今日收益率</span>
                  <span class="font-numeric text-sm font-bold" :class="getReturnColor(simulation.todayReturn)">
                    {{ simulation.todayReturn > 0 ? '+' : '' }}{{ simulation.todayReturn.toFixed(2) }}%
                  </span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-xs text-textMute">胜率</span>
                  <span class="font-numeric text-sm font-medium text-textMain">
                    {{ simulation.winRate.toFixed(1) }}%
                  </span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-xs text-textMute">交易次数</span>
                  <span class="font-numeric text-sm font-medium text-textSub">
                    {{ simulation.tradeCount }}
                  </span>
                </div>
              </div>

              <div class="border-t border-border pt-4">
                <div class="flex justify-between items-center">
                  <span class="text-xs text-textMute">开始日期</span>
                  <span class="text-sm text-textSub">
                    {{ simulation.startDate }}
                  </span>
                </div>
                <div class="flex justify-between items-center mt-2">
                  <span class="text-xs text-textMute">最后交易</span>
                  <span class="text-sm text-textSub">
                    {{ simulation.lastTradeTime }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧：交易记录 (固定高度，可滚动) -->
        <div class="col-span-8">
          <div class="bg-card rounded-xl border border-border shadow-sm overflow-hidden flex flex-col" style="max-height: 400px;">
            <div class="px-6 py-3 border-b border-border flex items-center justify-between shrink-0">
              <div class="flex items-center gap-3">
                <h2 class="font-bold text-sm text-textMain">交易记录</h2>
                <span class="text-xs text-textMute">最近 {{ trades.length }} 笔</span>
              </div>
              <button class="text-xs text-primary hover:underline font-semibold">查看全部</button>
            </div>
            <div class="overflow-y-auto flex-1">
              <table class="w-full">
              <thead>
                <tr class="bg-gray-50/50 dark:bg-gray-800/50 text-textMute text-[11px] uppercase tracking-wider">
                  <th class="px-6 py-3 font-semibold text-left">时间</th>
                  <th class="px-6 py-3 font-semibold text-left">股票</th>
                  <th class="px-6 py-3 font-semibold text-center">方向</th>
                  <th class="px-6 py-3 font-semibold text-right">价格</th>
                  <th class="px-6 py-3 font-semibold text-right">数量</th>
                  <th class="px-6 py-3 font-semibold text-right">金额</th>
                  <th class="px-6 py-3 font-semibold text-center">状态</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-border">
                <tr 
                  v-for="trade in trades"
                  :key="trade.id"
                  class="hover:bg-primary/5 transition-colors"
                >
                  <td class="px-6 py-3.5">
                    <span class="font-numeric text-xs text-textMute">{{ trade.time }}</span>
                  </td>
                  <td class="px-6 py-3.5">
                    <div class="flex flex-col">
                      <span class="font-bold text-sm text-textMain">{{ trade.stockName }}</span>
                      <span class="font-numeric text-[10px] text-textMute">{{ trade.stockCode }}</span>
                    </div>
                  </td>
                  <td class="px-6 py-3.5 text-center">
                    <span 
                      :class="[
                        'inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold',
                        trade.direction === 'buy' 
                          ? 'bg-up/10 text-up' 
                          : 'bg-down/10 text-down'
                      ]"
                    >
                      {{ trade.directionText }}
                    </span>
                  </td>
                  <td class="px-6 py-3.5 text-right font-numeric text-sm text-textSub">
                    {{ trade.price.toFixed(2) }}
                  </td>
                  <td class="px-6 py-3.5 text-right font-numeric text-sm text-textSub">
                    {{ trade.quantity }}
                  </td>
                  <td class="px-6 py-3.5 text-right font-numeric text-sm font-medium text-textMain">
                    {{ formatMoney(trade.amount) }}
                  </td>
                  <td class="px-6 py-3.5 text-center">
                    <span class="text-[10px] font-semibold text-green-600">{{ trade.status }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
            </div>

            <!-- 空状态 -->
            <div v-if="trades.length === 0" class="py-12 text-center">
              <Icon icon="mdi:format-list-bulleted" :size="48" class="mx-auto text-textMute mb-3" />
              <p class="text-textSub text-sm">暂无交易记录</p>
            </div>
          </div>
        </div>
      </div>
    </template>
    </div>
  </div>
</template>
