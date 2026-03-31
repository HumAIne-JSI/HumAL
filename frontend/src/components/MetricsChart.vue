<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  type ChartOptions,
} from 'chart.js'
import { Line } from 'vue-chartjs'

// Register only the components we need (tree-shaking)
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend)

export interface MetricsChartProps {
  scores: number[]
  label?: string
  height?: number
}

const props = withDefaults(defineProps<MetricsChartProps>(), {
  label: 'F1 Score',
  height: 200,
})

// CSS variable colors - read dynamically
const primaryColor = ref('hsl(221, 83%, 53%)')
const mutedColor = ref('hsl(215, 20%, 65%)')
const borderColor = ref('hsl(214, 32%, 91%)')
const foregroundColor = ref('hsl(222, 47%, 11%)')

const readCssVariables = () => {
  const root = document.documentElement
  const style = getComputedStyle(root)

  // Try to read CSS variables, fallback to defaults
  const primary = style.getPropertyValue('--primary').trim()
  const muted = style.getPropertyValue('--muted-foreground').trim()
  const border = style.getPropertyValue('--border').trim()
  const foreground = style.getPropertyValue('--foreground').trim()

  if (primary) primaryColor.value = primary
  if (muted) mutedColor.value = muted
  if (border) borderColor.value = border
  if (foreground) foregroundColor.value = foreground
}

onMounted(() => {
  readCssVariables()
})

// Watch for theme changes (dark/light mode toggle)
watch(
  () => document.documentElement.className,
  () => readCssVariables(),
  { deep: true }
)

const chartData = computed(() => ({
  labels: props.scores.map((_, i) => `Iteration ${i + 1}`),
  datasets: [
    {
      label: props.label,
      data: props.scores,
      borderColor: primaryColor.value,
      backgroundColor: `${primaryColor.value}33`, // 20% opacity
      tension: 0.3,
      fill: true,
      pointRadius: 4,
      pointHoverRadius: 6,
      pointBackgroundColor: primaryColor.value,
      pointBorderColor: '#fff',
      pointBorderWidth: 2,
    },
  ],
}))

const chartOptions = computed<ChartOptions<'line'>>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false,
    },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      titleColor: '#fff',
      bodyColor: '#fff',
      padding: 10,
      cornerRadius: 6,
      callbacks: {
        label: (context: { parsed: { y: number | null } }) => {
          const value = context.parsed.y
          return `${props.label}: ${((value ?? 0) * 100).toFixed(1)}%`
        },
      },
    },
  },
  scales: {
    x: {
      grid: {
        color: borderColor.value,
        drawBorder: false,
      },
      ticks: {
        color: mutedColor.value,
        font: {
          size: 11,
        },
      },
    },
    y: {
      min: 0,
      max: 1,
      grid: {
        color: borderColor.value,
        drawBorder: false,
      },
      ticks: {
        color: mutedColor.value,
        font: {
          size: 11,
        },
        callback: (value) => `${(Number(value) * 100).toFixed(0)}%`,
      },
    },
  },
  interaction: {
    intersect: false,
    mode: 'index',
  },
}))

const hasData = computed(() => props.scores.length > 0)
</script>

<template>
  <div class="metrics-chart" :style="{ height: `${height}px` }">
    <template v-if="hasData">
      <Line :data="chartData" :options="chartOptions" />
    </template>
    <div v-else class="metrics-chart__empty">
      <span>No data available</span>
    </div>
  </div>
</template>

<style scoped lang="scss">
.metrics-chart {
  width: 100%;
  position: relative;

  &__empty {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: var(--muted-foreground);
    font-size: 0.875rem;
  }
}
</style>
