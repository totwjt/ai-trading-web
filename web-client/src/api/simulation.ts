import { createApiClient } from '@/api/client'

const apiClient = createApiClient()

export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
  total?: number
  timestamp?: string
}

export interface SimulationItem {
  id: number
  name: string
  strategy_name: string
  strategyName: string
  status: string
  status_text: string
  statusText: string
  initial_capital: number
  initialCapital: number
  current_capital: number
  currentCapital: number
  total_return: number
  totalReturn: number
  today_return: number
  todayReturn: number
  today_pl: number
  todayPL: number
  holdings_value: number
  holdingsValue: number
  holdings_count: number
  holdingsCount: number
  win_rate: number
  winRate: number
  trade_count: number
  tradeCount: number
  start_date: string
  startDate: string
  last_trade_time: string
  lastTradeTime: string
  available_capital: number
  availableCapital: number
  frozen_capital: number
  frozenCapital: number
}

export interface AvailableStrategy {
  id: number
  name: string
  type?: string
  returns: string
  win_rate?: string
  winRate?: string
  risk?: string
  selected?: boolean
}

export interface HoldingItem {
  id?: number
  name: string
  code: string
  ts_code: string
  quantity: number
  avg_cost: number
  avgCost: number
  current_price: number
  currentPrice: number
  market_value: number
  marketValue: number
  pl: number
  pl_percent: number
  plPercent: number
  weight: number
}

export interface TradeRecord {
  id: number
  time: string
  stock_name?: string
  stockName?: string
  stock_code?: string
  stockCode?: string
  direction: string
  direction_text?: string
  directionText?: string
  price: number
  quantity: number
  amount: number
  status: string
}

export interface SimulationStats {
  running_count?: number
  runningCount?: number
  total_simulations?: number
  totalSimulations?: number
  total_return?: number
  totalReturn?: number
  total_today_pl?: number
  todayPL?: number
}

/** 标准化模拟列表/详情字段：兼容 camelCase 和 snake_case */
export function normalizeSimulation(item: any): SimulationItem {
  return {
    ...item,
    strategyName: item.strategyName || item.strategy_name || '',
    statusText: item.statusText || item.status_text || '',
    initialCapital: item.initialCapital ?? item.initial_capital ?? 0,
    currentCapital: item.currentCapital ?? item.current_capital ?? 0,
    totalReturn: item.totalReturn ?? item.total_return ?? 0,
    todayReturn: item.todayReturn ?? item.today_return ?? 0,
    todayPL: item.todayPL ?? item.today_pl ?? 0,
    holdingsValue: item.holdingsValue ?? item.holdings_value ?? 0,
    holdingsCount: item.holdingsCount ?? item.holdings_count ?? 0,
    winRate: item.winRate ?? item.win_rate ?? 0,
    tradeCount: item.tradeCount ?? item.trade_count ?? 0,
    startDate: item.startDate || item.start_date || '',
    lastTradeTime: item.lastTradeTime || item.last_trade_time || item.lastTradeDateTime || '',
    availableCapital: item.availableCapital ?? item.available_capital ?? 0,
    frozenCapital: item.frozenCapital ?? item.frozen_capital ?? 0,
  }
}

/** 标准化持仓字段 */
export function normalizeHolding(item: any): HoldingItem {
  return {
    ...item,
    code: item.code || item.symbol || item.ts_code || '',
    avgCost: item.avgCost ?? item.avg_cost ?? item.cost_price ?? 0,
    currentPrice: item.currentPrice ?? item.current_price ?? 0,
    marketValue: item.marketValue ?? item.market_value ?? 0,
    pl: item.pl ?? item.profit_loss ?? 0,
    plPercent: item.plPercent ?? item.pl_percent ?? item.profit_loss_percent ?? 0,
  }
}

/** 标准化交易记录字段 */
export function normalizeTrade(item: any): TradeRecord {
  return {
    ...item,
    time: item.time || item.timestamp || '',
    stockName: item.stockName || item.stock_name || item.name || '',
    stockCode: item.stockCode || item.stock_code || item.symbol || '',
    direction: item.direction || item.trade_type || '',
    directionText: item.directionText || item.direction_text || '',
    amount: item.amount ?? ((item.price * item.quantity) || 0),
    status: item.status || 'completed',
  }
}

export async function getSimulations(params?: {
  page?: number
  page_size?: number
  status?: string
  search?: string
}): Promise<{ items: SimulationItem[]; total: number }> {
  const response = await apiClient.get<ApiResponse>('/api/trading/simulations/', { params })
  const data = response.data
  if (data.code !== 0) {
    throw new Error(data.message || '获取模拟列表失败')
  }
  const rawItems = data.data?.items || data.data || []
  const items = Array.isArray(rawItems) ? rawItems.map(normalizeSimulation) : []
  return { items, total: data.total ?? items.length }
}

export async function getSimulationStats(): Promise<SimulationStats> {
  const response = await apiClient.get<ApiResponse>('/api/trading/simulations/stats')
  const data = response.data
  if (data.code !== 0) {
    throw new Error(data.message || '获取统计信息失败')
  }
  return data.data || {}
}

export async function getAvailableStrategies(): Promise<AvailableStrategy[]> {
  const response = await apiClient.get<ApiResponse>('/api/trading/simulations/available-strategies')
  const data = response.data
  if (data.code !== 0) {
    throw new Error(data.message || '获取策略列表失败')
  }
  return data.data || []
}

export async function getSimulation(id: number): Promise<SimulationItem> {
  const response = await apiClient.get<ApiResponse>(`/api/trading/simulations/${id}`)
  const data = response.data
  if (data.code !== 0) {
    throw new Error(data.message || '获取模拟详情失败')
  }
  return normalizeSimulation(data.data || {})
}

export async function createSimulation(payload: {
  strategy_id: number
  initial_capital?: number
  symbols?: string[]
}): Promise<any> {
  const response = await apiClient.post<ApiResponse>('/api/trading/simulations/', payload)
  const data = response.data
  if (data.code !== 0) {
    throw new Error(data.message || '创建模拟失败')
  }
  return data.data
}

export async function pauseSimulation(id: number): Promise<void> {
  const response = await apiClient.post<ApiResponse>(`/api/trading/simulations/${id}/pause`)
  if (response.data.code !== 0) {
    throw new Error(response.data.message || '暂停失败')
  }
}

export async function resumeSimulation(id: number): Promise<void> {
  const response = await apiClient.post<ApiResponse>(`/api/trading/simulations/${id}/resume`)
  if (response.data.code !== 0) {
    throw new Error(response.data.message || '恢复失败')
  }
}

export async function stopSimulation(id: number): Promise<void> {
  const response = await apiClient.post<ApiResponse>(`/api/trading/simulations/${id}/stop`)
  if (response.data.code !== 0) {
    throw new Error(response.data.message || '停止失败')
  }
}

export async function getHoldings(id: number): Promise<HoldingItem[]> {
  const response = await apiClient.get<ApiResponse>(`/api/trading/simulations/${id}/holdings`)
  const data = response.data
  if (data.code !== 0) {
    throw new Error(data.message || '获取持仓失败')
  }
  const rawItems = data.data || []
  return Array.isArray(rawItems) ? rawItems.map(normalizeHolding) : []
}

export async function getTrades(
  id: number,
  params?: { page?: number; page_size?: number }
): Promise<{ items: TradeRecord[]; total: number }> {
  const response = await apiClient.get<ApiResponse>(`/api/trading/simulations/${id}/trades`, { params })
  const data = response.data
  if (data.code !== 0) {
    throw new Error(data.message || '获取交易记录失败')
  }
  const rawItems = data.data?.items || data.data || []
  const items = Array.isArray(rawItems) ? rawItems.map(normalizeTrade) : []
  return { items, total: data.total ?? items.length }
}
