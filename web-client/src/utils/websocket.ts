import { ref } from 'vue'
import { getWsUrl } from '@/config/api'

function generateClientId(): string {
  const stored = localStorage.getItem('ws_client_id')
  if (stored) return stored
  
  const newId = 'client_' + Math.random().toString(36).substring(2, 15) + Date.now().toString(36)
  localStorage.setItem('ws_client_id', newId)
  return newId
}

const CLIENT_ID = generateClientId()

export type MessageType = 
  | 'recommendation' 
  | 'heartbeat' 
  | 'system' 
  | 'subscribe' 
  | 'unsubscribe' 
  | 'connect' 
  | 'disconnect'
  | 'backtest_progress'
  | 'backtest_log'
  | 'backtest_completed'
  | 'push'

export interface WSMessage {
  type: MessageType
  payload: Record<string, unknown>
  timestamp: string
  message_id: string
}

export interface StockInfo {
  stock_code: string
  stock_name: string
  score: string
}

export interface News {
  title: string
  content: string
  publish_time: string
  crawl_time: string
  source: string
  url: string
}

export interface Analysis {
  利好版块: string[]
  利好股票: (string | StockInfo)[]
  分析因素: string[]
  详细分析: string
}

export interface RecommendationData {
  news: News
  analysis: Analysis
}

export interface BacktestProgressData {
  backtest_id: number
  progress: number
  current_date?: string
  equity?: number
}

export interface BacktestLogData {
  backtest_id: number
  level: string
  message: string
  time: string
}

export interface BacktestCompletedData {
  backtest_id: number
  status: string
  results: Record<string, unknown>
}

export type MessageHandler = (data: RecommendationData) => void
export type BacktestProgressHandler = (data: BacktestProgressData) => void
export type BacktestLogHandler = (data: BacktestLogData) => void
export type BacktestCompletedHandler = (data: BacktestCompletedData) => void
export type ConnectHandler = () => void
export type DisconnectHandler = () => void
export type ErrorHandler = (error: Event) => void

// 自选列表相关类型
export interface WatchlistItem {
  ts_code: string
  name: string
  pre_close?: number
  open?: number
  high?: number
  low?: number
  close?: number
  change?: number
  change_pct?: number
  vol?: number
  amount?: number
  trade_time?: string
}

export interface ZixuanPushPayload {
  target_type: string
  target_action: string
  data: WatchlistItem[]
}

export type ZixuanHandler = (data: WatchlistItem[]) => void

class WebSocketClient {
  private ws: WebSocket | null = null
  private url: string
  private clientType: string = 'web'
  private reconnectInterval = 3000
  private heartbeatInterval: number | null = null
  private isManualClose = false
  
  public isConnected = ref(false)
  public messageHandler: MessageHandler | null = null
  public backtestProgressHandler: BacktestProgressHandler | null = null
  public backtestLogHandler: BacktestLogHandler | null = null
  public backtestCompletedHandler: BacktestCompletedHandler | null = null
  public connectHandler: ConnectHandler | null = null
  public disconnectHandler: DisconnectHandler | null = null
  public errorHandler: ErrorHandler | null = null
  public zixuanHandler: ZixuanHandler | null = null

  constructor(url: string = '', clientType: string = 'web') {
    this.url = url || `ws://${window.location.hostname}:8765/ws`
    this.clientType = clientType
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return
    }

    this.isManualClose = false
    
    try {
      this.ws = new WebSocket(this.url)
      
      this.ws.onopen = () => {
        this.isConnected.value = true
        this.startHeartbeat()
        this.sendConnect()
        this.connectHandler?.()
        console.log('[WS] 已连接')
      }

      this.ws.onmessage = (event) => {
        try {
          const message: WSMessage = JSON.parse(event.data)
          this.handleMessage(message)
        } catch (e) {
          console.error('[WS] 解析消息失败:', e)
        }
      }

      this.ws.onclose = (event) => {
        this.isConnected.value = false
        this.stopHeartbeat()
        this.disconnectHandler?.()
        console.log('[WS] 连接关闭, code:', event.code, 'reason:', event.reason)
        
        if (!this.isManualClose) {
          console.log('[WS] 准备重连...')
          setTimeout(() => {
            console.log('[WS] 正在重连...')
            this.connect()
          }, this.reconnectInterval)
        }
      }

      this.ws.onerror = (error) => {
        console.error('[WS] 错误:', error)
        this.errorHandler?.(error)
      }
    } catch (e) {
      console.error('[WS] 连接失败:', e)
    }
  }

  disconnect(): void {
    this.isManualClose = true
    this.stopHeartbeat()
    
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.isConnected.value = false
  }

  private handleMessage(message: WSMessage): void {
    switch (message.type) {
      case 'recommendation':
        this.messageHandler?.(message.payload as unknown as RecommendationData)
        break
      case 'backtest_progress':
        this.backtestProgressHandler?.(message.payload as unknown as BacktestProgressData)
        break
      case 'backtest_log':
        this.backtestLogHandler?.(message.payload as unknown as BacktestLogData)
        break
      case 'backtest_completed':
        this.backtestCompletedHandler?.(message.payload as unknown as BacktestCompletedData)
        break
      case 'push':
        if (message.payload.target_action === 'zixuan') {
          const data = (message.payload as unknown as ZixuanPushPayload).data
          this.zixuanHandler?.(data)
        }
        break
      case 'heartbeat':
        break
      case 'system':
        if (message.payload.status === 'connected') {
          console.log('[WS] 已认证')
        }
        break
      default:
        break
    }
  }

  private sendConnect(): void {
    this.send({
      type: 'connect',
      payload: {
        client_id: CLIENT_ID,
        client_type: this.clientType,
        action: 'default',
        user_agent: navigator.userAgent
      },
      timestamp: new Date().toISOString(),
      message_id: `msg_${Date.now()}`
    })
  }

  subscribe(topics: string[]): void {
    this.send({
      type: 'subscribe',
      payload: {
        topics,
        client_type: 'web'
      },
      timestamp: new Date().toISOString(),
      message_id: `msg_${Date.now()}`
    })
  }

  private send(message: WSMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    }
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = window.setInterval(() => {
      this.send({
        type: 'heartbeat',
        payload: { status: 'ping' },
        timestamp: new Date().toISOString(),
        message_id: `msg_${Date.now()}`
      })
    }, 30000)
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }
  }
}

export interface WebSocketOptions {
  url?: string
  clientType?: string
}

export function createWebSocketClient(options: WebSocketOptions = {}) {
  const { clientType = 'web' } = options
  const url = options.url || getWsUrl(clientType)
  const wsClient = new WebSocketClient(url, clientType)

  return {
    wsClient,
    isConnected: wsClient.isConnected,
    connect: () => wsClient.connect(),
    disconnect: () => wsClient.disconnect(),
    subscribe: (topics: string[]) => wsClient.subscribe(topics),
    onMessage: (handler: MessageHandler) => {
      wsClient.messageHandler = handler
    },
    onBacktestProgress: (handler: BacktestProgressHandler) => {
      wsClient.backtestProgressHandler = handler
    },
    onBacktestLog: (handler: BacktestLogHandler) => {
      wsClient.backtestLogHandler = handler
    },
    onBacktestCompleted: (handler: BacktestCompletedHandler) => {
      wsClient.backtestCompletedHandler = handler
    },
    onZixuan: (handler: ZixuanHandler) => {
      wsClient.zixuanHandler = handler
    },
    onConnect: (handler: ConnectHandler) => {
      wsClient.connectHandler = handler
    },
    onDisconnect: (handler: DisconnectHandler) => {
      wsClient.disconnectHandler = handler
    },
    onError: (handler: ErrorHandler) => {
      wsClient.errorHandler = handler
    }
  }
}

export function parseStockInfo(stock: string | StockInfo): { code: string; name: string; score: number } | null {
  if (typeof stock === 'object') {
    const codeNum = parseInt(stock.stock_code)
    return {
      code: stock.stock_code + (codeNum < 500000 ? '.SH' : '.SZ'),
      name: stock.stock_name,
      score: parseInt(stock.score) || 0
    }
  }
  
  const match = stock.match(/(\d{6})\(([^)]+?)(\d+)?\)/)
  if (!match) return null
  
  return {
    code: match[1] + (parseInt(match[1]) < 500000 ? '.SH' : '.SZ'),
    name: match[2],
    score: match[3] ? parseInt(match[3]) : 0
  }
}
