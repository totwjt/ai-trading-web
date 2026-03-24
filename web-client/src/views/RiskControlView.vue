<script setup lang="ts">
import { ref } from 'vue'
import Icon from '@/components/common/Icon.vue'

// 行业集中度数据
const industryConcentration = ref([
  { name: '电子 (Electronics)', percent: 28.4 },
  { name: '医疗保健 (Healthcare)', percent: 15.2 },
  { name: '新能源 (New Energy)', percent: 12.8 },
  { name: '半导体 (Semiconductor)', percent: 10.5 },
  { name: '消费品 (Consumer)', percent: 8.2 }
])

// 个股持仓占比数据
const stockPositions = ref([
  { name: '宁德时代', code: '300750', percent: 11.42, status: '超限' },
  { name: '贵州茅台', code: '600519', percent: 10.15, status: '超限' },
  { name: '比亚迪', code: '002594', percent: 8.4, status: '正常' },
  { name: '隆基绿能', code: '601012', percent: 6.12, status: '正常' }
])

// 总仓位数据
const totalPosition = ref({
  stockPercent: 72.5,
  cashPercent: 27.5,
  availableCash: '¥3,432,000'
})

// 止损止盈策略数据
const strategies = ref([
  {
    name: '宁德时代',
    code: '300750',
    type: '固定比例 %',
    sl: '-5.0%',
    tp: '+15.0%',
    orderType: '市价委托 (Market)',
    status: '运行中'
  },
  {
    name: '东方财富',
    code: '300059',
    type: '移动止损',
    sl: '-3.5%',
    tp: '未设置',
    orderType: '限价委托 (Limit)',
    status: '运行中'
  },
  {
    name: '中国平安',
    code: '601318',
    type: '固定比例 %',
    sl: '-4.0%',
    tp: '+10.0%',
    orderType: '市价委托 (Market)',
    status: '已暂停'
  }
])

// 风控摘要数据
const riskSummary = ref({
  ruleCount: 12,
  coverage: 85.4,
  todayTrigger: 3
})

// 市场指标数据
const marketIndicators = ref({
  volatility: { value: 18.4, change: '+2.1%' },
  liquidity: { value: 'Normal', status: '稳定' }
})

// 波动率迷你图数据
const volatilityChart = ref([30, 45, 40, 60, 55, 80])

// 流动性迷你图数据
const liquidityChart = ref([70, 65, 75, 80, 72, 68])

// 风险事件流数据
const riskEvents = ref([
  {
    level: '紧急',
    levelClass: 'text-up',
    borderClass: 'border-l-2 border-up',
    time: '14:22:10',
    title: '宁德时代 (300750) 触发止损规则',
    content: 'AI诊断: 电子板块出现异动下跌，伴随成交量突然放大，股价突破 -5% 止损线。',
    result: '已自动减仓 30%'
  },
  {
    level: '提示',
    levelClass: 'text-primary',
    borderClass: 'border-l-2 border-primary',
    time: '14:05:32',
    title: '行业集中度接近限额',
    content: 'AI诊断: 电子板块仓位已达 28.4%，接近系统软上限 (30%)。建议关注后续买入。'
  },
  {
    level: '警告',
    levelClass: 'text-yellow-600',
    borderClass: 'border-l-2 border-yellow-500',
    time: '13:45:00',
    title: '流动性风险预警: 隆基绿能',
    content: '当前买盘深度不足，建议分批执行后续交易指令。'
  },
  {
    level: '提示',
    levelClass: 'text-primary',
    borderClass: 'border-l-2 border-primary',
    time: '13:12:15',
    title: '午间休市复盘',
    content: '账户Beta值从 0.88 调整至 0.85，市场敏感度降低。',
    opacity: true
  }
])
</script>

<template>
  <div class="min-h-screen bg-bgMain p-4 flex flex-col gap-4">
    <!-- 主内容网格 -->
    <div class="grid grid-cols-12 gap-4 flex-grow">
      
      <!-- 左侧列：仓位管理 -->
      <div class="col-span-12 flex flex-col gap-4 lg:col-span-3">
        <section class="bg-card rounded-lg p-4 flex-1 flex flex-col shadow-sm border border-border">
          <!-- 标题 -->
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-sm font-bold flex items-center gap-2">
              <span class="w-1 h-4 bg-primary rounded-full"></span>仓位管理
            </h2>
            <Icon icon="pie_chart" :size="18" class="text-textMute" />
          </div>

          <!-- 行业集中度 -->
          <div class="mb-6">
            <div class="text-[10px] text-textMute font-bold mb-3 uppercase tracking-widest">行业集中度 (TOP 5)</div>
            <div class="space-y-3">
              <div v-for="(item, index) in industryConcentration" :key="item.name" class="space-y-1">
                <div class="flex justify-between text-[11px] font-medium">
                  <span>{{ item.name }}</span>
                  <span>{{ item.percent }}%</span>
                </div>
                <div class="w-full bg-gray-100 h-1.5 rounded-full">
                  <div 
                    class="bg-primary h-full rounded-full" 
                    :style="{ width: item.percent + '%', opacity: 1 - (index * 0.15) }"
                  ></div>
                </div>
              </div>
            </div>
          </div>

          <!-- 个股持仓占比 -->
          <div class="flex-grow">
            <div class="flex justify-between items-center mb-3">
              <div class="text-[10px] text-textMute font-bold uppercase tracking-widest">个股持仓占比 (警戒线: 10%)</div>
              <span class="text-[9px] bg-up/10 text-up px-1.5 rounded font-bold">2个预警</span>
            </div>
            <div class="overflow-y-auto max-h-[300px] space-y-1 pr-1 custom-scrollbar">
              <div 
                v-for="stock in stockPositions" 
                :key="stock.code"
                class="flex items-center justify-between p-2 rounded hover:bg-gray-50 transition-colors"
                :class="stock.status === '超限' ? 'bg-gray-50' : ''"
              >
                <div class="flex flex-col">
                  <span class="text-xs font-bold leading-none">{{ stock.name }}</span>
                  <span class="text-[10px] text-textMute leading-tight">{{ stock.code }}</span>
                </div>
                <div class="flex items-center gap-3">
                  <div class="text-right">
                    <div 
                      class="text-xs font-numeric font-bold"
                      :class="stock.status === '超限' ? 'text-up' : ''"
                    >
                      {{ stock.percent }}%
                    </div>
                    <div 
                      class="text-[9px] font-medium"
                      :class="stock.status === '超限' ? 'text-up' : 'text-down'"
                    >
                      {{ stock.status }}
                    </div>
                  </div>
                  <div class="w-12 bg-gray-200 h-1 rounded-full relative overflow-hidden">
                    <div 
                      class="absolute left-0 top-0 h-full rounded-full"
                      :class="stock.status === '超限' ? 'bg-up' : 'bg-primary'"
                      :style="{ width: Math.min(stock.percent / 10 * 100, 100) + '%' }"
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 总仓位控制 -->
          <div class="mt-4 pt-4 border-t border-border">
            <div class="flex justify-between items-end">
              <div>
                <span class="text-[10px] text-textMute font-bold uppercase">总仓位控制</span>
                <div class="text-xl font-bold font-numeric">{{ totalPosition.stockPercent }}%</div>
              </div>
              <div class="text-right">
                <span class="text-[10px] text-textMute font-bold uppercase">可用现金</span>
                <div class="text-sm font-bold font-numeric text-primary">{{ totalPosition.availableCash }}</div>
              </div>
            </div>
            <div class="mt-2 h-3 w-full bg-gray-100 flex rounded overflow-hidden">
              <div class="h-full bg-primary" :style="{ width: totalPosition.stockPercent + '%' }"></div>
              <div class="h-full bg-gray-200" :style="{ width: totalPosition.cashPercent + '%' }"></div>
            </div>
            <div class="flex justify-between mt-1">
              <span class="text-[9px] text-textMute font-medium">股票持仓</span>
              <span class="text-[9px] text-textMute font-medium">闲置资金</span>
            </div>
          </div>
        </section>
      </div>

      <!-- 中间列：止损止盈策略管理 -->
      <div class="col-span-12 flex flex-col gap-4 lg:col-span-6">
        <section class="bg-card rounded-lg p-4 flex-1 flex flex-col shadow-sm border border-border">
          <!-- 标题 -->
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-sm font-bold flex items-center gap-2">
              <span class="w-1 h-4 bg-primary rounded-full"></span>止损止盈策略管理
            </h2>
            <button class="bg-primary text-white px-3 py-1 text-[11px] font-bold rounded flex items-center gap-1 hover:opacity-90 transition-opacity">
              <Icon icon="add_circle" :size="14" />
              新增规则
            </button>
          </div>

          <!-- 表格 -->
          <div class="overflow-x-auto flex-grow">
            <table class="w-full text-left">
              <thead class="bg-gray-50 border-b border-border">
                <tr>
                  <th class="py-2 text-[10px] font-bold text-textSub uppercase tracking-wider whitespace-nowrap px-2">标的名称/代码</th>
                  <th class="py-2 text-[10px] font-bold text-textSub uppercase tracking-wider whitespace-nowrap px-2">策略类型</th>
                  <th class="py-2 text-[10px] font-bold text-textSub uppercase tracking-wider whitespace-nowrap px-2">触发阈值</th>
                  <th class="py-2 text-[10px] font-bold text-textSub uppercase tracking-wider whitespace-nowrap px-2">执行指令</th>
                  <th class="py-2 text-[10px] font-bold text-textSub uppercase tracking-wider whitespace-nowrap px-2">状态</th>
                  <th class="py-2 text-[10px] font-bold text-textSub uppercase tracking-wider text-right whitespace-nowrap px-2">操作</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-border">
                <tr v-for="strategy in strategies" :key="strategy.code" class="hover:bg-gray-50 transition-colors">
                  <td class="py-2.5 whitespace-nowrap px-2">
                    <div class="flex flex-col">
                      <span class="text-xs font-bold">{{ strategy.name }}</span>
                      <span class="text-[10px] text-textMute">{{ strategy.code }}</span>
                    </div>
                  </td>
                  <td class="py-2.5 whitespace-nowrap px-2">
                    <span 
                      class="text-[10px] px-1.5 py-0.5 rounded font-medium"
                      :class="strategy.type === '移动止损' ? 'bg-primary text-white' : 'bg-primary/5 text-primary border border-primary/20'"
                    >
                      {{ strategy.type }}
                    </span>
                  </td>
                  <td class="py-2.5 whitespace-nowrap px-2">
                    <div class="flex flex-col gap-0.5">
                      <span class="text-[10px] text-up font-numeric font-bold">{{ strategy.sl }}</span>
                      <span class="text-[10px] text-down font-numeric font-bold">{{ strategy.tp }}</span>
                    </div>
                  </td>
                  <td class="py-2.5 whitespace-nowrap px-2">
                    <span class="text-[10px] font-medium text-textSub">{{ strategy.orderType }}</span>
                  </td>
                  <td class="py-2.5 whitespace-nowrap px-2">
                    <div class="flex items-center gap-1">
                      <span 
                        class="w-1.5 h-1.5 rounded-full"
                        :class="strategy.status === '运行中' ? 'bg-down' : 'bg-gray-300'"
                      ></span>
                      <span class="text-[10px] font-medium" :class="strategy.status === '运行中' ? '' : 'text-textMute'">
                        {{ strategy.status }}
                      </span>
                    </div>
                  </td>
                  <td class="py-2.5 text-right whitespace-nowrap px-2">
                    <button class="text-primary hover:underline text-[10px] font-bold">
                      {{ strategy.status === '已暂停' ? '激活' : '编辑' }}
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 风控摘要卡片 -->
          <div class="mt-4 p-3 bg-primary/5 border border-primary/10 rounded flex items-center justify-between">
            <div class="flex items-center gap-3">
              <Icon icon="security" :size="20" class="text-primary" />
              <div class="flex flex-col">
                <span class="text-[11px] font-bold">风控执行状态: 正常监控中</span>
                <span class="text-[9px] text-textSub">当前已部署 {{ riskSummary.ruleCount }} 条止损规则，覆盖账户 {{ riskSummary.coverage }}% 的资产。</span>
              </div>
            </div>
            <div class="flex gap-2">
              <div class="text-right">
                <span class="text-[10px] text-textMute">今日触发次数</span>
                <div class="text-sm font-bold font-numeric">{{ String(riskSummary.todayTrigger).padStart(2, '0') }}</div>
              </div>
            </div>
          </div>
        </section>
      </div>

      <!-- 右侧列：风险监测与预警 -->
      <div class="col-span-12 lg:col-span-3 flex flex-col gap-4">
        <section class="bg-card rounded-lg p-4 flex-1 flex flex-col shadow-sm border border-border">
          <!-- 标题 -->
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-sm font-bold flex items-center gap-2">
              <span class="w-1 h-4 bg-primary rounded-full"></span>风险监测与预警
            </h2>
            <Icon icon="notification" :size="18" class="text-textMute" />
          </div>

          <!-- 市场指标 -->
          <div class="grid grid-cols-2 gap-3 mb-6">
            <div class="bg-gray-50 p-2 rounded">
              <span class="text-[10px] text-textMute font-bold block mb-1">波动率 (VIX Equiv)</span>
              <div class="flex items-end gap-2">
                <span class="text-sm font-bold font-numeric">{{ marketIndicators.volatility.value }}</span>
                <span class="text-[9px] text-up font-medium">{{ marketIndicators.volatility.change }}</span>
              </div>
              <div class="mt-2 h-6 flex items-end gap-1 overflow-hidden">
                <div 
                  v-for="(h, i) in volatilityChart" 
                  :key="i"
                  class="w-1.5 rounded-t-sm"
                  :class="i === volatilityChart.length - 1 ? 'bg-primary' : 'bg-primary/20'"
                  :style="{ height: h + '%' }"
                ></div>
              </div>
            </div>
            <div class="bg-gray-50 p-2 rounded">
              <span class="text-[10px] text-textMute font-bold block mb-1">流动性指数 (Turnover)</span>
              <div class="flex items-end gap-2">
                <span class="text-sm font-bold font-numeric">{{ marketIndicators.liquidity.value }}</span>
                <span class="text-[9px] text-down font-medium">{{ marketIndicators.liquidity.status }}</span>
              </div>
              <div class="mt-2 h-6 flex items-end gap-1 overflow-hidden">
                <div 
                  v-for="(h, i) in liquidityChart" 
                  :key="i"
                  class="w-1.5 rounded-t-sm"
                  :class="i === liquidityChart.length - 1 ? 'bg-down' : 'bg-down/20'"
                  :style="{ height: h + '%' }"
                ></div>
              </div>
            </div>
          </div>

          <!-- 风险事件流 -->
          <div class="flex-grow flex flex-col">
            <div class="text-[10px] text-textMute font-bold mb-3 uppercase tracking-widest">风险事件流 (实时馈送)</div>
            <div class="space-y-4 overflow-y-auto max-h-[450px] pr-2 custom-scrollbar">
              <div 
                v-for="(event, index) in riskEvents" 
                :key="index"
                class="relative pl-4 border-l-2"
                :class="[event.borderClass, event.opacity ? 'opacity-60' : '']"
              >
                <div class="flex items-center justify-between mb-1">
                  <span class="text-[10px] font-bold" :class="event.levelClass">{{ event.level }}</span>
                  <span class="text-[10px] text-textMute">{{ event.time }}</span>
                </div>
                <div class="text-[11px] font-bold mb-1">{{ event.title }}</div>
                <p class="text-[10px] text-textSub leading-relaxed">
                  <span class="font-bold text-primary">AI诊断:</span> {{ event.content }}
                </p>
                <div v-if="event.result" class="mt-2 bg-up/5 p-1.5 rounded border border-up/10 text-[9px] font-bold flex items-center gap-1">
                  <Icon icon="check" :size="12" /> 执行结果: {{ event.result }}
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>

    <!-- 系统底部状态栏 -->
    <div class="flex items-center justify-between px-4 py-2 bg-gray-50 text-textMute text-[10px] font-medium rounded border border-border">
      <div class="flex gap-6">
        <span>系统状态: <span class="text-down">同步中 (低延迟模式)</span></span>
        <span>核心版本: Alpha-7.2.4</span>
        <span>风控服务器: 华东-02-Cluster</span>
      </div>
      <div class="flex items-center gap-1">
        <Icon icon="lock_open" :size="12" />
        安全审计已启用
      </div>
    </div>
  </div>
</template>
