<script setup lang="ts">
import { ref, computed, onMounted, watch, onUnmounted } from 'vue'
import { getStrategyList } from '@/api/strategy'
import type { StrategyListItem } from '@/api/strategy'
import { toggleStrategy, getStrategySignals } from '@/api/externalStrategy'
import type { StrategySignal } from '@/api/externalStrategy'

const strategies = ref<StrategyListItem[]>([])
const selectedStrategyId = ref<number | null>(null)
const signals = ref<StrategySignal[]>([])
const loadingList = ref(true)
const loadingSignals = ref(false)
const togglingId = ref<number | null>(null)
const error = ref('')

const selectedStrategy = computed(() =>
  strategies.value.find(s => s.id === selectedStrategyId.value) ?? null
)

// Pagination
const signalPage = ref(1)
const signalTotal = ref(0)
const signalPageSize = 20
const signalTotalPages = computed(() => Math.max(Math.ceil(signalTotal.value / signalPageSize) || 1, 1))

// Countdown auto-refresh
const countdown = ref(0)
let countdownTimer: ReturnType<typeof setInterval> | null = null

function startAutoRefresh() {
  stopAutoRefresh()
  if (!selectedStrategy.value?.sta) return
  countdown.value = 15
  countdownTimer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      if (selectedStrategyId.value !== null) {
        fetchSignals(selectedStrategyId.value, signalPage.value)
      }
      countdown.value = 15
    }
  }, 1000)
}

function stopAutoRefresh() {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
  countdown.value = 0
}

async function fetchStrategies() {
  loadingList.value = true
  error.value = ''
  try {
    const result = await getStrategyList({ page_size: 100 })
    strategies.value = result.items
    if (result.items.length > 0 && !selectedStrategyId.value) {
      selectedStrategyId.value = result.items[0].id
    }
  } catch (e: any) {
    error.value = e?.message || '加载策略列表失败'
    strategies.value = []
  } finally {
    loadingList.value = false
  }
}

async function fetchSignals(strategyId: number, page: number = 1) {
  loadingSignals.value = true
  signalPage.value = page
  try {
    const result = await getStrategySignals({
      strategy_id: strategyId,
      page,
      page_size: signalPageSize
    })
    if (result && typeof result === 'object') {
      if (Array.isArray(result.items)) {
        signals.value = result.items
        signalTotal.value = result.total ?? signals.value.length
      } else if (Array.isArray(result)) {
        signals.value = result
        signalTotal.value = result.length
      } else if (result.data && Array.isArray(result.data)) {
        signals.value = result.data
        signalTotal.value = result.total ?? result.data.length
      } else {
        signals.value = []
        signalTotal.value = 0
      }
    } else {
      signals.value = []
      signalTotal.value = 0
    }
  } catch {
    signals.value = []
    signalTotal.value = 0
  } finally {
    loadingSignals.value = false
  }
}

function goToPage(page: number) {
  if (page < 1 || page > signalTotalPages.value || loadingSignals.value) return
  if (selectedStrategyId.value !== null) {
    fetchSignals(selectedStrategyId.value, page)
  }
  countdown.value = 15
}

async function handleToggle(strategy: StrategyListItem) {
  if (togglingId.value !== null) return
  togglingId.value = strategy.id
  const newAction = !strategy.sta
  try {
    await toggleStrategy(strategy.id, newAction)
    strategy.sta = newAction
    if (!newAction) {
      stopAutoRefresh()
    } else {
      startAutoRefresh()
    }
  } catch {
    // toggle failed — keep local state unchanged
  } finally {
    togglingId.value = null
  }
}

function selectStrategy(id: number) {
  selectedStrategyId.value = id
}

watch(selectedStrategyId, (id) => {
  stopAutoRefresh()
  if (id !== null) {
    fetchSignals(id, 1)
  }
})

watch(loadingSignals, (loading) => {
  if (!loading && selectedStrategy.value?.sta) {
    startAutoRefresh()
  }
})

onMounted(() => {
  fetchStrategies()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<template>
  <div class="flex h-[calc(100vh-48px)] bg-bgMain">
    <!-- Left Panel - Strategy List -->
    <aside class="w-72 bg-card border-r border-border flex flex-col shrink-0">
      <div class="px-3 py-2 border-b border-border">
        <h2 class="text-sm font-bold text-textMain">策略列表</h2>
      </div>

      <div v-if="loadingList" class="flex-1 flex items-center justify-center text-xs text-textMute">
        加载中...
      </div>
      <div v-else-if="error" class="flex-1 flex items-center justify-center text-xs text-red-500 px-4 text-center">
        {{ error }}
      </div>
      <div v-else class="flex-1 overflow-y-auto custom-scrollbar">
        <div
          v-for="strategy in strategies"
          :key="strategy.id"
          class="px-3 py-2.5 border-b border-border cursor-pointer transition-colors"
          :class="selectedStrategyId === strategy.id ? 'bg-primary/5 border-l-2 border-l-primary' : 'hover:bg-gray-50'"
          @click="selectStrategy(strategy.id)"
        >
          <div class="flex items-center justify-between mb-1">
            <span
              class="text-xs font-bold text-textMain truncate max-w-[130px]"
              :class="selectedStrategyId === strategy.id ? 'text-primary' : ''"
            >
              {{ strategy.name }}
            </span>
            <span
              class="text-[10px] px-1.5 py-0.5 rounded font-bold whitespace-nowrap"
              :class="strategy.sta ? 'bg-up text-white' : 'bg-gray-400 text-white'"
            >
              {{ strategy.sta ? '运行中' : '已停止' }}
            </span>
          </div>
          <div class="flex items-center justify-between">
            <span
              v-if="strategy.strategy_type"
              class="bg-primary/10 text-primary text-[10px] px-1.5 py-0.5 rounded font-bold"
            >
              {{ strategy.strategy_type }}
            </span>
            <span v-else class="text-[10px] text-textMute">-</span>
            <span class="text-[10px] text-textMute">{{ strategy.updated_at?.slice(0, 10) }}</span>
          </div>
        </div>
      </div>
    </aside>

    <!-- Right Panel -->
    <main class="flex-1 flex flex-col overflow-hidden min-h-0">
      <!-- Strategy Detail Header -->
      <div v-if="selectedStrategy" class="bg-card border-b border-border px-4 py-3 shrink-0">
        <div class="flex items-start justify-between">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <h1 class="text-base font-bold text-textMain truncate">
                {{ selectedStrategy.name }}
              </h1>
              <span
                class="text-[10px] px-1.5 py-0.5 rounded font-bold whitespace-nowrap"
                :class="selectedStrategy.sta ? 'bg-up text-white' : 'bg-gray-400 text-white'"
              >
                {{ selectedStrategy.sta ? '运行中' : '已停止' }}
              </span>
              <span
                v-if="selectedStrategy.strategy_type"
                class="bg-primary/10 text-primary text-[10px] px-1.5 py-0.5 rounded font-bold"
              >
                {{ selectedStrategy.strategy_type }}
              </span>
            </div>
          </div>
          <button
            class="flex items-center gap-1.5 text-xs font-bold px-4 py-2 rounded transition-opacity disabled:opacity-50"
            :class="selectedStrategy.sta
              ? 'bg-orange-500 text-white hover:opacity-90'
              : 'bg-primary text-white hover:opacity-90'"
            :disabled="togglingId === selectedStrategy.id"
            @click="handleToggle(selectedStrategy)"
          >
            <svg v-if="togglingId === selectedStrategy.id" class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <svg v-else class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
              <path v-if="selectedStrategy.sta" d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
              <path v-else d="M8 5v14l11-7z" />
            </svg>
            {{ togglingId === selectedStrategy.id
              ? '操作中...'
              : selectedStrategy.sta ? '停止策略' : '运行策略'
            }}
          </button>
        </div>

        <!-- 策略描述 -->
        <div v-if="selectedStrategy.description" class="mt-2 text-xs text-textSub leading-relaxed">
          {{ selectedStrategy.description }}
        </div>

        <div class="mt-3 flex gap-6 pt-3 border-t border-border">
          <div>
            <span class="text-[10px] font-bold text-textMute uppercase tracking-wider">更新时间 (UPDATED_AT)</span>
            <p class="text-xs text-textSub font-numeric mt-0.5">
              {{ selectedStrategy.updated_at?.slice(0, 19).replace('T', ' ') || '-' }}
            </p>
          </div>
          <div>
            <span class="text-[10px] font-bold text-textMute uppercase tracking-wider">创建时间 (CREATED_AT)</span>
            <p class="text-xs text-textSub font-numeric mt-0.5">
              {{ selectedStrategy.created_at?.slice(0, 19).replace('T', ' ') || '-' }}
            </p>
          </div>
        </div>
      </div>

      <!-- Signals Table -->
      <div class="flex-1 overflow-hidden p-4 min-h-0">
        <div class="bg-card rounded-lg shadow-sm border border-border flex flex-col h-full min-h-0">
          <!-- Table Header -->
          <div class="px-4 py-2.5 border-b border-border flex items-center justify-between shrink-0">
            <div class="flex items-center gap-2">
              <svg class="w-4 h-4 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path d="M13 10V3L4 14h7v7l9-11h-7z" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" />
              </svg>
              <h3 class="text-xs font-bold text-textMain">策略信号</h3>
            </div>
            <div class="flex items-center gap-2 text-xs">
              <!-- 只在运行策略时显示倒计时 -->
              <template v-if="selectedStrategy?.sta">
                <!-- Refresh spinner -->
                <svg
                  v-if="loadingSignals"
                  class="w-3.5 h-3.5 animate-spin text-primary"
                  fill="none" viewBox="0 0 24 24"
                >
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                <!-- Manual refresh -->
                <svg
                  v-else
                  class="w-3.5 h-3.5 cursor-pointer hover:text-primary transition-colors"
                  fill="none" stroke="currentColor" viewBox="0 0 24 24"
                  @click="selectedStrategyId !== null && fetchSignals(selectedStrategyId, signalPage)"
                >
                  <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" />
                </svg>
                <!-- 15s auto-refresh countdown -->
                <span class="flex items-center gap-1 text-textSub">
                  刷新
                  <span class="font-mono font-bold text-primary min-w-[22px] text-center tabular-nums">{{ countdown }}s</span>
                </span>
              </template>
              <!-- 停止策略只显示手动刷新 -->
              <svg
                v-else
                class="w-3.5 h-3.5 cursor-pointer hover:text-primary transition-colors"
                fill="none" stroke="currentColor" viewBox="0 0 24 24"
                @click="selectedStrategyId !== null && fetchSignals(selectedStrategyId, signalPage)"
              >
                <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" />
              </svg>
            </div>
          </div>

          <!-- Table Body -->
          <div class="flex-1 overflow-y-auto min-h-0">
            <div v-if="loadingSignals" class="flex items-center justify-center py-12 text-xs text-textMute">
              加载信号中...
            </div>
            <div v-else-if="signals.length === 0" class="flex items-center justify-center py-12 text-xs text-textMute">
              暂无策略信号数据
            </div>
            <table v-else class="w-full density-table">
              <thead class="sticky top-0 bg-gray-50 z-10">
                <tr>
                  <th class="text-left font-bold text-textMute text-xs py-2 px-3">股票名称</th>
                  <th class="text-left font-bold text-textMute text-xs py-2 px-3">代码</th>
                  <th class="text-left font-bold text-textMute text-xs py-2 px-3">信号类型</th>
                  <th class="text-right font-bold text-textMute text-xs py-2 px-3">触发价格</th>
                  <th class="text-right font-bold text-textMute text-xs py-2 px-3">触发时间</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(signal, index) in signals"
                  :key="index"
                  class="hover:bg-gray-50/50 transition-colors"
                >
                  <td class="py-2 px-3">
                    <span class="font-bold text-textMain text-xs">{{ signal.stock_name || signal.stockName || '-' }}</span>
                  </td>
                  <td class="py-2 px-3">
                    <span class="text-textSub text-xs font-numeric">{{ signal.ts_code || signal.code || '-' }}</span>
                  </td>
                  <td class="py-2 px-3">
                    <span
                      :class="[
                        'text-[10px] px-1.5 py-0.5 rounded font-bold',
                        (signal.signal_type === 'buy' || signal.signalType === 'buy')
                          ? 'bg-up/10 text-up border border-up/30'
                          : 'bg-down/10 text-down border border-down/30'
                      ]"
                    >
                      {{ signal.signal_type === 'buy' || signal.signalType === 'buy' ? '买入' : '卖出' }}
                    </span>
                  </td>
                  <td class="py-2 px-3 text-right">
                    <span class="font-bold font-numeric text-textMain text-xs">
                      {{ (signal.trigger_price ?? signal.triggerPrice ?? signal.price)?.toLocaleString?.('zh-CN', { minimumFractionDigits: 2 }) ?? '-' }}
                    </span>
                  </td>
                  <td class="py-2 px-3 text-right">
                    <span class="text-textSub text-xs font-numeric">{{ signal.trigger_time || signal.triggerTime || signal.created_at || '-' }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Pagination -->
          <div class="px-4 py-2 border-t border-border flex items-center justify-between shrink-0">
            <span class="text-[11px] text-textMute">
              共 {{ signalTotal }} 条
            </span>
            <div class="flex items-center gap-1">
              <button
                class="px-2 py-1 text-[11px] rounded border border-border text-textSub hover:bg-gray-50 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                :disabled="signalPage <= 1 || loadingSignals"
                @click="goToPage(signalPage - 1)"
              >
                上一页
              </button>
              <span class="px-2 text-[11px] text-textMain font-bold">
                {{ signalPage }} / {{ signalTotalPages }}
              </span>
              <button
                class="px-2 py-1 text-[11px] rounded border border-border text-textSub hover:bg-gray-50 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                :disabled="signalPage >= signalTotalPages || loadingSignals"
                @click="goToPage(signalPage + 1)"
              >
                下一页
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>
