<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import Icon from '@/components/common/Icon.vue'

const router = useRouter()

// 选择策略弹框
const showStrategyModal = ref(false)
const selectedStrategyId = ref<number | null>(null)

// 搜索和筛选
const searchQuery = ref('')
const filterStatus = ref('all')

// 模拟交易列表数据
const simulations = ref([
  {
    id: 1,
    name: '趋势先行A模拟',
    strategyName: '趋势先行A (大盘股)',
    status: 'running',
    statusText: '运行中',
    initialCapital: 1000000,
    currentCapital: 1124800,
    totalReturn: 12.48,
    todayReturn: 1.24,
    todayPL: 13840,
    holdingsValue: 824500,
    holdingsCount: 3,
    winRate: 68.5,
    tradeCount: 142,
    startDate: '2024-01-15',
    lastTradeTime: '10:32:15'
  },
  {
    id: 2,
    name: '高频套利V2模拟',
    strategyName: '高频套利V2',
    status: 'running',
    statusText: '运行中',
    initialCapital: 500000,
    currentCapital: 524000,
    totalReturn: 4.8,
    todayReturn: -0.32,
    todayPL: -1680,
    holdingsValue: 312000,
    holdingsCount: 2,
    winRate: 81.0,
    tradeCount: 567,
    startDate: '2024-02-01',
    lastTradeTime: '09:45:22'
  },
  {
    id: 3,
    name: '均线回归Alpha模拟',
    strategyName: '均线回归Alpha',
    status: 'paused',
    statusText: '已暂停',
    initialCapital: 1000000,
    currentCapital: 979000,
    totalReturn: -2.1,
    todayReturn: 0,
    todayPL: 0,
    holdingsValue: 545000,
    holdingsCount: 2,
    winRate: 52.3,
    tradeCount: 89,
    startDate: '2024-01-20',
    lastTradeTime: '14:28:00'
  },
  {
    id: 4,
    name: '小市值因子模拟',
    strategyName: '小市值因子策略',
    status: 'completed',
    statusText: '已完成',
    initialCapital: 1000000,
    currentCapital: 1356000,
    totalReturn: 35.6,
    todayReturn: 0,
    todayPL: 0,
    holdingsValue: 0,
    holdingsCount: 0,
    winRate: 72.1,
    tradeCount: 234,
    startDate: '2023-10-01',
    lastTradeTime: '2024-03-15'
  }
])

// 可选策略列表（用于弹框选择）
const availableStrategies = ref([
  {
    id: 1,
    name: '趋势先行A (大盘股)',
    type: 'MA交叉策略',
    returns: '+12.4%',
    winRate: '68.2%',
    risk: '中风险',
    selected: false
  },
  {
    id: 2,
    name: '均线回归Alpha',
    type: '量化多因子',
    returns: '-2.1%',
    winRate: '52.3%',
    risk: '高风险',
    selected: false
  },
  {
    id: 3,
    name: '高频套利V2',
    type: '高频交易',
    returns: '+4.8%',
    winRate: '81.0%',
    risk: '低风险',
    selected: false
  },
  {
    id: 4,
    name: '风格轮动',
    type: '多因子策略',
    returns: '+24.8%',
    winRate: '65.4%',
    risk: '中风险',
    selected: false
  }
])

// 统计汇总
const stats = computed(() => {
  const runningCount = simulations.value.filter(s => s.status === 'running').length
  const totalReturn = simulations.value.reduce((sum, s) => sum + s.totalReturn, 0)
  const totalTodayPL = simulations.value.reduce((sum, s) => sum + s.todayPL, 0)
  return {
    runningCount,
    totalSimulations: simulations.value.length,
    totalReturn,
    totalTodayPL
  }
})

// 筛选后的列表
const filteredSimulations = computed(() => {
  return simulations.value.filter(sim => {
    const matchSearch = sim.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      sim.strategyName.toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchStatus = filterStatus.value === 'all' || sim.status === filterStatus.value
    return matchSearch && matchStatus
  })
})

// 打开选择策略弹框
const openStrategyModal = () => {
  showStrategyModal.value = true
}

// 关闭弹框
const closeStrategyModal = () => {
  showStrategyModal.value = false
  selectedStrategyId.value = null
  // 重置选中状态
  availableStrategies.value.forEach(s => s.selected = false)
}

// 选择策略
const selectStrategy = (strategy: typeof availableStrategies.value[0]) => {
  availableStrategies.value.forEach(s => s.selected = false)
  strategy.selected = true
  selectedStrategyId.value = strategy.id
}

// 创建模拟
const createSimulation = () => {
  if (!selectedStrategyId.value) return
  
  // 模拟创建成功
  const strategy = availableStrategies.value.find(s => s.id === selectedStrategyId.value)
  const newSimulation = {
    id: simulations.value.length + 1,
    name: `${strategy?.name}模拟`,
    strategyName: strategy?.name || '',
    status: 'running',
    statusText: '运行中',
    initialCapital: 1000000,
    currentCapital: 1000000,
    totalReturn: 0,
    todayReturn: 0,
    todayPL: 0,
    holdingsValue: 0,
    holdingsCount: 0,
    winRate: parseFloat(strategy?.winRate || '0'),
    tradeCount: 0,
    startDate: new Date().toISOString().split('T')[0],
    lastTradeTime: '--'
  }
  
  simulations.value.unshift(newSimulation)
  closeStrategyModal()
  
  // 跳转到详情页
  router.push(`/simulation/detail/${newSimulation.id}`)
}

// 跳转到详情页
const viewDetail = (id: number) => {
  router.push(`/simulation/detail/${id}`)
}

// 格式化金额
const formatMoney = (value: number) => {
  return value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

// 状态颜色
const getStatusColor = (status: string) => {
  switch (status) {
    case 'running':
      return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
    case 'paused':
      return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
    case 'completed':
      return 'bg-gray-100 text-textSub dark:bg-gray-800'
    default:
      return 'bg-gray-100 text-textSub'
  }
}

// 收益率颜色
const getReturnColor = (value: number) => {
  return value > 0 ? 'text-up' : value < 0 ? 'text-down' : 'text-textSub'
}
</script>

<template>
  <div class="min-h-screen bg-bgMain p-6">
    <!-- 页面标题 -->
    <div class="flex justify-between items-start mb-6">
      <div>
        <h1 class="text-xl font-bold text-textMain">模拟交易</h1>
        <p class="text-sm text-textMute mt-1">使用策略进行虚拟交易，验证交易逻辑</p>
      </div>
      <button 
        class="bg-primary text-white px-4 py-2 rounded text-sm font-semibold hover:opacity-90 flex items-center gap-2 transition-opacity"
        @click="openStrategyModal"
      >
        <Icon icon="mdi:plus" :size="16" />
        新建模拟
      </button>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-4 gap-4 mb-6">
      <div class="bg-card p-4 rounded-lg shadow-sm border border-border">
        <p class="text-xs text-textMute mb-1">运行中模拟</p>
        <p class="text-2xl font-bold font-numeric text-textMain">{{ stats.runningCount }}</p>
        <p class="text-xs text-textMute mt-1">共 {{ stats.totalSimulations }} 个模拟</p>
      </div>
      <div class="bg-card p-4 rounded-lg shadow-sm border border-border">
        <p class="text-xs text-textMute mb-1">累计收益率</p>
        <p class="text-2xl font-bold font-numeric" :class="getReturnColor(stats.totalReturn)">
          {{ stats.totalReturn > 0 ? '+' : '' }}{{ stats.totalReturn.toFixed(2) }}%
        </p>
        <p class="text-xs text-textMute mt-1">所有模拟汇总</p>
      </div>
      <div class="bg-card p-4 rounded-lg shadow-sm border border-border">
        <p class="text-xs text-textMute mb-1">今日盈亏</p>
        <p class="text-2xl font-bold font-numeric" :class="getReturnColor(stats.totalTodayPL)">
          {{ stats.totalTodayPL > 0 ? '+' : '' }}{{ formatMoney(stats.totalTodayPL) }}
        </p>
        <p class="text-xs text-textMute mt-1">当日实时更新</p>
      </div>
      <div class="bg-card p-4 rounded-lg shadow-sm border border-border">
        <p class="text-xs text-textMute mb-1">策略库</p>
        <p class="text-2xl font-bold font-numeric text-primary">{{ availableStrategies.length }}</p>
        <p class="text-xs text-textMute mt-1">可引用策略</p>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="flex items-center gap-4 mb-4">
      <div class="relative flex-1 max-w-md">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜索模拟名称或策略..."
          class="w-full h-9 pl-9 pr-4 bg-card border border-border rounded-lg text-sm text-textMain focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
        />
        <Icon icon="mdi:magnify" :size="16" class="absolute left-3 top-1/2 -translate-y-1/2 text-textMute" />
      </div>
      <div class="flex items-center gap-2">
        <button
          v-for="status in ['all', 'running', 'paused', 'completed']"
          :key="status"
          :class="[
            'px-3 py-1.5 text-xs font-semibold rounded transition-all',
            filterStatus === status
              ? 'bg-primary text-white'
              : 'bg-card border border-border text-textSub hover:border-primary hover:text-primary'
          ]"
          @click="filterStatus = status"
        >
          {{ status === 'all' ? '全部' : status === 'running' ? '运行中' : status === 'paused' ? '已暂停' : '已完成' }}
        </button>
      </div>
    </div>

    <!-- 模拟交易列表 -->
    <div class="bg-card rounded-xl border border-border shadow-sm overflow-hidden">
      <table class="w-full">
        <thead>
          <tr class="bg-gray-50/50 dark:bg-gray-800/50 text-textMute text-[11px] uppercase tracking-wider">
            <th class="px-6 py-3.5 font-semibold text-left">模拟名称</th>
            <th class="px-6 py-3.5 font-semibold text-center">状态</th>
            <th class="px-6 py-3.5 font-semibold text-right">初始资金</th>
            <th class="px-6 py-3.5 font-semibold text-right">当前资金</th>
            <th class="px-6 py-3.5 font-semibold text-right">累计收益</th>
            <th class="px-6 py-3.5 font-semibold text-right">今日盈亏</th>
            <th class="px-6 py-3.5 font-semibold text-right">胜率</th>
            <th class="px-6 py-3.5 font-semibold text-center">持仓</th>
            <th class="px-6 py-3.5 font-semibold text-center">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-border">
          <tr 
            v-for="sim in filteredSimulations"
            :key="sim.id"
            class="hover:bg-primary/5 transition-colors cursor-pointer"
            @click="viewDetail(sim.id)"
          >
            <td class="px-6 py-4">
              <div class="flex flex-col">
                <span class="text-sm font-bold text-textMain">{{ sim.name }}</span>
                <span class="text-[10px] text-textMute mt-0.5">{{ sim.strategyName }}</span>
              </div>
            </td>
            <td class="px-6 py-4 text-center">
              <span 
                :class="[
                  'inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold',
                  getStatusColor(sim.status)
                ]"
              >
                {{ sim.statusText }}
              </span>
            </td>
            <td class="px-6 py-4 text-right font-numeric text-sm text-textSub">
              {{ formatMoney(sim.initialCapital) }}
            </td>
            <td class="px-6 py-4 text-right font-numeric text-sm font-medium text-textMain">
              {{ formatMoney(sim.currentCapital) }}
            </td>
            <td class="px-6 py-4 text-right">
              <span class="font-numeric text-sm font-bold" :class="getReturnColor(sim.totalReturn)">
                {{ sim.totalReturn > 0 ? '+' : '' }}{{ sim.totalReturn.toFixed(2) }}%
              </span>
            </td>
            <td class="px-6 py-4 text-right">
              <span class="font-numeric text-sm font-bold" :class="getReturnColor(sim.todayPL)">
                {{ sim.todayPL > 0 ? '+' : '' }}{{ formatMoney(sim.todayPL) }}
              </span>
              <span class="block text-[10px] text-textMute mt-0.5">
                {{ sim.todayReturn > 0 ? '+' : '' }}{{ sim.todayReturn.toFixed(2) }}%
              </span>
            </td>
            <td class="px-6 py-4 text-right font-numeric text-sm text-textSub">
              {{ sim.winRate.toFixed(1) }}%
            </td>
            <td class="px-6 py-4 text-center">
              <div class="flex flex-col items-center">
                <span class="text-sm font-medium text-textMain">{{ sim.holdingsCount }}</span>
                <span class="text-[10px] text-textMute">只股票</span>
              </div>
            </td>
            <td class="px-6 py-4 text-center" @click.stop>
              <div class="flex items-center justify-center gap-2">
                <button 
                  class="text-primary hover:underline text-xs font-semibold"
                  @click="viewDetail(sim.id)"
                >
                  详情
                </button>
                <button 
                  v-if="sim.status === 'running'"
                  class="text-yellow-600 hover:text-yellow-700 text-xs font-semibold"
                >
                  暂停
                </button>
                <button 
                  v-if="sim.status === 'paused'"
                  class="text-green-600 hover:text-green-700 text-xs font-semibold"
                >
                  恢复
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- 空状态 -->
      <div v-if="filteredSimulations.length === 0" class="py-12 text-center">
        <Icon icon="mdi:folder-open-outline" :size="48" class="mx-auto text-textMute mb-3" />
        <p class="text-textSub text-sm">暂无模拟交易记录</p>
        <button 
          class="mt-4 text-primary text-sm font-semibold hover:underline"
          @click="openStrategyModal"
        >
          创建第一个模拟
        </button>
      </div>
    </div>

    <!-- 选择策略弹框 -->
    <Teleport to="body">
      <div 
        v-if="showStrategyModal" 
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
        @click.self="closeStrategyModal"
      >
        <div class="bg-card rounded-xl shadow-2xl w-[560px] max-h-[80vh] overflow-hidden">
          <!-- 弹框头部 -->
          <div class="px-6 py-4 border-b border-border flex items-center justify-between">
            <div>
              <h3 class="font-bold text-lg text-textMain">选择策略</h3>
              <p class="text-xs text-textMute mt-0.5">选择一个策略来创建模拟交易</p>
            </div>
            <button 
              class="text-textMute hover:text-textMain transition-colors"
              @click="closeStrategyModal"
            >
              <Icon icon="mdi:close" :size="20" />
            </button>
          </div>

          <!-- 策略列表 -->
          <div class="p-4 space-y-3 max-h-[400px] overflow-y-auto custom-scrollbar">
            <div
              v-for="strategy in availableStrategies"
              :key="strategy.id"
              :class="[
                'p-4 rounded-lg border-2 cursor-pointer transition-all',
                strategy.selected 
                  ? 'border-primary bg-primary/5' 
                  : 'border-border hover:border-primary/50'
              ]"
              @click="selectStrategy(strategy)"
            >
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <div class="flex items-center gap-2 mb-1">
                    <span class="font-bold text-sm text-textMain">{{ strategy.name }}</span>
                    <span class="text-[10px] px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-textSub">
                      {{ strategy.type }}
                    </span>
                  </div>
                  <div class="flex items-center gap-4 text-xs text-textMute">
                    <span>历史收益: <span :class="strategy.returns.startsWith('+') ? 'text-up' : 'text-down'" class="font-semibold">{{ strategy.returns }}</span></span>
                    <span>胜率: <span class="font-semibold text-textSub">{{ strategy.winRate }}</span></span>
                    <span>风险: <span class="font-semibold text-yellow-500">{{ strategy.risk }}</span></span>
                  </div>
                </div>
                <div 
                  :class="[
                    'w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all',
                    strategy.selected 
                      ? 'border-primary bg-primary' 
                      : 'border-border'
                  ]"
                >
                  <Icon 
                    v-if="strategy.selected" 
                    icon="mdi:check" 
                    :size="12" 
                    class="text-white" 
                  />
                </div>
              </div>
            </div>
          </div>

          <!-- 弹框底部 -->
          <div class="px-6 py-4 border-t border-border flex items-center justify-between bg-gray-50/50 dark:bg-gray-800/50">
            <div class="text-xs text-textMute">
              <span v-if="selectedStrategyId">
                已选择: <span class="text-primary font-semibold">{{ availableStrategies.find(s => s.id === selectedStrategyId)?.name }}</span>
              </span>
              <span v-else>请选择一个策略</span>
            </div>
            <div class="flex items-center gap-3">
              <button 
                class="px-4 py-2 border border-border rounded text-sm font-semibold text-textSub hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                @click="closeStrategyModal"
              >
                取消
              </button>
              <button 
                :class="[
                  'px-4 py-2 rounded text-sm font-semibold transition-opacity',
                  selectedStrategyId 
                    ? 'bg-primary text-white hover:opacity-90' 
                    : 'bg-gray-200 text-textMute cursor-not-allowed'
                ]"
                :disabled="!selectedStrategyId"
                @click="createSimulation"
              >
                创建模拟
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
