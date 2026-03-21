<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { deleteStrategy, getStrategyList, type StrategyListItem } from '@/api/strategy'
import Icon from '@/components/common/Icon.vue'

const router = useRouter()

const strategies = ref<StrategyListItem[]>([])
const loading = ref(false)
const deletingStrategyId = ref<number | null>(null)

const statusMap: Record<string, { color: string; bgColor: string }> = {
  running: { color: 'text-green-700', bgColor: 'bg-green-100' },
  paused: { color: 'text-slate-600', bgColor: 'bg-slate-100' },
  stopped: { color: 'text-red-600', bgColor: 'bg-red-100' },
  error: { color: 'text-red-700', bgColor: 'bg-red-100' }
}

const statusText: Record<string, string> = {
  running: '运行中',
  paused: '已暂停',
  stopped: '已停止',
  error: '错误'
}

async function fetchStrategies() {
  loading.value = true
  try {
    const result = await getStrategyList({ page_size: 100 })
    strategies.value = result.items
  } catch (error) {
    console.error('获取策略列表失败:', error)
  } finally {
    loading.value = false
  }
}

function viewBacktestRecords() {
  router.push('/backtest/records')
}

function editStrategy(id: number) {
  router.push(`/backtest/edit/${id}`)
}

function viewStrategyBacktests(strategy: StrategyListItem) {
  router.push({
    path: '/backtest/records',
    query: {
      strategyId: String(strategy.id),
      strategyName: strategy.name
    }
  })
}

function createNewStrategy() {
  router.push('/backtest/edit')
}

async function removeStrategy(strategy: StrategyListItem) {
  const confirmed = window.confirm(`确认删除策略“${strategy.name}”？该策略关联的历史回测记录也会一起删除。`)
  if (!confirmed) return

  deletingStrategyId.value = strategy.id
  try {
    await deleteStrategy(strategy.id)
    strategies.value = strategies.value.filter(item => item.id !== strategy.id)
  } catch (error) {
    console.error('删除策略失败:', error)
    window.alert(error instanceof Error ? error.message : '删除策略失败，请稍后重试')
  } finally {
    deletingStrategyId.value = null
  }
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

onMounted(() => {
  fetchStrategies()
})
</script>

<template>
  <div class="min-h-screen bg-bgMain p-8 space-y-10">
    <div class="space-y-4">
      <div class="flex justify-between items-center">
        <h3 class="font-bold text-lg tracking-tight text-textMain">策略监控台</h3>
        <div class="flex items-center gap-4 text-xs text-textMute font-medium">
          <div class="flex items-center gap-1.5">
            <span class="size-2 rounded-full bg-green-600"></span>
            运行中: {{ strategies.filter(s => s.status === 'running').length }}
          </div>
          <div class="flex items-center gap-1.5">
            <span class="size-2 rounded-full bg-gray-300"></span>
            暂停: {{ strategies.filter(s => s.status === 'paused').length }}
          </div>
        </div>
      </div>

      <div class="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
        <div v-if="loading" class="p-8 text-center text-textMute">
          加载中...
        </div>

        <div v-else-if="strategies.length === 0" class="p-8 text-center text-textMute">
          暂无策略，点击"新建策略"开始
        </div>

        <table v-else class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-gray-50 dark:bg-gray-800 text-textMute text-[11px] uppercase tracking-wider">
              <th class="px-6 py-4 font-semibold text-textMain">策略名称</th>
              <th class="px-6 py-4 font-semibold text-textMain">状态</th>
              <th class="px-6 py-4 font-semibold text-right text-textMain">创建时间</th>
              <th class="px-6 py-4 font-semibold text-right text-textMain">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-border">
            <tr
              v-for="strategy in strategies"
              :key="strategy.id"
              class="hover:bg-primary/5 transition-colors"
            >
              <td class="px-6 py-4">
                <span class="text-sm font-bold text-textMain">{{ strategy.name }}</span>
              </td>
              <td class="px-6 py-4">
                <span
                  :class="[
                    'inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold',
                    statusMap[strategy.status]?.bgColor || 'bg-gray-100',
                    statusMap[strategy.status]?.color || 'text-gray-600'
                  ]"
                >
                  {{ statusText[strategy.status] || strategy.status }}
                </span>
              </td>
              <td class="px-6 py-4 text-right text-sm text-textSub">
                {{ formatDate(strategy.created_at) }}
              </td>
              <td class="px-6 py-4 text-right space-x-3">
                <button
                  class="text-textMute hover:text-textMain text-xs font-semibold"
                  @click="viewStrategyBacktests(strategy)"
                >
                  历史回测
                </button>
                <button
                  class="text-primary hover:underline text-xs font-semibold"
                  @click="editStrategy(strategy.id)"
                >
                  编辑
                </button>
                <button
                  class="text-down hover:underline text-xs font-semibold disabled:opacity-40 disabled:no-underline"
                  :disabled="deletingStrategyId === strategy.id"
                  @click="removeStrategy(strategy)"
                >
                  {{ deletingStrategyId === strategy.id ? '删除中...' : '删除' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="flex justify-between items-center">
      <div class="text-xs text-textMute">
        共 {{ strategies.length }} 个策略
      </div>
      <div class="flex gap-3">
        <button
          class="border border-border px-4 py-2 rounded text-sm font-medium hover:bg-gray-50 flex items-center gap-2"
          @click="viewBacktestRecords"
        >
          <Icon icon="mdi:history" :size="16" />
          全部回测记录
        </button>
        <button
          class="bg-primary text-white px-4 py-2 rounded text-sm font-semibold hover:opacity-90 flex items-center gap-2"
          @click="createNewStrategy"
        >
          <Icon icon="mdi:plus" :size="16" />
          新建策略
        </button>
      </div>
    </div>

    <div class="space-y-6 mt-10">
      <div class="flex justify-between items-end border-b border-border pb-4">
        <div>
          <h3 class="font-bold text-lg tracking-tight text-textMain">策略模板</h3>
          <p class="text-xs text-textMute mt-1">使用模板快速创建策略</p>
        </div>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div
          class="bg-card border border-border rounded-xl p-6 shadow-sm flex flex-col hover:border-primary/30 transition-all group cursor-pointer"
          @click="createNewStrategy"
        >
          <div class="flex justify-between items-start mb-4">
            <div class="p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-primary">
              <Icon icon="mdi:chart-line" :size="24" />
            </div>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-gray-100 dark:bg-gray-800 text-textSub">MA</span>
          </div>
          <h4 class="font-bold text-sm mb-2 text-textMain group-hover:text-primary transition-colors">均线交叉策略</h4>
          <p class="text-xs text-textMute leading-relaxed mb-4 flex-1">
            经典的移动平均线交叉策略，快线金叉慢线买入，死叉卖出。
          </p>
          <div class="pt-4 border-t border-border">
            <button class="w-full text-[11px] py-1.5 bg-primary text-white rounded-lg font-semibold hover:opacity-90 transition-opacity">
              使用模板
            </button>
          </div>
        </div>

        <div
          class="bg-card border border-border rounded-xl p-6 shadow-sm flex flex-col hover:border-primary/30 transition-all group cursor-pointer"
          @click="createNewStrategy"
        >
          <div class="flex justify-between items-start mb-4">
            <div class="p-2 bg-orange-50 dark:bg-orange-900/20 rounded-lg text-orange-500">
              <Icon icon="mdi:history" :size="24" />
            </div>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-gray-100 dark:bg-gray-800 text-textSub">RSI</span>
          </div>
          <h4 class="font-bold text-sm mb-2 text-textMain group-hover:text-primary transition-colors">RSI 超买超卖</h4>
          <p class="text-xs text-textMute leading-relaxed mb-4 flex-1">
            基于相对强弱指标的择时策略，RSI低于30超卖买入，高于70超买卖出。
          </p>
          <div class="pt-4 border-t border-border">
            <button class="w-full text-[11px] py-1.5 bg-primary text-white rounded-lg font-semibold hover:opacity-90 transition-opacity">
              使用模板
            </button>
          </div>
        </div>

        <div
          class="bg-card border border-border rounded-xl p-6 shadow-sm flex flex-col hover:border-primary/30 transition-all group cursor-pointer"
          @click="createNewStrategy"
        >
          <div class="flex justify-between items-start mb-4">
            <div class="p-2 bg-green-50 dark:bg-green-900/20 rounded-lg text-green-600">
              <Icon icon="mdi:chart-bar" :size="24" />
            </div>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-gray-100 dark:bg-gray-800 text-textSub">MACD</span>
          </div>
          <h4 class="font-bold text-sm mb-2 text-textMain group-hover:text-primary transition-colors">MACD 策略</h4>
          <p class="text-xs text-textMute leading-relaxed mb-4 flex-1">
            利用MACD指标的信号线交叉和柱状图变化进行交易决策。
          </p>
          <div class="pt-4 border-t border-border">
            <button class="w-full text-[11px] py-1.5 bg-primary text-white rounded-lg font-semibold hover:opacity-90 transition-opacity">
              使用模板
            </button>
          </div>
        </div>

        <div
          class="bg-card border border-border rounded-xl p-6 shadow-sm flex flex-col hover:border-primary/30 transition-all group cursor-pointer"
          @click="createNewStrategy"
        >
          <div class="flex justify-between items-start mb-4">
            <div class="p-2 bg-purple-50 dark:bg-purple-900/20 rounded-lg text-purple-500">
              <Icon icon="mdi:finance" :size="24" />
            </div>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-gray-100 dark:bg-gray-800 text-textSub">布林带</span>
          </div>
          <h4 class="font-bold text-sm mb-2 text-textMain group-hover:text-primary transition-colors">布林带策略</h4>
          <p class="text-xs text-textMute leading-relaxed mb-4 flex-1">
            价格触及下轨买入，触及上轨卖出，结合波动率进行风险管理。
          </p>
          <div class="pt-4 border-t border-border">
            <button class="w-full text-[11px] py-1.5 bg-primary text-white rounded-lg font-semibold hover:opacity-90 transition-opacity">
              使用模板
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
