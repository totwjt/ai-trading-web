<script setup lang="ts">
import { computed, ref } from 'vue'
import Icon from '@/components/common/Icon.vue'

interface FactorRow {
  name: string
  english: string
  day: string
  week: string
  month: string
  quarter: string
  year: string
  winRate: string
  category?: string
}

const search = ref('')

const factors = ref<FactorRow[]>([
  {
    name: '动量',
    english: 'Momentum',
    day: '92.4%',
    week: '+0.045',
    month: '0.012',
    quarter: '0.52',
    year: '14.2%',
    winRate: '54.8%'
  },
  {
    name: '价值',
    english: 'Value',
    day: '88.1%',
    week: '+0.032',
    month: '0.008',
    quarter: '0.88',
    year: '2.1%',
    winRate: '51.2%'
  },
  {
    name: '成长',
    english: 'Growth',
    day: '75.0%',
    week: '-0.012',
    month: '0.015',
    quarter: '-0.14',
    year: '5.5%',
    winRate: '48.9%'
  },
  {
    name: 'Volatility_30D',
    english: '风险类',
    day: '100.0%',
    week: '+0.061',
    month: '0.021',
    quarter: '1.12',
    year: '22.4%',
    winRate: '58.2%',
    category: '风险类'
  },
  {
    name: 'Institutional_Flow_1D',
    english: '情绪类',
    day: '62.8%',
    week: '+0.088',
    month: '0.045',
    quarter: '0.45',
    year: '82.1%',
    winRate: '52.5%',
    category: '情绪类'
  }
])

const filteredFactors = computed(() => {
  const keyword = search.value.trim().toLowerCase()

  if (!keyword) {
    return factors.value
  }

  return factors.value.filter((factor) => {
    return factor.name.toLowerCase().includes(keyword) || factor.english.toLowerCase().includes(keyword)
  })
})

const metricClass = (value: string) => {
  if (value.startsWith('+')) {
    return 'text-up'
  }

  if (value.startsWith('-')) {
    return 'text-down'
  }

  return 'text-textMain'
}
</script>

<template>
  <div class="min-h-[calc(100vh-48px)] bg-bgMain p-3">
    <div>
      <header class="mb-10 flex flex-col gap-6 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <div class="mb-3 flex items-center gap-2 text-primary">
            <Icon icon="mdi:chart-box-outline" :size="20" />
            <span class="text-sm font-bold uppercase tracking-[0.3em]">Alpha Terminal</span>
          </div>
          <h1 class="text-xl font-bold tracking-tight text-textMain">
            因子看板
            <span class="ml-2 text-lg font-medium text-textSub">Factor Gallery</span>
          </h1>
          <p class="mt-3 max-w-3xl text-sm text-textSub">
            中国权益市场因子收益的量化分解。实时展示因子敞口、风格轮动及横截面表现指标。
          </p>
        </div>

        <div class="flex flex-wrap gap-3">
          <button
            type="button"
            class="flex items-center gap-2 rounded-lg bg-border/70 px-5 py-3 text-base font-medium text-textMain transition-colors hover:bg-border"
          >
            <Icon icon="mdi:download" :size="18" />
            <span>导出报告</span>
          </button>
          <button
            type="button"
            class="flex items-center gap-2 rounded-lg bg-primary px-5 py-3 text-base font-bold text-white shadow-sm transition-opacity hover:opacity-90"
          >
            <Icon icon="mdi:tune-variant" :size="18" />
            <span>调整样本股</span>
          </button>
        </div>
      </header>

      <div class="mb-8 text-sm font-medium leading-7 text-textMain">
        “在当前看涨行情下，动量依然是主导信号，但换手成本仍然处于高位。”
      </div>

      <section class="overflow-hidden rounded-xl border border-border bg-card shadow-sm">
        <div class="flex flex-col gap-4 border-b border-border px-6 py-5 lg:flex-row lg:items-center lg:justify-between">
          <h2 class="text-lg font-bold text-textMain">
            详细因子归因
            <span class="ml-2 text-base font-normal text-textSub">(月度调仓)</span>
          </h2>

          <label class="relative block">
            <Icon icon="mdi:magnify" :size="18" class="absolute left-3 top-1/2 -translate-y-1/2 text-textMute" />
            <input
              v-model="search"
              type="text"
              placeholder="搜索因子..."
              class="w-full rounded-lg border-0 bg-bgMain py-2 pl-10 pr-4 text-sm text-textMain focus:ring-1 focus:ring-primary lg:w-64"
            />
          </label>
        </div>

        <div class="overflow-x-auto">
          <table class="min-w-full text-left">
            <thead class="bg-bgMain text-sm uppercase tracking-[0.18em] text-textSub">
              <tr>
                <th class="px-6 py-4 font-bold">因子风格</th>
                <th class="px-3 py-4 text-right font-bold">日</th>
                <th class="px-3 py-4 text-right font-bold">周</th>
                <th class="px-3 py-4 text-right font-bold">月</th>
                <th class="px-3 py-4 text-right font-bold">季至今</th>
                <th class="px-3 py-4 text-right font-bold">年至今</th>
                <th class="px-3 py-4 text-right font-bold">胜率</th>
                <th class="px-6 py-4 text-right font-bold">操作</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-border">
              <tr
                v-for="factor in filteredFactors"
                :key="factor.name"
                class="hover:bg-primary/5"
              >
                <td class="px-6 py-6">
                  <div class="text-sm font-bold text-textMain">{{ factor.name }}</div>
                  <div class="mt-1 text-xs text-textSub">{{ factor.category || factor.english }}</div>
                </td>
                <td class="px-3 py-6 text-right text-sm font-numeric text-textMain">{{ factor.day }}</td>
                <td class="px-3 py-6 text-right text-sm font-numeric" :class="metricClass(factor.week)">{{ factor.week }}</td>
                <td class="px-3 py-6 text-right text-sm font-numeric text-textMain">{{ factor.month }}</td>
                <td class="px-3 py-6 text-right text-sm font-numeric text-textMain">{{ factor.quarter }}</td>
                <td class="px-3 py-6 text-right text-sm font-numeric text-textMain">{{ factor.year }}</td>
                <td class="px-3 py-6 text-right text-sm font-numeric text-textMain">{{ factor.winRate }}</td>
                <td class="px-6 py-6 text-right">
                  <button type="button" class="text-sm font-bold text-primary hover:underline">详情</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="flex justify-center border-t border-border bg-bgMain/50 px-6 py-5">
          <button type="button" class="flex items-center gap-2 text-sm font-bold text-textMain">
            <span>加载更多因子</span>
            <Icon icon="mdi:chevron-down" :size="18" />
          </button>
        </div>
      </section>

      <div class="pointer-events-none fixed bottom-6 right-6 flex justify-end">
        <section class="pointer-events-auto w-[360px] rounded-2xl border border-border bg-card p-5 shadow-2xl">
          <div class="mb-4 flex items-center gap-3">
            <div class="rounded-xl bg-primary/10 p-3 text-primary">
              <Icon icon="mdi:lightbulb-on-outline" :size="22" />
            </div>
            <h3 class="text-lg font-bold text-textMain">实时因子洞察</h3>
          </div>

          <p class="text-sm leading-7 text-textMain">
            <span class="font-bold text-up">动量</span>
            因子目前正在测试相对基准的上轨阻力。分析师建议，若CPI数据保持平稳，需关注向成长风格的轮动。
          </p>

          <div class="mt-5 flex justify-end">
            <button type="button" class="flex items-center gap-1 text-sm font-bold text-primary">
              <span>完整预测</span>
              <Icon icon="mdi:arrow-right" :size="18" />
            </button>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>
