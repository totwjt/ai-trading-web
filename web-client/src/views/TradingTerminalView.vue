<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { message, Modal } from 'ant-design-vue'
import Icon from '@/components/common/Icon.vue'
import { useUserStore } from '@/stores/userStore'
import {
  addToWatchlistAPI,
  createPendingOrderAPI,
  createOrderAPI,
  getPendingOrderConfigAPI,
  getPendingOrdersAPI,
  getTradeRecordsByMachine,
  getUserTerminals,
  getWatchlist,
  removeFromWatchlistAPI,
  removePendingOrderAPI,
  searchStocks,
  updateTerminalNameAPI,
  updatePendingOrderAPI,
  type MachineTradeRecord,
  type PendingOrderConfig,
  type PendingOrderItem,
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
  connected: boolean
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

const MAX_RECORDS_PER_TERMINAL = 200
const ACTION_COOLDOWN_MS = 1200
const userStore = useUserStore()
const currentUid = computed(() => userStore.uid.trim())

const searchKeyword = ref('')
const searchResults = ref<StockSearchResult[] | null>(null)
const isSearching = ref(false)
const isAddingToWatchlist = ref(false)
const watchlist = ref<WatchlistItem[]>([])
const pushCount = ref(0)
const lastPushTime = ref('')
const tradeMode = ref<'buy' | 'sell'>('buy')
const orderStockCode = ref('')
const orderStockName = ref('')
const orderPriceValue = ref<number | null>(null)
const orderQuantity = ref<number>(100)
const selectedPositionLevel = ref<number | null>(null)
const isSubmittingOrder = ref(false)
const orderSearchResults = ref<StockSearchResult[] | null>(null)
const isOrderSearching = ref(false)
const suppressOrderSearch = ref(false)
const pendingDrawerOpen = ref(false)
const pendingOrders = ref<PendingOrderItem[]>([])
const pendingTimeMap = ref<Record<number, string>>({})
const isPendingLoading = ref(false)
const isPendingSaving = ref(false)
const pendingConfig = ref<PendingOrderConfig>({
  uid: '',
  enabled: true,
  default_delay_minutes: 10,
  auto_submit: false
})
const pendingOrderColumns = [
  { title: '股票代码', dataIndex: 'stock_code', key: 'stock_code', width: 104 },
  { title: '股票名称', dataIndex: 'stock_name', key: 'stock_name', width: 112 },
  { title: '挂单时间', dataIndex: 'scheduled_at', key: 'scheduled_at' },
  { title: '操作', key: 'actions', width: 72, align: 'center' as const }
]

const terminals = ref<Record<string, TerminalState>>({})
const terminalSeqMap = ref<Record<string, number>>({})
const terminalHistoryLoaded = ref<Record<string, boolean>>({})
const terminalHistoryLoading = ref<Record<string, boolean>>({})
const controlEventsCount = ref(0)
const editingTerminalId = ref<string>('')
const editingTerminalName = ref<string>('')
const terminalRenameTimers = new Map<string, ReturnType<typeof setTimeout>>()
const actionLastTriggerAt = new Map<string, number>()

const ws = useWebSocket()
const controlTopic = computed(() => (currentUid.value ? 'trading-terminal.control.' + currentUid.value : ''))

let searchDebounceTimer: ReturnType<typeof setTimeout> | null = null
let orderSearchDebounceTimer: ReturnType<typeof setTimeout> | null = null
let offZixuan: (() => void) | null = null
let offControlTopic: (() => void) | null = null
let offTerminalSnapshot: (() => void) | null = null
let offWsConnect: (() => void) | null = null
const terminalTopicOffFns = new Map<string, () => void>()

const terminalList = computed(() => {
  return Object.values(terminals.value).sort((a, b) => {
    if (a.online !== b.online) return a.online ? -1 : 1
    return a.terminalId.localeCompare(b.terminalId)
  })
})

const terminalCount = computed(() => terminalList.value.length)

const terminalTopic = (uid: string, terminalId: string) => 'trading-terminal.' + uid + '.' + terminalId

const allowSubmitAction = (actionKey: string, cooldownMs = ACTION_COOLDOWN_MS) => {
  const now = Date.now()
  const last = actionLastTriggerAt.get(actionKey) || 0
  if (now - last < cooldownMs) {
    message.warning('操作过于频繁，请稍后重试')
    return false
  }
  actionLastTriggerAt.set(actionKey, now)
  return true
}

const ensureTerminalState = (terminalId: string, terminalName?: string): TerminalState => {
  const current = terminals.value[terminalId]
  if (current) {
    if (terminalName) current.terminalName = terminalName
    return current
  }

  const created: TerminalState = {
    userId: currentUid.value,
    terminalId,
    terminalName: terminalName || terminalId,
    macAddress: '',
    accountName: '',
    connected: false,
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

  const nextLoaded = { ...terminalHistoryLoaded.value }
  delete nextLoaded[terminalId]
  terminalHistoryLoaded.value = nextLoaded

  const nextLoading = { ...terminalHistoryLoading.value }
  delete nextLoading[terminalId]
  terminalHistoryLoading.value = nextLoading
  if (editingTerminalId.value === terminalId) {
    editingTerminalId.value = ''
    editingTerminalName.value = ''
  }
  const timer = terminalRenameTimers.get(terminalId)
  if (timer) {
    clearTimeout(timer)
    terminalRenameTimers.delete(terminalId)
  }

  const uid = currentUid.value
  if (!uid) return
  const topic = terminalTopic(uid, terminalId)
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
  const uid = currentUid.value
  if (!uid) return
  const topic = terminalTopic(uid, terminalId)
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
      appendRecord(terminalId, normalizeTradeRecord(envelope.data || {}))
      return
    }

    if (envelope.eventType === 'trade.record.batch') {
      const records = (envelope.data?.records as TerminalTradeRecord[]) || []
      replaceRecords(terminalId, records.map((item) => normalizeTradeRecord(item)))
      return
    }

    if (envelope.eventType === 'terminal.online') {
      terminal.online = true
      return
    }

    if (envelope.eventType === 'terminal.offline') {
      terminal.online = false
      return
    }

    if (envelope.eventType === 'terminal.connected') {
      terminal.connected = true
      return
    }

    if (envelope.eventType === 'terminal.disconnected') {
      terminal.connected = false
      terminal.online = false
    }
  })

  terminalTopicOffFns.set(topic, off)
}

const toNumber = (value: unknown, fallback = 0): number => {
  const num = Number(value)
  return Number.isFinite(num) ? num : fallback
}

const normalizeSide = (value: unknown): string => {
  const raw = String(value || '').toLowerCase()
  if (!raw) return 'buy'
  if (raw.includes('sell') || raw.includes('卖') || raw.includes('short')) return 'sell'
  return 'buy'
}

const normalizeTradeRecord = (item: Record<string, unknown>): TerminalTradeRecord => {
  const symbol = String(item.symbol || item.stock_code || item.ts_code || item.code || '').trim()
  const name = String(
    item.name ||
    item.stock_name ||
    item.stockName ||
    item.security_name ||
    item.securityName ||
    item.remark ||
    symbol
  ).trim()

  const qty = toNumber(item.qty ?? item.quantity, 0)
  const price = toNumber(item.price ?? item.deal_price, 0)
  const amount = toNumber(item.amount, Number((price * qty).toFixed(2)))

  return {
    tradeId: String(item.tradeId || item.trade_id || item.id || ''),
    time: String(item.time || item.trade_time || item.ts || item.timestamp || ''),
    symbol,
    name,
    side: normalizeSide(item.side ?? item.direction ?? item.trade_type),
    price,
    qty,
    amount
  }
}

const mapMachineRecordsToTerminalRecords = (items: MachineTradeRecord[]): TerminalTradeRecord[] => {
  const mapped = items.map((item) => normalizeTradeRecord(item as unknown as Record<string, unknown>))

  mapped.sort((a, b) => String(b.time || '').localeCompare(String(a.time || '')))
  return mapped.slice(0, MAX_RECORDS_PER_TERMINAL)
}

const initTerminalRecordsByMachine = async (terminalId: string, macAddress?: string) => {
  const mac = String(macAddress || '').trim()
  if (!terminalId || !mac) return
  if (terminalHistoryLoaded.value[terminalId] || terminalHistoryLoading.value[terminalId]) return

  terminalHistoryLoading.value = {
    ...terminalHistoryLoading.value,
    [terminalId]: true
  }
  try {
    const rows = await getTradeRecordsByMachine(mac)
    replaceRecords(terminalId, mapMachineRecordsToTerminalRecords(rows))
    terminalHistoryLoaded.value = {
      ...terminalHistoryLoaded.value,
      [terminalId]: true
    }
  } catch (error) {
    console.warn('[TradingTerminal] init records by machine failed', terminalId, mac, error)
  } finally {
    const next = { ...terminalHistoryLoading.value }
    delete next[terminalId]
    terminalHistoryLoading.value = next
  }
}

const applySnapshot = (items: Array<Record<string, unknown>>) => {
  items.forEach((item) => {
    const terminalId = String(item.terminalId || '')
    if (!terminalId) return

    const terminal = ensureTerminalState(terminalId, String(item.terminalName || terminalId))
    const macAddress = String(item.macAddress || item.mac_address || '').trim()
    const accountName = String(item.accountName || item.account_name || '').trim()
    if (macAddress) terminal.macAddress = macAddress
    if (accountName) terminal.accountName = accountName
    terminal.connected = Boolean(item.connected)
    terminal.online = terminal.connected ? Boolean(item.online) : false
    terminal.lastHeartbeatAt = String(item.lastHeartbeatAt || '')
    terminal.connectedAt = String(item.connectedAt || '')
    terminal.updatedAt = String(item.updatedAt || '')

    subscribeTerminalTopic(terminalId)
    void initTerminalRecordsByMachine(terminalId, terminal.macAddress)
  })
}

const loadUserTerminals = async (uid: string) => {
  if (!uid) return
  const items = await getUserTerminals(uid)
  items.forEach((item: UserTerminal) => {
    const terminal = ensureTerminalState(item.terminal_id, item.terminal_name || item.terminal_id)
    terminal.userId = item.uid
    terminal.macAddress = item.mac_address
    terminal.accountName = item.account_name
    terminal.connected = false
    terminal.online = false
    terminal.updatedAt = item.updated_at || terminal.updatedAt
    subscribeTerminalTopic(item.terminal_id)
    void initTerminalRecordsByMachine(item.terminal_id, terminal.macAddress)
  })
}

const handleControlEvent = (payload: unknown) => {
  const envelope = payload as TerminalEnvelope
  if (envelope.userId !== currentUid.value || !envelope.terminalId) return

  const terminalId = envelope.terminalId
  const terminalName = String(envelope.data?.terminalName || terminalId)
  const terminal = ensureTerminalState(terminalId, terminalName)
  const macAddress = envelope.data?.macAddress || envelope.data?.mac_address
  const accountName = envelope.data?.accountName || envelope.data?.account_name
  if (typeof macAddress === 'string' && macAddress) terminal.macAddress = macAddress
  if (typeof accountName === 'string' && accountName) terminal.accountName = accountName

  controlEventsCount.value += 1

  if (envelope.eventType === 'terminal.added') {
    terminal.updatedAt = envelope.ts || terminal.updatedAt
    subscribeTerminalTopic(terminalId)
    void initTerminalRecordsByMachine(terminalId, terminal.macAddress)
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

  if (envelope.eventType === 'terminal.connected') {
    terminal.connected = true
    terminal.updatedAt = envelope.ts || terminal.updatedAt
    return
  }

  if (envelope.eventType === 'terminal.disconnected') {
    terminal.connected = false
    terminal.online = false
    terminal.updatedAt = envelope.ts || terminal.updatedAt
    return
  }

  if (envelope.eventType === 'terminal.removed') {
    removeTerminal(terminalId)
  }
}

const requestSnapshot = () => {
  if (!currentUid.value) return
  ws.emit('terminal_snapshot_request', { userId: currentUid.value })
}

const beginEditTerminalName = (terminalId: string) => {
  const terminal = terminals.value[terminalId]
  if (!terminal) return
  editingTerminalId.value = terminalId
  editingTerminalName.value = terminal.terminalName || terminalId
}

const cancelEditTerminalName = () => {
  editingTerminalId.value = ''
  editingTerminalName.value = ''
}

const applyRenameLocal = (terminalId: string, nextName: string) => {
  const terminal = terminals.value[terminalId]
  if (!terminal) return
  terminal.terminalName = nextName
}

const commitTerminalNameDebounced = (terminalId: string) => {
  const terminal = terminals.value[terminalId]
  if (!terminal) return
  const nextName = editingTerminalName.value.trim()
  if (!nextName || nextName === terminal.terminalName) return

  const prevTimer = terminalRenameTimers.get(terminalId)
  if (prevTimer) clearTimeout(prevTimer)

  const timer = setTimeout(async () => {
    try {
      await updateTerminalNameAPI({
        uid: currentUid.value,
        terminal_id: terminal.terminalId,
        mac_address: terminal.macAddress,
        terminal_name: nextName
      })
      applyRenameLocal(terminalId, nextName)
    } catch (error: any) {
      message.error(error?.message || '终端名称更新失败')
    } finally {
      terminalRenameTimers.delete(terminalId)
    }
  }, 450)

  terminalRenameTimers.set(terminalId, timer)
}

const finishEditTerminalName = (terminalId: string) => {
  commitTerminalNameDebounced(terminalId)
  cancelEditTerminalName()
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

watch(orderStockCode, (value) => {
  if (suppressOrderSearch.value) return
  orderPriceValue.value = null
  debouncedOrderSearch(value)
})

const isInWatchlist = (tsCode: string) => watchlist.value.some((item) => item.ts_code === tsCode)

const addToWatchlist = async (stock: StockSearchResult) => {
  if (!allowSubmitAction('watchlist-add-' + stock.ts_code)) return

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
  if (!allowSubmitAction('watchlist-remove-' + tsCode)) return

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

const normalizeStockCode = (code: string) => code.trim().toUpperCase()

const pad2 = (value: number) => String(value).padStart(2, '0')

const toDateTimeInputValue = (value: string): string => {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return [
    date.getFullYear(),
    '-',
    pad2(date.getMonth() + 1),
    '-',
    pad2(date.getDate()),
    'T',
    pad2(date.getHours()),
    ':',
    pad2(date.getMinutes())
  ].join('')
}

const toIsoFromDateTimeInput = (value: string): string => {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return [
    date.getFullYear(),
    '-',
    pad2(date.getMonth() + 1),
    '-',
    pad2(date.getDate()),
    'T',
    pad2(date.getHours()),
    ':',
    pad2(date.getMinutes()),
    ':00'
  ].join('')
}

const defaultPendingTimeInput = () => {
  const now = new Date()
  now.setHours(21, 0, 0, 0)
  return [
    now.getFullYear(),
    '-',
    pad2(now.getMonth() + 1),
    '-',
    pad2(now.getDate()),
    'T',
    pad2(now.getHours()),
    ':',
    pad2(now.getMinutes())
  ].join('')
}

const syncPendingTimeMap = (items: PendingOrderItem[]) => {
  const map: Record<number, string> = {}
  items.forEach((item) => {
    map[item.id] = toDateTimeInputValue(item.scheduled_at)
  })
  pendingTimeMap.value = map
}

const loadPendingConfig = async (uid: string) => {
  if (!uid) return
  try {
    pendingConfig.value = await getPendingOrderConfigAPI(uid)
  } catch (error: any) {
    console.warn('[TradingTerminal] load pending config failed', error)
  }
}

const loadPendingOrders = async (uid: string) => {
  if (!uid) {
    pendingOrders.value = []
    pendingTimeMap.value = {}
    return
  }
  isPendingLoading.value = true
  try {
    const items = await getPendingOrdersAPI(uid)
    pendingOrders.value = items
    syncPendingTimeMap(items)
  } catch (error: any) {
    message.error(error?.message || '获取挂单列表失败')
  } finally {
    isPendingLoading.value = false
  }
}

const addPendingOrder = async (stockCodeRaw: string, stockNameRaw: string) => {
  const stockCodeKey = normalizeStockCode(stockCodeRaw)
  if (!allowSubmitAction('pending-add-' + stockCodeKey)) return

  const uid = currentUid.value
  const stockCode = stockCodeKey
  const stockName = String(stockNameRaw || '').trim()

  if (!uid) {
    message.warning('UID 缺失，无法挂单')
    return
  }
  if (!stockCode || !stockName) {
    message.warning('股票代码或名称缺失，无法挂单')
    return
  }

  const scheduledInput = defaultPendingTimeInput()
  const scheduledAt = toIsoFromDateTimeInput(scheduledInput)
  if (!scheduledAt) {
    message.warning('挂单时间无效')
    return
  }

  isPendingSaving.value = true
  try {
    const created = await createPendingOrderAPI({
      uid,
      stock_code: stockCode,
      stock_name: stockName,
      scheduled_at: scheduledAt
    })
    pendingOrders.value = [created, ...pendingOrders.value]
    pendingTimeMap.value = {
      ...pendingTimeMap.value,
      [created.id]: toDateTimeInputValue(created.scheduled_at)
    }
    pendingDrawerOpen.value = true
    message.success('已加入挂单列表')
  } catch (error: any) {
    message.error(error?.message || '新增挂单失败')
  } finally {
    isPendingSaving.value = false
  }
}

const addPendingFromWatchlist = async (stock: WatchlistItem) => {
  await addPendingOrder(stock.ts_code || '', stock.name || '')
}

const onPendingTimeChange = async (item: PendingOrderItem) => {
  if (!allowSubmitAction('pending-update-' + item.id)) return

  const timeInput = pendingTimeMap.value[item.id] || ''
  const scheduledAt = toIsoFromDateTimeInput(timeInput)
  if (!scheduledAt) {
    message.warning('请选择有效挂单时间')
    pendingTimeMap.value = {
      ...pendingTimeMap.value,
      [item.id]: toDateTimeInputValue(item.scheduled_at)
    }
    return
  }

  if (scheduledAt === item.scheduled_at) {
    return
  }

  isPendingSaving.value = true
  try {
    await updatePendingOrderAPI(item.id, { scheduled_at: scheduledAt })
    pendingOrders.value = pendingOrders.value.map((row) => (
      row.id === item.id
        ? {
          ...row,
          scheduled_at: scheduledAt
        }
        : row
    ))
    message.success('挂单时间已更新')
  } catch (error: any) {
    message.error(error?.message || '更新挂单失败')
    pendingTimeMap.value = {
      ...pendingTimeMap.value,
      [item.id]: toDateTimeInputValue(item.scheduled_at)
    }
  } finally {
    isPendingSaving.value = false
  }
}

const removePendingOrder = async (id: number) => {
  if (!allowSubmitAction('pending-remove-' + id)) return

  isPendingSaving.value = true
  try {
    await removePendingOrderAPI(id)
    pendingOrders.value = pendingOrders.value.filter((item) => item.id !== id)
    const next = { ...pendingTimeMap.value }
    delete next[id]
    pendingTimeMap.value = next
    message.success('挂单已删除')
  } catch (error: any) {
    message.error(error?.message || '删除挂单失败')
  } finally {
    isPendingSaving.value = false
  }
}

const debouncedOrderSearch = (keyword: string) => {
  if (orderSearchDebounceTimer) clearTimeout(orderSearchDebounceTimer)

  orderSearchDebounceTimer = setTimeout(async () => {
    if (!keyword.trim()) {
      orderSearchResults.value = null
      orderStockName.value = ''
      return
    }

    isOrderSearching.value = true
    try {
      orderSearchResults.value = await searchStocks(keyword, 20)
    } catch {
      orderSearchResults.value = []
    } finally {
      isOrderSearching.value = false
    }
  }, 300)
}

const choosePositionLevel = (positionLevel: number) => {
  selectedPositionLevel.value = positionLevel
}

const selectOrderStock = (stock: StockSearchResult) => {
  suppressOrderSearch.value = true
  orderStockCode.value = stock.ts_code
  orderStockName.value = stock.name
  orderPriceValue.value = null
  orderSearchResults.value = null
  setTimeout(() => {
    suppressOrderSearch.value = false
  }, 0)
}

const quickSubmitFromWatchlist = async (stock: WatchlistItem) => {
  if (!allowSubmitAction('order-quick-submit-' + String(stock.ts_code || ''))) return

  const stockCode = normalizeStockCode(stock.ts_code || '')
  const stockName = String(stock.name || '').trim()
  const price = Number(stock.close ?? 0)

  if (!stockCode || !stockName) {
    message.warning('该自选股票缺少代码或名称，无法下单')
    return
  }
  if (!Number.isFinite(price) || price <= 0) {
    message.warning('该自选股票价格无效，无法一键下单')
    return
  }

  suppressOrderSearch.value = true
  orderStockCode.value = stockCode
  orderStockName.value = stockName
  orderPriceValue.value = Number(price.toFixed(2))
  orderSearchResults.value = null
  setTimeout(() => {
    suppressOrderSearch.value = false
  }, 0)

  await submitOrder()
}

const submitOrder = async (positionLevel?: number) => {
  if (!allowSubmitAction('order-submit')) return

  const stockCode = normalizeStockCode(orderStockCode.value)
  const stockName = String(orderStockName.value || '').trim() || stockCode
  const price = Number(orderPriceValue.value || 0)
  const quantity = Number(orderQuantity.value || 0)

  if (!stockCode) {
    message.warning('请先输入并选择证券代码')
    return
  }

  if (!Number.isFinite(price) || price <= 0) {
    message.warning('请输入有效委托价格')
    return
  }

  if (!Number.isInteger(quantity) || quantity < 100) {
    message.warning('委托数量最小为 100')
    return
  }

  isSubmittingOrder.value = true
  try {
    const validPositionLevel = typeof positionLevel === 'number' ? positionLevel : undefined
    const selectedLevel = typeof selectedPositionLevel.value === 'number' ? selectedPositionLevel.value : undefined
    await createOrderAPI({
      stock_code: stockCode,
      stock_name: stockName,
      price,
      quantity,
      ...(validPositionLevel ? { position_level: validPositionLevel } : (selectedLevel ? { position_level: selectedLevel } : {}))
    })
    message.success(`${tradeMode.value === 'buy' ? '买入' : '卖出'}下单成功`)
  } catch (error: any) {
    message.error(error?.message || '下单失败')
  } finally {
    isSubmittingOrder.value = false
  }
}

const validateOrderInputs = () => {
  const stockCode = normalizeStockCode(orderStockCode.value)
  if (!stockCode) {
    message.warning('请先输入并选择证券代码')
    return null
  }

  const price = Number(orderPriceValue.value || 0)
  if (!Number.isFinite(price) || price <= 0) {
    message.warning('请输入有效委托价格')
    return null
  }

  const quantity = Number(orderQuantity.value || 0)
  if (!Number.isInteger(quantity) || quantity < 100) {
    message.warning('委托数量最小为 100')
    return null
  }
  return { stockCode, price, quantity }
}

const confirmPositionOrder = (positionLevel: number, label: string) => {
  if (!allowSubmitAction('order-confirm-' + positionLevel, 500)) return

  const validation = validateOrderInputs()
  if (!validation) return

  choosePositionLevel(positionLevel)
  Modal.confirm({
    title: `确认${tradeMode.value === 'buy' ? '买入' : '卖出'}${label}下单`,
    content: `证券 ${validation.stockCode}，价格 ${validation.price.toFixed(2)}，数量 ${validation.quantity}`,
    okText: '确认下单',
    cancelText: '取消',
    onOk: async () => {
      await submitOrder(positionLevel)
    }
  })
}

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

  offTerminalSnapshot = ws.onEvent('terminal_snapshot', (payload) => {
    const snapshot = payload as { userId?: string; terminals?: Array<Record<string, unknown>> }
    if (snapshot.userId !== currentUid.value) return
    applySnapshot(snapshot.terminals || [])
  })

  offWsConnect = ws.onConnect(() => {
    if (controlTopic.value) ws.subscribe([controlTopic.value])
    requestSnapshot()
  })

  watch(currentUid, async (uid, prevUid) => {
    if (prevUid) {
      ws.unsubscribe(['trading-terminal.control.' + prevUid])
    }

    if (offControlTopic) {
      offControlTopic()
      offControlTopic = null
    }

    terminalTopicOffFns.forEach((off, topic) => {
      ws.unsubscribe([topic])
      off()
    })
    terminalTopicOffFns.clear()

    terminals.value = {}
    terminalSeqMap.value = {}
    terminalHistoryLoaded.value = {}
    terminalHistoryLoading.value = {}
    editingTerminalId.value = ''
    editingTerminalName.value = ''
    terminalRenameTimers.forEach((timer) => clearTimeout(timer))
    terminalRenameTimers.clear()
    controlEventsCount.value = 0
    pendingOrders.value = []
    pendingTimeMap.value = {}
    pendingConfig.value = {
      uid: '',
      enabled: true,
      default_delay_minutes: 10,
      auto_submit: false
    }

    if (!uid) return

    const nextControlTopic = 'trading-terminal.control.' + uid
    ws.subscribe([nextControlTopic])
    offControlTopic = ws.onEvent(nextControlTopic, handleControlEvent)

    await Promise.all([
      loadUserTerminals(uid),
      loadPendingConfig(uid),
      loadPendingOrders(uid)
    ])
    requestSnapshot()
  }, { immediate: true })
})

onUnmounted(() => {
  ws.unsubscribe(['zixuan'])
  if (controlTopic.value) {
    ws.unsubscribe([controlTopic.value])
  }
  offZixuan?.()
  offControlTopic?.()
  offTerminalSnapshot?.()
  offWsConnect?.()

  terminalTopicOffFns.forEach((off, topic) => {
    ws.unsubscribe([topic])
    off()
  })
  terminalTopicOffFns.clear()
  terminalRenameTimers.forEach((timer) => clearTimeout(timer))
  terminalRenameTimers.clear()

  if (searchDebounceTimer) clearTimeout(searchDebounceTimer)
  if (orderSearchDebounceTimer) clearTimeout(orderSearchDebounceTimer)
})
</script>

<template>
  <div class="min-h-[calc(100vh-48px)] bg-bgMain p-3">
    <div class="flex flex-col gap-3">
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

          <div v-if="watchlist.length === 0" class="flex-1 flex items-center justify-center text-textMute text-xs">
            暂无自选股票
          </div>
          <div v-else class="watchlist-scroll-wrap overflow-y-auto h-[224px]">
            <table class="density-table w-full text-xs">
              <thead>
                <tr class="bg-bgMain/70">
                  <th class="text-left text-textSub font-medium">代码</th>
                  <th class="text-left text-textSub font-medium">名称</th>
                  <th class="text-right text-textSub font-medium">收盘</th>
                  <th class="text-right text-textSub font-medium">涨跌</th>
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
                  <td class="text-center">
                    <div class="inline-flex items-center gap-2">
                      <button
                        type="button"
                        class="h-6 px-2 rounded border border-primary/30 text-primary hover:bg-primary/10 transition-colors disabled:opacity-50"
                        :disabled="isSubmittingOrder"
                        @click="quickSubmitFromWatchlist(stock)"
                      >
                        一键下单
                      </button>
                      <button
                        type="button"
                        class="h-6 px-2 rounded border border-border text-textSub hover:bg-bgMain transition-colors disabled:opacity-50"
                        :disabled="isPendingSaving"
                        @click="addPendingFromWatchlist(stock)"
                      >
                        加入挂单
                      </button>
                      <a-button
                        class="rounded hover:bg-down/10 transition-colors"
                        @click="removeFromWatchlist(stock.ts_code)"
                        danger
                        size="small"
                      >
                        删除
                      </a-button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="bg-card rounded-lg border border-border shadow-sm p-3 flex flex-col gap-3 min-h-[280px] quick-terminal-panel">
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
              <button
                type="button"
                class="px-4 py-1 rounded font-medium"
                :class="pendingDrawerOpen ? 'bg-primary text-white' : 'text-textSub'"
                @click="pendingDrawerOpen = !pendingDrawerOpen"
              >
                挂单
              </button>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-2 rounded border border-border bg-bgMain/70 p-3 text-xs">
            <div class="space-y-1">
              <label class="text-textSub">证券代码</label>
              <div class="relative">
                <input
                  v-model="orderStockCode"
                  type="text"
                  class="h-8 w-full rounded border border-border bg-card pl-8 pr-2 text-textMain font-numeric placeholder-textMute focus:border-primary focus:outline-none"
                  placeholder="代码/名称检索"
                />
                <Icon icon="search" :size="14" class="absolute left-2.5 top-2 text-textMute" />

                <div
                  v-if="orderStockCode && (isOrderSearching || orderSearchResults)"
                  class="absolute top-9 left-0 right-0 z-20 rounded border border-border bg-card shadow-sm max-h-52 overflow-y-auto"
                >
                  <div v-if="isOrderSearching" class="px-3 py-2 text-xs text-textMute">搜索中...</div>
                  <div v-else-if="orderSearchResults && orderSearchResults.length === 0" class="px-3 py-2 text-xs text-textMute">未找到匹配股票</div>
                  <button
                    v-for="stock in orderSearchResults || []"
                    :key="stock.ts_code"
                    type="button"
                    class="w-full px-3 py-2 text-left hover:bg-primary/5 border-b border-border last:border-b-0"
                    @click="selectOrderStock(stock)"
                  >
                    <div class="flex items-center justify-between">
                      <div class="min-w-0">
                        <p class="text-xs text-textMain truncate">{{ stock.name }}</p>
                        <p class="text-xxs text-textSub font-numeric">{{ stock.ts_code }}</p>
                      </div>
                    </div>
                  </button>
                </div>
              </div>
            </div>
            <div class="space-y-1">
              <label class="text-textSub">名称</label>
              <input
                type="text"
                :value="orderStockName"
                class="h-8 w-full rounded border border-border bg-card px-2 text-textMain"
                readonly
              />
            </div>
            <div class="space-y-1">
              <label class="text-textSub">委托价格</label>
              <input
                v-model.number="orderPriceValue"
                type="number"
                min="0"
                step="0.01"
                placeholder="输入委托价格"
                class="h-8 w-full rounded border border-border bg-card px-2 text-textMain font-numeric"
              />
            </div>
            <div class="space-y-1">
              <label class="text-textSub">委托数量</label>
              <input
                v-model.number="orderQuantity"
                type="number"
                min="100"
                step="100"
                placeholder="最小100"
                class="h-8 w-full rounded border border-border bg-card px-2 text-textMain font-numeric"
              />
            </div>
            <div class="col-span-2 flex items-center gap-2 mt-1">
              <button
                type="button"
                class="flex-1 h-7 rounded border border-border bg-card text-textSub"
                :class="selectedPositionLevel === 4 ? 'border-primary text-primary' : ''"
                @click="confirmPositionOrder(4, '1/4仓')"
              >
                1/4
              </button>
              <button
                type="button"
                class="flex-1 h-7 rounded border border-border bg-card text-textSub"
                :class="selectedPositionLevel === 3 ? 'border-primary text-primary' : ''"
                @click="confirmPositionOrder(3, '1/3仓')"
              >
                1/3
              </button>
              <button
                type="button"
                class="flex-1 h-7 rounded border border-border bg-card text-textSub"
                :class="selectedPositionLevel === 2 ? 'border-primary text-primary' : ''"
                @click="confirmPositionOrder(2, '1/2仓')"
              >
                1/2
              </button>
              <button
                type="button"
                class="flex-1 h-7 rounded border border-border bg-card text-textSub"
                :class="selectedPositionLevel === 1 ? 'border-primary text-primary' : ''"
                @click="confirmPositionOrder(1, '全仓')"
              >
                全仓
              </button>
              <button
                type="button"
                class="h-7 px-4 rounded bg-primary text-white font-medium disabled:opacity-50"
                :disabled="isSubmittingOrder"
                @click="submitOrder()"
              >
                {{ isSubmittingOrder ? '下单中...' : '确认下单' }}
              </button>
            </div>
          </div>

          <div class="text-xxs text-textMute flex items-center justify-between">
            <span>UID: <span class="font-numeric">{{ currentUid || '-' }}</span></span>
            <span>终端数: <span class="font-numeric text-primary">{{ terminalCount }}</span></span>
            <span>控制事件: <span class="font-numeric">{{ controlEventsCount }}</span></span>
          </div>
        </div>
      </section>

      <section class="bg-card rounded-lg border border-border shadow-sm p-3 flex flex-col gap-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <Icon icon="mdi:console-network-outline" :size="16" class="text-primary" />
            <h2 class="text-sm font-semibold text-textMain">终端面板</h2>
          </div>
          <p class="text-xxs text-textMute">
            共 <span class="font-numeric text-primary">{{ terminalCount }}</span> 个终端
          </p>
        </div>


          <div v-if="terminalList.length === 0" class="py-10 flex items-center justify-center text-xs text-textMute">
            暂无终端
          </div>

        <div class="grid grid-cols-1 xl:grid-cols-2 gap-3" v-else>
          <article
            v-for="terminal in terminalList"
            :key="terminal.terminalId"
            class="bg-bgMain/40 rounded-lg border border-border overflow-hidden flex flex-col"
          >
            <div class="px-3 py-2 bg-card/70 border-b border-border flex items-center justify-between">
              <div class="min-w-0">
                <div class="flex items-center gap-2 text-textSub min-w-0">
                  <Icon icon="mdi:console" :size="14" />
                  <span class="text-xxs font-numeric truncate">{{ terminal.terminalId }} {{ terminal.macAddress || '-' }}</span>
                </div>
                <div class="mt-0.5">
                  <button
                    v-if="editingTerminalId !== terminal.terminalId"
                    type="button"
                    class="text-xxs text-textMute truncate max-w-full text-left hover:text-primary"
                    @click="beginEditTerminalName(terminal.terminalId)"
                  >
                    {{ terminal.terminalName || terminal.terminalId }}
                  </button>
                  <input
                    v-else
                    v-model="editingTerminalName"
                    type="text"
                    class="h-6 w-44 max-w-full rounded border border-primary/40 bg-card px-2 text-xxs text-textMain focus:border-primary focus:outline-none"
                    @input="commitTerminalNameDebounced(terminal.terminalId)"
                    @keydown.enter.prevent="finishEditTerminalName(terminal.terminalId)"
                    @blur="finishEditTerminalName(terminal.terminalId)"
                  />
                </div>
              </div>
              <div class="flex items-center gap-2 status-panel">
                <div class="status-input">
                  <span class="status-addon">系统</span>
                  <span class="status-value" :class="terminal.connected ? 'text-down' : 'text-up'">
                    <span class="w-1.5 h-1.5 rounded-full inline-block mr-1" :class="terminal.connected ? 'bg-down' : 'bg-up'" />
                    {{ terminal.connected ? 'Connected' : 'Disconnected' }}
                  </span>
                </div>
                <div class="status-input">
                  <span class="status-addon">交易机</span>
                  <span class="status-value" :class="terminal.connected && terminal.online ? 'text-down' : 'text-up'">
                    <span class="w-1.5 h-1.5 rounded-full inline-block mr-1" :class="terminal.connected && terminal.online ? 'bg-down' : 'bg-up'" />
                    {{ terminal.connected && terminal.online ? 'Online' : 'Offline' }}
                  </span>
                </div>
              </div>
            </div>

            <div class="p-3 terminal-records-wrap">
              <div v-if="terminal.records.length === 0" class="h-full flex items-center justify-center text-xs text-textMute">
                暂无交易记录
              </div>
              <table v-else class="w-full text-xs terminal-table">
                <thead>
                  <tr>
                    <th class="text-left">时间</th>
                    <th class="text-left">代码</th>
                    <th class="text-left">名称</th>
                    <th class="text-center">方向</th>
                    <th class="text-right">成交价</th>
                    <th class="text-right">成交量</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(record, idx) in terminal.records" :key="record.tradeId || (terminal.terminalId + '-' + idx)">
                    <td class="font-numeric text-textMute text-left truncate">{{ String(record.time || '-') }}</td>
                    <td class="font-numeric text-textSub text-left truncate">{{ String(record.symbol || '-') }}</td>
                    <td class="text-textMain text-left truncate">{{ String(record.name || '-') }}</td>
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

        </div>
      </section>
    </div>

    <a-drawer
      v-model:open="pendingDrawerOpen"
      title="挂单列表"
      placement="right"
      width="600"
      :body-style="{ padding: '12px' }"
    >
      <div class="text-xxs text-textMute mb-2 flex items-center justify-between">
        <span>UID: <span class="font-numeric">{{ currentUid || '-' }}</span></span>
        <span>挂单数: <span class="font-numeric text-primary">{{ pendingOrders.length }}</span></span>
      </div>

      <div v-if="isPendingLoading" class="py-6 text-center text-xs text-textMute">挂单加载中...</div>
      <div v-else-if="pendingOrders.length === 0" class="py-6 text-center text-xs text-textMute">暂无挂单</div>
      <div v-else class="pending-orders-wrap">
        <a-table
          :columns="pendingOrderColumns"
          :data-source="pendingOrders"
          :pagination="false"
          :row-key="(record: PendingOrderItem) => record.id"
          size="small"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'stock_code'">
              <span class="font-numeric text-textMain">{{ record.stock_code }}</span>
            </template>
            <template v-else-if="column.key === 'stock_name'">
              <span class="text-textMain">{{ record.stock_name }}</span>
            </template>
            <template v-else-if="column.key === 'scheduled_at'">
              <div class="min-w-[170px]">
                <input
                  v-model="pendingTimeMap[record.id]"
                  type="datetime-local"
                  class="h-7 w-full rounded border border-border bg-card px-2 text-xxs text-textMain font-numeric"
                  :disabled="isPendingSaving"
                  @change="onPendingTimeChange(record)"
                />
              </div>
            </template>
            <template v-else-if="column.key === 'actions'">
              <a-button
                type="text"
                danger
                size="small"
                class="h-7 w-7 !inline-flex !items-center !justify-center disabled:opacity-50"
                :disabled="isPendingSaving"
                @click="removePendingOrder(record.id)"
                :title="'删除挂单'"
              >
                <Icon icon="mdi:delete-outline" :size="14" />
              </a-button>
            </template>
          </template>
        </a-table>
      </div>
    </a-drawer>
  </div>
</template>

<style scoped>
.terminal-table th,
.terminal-table td {
  padding: 4px 6px;
  border-bottom: 1px solid var(--color-border);
  vertical-align: middle;
}

.terminal-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.terminal-table thead th {
  position: sticky;
  top: -12px;
  z-index: 1;
  background-color: rgb(var(--color-card));
}

.terminal-table thead {
  background-color: rgb(var(--color-card));
  box-shadow: inset 0 -1px 0 0 var(--color-border);
}

.terminal-table th {
  color: var(--color-text-sub);
  font-weight: 500;
}

.terminal-records-wrap {
  height: 160px;
  max-height: 160px;
  min-height: 160px;
  overflow-y: auto;
}

.status-panel {
  padding: 2px 0;
}

.status-input {
  display: inline-flex;
  align-items: center;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  overflow: hidden;
  background: var(--color-card);
  min-height: 22px;
}

.status-addon {
  display: inline-flex;
  align-items: center;
  padding: 0 6px;
  font-size: 11px;
  color: var(--color-text-sub);
  background: rgba(15, 23, 42, 0.04);
  border-right: 1px solid var(--color-border);
}

.status-value {
  display: inline-flex;
  align-items: center;
  padding: 0 8px;
  font-size: 11px;
}

.quick-terminal-panel,
.quick-terminal-panel input,
.quick-terminal-panel button,
.quick-terminal-panel label {
  font-family: inherit;
}

.quick-terminal-panel {
  font-size: 12px;
  line-height: 1.4;
}

.quick-terminal-panel input {
  font-size: 12px;
  line-height: 1.25;
}

.quick-terminal-panel input::placeholder {
  font-size: 12px;
}

.watchlist-scroll-wrap {
  min-height: 224px;
  max-height: 224px;
}

.watchlist-scroll-wrap thead th {
  position: sticky;
  top: 0;
  z-index: 2;
  background-color: rgb(var(--color-bg-main));
}

.watchlist-scroll-wrap thead {
  box-shadow: inset 0 -1px 0 0 var(--color-border);
}

.pending-orders-wrap {
  max-height: calc(100vh - 170px);
  overflow-y: auto;
}

</style>
