/**
 * 全局 WebSocket 消息中心
 * - 单例连接，全局复用
 * - 页面独立订阅 topic
 * - 消息仅用于实时显示，不持久化
 */

import { ref, onUnmounted } from 'vue'
import { io, Socket } from 'socket.io-client'

export type ZixuanHandler = (data: unknown[]) => void
export type RecommendationHandler = (data: unknown) => void
export type BacktestProgressHandler = (data: unknown) => void
export type BacktestLogHandler = (data: unknown) => void
export type BacktestCompletedHandler = (data: unknown) => void
export type ConnectHandler = () => void
export type DisconnectHandler = () => void
export type ErrorHandler = (error: Error) => void

let socketInstance: Socket | null = null
let refCount = 0

const isConnected = ref(false)
const subscribedTopics = ref<string[]>([])

const zixuanHandlers: ZixuanHandler[] = []
const recommendationHandlers: RecommendationHandler[] = []
const backtestProgressHandlers: BacktestProgressHandler[] = []
const backtestLogHandlers: BacktestLogHandler[] = []
const backtestCompletedHandlers: BacktestCompletedHandler[] = []
const connectHandlers: ConnectHandler[] = []
const disconnectHandlers: DisconnectHandler[] = []
const errorHandlers: ErrorHandler[] = []

function getSocketUrl(): string {
  const wsHost = import.meta.env.VITE_WS_HOST || window.location.hostname
  const wsPort = import.meta.env.VITE_WS_PORT || '8766'
  return `http://${wsHost}:${wsPort}`
}

function generateClientId(): string {
  const stored = localStorage.getItem('ws_client_id')
  if (stored) return stored
  
  const newId = 'client_' + Math.random().toString(36).substring(2, 15) + Date.now().toString(36)
  localStorage.setItem('ws_client_id', newId)
  return newId
}

function initSocket(): Socket {
  if (socketInstance) {
    return socketInstance
  }

  const clientId = generateClientId()
  
  socketInstance = io(getSocketUrl(), {
    transports: ['websocket'],
    autoConnect: true,
    reconnection: true,
    reconnectionDelay: 3000,
    reconnectionAttempts: Infinity,
    query: {
      client_id: clientId,
      client_type: 'web'
    }
  })

  socketInstance.on('connect', () => {
    isConnected.value = true
    console.log('[WS Center] 已连接, sid:', socketInstance?.id)
    
    // 重连后重新订阅之前的 topic
    if (subscribedTopics.value.length > 0) {
      socketInstance?.emit('subscribe', { topics: subscribedTopics.value })
    }
    
    connectHandlers.forEach(handler => handler())
  })

  socketInstance.on('disconnect', (reason) => {
    isConnected.value = false
    console.log('[WS Center] 连接关闭:', reason)
    disconnectHandlers.forEach(handler => handler())
  })

  socketInstance.on('connect_error', (error) => {
    console.error('[WS Center] 连接错误:', error)
    errorHandlers.forEach(handler => handler(error as Error))
  })

  socketInstance.on('zixuan', (data) => {
    zixuanHandlers.forEach(handler => handler(data as unknown[]))
  })

  socketInstance.on('recommendation', (data) => {
    recommendationHandlers.forEach(handler => handler(data as unknown))
  })

  socketInstance.on('backtest_progress', (data) => {
    backtestProgressHandlers.forEach(handler => handler(data as unknown))
  })

  socketInstance.on('backtest_log', (data) => {
    backtestLogHandlers.forEach(handler => handler(data as unknown))
  })

  socketInstance.on('backtest_completed', (data) => {
    backtestCompletedHandlers.forEach(handler => handler(data as unknown))
  })

  socketInstance.on('subscribed', (data) => {
    console.log('[WS Center] 订阅确认:', data)
  })

  return socketInstance
}

export function useWebSocket() {
  const socket = initSocket()
  refCount++

  onUnmounted(() => {
    refCount--
    // 不在这里断开连接，由 App.vue 统一管理
  })

  function connect(): void {
    if (socket.connected) return
    socket.connect()
  }

  function disconnect(): void {
    if (!socket.connected) return
    socket.disconnect()
  }

  function subscribe(topics: string[]): void {
    const newTopics = topics.filter(t => !subscribedTopics.value.includes(t))
    if (newTopics.length === 0) return

    if (!socket.connected) {
      // 未连接时先记录，连接后自动订阅
      subscribedTopics.value = [...subscribedTopics.value, ...newTopics]
      console.log('[WS Center] 记录待订阅:', newTopics)
      return
    }
    
    socket.emit('subscribe', { topics: newTopics })
    subscribedTopics.value = [...subscribedTopics.value, ...newTopics]
    console.log('[WS Center] 订阅:', newTopics)
  }

  function unsubscribe(topics: string[]): void {
    if (!socket.connected) return
    
    socket.emit('unsubscribe', { topics })
    subscribedTopics.value = subscribedTopics.value.filter(t => !topics.includes(t))
    console.log('[WS Center] 取消订阅:', topics)
  }

  function onZixuan(handler: ZixuanHandler): () => void {
    zixuanHandlers.push(handler)
    return () => {
      const index = zixuanHandlers.indexOf(handler)
      if (index > -1) zixuanHandlers.splice(index, 1)
    }
  }

  function onRecommendation(handler: RecommendationHandler): () => void {
    recommendationHandlers.push(handler)
    return () => {
      const index = recommendationHandlers.indexOf(handler)
      if (index > -1) recommendationHandlers.splice(index, 1)
    }
  }

  function onBacktestProgress(handler: BacktestProgressHandler): () => void {
    backtestProgressHandlers.push(handler)
    return () => {
      const index = backtestProgressHandlers.indexOf(handler)
      if (index > -1) backtestProgressHandlers.splice(index, 1)
    }
  }

  function onBacktestLog(handler: BacktestLogHandler): () => void {
    backtestLogHandlers.push(handler)
    return () => {
      const index = backtestLogHandlers.indexOf(handler)
      if (index > -1) backtestLogHandlers.splice(index, 1)
    }
  }

  function onBacktestCompleted(handler: BacktestCompletedHandler): () => void {
    backtestCompletedHandlers.push(handler)
    return () => {
      const index = backtestCompletedHandlers.indexOf(handler)
      if (index > -1) backtestCompletedHandlers.splice(index, 1)
    }
  }

  function onConnect(handler: ConnectHandler): () => void {
    connectHandlers.push(handler)
    return () => {
      const index = connectHandlers.indexOf(handler)
      if (index > -1) connectHandlers.splice(index, 1)
    }
  }

  function onDisconnect(handler: DisconnectHandler): () => void {
    disconnectHandlers.push(handler)
    return () => {
      const index = disconnectHandlers.indexOf(handler)
      if (index > -1) disconnectHandlers.splice(index, 1)
    }
  }

  function onError(handler: ErrorHandler): () => void {
    errorHandlers.push(handler)
    return () => {
      const index = errorHandlers.indexOf(handler)
      if (index > -1) errorHandlers.splice(index, 1)
    }
  }

  return {
    isConnected,
    subscribedTopics,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    onZixuan,
    onRecommendation,
    onBacktestProgress,
    onBacktestLog,
    onBacktestCompleted,
    onConnect,
    onDisconnect,
    onError
  }
}

export function getWebSocketRefCount(): number {
  return refCount
}

export function forceDisconnectWebSocket(): void {
  if (socketInstance) {
    socketInstance.disconnect()
    socketInstance = null
  }
  refCount = 0
  isConnected.value = false
  subscribedTopics.value = []
}
