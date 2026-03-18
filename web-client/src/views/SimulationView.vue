<script setup lang="ts">
import { ref } from 'vue'

// 模拟账户数据
const accountInfo = ref({
  balance: 406200.00,
  totalAssets: 1248500.00,
  todayPL: 15240.50,
  todayPLPercent: 1.24
})

// 模拟持仓数据
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
    plPercent: 1.65
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
    plPercent: -2.05
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
    plPercent: 3.66
  }
])

// 模拟订单数据
const orders = ref([
  {
    id: 1,
    time: '09:30:15',
    name: '贵州茅台',
    code: '600519.SH',
    type: '买入',
    price: 1880.00,
    quantity: 100,
    status: '已成交'
  },
  {
    id: 2,
    time: '09:45:22',
    name: '宁德时代',
    code: '300750.SZ',
    type: '卖出',
    price: 216.00,
    quantity: 200,
    status: '已成交'
  },
  {
    id: 3,
    time: '10:15:30',
    name: '招商银行',
    code: '600036.SH',
    type: '买入',
    price: 36.50,
    quantity: 500,
    status: '部分成交'
  }
])
</script>

<template>
  <div class="min-h-screen bg-bgMain p-6">
    <div class="max-w-6xl mx-auto">
      <!-- Header -->
      <div class="flex justify-between items-center mb-6">
        <div>
          <h1 class="text-xl font-bold text-textMain">模拟交易</h1>
          <p class="text-sm text-textMute">模拟真实交易环境，练习交易策略</p>
        </div>
        <div class="flex gap-2">
          <button class="px-4 py-2 bg-primary text-white text-sm font-bold rounded hover:bg-blue-600 transition-colors">
            充值
          </button>
          <button class="px-4 py-2 border border-gray-200 text-textMain text-sm font-bold rounded hover:bg-gray-50 transition-colors">
            重置账户
          </button>
        </div>
      </div>

      <!-- Account Summary -->
      <div class="grid grid-cols-4 gap-4 mb-6">
        <div class="bg-card p-4 rounded-lg shadow-sm border border-border">
          <p class="text-xs text-textMute mb-1">模拟账户余额</p>
          <p class="text-xl font-bold font-numeric text-textMain">{{ accountInfo.balance.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</p>
        </div>
        <div class="bg-card p-4 rounded-lg shadow-sm border border-border">
          <p class="text-xs text-textMute mb-1">总资产</p>
          <p class="text-xl font-bold font-numeric text-textMain">{{ accountInfo.totalAssets.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</p>
        </div>
        <div class="bg-card p-4 rounded-lg shadow-sm border border-border">
          <p class="text-xs text-textMute mb-1">今日盈亏</p>
          <div class="flex items-baseline space-x-2">
            <p class="text-xl font-bold font-numeric text-up">{{ accountInfo.todayPL > 0 ? '+' : '' }}{{ accountInfo.todayPL.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</p>
            <span class="text-sm font-semibold text-up">+{{ accountInfo.todayPLPercent }}%</span>
          </div>
        </div>
        <div class="bg-card p-4 rounded-lg shadow-sm border border-border">
          <p class="text-xs text-textMute mb-1">持仓市值</p>
          <p class="text-xl font-bold font-numeric text-textMain">
            {{ holdings.reduce((sum, h) => sum + h.marketValue, 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}
          </p>
        </div>
      </div>

      <!-- Main Content Grid -->
      <div class="grid grid-cols-3 gap-4">
        <!-- Left: Holdings -->
        <div class="col-span-2 bg-card rounded-lg shadow-sm border border-border overflow-hidden">
          <div class="px-4 py-3 border-b border-border flex justify-between items-center">
            <h3 class="font-bold text-sm text-textMain">持仓列表</h3>
            <button class="text-xs text-primary hover:underline">一键清仓</button>
          </div>
          <table class="w-full density-table">
            <thead class="bg-gray-50 dark:bg-gray-800 text-textMute">
              <tr>
                <th class="text-left">股票名称</th>
                <th class="text-left">代码</th>
                <th class="text-right">持仓</th>
                <th class="text-right">成本价</th>
                <th class="text-right">现价</th>
                <th class="text-right">市值</th>
                <th class="text-right">盈亏</th>
                <th class="text-right">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr 
                v-for="holding in holdings"
                :key="holding.id"
                class="hover:bg-primary/5"
              >
                <td class="font-medium text-textMain">{{ holding.name }}</td>
                <td class="text-textMute">{{ holding.code }}</td>
                <td class="text-right font-numeric text-textSub">{{ holding.quantity }}</td>
                <td class="text-right font-numeric text-textSub">{{ holding.avgCost.toFixed(2) }}</td>
                <td class="text-right font-numeric text-textSub">{{ holding.currentPrice.toFixed(2) }}</td>
                <td class="text-right font-numeric text-textSub">{{ holding.marketValue.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</td>
                <td 
                  :class="[
                    'text-right font-numeric font-bold',
                    holding.pl > 0 ? 'text-up' : 'text-down'
                  ]"
                >
                  {{ holding.pl > 0 ? '+' : '' }}{{ holding.pl.toFixed(2) }}
                </td>
                <td class="text-right">
                  <button class="text-primary hover:underline text-xs mr-2">买</button>
                  <button class="text-down hover:underline text-xs">卖</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Right: Order Panel -->
        <div class="bg-card rounded-lg shadow-sm border border-border p-4">
          <h3 class="font-bold text-sm text-textMain mb-4">下单面板</h3>
          
          <!-- Trade Form -->
          <div class="space-y-3 mb-6">
            <div>
              <label class="text-xs text-textMute block mb-1">股票代码</label>
              <input 
                type="text" 
                placeholder="输入股票代码"
                class="w-full px-3 py-2 border border-border rounded text-sm bg-card text-textMain focus:ring-2 focus:ring-primary/20 focus:border-primary"
              />
            </div>
            <div class="flex gap-2">
              <button class="flex-1 py-2 bg-up text-white text-sm font-bold rounded hover:opacity-90 transition-opacity">
                买入
              </button>
              <button class="flex-1 py-2 bg-down text-white text-sm font-bold rounded hover:opacity-90 transition-opacity">
                卖出
              </button>
            </div>
            <div>
              <label class="text-xs text-textMute block mb-1">价格</label>
              <input 
                type="number" 
                placeholder="委托价格"
                class="w-full px-3 py-2 border border-border rounded text-sm bg-card text-textMain focus:ring-2 focus:ring-primary/20 focus:border-primary"
              />
            </div>
            <div>
              <label class="text-xs text-textMute block mb-1">数量</label>
              <input 
                type="number" 
                placeholder="委托数量"
                class="w-full px-3 py-2 border border-border rounded text-sm bg-card text-textMain focus:ring-2 focus:ring-primary/20 focus:border-primary"
              />
            </div>
            <button class="w-full py-2 bg-primary text-white text-sm font-bold rounded hover:opacity-90 transition-opacity">
              确认下单
            </button>
          </div>

          <!-- Recent Orders -->
          <div>
            <h4 class="text-xs font-bold text-textMute mb-2">今日委托</h4>
            <div class="space-y-2">
              <div 
                v-for="order in orders"
                :key="order.id"
                class="flex justify-between items-center text-xs py-2 border-b border-border"
              >
                <div>
                  <p class="font-medium text-textMain">{{ order.name }}</p>
                  <p class="text-textMute">{{ order.time }} {{ order.type }}</p>
                </div>
                <div class="text-right">
                  <p class="font-numeric text-textSub">{{ order.price.toFixed(2) }} * {{ order.quantity }}</p>
                  <p 
                    :class="[
                      order.status === '已成交' ? 'text-down' : 
                      order.status === '部分成交' ? 'text-yellow-500 dark:text-yellow-400' : 'text-textMute'
                    ]"
                  >
                    {{ order.status }}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>