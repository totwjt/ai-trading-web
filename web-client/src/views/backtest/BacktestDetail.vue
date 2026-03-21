<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getBacktestDetail, getBacktestTrades, getBacktestLogs, getEquityCurve, getPerformance, type BacktestDetail, type TradeItem, type LogItem, type EquityPoint } from '@/api/backtest'
import EquityChart from '@/components/backtest/EquityChart.vue'
import Icon from '@/components/common/Icon.vue'

const route = useRoute()
const router = useRouter()

const backtestId = computed(() => Number(route.params.id))

const detail = ref<BacktestDetail | null>(null)
const trades = ref<TradeItem[]>([])
const logs = ref<LogItem[]>([])
const equityCurve = ref<EquityPoint[]>([])
const performance = ref<any>(null)

const loading = ref(true)
const chartFrequency = ref('1d')

async function fetchData() {
  loading.value = true
  try {
    const [detailData, tradesData, logsData, equityData, perfData] = await Promise.all([
      getBacktestDetail(backtestId.value),
      getBacktestTrades(backtestId.value),
      getBacktestLogs(backtestId.value),
      getEquityCurve(backtestId.value, chartFrequency.value),
      getPerformance(backtestId.value)
    ])
    
    detail.value = detailData
    trades.value = tradesData.items
    logs.value = logsData.logs
    equityCurve.value = equityData.data_points
    performance.value = perfData
  } catch (error) {
    console.error('获取数据失败:', error)
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push('/backtest')
}

function editStrategy() {
  if (detail.value?.strategy_id) {
    router.push(`/backtest/edit/${detail.value.strategy_id}`)
  }
}

function formatNumber(value: number | undefined, decimals: number = 2): string {
  if (value === undefined || value === null) return '-'
  return value.toLocaleString('zh-CN', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
}

function formatReturn(value: number | undefined): string {
  if (value === undefined || value === null) return '-'
  return (value >= 0 ? '+' : '') + value.toFixed(2) + '%'
}

function getReturnClass(value: number | undefined): string {
  if (value === undefined || value === null) return 'text-textSub'
  return value >= 0 ? 'text-up' : 'text-down'
}

function changeFrequency(freq: string) {
  chartFrequency.value = freq
  getEquityCurve(backtestId.value, freq).then(res => {
    equityCurve.value = res.data_points
  })
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="flex-1 bg-white flex flex-col overflow-hidden min-h-0 h-full">
    <header class="flex items-center justify-between px-6 h-14 border-b border-slate-200 bg-white shrink-0">
      <div class="flex items-center">
        <button
          class="flex items-center gap-1 mr-6 text-sm text-slate-600 hover:text-primary transition-colors"
          @click="goBack"
        >
          <Icon icon="mdi:arrow-left" :size="20" />
          返回
        </button>
        <div class="h-6 w-px bg-slate-200 mr-6"></div>
        <span class="text-sm font-medium text-slate-600">
          策略: {{ detail?.strategy_name || '加载中...' }}
        </span>
      </div>
      
      <div class="flex items-center gap-2">
        <button
          class="p-1.5 hover:bg-slate-50 text-slate-400 rounded transition-colors"
          title="刷新"
          @click="fetchData"
        >
          <Icon icon="mdi:refresh" :size="20" />
        </button>
        <button
          class="bg-primary text-white px-3 py-1.5 rounded text-xs font-bold flex items-center gap-1 hover:bg-blue-700"
          @click="fetchData"
        >
          <Icon icon="mdi:play" :size="16" />
          重新运行
        </button>
      </div>
    </header>

    <main class="flex-1 overflow-auto p-6">
      <div v-if="loading" class="flex items-center justify-center h-64">
        <span class="text-textMute">加载中...</span>
      </div>
      
      <div v-else class="space-y-4">
        <section class="grid grid-cols-1 md:grid-cols-4 gap-4 border border-slate-200 rounded p-4 bg-white shadow-sm">
          <div class="border-r border-slate-100 last:border-0">
            <p class="text-[10px] text-slate-400 uppercase font-bold tracking-wider mb-1">回测策略名称</p>
            <div class="flex items-center gap-2">
              <Icon icon="mdi:code-braces" :size="20" class="text-primary" />
              <h1 class="text-sm font-bold truncate">{{ detail?.strategy_name || '-' }}</h1>
            </div>
          </div>
          <div class="border-r border-slate-100 last:border-0 px-2">
            <p class="text-[10px] text-slate-400 uppercase font-bold tracking-wider mb-1">测试时间周期</p>
            <p class="text-sm font-mono font-medium">
              {{ detail?.params.start_date }} ~ {{ detail?.params.end_date }}
            </p>
          </div>
          <div class="border-r border-slate-100 last:border-0 px-2">
            <p class="text-[10px] text-slate-400 uppercase font-bold tracking-wider mb-1">初始资金 / 期末权益</p>
            <div class="flex items-baseline gap-2">
              <span class="text-sm font-mono">{{ formatNumber(detail?.params.initial_capital) }}</span>
              <span class="text-slate-300 text-xs">→</span>
              <span class="text-sm font-mono font-bold text-up">{{ formatNumber(detail?.results.final_equity) }}</span>
            </div>
          </div>
          <div class="px-2">
            <p class="text-[10px] text-slate-400 uppercase font-bold tracking-wider mb-1">总收益率</p>
            <div class="flex items-center gap-2">
              <span class="text-xl font-bold" :class="getReturnClass(detail?.results.total_return)">
                {{ formatReturn(detail?.results.total_return) }}
              </span>
              <span
                v-if="(detail?.results.total_return || 0) > (detail?.results.benchmark_return || 0)"
                class="px-1.5 py-0.5 bg-green-100 text-green-700 text-[10px] font-bold rounded ring-1 ring-green-200"
              >
                跑赢基准
              </span>
            </div>
          </div>
        </section>

        <section class="border border-slate-200 rounded bg-white shadow-sm flex flex-col overflow-hidden min-h-[400px]">
          <div class="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
            <div class="flex items-center gap-4">
              <h3 class="text-sm font-bold flex items-center gap-2">
                <Icon icon="mdi:chart-line" :size="20" class="text-primary" />
                策略净值曲线 vs 沪深300基准
              </h3>
              <div class="flex items-center gap-3 text-[11px]">
                <div class="flex items-center gap-1.5">
                  <span class="w-3 h-0.5 bg-primary"></span>
                  <span class="text-slate-600 font-medium">策略组合</span>
                </div>
                <div class="flex items-center gap-1.5">
                  <span class="w-3 h-0.5 bg-slate-300"></span>
                  <span class="text-slate-400 font-medium">沪深300</span>
                </div>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <button
                v-for="freq in ['1d', '1w']"
                :key="freq"
                :class="[
                  'text-[11px] px-2 py-1 border border-slate-200 rounded hover:bg-slate-50',
                  chartFrequency === freq ? 'bg-slate-100 font-bold' : 'bg-white'
                ]"
                @click="changeFrequency(freq)"
              >
                {{ freq === '1d' ? '日线' : '周线' }}
              </button>
              <div class="w-px h-4 bg-slate-200 mx-1"></div>
              <button class="p-1 text-slate-400 hover:text-slate-600">
                <Icon icon="mdi:fullscreen" :size="20" />
              </button>
            </div>
          </div>
          <div class="flex-1 relative p-4">
            <EquityChart
              v-if="equityCurve.length > 0"
              :data="equityCurve"
              :benchmark="detail?.results.total_return ? '沪深300' : undefined"
            />
            <div v-else class="w-full h-full flex items-center justify-center text-slate-400">
              暂无数据
            </div>
          </div>
        </section>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 h-[350px]">
          <div class="border border-slate-200 rounded bg-white shadow-sm flex flex-col overflow-hidden">
            <div class="px-4 py-2 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
              <h3 class="text-[12px] font-bold text-slate-600 flex items-center gap-1.5">
                <Icon icon="mdi:list-status" :size="16" />
                交易明细
              </h3>
              <span class="text-[10px] text-slate-400 font-mono">Total: {{ trades.length }} Trades</span>
            </div>
            <div class="flex-1 overflow-auto">
              <table class="w-full text-left text-[11px] border-collapse font-mono">
                <thead class="sticky top-0 bg-white shadow-sm text-slate-400 font-bold uppercase">
                  <tr>
                    <th class="px-4 py-2 border-b border-slate-50">成交时间</th>
                    <th class="px-4 py-2 border-b border-slate-50">代码</th>
                    <th class="px-4 py-2 border-b border-slate-50">类型</th>
                    <th class="px-4 py-2 border-b border-slate-50 text-right">价格</th>
                    <th class="px-4 py-2 border-b border-slate-50 text-right">数量</th>
                    <th class="px-4 py-2 border-b border-slate-50 text-right">净盈亏</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-50">
                  <tr v-for="trade in trades" :key="trade.id" class="hover:bg-slate-50/50">
                    <td class="px-4 py-2 text-slate-500">{{ trade.time }}</td>
                    <td class="px-4 py-2 font-bold text-slate-800">{{ trade.code }}</td>
                    <td class="px-4 py-2">
                      <span :class="trade.type === 'BUY' ? 'text-primary font-bold' : 'text-green-500 font-bold'">
                        {{ trade.type }}
                      </span>
                    </td>
                    <td class="px-4 py-2 text-right">{{ formatNumber(trade.price) }}</td>
                    <td class="px-4 py-2 text-right text-slate-500">{{ trade.quantity }}</td>
                    <td
                      class="px-4 py-2 text-right"
                      :class="{
                        'text-green-500 font-bold': trade.profit && trade.profit > 0,
                        'text-red-500 font-bold': trade.profit && trade.profit < 0,
                        'text-slate-300': !trade.profit
                      }"
                    >
                      {{ trade.profit ? formatReturn(trade.profit) : '-' }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="border border-slate-200 rounded bg-white shadow-sm flex flex-col overflow-hidden">
            <div class="px-4 py-2 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
              <h3 class="text-[12px] font-bold text-slate-600 flex items-center gap-1.5">
                <Icon icon="mdi:terminal" :size="16" />
                系统运行日志
              </h3>
              <div class="flex items-center gap-2">
                <span class="flex items-center gap-1 text-[10px] text-red-500">
                  <span class="w-1.5 h-1.5 rounded-full bg-red-500"></span>
                  {{ logs.filter(l => l.level === 'ERROR').length }} Errors
                </span>
                <span class="flex items-center gap-1 text-[10px] text-amber-500">
                  <span class="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
                  {{ logs.filter(l => l.level === 'WARNING').length }} Warnings
                </span>
              </div>
            </div>
            <div class="flex-1 bg-slate-900 p-4 font-mono text-[11px] text-slate-300 overflow-auto">
              <div v-for="(log, index) in logs" :key="index" class="mb-1">
                <span class="text-slate-500">[{{ log.time }}]</span>
                <span
                  :class="{
                    'text-blue-400': log.level === 'INFO',
                    'text-amber-500': log.level === 'WARNING',
                    'text-red-400': log.level === 'ERROR',
                    'text-green-400': log.level === 'SUCCESS'
                  }"
                >
                  {{ log.level }}:
                </span>
                {{ log.message }}
              </div>
              <div class="text-primary animate-pulse">_</div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <footer class="bg-white border-t border-slate-200 px-6 py-1.5 flex items-center justify-between text-[10px] text-slate-400 font-medium shrink-0">
      <div class="flex items-center gap-4">
        <span class="flex items-center gap-1">
          <span class="w-1.5 h-1.5 rounded-full bg-green-500"></span>
          Connected to DataServer
        </span>
        <span>Backtrader v1.9.78.123</span>
      </div>
      <div>Memory Usage: 428MB / 4096MB</div>
    </footer>
  </div>
</template>
