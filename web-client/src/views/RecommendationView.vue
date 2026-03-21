<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { getLatestNews, type NewsItem } from '@/api/news'
import { useWebSocket, parseStockInfo, type RecommendationData } from '@/utils/websocket'

interface Stock {
  name: string
  code: string
  score: number
}

interface Recommendation {
  id: number
  type: string
  typeColor: string
  source: string
  time: string
  title: string
  analysis: string
  sectors: string[]
  stocks: Stock[]
}

const {
  connect,
  disconnect,
  subscribe,
  onMessage,
  onConnect,
  onDisconnect,
  onError
} = useWebSocket()

const recommendations = ref<Recommendation[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const isWsConnected = ref(false)

// 统计数据
const stats = ref([
  { label: '今日处理新闻', value: '12,482', change: '+12% vs 昨', trend: 'up' },
  { label: '今日板块推荐', value: '12', change: '查看全部', trend: 'neutral' },
  { label: 'AI胜率 (近30日)', value: '72.4%', change: '跑赢大盘', trend: 'down' },
  { label: '系统延迟', value: '14ms', change: '优于 99% 节点', trend: 'neutral' }
])

// 筛选标签
const filterTabs = ref([
  { name: '实时推送', active: true },
  { name: '机构调研', active: false },
  { name: '研报精选', active: false },
  { name: '北向资金', active: false },
  { name: '政策解读', active: false }
])

function formatTime(publishTime: string | null): string {
  if (!publishTime) return ''
  const date = new Date(publishTime)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).replace(/\//g, '-')
}

function getTypeAndColor(title: string, source: string): { type: string; typeColor: string } {
  const sourceTypes: Record<string, { type: string; color: string }> = {
    '东方财富': { type: '资讯', color: 'blue' },
    '华泰证券': { type: '研报精选', color: 'blue' },
    'Wind资讯': { type: '资金流向', color: 'green' },
    '中金公司': { type: '研报精选', color: 'blue' },
    '国泰君安': { type: '研报精选', color: 'blue' }
  }
  
  const matched = sourceTypes[source]
  if (matched) {
    return { type: matched.type, typeColor: matched.color }
  }
  
  const lowerTitle = title.toLowerCase()
  if (lowerTitle.includes('资金') || lowerTitle.includes('净买入') || lowerTitle.includes('北向')) {
    return { type: '资金流向', typeColor: 'green' }
  }
  if (lowerTitle.includes('政策') || lowerTitle.includes('监管')) {
    return { type: '政策解读', typeColor: 'purple' }
  }
  if (lowerTitle.includes('调研') || lowerTitle.includes('机构')) {
    return { type: '机构调研', typeColor: 'red' }
  }
  return { type: '资讯', typeColor: 'blue' }
}

function formatStockCode(code: string | null): string {
  if (!code) return '-'
  const codeNum = parseInt(code)
  if (isNaN(codeNum)) return code
  return code + (codeNum < 500000 ? '.SH' : '.SZ')
}

// 转换 API 数据为 Recommendation 格式
function convertApiToRecommendation(item: NewsItem): Recommendation {
  const { type, typeColor } = getTypeAndColor(item.title, item.source)
  
  const stocks: Stock[] = (item.stocks || []).map(s => ({
    name: s.name,
    code: formatStockCode(s.code),
    score: s.score || 0
  }))
  
  return {
    id: item.id,
    type,
    typeColor,
    source: item.source,
    time: formatTime(item.publish_time),
    title: item.title,
    analysis: item.analysis,
    sectors: item.sectors || [],
    stocks
  }
}

// 转换 WebSocket 数据为 Recommendation 格式
function convertWsToRecommendation(data: RecommendationData): Recommendation {
  const news = data.news
  const analysis = data.analysis

  const stocks: Stock[] = (analysis.利好股票 || []).map((stock: string | { stock_code: string; stock_name: string; score: string }) => {
    if (typeof stock === 'object') {
      const codeNum = parseInt(stock.stock_code)
      return {
        name: stock.stock_name,
        code: stock.stock_code + (codeNum < 500000 ? '.SH' : '.SZ'),
        score: parseInt(stock.score) || 0
      }
    }
    const parsed = parseStockInfo(stock)
    return parsed || { name: stock, code: '-', score: 0 }
  })

  const { type, typeColor } = getTypeAndColor(news.title, news.source)

  return {
    id: Date.now(),
    type,
    typeColor,
    source: news.source,
    time: news.publish_time,
    title: news.title,
    analysis: analysis.详细分析 || '',
    sectors: analysis.利好版块 || [],
    stocks
  }
}

// 添加 WebSocket 推送的资讯到列表
function addWebSocketRecommendation(data: RecommendationData) {
  const newRec = convertWsToRecommendation(data)
  recommendations.value.unshift(newRec)
  
  // 最多保留50条
  if (recommendations.value.length > 50) {
    recommendations.value.pop()
  }
}

// 获取初始数据
async function fetchNews() {
  loading.value = true
  error.value = null
  
  try {
    const newsList = await getLatestNews(10)
    recommendations.value = newsList.map(convertApiToRecommendation)
  } catch (e) {
    console.error('获取资讯失败:', e)
    error.value = e instanceof Error ? e.message : '获取数据失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  // 初始化 WebSocket
  onConnect(() => {
    isWsConnected.value = true
    subscribe(['recommendation'])
  })

  onDisconnect(() => {
    isWsConnected.value = false
  })

  onError((err) => {
    console.error('WebSocket错误:', err)
  })

  onMessage(addWebSocketRecommendation)
  
  // 连接 WebSocket
  connect()
  
  // 获取初始数据
  fetchNews()
})

onUnmounted(() => {
  disconnect()
})
</script>

<template>
  <div class="min-h-screen bg-bgMain">
    <!-- Connection Status -->
    <div class="px-6 pt-4 flex items-center gap-2">
      <span
        :class="[
          'w-2 h-2 rounded-full',
          isWsConnected ? 'bg-green-500 animate-pulse' : 'bg-gray-300'
        ]"
      ></span>
      <span class="text-xs font-bold text-textMute">
        {{ isWsConnected ? '实时连接' : '连接中...' }}
      </span>
    </div>

    <!-- Stats Summary -->
    <div class="grid grid-cols-4 gap-4 p-6 pb-0">
      <div
        v-for="(stat, index) in stats"
        :key="index"
        class="bg-card p-4 border border-border flex justify-between items-end"
      >
        <div>
          <p class="text-[10px] text-textMute font-bold uppercase tracking-wider">{{ stat.label }}</p>
          <p class="text-2xl font-bold text-textMain">{{ stat.value }}</p>
        </div>
        <span
          :class="[
            'text-xs font-bold',
            stat.trend === 'up' ? 'text-up' :
            stat.trend === 'down' ? 'text-down' : 'text-primary'
          ]"
        >
          {{ stat.change }}
        </span>
      </div>
    </div>

    <!-- Filter Tabs -->
    <div class="flex gap-2 px-6 pt-4">
      <button
        v-for="tab in filterTabs"
        :key="tab.name"
        :class="[
          'px-4 py-1.5 text-xs font-bold rounded transition-all',
          tab.active
            ? 'bg-primary text-white'
            : 'bg-card border border-border text-textSub hover:border-primary hover:text-primary'
        ]"
      >
        {{ tab.name }}
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="p-6">
      <div class="flex items-center justify-center h-64">
        <div class="text-textMute">加载中...</div>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="p-6">
      <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <p class="text-red-600 dark:text-red-400 text-sm">{{ error }}</p>
        <button 
          @click="fetchNews"
          class="mt-2 text-sm text-primary hover:underline"
        >
          重试
        </button>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="recommendations.length === 0" class="p-6">
      <div class="flex items-center justify-center h-64">
        <div class="text-textMute">暂无资讯数据</div>
      </div>
    </div>

    <!-- Recommendation List -->
    <div v-else class="p-6 space-y-4">
      <div
        v-for="rec in recommendations"
        :key="rec.id"
        class="bg-card border border-border transition-colors shadow-sm overflow-hidden flex"
      >
        <div class="p-4 border-r border-border flex-1">
          <div class="flex items-center gap-3 mb-2">
            <span
              :class="[
                'text-[10px] font-bold px-1.5 py-0.5 rounded',
                rec.typeColor === 'red' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                rec.typeColor === 'blue' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' :
                rec.typeColor === 'green' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400'
              ]"
            >
              {{ rec.type }}
            </span>
            <span class="text-xs text-textMute font-medium">来源：{{ rec.source }} • {{ rec.time }}</span>
          </div>
          <h2 class="text-lg font-bold text-textMain mb-2 leading-snug hover:text-primary cursor-pointer transition-colors">
            {{ rec.title }}
          </h2>
          <div v-if="rec.analysis" class="bg-gray-50 dark:bg-gray-800 p-3 mb-3 border-l-2 border-primary">
            <p class="text-xs leading-relaxed text-textSub">
              <span class="font-bold text-textMain">AI解析：</span>
              {{ rec.analysis }}
            </p>
          </div>
          <div v-if="rec.sectors.length > 0" class="flex flex-wrap gap-2 items-center">
            <span class="text-xs font-bold text-textMute">利好板块:</span>
            <span
              v-for="sector in rec.sectors"
              :key="sector"
              class="px-2 py-0.5 bg-primary/10 text-primary text-[11px] font-bold rounded"
            >
              {{ sector }}
            </span>
          </div>
        </div>

        <div v-if="rec.stocks.length > 0" class="w-[300px] min-w-[300px] bg-gray-50/30 dark:bg-gray-800/30 p-3">
          <table class="w-full table-fixed">
            <thead class="bg-transparent">
              <tr>
                <th class="text-left font-bold text-textMute text-xs py-1 w-[100px]">利好股票</th>
                <th class="text-left font-bold text-textMute text-xs py-1 w-[80px]">代码</th>
                <th class="text-right font-bold text-textMute text-xs py-1">AI评分</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="stock in rec.stocks"
                :key="stock.code"
                class="cursor-pointer"
              >
                <td class="py-2 truncate">
                  <span class="font-bold text-primary">{{ stock.name }}</span>
                </td>
                <td class="py-2">
                  <span class="text-textSub text-xs font-numeric">{{ stock.code }}</span>
                </td>
                <td class="py-2 text-right">
                  <span
                    :class="[
                      'inline-flex items-center justify-center min-w-[36px] h-5 px-1.5 rounded text-xs font-bold font-numeric',
                      stock.score >= 90 ? 'bg-up/20 text-up' :
                      stock.score >= 80 ? 'bg-up/10 text-up/80' :
                      'bg-gray-200 text-textSub dark:bg-gray-700'
                    ]"
                  >
                    {{ stock.score }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>
