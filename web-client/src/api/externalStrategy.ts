import axios from 'axios'

function getApiBaseUrl(): string {
  if ((import.meta as any).env?.VITE_API_URL) {
    return (import.meta as any).env.VITE_API_URL
  }
  return `http://${window.location.hostname}:8766`
}

const apiClient = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' }
})

export interface StrategyToggleRequest {
  strategy_id: number
  action: boolean
}

export interface StrategySignalQuery {
  strategy_id?: number
  page?: number
  page_size?: number
}

export interface StrategySignal {
  id?: number
  strategy_id?: number
  ts_code?: string
  stock_name?: string
  signal_type?: string
  price?: number
  trigger_price?: number
  quantity?: number
  trigger_time?: string
  created_at?: string
  [key: string]: any
}

export interface StrategySignalResponse {
  total?: number
  page?: number
  page_size?: number
  items?: StrategySignal[]
  [key: string]: any
}

export interface RiskConfig {
  enabled: boolean
  percent: number
  description?: string
  [key: string]: any
}

export interface RiskConfigPayload {
  enabled: boolean
  percent: number
}

export async function toggleStrategy(strategyId: number, action: boolean): Promise<any> {
  const response = await apiClient.post('/strategy/toggle', {
    strategy_id: strategyId,
    action
  } satisfies StrategyToggleRequest)
  return response.data
}

export async function getStrategySignals(query: StrategySignalQuery): Promise<StrategySignalResponse> {
  const response = await apiClient.post('/strategy/signals', {
    strategy_id: query.strategy_id,
    page: query.page ?? 1,
    page_size: query.page_size ?? 20
  })
  return response.data
}

export async function getTakeProfitConfig(): Promise<RiskConfig> {
  const response = await apiClient.get<RiskConfig>('/strategy/config/take_profit')
  return response.data
}

export async function setTakeProfitConfig(payload: RiskConfigPayload): Promise<any> {
  const response = await apiClient.post('/strategy/config/take_profit', null, {
    params: payload
  })
  return response.data
}

export async function getStopLossConfig(): Promise<RiskConfig> {
  const response = await apiClient.get<RiskConfig>('/strategy/config/stop_loss')
  return response.data
}

export async function setStopLossConfig(payload: RiskConfigPayload): Promise<any> {
  const response = await apiClient.post('/strategy/config/stop_loss', null, {
    params: payload
  })
  return response.data
}
