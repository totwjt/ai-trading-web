<script setup lang="ts">
import { ref, watch, computed, onMounted, onUnmounted } from 'vue'
import { message } from 'ant-design-vue'
import Icon from '@/components/common/Icon.vue'
import { searchStocks, getWatchlist, addToWatchlistAPI, removeFromWatchlistAPI, type StockSearchResult, type WatchlistItem } from '@/api/trading'
import { useWebSocket } from '@/composables/useWebSocket'

const searchKeyword = ref('')
const searchResults = ref<StockSearchResult[] | null>(null)
const isSearching = ref(false)
const isAddingToWatchlist = ref(false)
const watchlist = ref<WatchlistItem[]>([])
const pushCount = ref(0)
const lastPushTime = ref('')
const tradeMode = ref<'buy' | 'sell'>('buy')

const ws = useWebSocket()
let debounceTimer: ReturnType<typeof setTimeout> | null = null

const activeStock = computed(() => watchlist.value[0])

const loadWatchlist = async () => {
  watchlist.value = await getWatchlist()
}

const debouncedSearch = (keyword: string) => {
  if (debounceTimer) {
    clearTimeout(debounceTimer)
  }

  debounceTimer = setTimeout(async () => {
    if (!keyword.trim()) {
      searchResults.value = null
      return
    }

    isSearching.value = true
    try {
      searchResults.value = await searchStocks(keyword, 20)
    } catch {
      searchResults.value = []
    } finally {
      isSearching.value = false
    }
  }, 300)
}

watch(searchKeyword, (value) => {
  debouncedSearch(value)
})

const isInWatchlist = (tsCode: string) => {
  return watchlist.value.some((item) => item.ts_code === tsCode)
}

const addToWatchlist = async (stock: StockSearchResult) => {
  if (isInWatchlist(stock.ts_code)) {
    message.warning('该股票已在自选列表中')
    return
  }

  isAddingToWatchlist.value = true
  try {
    const success = await addToWatchlistAPI(stock.ts_code, stock.name)
    if (success) {
      message.success('添加自选成功')
      await loadWatchlist()
    }
  } catch (error: any) {
    message.error(error?.message || '添加自选失败')
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
      watchlist.value = watchlist.value.filter((item) => item.ts_code !== tsCode)
    }
  } catch (error: any) {
    message.error(error?.message || '删除失败')
  }
}

let offZixuan: (() => void) | null = null

onMounted(() => {
  loadWatchlist()
  ws.subscribe(['zixuan'])

  offZixuan = ws.onZixuan((data) => {
    if (Array.isArray(data) && data.length > 0) {
      pushCount.value += 1
      lastPushTime.value = new Date().toLocaleTimeString()
      watchlist.value = data as WatchlistItem[]
    }
  })
})

onUnmounted(() => {
  ws.unsubscribe(['zixuan'])
  offZixuan?.()

  if (debounceTimer) {
    clearTimeout(debounceTimer)
  }
})
</script>

<template>
  <div class="h-full min-h-[calc(100vh-48px)] bg-bgMain p-3">
    <div class="h-full flex flex-col gap-3">
      <section class="grid grid-cols-1 2xl:grid-cols-2 gap-3 min-h-[340px]">
        <div class="bg-card rounded-lg border border-border shadow-sm flex flex-col min-h-[340px]">
          <div class="px-3 py-2 border-b border-border bg-bgMain/60 flex items-center justify-between gap-3">
            <div>
              <h2 class="text-sm font-semibold text-textMain">我的自选</h2>
              <p class="text-xxs text-textMute mt-0.5">
                推送 <span class="text-primary font-semibold font-numeric">{{ pushCount }}</span>
                <span v-if="lastPushTime" class="ml-2">最后更新 {{ lastPushTime }}</span>
              </p>
            </div>
            <div class="relative w-56 max-w-full">
              <input
                v-model="searchKeyword"
                type="text"
                placeholder="代码/名称检索"
                class="h-8 w-full rounded border border-border bg-card pl-8 pr-2 text-xs text-textMain placeholder-textMute focus:border-primary focus:outline-none"
              />
              <Icon icon="search" :size="14" class="absolute left-2.5 top-2 text-textMute" />

              <div
                v-if="searchKeyword"
                class="absolute top-9 left-0 right-0 z-20 rounded border border-border bg-card shadow-sm max-h-52 overflow-y-auto"
              >
                <div v-if="isSearching" class="px-3 py-2 text-xs text-textMute">搜索中...</div>
                <div v-else-if="searchResults && searchResults.length === 0" class="px-3 py-2 text-xs text-textMute">未找到匹配股票</div>
                <button
                  v-for="stock in searchResults || []"
                  :key="stock.ts_code"
                  type="button"
                  class="w-full px-3 py-2 text-left hover:bg-primary/5 border-b border-border last:border-b-0 disabled:opacity-50"
                  :disabled="isInWatchlist(stock.ts_code) || isAddingToWatchlist"
                  @click="addToWatchlist(stock)"
                >
                  <div class="flex items-center justify-between">
                    <div class="min-w-0">
                      <p class="text-xs text-textMain truncate">{{ stock.name }}</p>
                      <p class="text-xxs text-textSub font-numeric">{{ stock.ts_code }}</p>
                    </div>
                    <span class="text-xxs" :class="isInWatchlist(stock.ts_code) ? 'text-textMute' : 'text-primary'">
                      {{ isInWatchlist(stock.ts_code) ? '已添加' : '加入自选' }}
                    </span>
                  </div>
                </button>
              </div>
            </div>
          </div>

          <div class="flex-1 overflow-auto">
            <table class="density-table w-full text-xs">
              <thead>
                <tr class="bg-bgMain/70">
                  <th class="text-left text-textSub font-medium">代码</th>
                  <th class="text-left text-textSub font-medium">名称</th>
                  <th class="text-right text-textSub font-medium">收盘</th>
                  <th class="text-right text-textSub font-medium">涨跌</th>
                  <!-- <th class="text-right text-textSub font-medium">幅%</th> -->
                  <th class="text-center text-textSub font-medium">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="stock in watchlist" :key="stock.ts_code" class="hover:bg-primary/5">
                  <td class="text-textMain font-numeric">{{ stock.ts_code }}</td>
                  <td class="text-textMain">{{ stock.name }}</td>
                  <td class="text-right text-textMain font-numeric">{{ (stock.close ?? 0).toFixed(2) }}</td>
                  <td class="text-right font-numeric" :class="(stock.change ?? 0) >= 0 ? 'text-up' : 'text-down'">
                    {{ (stock.change ?? 0).toFixed(2) }}
                  </td>
                  <!-- <td class="text-right font-numeric" :class="(stock.change_pct ?? 0) >= 0 ? 'text-up' : 'text-down'">
                    {{ (stock.change_pct ?? 0).toFixed(2) }}%
                  </td> -->
                  <td class="text-center">
                    <button
                      type="button"
                      class="text-up hover:underline"
                      @click="removeFromWatchlist(stock.ts_code)"
                    >
                      删除
                    </button>
                  </td>
                </tr>
                <tr v-if="watchlist.length === 0">
                  <td colspan="6" class="text-center py-8 text-textMute">暂无自选股票</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="bg-card rounded-lg border border-border shadow-sm p-3 flex flex-col gap-3 min-h-[340px]">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <Icon icon="analytics" :size="16" class="text-primary" />
              <h2 class="text-sm font-semibold text-textMain">快速交易终端</h2>
            </div>
            <div class="flex items-center rounded border border-border p-0.5 bg-bgMain/70 text-xs">
              <button
                type="button"
                class="px-4 py-1 rounded font-medium"
                :class="tradeMode === 'buy' ? 'bg-up text-white' : 'text-textSub'"
                @click="tradeMode = 'buy'"
              >
                买入(B)
              </button>
              <button
                type="button"
                class="px-4 py-1 rounded font-medium"
                :class="tradeMode === 'sell' ? 'bg-down text-white' : 'text-textSub'"
                @click="tradeMode = 'sell'"
              >
                卖出(S)
              </button>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-2 rounded border border-border bg-bgMain/70 p-3 text-xs">
            <div class="space-y-1">
              <label class="text-textSub">证券代码</label>
              <input
                type="text"
                :value="activeStock?.ts_code || ''"
                class="h-8 w-full rounded border border-border bg-card px-2 text-textMain font-numeric"
                readonly
              />
            </div>
            <div class="space-y-1">
              <label class="text-textSub">名称</label>
              <input
                type="text"
                :value="activeStock?.name || ''"
                class="h-8 w-full rounded border border-border bg-card px-2 text-textMain"
                readonly
              />
            </div>
            <div class="space-y-1">
              <label class="text-textSub">委托价格</label>
              <input
                type="number"
                :value="activeStock?.close || 0"
                class="h-8 w-full rounded border border-border bg-card px-2 text-textMain font-numeric"
                readonly
              />
            </div>
            <div class="space-y-1">
              <label class="text-textSub">委托数量</label>
              <input
                type="number"
                placeholder="0"
                class="h-8 w-full rounded border border-border bg-card px-2 text-textMain font-numeric"
              />
            </div>
            <div class="col-span-2 flex items-center gap-2 mt-1">
              <button type="button" class="flex-1 h-7 rounded border border-border bg-card text-textSub">1/4</button>
              <button type="button" class="flex-1 h-7 rounded border border-border bg-card text-textSub">1/3</button>
              <button type="button" class="flex-1 h-7 rounded border border-border bg-card text-textSub">1/2</button>
              <button type="button" class="flex-1 h-7 rounded border border-border bg-card text-textSub">全仓</button>
              <button type="button" class="h-7 px-4 rounded bg-primary text-white font-medium">确认下单</button>
            </div>
          </div>

          <p class="text-xxs text-textMute">
            第一阶段仅完成终端布局与自选联动，委托下单功能下一步接入。
          </p>
        </div>
      </section>

      <section class="grid grid-cols-1 2xl:grid-cols-2 gap-[1px] bg-border rounded-lg overflow-hidden border border-border flex-1 min-h-[300px]">
        <article v-for="index in 4" :key="index" class="bg-card flex flex-col min-h-[180px]">
          <div class="px-3 py-2 bg-bgMain/70 border-b border-border flex items-center justify-between">
            <div class="flex items-center gap-2 text-textSub">
              <Icon icon="mdi:console" :size="14" />
              <span class="text-xxs font-numeric">terminal-node-{{ index }}</span>
            </div>
            <div class="flex items-center gap-1">
              <span class="w-1.5 h-1.5 rounded-full" :class="index === 4 ? 'bg-border' : 'bg-down'" />
              <span class="text-xxs" :class="index === 4 ? 'text-textMute' : 'text-down'">
                {{ index === 4 ? '等待连接' : 'Connected' }}
              </span>
            </div>
          </div>
          <div class="flex-1 p-3 overflow-auto">
            <div v-if="index === 4" class="h-full flex items-center justify-center text-xs text-textMute">
              等待新终端连接...
            </div>
            <table v-else class="w-full text-xs terminal-table">
              <thead>
                <tr>
                  <th>时间</th>
                  <th>代码</th>
                  <th>名称</th>
                  <th class="text-center">方向</th>
                  <th class="text-right">成交价</th>
                  <th class="text-right">成交量</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td class="font-numeric text-textMute">10:4{{ index }}:2{{ index }}</td>
                  <td class="font-numeric text-textSub">{{ index === 1 ? '600519' : index === 2 ? '601318' : '000858' }}</td>
                  <td class="text-textMain">{{ index === 1 ? '贵州茅台' : index === 2 ? '中国平安' : '五粮液' }}</td>
                  <td class="text-center font-medium" :class="index === 3 ? 'text-down' : 'text-up'">{{ index === 3 ? '卖出' : '买入' }}</td>
                  <td class="text-right font-numeric text-textMain">{{ index === 1 ? '1723.40' : index === 2 ? '45.22' : '152.40' }}</td>
                  <td class="text-right font-numeric text-textMain">{{ index === 1 ? '500' : index === 2 ? '5000' : '1200' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>
      </section>
    </div>
  </div>
</template>

<style scoped>
.terminal-table th,
.terminal-table td {
  padding: 4px 6px;
  border-bottom: 1px solid var(--color-border);
}

.terminal-table th {
  color: var(--color-text-sub);
  font-weight: 500;
  text-align: left;
}
</style>
