<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getStrategyDetail, createStrategy, updateStrategy } from '@/api/strategy'
import { previewStrategy, createBacktest, type BacktestParams, type PreviewResult } from '@/api/backtest'
import Icon from '@/components/common/Icon.vue'

const route = useRoute()
const router = useRouter()

const strategyId = computed(() => route.params.id ? Number(route.params.id) : null)
const isNew = computed(() => !strategyId.value)

const strategyName = ref('新建策略')
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

const logs = ref<Array<{ time: string; level: string; message: string }>>([
  { time: '10:00:00', level: 'INFO', message: '策略编辑器已就绪' }
])
const isRunning = ref(false)
const isSaving = ref(false)
const previewResult = ref<PreviewResult | null>(null)
const totalReturn = ref<number | null>(null)
const annualReturn = ref<number | null>(null)
const maxDrawdown = ref<number | null>(null)
const sharpeRatio = ref<number | null>(null)
const winRate = ref<number | null>(null)
const profitLossRatio = ref<number | null>(null)

const frequencyOptions = [
  { label: '日线', value: '1d' },
  { label: '周线', value: '1w' },
  { label: '1分钟', value: '1m' },
  { label: '5分钟', value: '5m' },
  { label: '15分钟', value: '15m' }
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
  
  try {
    const strategy = await getStrategyDetail(strategyId.value)
    strategyName.value = strategy.name
    strategyCode.value = strategy.code || strategyCode.value
    addLog('INFO', `已加载策略: ${strategy.name}`)
  } catch (error) {
    addLog('ERROR', `加载策略失败: ${error}`)
  }
}

async function handleSave() {
  isSaving.value = true
  try {
    const params = {
      name: strategyName.value,
      code: strategyCode.value
    }
    
    if (isNew.value) {
      const result = await createStrategy(params)
      addLog('SUCCESS', `策略已创建，ID: ${result.id}`)
      router.replace(`/backtest/edit/${result.id}`)
    } else {
      await updateStrategy(strategyId.value!, params)
      addLog('SUCCESS', '策略已保存')
    }
  } catch (error) {
    addLog('ERROR', `保存失败: ${error}`)
  } finally {
    isSaving.value = false
  }
}

async function handlePreview() {
  isRunning.value = true
  addLog('INFO', '开始编译检查...')
  
  try {
    const params: BacktestParams = {
      start_date: startDate.value,
      end_date: endDate.value,
      frequency: frequency.value,
      initial_capital: 1000000
    }
    
    const result = await previewStrategy({
      strategy_id: strategyId.value || undefined,
      code: strategyCode.value,
      params
    })
    
    previewResult.value = result
    
    if (result.success) {
      if (result.logs) {
        result.logs.forEach(log => {
          addLog(log.level, log.message)
        })
      }
      
      if (result.summary) {
        totalReturn.value = result.summary.total_return || null
        annualReturn.value = result.summary.annual_return || null
        maxDrawdown.value = result.summary.max_drawdown || null
        sharpeRatio.value = result.summary.sharpe_ratio || null
        winRate.value = result.summary.win_rate || null
        profitLossRatio.value = result.summary.profit_loss_ratio || null
      }
      
      addLog('SUCCESS', '编译运行完成')
    } else {
      addLog('ERROR', result.error || '编译失败')
    }
  } catch (error) {
    addLog('ERROR', `执行失败: ${error}`)
  } finally {
    isRunning.value = false
  }
}

async function handleRunBacktest() {
  if (!strategyId.value) {
    addLog('WARNING', '请先保存策略后再运行回测')
    return
  }
  
  isRunning.value = true
  addLog('INFO', '创建回测任务...')
  
  try {
    const params: BacktestParams = {
      start_date: startDate.value,
      end_date: endDate.value,
      frequency: frequency.value,
      initial_capital: 1000000
    }
    
    const result = await createBacktest(strategyId.value, params)
    addLog('SUCCESS', `回测任务已创建: ID ${result.backtest_id}`)
    
    router.push(`/backtest/detail/${result.backtest_id}`)
  } catch (error) {
    addLog('ERROR', `创建回测失败: ${error}`)
    isRunning.value = false
  }
}

function goBack() {
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
        <span class="text-sm font-medium text-slate-600">策略: {{ strategyName }}</span>
      </div>
      
      <div class="flex items-center gap-3 bg-slate-50 px-3 py-1.5 rounded-md border border-slate-200">
        <div class="flex items-center gap-1.5">
          <label class="text-[11px] text-slate-500 whitespace-nowrap">开始日期</label>
          <input
            v-model="startDate"
            type="date"
            class="bg-transparent border-none p-0 text-xs focus:ring-0 w-24 text-slate-700"
          />
        </div>
        <div class="w-px h-3 bg-slate-300"></div>
        <div class="flex items-center gap-1.5">
          <label class="text-[11px] text-slate-500 whitespace-nowrap">结束日期</label>
          <input
            v-model="endDate"
            type="date"
            class="bg-transparent border-none p-0 text-xs focus:ring-0 w-24 text-slate-700"
          />
        </div>
        <div class="w-px h-3 bg-slate-300"></div>
        <div class="flex items-center gap-1.5">
          <label class="text-[11px] text-slate-500 whitespace-nowrap">数据频率</label>
          <select
            v-model="frequency"
            class="bg-transparent border-none p-0 text-xs focus:ring-0 text-slate-700 cursor-pointer"
          >
            <option v-for="opt in frequencyOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </div>
      </div>
      
      <div class="flex items-center gap-3">
        <button
          class="bg-primary text-white px-5 py-1.5 rounded text-sm font-semibold hover:bg-blue-700 shadow-sm shadow-blue-200 transition-all disabled:opacity-50"
          :disabled="isRunning"
          @click="handleRunBacktest"
        >
          <Icon v-if="isRunning" icon="mdi:loading" class="animate-spin" :size="16" />
          <span v-else>运行回测</span>
        </button>
        <button
          class="border border-slate-200 px-5 py-1.5 rounded text-sm font-medium hover:bg-slate-50 transition-colors disabled:opacity-50"
          :disabled="isSaving"
          @click="handleSave"
        >
          保存
        </button>
      </div>
    </header>

    <main class="flex-1 flex overflow-hidden">
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
              @click="handlePreview"
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
    </main>

    <footer class="h-16 border-t border-slate-200 px-6 flex items-center bg-slate-50 shrink-0">
      <div class="flex items-center space-x-2">
        <span class="text-xs text-slate-500">
          最后更新: {{ new Date().toLocaleString('zh-CN') }}
        </span>
      </div>
    </footer>
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
