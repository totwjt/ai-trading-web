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
  <div class="min-h-screen bg-bgMain p-8 space-y-10">
    <!-- 策略监控台 -->
    <div class="space-y-4">
      <div class="flex justify-between items-center">
        <h3 class="font-bold text-lg tracking-tight text-textMain">策略监控台</h3>
        <div class="flex items-center gap-4 text-xs text-textMute font-medium">
          <div class="flex items-center gap-1.5">
            <span class="size-2 rounded-full bg-green-600"></span> 运行中: 2
          </div>
          <div class="flex items-center gap-1.5">
            <span class="size-2 rounded-full bg-gray-300"></span> 暂停: 1
          </div>
        </div>
      </div>

      <!-- 策略列表表格 -->
      <div class="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-gray-50 dark:bg-gray-800 text-textMute text-[11px] uppercase tracking-wider">
                <th class="px-6 py-4 font-semibold text-textMain">策略名称</th>
                <th class="px-6 py-4 font-semibold text-textMain">状态</th>
                <th class="px-6 py-4 font-semibold text-textMain">持仓标的</th>
                <th class="px-6 py-4 font-semibold text-right text-textMain">当前收益率</th>
                <th class="px-6 py-4 font-semibold text-right text-textMain">胜率</th>
                <th class="px-6 py-4 font-semibold text-right text-textMain">交易次数</th>
                <th class="px-6 py-4 font-semibold text-center text-textMain">风险等级</th>
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
                  <div class="flex flex-col">
                    <span class="text-sm font-bold text-textMain">{{ strategy.name }}</span>
                    <span class="text-[10px] text-textMute">{{ strategy.type }}</span>
                  </div>
                </td>
                <td class="px-6 py-4">
                  <span 
                    :class="[
                      'inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold',
                      strategy.status === '运行中' 
                        ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' 
                        : 'bg-gray-100 dark:bg-gray-800 text-textSub'
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
                      class="text-[11px] px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-textSub"
                    >
                      {{ holding }}
                    </span>
                  </div>
                </td>
                <td class="px-6 py-4 text-right font-bold" :class="strategy.returns.startsWith('+') ? 'text-up' : 'text-down'">
                  {{ strategy.returns }}
                </td>
                <td class="px-6 py-4 text-right text-sm text-textSub">{{ strategy.winRate }}</td>
                <td class="px-6 py-4 text-right text-sm font-medium text-textSub">{{ strategy.tradeCount }}</td>
                <td class="px-6 py-4 text-center">
                  <span class="text-[11px] font-semibold text-yellow-500">{{ strategy.riskLevel }}</span>
                </td>
                <td class="px-6 py-4 text-right space-x-3">
                  <button 
                    class="text-primary hover:underline text-xs font-semibold"
                    @click="viewDetail(strategy.id)"
                  >
                    详情
                  </button>
                  <button 
                    class="text-textMute hover:text-textMain text-xs font-semibold"
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
      <div class="text-xs text-textMute">
        共 {{ strategies.length }} 个策略
      </div>
      <button 
        class="bg-primary text-white px-4 py-2 rounded text-sm font-semibold hover:opacity-90 flex items-center gap-2"
        @click="editStrategy(0)"
      >
        <Icon icon="mdi:plus" :size="16" />
        新建策略
      </button>
    </div>

    <!-- 策略中心/市场 -->
    <div class="space-y-6 mt-10">
      <div class="flex justify-between items-end border-b border-border pb-4">
        <div>
          <h3 class="font-bold text-lg tracking-tight text-textMain">策略中心</h3>
          <p class="text-xs text-textMute mt-1">发现经过回测验证的高效量化模型</p>
        </div>
        <button class="text-xs text-primary font-semibold flex items-center gap-1">
          查看更多 <Icon icon="mdi:arrow-right" :size="16" />
        </button>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <!-- 策略卡片 1 -->
        <div class="bg-card border border-border rounded-xl p-6 shadow-sm flex flex-col hover:border-primary/30 transition-all group">
          <div class="flex justify-between items-start mb-4">
            <div class="p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-primary">
              <Icon icon="mdi:chart-line" :size="24" />
            </div>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-gray-100 dark:bg-gray-800 text-textSub">股票</span>
          </div>
          <h4 class="font-bold text-sm mb-2 text-textMain group-hover:text-primary transition-colors">风格轮动</h4>
          <p class="text-xs text-textMute leading-relaxed mb-4 flex-1">
            基于价值、成长，质量等多因子，自动捕捉当前市场强势风格并进行行业均衡配置。
          </p>
          <div class="pt-4 border-t border-border flex flex-col gap-3">
            <div class="flex justify-between items-center">
              <span class="text-[10px] text-textMute uppercase font-semibold">历史年化收益</span>
              <span class="text-sm font-bold text-up">24.8%</span>
            </div>
            <div class="grid grid-cols-2 gap-2">
              <button class="text-[11px] py-1.5 border border-border rounded-lg font-semibold hover:bg-primary/5 text-textMain">查看详情</button>
              <button class="text-[11px] py-1.5 bg-primary text-white rounded-lg font-semibold hover:opacity-90 transition-opacity">引用策略</button>
            </div>
          </div>
        </div>

        <!-- 策略卡片 2 -->
        <div class="bg-card border border-border rounded-xl p-6 shadow-sm flex flex-col hover:border-primary/30 transition-all group">
          <div class="flex justify-between items-start mb-4">
            <div class="p-2 bg-orange-50 dark:bg-orange-900/20 rounded-lg text-orange-500">
              <Icon icon="mdi:history" :size="24" />
            </div>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-gray-100 dark:bg-gray-800 text-textSub">股票</span>
          </div>
          <h4 class="font-bold text-sm mb-2 text-textMain group-hover:text-primary transition-colors">日内回转交易 (T+0)</h4>
          <p class="text-xs text-textMute leading-relaxed mb-4 flex-1">
            针对高波动性标的，通过高频价格监控实现日内低买高卖，不留底仓风险。
          </p>
          <div class="pt-4 border-t border-border flex flex-col gap-3">
            <div class="flex justify-between items-center">
              <span class="text-[10px] text-textMute uppercase font-semibold">历史胜率</span>
              <span class="text-sm font-bold text-textMain">62.1%</span>
            </div>
            <div class="grid grid-cols-2 gap-2">
              <button class="text-[11px] py-1.5 border border-border rounded-lg font-semibold hover:bg-primary/5 text-textMain">查看详情</button>
              <button class="text-[11px] py-1.5 bg-primary text-white rounded-lg font-semibold hover:opacity-90 transition-opacity">引用策略</button>
            </div>
          </div>
        </div>

        <!-- 策略卡片 3 -->
        <div class="bg-card border border-border rounded-xl p-6 shadow-sm flex flex-col hover:border-primary/30 transition-all group">
          <div class="flex justify-between items-start mb-4">
            <div class="p-2 bg-green-50 dark:bg-green-900/20 rounded-lg text-green-600">
              <Icon icon="mdi:chart-bar" :size="24" />
            </div>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-gray-100 dark:bg-gray-800 text-textSub">股票</span>
          </div>
          <h4 class="font-bold text-sm mb-2 text-textMain group-hover:text-primary transition-colors">小市值因子策略</h4>
          <p class="text-xs text-textMute leading-relaxed mb-4 flex-1">
            筛选低估值、高成长潜力的小市值标的，利用市场非对称信息获取长期超额回报。
          </p>
          <div class="pt-4 border-t border-border flex flex-col gap-3">
            <div class="flex justify-between items-center">
              <span class="text-[10px] text-textMute uppercase font-semibold">Sharpe比率</span>
              <span class="text-sm font-bold text-textMain">2.1</span>
            </div>
            <div class="grid grid-cols-2 gap-2">
              <button class="text-[11px] py-1.5 border border-border rounded-lg font-semibold hover:bg-primary/5 text-textMain">查看详情</button>
              <button class="text-[11px] py-1.5 bg-primary text-white rounded-lg font-semibold hover:opacity-90 transition-opacity">引用策略</button>
            </div>
          </div>
        </div>

        <!-- 策略卡片 4 -->
        <div class="bg-card border border-border rounded-xl p-6 shadow-sm flex flex-col hover:border-primary/30 transition-all group">
          <div class="flex justify-between items-start mb-4">
            <div class="p-2 bg-purple-50 dark:bg-purple-900/20 rounded-lg text-purple-500">
              <Icon icon="mdi:finance" :size="24" />
            </div>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-gray-100 dark:bg-gray-800 text-textSub">ETF</span>
          </div>
          <h4 class="font-bold text-sm mb-2 text-textMain group-hover:text-primary transition-colors">行业轮动ETF</h4>
          <p class="text-xs text-textMute leading-relaxed mb-4 flex-1">
            基于行业景气度轮动，配置不同行业ETF，实现行业alpha收益。
          </p>
          <div class="pt-4 border-t border-border flex flex-col gap-3">
            <div class="flex justify-between items-center">
              <span class="text-[10px] text-textMute uppercase font-semibold">最大回撤</span>
              <span class="text-sm font-bold text-textMain">8.5%</span>
            </div>
            <div class="grid grid-cols-2 gap-2">
              <button class="text-[11px] py-1.5 border border-border rounded-lg font-semibold hover:bg-primary/5 text-textMain">查看详情</button>
              <button class="text-[11px] py-1.5 bg-primary text-white rounded-lg font-semibold hover:opacity-90 transition-opacity">引用策略</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>