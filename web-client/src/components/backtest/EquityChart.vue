<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import * as echarts from 'echarts'
import type { EquityPoint } from '@/api/backtest'

const props = defineProps<{
  data: EquityPoint[]
  benchmark?: string
}>()

const chartRef = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

const initChart = () => {
  if (!chartRef.value) return
  
  chart = echarts.init(chartRef.value)
  
  const dates = props.data.map(d => d.date)
  const equityData = props.data.map(d => d.equity)
  const benchmarkData = props.data.map(d => d.benchmark)
  
  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: (params: any) => {
        const date = params[0]?.axisValue || ''
        let html = `<div style="font-weight:bold">${date}</div>`
        params.forEach((p: any) => {
          const color = p.seriesName === '策略' ? '#0066FF' : '#cbd5e1'
          html += `<div style="color:${color}">${p.seriesName}: ${p.value?.toLocaleString() || '-'}</div>`
        })
        return html
      }
    },
    legend: {
      show: false
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      top: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates,
      boundaryGap: false,
      axisLine: {
        lineStyle: {
          color: '#e2e8f0'
        }
      },
      axisLabel: {
        color: '#94a3b8',
        fontSize: 10,
        formatter: (value: string) => {
          const date = new Date(value)
          return `${date.getMonth() + 1}-${date.getDate()}`
        }
      },
      axisTick: {
        show: false
      }
    },
    yAxis: {
      type: 'value',
      scale: true,
      splitLine: {
        lineStyle: {
          color: '#f1f5f9',
          type: 'dashed'
        }
      },
      axisLabel: {
        color: '#94a3b8',
        fontSize: 10,
        formatter: (value: number) => (value / 10000).toFixed(0) + '万'
      },
      axisLine: {
        show: false
      },
      axisTick: {
        show: false
      }
    },
    series: [
      {
        name: '策略',
        type: 'line',
        data: equityData,
        smooth: true,
        symbol: 'none',
        lineStyle: {
          color: '#0066FF',
          width: 2
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(0, 102, 255, 0.2)' },
            { offset: 1, color: 'rgba(0, 102, 255, 0)' }
          ])
        }
      },
      {
        name: props.benchmark || '沪深300',
        type: 'line',
        data: benchmarkData,
        smooth: true,
        symbol: 'none',
        lineStyle: {
          color: '#cbd5e1',
          width: 2,
          type: 'dashed'
        }
      }
    ],
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        type: 'slider',
        show: false,
        start: 0,
        end: 100
      }
    ]
  }
  
  chart.setOption(option)
}

const updateChart = () => {
  if (!chart || props.data.length === 0) return
  
  const dates = props.data.map(d => d.date)
  const equityData = props.data.map(d => d.equity)
  const benchmarkData = props.data.map(d => d.benchmark)
  
  chart.setOption({
    xAxis: {
      data: dates
    },
    series: [
      {
        data: equityData
      },
      {
        data: benchmarkData
      }
    ]
  })
}

onMounted(() => {
  if (props.data.length > 0) {
    initChart()
  }
})

watch(() => props.data, () => {
  if (props.data.length > 0) {
    if (!chart) {
      initChart()
    } else {
      updateChart()
    }
  }
}, { deep: true })
</script>

<template>
  <div ref="chartRef" class="w-full h-full min-h-[300px]"></div>
</template>
