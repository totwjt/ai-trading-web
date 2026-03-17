<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import Icon from '@/components/common/Icon.vue'

const router = useRouter()

// 模拟策略数据
const strategies = ref([
  {
    id: 1,
    name: '趋势先行A (大盘股)',
    type: 'MA交叉策略',
    status: '运行中',
    holdings: ['贵州茅台', '招商银行'],
    returns: '+12.4%',
    winRate: '68.2%',
    tradeCount: 142,
    riskLevel: '中风险'
  },
  {
    id: 2,
    name: '均线回归Alpha',
    type: '量化多因子',
    status: '暂停',
    holdings: ['宁德时代', '比亚迪'],
    returns: '-2.1%',
    winRate: '52.3%',
    tradeCount: 89,
    riskLevel: '高风险'
  },
  {
    id: 3,
    name: '高频套利V2',
    type: '高频交易',
    status: '运行中',
    holdings: ['中信证券', '华泰证券'],
    returns: '+4.8%',
    winRate: '81.0%',
    tradeCount: 567,
    riskLevel: '低风险'
  }
])

// 跳转到编辑策略页面
const editStrategy = (id: number) => {
  router.push(`/backtest/edit/${id}`)
}

// 跳转到回测详情页面
const viewDetail = (id: number) => {
  router.push(`/backtest/detail/${id}`)
}
</script>

<template>
  <div class="min-h-screen bg-white p-8 space-y-10">
    <!-- 策略监控台 -->
    <div class="space-y-4">
      <div class="flex justify-between items-center">
        <h3 class="font-bold text-lg tracking-tight">策略监控台</h3>
        <div class="flex items-center gap-4 text-xs text-slate-500 font-medium">
          <div class="flex items-center gap-1.5">
            <span class="size-2 rounded-full bg-green-600"></span> 运行中: 2
          </div>
          <div class="flex items-center gap-1.5">
            <span class="size-2 rounded-full bg-slate-300"></span> 暂停: 1
          </div>
        </div>
      </div>

      <!-- 策略列表表格 -->
      <div class="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-slate-50 text-slate-500 text-[11px] uppercase tracking-wider">
                <th class="px-6 py-4 font-semibold">策略名称</th>
                <th class="px-6 py-4 font-semibold">状态</th>
                <th class="px-6 py-4 font-semibold">持仓标的</th>
                <th class="px-6 py-4 font-semibold text-right">当前收益率</th>
                <th class="px-6 py-4 font-semibold text-right">胜率</th>
                <th class="px-6 py-4 font-semibold text-right">交易次数</th>
                <th class="px-6 py-4 font-semibold text-center">风险等级</th>
                <th class="px-6 py-4 font-semibold text-right">操作</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr 
                v-for="strategy in strategies"
                :key="strategy.id"
                class="hover:bg-slate-50 transition-colors"
              >
                <td class="px-6 py-4">
                  <div class="flex flex-col">
                    <span class="text-sm font-bold">{{ strategy.name }}</span>
                    <span class="text-[10px] text-slate-400">{{ strategy.type }}</span>
                  </div>
                </td>
                <td class="px-6 py-4">
                  <span 
                    :class="[
                      'inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold',
                      strategy.status === '运行中' 
                        ? 'bg-green-100 text-green-700' 
                        : 'bg-slate-100 text-slate-600'
                    ]"
                  >
                    {{ strategy.status }}
                  </span>
                </td>
                <td class="px-6 py-4">
                  <div class="flex flex-wrap gap-1">
                    <span 
                      v-for="holding in strategy.holdings"
                      :key="holding"
                      class="text-[11px] px-1.5 py-0.5 bg-slate-100 rounded"
                    >
                      {{ holding }}
                    </span>
                  </div>
                </td>
                <td class="px-6 py-4 text-right font-bold" :class="strategy.returns.startsWith('+') ? 'text-red-600' : 'text-green-600'">
                  {{ strategy.returns }}
                </td>
                <td class="px-6 py-4 text-right text-sm">{{ strategy.winRate }}</td>
                <td class="px-6 py-4 text-right text-sm font-medium">{{ strategy.tradeCount }}</td>
                <td class="px-6 py-4 text-center">
                  <span class="text-[11px] font-semibold text-orange-500">{{ strategy.riskLevel }}</span>
                </td>
                <td class="px-6 py-4 text-right space-x-3">
                  <button 
                    class="text-primary hover:underline text-xs font-semibold"
                    @click="viewDetail(strategy.id)"
                  >
                    详情
                  </button>
                  <button 
                    class="text-slate-500 hover:text-slate-900 text-xs font-semibold"
                    @click="editStrategy(strategy.id)"
                  >
                    编辑
                  </button>
                  <button class="text-red-500 hover:text-red-700 text-xs font-semibold">
                    停止
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 快速操作 -->
    <div class="flex justify-between items-center">
      <div class="text-xs text-slate-500">
        共 {{ strategies.length }} 个策略
      </div>
      <button 
        class="bg-primary text-white px-4 py-2 rounded text-sm font-semibold hover:bg-blue-700 flex items-center gap-2"
        @click="editStrategy(0)"
      >
        <Icon icon="mdi:plus" :size="16" />
        新建策略
      </button>
    </div>
  </div>
</template>