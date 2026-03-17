<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Icon from '@/components/common/Icon.vue'

const route = useRoute()
const router = useRouter()

// 获取策略ID
const strategyId = route.params.id

// 模拟回测数据
const backtestData = ref({
  strategyName: 'DualMovingAverageCross_V2',
  timePeriod: '2021-01-01 至 2023-12-31',
  initialCapital: '1,000,000.00',
  finalEquity: '1,324,412.00',
  totalReturn: '+32.44%',
  benchmark: '跑赢基准'
})

// 模拟交易明细数据
const transactionLog = ref([
  { time: '2023-12-28 14:35', code: '600519.SH', type: 'SELL', price: '1,728.50', quantity: '-200', profit: '+12,227.15' },
  { time: '2023-12-27 10:15', code: '300750.SZ', type: 'BUY', price: '163.20', quantity: '+1,000', profit: '---' },
  { time: '2023-12-25 09:30', code: '002371.SZ', type: 'SELL', price: '245.80', quantity: '-500', profit: '-2,211.45' },
  { time: '2023-12-24 13:45', code: '600036.SH', type: 'BUY', price: '28.45', quantity: '+5,000', profit: '---' },
  { time: '2023-12-20 11:20', code: '601318.SH', type: 'SELL', price: '41.12', quantity: '-1,500', profit: '+1,450.20' }
])

// 模拟系统日志
const systemLog = ref([
  { time: '2023-12-31 23:59:59', level: 'INFO', message: 'Cerebro engine initialized.' },
  { time: '2023-12-31 23:59:59', level: 'INFO', message: 'Loading data feeds for 15 assets...' },
  { time: '2024-01-01 00:00:01', level: 'INFO', message: "Adding Strategy 'DualMovingAverageCross_V2' to Brain." },
  { time: '2024-01-01 00:00:02', level: 'INFO', message: 'Starting backtest loop...' },
  { time: '2024-01-01 00:00:05', level: 'WARN', message: 'Missing data points for 002371.SZ on 2021-05-12. Interpolating.' },
  { time: '2024-01-01 00:00:08', level: 'INFO', message: 'Multi-asset optimization enabled. Level 2.' },
  { time: '2024-01-01 00:00:12', level: 'WARN', message: 'Margin call threshold reached on 2022-04-15. No action taken.' },
  { time: '2024-01-01 00:00:15', level: 'SUCCESS', message: 'Backtest completed in 14.2s.' },
  { time: '2024-01-01 00:00:15', level: 'INFO', message: 'Final Value: 1,324,412.00 (Cash: 245,820.45)' }
])

// 返回策略中心
const goBack = () => {
  router.push('/backtest')
}

// 编辑策略
const editStrategy = () => {
  router.push(`/backtest/edit/${strategyId}`)
}
</script>

<template>
  <div class="flex-1 bg-white flex flex-col overflow-hidden min-h-0 h-full">
    <!-- 顶部导航栏 - 按照设计文件 -->
    <header class="flex items-center justify-between px-6 h-14 border-b border-slate-200 bg-white shrink-0">
      <!-- 返回按钮移到左边 -->
      <div class="flex items-center">
        <button
          class="flex items-center gap-1 mr-6 text-sm text-slate-600 hover:text-primary transition-colors"
          @click="goBack"
        >
          <Icon icon="mdi:arrow-left" :size="20" />
          返回策略中心
        </button>
        <div class="h-6 w-px bg-slate-200 mr-6"></div>
        <div class="flex items-center h-full space-x-8">
          <div class="flex items-center h-full">
            <button
              class="h-full px-4 text-sm font-medium text-slate-500 hover:text-primary transition-colors"
              @click="editStrategy"
            >
              编辑策略
            </button>
            <button class="h-full px-4 text-sm font-bold active-tab">
              回测详情
            </button>
          </div>
          <div class="h-6 w-px bg-slate-200"></div>
          <span class="text-sm font-medium text-slate-600">策略: {{ backtestData.strategyName }}</span>
        </div>
      </div>
      <div class="flex items-center space-x-4">
        <!-- 右侧可以放其他操作按钮 -->
      </div>
    </header>

    <!-- 内容区域 - 添加左右留白 -->
    <main class="flex-1 overflow-auto p-6">
      <!-- Top Section: Essential Parameters -->
      <section class="grid grid-cols-1 md:grid-cols-4 gap-4 border border-slate-200 rounded p-4 bg-white shadow-sm mb-4">
      <div class="border-r border-slate-100 last:border-0">
        <p class="text-[10px] text-slate-400 uppercase font-bold tracking-wider mb-1">回测策略名称</p>
        <div class="flex items-center gap-2">
          <Icon icon="mdi:code-braces" :size="20" class="text-primary" />
          <h1 class="text-sm font-bold truncate">{{ backtestData.strategyName }}</h1>
        </div>
      </div>
      <div class="border-r border-slate-100 last:border-0 px-2">
        <p class="text-[10px] text-slate-400 uppercase font-bold tracking-wider mb-1">测试时间周期</p>
        <p class="text-sm font-mono font-medium">{{ backtestData.timePeriod }}</p>
      </div>
      <div class="border-r border-slate-100 last:border-0 px-2">
        <p class="text-[10px] text-slate-400 uppercase font-bold tracking-wider mb-1">初始资金 / 期末权益</p>
        <div class="flex items-baseline gap-2">
          <span class="text-sm font-mono">{{ backtestData.initialCapital }}</span>
          <span class="text-slate-300 text-xs">→</span>
          <span class="text-sm font-mono font-bold text-success">{{ backtestData.finalEquity }}</span>
        </div>
      </div>
      <div class="px-2 flex justify-between items-center">
        <div>
          <p class="text-[10px] text-slate-400 uppercase font-bold tracking-wider mb-1">总收益率</p>
          <div class="flex items-center gap-2">
            <span class="text-xl font-bold text-success">{{ backtestData.totalReturn }}</span>
            <span class="px-1.5 py-0.5 bg-success/10 text-success text-[10px] font-bold rounded ring-1 ring-success/20">{{ backtestData.benchmark }}</span>
          </div>
        </div>
        <div class="flex gap-2">
          <button class="p-1.5 hover:bg-slate-50 text-slate-400 rounded transition-colors" title="设置">
            <Icon icon="mdi:cog" :size="20" />
          </button>
          <button class="bg-primary text-white px-3 py-1.5 rounded text-xs font-bold flex items-center gap-1 hover:bg-blue-700">
            <Icon icon="mdi:play" :size="16" />
            重新运行
          </button>
        </div>
        </div>
      </section>

      <!-- Middle Section: Main Equity Chart -->
    <section class="border border-slate-200 rounded bg-white shadow-sm flex flex-col overflow-hidden min-h-[400px] mb-4">
      <div class="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
        <div class="flex items-center gap-4">
          <h3 class="text-sm font-bold flex items-center gap-2">
            <Icon icon="mdi:chart-line" :size="20" class="text-primary" />
            策略净值曲线 vs 沪深300基准
          </h3>
          <div class="flex items-center gap-3 text-[11px]">
            <div class="flex items-center gap-1.5">
              <span class="w-3 h-0.5 bg-primary"></span>
              <span class="text-slate-600 font-medium">策略组合 (Strategy)</span>
            </div>
            <div class="flex items-center gap-1.5">
              <span class="w-3 h-0.5 bg-slate-300"></span>
              <span class="text-slate-400 font-medium">沪深300 (CSI 300)</span>
            </div>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button class="text-[11px] px-2 py-1 border border-slate-200 rounded bg-white hover:bg-slate-50">日线</button>
          <button class="text-[11px] px-2 py-1 bg-slate-100 font-bold border border-slate-200 rounded">周线</button>
          <div class="w-px h-4 bg-slate-200 mx-1"></div>
          <button class="p-1 text-slate-400 hover:text-slate-600">
            <Icon icon="mdi:fullscreen" :size="20" />
          </button>
        </div>
      </div>
      <div class="flex-1 relative p-6">
        <!-- Chart Placeholder -->
        <div class="w-full h-full bg-slate-50 rounded flex items-center justify-center text-slate-400">
          策略净值曲线图 (Canvas)
        </div>
      </div>
    </section>

    <!-- Bottom Section: Transaction Log & System Log -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 h-[350px]">
      <!-- Transaction Log -->
      <div class="border border-slate-200 rounded bg-white shadow-sm flex flex-col overflow-hidden">
        <div class="px-4 py-2 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
          <h3 class="text-[12px] font-bold text-slate-600 flex items-center gap-1.5">
            <Icon icon="mdi:list-status" :size="16" />
            Cerebro 交易明细
          </h3>
          <span class="text-[10px] text-slate-400 font-mono">Total: 1,284 Trades</span>
        </div>
        <div class="flex-1 overflow-auto log-container">
          <table class="w-full text-left text-[11px] border-collapse font-mono">
            <thead class="sticky top-0 bg-white shadow-sm text-slate-400 font-bold uppercase">
              <tr>
                <th class="px-4 py-2 border-b border-slate-50">成交时间</th>
                <th class="px-4 py-2 border-b border-slate-50">代码</th>
                <th class="px-4 py-2 border-b border-slate-50">类型</th>
                <th class="px-4 py-2 border-b border-slate-50 text-right">价格</th>
                <th class="px-4 py-2 border-b border-slate-50 text-right">数量</th>
                <th class="px-4 py-2 border-b border-slate-50 text-right">净盈亏</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-50">
              <tr
                v-for="(trade, index) in transactionLog"
                :key="index"
                class="hover:bg-slate-50/50"
              >
                <td class="px-4 py-2 text-slate-500">{{ trade.time }}</td>
                <td class="px-4 py-2 font-bold text-slate-800">{{ trade.code }}</td>
                <td class="px-4 py-2">
                  <span :class="trade.type === 'BUY' ? 'text-primary font-bold' : 'text-success font-bold'">
                    {{ trade.type }}
                  </span>
                </td>
                <td class="px-4 py-2 text-right">{{ trade.price }}</td>
                <td class="px-4 py-2 text-right text-slate-500">{{ trade.quantity }}</td>
                <td class="px-4 py-2 text-right" :class="trade.profit.startsWith('+') ? 'text-success font-bold' : trade.profit.startsWith('-') ? 'text-danger font-bold' : 'text-slate-300'">
                  {{ trade.profit }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- System Log -->
      <div class="border border-slate-200 rounded bg-white shadow-sm flex flex-col overflow-hidden">
        <div class="px-4 py-2 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
          <h3 class="text-[12px] font-bold text-slate-600 flex items-center gap-1.5">
            <Icon icon="mdi:terminal" :size="16" />
            系统运行日志 (System Log)
          </h3>
          <div class="flex items-center gap-2">
            <span class="flex items-center gap-1 text-[10px] text-danger">
              <span class="w-1.5 h-1.5 rounded-full bg-danger"></span> 0 Errors
            </span>
            <span class="flex items-center gap-1 text-[10px] text-amber-500">
              <span class="w-1.5 h-1.5 rounded-full bg-amber-500"></span> 2 Warnings
            </span>
          </div>
        </div>
        <div class="flex-1 bg-slate-900 p-4 font-mono text-[11px] text-slate-300 overflow-auto log-container">
          <div
            v-for="(log, index) in systemLog"
            :key="index"
            class="mb-1"
          >
            <span class="text-slate-500">[{{ log.time }}]</span>
            <span :class="{
              'text-blue-400': log.level === 'INFO',
              'text-amber-500': log.level === 'WARN',
              'text-success': log.level === 'SUCCESS'
            }">
              {{ log.level }}:
            </span>
            {{ log.message }}
            </div>
            <div class="animate-pulse text-primary">_</div>
          </div>
        </div>
      </div>
    </main>

    <!-- Footer Status Bar -->
    <footer class="bg-white border-t border-slate-200 px-6 py-1.5 flex items-center justify-between text-[10px] text-slate-400 font-medium shrink-0">
      <div class="flex items-center gap-4">
        <span class="flex items-center gap-1">
          <span class="w-1.5 h-1.5 rounded-full bg-success"></span> Connected to DataServer
        </span>
        <span>Backtrader v1.9.78.123</span>
      </div>
      <div>
        Memory Usage: 428MB / 4096MB
      </div>
    </footer>
  </div>
</template>

<style scoped>
.log-container::-webkit-scrollbar {
  width: 4px;
}

.log-container::-webkit-scrollbar-track {
  background: transparent;
}

.log-container::-webkit-scrollbar-thumb {
  background: #e2e8f0;
  border-radius: 10px;
}

.active-tab {
  border-bottom: 2px solid #0066FF;
  color: #0066FF;
}
</style>