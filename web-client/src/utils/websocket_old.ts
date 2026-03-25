import { ref } from 'vue'
import { io, Socket } from 'socket.io-client'

function generateClientId(): string {
  const stored = localStorage.getItem('ws_client_id')
  if (stored) return stored
  
  const newId = 'client_' + Math.random().toString(36).substring(2, 15) + Date.now().toString(36)
  localStorage.setItem('ws_client_id', newId)
  return newId
}

const CLIENT_ID = generateClientId()

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

export type MessageHandler = (data: RecommendationData) => void
export type BacktestProgressHandler = (data: BacktestProgressData) => void
export type BacktestLogHandler = (data: BacktestLogData) => void
export type BacktestCompletedHandler = (data: BacktestCompletedData) => void
export type ConnectHandler = () => void
export type DisconnectHandler = () => void
export type ErrorHandler = (error: Error) => void
export type ZixuanHandler = (data: WatchlistItem[]) => void

function getSocketUrl(): string {
  const wsHost = import.meta.env.VITE_WS_HOST || window.location.hostname
  const wsPort = import.meta.env.VITE_WS_PORT || '8766'
  return `http://${wsHost}:${wsPort}`
}

class SocketIOClient {
  private socket: Socket | null = null
  private clientType: string = 'web'
  private reconnectInterval = 3000
  
  public isConnected = ref(false)
  public messageHandler: MessageHandler | null = null
  public backtestProgressHandler: BacktestProgressHandler | null = null
  public backtestLogHandler: BacktestLogHandler | null = null
  public backtestCompletedHandler: BacktestCompletedHandler | null = null
  public connectHandler: ConnectHandler | null = null
  public disconnectHandler: DisconnectHandler | null = null
  public errorHandler: ErrorHandler | null = null
  public zixuanHandler: ZixuanHandler | null = null

  constructor(clientType: string = 'web') {
    this.clientType = clientType
  }

  connect(): void {
    if (this.socket?.connected) {
      return
    }

    const url = getSocketUrl()
    this.socket = io(url, {
      transports: ['websocket'],
      autoConnect: true,
      reconnection: true,
      reconnectionDelay: this.reconnectInterval,
      reconnectionAttempts: Infinity,
      query: {
        client_id: CLIENT_ID,
        client_type: this.clientType
      }
    })

    this.socket.on('connect', () => {
      this.isConnected.value = true
      console.log('[SocketIO] 已连接, sid:', this.socket?.id)
      this.connectHandler?.()
      
      this.socket?.emit('subscribe', { topics: [] })
    })

    this.socket.on('disconnect', (reason) => {
      this.isConnected.value = false
      console.log('[SocketIO] 连接关闭:', reason)
      this.disconnectHandler?.()
    })

    this.socket.on('connect_error', (error) => {
      console.error('[SocketIO] 连接错误:', error)
      this.errorHandler?.(error as Error)
    })

    this.socket.on('recommendation', (data) => {
      this.messageHandler?.(data as RecommendationData)
    })

    this.socket.on('zixuan', (data) => {
      this.zixuanHandler?.(data as WatchlistItem[])
    })

    this.socket.on('backtest_progress', (data) => {
      this.backtestProgressHandler?.(data as BacktestProgressData)
    })

    this.socket.on('backtest_log', (data) => {
      this.backtestLogHandler?.(data as BacktestLogData)
    })

    this.socket.on('backtest_completed', (data) => {
      this.backtestCompletedHandler?.(data as BacktestCompletedData)
    })

    this.socket.on('heartbeat', (data) => {
      console.log('[SocketIO] heartbeat:', data)
    })

    this.socket.on('subscribed', (data) => {
      console.log('[SocketIO] 已订阅:', data)
    })

    this.socket.on('connected', (data) => {
      console.log('[SocketIO] 服务器确认:', data)
    })
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
    this.isConnected.value = false
  }

  subscribe(topics: string[]): void {
    this.socket?.emit('subscribe', { topics })
  }

  unsubscribe(topics: string[]): void {
    this.socket?.emit('unsubscribe', { topics })
  }
}

export interface SocketIOOptions {
  url?: string
  clientType?: string
}

export function createSocketIOClient(options: SocketIOOptions = {}) {
  const { clientType = 'web' } = options
  const wsClient = new SocketIOClient(clientType)

  return {
    wsClient,
    isConnected: wsClient.isConnected,
    connect: () => wsClient.connect(),
    disconnect: () => wsClient.disconnect(),
    subscribe: (topics: string[]) => wsClient.subscribe(topics),
    unsubscribe: (topics: string[]) => wsClient.unsubscribe(topics),
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

export { createWebSocketClient, type WebSocketOptions } from './websocket_old'
