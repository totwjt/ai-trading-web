<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  getBacktestDetail,
  getBacktestLogs,
  getBacktestProgress,
  getBacktestTrades,
  getEquityCurve,
  getPerformance,
  runBacktest,
  type BacktestDetail,
  type EquityPoint,
  type LogItem,
  type PerformanceResponse,
  type TradeItem
} from '@/api/backtest'
import EquityChart from '@/components/backtest/EquityChart.vue'
import Icon from '@/components/common/Icon.vue'

const route = useRoute()
const router = useRouter()

const backtestId = computed(() => Number(route.params.id))
const returnStrategyId = computed(() => {
  const parsed = Number(route.query.strategyId ?? route.query.strategy_id)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null
})
const returnStrategyName = computed(() => {
  const value = route.query.strategyName
  return typeof value === 'string' && value.trim() ? value.trim() : ''
})

const detail = ref<BacktestDetail | null>(null)
const trades = ref<TradeItem[]>([])
const logs = ref<LogItem[]>([])
const equityCurve = ref<EquityPoint[]>([])
const performance = ref<PerformanceResponse | null>(null)

const loading = ref(true)
const isRefreshingPanels = ref(false)
const runningAction = ref(false)
const chartFrequency = ref('1d')
const pageError = ref('')
const tradesError = ref('')
const logsError = ref('')
const equityError = ref('')
const performanceError = ref('')

const isPolling = computed(() => ['pending', 'running'].includes(detail.value?.status ?? ''))
const statusText = computed(() => {
  const currentStatus = detail.value?.status
  const mapping: Record<string, string> = {
    pending: '等待启动',
    running: '运行中',
    completed: '已完成',
    failed: '已失败',
    cancelled: '已取消'
  }
  return mapping[currentStatus ?? ''] ?? '未知状态'
})
const statusClass = computed(() => {
  const currentStatus = detail.value?.status
  const mapping: Record<string, string> = {
    pending: 'bg-amber-100 text-amber-700',
    running: 'bg-blue-100 text-blue-700',
    completed: 'bg-emerald-100 text-emerald-700',
    failed: 'bg-red-100 text-red-700',
    cancelled: 'bg-slate-100 text-slate-600'
  }
  return mapping[currentStatus ?? ''] ?? 'bg-slate-100 text-slate-600'
})
const statusDescription = computed(() => {
  if (!detail.value) return '正在加载回测详情'
  if (detail.value.status === 'pending') return '任务已创建，等待启动'
  if (detail.value.status === 'running') return '引擎正在执行，页面会自动刷新日志和结果'
  if (detail.value.status === 'completed') return '回测已完成，可以查看完整结果'
  if (detail.value.status === 'failed') return detail.value.error_message || '回测执行失败，请检查日志'
  if (detail.value.status === 'cancelled') return '回测已取消'
  return '状态未知'
})
const runButtonText = computed(() => {
  if (runningAction.value) return '启动中...'
  if (detail.value?.status === 'pending') return '启动回测'
  if (detail.value?.status === 'running') return '运行中'
  return '刷新数据'
})
const summaryMetrics = computed(() => {
  if (!detail.value) return []
  return [
    {
      label: '总收益率',
      value: formatReturn(detail.value.results.total_return),
      className: getReturnClass(detail.value.results.total_return)
    },
    {
      label: '年化收益',
      value: formatReturn(detail.value.results.annual_return),
      className: getReturnClass(detail.value.results.annual_return)
    },
    {
      label: '最大回撤',
      value: formatPercent(detail.value.results.max_drawdown),
      className: 'text-down'
    },
    {
      label: '夏普比率',
      value: formatDecimal(detail.value.results.sharpe_ratio),
      className: 'text-textMain'
    },
    {
      label: '胜率',
      value: formatPercent(detail.value.results.win_rate),
      className: 'text-textMain'
    },
    {
      label: '盈亏比',
      value: formatDecimal(detail.value.results.profit_loss_ratio),
      className: 'text-textMain'
    }
  ]
})
const extendedMetrics = computed(() => {
  const metrics = performance.value?.metrics ?? {}
  return [
    { label: 'Calmar', value: formatDecimal(metrics.calmar_ratio) },
    { label: 'Sortino', value: formatDecimal(metrics.sortino_ratio) },
    { label: '波动率', value: formatPercent(metrics.volatility) },
    { label: 'Beta', value: formatDecimal(metrics.beta) },
    { label: 'Alpha', value: formatPercent(metrics.alpha) },
    { label: '信息比率', value: formatDecimal(metrics.information_ratio) },
    { label: '总交易数', value: formatInteger(metrics.total_trades) },
    { label: '平均持仓天数', value: formatDecimal(metrics.avg_holding_days) },
    { label: '单笔平均收益', value: formatDecimal(metrics.avg_profit_per_trade) }
  ]
})

let progressTimer: ReturnType<typeof setInterval> | null = null
let progressRequestInFlight = false
let panelsRequestInFlight = false

function stopProgressPolling() {
  if (progressTimer) {
    clearInterval(progressTimer)
    progressTimer = null
  }
}

function startProgressPolling() {
  if (!isPolling.value || progressTimer) return
  progressTimer = setInterval(() => {
    void pollProgress()
  }, 2000)
}

function formatNumber(value: number | undefined, decimals: number = 2): string {
  if (value === undefined || value === null) return '-'
  return value.toLocaleString('zh-CN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  })
}

function formatDecimal(value: number | undefined): string {
  if (value === undefined || value === null) return '-'
  return value.toFixed(2)
}

function formatInteger(value: number | undefined): string {
  if (value === undefined || value === null) return '-'
  return value.toString()
}

function formatPercent(value: number | undefined): string {
  if (value === undefined || value === null) return '-'
  return `${value.toFixed(2)}%`
}

function formatReturn(value: number | undefined): string {
  if (value === undefined || value === null) return '-'
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
}

function getReturnClass(value: number | undefined): string {
  if (value === undefined || value === null) return 'text-textSub'
  return value >= 0 ? 'text-up' : 'text-down'
}

async function fetchDetailData() {
  const detailData = await getBacktestDetail(backtestId.value)
  detail.value = detailData
  pageError.value = ''

  if (isPolling.value) {
    startProgressPolling()
  } else {
    stopProgressPolling()
  }
}

async function fetchPanelData(options?: { silent?: boolean }) {
  if (panelsRequestInFlight) return

  panelsRequestInFlight = true
  if (!options?.silent) {
    isRefreshingPanels.value = true
  }

  const [tradesResult, logsResult, equityResult, performanceResult] = await Promise.allSettled([
    getBacktestTrades(backtestId.value),
    getBacktestLogs(backtestId.value),
    getEquityCurve(backtestId.value, chartFrequency.value),
    getPerformance(backtestId.value)
  ])

  if (tradesResult.status === 'fulfilled') {
    trades.value = tradesResult.value.items
    tradesError.value = ''
  } else {
    tradesError.value = '交易明细刷新失败'
  }

  if (logsResult.status === 'fulfilled') {
    logs.value = logsResult.value.logs
    logsError.value = ''
  } else {
    logsError.value = '日志刷新失败'
  }

  if (equityResult.status === 'fulfilled') {
    equityCurve.value = equityResult.value.data_points
    equityError.value = ''
  } else {
    equityError.value = '净值曲线刷新失败'
  }

  if (performanceResult.status === 'fulfilled') {
    performance.value = performanceResult.value
    performanceError.value = ''
  } else {
    performanceError.value = '性能指标刷新失败'
  }

  panelsRequestInFlight = false
  isRefreshingPanels.value = false
}

async function fetchData(options?: { silentPanels?: boolean }) {
  if (!options?.silentPanels) {
    loading.value = true
  }

  try {
    await fetchDetailData()
    await fetchPanelData({ silent: options?.silentPanels })
  } catch (error) {
    pageError.value = error instanceof Error ? error.message : '加载回测详情失败'
    stopProgressPolling()
  } finally {
    loading.value = false
  }
}

async function pollProgress() {
  if (!detail.value || progressRequestInFlight || !isPolling.value) {
    if (!isPolling.value) {
      stopProgressPolling()
    }
    return
  }

  progressRequestInFlight = true
  try {
    const progress = await getBacktestProgress(backtestId.value)
    detail.value = {
      ...detail.value,
      status: progress.status as BacktestDetail['status'],
      progress: progress.progress
    }

    await fetchPanelData({ silent: true })

    if (!['pending', 'running'].includes(progress.status)) {
      stopProgressPolling()
      await fetchData({ silentPanels: true })
    }
  } catch (error) {
    console.error('获取回测进度失败:', error)
    stopProgressPolling()
  } finally {
    progressRequestInFlight = false
  }
}

function goBack() {
  router.push({
    path: '/backtest/records',
    query: returnStrategyId.value
      ? {
          strategyId: String(returnStrategyId.value),
          strategyName: returnStrategyName.value || undefined
        }
      : undefined
  })
}

function editStrategy() {
  if (!detail.value) return
  router.push(`/backtest/edit/${detail.value.strategy_id}?backtestId=${backtestId.value}`)
}

async function changeFrequency(freq: string) {
  chartFrequency.value = freq
  await fetchPanelData()
}

async function handlePrimaryAction() {
  if (!detail.value) return

  if (detail.value.status === 'pending') {
    runningAction.value = true
    try {
      await runBacktest(backtestId.value)
      await fetchData({ silentPanels: true })
      startProgressPolling()
    } catch (error) {
      pageError.value = error instanceof Error ? error.message : '启动回测失败'
    } finally {
      runningAction.value = false
    }
    return
  }

  await fetchData({ silentPanels: true })
}

onMounted(() => {
  void fetchData()
})

onBeforeUnmount(() => {
  stopProgressPolling()
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
          返回记录
        </button>
        <div class="h-6 w-px bg-slate-200 mr-6"></div>
        <span class="text-sm font-medium text-slate-600">
          策略: {{ detail?.strategy_name || '加载中...' }}
        </span>
      </div>

      <div class="flex items-center gap-2">
        <button
          class="border border-slate-200 px-3 py-1.5 rounded text-xs font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-50"
          :disabled="!detail"
          @click="editStrategy"
        >
          编辑策略
        </button>
        <button
          class="p-1.5 hover:bg-slate-50 text-slate-400 rounded transition-colors"
          title="刷新"
          @click="fetchData({ silentPanels: true })"
        >
          <Icon icon="mdi:refresh" :size="20" />
        </button>
        <button
          class="bg-primary text-white px-3 py-1.5 rounded text-xs font-bold flex items-center gap-1 hover:bg-blue-700 disabled:opacity-50"
          :disabled="runningAction || detail?.status === 'running' || !detail"
          @click="handlePrimaryAction"
        >
          <Icon :icon="detail?.status === 'pending' ? 'mdi:play' : 'mdi:refresh'" :size="16" />
          {{ runButtonText }}
        </button>
      </div>
    </header>

    <main class="flex-1 overflow-auto p-6 bg-bgMain">
      <div v-if="loading" class="flex items-center justify-center h-64">
        <span class="text-textMute">加载中...</span>
      </div>

      <div v-else-if="pageError" class="border border-red-200 rounded-lg bg-red-50 p-4 text-sm text-red-700">
        {{ pageError }}
      </div>

      <div v-else-if="detail" class="space-y-4">
        <section class="grid grid-cols-1 md:grid-cols-4 gap-4 border border-border rounded-lg p-4 bg-card shadow-sm">
          <div class="border-r border-slate-100 last:border-0">
            <p class="text-[10px] text-textMute uppercase font-bold tracking-wider mb-1">回测策略名称</p>
            <div class="flex items-center gap-2">
              <Icon icon="mdi:code-braces" :size="20" class="text-primary" />
              <h1 class="text-sm font-bold truncate text-textMain">{{ detail.strategy_name || '-' }}</h1>
            </div>
          </div>
          <div class="border-r border-slate-100 last:border-0 px-2">
            <p class="text-[10px] text-textMute uppercase font-bold tracking-wider mb-1">测试时间周期</p>
            <p class="text-sm font-mono font-medium text-textMain">
              {{ detail.params.start_date }} ~ {{ detail.params.end_date }}
            </p>
          </div>
          <div class="border-r border-slate-100 last:border-0 px-2">
            <p class="text-[10px] text-textMute uppercase font-bold tracking-wider mb-1">初始资金 / 期末权益</p>
            <div class="flex items-baseline gap-2">
              <span class="text-sm font-mono text-textMain">{{ formatNumber(detail.params.initial_capital) }}</span>
              <span class="text-slate-300 text-xs">→</span>
              <span class="text-sm font-mono font-bold" :class="getReturnClass(detail.results.total_return)">
                {{ formatNumber(detail.results.final_equity) }}
              </span>
            </div>
          </div>
          <div class="px-2">
            <p class="text-[10px] text-textMute uppercase font-bold tracking-wider mb-1">当前状态</p>
            <div class="flex items-center gap-2">
              <span :class="['px-2 py-0.5 rounded text-[11px] font-bold', statusClass]">
                {{ statusText }}
              </span>
              <span class="text-xs text-textSub font-mono">{{ detail.progress }}%</span>
            </div>
            <p class="mt-2 text-xs text-textSub">{{ statusDescription }}</p>
          </div>
        </section>

        <section
          class="border rounded-lg p-4"
          :class="detail.status === 'failed' ? 'border-red-200 bg-red-50' : 'border-border bg-card'"
        >
          <div class="flex items-center justify-between gap-4">
            <div>
              <span class="text-sm font-bold text-textMain">任务进度</span>
              <span class="text-xs text-textSub mt-1">
                创建时间 {{ new Date(detail.created_at).toLocaleString('zh-CN') }}
                <span v-if="detail.completed_at">
                  · 完成时间 {{ new Date(detail.completed_at).toLocaleString('zh-CN') }}
                </span>
              </span>
            </div>
            <span v-if="isRefreshingPanels" class="text-xs text-textMute">子模块刷新中...</span>
          </div>
          <div class="mt-3 h-2 bg-slate-100 rounded-full overflow-hidden">
            <div
              class="h-full bg-primary rounded-full transition-all"
              :style="{ width: `${detail.progress}%` }"
            ></div>
          </div>
          <p v-if="detail.error_message" class="mt-3 text-sm text-red-600">
            {{ detail.error_message }}
          </p>
        </section>

        <section class="border border-border rounded-lg bg-card shadow-sm">
          <div class="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
            <div class="flex items-center gap-4">
              <h3 class="text-sm font-bold flex items-center gap-2 text-textMain">
                <Icon icon="mdi:chart-line" :size="20" class="text-primary" />
                策略净值曲线 vs 沪深300基准
              </h3>
              <div class="flex items-center gap-3 text-[11px]">
                <div class="flex items-center gap-1.5">
                  <span class="w-3 h-0.5 bg-primary"></span>
                  <span class="text-textSub font-medium">策略组合</span>
                </div>
                <div class="flex items-center gap-1.5">
                  <span class="w-3 h-0.5 bg-slate-300"></span>
                  <span class="text-textMute font-medium">沪深300</span>
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
            </div>
          </div>
          <div class="p-4 min-h-[360px]">
            <div v-if="equityError" class="h-full flex items-center justify-center text-sm text-red-600">
              {{ equityError }}
            </div>
            <EquityChart
              v-else-if="equityCurve.length > 0"
              :data="equityCurve"
              benchmark="沪深300"
            />
            <div v-else class="h-full flex items-center justify-center text-textMute">
              {{ isPolling ? '回测运行中，净值曲线生成后会自动展示' : '暂无净值曲线数据' }}
            </div>
          </div>
        </section>

        <section class="grid grid-cols-1 xl:grid-cols-3 gap-4">
          <div class="xl:col-span-1 border border-border rounded-lg bg-card shadow-sm">
            <div class="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
              <h3 class="text-sm font-bold text-textMain flex items-center gap-2">
                <Icon icon="mdi:sigma" :size="18" />
                性能指标
              </h3>
              <span class="text-xs text-textMute">{{ performanceError || '结果摘要' }}</span>
            </div>
            <div class="p-4 space-y-4">
              <div class="grid grid-cols-2 gap-3">
                <div
                  v-for="item in summaryMetrics"
                  :key="item.label"
                  class="border border-slate-100 rounded-lg p-3 bg-slate-50/70"
                >
                  <p class="text-[10px] uppercase text-textMute">{{ item.label }}</p>
                  <p class="mt-2 text-base font-bold" :class="item.className">{{ item.value }}</p>
                </div>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div
                  v-for="item in extendedMetrics"
                  :key="item.label"
                  class="text-sm"
                >
                  <p class="text-[10px] uppercase text-textMute">{{ item.label }}</p>
                  <p class="mt-1 font-semibold text-textMain">{{ item.value }}</p>
                </div>
              </div>
            </div>
          </div>

          <div class="xl:col-span-1 border border-border rounded-lg bg-card shadow-sm flex flex-col overflow-hidden min-h-[350px]">
            <div class="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
              <h3 class="text-sm font-bold text-textMain flex items-center gap-2">
                <Icon icon="mdi:list-status" :size="18" />
                交易明细
              </h3>
              <span class="text-xs text-textMute">共 {{ trades.length }} 笔</span>
            </div>
            <div v-if="tradesError" class="flex-1 flex items-center justify-center text-sm text-red-600">
              {{ tradesError }}
            </div>
            <div v-else-if="trades.length === 0" class="flex-1 flex items-center justify-center text-textMute">
              {{ isPolling ? '回测运行中，交易生成后会自动展示' : '暂无交易明细' }}
            </div>
            <div v-else class="flex-1 overflow-auto">
              <table class="w-full text-left text-[11px] border-collapse font-mono">
                <thead class="sticky top-0 bg-white shadow-sm text-textMute font-bold uppercase">
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
                      <span :class="trade.type === 'BUY' ? 'text-primary font-bold' : 'text-down font-bold'">
                        {{ trade.type }}
                      </span>
                    </td>
                    <td class="px-4 py-2 text-right">{{ formatNumber(trade.price) }}</td>
                    <td class="px-4 py-2 text-right text-slate-500">{{ trade.quantity }}</td>
                    <td class="px-4 py-2 text-right" :class="getReturnClass(trade.profit)">
                      {{ trade.profit === undefined || trade.profit === null ? '-' : formatReturn(trade.profit) }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="xl:col-span-1 border border-border rounded-lg bg-card shadow-sm flex flex-col overflow-hidden min-h-[350px]">
            <div class="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
              <h3 class="text-sm font-bold text-textMain flex items-center gap-2">
                <Icon icon="mdi:terminal" :size="18" />
                系统运行日志
              </h3>
              <div class="flex items-center gap-2">
                <span class="flex items-center gap-1 text-[10px] text-red-500">
                  <span class="w-1.5 h-1.5 rounded-full bg-red-500"></span>
                  {{ logs.filter(log => log.level === 'ERROR').length }} Errors
                </span>
                <span class="flex items-center gap-1 text-[10px] text-amber-500">
                  <span class="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
                  {{ logs.filter(log => log.level === 'WARNING').length }} Warnings
                </span>
              </div>
            </div>
            <div v-if="logsError" class="flex-1 flex items-center justify-center text-sm text-red-600">
              {{ logsError }}
            </div>
            <div v-else-if="logs.length === 0" class="flex-1 flex items-center justify-center bg-slate-900 text-slate-400">
              {{ isPolling ? '任务运行中，日志输出后会自动展示' : '暂无系统日志' }}
            </div>
            <div v-else class="flex-1 bg-slate-900 p-4 font-mono text-[11px] text-slate-300 overflow-auto">
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
            </div>
          </div>
        </section>
      </div>
    </main>
  </div>
</template>
