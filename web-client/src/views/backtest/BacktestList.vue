<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { getBacktestList, type BacktestListItem } from '@/api/backtest'
import Icon from '@/components/common/Icon.vue'

const router = useRouter()

const backtests = ref<BacktestListItem[]>([])
const loading = ref(false)
const pagination = ref({
  page: 1,
  pageSize: 10,
  total: 0
})

const statusMap: Record<string, { color: string; bgColor: string }> = {
  pending: { color: 'text-yellow-600', bgColor: 'bg-yellow-100' },
  running: { color: 'text-blue-600', bgColor: 'bg-blue-100' },
  completed: { color: 'text-green-600', bgColor: 'bg-green-100' },
  failed: { color: 'text-red-600', bgColor: 'bg-red-100' },
  cancelled: { color: 'text-gray-600', bgColor: 'bg-gray-100' }
}

const statusText: Record<string, string> = {
  pending: '等待中',
  running: '运行中',
  completed: '已完成',
  failed: '失败',
  cancelled: '已取消'
}

async function fetchData() {
  loading.value = true
  try {
    const result = await getBacktestList({
      page: pagination.value.page,
      page_size: pagination.value.pageSize
    })
    backtests.value = result.items
    pagination.value.total = result.total
  } catch (error) {
    console.error('获取回测列表失败:', error)
  } finally {
    loading.value = false
  }
}

function viewDetail(id: number) {
  router.push(`/backtest/detail/${id}`)
}

function editStrategy(strategyId: number) {
  router.push(`/backtest/edit/${strategyId}`)
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

function formatReturn(value: number | undefined): string {
  if (value === undefined || value === null) return '-'
  return (value >= 0 ? '+' : '') + value.toFixed(2) + '%'
}

function getReturnClass(value: number | undefined): string {
  if (value === undefined || value === null) return 'text-textSub'
  return value >= 0 ? 'text-up' : 'text-down'
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="min-h-screen bg-bgMain p-8">
    <div class="max-w-7xl mx-auto">
      <div class="flex justify-between items-center mb-6">
        <div>
          <h2 class="text-lg font-bold text-textMain">回测记录</h2>
          <p class="text-xs text-textMute mt-1">查看所有回测历史记录</p>
        </div>
        <button
          class="bg-primary text-white px-4 py-2 rounded text-sm font-semibold hover:opacity-90 flex items-center gap-2"
          @click="router.push('/backtest/edit')"
        >
          <Icon icon="mdi:plus" :size="16" />
          新建策略
        </button>
      </div>

      <div class="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
        <div v-if="loading" class="p-8 text-center text-textMute">
          加载中...
        </div>
        
        <div v-else-if="backtests.length === 0" class="p-8 text-center text-textMute">
          暂无回测记录
        </div>

        <table v-else class="w-full text-left">
          <thead>
            <tr class="bg-gray-50 dark:bg-gray-800 text-textMute text-[11px] uppercase tracking-wider">
              <th class="px-6 py-4 font-semibold text-textMain">策略名称</th>
              <th class="px-6 py-4 font-semibold text-textMain">状态</th>
              <th class="px-6 py-4 font-semibold text-textMain">回测区间</th>
              <th class="px-6 py-4 font-semibold text-right text-textMain">总收益率</th>
              <th class="px-6 py-4 font-semibold text-right text-textMain">夏普比率</th>
              <th class="px-6 py-4 font-semibold text-right text-textMain">进度</th>
              <th class="px-6 py-4 font-semibold text-textMain">创建时间</th>
              <th class="px-6 py-4 font-semibold text-right text-textMain">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-border">
            <tr
              v-for="bt in backtests"
              :key="bt.id"
              class="hover:bg-primary/5 transition-colors"
            >
              <td class="px-6 py-4">
                <span class="text-sm font-medium text-textMain">{{ bt.strategy_name || '未命名策略' }}</span>
              </td>
              <td class="px-6 py-4">
                <span
                  :class="[
                    'inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold',
                    statusMap[bt.status]?.bgColor || 'bg-gray-100',
                    statusMap[bt.status]?.color || 'text-gray-600'
                  ]"
                >
                  {{ statusText[bt.status] || bt.status }}
                </span>
              </td>
              <td class="px-6 py-4">
                <span class="text-sm text-textSub">
                  {{ bt.start_date }} ~ {{ bt.end_date }}
                </span>
              </td>
              <td class="px-6 py-4 text-right font-bold" :class="getReturnClass(bt.total_return)">
                {{ formatReturn(bt.total_return) }}
              </td>
              <td class="px-6 py-4 text-right text-sm text-textSub">
                {{ bt.sharpe_ratio?.toFixed(2) || '-' }}
              </td>
              <td class="px-6 py-4">
                <div class="flex items-center gap-2">
                  <div class="w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      class="h-full bg-primary rounded-full transition-all"
                      :style="{ width: `${bt.progress}%` }"
                    ></div>
                  </div>
                  <span class="text-xs text-textMute">{{ bt.progress }}%</span>
                </div>
              </td>
              <td class="px-6 py-4 text-sm text-textSub">
                {{ formatDate(bt.created_at) }}
              </td>
              <td class="px-6 py-4 text-right space-x-3">
                <button
                  class="text-primary hover:underline text-xs font-semibold"
                  @click="viewDetail(bt.id)"
                >
                  详情
                </button>
                <button
                  class="text-textMute hover:text-textMain text-xs font-semibold"
                  @click="editStrategy(bt.strategy_id)"
                >
                  编辑
                </button>
              </td>
            </tr>
          </tbody>
        </table>

        <div v-if="pagination.total > 0" class="px-6 py-4 border-t border-border flex justify-between items-center">
          <span class="text-xs text-textMute">
            共 {{ pagination.total }} 条记录
          </span>
          <div class="flex gap-2">
            <button
              class="px-3 py-1 text-xs border border-border rounded hover:bg-gray-50 disabled:opacity-50"
              :disabled="pagination.page <= 1"
              @click="pagination.page--; fetchData()"
            >
              上一页
            </button>
            <span class="px-3 py-1 text-xs text-textSub">
              第 {{ pagination.page }} / {{ Math.ceil(pagination.total / pagination.pageSize) }} 页
            </span>
            <button
              class="px-3 py-1 text-xs border border-border rounded hover:bg-gray-50 disabled:opacity-50"
              :disabled="pagination.page >= Math.ceil(pagination.total / pagination.pageSize)"
              @click="pagination.page++; fetchData()"
            >
              下一页
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
