<script setup lang="ts">
import { ref, watch, computed, onMounted, onUnmounted } from 'vue'
import { message } from 'ant-design-vue'
import { searchStocks, getTradeRecords, getWatchlist, addToWatchlistAPI, removeFromWatchlistAPI, getStrategyConfig, setStrategySwitch, setBuyThreshold, setSellThreshold, type StockSearchResult, type TradeRecord, type StrategyConfig } from '@/api/trading'
import { useWebSocket } from '@/composables/useWebSocket'
import type { WatchlistItem } from '@/utils/websocket'
import TradingStatus from '@/components/common/TradingStatus.vue'

const searchKeyword = ref('')
const searchResults = ref<StockSearchResult[] | null>(null)
const isSearching = ref(false)
const isAddingToWatchlist = ref(false)
const watchlist = ref<WatchlistItem[]>([])
const tradeRecords = ref<TradeRecord[]>([])
const strategyConfig = ref<StrategyConfig>({
  enabled: false,
  buy_5m: 0,
  sell_5m: 0
})

const strategyEnabled = computed({
  get: () => strategyConfig.value.enabled,
  set: async (val: boolean) => {
    strategyConfig.value.enabled = val
    await setStrategySwitch(val)
  }
})

const buyThreshold = computed({
  get: () => strategyConfig.value.buy_5m,
  set: (val: number) => {
    strategyConfig.value.buy_5m = val
    debouncedSaveBuy()
  }
})

const sellThreshold = computed({
  get: () => strategyConfig.value.sell_5m,
  set: (val: number) => {
    strategyConfig.value.sell_5m = val
    debouncedSaveSell()
  }
})

let buyTimer: ReturnType<typeof setTimeout> | null = null
let sellTimer: ReturnType<typeof setTimeout> | null = null

const debouncedSaveBuy = () => {
  if (buyTimer) clearTimeout(buyTimer)
  buyTimer = setTimeout(async () => {
    await setBuyThreshold(strategyConfig.value.buy_5m)
    message.success('买点涨幅已保存')
  }, 800)
}

const debouncedSaveSell = () => {
  if (sellTimer) clearTimeout(sellTimer)
  sellTimer = setTimeout(async () => {
    await setSellThreshold(strategyConfig.value.sell_5m)
    message.success('卖点跌幅已保存')
  }, 800)
}

const pushCount = ref(0)
const lastPushTime = ref('')

const ws = useWebSocket()

const loadWatchlist = async () => {
  watchlist.value = await getWatchlist()
}

const loadStrategyConfig = async () => {
  try {
    const config = await getStrategyConfig()
    strategyConfig.value = config
  } catch (error) {
    console.error('加载策略配置失败:', error)
  }
}

onMounted(() => {
  loadWatchlist()
  loadTradeRecords()
  loadStrategyConfig()
  ws.subscribe(['zixuan', 'trading'])

  ws.onConnect(() => {
    console.log('[Trading] WebSocket 已连接')
  })

  ws.onError((err) => {
    console.error('[Trading] WebSocket 错误:', err)
  })

  ws.onZixuan((data) => {
    if (data && data.length > 0) {
      pushCount.value++
      lastPushTime.value = new Date().toLocaleTimeString()
      watchlist.value = data as WatchlistItem[]
    }
  })

  ws.onTrading((data) => {
    console.log('[Trading] 收到交易推送:', data)
    if (data && Array.isArray(data) && data.length > 0) {
      const newTrades = data as TradeRecord[]
      tradeRecords.value = [...newTrades, ...tradeRecords.value]
    }
  })
})

onUnmounted(() => {
  ws.unsubscribe(['zixuan', 'trading'])
})

let debounceTimer: ReturnType<typeof setTimeout> | null = null

const debouncedSearch = (keyword: string) => {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(async () => {
    if (!keyword.trim()) {
      searchResults.value = null
      return
    }
    isSearching.value = true
    try {
      searchResults.value = await searchStocks(keyword, 20)
    } catch {
      searchResults.value = null
    } finally {
      isSearching.value = false
    }
  }, 300)
}

watch(searchKeyword, (val) => {
  debouncedSearch(val)
})

const addToWatchlist = async (stock: StockSearchResult) => {
  if (watchlist.value.find(s => s.ts_code === stock.ts_code)) {
    message.warning('该股票已在自选列表中')
    return
  }

  isAddingToWatchlist.value = true
  try {
    const success = await addToWatchlistAPI(stock.ts_code, stock.name)
    if (success) {
      message.success('添加自选成功')
      await loadWatchlist()
    } else {
      message.error('添加自选失败')
    }
  } catch (error: any) {
    message.error(error?.message || '添加自选失败')
    console.error('添加自选失败:', error)
  } finally {
    isAddingToWatchlist.value = false
  }
  searchKeyword.value = ''
  searchResults.value = null
}

const removeFromWatchlist = async (tsCode: string) => {
  try {
    const success = await removeFromWatchlistAPI(tsCode)
    if (success) {
      message.success('删除成功')
      watchlist.value = watchlist.value.filter(s => s.ts_code !== tsCode)
    }
  } catch (error: any) {
    message.error(error?.message || '删除失败')
    console.error('删除自选失败:', error)
  }
}

const isInWatchlist = (tsCode: string) => {
  return watchlist.value.some(s => s.ts_code === tsCode)
}

const loadTradeRecords = async () => {
  tradeRecords.value = await getTradeRecords()
}
</script>

<template>
  <div class="min-h-screen bg-bgMain p-6">
    <div class="max-w-7xl mx-auto">
      <div class="mb-6">
        <h1 class="text-xl font-bold text-textMain">股票交易</h1>
        <p class="text-sm text-textMute">实时买卖股票，执行交易策略</p>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="space-y-6">
          <div class="bg-card rounded-lg shadow-sm border border-gray-100 p-4">
            <h2 class="text-base font-semibold text-textMain mb-4">条件检索</h2>
            <div class="relative">
              <input
                v-model="searchKeyword"
                type="text"
                placeholder="输入股票代码或名称搜索..."
                class="w-full px-3 py-2 border border-border rounded text-sm text-textMain placeholder-textMute focus:outline-none focus:border-primary"
              />
              <div v-if="isSearching" class="absolute right-3 top-2.5">
                <span class="text-xs text-textMute">搜索中...</span>
              </div>
            </div>

            <div class="mt-4">
              <table v-if="searchResults && searchResults.length > 0" class="density-table w-full">
                <thead>
                  <tr class="bg-gray-50">
                    <th class="text-left text-xs font-medium text-textSub">代码</th>
                    <th class="text-left text-xs font-medium text-textSub">名称</th>
                    <th class="text-left text-xs font-medium text-textSub">行业</th>
                    <th class="text-left text-xs font-medium text-textSub">市场</th>
                    <th class="text-center text-xs font-medium text-textSub">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="stock in searchResults" :key="stock.ts_code" class="hover:bg-blue-50/30">
                    <td class="text-xs text-textMain font-numeric">{{ stock.ts_code }}</td>
                    <td class="text-xs text-textMain">{{ stock.name }}</td>
                    <td class="text-xs text-textSub">{{ stock.industry || '-' }}</td>
                    <td class="text-xs text-textSub">{{ stock.market || '-' }}</td>
                    <td class="text-center">
                      <button
                        v-if="!isInWatchlist(stock.ts_code)"
                        @click="addToWatchlist(stock)"
                        class="text-xs text-primary hover:underline"
                      >
                        添加自选
                      </button>
                      <span v-else class="text-xs text-textMute">已添加</span>
                    </td>
                  </tr>
                </tbody>
              </table>
              <div v-else-if="searchResults === null && searchKeyword" class="text-center py-8 text-textMute text-sm">
                输入关键词搜索股票
              </div>
              <div v-else class="text-center py-8 text-textMute text-sm">
                输入关键词搜索股票
              </div>
            </div>
          </div>

            <div class="bg-card rounded-lg shadow-sm border border-gray-100 p-4">
            <div class="flex justify-between items-center mb-4">
              <h2 class="text-base font-semibold text-textMain">我的自选</h2>
              <div class="text-xs text-textMute">
                推送次数: <span class="text-primary font-bold">{{ pushCount }}</span>
                <span v-if="lastPushTime" class="ml-2">最后: {{ lastPushTime }}</span>
              </div>
            </div>
            <div v-if="watchlist.length === 0" class="text-center py-8 text-textMute text-sm">
              暂无自选股票
            </div>
            <table v-else class="density-table w-full">
              <thead>
                <tr class="bg-gray-50">
                  <th class="text-left text-xs font-medium text-textSub">代码</th>
                  <th class="text-left text-xs font-medium text-textSub">名称</th>
                  <th class="text-right text-xs font-medium text-textSub">收盘价</th>
                  <th class="text-right text-xs font-medium text-textSub">涨跌额</th>
                  <th class="text-right text-xs font-medium text-textSub">涨跌幅</th>
                  <th class="text-center text-xs font-medium text-textSub">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="stock in watchlist" :key="stock.ts_code" class="hover:bg-blue-50/30">
                  <td class="text-xs text-textMain font-numeric">{{ stock.ts_code }}</td>
                  <td class="text-xs text-textMain">{{ stock.name }}</td>
                  <td class="text-xs text-textMain font-numeric text-right">{{ stock.close?.toFixed(2) }}</td>
                  <td class="text-xs font-numeric text-right" :class="(stock.change ?? 0) >= 0 ? 'text-up' : 'text-down'">
                    {{ (stock.change ?? 0).toFixed(2) }}
                  </td>
                  <td class="text-xs font-numeric text-right" :class="(stock.change_pct ?? 0) >= 0 ? 'text-up' : 'text-down'">
                    {{ (stock.change_pct ?? 0).toFixed(2) }}%
                  </td>
                  <td class="text-center">
                    <button
                      @click="removeFromWatchlist(stock.ts_code)"
                      class="text-xs text-up hover:underline"
                    >
                      删除
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="space-y-6">
          <div class="bg-card rounded-lg shadow-sm border border-gray-100 p-4">
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-base font-semibold text-textMain">策略配置</h2>
              <label class="flex items-center cursor-pointer">
                <span class="mr-2 text-sm text-textSub">启用策略</span>
                <div class="relative">
                  <input type="checkbox" v-model="strategyEnabled" class="sr-only" />
                  <div class="toggle-bg" :class="strategyEnabled ? 'bg-primary' : 'bg-gray-200'"></div>
                  <div class="toggle-dot absolute left-0.5 top-0.5 bg-white w-4 h-4 rounded-full transition" :class="strategyEnabled ? 'translate-x-4' : ''"></div>
                </div>
              </label>
            </div>

            <div class="space-y-4">
              <div>
                <div class="flex justify-between mb-2">
                  <span class="text-sm text-textSub">买点涨幅</span>
                  <span class="text-sm text-textMain font-numeric">{{ buyThreshold }}%</span>
                </div>
                <input
                  type="range"
                  v-model.number="buyThreshold"
                  min="0"
                  max="10"
                  step="0.1"
                  class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                />
              </div>

              <div>
                <div class="flex justify-between mb-2">
                  <span class="text-sm text-textSub">卖点跌幅</span>
                  <span class="text-sm text-textMain font-numeric">{{ sellThreshold }}%</span>
                </div>
                <input
                  type="range"
                  v-model.number="sellThreshold"
                  min="0"
                  max="20"
                  step="0.1"
                  class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                />
              </div>
            </div>
          </div>

          <div class="bg-card rounded-lg shadow-sm border border-gray-100 p-4">
            <div class="flex justify-between items-center mb-4">
              <h2 class="text-base font-semibold text-textMain">交易记录</h2>
              <TradingStatus />
            </div>
            <div v-if="tradeRecords.length === 0" class="text-center py-8 text-textMute text-sm">
              暂无交易记录
            </div>
            <div v-else class="overflow-x-auto max-h-[300px] overflow-y-auto">
              <table class="density-table w-full">
                <thead>
                  <tr class="bg-gray-50">
                    <th class="text-left text-xs font-medium text-textSub">时间</th>
                    <th class="text-left text-xs font-medium text-textSub">代码</th>
                    <th class="text-left text-xs font-medium text-textSub">名称</th>
                    <th class="text-center text-xs font-medium text-textSub">方向</th>
                    <th class="text-right text-xs font-medium text-textSub">价格</th>
                    <th class="text-right text-xs font-medium text-textSub">数量</th>
                    <th class="text-right text-xs font-medium text-textSub">金额</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="record in tradeRecords" :key="record.id" class="hover:bg-blue-50/30">
                    <td class="text-xs text-textMute font-numeric">{{ record.time }}</td>
                    <td class="text-xs text-textMain font-numeric">{{ record.ts_code }}</td>
                    <td class="text-xs text-textMain">{{ record.name }}</td>
                    <td class="text-center">
                      <span
                        :class="record.direction === 'buy' ? 'text-up' : 'text-down'"
                        class="text-xs font-medium"
                      >
                        {{ record.direction === 'buy' ? '买入' : '卖出' }}
                      </span>
                    </td>
                    <td class="text-xs text-textMain font-numeric text-right">{{ record.price.toFixed(2) }}</td>
                    <td class="text-xs text-textMain font-numeric text-right">{{ record.quantity }}</td>
                    <td class="text-xs text-textMain font-numeric text-right">{{ record.amount.toFixed(2) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.toggle-bg {
  width: 40px;
  height: 22px;
  border-radius: 11px;
  transition: background-color 0.2s;
}
.toggle-dot {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  transition: transform 0.2s;
}
</style>