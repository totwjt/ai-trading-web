<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Icon from '@/components/common/Icon.vue'

const route = useRoute()
const router = useRouter()

// 模拟详情数据
const simulation = ref({
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
  lastTradeTime: '10:32:15',
  availableCapital: 300300,
  frozenCapital: 0
})

// 持仓股票列表
const holdings = ref([
  {
    id: 1,
    name: '贵州茅台',
    code: '600519.SH',
    quantity: 100,
    avgCost: 1850.00,
    currentPrice: 1880.50,
    marketValue: 188050.00,
    pl: 3050.00,
    plPercent: 1.65,
    weight: 22.8
  },
  {
    id: 2,
    name: '宁德时代',
    code: '300750.SZ',
    quantity: 500,
    avgCost: 220.00,
    currentPrice: 215.50,
    marketValue: 107750.00,
    pl: -2250.00,
    plPercent: -2.05,
    weight: 13.1
  },
  {
    id: 3,
    name: '招商银行',
    code: '600036.SH',
    quantity: 2000,
    avgCost: 35.50,
    currentPrice: 36.80,
    marketValue: 73600.00,
    pl: 2600.00,
    plPercent: 3.66,
    weight: 8.9
  },
  {
    id: 4,
    name: '中国平安',
    code: '601318.SH',
    quantity: 1000,
    avgCost: 42.50,
    currentPrice: 41.20,
    marketValue: 41200.00,
    pl: -1300.00,
    plPercent: -3.06,
    weight: 5.0
  },
  {
    id: 5,
    name: '五粮液',
    code: '000858.SZ',
    quantity: 200,
    avgCost: 145.00,
    currentPrice: 148.50,
    marketValue: 29700.00,
    pl: 700.00,
    plPercent: 2.41,
    weight: 3.6
  }
])

// 交易记录列表
const trades = ref([
  {
    id: 1,
    time: '10:32:15',
    stockName: '中国平安',
    stockCode: '601318.SH',
    direction: 'buy',
    directionText: '买入',
    price: 41.20,
    quantity: 1000,
    amount: 41200.00,
    status: '已成交'
  },
  {
    id: 2,
    time: '09:45:22',
    stockName: '五粮液',
    stockCode: '000858.SZ',
    direction: 'sell',
    directionText: '卖出',
    price: 148.50,
    quantity: 100,
    amount: 14850.00,
    status: '已成交'
  },
  {
    id: 3,
    time: '09:30:15',
    stockName: '贵州茅台',
    stockCode: '600519.SH',
    direction: 'buy',
    directionText: '买入',
    price: 1875.00,
    quantity: 100,
    amount: 187500.00,
    status: '已成交'
  },
  {
    id: 4,
    time: '10:15:30',
    stockName: '招商银行',
    stockCode: '600036.SH',
    direction: 'buy',
    directionText: '买入',
    price: 36.50,
    quantity: 500,
    amount: 18250.00,
    status: '已成交'
  },
  {
    id: 5,
    time: '14:28:00',
    stockName: '宁德时代',
    stockCode: '300750.SZ',
    direction: 'sell',
    directionText: '卖出',
    price: 218.00,
    quantity: 200,
    amount: 43600.00,
    status: '已成交'
  }
])

// 格式化金额
const formatMoney = (value: number) => {
  return value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

// 收益率颜色
const getReturnColor = (value: number) => {
  return value > 0 ? 'text-up' : value < 0 ? 'text-down' : 'text-textSub'
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

// 返回列表
const goBack = () => {
  router.push('/simulation')
}

// 控制操作
const pauseSimulation = () => {
  simulation.value.status = 'paused'
  simulation.value.statusText = '已暂停'
}

const resumeSimulation = () => {
  simulation.value.status = 'running'
  simulation.value.statusText = '运行中'
}

onMounted(() => {
  const id = route.params.id
  console.log('Simulation Detail ID:', id)
})
</script>

<template>
  <div class="h-full flex flex-col bg-bgMain overflow-hidden">
    <!-- 页面标题栏 -->
    <div class="px-6 py-3 border-b border-border bg-card shrink-0">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-4">
          <button 
            class="flex items-center gap-1 text-textSub hover:text-primary transition-colors"
            @click="goBack"
          >
            <Icon icon="mdi:arrow-left" :size="18" />
            <span class="text-sm">返回</span>
          </button>
          <div class="h-6 w-px bg-border"></div>
          <div>
            <div class="flex items-center gap-2">
              <h1 class="text-lg font-bold text-textMain">{{ simulation.name }}</h1>
              <span 
                :class="[
                  'inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold',
                  getStatusColor(simulation.status)
                ]"
              >
                {{ simulation.statusText }}
              </span>
            </div>
            <p class="text-xs text-textMute mt-0.5">策略: {{ simulation.strategyName }}</p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button 
            v-if="simulation.status === 'running'"
            class="px-3 py-1.5 border border-yellow-500 text-yellow-600 rounded text-xs font-semibold hover:bg-yellow-50 transition-colors"
            @click="pauseSimulation"
          >
            暂停模拟
          </button>
          <button 
            v-if="simulation.status === 'paused'"
            class="px-3 py-1.5 bg-green-500 text-white rounded text-xs font-semibold hover:bg-green-600 transition-colors"
            @click="resumeSimulation"
          >
            恢复模拟
          </button>
          <button class="px-3 py-1.5 bg-red-500 text-white rounded text-xs font-semibold hover:bg-red-600 transition-colors">
            结束模拟
          </button>
        </div>
      </div>
    </div>

    <!-- 页面内容 (可滚动) -->
    <div class="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-4">
      <!-- 上：持仓股票列表 (固定高度，可滚动) -->
      <div class="bg-card rounded-xl border border-border shadow-sm overflow-hidden flex flex-col" style="max-height: 280px;">
        <div class="px-6 py-3 border-b border-border flex items-center justify-between shrink-0">
          <div class="flex items-center gap-3">
            <h2 class="font-bold text-sm text-textMain">持仓股票</h2>
            <span class="text-xs text-textMute">共 {{ holdings.length }} 只</span>
          </div>
          <div class="flex items-center gap-4 text-xs text-textMute">
            <span>持仓市值: <span class="font-numeric font-semibold text-textMain">{{ formatMoney(simulation.holdingsValue) }}</span></span>
          </div>
        </div>
        <div class="overflow-y-auto flex-1">
          <table class="w-full">
          <thead>
            <tr class="bg-gray-50/50 dark:bg-gray-800/50 text-textMute text-[11px] uppercase tracking-wider">
              <th class="px-6 py-3 font-semibold text-left">股票名称</th>
              <th class="px-6 py-3 font-semibold text-left">代码</th>
              <th class="px-6 py-3 font-semibold text-right">持仓数量</th>
              <th class="px-6 py-3 font-semibold text-right">成本价</th>
              <th class="px-6 py-3 font-semibold text-right">现价</th>
              <th class="px-6 py-3 font-semibold text-right">市值</th>
              <th class="px-6 py-3 font-semibold text-right">持仓盈亏</th>
              <th class="px-6 py-3 font-semibold text-right">盈亏率</th>
              <th class="px-6 py-3 font-semibold text-right">权重</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-border">
            <tr 
              v-for="holding in holdings"
              :key="holding.id"
              class="hover:bg-primary/5 transition-colors"
            >
              <td class="px-6 py-3.5">
                <span class="font-bold text-sm text-textMain">{{ holding.name }}</span>
              </td>
              <td class="px-6 py-3.5">
                <span class="font-numeric text-xs text-textMute">{{ holding.code }}</span>
              </td>
              <td class="px-6 py-3.5 text-right font-numeric text-sm text-textSub">
                {{ holding.quantity }}
              </td>
              <td class="px-6 py-3.5 text-right font-numeric text-sm text-textSub">
                {{ holding.avgCost.toFixed(2) }}
              </td>
              <td class="px-6 py-3.5 text-right font-numeric text-sm font-medium text-textMain">
                {{ holding.currentPrice.toFixed(2) }}
              </td>
              <td class="px-6 py-3.5 text-right font-numeric text-sm font-medium text-textMain">
                {{ formatMoney(holding.marketValue) }}
              </td>
              <td class="px-6 py-3.5 text-right">
                <span class="font-numeric text-sm font-bold" :class="getReturnColor(holding.pl)">
                  {{ holding.pl > 0 ? '+' : '' }}{{ formatMoney(holding.pl) }}
                </span>
              </td>
              <td class="px-6 py-3.5 text-right">
                <span class="font-numeric text-sm font-bold" :class="getReturnColor(holding.plPercent)">
                  {{ holding.plPercent > 0 ? '+' : '' }}{{ holding.plPercent.toFixed(2) }}%
                </span>
              </td>
              <td class="px-6 py-3.5 text-right">
                <span class="font-numeric text-sm text-textSub">{{ holding.weight.toFixed(1) }}%</span>
              </td>
            </tr>
          </tbody>
        </table>
        </div>
        
        <!-- 空状态 -->
        <div v-if="holdings.length === 0" class="py-12 text-center">
          <Icon icon="mdi:package-variant" :size="48" class="mx-auto text-textMute mb-3" />
          <p class="text-textSub text-sm">暂无持仓</p>
        </div>
      </div>

      <!-- 下：账户信息 + 交易记录 -->
      <div class="grid grid-cols-12 gap-6">
        <!-- 左侧：账户信息 -->
        <div class="col-span-4">
          <div class="bg-card rounded-xl border border-border shadow-sm overflow-hidden">
            <div class="px-6 py-4 border-b border-border">
              <h2 class="font-bold text-sm text-textMain">账户信息</h2>
            </div>
            <div class="p-6 space-y-4">
              <!-- 总资产 -->
              <div class="p-4 bg-primary/5 rounded-lg">
                <p class="text-xs text-textMute mb-1">总资产 (CNY)</p>
                <p class="text-2xl font-bold font-numeric text-textMain">
                  {{ formatMoney(simulation.currentCapital) }}
                </p>
                <div class="flex items-center gap-2 mt-1">
                  <span class="text-xs font-semibold" :class="getReturnColor(simulation.totalReturn)">
                    {{ simulation.totalReturn > 0 ? '+' : '' }}{{ simulation.totalReturn.toFixed(2) }}%
                  </span>
                  <span class="text-xs text-textMute">累计收益</span>
                </div>
              </div>

              <!-- 账户明细 -->
              <div class="space-y-3">
                <div class="flex justify-between items-center">
                  <span class="text-xs text-textMute">初始资金</span>
                  <span class="font-numeric text-sm font-medium text-textSub">
                    {{ formatMoney(simulation.initialCapital) }}
                  </span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-xs text-textMute">可用资金</span>
                  <span class="font-numeric text-sm font-medium text-textMain">
                    {{ formatMoney(simulation.availableCapital) }}
                  </span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-xs text-textMute">持仓市值</span>
                  <span class="font-numeric text-sm font-medium text-textMain">
                    {{ formatMoney(simulation.holdingsValue) }}
                  </span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-xs text-textMute">冻结资金</span>
                  <span class="font-numeric text-sm font-medium text-textSub">
                    {{ formatMoney(simulation.frozenCapital) }}
                  </span>
                </div>
              </div>

              <div class="border-t border-border pt-4 space-y-3">
                <div class="flex justify-between items-center">
                  <span class="text-xs text-textMute">今日盈亏</span>
                  <span class="font-numeric text-sm font-bold" :class="getReturnColor(simulation.todayPL)">
                    {{ simulation.todayPL > 0 ? '+' : '' }}{{ formatMoney(simulation.todayPL) }}
                  </span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-xs text-textMute">今日收益率</span>
                  <span class="font-numeric text-sm font-bold" :class="getReturnColor(simulation.todayReturn)">
                    {{ simulation.todayReturn > 0 ? '+' : '' }}{{ simulation.todayReturn.toFixed(2) }}%
                  </span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-xs text-textMute">胜率</span>
                  <span class="font-numeric text-sm font-medium text-textMain">
                    {{ simulation.winRate.toFixed(1) }}%
                  </span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-xs text-textMute">交易次数</span>
                  <span class="font-numeric text-sm font-medium text-textSub">
                    {{ simulation.tradeCount }}
                  </span>
                </div>
              </div>

              <div class="border-t border-border pt-4">
                <div class="flex justify-between items-center">
                  <span class="text-xs text-textMute">开始日期</span>
                  <span class="text-sm text-textSub">
                    {{ simulation.startDate }}
                  </span>
                </div>
                <div class="flex justify-between items-center mt-2">
                  <span class="text-xs text-textMute">最后交易</span>
                  <span class="text-sm text-textSub">
                    {{ simulation.lastTradeTime }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧：交易记录 (固定高度，可滚动) -->
        <div class="col-span-8">
          <div class="bg-card rounded-xl border border-border shadow-sm overflow-hidden flex flex-col" style="max-height: 400px;">
            <div class="px-6 py-3 border-b border-border flex items-center justify-between shrink-0">
              <div class="flex items-center gap-3">
                <h2 class="font-bold text-sm text-textMain">交易记录</h2>
                <span class="text-xs text-textMute">最近 {{ trades.length }} 笔</span>
              </div>
              <button class="text-xs text-primary hover:underline font-semibold">查看全部</button>
            </div>
            <div class="overflow-y-auto flex-1">
              <table class="w-full">
              <thead>
                <tr class="bg-gray-50/50 dark:bg-gray-800/50 text-textMute text-[11px] uppercase tracking-wider">
                  <th class="px-6 py-3 font-semibold text-left">时间</th>
                  <th class="px-6 py-3 font-semibold text-left">股票</th>
                  <th class="px-6 py-3 font-semibold text-center">方向</th>
                  <th class="px-6 py-3 font-semibold text-right">价格</th>
                  <th class="px-6 py-3 font-semibold text-right">数量</th>
                  <th class="px-6 py-3 font-semibold text-right">金额</th>
                  <th class="px-6 py-3 font-semibold text-center">状态</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-border">
                <tr 
                  v-for="trade in trades"
                  :key="trade.id"
                  class="hover:bg-primary/5 transition-colors"
                >
                  <td class="px-6 py-3.5">
                    <span class="font-numeric text-xs text-textMute">{{ trade.time }}</span>
                  </td>
                  <td class="px-6 py-3.5">
                    <div class="flex flex-col">
                      <span class="font-bold text-sm text-textMain">{{ trade.stockName }}</span>
                      <span class="font-numeric text-[10px] text-textMute">{{ trade.stockCode }}</span>
                    </div>
                  </td>
                  <td class="px-6 py-3.5 text-center">
                    <span 
                      :class="[
                        'inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold',
                        trade.direction === 'buy' 
                          ? 'bg-up/10 text-up' 
                          : 'bg-down/10 text-down'
                      ]"
                    >
                      {{ trade.directionText }}
                    </span>
                  </td>
                  <td class="px-6 py-3.5 text-right font-numeric text-sm text-textSub">
                    {{ trade.price.toFixed(2) }}
                  </td>
                  <td class="px-6 py-3.5 text-right font-numeric text-sm text-textSub">
                    {{ trade.quantity }}
                  </td>
                  <td class="px-6 py-3.5 text-right font-numeric text-sm font-medium text-textMain">
                    {{ formatMoney(trade.amount) }}
                  </td>
                  <td class="px-6 py-3.5 text-center">
                    <span class="text-[10px] font-semibold text-green-600">{{ trade.status }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
            </div>

            <!-- 空状态 -->
            <div v-if="trades.length === 0" class="py-12 text-center">
              <Icon icon="mdi:format-list-bulleted" :size="48" class="mx-auto text-textMute mb-3" />
              <p class="text-textSub text-sm">暂无交易记录</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
