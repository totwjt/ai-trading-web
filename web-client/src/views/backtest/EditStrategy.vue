<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getStrategyDetail, createStrategy, updateStrategy } from '@/api/strategy'
import { previewStrategy, createBacktest, runBacktest, type BacktestParams, type PreviewResult } from '@/api/backtest'
import Icon from '@/components/common/Icon.vue'

const route = useRoute()
const router = useRouter()

const strategyId = computed(() => route.params.id ? Number(route.params.id) : null)
const isNew = computed(() => !strategyId.value)
const returnBacktestId = computed(() => {
  const rawValue = route.query.backtestId ?? route.query.backtest_id
  const parsed = Number(rawValue)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null
})

const strategyName = ref('新建策略')
const strategyType = ref('custom')
const strategyCode = ref(`import backtrader as bt

class MyStrategy(bt.Strategy):
    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                print(f'买入: 价格 {order.executed.price:.2f}, 数量 {order.executed.size}')
            elif order.issell():
                print(f'卖出: 价格 {order.executed.price:.2f}, 数量 {order.executed.size}')
        self.order = None

    def next(self):
        if self.order:
            return
        if not self.position:
            if self.dataclose[0] > self.dataclose[-1]:
                self.order = self.buy()
        else:
            if self.dataclose[0] < self.dataclose[-1]:
                self.order = self.sell()
`)

const startDate = ref(new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0])
const endDate = ref(new Date().toISOString().split('T')[0])
const frequency = ref('1d')
const initialCapital = ref(1000000)
const commissionRate = ref(0.0003)
const useMinCommission = ref(true)
const minCommission = ref(5)
const slippageRate = ref(0.0001)
const fillRatio = ref(1)
const adjustMode = ref('qfq')
const benchmarkCode = ref('000300.SH')
const symbolInput = ref('')
const matchMode = ref<'open' | 'close'>('open')
const strategyDescription = ref('')

// 时间范围选项
const dateRangeOption = ref<'custom' | '3years'>('custom')

const today = new Date()
const threeYearsAgo = new Date(today.getFullYear() - 3, today.getMonth(), today.getDate())

const computedStartDate = computed(() => {
  return dateRangeOption.value === '3years'
    ? threeYearsAgo.toISOString().split('T')[0]
    : startDate.value
})

const computedEndDate = computed(() => {
  return dateRangeOption.value === '3years'
    ? today.toISOString().split('T')[0]
    : endDate.value
})

const adjustModeOptions = [
  { label: '前复权', value: 'qfq' },
  { label: '后复权', value: 'hfq' },
  { label: '不复权', value: 'none' }
]

const matchModeOptions = [
  { label: '下一根开盘撮合', value: 'open' },
  { label: '当前收盘撮合', value: 'close' }
]

function parseSymbols(value: string): string[] {
  return value
    .split(/[\s,，]+/)
    .map(item => item.trim().toUpperCase())
    .filter(Boolean)
}

function setDateRangeOption(option: 'custom' | '3years') {
  dateRangeOption.value = option
}

const logs = ref<Array<{ time: string; level: string; message: string }>>([
  { time: '10:00:00', level: 'INFO', message: '策略编辑器已就绪' }
])
const isRunning = ref(false)
const isSaving = ref(false)
const isLoadingStrategy = ref(false)
const previewResult = ref<PreviewResult | null>(null)
const totalReturn = ref<number | null>(null)
const annualReturn = ref<number | null>(null)
const maxDrawdown = ref<number | null>(null)
const sharpeRatio = ref<number | null>(null)
const winRate = ref<number | null>(null)
const profitLossRatio = ref<number | null>(null)
const previewFinalEquity = ref<number | null>(null)
const previewInitialValue = ref<number | null>(null)
const parameterModalOpen = ref(false)

const frequencyOptions = [
  { label: '日线', value: '1d' }
]

function addLog(level: string, message: string) {
  const now = new Date()
  const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`
  logs.value.push({ time, level, message })
}

function clearLogs() {
  logs.value = []
}

async function loadStrategy() {
  if (!strategyId.value) return

  isLoadingStrategy.value = true
  try {
    const strategy = await getStrategyDetail(strategyId.value)
    strategyName.value = strategy.name
    strategyType.value = strategy.strategy_type || 'custom'
    strategyCode.value = strategy.code || strategyCode.value
    strategyDescription.value = strategy.description || ''
    if (strategy.config) {
      initialCapital.value = strategy.config.initial_capital ?? initialCapital.value
      commissionRate.value = strategy.config.commission ?? commissionRate.value
      useMinCommission.value = strategy.config.use_min_commission ?? useMinCommission.value
      minCommission.value = strategy.config.min_commission ?? minCommission.value
      slippageRate.value = strategy.config.slippage ?? slippageRate.value
      fillRatio.value = strategy.config.fill_ratio ?? fillRatio.value
      adjustMode.value = strategy.config.adjust_mode ?? adjustMode.value
      benchmarkCode.value = strategy.config.benchmark_code ?? benchmarkCode.value
      symbolInput.value = (strategy.config.symbols ?? []).join(', ')
      matchMode.value = (strategy.config.match_mode as 'open' | 'close') ?? matchMode.value
    }
    if (strategy.name.includes('掘金-布林线均值回归') && !symbolInput.value.trim()) {
      symbolInput.value = '600004.SH'
      matchMode.value = 'close'
      addLog('INFO', '已为掘金布林线策略预填白云机场与收盘撮合参数')
    }
    addLog('INFO', `已加载策略: ${strategy.name}`)
  } catch (error) {
    addLog('ERROR', `加载策略失败: ${error}`)
  } finally {
    isLoadingStrategy.value = false
  }
}

function validateBeforeSubmit(): boolean {
  if (!strategyName.value.trim()) {
    addLog('WARNING', '请输入策略名称')
    return false
  }

  if (!strategyCode.value.trim()) {
    addLog('WARNING', '策略代码不能为空')
    return false
  }

  if (!computedStartDate.value || !computedEndDate.value || computedStartDate.value > computedEndDate.value) {
    addLog('WARNING', '请检查回测日期范围')
    return false
  }

  if (!Number.isFinite(initialCapital.value) || initialCapital.value <= 0) {
    addLog('WARNING', '初始资金必须大于 0')
    return false
  }

  if (!Number.isFinite(commissionRate.value) || commissionRate.value < 0) {
    addLog('WARNING', '手续费率不能小于 0')
    return false
  }

  if (!Number.isFinite(minCommission.value) || minCommission.value < 0) {
    addLog('WARNING', '最低手续费不能小于 0')
    return false
  }

  if (!Number.isFinite(slippageRate.value) || slippageRate.value < 0) {
    addLog('WARNING', '滑点比率不能小于 0')
    return false
  }

  if (!Number.isFinite(fillRatio.value) || fillRatio.value <= 0 || fillRatio.value > 1) {
    addLog('WARNING', '成交比率必须在 0 到 1 之间')
    return false
  }

  return true
}

function buildStrategyPayload() {
  return {
    name: strategyName.value.trim(),
    strategy_type: strategyType.value,
    code: strategyCode.value,
    description: strategyDescription.value || undefined,
    config: {
      initial_capital: initialCapital.value,
      commission: commissionRate.value,
      use_min_commission: useMinCommission.value,
      min_commission: minCommission.value,
      slippage: slippageRate.value,
      fill_ratio: fillRatio.value,
      adjust_mode: adjustMode.value,
      benchmark_code: benchmarkCode.value.trim() || '000300.SH',
      symbols: parseSymbols(symbolInput.value),
      match_mode: matchMode.value
    }
  }
}

function buildBacktestParams(): BacktestParams {
  return {
    start_date: computedStartDate.value,
    end_date: computedEndDate.value,
    frequency: frequency.value,
    initial_capital: initialCapital.value,
    commission: commissionRate.value,
    use_min_commission: useMinCommission.value,
    min_commission: minCommission.value,
    slippage: slippageRate.value,
    fill_ratio: fillRatio.value,
    adjust_mode: adjustMode.value,
    benchmark_code: benchmarkCode.value.trim() || '000300.SH',
    symbols: parseSymbols(symbolInput.value),
    match_mode: matchMode.value
  }
}

async function handleSave() {
  if (!validateBeforeSubmit()) return

  isSaving.value = true
  try {
    if (isNew.value) {
      const result = await createStrategy(buildStrategyPayload())
      addLog('SUCCESS', `策略已创建，ID: ${result.id}`)
      router.replace({
        path: `/backtest/edit/${result.id}`,
        query: route.query
      })
    } else {
      await updateStrategy(strategyId.value!, buildStrategyPayload())
      addLog('SUCCESS', '策略已保存')
    }
  } catch (error) {
    addLog('ERROR', `保存失败: ${error}`)
  } finally {
    isSaving.value = false
  }
}

function openParameterModal() {
  parameterModalOpen.value = true
}

function closeParameterModal() {
  if (isRunning.value) return
  parameterModalOpen.value = false
}

async function executePreview() {
  if (!validateBeforeSubmit()) return

  isRunning.value = true
  addLog('INFO', '开始编译检查...')

  try {
    const result = await previewStrategy({
      strategy_id: strategyId.value || undefined,
      code: strategyCode.value,
      params: buildBacktestParams()
    })

    previewResult.value = result

    if (result.success) {
      result.logs?.forEach(log => {
        addLog(log.level, log.message)
      })

      if (result.summary) {
        totalReturn.value = result.summary.total_return || null
        annualReturn.value = result.summary.annual_return || null
        maxDrawdown.value = result.summary.max_drawdown || null
        sharpeRatio.value = result.summary.sharpe_ratio || null
        winRate.value = result.summary.win_rate || null
        profitLossRatio.value = result.summary.profit_loss_ratio || null
        previewFinalEquity.value = result.summary.final_equity || null
        previewInitialValue.value = result.summary.initial_value || null
      }

      addLog('SUCCESS', '编译运行完成')
    } else {
      result.logs?.forEach(log => {
        addLog(log.level, log.message)
      })
      addLog('ERROR', result.error || '编译失败')
    }
  } catch (error) {
    addLog('ERROR', `执行失败: ${error}`)
  } finally {
    isRunning.value = false
  }
}

async function executeRunBacktest() {
  if (!validateBeforeSubmit()) return

  if (!strategyId.value) {
    addLog('WARNING', '请先保存策略后再运行回测')
    return
  }

  isRunning.value = true
  addLog('INFO', '创建回测任务...')

  try {
    await updateStrategy(strategyId.value!, buildStrategyPayload())
    addLog('INFO', '已同步当前策略代码与回测参数')

    const result = await createBacktest(strategyId.value, buildBacktestParams())
    addLog('SUCCESS', `回测任务已创建: ID ${result.backtest_id}`)

    await runBacktest(result.backtest_id)
    addLog('INFO', `回测任务已启动: ID ${result.backtest_id}`)

    router.push({
      path: `/backtest/detail/${result.backtest_id}`,
      query: {
        strategyId: String(strategyId.value),
        strategyName: strategyName.value.trim() || undefined
      }
    })
  } catch (error) {
    addLog('ERROR', `启动回测失败: ${error}`)
    isRunning.value = false
    parameterModalOpen.value = false
  }
}

async function confirmModalAction() {
  await executeRunBacktest()
}

function goBack() {
  if (returnBacktestId.value) {
    router.push(`/backtest/detail/${returnBacktestId.value}`)
    return
  }
  if (route.query.strategyId || route.query.strategyName) {
    router.push({
      path: '/backtest/records',
      query: {
        strategyId: typeof route.query.strategyId === 'string' ? route.query.strategyId : undefined,
        strategyName: typeof route.query.strategyName === 'string' ? route.query.strategyName : undefined
      }
    })
    return
  }
  router.push('/backtest')
}

onMounted(() => {
  if (!isNew.value) {
    loadStrategy()
  }
})
</script>

<template>
  <div class="flex-1 bg-white flex flex-col overflow-hidden min-h-0 h-full">
    <header class="flex items-center justify-between px-5 h-12 border-b border-slate-200 bg-white shrink-0">
      <div class="flex items-center min-w-0">
        <button
          class="flex items-center gap-1 mr-6 text-sm text-slate-600 hover:text-primary transition-colors"
          @click="goBack"
        >
          <Icon icon="mdi:arrow-left" :size="20" />
          返回
        </button>
        <div class="h-6 w-px bg-slate-200 mr-6"></div>
        <div class="flex items-center gap-2 min-w-0">
          <span class="text-xs text-slate-500">策略:</span>
          <input
            v-model="strategyName"
            class="w-72 rounded-md border border-border bg-card px-3 py-1 text-sm text-textMain focus:border-primary focus:outline-none"
            placeholder="请输入策略名称"
          />
        </div>
      </div>

      <div class="flex items-center gap-3">
        <button
          class="bg-primary text-white px-3.5 py-1.5 rounded-lg text-sm font-semibold hover:opacity-90 transition-opacity disabled:opacity-50"
          :disabled="isRunning"
          @click="openParameterModal"
        >
          <Icon v-if="isRunning" icon="mdi:loading" class="animate-spin" :size="16" />
          <span v-else>运行回测</span>
        </button>
        <button
          class="border border-border bg-card px-3.5 py-1.5 rounded-lg text-sm font-medium text-textMain hover:bg-gray-50 transition-colors disabled:opacity-50"
          :disabled="isSaving"
          @click="handleSave"
        >
          保存
        </button>
      </div>
    </header>

    <main class="flex-1 flex flex-col overflow-hidden">
      <div class="flex-1 flex overflow-hidden">
        <section class="w-[60%] bg-[#1e1e1e] flex flex-col relative">
        <div class="flex items-center justify-between px-4 py-2 border-b border-white/10 text-xs text-slate-400 bg-[#252526]">
          <span class="flex items-center">
            <span class="w-2 h-2 rounded-full bg-orange-400 mr-2"></span>
            main.py
          </span>
          <span>Python 3.8</span>
        </div>
        <textarea
          v-model="strategyCode"
          class="flex-1 w-full bg-[#1e1e1e] text-slate-300 font-mono text-[13px] leading-relaxed p-4 resize-none focus:outline-none"
          spellcheck="false"
        ></textarea>
        <div v-if="isLoadingStrategy" class="absolute inset-0 bg-black/30 flex items-center justify-center text-white text-sm">
          正在加载策略...
        </div>
        </section>

        <section class="w-[40%] flex flex-col border-l border-slate-200 bg-slate-50 overflow-hidden">
        <div class="h-1/2 flex flex-col border-b border-slate-200">
          <div class="flex items-center justify-between px-4 py-2 bg-white border-b border-slate-200">
            <span class="text-xs font-bold text-slate-700 uppercase tracking-tight">运行日志 / 错误</span>
            <button class="text-slate-400 hover:text-slate-600" @click="clearLogs">
              <Icon icon="mdi:delete" :size="16" />
            </button>
          </div>
          <div class="flex-1 overflow-auto custom-scrollbar p-4 font-mono text-[12px] space-y-2">
            <div
              v-for="(log, index) in logs"
              :key="index"
              class="flex"
            >
              <span class="w-20 shrink-0 text-slate-500">{{ log.time }}</span>
              <span
                :class="{
                  'text-blue-600': log.level === 'INFO',
                  'text-amber-500': log.level === 'WARNING',
                  'text-red-500': log.level === 'ERROR',
                  'text-green-500': log.level === 'SUCCESS'
                }"
              >{{ log.level }}:</span>
              <span class="ml-2 text-slate-700">{{ log.message }}</span>
            </div>
          </div>
        </div>

        <div class="h-1/2 flex flex-col bg-white">
          <div class="px-4 py-2 border-b border-slate-100 flex items-center justify-between">
            <span class="text-xs font-bold text-slate-700 uppercase tracking-tight">实时回测预览</span>
            <button
              class="bg-primary text-white px-3 py-1 rounded text-[11px] font-medium hover:bg-blue-700 disabled:opacity-50"
              :disabled="isRunning"
              @click="executePreview"
            >
              {{ isRunning ? '运行中...' : '编译运行' }}
            </button>
          </div>
          <div class="flex-1 p-4">
            <div v-if="isRunning" class="h-full flex items-center justify-center">
              <span class="text-slate-400 flex items-center">
                <Icon icon="mdi:loading" class="animate-spin mr-2" :size="16" />
                运行中...
              </span>
            </div>
            <div v-else-if="!previewResult" class="h-full flex items-center justify-center text-slate-400">
              点击"编译运行"开始预览
            </div>
            <div v-else class="space-y-4">
              <div v-if="previewResult.error" class="text-red-500 text-sm">
                {{ previewResult.error }}
              </div>
              <div v-else class="grid grid-cols-2 gap-4">
                <div>
                  <div class="text-[10px] text-slate-400 uppercase">初始权益</div>
                  <div class="text-lg font-bold text-slate-800">
                    {{ previewInitialValue ? previewInitialValue.toLocaleString('zh-CN', { maximumFractionDigits: 2 }) : '-' }}
                  </div>
                </div>
                <div>
                  <div class="text-[10px] text-slate-400 uppercase">期末权益</div>
                  <div class="text-lg font-bold text-slate-800">
                    {{ previewFinalEquity ? previewFinalEquity.toLocaleString('zh-CN', { maximumFractionDigits: 2 }) : '-' }}
                  </div>
                </div>
                <div>
                  <div class="text-[10px] text-slate-400 uppercase">累计收益率</div>
                  <div
                    class="text-lg font-bold"
                    :class="(totalReturn || 0) >= 0 ? 'text-up' : 'text-down'"
                  >
                    {{ totalReturn ? (totalReturn >= 0 ? '+' : '') + totalReturn.toFixed(2) + '%' : '-' }}
                  </div>
                </div>
                <div>
                  <div class="text-[10px] text-slate-400 uppercase">年化收益</div>
                  <div
                    class="text-lg font-bold"
                    :class="(annualReturn || 0) >= 0 ? 'text-up' : 'text-down'"
                  >
                    {{ annualReturn ? (annualReturn >= 0 ? '+' : '') + annualReturn.toFixed(2) + '%' : '-' }}
                  </div>
                </div>
                <div>
                  <div class="text-[10px] text-slate-400 uppercase">最大回撤</div>
                  <div class="text-lg font-bold text-down">
                    {{ maxDrawdown ? maxDrawdown.toFixed(2) + '%' : '-' }}
                  </div>
                </div>
                <div>
                  <div class="text-[10px] text-slate-400 uppercase">夏普比率</div>
                  <div class="text-lg font-bold text-slate-800">
                    {{ sharpeRatio?.toFixed(2) || '-' }}
                  </div>
                </div>
                <div>
                  <div class="text-[10px] text-slate-400 uppercase">胜率</div>
                  <div class="text-lg font-bold text-slate-800">
                    {{ winRate ? winRate.toFixed(1) + '%' : '-' }}
                  </div>
                </div>
                <div>
                  <div class="text-[10px] text-slate-400 uppercase">盈亏比</div>
                  <div class="text-lg font-bold text-slate-800">
                    {{ profitLossRatio?.toFixed(2) || '-' }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        </section>
      </div>
    </main>

    <footer class="h-8 border-t border-slate-200 px-6 flex items-center bg-slate-50 shrink-0">
      <div class="flex items-center space-x-2">
        <span class="text-xs text-slate-500">
          最后更新: {{ new Date().toLocaleString('zh-CN') }}
        </span>
      </div>
    </footer>

    <a-modal
      :open="parameterModalOpen"
      title="确认回测参数"
      width="720px"
      :closable="!isRunning"
      :mask-closable="!isRunning"
      :keyboard="!isRunning"
      @cancel="closeParameterModal"
    >
      <div class="space-y-4">
        <div class="rounded-xl border border-border bg-gray-50 p-3">
          <div class="mb-2 flex items-center justify-between">
            <span class="text-xs font-semibold text-textMain">时间范围</span>
            <div class="flex items-center gap-2">
              <button
                class="px-2 py-0.5 rounded text-[11px] font-medium transition-colors"
                :class="dateRangeOption === 'custom' ? 'bg-primary text-white' : 'bg-card text-textSub border border-border hover:text-primary'"
                @click="setDateRangeOption('custom')"
              >
                自定义
              </button>
              <button
                class="px-2 py-0.5 rounded text-[11px] font-medium transition-colors"
                :class="dateRangeOption === '3years' ? 'bg-primary text-white' : 'bg-card text-textSub border border-border hover:text-primary'"
                @click="setDateRangeOption('3years')"
              >
                近三年
              </button>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-2.5">
            <label class="space-y-1">
              <span class="block text-[11px] text-textSub">开始日期</span>
              <input
                v-model="startDate"
                type="date"
                :disabled="dateRangeOption === '3years'"
                class="w-full rounded-md border border-border bg-card px-2.5 py-1.5 text-sm text-textMain focus:border-primary focus:outline-none disabled:bg-gray-100 disabled:text-textMute"
              />
            </label>
            <label class="space-y-1">
              <span class="block text-[11px] text-textSub">结束日期</span>
              <input
                v-model="endDate"
                type="date"
                :disabled="dateRangeOption === '3years'"
                class="w-full rounded-md border border-border bg-card px-2.5 py-1.5 text-sm text-textMain focus:border-primary focus:outline-none disabled:bg-gray-100 disabled:text-textMute"
              />
            </label>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <label class="space-y-1">
            <span class="block text-[11px] text-textSub">初始资金</span>
            <input v-model.number="initialCapital" type="number" min="1" step="10000" class="w-full rounded-md border border-border bg-card px-2.5 py-1.5 text-sm text-textMain focus:border-primary focus:outline-none" />
          </label>
          <label class="space-y-1">
            <span class="block text-[11px] text-textSub">数据频率</span>
            <select v-model="frequency" class="w-full rounded-md border border-border bg-card px-2.5 py-1.5 text-sm text-textMain focus:border-primary focus:outline-none">
              <option v-for="opt in frequencyOptions" :key="opt.value" :value="opt.value">
                {{ opt.label }}
              </option>
            </select>
          </label>
          <label class="space-y-1">
            <span class="block text-[11px] text-textSub">手续费率</span>
            <input v-model.number="commissionRate" type="number" min="0" step="0.0001" class="w-full rounded-md border border-border bg-card px-2.5 py-1.5 text-sm text-textMain focus:border-primary focus:outline-none" />
          </label>
          <label class="space-y-1">
            <span class="block text-[11px] text-textSub">最低手续费规则</span>
            <label class="flex h-[34px] items-center gap-2 rounded-md border border-border bg-card px-2.5 text-sm text-textMain">
              <input v-model="useMinCommission" type="checkbox" class="h-3.5 w-3.5 rounded border-border text-primary focus:ring-primary" />
              <span>启用最低 5 元/笔</span>
            </label>
          </label>
          <label class="space-y-1">
            <span class="block text-[11px] text-textSub">最低手续费</span>
            <input v-model.number="minCommission" type="number" min="0" step="1" :disabled="!useMinCommission" class="w-full rounded-md border border-border bg-card px-2.5 py-1.5 text-sm text-textMain focus:border-primary focus:outline-none disabled:bg-gray-100 disabled:text-textMute" />
          </label>
          <label class="space-y-1">
            <span class="block text-[11px] text-textSub">滑点比率</span>
            <input v-model.number="slippageRate" type="number" min="0" step="0.0001" class="w-full rounded-md border border-border bg-card px-2.5 py-1.5 text-sm text-textMain focus:border-primary focus:outline-none" />
          </label>
          <label class="space-y-1">
            <span class="block text-[11px] text-textSub">成交比率</span>
            <input v-model.number="fillRatio" type="number" min="0.01" max="1" step="0.01" class="w-full rounded-md border border-border bg-card px-2.5 py-1.5 text-sm text-textMain focus:border-primary focus:outline-none" />
          </label>
          <label class="space-y-1">
            <span class="block text-[11px] text-textSub">复权方式</span>
            <select v-model="adjustMode" class="w-full rounded-md border border-border bg-card px-2.5 py-1.5 text-sm text-textMain focus:border-primary focus:outline-none">
              <option v-for="option in adjustModeOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>
          <label class="space-y-1">
            <span class="block text-[11px] text-textSub">成交模式</span>
            <select v-model="matchMode" class="w-full rounded-md border border-border bg-card px-2.5 py-1.5 text-sm text-textMain focus:border-primary focus:outline-none">
              <option v-for="option in matchModeOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>
          <label class="space-y-1">
            <span class="block text-[11px] text-textSub">基准代码</span>
            <input v-model="benchmarkCode" type="text" class="w-full rounded-md border border-border bg-card px-2.5 py-1.5 text-sm text-textMain focus:border-primary focus:outline-none" placeholder="000300.SH" />
          </label>
        </div>

        <label class="block space-y-1">
          <span class="block text-[11px] text-textSub">回测标的 / 股票池</span>
          <input
            v-model="symbolInput"
            type="text"
            placeholder="例: 000001.SZ, 600519.SH"
            class="w-full rounded-md border border-border bg-card px-2.5 py-1.5 text-sm text-textMain focus:border-primary focus:outline-none"
          />
        </label>

        <div class="rounded-lg border border-border bg-gray-50 px-3 py-2 text-[11px] text-textMute">
          当前操作:
          <span class="font-medium text-textMain">运行回测</span>
          <span class="ml-3">成交模式: {{ matchMode === 'close' ? '当前收盘撮合' : '下一根开盘撮合' }}</span>
          <span class="ml-3">佣金: {{ useMinCommission ? `比例 + 最低 ${minCommission} 元` : '仅比例佣金' }}</span>
        </div>
      </div>

      <template #footer>
        <div class="flex items-center justify-end gap-3">
          <button
            class="border border-border bg-card px-3.5 py-1.5 rounded-lg text-sm font-medium text-textMain hover:bg-gray-50 transition-colors disabled:opacity-50"
            :disabled="isRunning"
            @click="closeParameterModal"
          >
            取消
          </button>
          <button
            class="bg-primary text-white px-3.5 py-1.5 rounded-lg text-sm font-semibold hover:opacity-90 transition-opacity disabled:opacity-50"
            :disabled="isRunning"
            @click="confirmModalAction"
          >
            {{ isRunning ? '回测中...' : '确认运行回测' }}
          </button>
        </div>
      </template>
    </a-modal>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 10px;
}
</style>
