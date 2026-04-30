<script setup lang="ts">
import { computed, ref } from 'vue'
import Icon from '@/components/common/Icon.vue'

interface RegionOption {
  code: string
  name: string
  active: boolean
}

interface EventTypeOption {
  label: string
  active: boolean
}

interface CalendarEvent {
  time: string
  country: string
  event: string
  impact: number
  actual: string
  forecast: string
  previous: string
  tone: 'up' | 'down' | 'neutral'
}

const period = ref<'month' | 'week'>('month')
const impactFilter = ref<'high' | 'medium' | 'low'>('high')

const regions = ref<RegionOption[]>([
  { code: 'CN', name: '中国', active: true },
  { code: 'US', name: '美国', active: true },
  { code: 'EU', name: '欧元区', active: false }
])

const eventTypes = ref<EventTypeOption[]>([
  { label: '宏观指标', active: true },
  { label: '央行动态', active: false },
  { label: '公司财报', active: false }
])

const events = ref<CalendarEvent[]>([
  {
    time: '09:45',
    country: 'CN',
    event: '财新制造业PMI (十月)',
    impact: 3,
    actual: '49.5',
    forecast: '50.8',
    previous: '50.6',
    tone: 'up'
  },
  {
    time: '17:30',
    country: 'EU',
    event: '欧元区制造业PMI (十月)',
    impact: 2,
    actual: '43.1',
    forecast: '43.0',
    previous: '43.4',
    tone: 'down'
  },
  {
    time: '20:30',
    country: 'US',
    event: '非农就业人数 (十月)',
    impact: 3,
    actual: '--',
    forecast: '180K',
    previous: '336K',
    tone: 'neutral'
  }
])

const activeRegionCodes = computed(() => {
  return regions.value.filter((region) => region.active).map((region) => region.code)
})

const filteredEvents = computed(() => {
  const minImpact = impactFilter.value === 'high' ? 3 : impactFilter.value === 'medium' ? 2 : 1

  return events.value.filter((item) => {
    return activeRegionCodes.value.includes(item.country) && item.impact >= minImpact
  })
})

const toggleRegion = (code: string) => {
  const target = regions.value.find((region) => region.code === code)

  if (!target) {
    return
  }

  target.active = !target.active
}

const selectEventType = (label: string) => {
  eventTypes.value = eventTypes.value.map((item) => ({
    ...item,
    active: item.label === label
  }))
}

const countryBadgeClass = (country: string) => {
  if (country === 'CN') {
    return 'bg-up/10 text-up'
  }

  if (country === 'US') {
    return 'bg-primary/10 text-primary'
  }

  return 'bg-down/10 text-down'
}

const actualValueClass = (tone: CalendarEvent['tone']) => {
  if (tone === 'up') {
    return 'text-up'
  }

  if (tone === 'down') {
    return 'text-down'
  }

  return 'text-textMain'
}
</script>

<template>
  <div class="min-h-[calc(100vh-48px)] bg-bgMain p-3">
    <div class="flex flex-col gap-6 xl:flex-row">
      <aside class="w-full shrink-0 space-y-6 xl:w-[360px]">
        <section class="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 class="mb-6 text-lg font-bold text-textMain">精准筛选</h2>

          <div class="mb-8">
            <p class="mb-4 text-xs font-bold uppercase tracking-[0.18em] text-textSub">地理区域</p>
            <div class="space-y-3">
              <button
                v-for="region in regions"
                :key="region.code"
                type="button"
                class="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm transition-colors"
                :class="region.active ? 'bg-primary/5 text-textMain' : 'text-textSub hover:bg-bgMain'"
                @click="toggleRegion(region.code)"
              >
                <span
                  class="flex h-6 w-6 items-center justify-center rounded border text-xs font-bold"
                  :class="region.active ? 'border-primary bg-primary text-white' : 'border-border bg-card text-transparent'"
                >
                  <Icon icon="mdi:check" :size="14" />
                </span>
                <span>{{ region.name }} ({{ region.code }})</span>
              </button>
            </div>
          </div>

          <div class="mb-8">
            <p class="mb-4 text-xs font-bold uppercase tracking-[0.18em] text-textSub">事件类别</p>
            <div class="space-y-3">
              <button
                v-for="item in eventTypes"
                :key="item.label"
                type="button"
                class="flex w-full items-center justify-between rounded-lg px-3 py-4 text-left text-sm transition-colors"
                :class="item.active ? 'bg-bgMain text-textMain' : 'text-textSub hover:bg-bgMain'"
                @click="selectEventType(item.label)"
              >
                <span>{{ item.label }}</span>
                <Icon
                  :icon="item.active ? 'mdi:check-circle-outline' : 'mdi:circle-outline'"
                  :size="20"
                  :class="item.active ? 'text-primary' : 'text-textMute'"
                />
              </button>
            </div>
          </div>

          <div>
            <p class="mb-4 text-xs font-bold uppercase tracking-[0.18em] text-textSub">影响波动率</p>
            <div class="space-y-3">
              <button
                type="button"
                class="flex w-full items-center justify-between rounded-lg px-4 py-4 text-left text-sm font-bold transition-colors"
                :class="impactFilter === 'high' ? 'bg-up text-white' : 'border border-border bg-card text-textMain hover:bg-bgMain'"
                @click="impactFilter = 'high'"
              >
                <span>高影响</span>
                <Icon icon="mdi:priority-high" :size="18" />
              </button>
              <button
                type="button"
                class="w-full rounded-lg border border-border px-4 py-4 text-left text-sm transition-colors"
                :class="impactFilter === 'medium' ? 'bg-primary/5 text-primary' : 'text-textMain hover:bg-bgMain'"
                @click="impactFilter = 'medium'"
              >
                中影响
              </button>
              <button
                type="button"
                class="w-full rounded-lg border border-border px-4 py-4 text-left text-sm transition-colors"
                :class="impactFilter === 'low' ? 'bg-primary/5 text-primary' : 'text-textMain hover:bg-bgMain'"
                @click="impactFilter = 'low'"
              >
                低影响
              </button>
            </div>
          </div>
        </section>

        <section class="overflow-hidden rounded-lg bg-primary shadow-sm">
          <div class="flex min-h-[360px] flex-col justify-end bg-gradient-to-br from-primary via-primary to-primary/80 p-6 text-white">
            <span class="mb-3 text-xs font-bold uppercase tracking-[0.18em] text-white/70">机构洞察</span>
            <h3 class="max-w-[220px] text-2xl font-bold leading-tight">第四季度波动率展望：结构性转变</h3>
            <button
              type="button"
              class="mt-6 w-fit rounded-lg border border-white/30 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-white/10"
            >
              阅读报告
            </button>
          </div>
        </section>
      </aside>

      <section class="min-w-0 flex-1">
        <header class="mb-8 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div class="flex flex-col gap-4 sm:flex-row sm:items-center">
            <h1 class="text-xl font-bold tracking-tight text-textMain">宏观日历</h1>
            <div class="flex w-fit rounded-full bg-border/70 p-1">
              <button
                type="button"
                class="rounded-full px-6 py-2 text-sm font-bold transition-colors"
                :class="period === 'month' ? 'bg-card text-primary shadow-sm' : 'text-textSub'"
                @click="period = 'month'"
              >
                月度
              </button>
              <button
                type="button"
                class="rounded-full px-6 py-2 text-sm font-bold transition-colors"
                :class="period === 'week' ? 'bg-card text-primary shadow-sm' : 'text-textSub'"
                @click="period = 'week'"
              >
                周度
              </button>
            </div>
          </div>

          <div class="flex flex-wrap items-center gap-3">
            <button
              type="button"
              class="flex items-center gap-2 rounded border border-border bg-card px-5 py-3 text-sm font-medium text-textMain shadow-sm"
            >
              <Icon icon="mdi:calendar-month-outline" :size="18" />
              <span>2023年11月</span>
            </button>
            <button
              type="button"
              class="flex items-center gap-2 rounded bg-primary px-5 py-3 text-sm font-bold text-white shadow-sm transition-opacity hover:opacity-90"
            >
              <Icon icon="mdi:download" :size="18" />
              <span>导出数据</span>
            </button>
          </div>
        </header>

        <div class="mb-12 text-base text-textMain">周一</div>

        <section class="overflow-hidden rounded-lg border border-border bg-card shadow-sm">
          <div class="border-b border-border px-6 py-5">
            <h2 class="text-lg font-bold text-textMain">详细经济指标</h2>
          </div>

          <div class="overflow-x-auto">
            <table class="min-w-full text-left">
              <thead class="bg-bgMain text-sm uppercase tracking-[0.18em] text-textSub">
                <tr>
                  <th class="px-6 py-5 font-bold">时间 (CST)</th>
                  <th class="px-6 py-5 font-bold">国家</th>
                  <th class="px-6 py-5 font-bold">事件</th>
                  <th class="px-6 py-5 text-center font-bold">影响</th>
                  <th class="px-6 py-5 text-right font-bold">实际</th>
                  <th class="px-6 py-5 text-right font-bold">预测</th>
                  <th class="px-6 py-5 text-right font-bold">前值</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="item in filteredEvents"
                  :key="`${item.country}-${item.time}-${item.event}`"
                  class="border-b border-border last:border-b-0 hover:bg-primary/5"
                >
                  <td class="px-6 py-6 text-sm font-numeric text-textMain">{{ item.time }}</td>
                  <td class="px-6 py-6">
                    <div class="flex items-center gap-3">
                      <span
                        class="rounded px-2 py-1 text-xs font-bold"
                        :class="countryBadgeClass(item.country)"
                      >
                        {{ item.country }}
                      </span>
                      <span class="text-sm text-textMain">{{ item.country }}</span>
                    </div>
                  </td>
                  <td class="px-6 py-6 text-sm font-bold text-textMain">{{ item.event }}</td>
                  <td class="px-6 py-6">
                    <div class="flex justify-center gap-1">
                      <Icon
                        v-for="index in 3"
                        :key="index"
                        icon="mdi:star-four-points"
                        :size="16"
                        :class="index <= item.impact ? (item.impact === 3 ? 'text-up' : 'text-primary') : 'text-border'"
                      />
                    </div>
                  </td>
                  <td class="px-6 py-6 text-right text-sm font-bold font-numeric" :class="actualValueClass(item.tone)">
                    {{ item.actual }}
                  </td>
                  <td class="px-6 py-6 text-right text-sm font-numeric text-textMain">{{ item.forecast }}</td>
                  <td class="px-6 py-6 text-right text-sm font-numeric text-textMain">{{ item.previous }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="flex justify-center px-6 py-6">
            <button type="button" class="flex items-center gap-2 text-sm font-bold text-primary">
              <span>查看未来48小时</span>
              <Icon icon="mdi:chevron-down" :size="20" />
            </button>
          </div>
        </section>
      </section>
    </div>

    <button
      type="button"
      class="fixed bottom-6 right-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary text-white shadow-2xl"
    >
      <Icon icon="mdi:bell-outline" :size="28" />
    </button>
  </div>
</template>
