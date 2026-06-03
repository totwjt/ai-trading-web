<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Icon from '@/components/common/Icon.vue'
import {
  getSimulations,
  getSimulationStats,
  getAvailableStrategies,
  createSimulation,
  pauseSimulation,
  resumeSimulation,
} from '@/api/simulation'
import type { SimulationItem, AvailableStrategy } from '@/api/simulation'

const router = useRouter()

// 加载状态
const loading = ref(false)
const error = ref('')

// 选择策略弹框
const showStrategyModal = ref(false)
const selectedStrategyId = ref<number | null>(null)
const creating = ref(false)

// 搜索和筛选
const searchQuery = ref('')
const filterStatus = ref('all')

// 模拟交易列表（来自 API）
const simulations = ref<SimulationItem[]>([])
const totalSimulationsCount = ref(0)

// 统计汇总（来自 API）
const stats = ref({
  runningCount: 0,
  totalSimulations: 0,
  totalReturn: 0,
  todayPL: 0,
  strategyCount: 0,
})

// 可选策略列表（来自 API）
const availableStrategies = ref<AvailableStrategy[]>([])

// 筛选后的列表
const filteredSimulations = computed(() => {
  return simulations.value.filter(sim => {
    const matchSearch = sim.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      (sim.strategyName || '').toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchStatus = filterStatus.value === 'all' || sim.status === filterStatus.value
    return matchSearch && matchStatus
  })
})

// 从 API 加载所有数据
async function loadData() {
  loading.value = true
  error.value = ''
  try {
    const [simRes, statsRes] = await Promise.all([
      getSimulations({ page: 1, page_size: 50 }),
      getSimulationStats(),
    ])
    simulations.value = simRes.items
    totalSimulationsCount.value = simRes.total
    stats.value = {
      runningCount: (statsRes as any).running_count ?? (statsRes as any).runningCount,
      totalSimulations: (statsRes as any).total_simulations ?? (statsRes as any).totalSimulations,
      totalReturn: (statsRes as any).total_return ?? (statsRes as any).totalReturn,
      todayPL: (statsRes as any).todayPL ?? (statsRes as any).totalTodayPL,
      strategyCount: (statsRes as any).strategy_count ?? (statsRes as any).strategyCount,
    }
  } catch (e: any) {
    error.value = e.message || '加载失败'
    console.error('加载模拟交易数据失败:', e)
  } finally {
    loading.value = false
  }
}

// 打开选择策略弹框（懒加载策略列表）
const openStrategyModal = async () => {
  showStrategyModal.value = true
  if (availableStrategies.value.length === 0) {
    try {
      availableStrategies.value = await getAvailableStrategies()
    } catch (e: any) {
      console.error('获取策略列表失败:', e)
    }
  }
}

// 关闭弹框
const closeStrategyModal = () => {
  showStrategyModal.value = false
  selectedStrategyId.value = null
  availableStrategies.value.forEach(s => s.selected = false)
}

// 选择策略
const selectStrategy = (strategy: AvailableStrategy) => {
  availableStrategies.value.forEach(s => s.selected = false)
  strategy.selected = true
  selectedStrategyId.value = strategy.id
}

// 创建模拟（调用 API）
const handleCreateSimulation = async () => {
  if (!selectedStrategyId.value || creating.value) return
  creating.value = true
  try {
    const result = await createSimulation({ strategy_id: selectedStrategyId.value })
    closeStrategyModal()
    await loadData() // 刷新列表
    const newId = result?.id
    if (newId) {
      router.push(`/simulation/detail/${newId}`)
    }
  } catch (e: any) {
    console.error('创建模拟失败:', e)
    error.value = e.message || '创建模拟失败'
  } finally {
    creating.value = false
  }
}

// 跳转到详情页
const viewDetail = (id: number) => {
  router.push(`/simulation/detail/${id}`)
}

// 列表页暂停模拟
const handleListPause = async (id: number) => {
  try {
    await pauseSimulation(id)
    const sim = simulations.value.find(s => s.id === id)
    if (sim) {
      sim.status = 'paused'
    }
  } catch (e: any) {
    error.value = e.message || '暂停失败'
  }
}

// 列表页恢复模拟
const handleListResume = async (id: number) => {
  try {
    await resumeSimulation(id)
    const sim = simulations.value.find(s => s.id === id)
    if (sim) {
      sim.status = 'running'
    }
  } catch (e: any) {
    error.value = e.message || '恢复失败'
  }
}

// 格式化金额
const formatMoney = (value: number) => {
  return (value || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
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
  return (value || 0) > 0 ? 'text-up' : (value || 0) < 0 ? 'text-down' : 'text-textSub'
}

// 状态文本映射
onMounted(() => {
  loadData()
})

</script>

<template>
  <div class="min-h-[calc(100vh-48px)] bg-bgMain p-3">
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
          {{ stats.totalReturn != null ? ((stats.totalReturn > 0 ? '+' : '') + stats.totalReturn.toFixed(2) + '%') : '' }}
        </p>
        <p class="text-xs text-textMute mt-1">所有模拟汇总</p>
      </div>
      <div class="bg-card p-4 rounded-lg shadow-sm border border-border">
        <p class="text-xs text-textMute mb-1">今日盈亏</p>
        <p class="text-2xl font-bold font-numeric" :class="getReturnColor(stats.todayPL)">
          {{ stats.todayPL != null ? ((stats.todayPL > 0 ? '+' : '') + formatMoney(stats.todayPL)) : '' }}
        </p>
        <p class="text-xs text-textMute mt-1">当日实时更新</p>
      </div>
      <div class="bg-card p-4 rounded-lg shadow-sm border border-border">
        <p class="text-xs text-textMute mb-1">策略库</p>
        <p class="text-2xl font-bold font-numeric text-primary">{{ stats.strategyCount }}</p>
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
                  @click="handleListPause(sim.id)"
                >
                  暂停
                </button>
                <button 
                  v-if="sim.status === 'paused'"
                  class="text-green-600 hover:text-green-700 text-xs font-semibold"
                  @click="handleListResume(sim.id)"
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
                    <span>历史收益: <span :class="(strategy.returns || '').startsWith('+') ? 'text-up' : 'text-down'" class="font-semibold">{{ strategy.returns }}</span></span>
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
                  selectedStrategyId && !creating
                    ? 'bg-primary text-white hover:opacity-90' 
                    : 'bg-gray-200 text-textMute cursor-not-allowed'
                ]"
                :disabled="!selectedStrategyId || creating"
                @click="handleCreateSimulation"
              >
                {{ creating ? '创建中...' : '创建模拟' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
