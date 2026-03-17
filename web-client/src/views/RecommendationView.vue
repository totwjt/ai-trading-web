<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import Icon from '@/components/common/Icon.vue'
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
  wsClient, 
  isConnected, 
  connect, 
  disconnect, 
  subscribe,
  onMessage,
  onConnect,
  onDisconnect,
  onError
} = useWebSocket()

const isWsConnected = ref(false)
const connectionStatus = ref('disconnected')

// 模拟统计数据
const stats = ref([
  { label: '今日处理新闻', value: '12,482', change: '+12% vs 昨', trend: 'up' },
  { label: '今日板块推荐', value: '12', change: '查看全部', trend: 'neutral' },
  { label: 'AI胜率 (近30日)', value: '72.4%', change: '跑赢大盘', trend: 'down' },
  { label: '系统延迟', value: '14ms', change: '优于 99% 节点', trend: 'neutral' }
])

// 模拟筛选标签
const filterTabs = ref([
  { name: '全部推荐', active: true },
  { name: '机构调研', active: false },
  { name: '研报精选', active: false },
  { name: '北向资金', active: false },
  { name: '政策解读', active: false }
])

// 模拟推荐数据
const recommendations = ref([
  {
    id: 1,
    type: '深度解析',
    typeColor: 'red',
    source: '东方财富',
    time: '2023-10-24 09:30',
    title: 'Meta裁员标志着效率优先战略调整，云服务外包迎来新机遇',
    analysis: '通过大模型分析全球头部互联网企业财报，识别出在降本增效的大背景下，企业正加速将非核心研发业务外包。Meta的策略转型预示着北美大型科技公司对外部IT服务供应商的依赖度将提升，尤其是具备数字化转型交付能力的头部服务商，有望获得确定性溢价空间。',
    sectors: ['人力资源服务', '云计算', 'IT外包', '跨境交付'],
    stocks: [
      { name: '科大讯飞', code: '002230.SZ', score: 98 },
      { name: '中软国际', code: '0354.HK', score: 92 },
      { name: '软通动力', code: '301236.SZ', score: 89 }
    ]
  },
  {
    id: 2,
    type: '研报精选',
    typeColor: 'blue',
    source: '华泰证券',
    time: '2023-10-24 10:15',
    title: '半导体国产化进程加速：设备端采购订单Q3环比增长40%',
    analysis: '分析国内主要晶圆厂招投标数据，发现刻蚀机、薄膜沉积设备等关键环节国产替代率显著提升。近期产业链调研显示，下游排产已排至明年Q2。AI模型预测，具有先进制程突破能力的设备厂商将在接下来的财报季迎来业绩与估值的双重修复。',
    sectors: ['半导体设备', '国产化替代', '电子元器件'],
    stocks: [
      { name: '中微公司', code: '688012.SH', score: 96 },
      { name: '北方华创', code: '002371.SZ', score: 94 },
      { name: '拓荆科技', code: '688072.SH', score: 85 }
    ]
  },
  {
    id: 3,
    type: '资金流向',
    typeColor: 'green',
    source: 'Wind资讯',
    time: '2023-10-24 11:45',
    title: '北向资金大幅净买入白酒板块，消费复苏预期重新点燃',
    analysis: '今日早盘陆股通资金异常流入核心蓝筹，其中白酒龙头个股流入量占全天预计交易量的15%。AI大数据回测显示，白酒板块在资金连续3天净买入后，未来一周出现阶段性底部的概率为82%。建议关注高端及次高端白酒龙头。',
    sectors: ['白酒', '核心资产', '消费升级'],
    stocks: [
      { name: '贵州茅台', code: '600519.SH', score: 91 },
      { name: '泸州老窖', code: '000568.SZ', score: 88 },
      { name: '山西汾酒', code: '600809.SH', score: 84 }
    ]
  }
])

function convertWsDataToRecommendation(data: RecommendationData): Recommendation {
  const news = data.news
  const analysis = data.analysis
  
  const stocks: Stock[] = (analysis.利好股票 || []).map((stockStr: string) => {
    const parsed = parseStockInfo(stockStr)
    return parsed || { name: stockStr, code: '-', score: 0 }
  })
  
  const typeColors: Record<string, string> = {
    '深度解析': 'red',
    '研报精选': 'blue',
    '资金流向': 'green',
    '政策解读': 'purple'
  }
  
  const typeColor = typeColors[news.title.slice(0, 4)] || 'blue'
  
  return {
    id: Date.now(),
    type: '实时推送',
    typeColor,
    source: news.source,
    time: news.publish_time,
    title: news.title,
    analysis: analysis.详细分析,
    sectors: analysis.利好版块 || [],
    stocks
  }
}

function addRecommendation(data: RecommendationData) {
  const newRec = convertWsDataToRecommendation(data)
  recommendations.value.unshift(newRec)
  
  if (recommendations.value.length > 50) {
    recommendations.value.pop()
  }
}

onMounted(() => {
  onConnect(() => {
    isWsConnected.value = true
    connectionStatus.value = 'connected'
    subscribe(['recommendation'])
  })
  
  onDisconnect(() => {
    isWsConnected.value = false
    connectionStatus.value = 'disconnected'
  })
  
  onError((error) => {
    console.error('WebSocket错误:', error)
    connectionStatus.value = 'error'
  })
  
  onMessage(addRecommendation)
  
  connect()
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
        class="bg-white p-4 border border-gray-100 flex justify-between items-end"
      >
        <div>
          <p class="text-[10px] text-textMute font-bold uppercase tracking-wider">{{ stat.label }}</p>
          <p class="text-2xl font-bold">{{ stat.value }}</p>
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
            : 'bg-white border border-gray-200 text-textSub hover:border-primary hover:text-primary'
        ]"
      >
        {{ tab.name }}
      </button>
    </div>

    <!-- Recommendation List -->
    <div class="p-6 space-y-4">
      <div 
        v-for="rec in recommendations"
        :key="rec.id"
        class="bg-white border border-gray-100 hover:border-primary/50 transition-colors shadow-sm overflow-hidden flex"
      >
        <!-- Left: Analysis Logic -->
        <div class="w-[65%] p-4 border-r border-gray-100">
          <div class="flex items-center gap-3 mb-2">
            <span 
              :class="[
                'text-[10px] font-bold px-1.5 py-0.5 rounded',
                rec.typeColor === 'red' ? 'bg-red-100 text-red-700' :
                rec.typeColor === 'blue' ? 'bg-blue-100 text-blue-700' :
                rec.typeColor === 'green' ? 'bg-green-100 text-green-700' :
                'bg-purple-100 text-purple-700'
              ]"
            >
              {{ rec.type }}
            </span>
            <span class="text-xs text-textMute font-medium">来源：{{ rec.source }} • {{ rec.time }}</span>
          </div>
          <h2 class="text-lg font-bold text-textMain mb-2 leading-snug hover:text-primary cursor-pointer transition-colors">
            {{ rec.title }}
          </h2>
          <div class="bg-gray-50 p-3 mb-3 border-l-2 border-primary">
            <p class="text-xs leading-relaxed text-textSub">
              <span class="font-bold text-textMain">AI解析逻辑：</span>
              {{ rec.analysis }}
            </p>
          </div>
          <div class="flex flex-wrap gap-2 items-center">
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
        
        <!-- Right: Stocks Table -->
        <div class="w-[35%] bg-gray-50/30">
          <table class="w-full h-full density-table">
            <thead class="bg-gray-50">
              <tr>
                <th class="text-left font-bold text-textMute">利好股票</th>
                <th class="text-left font-bold text-textMute">代码</th>
                <th class="text-right font-bold text-textMute">AI评分</th>
                <th class="text-right font-bold text-textMute">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr 
                v-for="stock in rec.stocks"
                :key="stock.code"
                class="hover:bg-blue-50"
              >
                <td class="font-bold text-textMain">{{ stock.name }}</td>
                <td class="text-textMute">{{ stock.code }}</td>
                <td class="text-right text-up font-bold text-sm font-numeric">{{ stock.score }}</td>
                <td class="text-right">
                  <button class="text-sm text-primary">
                    <Icon icon="add_circle" :size="16" />
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Load More -->
    <div class="pb-8 flex justify-center">
      <button class="px-12 py-2 border-2 border-gray-200 text-textMute text-xs font-bold hover:border-primary hover:text-primary transition-all rounded">
        加载更多分析数据
      </button>
    </div>
  </div>
</template>