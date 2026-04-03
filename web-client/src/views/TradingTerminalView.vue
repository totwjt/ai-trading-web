<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import Icon from '@/components/common/Icon.vue'
import {
  addToWatchlistAPI,
  getUserTerminals,
  getWatchlist,
  removeFromWatchlistAPI,
  searchStocks,
  type StockSearchResult,
  type UserTerminal,
  type WatchlistItem
} from '@/api/trading'
import { useWebSocket } from '@/composables/useWebSocket'

interface TerminalTradeRecord {
  tradeId?: string
  time?: string
  symbol?: string
  name?: string
  side?: string
  price?: number
  qty?: number
  amount?: number
  [key: string]: unknown
}

interface TerminalState {
  userId: string
  terminalId: string
  terminalName: string
  macAddress: string
  accountName: string
  online: boolean
  lastHeartbeatAt: string
  connectedAt: string
  updatedAt: string
  records: TerminalTradeRecord[]
}

interface TerminalEnvelope {
  v?: string
  msgId?: string
  ts?: string
  userId?: string
  terminalId?: string
  eventType?: string
  seq?: number
  data?: Record<string, unknown>
}

const USER_ID = 'u_1001'
const MAX_RECORDS_PER_TERMINAL = 200

const searchKeyword = ref('')
const searchResults = ref<StockSearchResult[] | null>(null)
const isSearching = ref(false)
const isAddingToWatchlist = ref(false)
const watchlist = ref<WatchlistItem[]>([])
const pushCount = ref(0)
const lastPushTime = ref('')
const tradeMode = ref<'buy' | 'sell'>('buy')

const terminals = ref<Record<string, TerminalState>>({})
const terminalSeqMap = ref<Record<string, number>>({})
const controlEventsCount = ref(0)
const controlLastEventTime = ref('')

const ws = useWebSocket()
const controlTopic = 'trading-terminal.control.' + USER_ID

let searchDebounceTimer: ReturnType<typeof setTimeout> | null = null
let offZixuan: (() => void) | null = null
let offControlTopic: (() => void) | null = null
let offTerminalSnapshot: (() => void) | null = null
let offWsConnect: (() => void) | null = null
const terminalTopicOffFns = new Map<string, () => void>()

const activeStock = computed(() => watchlist.value[0])

const terminalList = computed(() => {
  return Object.values(terminals.value).sort((a, b) => {
    if (a.online !== b.online) return a.online ? -1 : 1
    return a.terminalId.localeCompare(b.terminalId)
  })
})

const terminalCount = computed(() => terminalList.value.length)

const terminalTopic = (terminalId: string) => 'trading-terminal.' + USER_ID + '.' + terminalId

const ensureTerminalState = (terminalId: string, terminalName?: string): TerminalState => {
  const current = terminals.value[terminalId]
  if (current) {
    if (terminalName) current.terminalName = terminalName
    return current
  }

  const created: TerminalState = {
    userId: USER_ID,
    terminalId,
    terminalName: terminalName || terminalId,
    macAddress: '',
    accountName: '',
    online: false,
    lastHeartbeatAt: '',
    connectedAt: '',
    updatedAt: '',
    records: []
  }
  terminals.value = {
    ...terminals.value,
    [terminalId]: created
  }
  return created
}

const removeTerminal = (terminalId: string) => {
  const next = { ...terminals.value }
  delete next[terminalId]
  terminals.value = next

  const nextSeq = { ...terminalSeqMap.value }
  delete nextSeq[terminalId]
  terminalSeqMap.value = nextSeq

  const topic = terminalTopic(terminalId)
  ws.unsubscribe([topic])
  const off = terminalTopicOffFns.get(topic)
  if (off) {
    off()
    terminalTopicOffFns.delete(topic)
  }
}

const appendRecord = (terminalId: string, record: TerminalTradeRecord) => {
  const terminal = ensureTerminalState(terminalId)
  terminal.records = [record, ...terminal.records].slice(0, MAX_RECORDS_PER_TERMINAL)
}

const replaceRecords = (terminalId: string, records: TerminalTradeRecord[]) => {
  const terminal = ensureTerminalState(terminalId)
  terminal.records = records.slice(0, MAX_RECORDS_PER_TERMINAL)
}

const updateSeq = (terminalId: string, seq?: number) => {
  if (typeof seq !== 'number') return true
  const last = terminalSeqMap.value[terminalId] ?? -1
  if (seq <= last) return false
  terminalSeqMap.value = {
    ...terminalSeqMap.value,
    [terminalId]: seq
  }
  return true
}

const subscribeTerminalTopic = (terminalId: string) => {
  const topic = terminalTopic(terminalId)
  if (terminalTopicOffFns.has(topic)) return

  ws.subscribe([topic])
  const off = ws.onEvent(topic, (payload) => {
    const envelope = payload as TerminalEnvelope
    const msgTerminalId = envelope.terminalId || terminalId
    if (msgTerminalId !== terminalId) return
    if (!updateSeq(terminalId, envelope.seq)) return

    const terminal = ensureTerminalState(terminalId)
    terminal.updatedAt = envelope.ts || terminal.updatedAt

    if (envelope.eventType === 'trade.record.append') {
      appendRecord(terminalId, (envelope.data || {}) as TerminalTradeRecord)
      return
    }

    if (envelope.eventType === 'trade.record.batch') {
      const records = (envelope.data?.records as TerminalTradeRecord[]) || []
      replaceRecords(terminalId, records)
      return
    }

    if (envelope.eventType === 'terminal.online') {
      terminal.online = true
      return
    }

    if (envelope.eventType === 'terminal.offline') {
      terminal.online = false
    }
  })

  terminalTopicOffFns.set(topic, off)
}

const applySnapshot = (items: Array<Record<string, unknown>>) => {
  items.forEach((item) => {
    const terminalId = String(item.terminalId || '')
    if (!terminalId) return

    const terminal = ensureTerminalState(terminalId, String(item.terminalName || terminalId))
    terminal.online = Boolean(item.online)
    terminal.lastHeartbeatAt = String(item.lastHeartbeatAt || '')
    terminal.connectedAt = String(item.connectedAt || '')
    terminal.updatedAt = String(item.updatedAt || '')

    subscribeTerminalTopic(terminalId)
  })
}

const handleControlEvent = (payload: unknown) => {
  const envelope = payload as TerminalEnvelope
  if (envelope.userId !== USER_ID || !envelope.terminalId) return

  const terminalId = envelope.terminalId
  const terminalName = String(envelope.data?.terminalName || terminalId)
  const terminal = ensureTerminalState(terminalId, terminalName)
  const macAddress = envelope.data?.macAddress || envelope.data?.mac_address
  const accountName = envelope.data?.accountName || envelope.data?.account_name
  if (typeof macAddress === 'string' && macAddress) terminal.macAddress = macAddress
  if (typeof accountName === 'string' && accountName) terminal.accountName = accountName

  controlEventsCount.value += 1
  controlLastEventTime.value = new Date().toLocaleTimeString()

  if (envelope.eventType === 'terminal.added') {
    terminal.updatedAt = envelope.ts || terminal.updatedAt
    subscribeTerminalTopic(terminalId)
    return
  }

  if (envelope.eventType === 'terminal.online') {
    terminal.online = true
    terminal.lastHeartbeatAt = envelope.ts || terminal.lastHeartbeatAt
    terminal.updatedAt = envelope.ts || terminal.updatedAt
    subscribeTerminalTopic(terminalId)
    return
  }

  if (envelope.eventType === 'terminal.offline') {
    terminal.online = false
    terminal.updatedAt = envelope.ts || terminal.updatedAt
    return
  }

  if (envelope.eventType === 'terminal.removed') {
    removeTerminal(terminalId)
  }
}

const requestSnapshot = () => {
  ws.emit('terminal_snapshot_request', { userId: USER_ID })
}

const loadUserTerminals = async () => {
  const items = await getUserTerminals(USER_ID)
  items.forEach((item: UserTerminal) => {
    const terminal = ensureTerminalState(item.terminal_id, item.terminal_name || item.terminal_id)
    terminal.userId = item.uid
    terminal.macAddress = item.mac_address
    terminal.accountName = item.account_name
    terminal.updatedAt = item.updated_at || terminal.updatedAt
    subscribeTerminalTopic(item.terminal_id)
  })
}

const loadWatchlist = async () => {
  watchlist.value = await getWatchlist()
}

const debouncedSearch = (keyword: string) => {
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer)

  searchDebounceTimer = setTimeout(async () => {
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

const isInWatchlist = (tsCode: string) => watchlist.value.some((item) => item.ts_code === tsCode)

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

onMounted(() => {
  loadUserTerminals()
  loadWatchlist()
  ws.subscribe(['zixuan', controlTopic])

  offZixuan = ws.onZixuan((data) => {
    if (Array.isArray(data) && data.length > 0) {
      pushCount.value += 1
      lastPushTime.value = new Date().toLocaleTimeString()
      watchlist.value = data as WatchlistItem[]
    }
  })

  offControlTopic = ws.onEvent(controlTopic, handleControlEvent)

  offTerminalSnapshot = ws.onEvent('terminal_snapshot', (payload) => {
    const snapshot = payload as { userId?: string; terminals?: Array<Record<string, unknown>> }
    if (snapshot.userId !== USER_ID) return
    applySnapshot(snapshot.terminals || [])
  })

  offWsConnect = ws.onConnect(() => {
    ws.subscribe([controlTopic])
    requestSnapshot()
  })

  requestSnapshot()
})

onUnmounted(() => {
  ws.unsubscribe(['zixuan', controlTopic])
  offZixuan?.()
  offControlTopic?.()
  offTerminalSnapshot?.()
  offWsConnect?.()

  terminalTopicOffFns.forEach((off, topic) => {
    ws.unsubscribe([topic])
    off()
  })
  terminalTopicOffFns.clear()

  if (searchDebounceTimer) clearTimeout(searchDebounceTimer)
})
</script>

<template>
  <div class="h-full min-h-[calc(100vh-48px)] bg-bgMain p-3">
    <div class="h-full flex flex-col gap-3">
      <section class="grid grid-cols-1 xl:grid-cols-2 gap-3 min-h-[280px]">
        <div class="bg-card rounded-lg border border-border shadow-sm flex flex-col min-h-[280px]">
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
                  <th class="text-right text-textSub font-medium">幅%</th>
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
                  <td class="text-right font-numeric" :class="(stock.change_pct ?? 0) >= 0 ? 'text-up' : 'text-down'">
                    {{ (stock.change_pct ?? 0).toFixed(2) }}%
                  </td>
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

        <div class="bg-card rounded-lg border border-border shadow-sm p-3 flex flex-col gap-3 min-h-[280px]">
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

          <div class="text-xxs text-textMute flex items-center justify-between">
            <span>UID: <span class="font-numeric">{{ USER_ID }}</span></span>
            <span>终端数: <span class="font-numeric text-primary">{{ terminalCount }}</span></span>
            <span>控制事件: <span class="font-numeric">{{ controlEventsCount }}</span></span>
          </div>
        </div>
      </section>

      <section class="bg-card rounded-lg border border-border shadow-sm p-3 flex flex-col gap-3 flex-1 min-h-[220px]">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <Icon icon="mdi:console-network-outline" :size="16" class="text-primary" />
            <h2 class="text-sm font-semibold text-textMain">终端面板</h2>
          </div>
          <p class="text-xxs text-textMute">
            共 <span class="font-numeric text-primary">{{ terminalCount }}</span> 个终端
          </p>
        </div>

        <div class="grid grid-cols-1 xl:grid-cols-2 gap-3 flex-1 min-h-[180px]">
          <article
            v-for="terminal in terminalList"
            :key="terminal.terminalId"
            class="bg-bgMain/40 rounded-lg border border-border overflow-hidden flex flex-col min-h-[180px]"
          >
            <div class="px-3 py-2 bg-card/70 border-b border-border flex items-center justify-between">
              <div class="min-w-0">
                <div class="flex items-center gap-2 text-textSub min-w-0">
                  <Icon icon="mdi:console" :size="14" />
                  <span class="text-xxs font-numeric truncate">{{ (terminal.macAddress || '-') + ' ' + (terminal.accountName || '-') }}</span>
                </div>
                <p class="text-xxs text-textMute truncate mt-0.5">
                  {{ terminal.terminalName }} ({{ terminal.terminalId }})
                </p>
              </div>
              <div class="flex items-center gap-1">
                <span class="w-1.5 h-1.5 rounded-full" :class="terminal.online ? 'bg-down' : 'bg-border'" />
                <span class="text-xxs" :class="terminal.online ? 'text-down' : 'text-textMute'">
                  {{ terminal.online ? 'Connected' : 'Offline' }}
                </span>
              </div>
            </div>

            <div class="flex-1 p-3 overflow-auto">
              <div v-if="terminal.records.length === 0" class="h-full flex items-center justify-center text-xs text-textMute">
                暂无交易记录
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
                  <tr v-for="(record, idx) in terminal.records" :key="record.tradeId || (terminal.terminalId + '-' + idx)">
                    <td class="font-numeric text-textMute">{{ String(record.time || '-') }}</td>
                    <td class="font-numeric text-textSub">{{ String(record.symbol || '-') }}</td>
                    <td class="text-textMain">{{ String(record.name || '-') }}</td>
                    <td class="text-center font-medium" :class="String(record.side || '').toLowerCase() === 'sell' ? 'text-down' : 'text-up'">
                      {{ String(record.side || '').toLowerCase() === 'sell' ? '卖出' : '买入' }}
                    </td>
                    <td class="text-right font-numeric text-textMain">{{ Number(record.price || 0).toFixed(2) }}</td>
                    <td class="text-right font-numeric text-textMain">{{ Number(record.qty || 0) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </article>

          <article v-if="terminalList.length === 0" class="bg-bgMain/30 rounded-lg border border-dashed border-border flex items-center justify-center min-h-[220px] xl:col-span-2">
            <div class="text-center text-textMute text-xs">
              <p>等待终端注册...</p>
              <p v-if="controlLastEventTime" class="mt-1">最后控制事件: {{ controlLastEventTime }}</p>
            </div>
          </article>
        </div>
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
