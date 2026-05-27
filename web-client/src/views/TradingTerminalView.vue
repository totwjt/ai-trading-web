<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { h } from 'vue'
import { DeleteOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import Icon from '@/components/common/Icon.vue'
import { useUserStore } from '@/stores/userStore'
import {
  addToWatchlistAPI,
  createPendingOrderAPI,
  createOrderAPI,
  getFinaMainbz,
  getPendingOrderConfigAPI,
  getPendingOrdersAPI,
  getTradeRecordsByMachine,
  getUserTerminals,
  getWatchlist,
  removeFromWatchlistAPI,
  removePendingOrderAPI,
  searchStocks,
  updateTerminalCityAPI,
  updateTerminalNameAPI,
  updatePendingOrderAPI,
  type FinaMainbzItem,
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
  status?: 'success' | 'failed'
  price?: number
  qty?: number
  amount?: number
  [key: string]: unknown
}

interface TerminalState {
  userId: string
  terminalId: string
  terminalName: string
  terminalCity: string
  macAddress: string
  accountName: string
  connected: boolean
  online: boolean
  ignored?: boolean
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
const DEFAULT_TERMINAL_NAME = '交易终端_default'
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
const selectedPositionLevel = ref<number | undefined>(undefined)
const isSubmittingOrder = ref(false)
const orderSearchResults = ref<StockSearchResult[] | null>(null)
const isOrderSearching = ref(false)
const suppressOrderSearch = ref(false)
const pendingDrawerOpen = ref(false)
const pendingOrders = ref<PendingOrderItem[]>([])
const pendingTimeMap = ref<Record<number, string>>({})
const pendingPriceMap = ref<Record<number, number | null>>({})
const pendingQuantityMap = ref<Record<number, number | null>>({})
const isPendingLoading = ref(false)
const isPendingSaving = ref(false)
const pendingConfig = ref<PendingOrderConfig>({
  uid: '',
  enabled: true,
  default_delay_minutes: 10,
  auto_submit: false
})
const mainbzDrawerOpen = ref(false)
const mainbzData = ref<FinaMainbzItem[]>([])
const mainbzLoading = ref(false)
const mainbzStockInfo = ref<{ tsCode: string; name: string }>({ tsCode: '', name: '' })

const fetchFinaMainbz = async (stock: WatchlistItem) => {
  const tsCode = stock.ts_code || ''
  if (!tsCode) return

  mainbzStockInfo.value = { tsCode, name: stock.name || tsCode }
  mainbzDrawerOpen.value = true
  mainbzLoading.value = true
  mainbzData.value = []
  try {
    mainbzData.value = await getFinaMainbz(tsCode)
  } catch (error: any) {
    message.error(error?.message || '获取主营业务数据失败')
  } finally {
    mainbzLoading.value = false
  }
}

const pendingOrderColumns = [
  { title: '挂单信息', key: 'summary' },
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
const pendingFieldTimers = new Map<string, ReturnType<typeof setTimeout>>()
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
  return Object.values(terminals.value)
    .filter((t) => !t.ignored)
    .sort((a, b) => {
      if (a.online !== b.online) return a.online ? -1 : 1
      return a.terminalId.localeCompare(b.terminalId)
    })
})

const terminalCount = computed(() => terminalList.value.length)

const terminalTopic = (uid: string, terminalId: string) => 'trading-terminal.' + uid + '.' + terminalId

const cityOptions = [
  { label: '上海', value: '上海' },
  { label: '北京', value: '北京' },
  { label: '深圳', value: '深圳' },
  { label: '广州', value: '广州' },
  { label: '杭州', value: '杭州' },
  { label: '成都', value: '成都' }
]

const DEFAULT_TERMINAL_CITY = '北京'

const normalizeTerminalCity = (value: unknown): string => {
  const normalized = String(value || '').trim()
  return cityOptions.some((item) => item.value === normalized) ? normalized : DEFAULT_TERMINAL_CITY
}

const pad2 = (value: number) => String(value).padStart(2, '0')

const normalizeTerminalName = (value: unknown, fallback?: string): string => {
  const normalized = String(value || '').trim()
  if (normalized) return normalized

  const fallbackName = String(fallback || '').trim()
  if (fallbackName) return fallbackName

  return DEFAULT_TERMINAL_NAME
}

const formatRecordTime = (value: unknown): string => {
  const raw = String(value || '').trim()
  if (!raw) return ''
  if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(raw)) return raw
  if (/^\d{2}:\d{2}:\d{2}$/.test(raw)) return raw

  const parsed = new Date(raw)
  if (Number.isNaN(parsed.getTime())) return raw

  return [
    parsed.getFullYear(),
    '-',
    pad2(parsed.getMonth() + 1),
    '-',
    pad2(parsed.getDate()),
    ' ',
    pad2(parsed.getHours()),
    ':',
    pad2(parsed.getMinutes()),
    ':',
    pad2(parsed.getSeconds())
  ].join('')
}

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
    if (String(terminalName || '').trim()) current.terminalName = normalizeTerminalName(terminalName, current.terminalName)
    return current
  }

  const created: TerminalState = {
    userId: currentUid.value,
    terminalId,
    terminalName: normalizeTerminalName(terminalName),
    terminalCity: DEFAULT_TERMINAL_CITY,
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

const applyTerminalDisplayFields = (
  terminal: TerminalState,
  fields: {
    terminalName?: unknown
    terminalCity?: unknown
    macAddress?: unknown
    accountName?: unknown
  }
) => {
  if (String(fields.terminalName || '').trim()) {
    terminal.terminalName = normalizeTerminalName(fields.terminalName, terminal.terminalName)
  } else if (!String(terminal.terminalName || '').trim()) {
    terminal.terminalName = DEFAULT_TERMINAL_NAME
  }

  terminal.terminalCity = normalizeTerminalCity(fields.terminalCity ?? terminal.terminalCity)

  const macAddress = String(fields.macAddress || '').trim()
  const accountName = String(fields.accountName || '').trim()
  if (macAddress) terminal.macAddress = macAddress
  if (accountName) terminal.accountName = accountName
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

const subscribeTerminalTopic = (terminalId: string, ignored?: boolean) => {
  if (ignored) return
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
      appendRecord(terminalId, normalizeTradeRecord(envelope.data || {}, envelope.ts))
      return
    }

    if (envelope.eventType === 'trade.record.batch') {
      const records = (envelope.data?.records as TerminalTradeRecord[]) || []
      replaceRecords(terminalId, records.map((item) => normalizeTradeRecord(item, envelope.ts)))
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

const normalizeTradeStatus = (value: unknown): 'success' | 'failed' => {
  const raw = String(value || '').trim().toLowerCase()
  if (
    raw === 'success' ||
    raw === 'succeeded' ||
    raw === 'ok' ||
    raw === 'done' ||
    raw === 'filled' ||
    raw === 'completed' ||
    raw.includes('success') ||
    raw.includes('成功')
  ) {
    return 'success'
  }
  if (
    raw === 'failed' ||
    raw === 'fail' ||
    raw === 'error' ||
    raw === 'rejected' ||
    raw === 'cancelled' ||
    raw.includes('failed') ||
    raw.includes('失败')
  ) {
    return 'failed'
  }
  return 'success'
}

const normalizeTradeRecord = (item: Record<string, unknown>, fallbackTime?: string): TerminalTradeRecord => {
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
    time: formatRecordTime(item.time || item.trade_time || item.ts || item.timestamp || fallbackTime || ''),
    symbol,
    name,
    side: normalizeSide(item.side ?? item.direction ?? item.trade_type),
    status: normalizeTradeStatus(item.status ?? item.trade_status ?? item.result ?? item.state),
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

const syncTerminalDisplayInfo = async (uid: string, targetTerminalId?: string) => {
  if (!uid) return
  const items = await getUserTerminals(uid)
  items.forEach((item: UserTerminal) => {
    if (targetTerminalId && item.terminal_id !== targetTerminalId) return
    const terminal = ensureTerminalState(item.terminal_id, item.terminal_name || undefined)
    terminal.userId = item.uid
    applyTerminalDisplayFields(terminal, {
      terminalName: item.terminal_name,
      terminalCity: item.terminal_city,
      macAddress: item.mac_address,
      accountName: item.account_name
    })
    terminal.updatedAt = item.updated_at || terminal.updatedAt
  })
}

const applySnapshot = (items: Array<Record<string, unknown>>) => {
  items.forEach((item) => {
    const terminalId = String(item.terminalId || '')
    if (!terminalId) return

    const terminal = ensureTerminalState(terminalId, String(item.terminalName || ''))
    terminal.ignored = Boolean(item.ignored)
    applyTerminalDisplayFields(terminal, {
      terminalName: item.terminalName,
      terminalCity: item.terminalCity || item.terminal_city,
      macAddress: item.macAddress || item.mac_address,
      accountName: item.accountName || item.account_name
    })
    terminal.connected = Boolean(item.connected)
    terminal.online = terminal.connected ? Boolean(item.online) : false
    terminal.lastHeartbeatAt = String(item.lastHeartbeatAt || '')
    terminal.connectedAt = String(item.connectedAt || '')
    terminal.updatedAt = String(item.updatedAt || '')

    subscribeTerminalTopic(terminalId, terminal.ignored)
    if (!terminal.ignored) {
      void initTerminalRecordsByMachine(terminalId, terminal.macAddress)
    }
  })
}

const loadUserTerminals = async (uid: string) => {
  if (!uid) return
  const items = await getUserTerminals(uid)
  items.forEach((item: UserTerminal) => {
    const terminal = ensureTerminalState(item.terminal_id, item.terminal_name || undefined)
    terminal.userId = item.uid
    applyTerminalDisplayFields(terminal, {
      terminalName: item.terminal_name,
      terminalCity: item.terminal_city,
      macAddress: item.mac_address,
      accountName: item.account_name
    })
    terminal.connected = false
    terminal.online = false
    terminal.ignored = item.ignored || false
    terminal.updatedAt = item.updated_at || terminal.updatedAt
    subscribeTerminalTopic(item.terminal_id, terminal.ignored)
    if (!terminal.ignored) {
      void initTerminalRecordsByMachine(item.terminal_id, terminal.macAddress)
    }
  })
}

const handleControlEvent = (payload: unknown) => {
  const envelope = payload as TerminalEnvelope
  if (envelope.userId !== currentUid.value || !envelope.terminalId) return

  const terminalId = envelope.terminalId
  const terminal = ensureTerminalState(terminalId, String(envelope.data?.terminalName || ''))
  applyTerminalDisplayFields(terminal, {
    terminalName: envelope.data?.terminalName,
    terminalCity: envelope.data?.terminalCity || envelope.data?.terminal_city,
    macAddress: envelope.data?.macAddress || envelope.data?.mac_address,
    accountName: envelope.data?.accountName || envelope.data?.account_name
  })

  controlEventsCount.value += 1
  void syncTerminalDisplayInfo(currentUid.value, terminalId)

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
      await syncTerminalDisplayInfo(currentUid.value, terminalId)
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

const changeTerminalCity = async (terminalId: string, value: unknown) => {
  const terminal = terminals.value[terminalId]
  if (!terminal) return

  const nextCity = normalizeTerminalCity(value)
  const previousCity = terminal.terminalCity
  if (nextCity === previousCity) return

  terminal.terminalCity = nextCity
  try {
    await updateTerminalCityAPI({
      uid: currentUid.value,
      terminal_id: terminal.terminalId,
      mac_address: terminal.macAddress,
      terminal_city: nextCity
    })
    await syncTerminalDisplayInfo(currentUid.value, terminalId)
  } catch (error: any) {
    terminal.terminalCity = previousCity
    message.error(error?.message || '终端城市更新失败')
  }
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

const formatAmount = (value: number | null | undefined): string => {
  if (value == null) return '-'
  if (Math.abs(value) >= 1e8) return (value / 1e8).toFixed(2) + '亿'
  if (Math.abs(value) >= 1e4) return (value / 1e4).toFixed(2) + '万'
  return value.toFixed(2)
}

const normalizeStockCode = (code: string) => code.trim().toUpperCase()

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
  const timeMap: Record<number, string> = {}
  const priceMap: Record<number, number | null> = {}
  const quantityMap: Record<number, number | null> = {}
  items.forEach((item) => {
    timeMap[item.id] = toDateTimeInputValue(item.scheduled_at)
    priceMap[item.id] = item.order_price
    quantityMap[item.id] = item.order_quantity
  })
  pendingTimeMap.value = timeMap
  pendingPriceMap.value = priceMap
  pendingQuantityMap.value = quantityMap
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
    pendingPriceMap.value = {}
    pendingQuantityMap.value = {}
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

const resolvePendingOrderDraft = (fallbackPrice?: number | null) => {
  const orderPrice = Number(fallbackPrice ?? orderPriceValue.value ?? 0)
  const orderQty = Number(orderQuantity.value || 0)
  const price = Number.isFinite(orderPrice) ? Number(orderPrice.toFixed(2)) : 0
  const quantity = Number.isInteger(orderQty) && orderQty > 0 ? orderQty : 0
  return { price, quantity }
}

const addPendingOrder = async (stockCodeRaw: string, stockNameRaw: string, fallbackPrice?: number | null) => {
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

  const draft = resolvePendingOrderDraft(fallbackPrice)
  if (!Number.isFinite(draft.price) || draft.price <= 0) {
    message.warning('请输入有效挂单价格')
    return
  }
  if (!Number.isInteger(draft.quantity) || draft.quantity < 1) {
    message.warning('请输入有效挂单数量')
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
      order_price: draft.price,
      order_quantity: draft.quantity,
      scheduled_at: scheduledAt
    })
    pendingOrders.value = [created, ...pendingOrders.value]
    pendingTimeMap.value = {
      ...pendingTimeMap.value,
      [created.id]: toDateTimeInputValue(created.scheduled_at)
    }
    pendingPriceMap.value = {
      ...pendingPriceMap.value,
      [created.id]: created.order_price
    }
    pendingQuantityMap.value = {
      ...pendingQuantityMap.value,
      [created.id]: created.order_quantity
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
  await addPendingOrder(stock.ts_code || '', stock.name || '', Number(stock.close ?? 0))
}

const clearPendingFieldTimer = (key: string) => {
  const timer = pendingFieldTimers.get(key)
  if (!timer) return
  clearTimeout(timer)
  pendingFieldTimers.delete(key)
}

const schedulePendingFieldCommit = (key: string, task: () => Promise<void>) => {
  clearPendingFieldTimer(key)
  const timer = setTimeout(async () => {
    try {
      await task()
    } finally {
      pendingFieldTimers.delete(key)
    }
  }, 600)
  pendingFieldTimers.set(key, timer)
}

const commitPendingTimeChange = async (item: PendingOrderItem) => {
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

const commitPendingPriceChange = async (item: PendingOrderItem) => {
  if (!allowSubmitAction('pending-price-update-' + item.id)) return

  const nextPrice = Number(pendingPriceMap.value[item.id] ?? 0)
  if (!Number.isFinite(nextPrice) || nextPrice <= 0) {
    message.warning('请输入有效挂单价格')
    pendingPriceMap.value = {
      ...pendingPriceMap.value,
      [item.id]: item.order_price
    }
    return
  }

  const normalizedPrice = Number(nextPrice.toFixed(2))
  if (normalizedPrice === item.order_price) {
    pendingPriceMap.value = {
      ...pendingPriceMap.value,
      [item.id]: normalizedPrice
    }
    return
  }

  isPendingSaving.value = true
  try {
    await updatePendingOrderAPI(item.id, { order_price: normalizedPrice })
    pendingOrders.value = pendingOrders.value.map((row) => (
      row.id === item.id
        ? {
          ...row,
          order_price: normalizedPrice
        }
        : row
    ))
    pendingPriceMap.value = {
      ...pendingPriceMap.value,
      [item.id]: normalizedPrice
    }
    message.success('挂单价格已更新')
  } catch (error: any) {
    message.error(error?.message || '更新挂单失败')
    pendingPriceMap.value = {
      ...pendingPriceMap.value,
      [item.id]: item.order_price
    }
  } finally {
    isPendingSaving.value = false
  }
}

const commitPendingQuantityChange = async (item: PendingOrderItem) => {
  if (!allowSubmitAction('pending-quantity-update-' + item.id)) return

  const nextQuantity = Number(pendingQuantityMap.value[item.id] ?? 0)
  if (!Number.isInteger(nextQuantity) || nextQuantity < 1) {
    message.warning('请输入有效挂单数量')
    pendingQuantityMap.value = {
      ...pendingQuantityMap.value,
      [item.id]: item.order_quantity
    }
    return
  }

  if (nextQuantity === item.order_quantity) {
    return
  }

  isPendingSaving.value = true
  try {
    await updatePendingOrderAPI(item.id, { order_quantity: nextQuantity })
    pendingOrders.value = pendingOrders.value.map((row) => (
      row.id === item.id
        ? {
          ...row,
          order_quantity: nextQuantity
        }
        : row
    ))
    message.success('挂单数量已更新')
  } catch (error: any) {
    message.error(error?.message || '更新挂单失败')
    pendingQuantityMap.value = {
      ...pendingQuantityMap.value,
      [item.id]: item.order_quantity
    }
  } finally {
    isPendingSaving.value = false
  }
}

const onPendingTimeChange = async (item: PendingOrderItem) => {
  await commitPendingTimeChange(item)
}

const onPendingPriceInput = (item: PendingOrderItem) => {
  schedulePendingFieldCommit('price-' + item.id, () => commitPendingPriceChange(item))
}

const onPendingQuantityInput = (item: PendingOrderItem) => {
  schedulePendingFieldCommit('quantity-' + item.id, () => commitPendingQuantityChange(item))
}

const removePendingOrder = async (id: number) => {
  if (!allowSubmitAction('pending-remove-' + id)) return

  isPendingSaving.value = true
  try {
    await removePendingOrderAPI(id)
    clearPendingFieldTimer('price-' + id)
    clearPendingFieldTimer('quantity-' + id)
    pendingOrders.value = pendingOrders.value.filter((item) => item.id !== id)
    const nextTime = { ...pendingTimeMap.value }
    delete nextTime[id]
    pendingTimeMap.value = nextTime
    const nextPrice = { ...pendingPriceMap.value }
    delete nextPrice[id]
    pendingPriceMap.value = nextPrice
    const nextQuantity = { ...pendingQuantityMap.value }
    delete nextQuantity[id]
    pendingQuantityMap.value = nextQuantity
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
  selectedPositionLevel.value = selectedPositionLevel.value === positionLevel ? undefined : positionLevel
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

const submitOrder = async () => {
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
    const selectedLevel = typeof selectedPositionLevel.value === 'number' ? selectedPositionLevel.value : undefined
    await createOrderAPI({
      stock_code: stockCode,
      stock_name: stockName,
      price,
      quantity,
      trade_mode: tradeMode.value,
      ...(selectedLevel ? { position_level: selectedLevel } : {})
    })
    message.success(`${tradeMode.value === 'buy' ? '买入' : '卖出'}下单成功`)
  } catch (error: any) {
    message.error(error?.message || '下单失败')
  } finally {
    isSubmittingOrder.value = false
  }
}

const testBatchOrderCreate = () => {
  const uid = currentUid.value
  if (!uid) {
    message.warning('请先连接终端')
    return
  }

  ws.emit('push_order', {
    userId: uid,
    eventType: 'batch.order.create',
    source: 'signal_platform',
    data: [
      {
        stock_code: '000001',
        stock_name: '平安银行',
        price: 12.5,
        quantity: 1000,
        position_ratio: 0.5,
        position_level: 2,
        side: 'buy',
        timestamp: new Date().toISOString()
      },
      {
        stock_code: '600036',
        stock_name: '招商银行',
        price: 35.8,
        quantity: 500,
        position_ratio: 0.333,
        position_level: 3,
        side: 'sell',
        timestamp: new Date().toISOString()
      }
    ]
  })
  message.success('已发送 batch.order.create 测试消息')
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
    pendingFieldTimers.forEach((timer) => clearTimeout(timer))
    pendingFieldTimers.clear()
    controlEventsCount.value = 0
    pendingOrders.value = []
    pendingTimeMap.value = {}
    pendingPriceMap.value = {}
    pendingQuantityMap.value = {}
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
  pendingFieldTimers.forEach((timer) => clearTimeout(timer))
  pendingFieldTimers.clear()

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
                  <th class="text-right text-textSub font-medium">换手率</th>
                  <th class="text-center text-textSub font-medium">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="stock in watchlist" :key="stock.ts_code" class="hover:bg-primary/5">
                  <td class="text-textMain font-numeric">{{ stock.ts_code }}</td>
                  <td class="text-textMain">{{ stock.name }}</td>
                  <td class="text-right text-textMain font-numeric">{{ (stock.close ?? 0).toFixed(2) }}</td>
                  <td class="text-right font-numeric" :class="(stock.change ?? 0) >= 0 ? 'text-up' : 'text-down'">
                    {{ (stock?.change ?? 0) }} %
                  </td>
                  <td class="text-right font-numeric text-textMain">
                    {{ stock.turnover_rate != null ? stock.turnover_rate + '%' : '-' }}
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
                        挂单
                      </button>
                      <button
                        type="button"
                        class="h-6 px-2 rounded border border-border text-textSub hover:bg-bgMain transition-colors disabled:opacity-50"
                        :disabled="mainbzLoading"
                        @click="fetchFinaMainbz(stock)"
                      >
                        主营业务
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
              <button
                type="button"
                class="px-4 py-1 rounded font-medium border border-dashed border-orange-400 text-orange-500 hover:bg-orange-50"
                @click="testBatchOrderCreate"
              >
                批量测试
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
                @click="choosePositionLevel(4)"
              >
                1/4
              </button>
              <button
                type="button"
                class="flex-1 h-7 rounded border border-border bg-card text-textSub"
                :class="selectedPositionLevel === 3 ? 'border-primary text-primary' : ''"
                @click="choosePositionLevel(3)"
              >
                1/3
              </button>
              <button
                type="button"
                class="flex-1 h-7 rounded border border-border bg-card text-textSub"
                :class="selectedPositionLevel === 2 ? 'border-primary text-primary' : ''"
                @click="choosePositionLevel(2)"
              >
                1/2
              </button>
              <button
                type="button"
                class="flex-1 h-7 rounded border border-border bg-card text-textSub"
                :class="selectedPositionLevel === 1 ? 'border-primary text-primary' : ''"
                @click="choosePositionLevel(1)"
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
                <div class="terminal-city-field">
                  <span class="terminal-city-label">城市</span>
                  <a-select
                    :value="terminal.terminalCity"
                    :options="cityOptions"
                    :bordered="false"
                    :dropdown-match-select-width="false"
                    size="small"
                    class="terminal-city-select"
                    popup-class-name="terminal-city-dropdown"
                    @change="changeTerminalCity(terminal.terminalId, $event)"
                  />
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
                    <th class="text-center">状态</th>
                    <th class="text-right">价格</th>
                    <th class="text-right">数量</th>
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
                    <td class="text-center font-medium" :class="record.status === 'failed' ? 'text-up' : 'text-down'">
                      {{ record.status === 'failed' ? '失败' : '成功' }}
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
      width="520"
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
          bordered
          :columns="pendingOrderColumns"
          :data-source="pendingOrders"
          :pagination="false"
          :row-key="(record: PendingOrderItem) => record.id"
          size="small"
          class="pending-orders-table ant-table-striped"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'summary'">
              <div class="flex flex-col gap-1 py-1">
                <div class="flex items-center gap-2 min-w-0 text-xs font-bold">
                  <span class="font-numeric text-textMain shrink-0">{{ record.stock_code }}</span>
                  <span class="text-textSub truncate">{{ record.stock_name }}</span>
                </div>
                <div class="grid grid-cols-[84px_84px_minmax(0,1fr)] gap-2 items-center">
                  <input
                    v-model.number="pendingPriceMap[record.id]"
                    type="number"
                    min="0"
                    step="0.01"
                    class="h-7 w-full rounded border border-border bg-card px-2 text-xxs text-textMain font-numeric"
                    :disabled="isPendingSaving"
                    @input="onPendingPriceInput(record)"
                  />
                  <input
                    v-model.number="pendingQuantityMap[record.id]"
                    type="number"
                    min="100"
                    step="100"
                    class="h-7 w-full rounded border border-border bg-card px-2 text-xxs text-textMain font-numeric"
                    :disabled="isPendingSaving"
                    @input="onPendingQuantityInput(record)"
                  />
                  <div class="flex items-center gap-1">
                    <a-date-picker
                      v-model:value="pendingTimeMap[record.id]"
                      show-time
                      value-format="YYYY-MM-DDTHH:mm"
                      format="YYYY-MM-DD HH:mm"
                      input-read-only
                      :allow-clear="false"
                      :disabled="isPendingSaving"
                      class="pending-time-picker"
                      @change="onPendingTimeChange(record)"
                    />
                  </div>
                </div>
                <div class="grid grid-cols-[84px_84px_minmax(0,1fr)] gap-2 text-[11px] leading-none text-textMute">
                  <span>价格</span>
                  <span>数量</span>
                  <span>时间</span>
                </div>
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
                :icon="h(DeleteOutlined)"
              >
              </a-button>
            </template>
          </template>
        </a-table>
      </div>
    </a-drawer>

    <a-drawer
      v-model:open="mainbzDrawerOpen"
      :title="'主营业务 - ' + mainbzStockInfo.name + ' (' + mainbzStockInfo.tsCode + ')'"
      placement="bottom"
      height="420"
      :body-style="{ padding: '12px' }"
    >
      <div v-if="mainbzLoading" class="py-10 text-center text-xs text-textMute">加载中...</div>
      <div v-else-if="mainbzData.length === 0" class="py-10 text-center text-xs text-textMute">暂无主营业务数据</div>
      <template v-else>
        <div class="text-xxs text-textMute mb-2">共 {{ mainbzData.length }} 条记录</div>
        <div class="mainbz-table-wrap overflow-y-auto" style="max-height: 320px">
          <table class="w-full text-xs mainbz-table">
            <thead>
              <tr>
                <th class="text-left">报告期</th>
                <th class="text-left">业务项目</th>
                <th class="text-right">营业收入</th>
                <th class="text-right">收入占比(%)</th>
                <th class="text-right">营业利润</th>
                <th class="text-right">利润占比(%)</th>
                <th class="text-right">营业成本</th>
                <th class="text-center">币种</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, idx) in mainbzData" :key="idx" class="hover:bg-primary/5">
                <td class="font-numeric text-textSub">{{ item.end_date }}</td>
                <td class="text-textMain">{{ item.bz_item }}</td>
                <td class="text-right font-numeric text-textMain">{{ formatAmount(item.bz_sales) }}</td>
                <td class="text-right font-numeric text-textMain">{{ item.sales_ratio != null ? item.sales_ratio.toFixed(2) : '-' }}</td>
                <td class="text-right font-numeric text-textMain">{{ formatAmount(item.bz_profit) }}</td>
                <td class="text-right font-numeric text-textMain">{{ item.profit_ratio != null ? item.profit_ratio.toFixed(2) : '-' }}</td>
                <td class="text-right font-numeric text-textMain">{{ formatAmount(item.bz_cost) }}</td>
                <td class="text-center font-numeric text-textSub">{{ item.curr_type || '-' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
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

:deep(.pending-orders-table .ant-table-thead > tr > th) {
  padding: 6px 8px;
}

:deep(.pending-orders-table .ant-table-tbody > tr > td) {
  padding: 6px 8px;
  vertical-align: top;
}

:deep(.pending-orders-table .ant-table-thead > tr > th:last-child),
:deep(.pending-orders-table .ant-table-tbody > tr > td:last-child) {
  width: 72px;
  white-space: nowrap;
  vertical-align: middle;
  text-align: center;
}

:deep(.pending-time-picker) {
  width: 180px;
}

.status-panel {
  padding: 2px 0;
  flex-shrink: 0;
}

.status-input {
  display: inline-flex;
  align-items: center;
  border:1px solid rgba(var(--color-border));
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

.terminal-city-field {
  display: inline-flex;
  align-items: center;
  height: 24px;
  overflow: hidden;
  border:1px solid rgba(var(--color-border));
  border-radius: 6px;
  background: var(--color-card);
}

.terminal-city-label {
  display: inline-flex;
  align-items: center;
  height: 100%;
  padding: 0 6px;
  border-right: 1px solid var(--color-border);
  background: rgba(15, 23, 42, 0.04);
  color: var(--color-text-sub);
  font-size: 11px;
  line-height: 1;
  white-space: nowrap;
}

:deep(.terminal-city-select) {
  width: 76px;
}

:deep(.terminal-city-select .ant-select-selector) {
  height: 22px !important;
  min-height: 22px;
  padding: 0 20px 0 7px !important;
  border: 0 !important;
  border-radius: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
  font-size: 11px;
}

:deep(.terminal-city-select .ant-select-selection-item),
:deep(.terminal-city-select .ant-select-selection-placeholder) {
  line-height: 22px !important;
  font-size: 11px;
  color: var(--color-text-sub);
}

:deep(.terminal-city-select .ant-select-arrow) {
  right: 7px;
  color: var(--color-text-mute);
  font-size: 10px;
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

.mainbz-table th,
.mainbz-table td {
  padding: 4px 8px;
  border-bottom: 1px solid var(--color-border);
  vertical-align: middle;
  white-space: nowrap;
}

.mainbz-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.mainbz-table thead th {
  position: sticky;
  top: 0;
  z-index: 2;
  background-color: rgb(var(--color-card));
  color: var(--color-text-sub);
  font-weight: 500;
  box-shadow: inset 0 -1px 0 0 var(--color-border);
}

.mainbz-table-wrap {
  border: 1px solid var(--color-border);
  border-radius: 6px;
}

</style>
