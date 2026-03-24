<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { searchStocks, getTradeRecords, getWatchlist, addToWatchlistAPI, removeFromWatchlistAPI, type StockSearchResult, type TradeRecord, type WatchlistItem } from '@/api/trading'

const searchKeyword = ref('')
const searchResults = ref<StockSearchResult[] | null>(null)
const isSearching = ref(false)
const watchlist = ref<WatchlistItem[]>([])
const tradeRecords = ref<TradeRecord[]>([])
const strategyEnabled = ref(false)
const riseSpeedMin = ref(0)
const riseSpeedMax = ref(5)

const loadWatchlist = async () => {
  watchlist.value = await getWatchlist()
}

onMounted(() => {
  loadWatchlist()
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
  if (!watchlist.value.find(s => s.ts_code === stock.ts_code)) {
    await addToWatchlistAPI(stock.ts_code, stock.name)
    await loadWatchlist()
  }
  searchKeyword.value = ''
  searchResults.value = null
}

const removeFromWatchlist = async (tsCode: string) => {
  await removeFromWatchlistAPI(tsCode)
  watchlist.value = watchlist.value.filter(s => s.ts_code !== tsCode)
}

const isInWatchlist = (tsCode: string) => {
  return watchlist.value.some(s => s.ts_code === tsCode)
}

const loadTradeRecords = async () => {
  tradeRecords.value = await getTradeRecords()
}

loadTradeRecords()
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
            <h2 class="text-base font-semibold text-textMain mb-4">我的自选</h2>
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
                  <td class="text-xs font-numeric text-right" :class="stock.change >= 0 ? 'text-up' : 'text-down'">
                    {{ stock.change?.toFixed(2) }}
                  </td>
                  <td class="text-xs font-numeric text-right" :class="stock.change_pct >= 0 ? 'text-up' : 'text-down'">
                    {{ stock.change_pct?.toFixed(2) }}%
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
                  <span class="text-sm text-textSub">涨速范围</span>
                  <span class="text-sm text-textMain font-numeric">{{ riseSpeedMin }}% - {{ riseSpeedMax }}%</span>
                </div>
                <div class="flex gap-4 items-center">
                  <input
                    type="range"
                    v-model.number="riseSpeedMin"
                    min="0"
                    max="10"
                    step="0.5"
                    class="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                  />
                  <input
                    type="range"
                    v-model.number="riseSpeedMax"
                    min="0"
                    max="10"
                    step="0.5"
                    class="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                  />
                </div>
              </div>
            </div>
          </div>

          <div class="bg-card rounded-lg shadow-sm border border-gray-100 p-4">
            <h2 class="text-base font-semibold text-textMain mb-4">交易记录</h2>
            <div v-if="tradeRecords.length === 0" class="text-center py-8 text-textMute text-sm">
              暂无交易记录
            </div>
            <div v-else class="overflow-x-auto">
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