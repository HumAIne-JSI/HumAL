<script setup lang="ts">
import { computed } from 'vue'
import { Play, RotateCcw, Timer } from 'lucide-vue-next'
import { useExperimentTimerStore } from '@/stores/useExperimentTimerStore'

const timer = useExperimentTimerStore()

const totalSeconds = computed(() => (timer.selectedMinutes ? timer.remainingSeconds : 90 * 60))
const displayTime = computed(() => `${String(Math.floor(totalSeconds.value / 60)).padStart(2, '0')}:${String(totalSeconds.value % 60).padStart(2, '0')}`)
</script>

<template>
  <div class="experiment-timer" aria-label="Experiment timer">
    <Timer :size="15" class="experiment-timer__icon" />
    <span class="experiment-timer__label">Experiment timer</span>
    <strong class="experiment-timer__display">{{ displayTime }}</strong>
    <button v-if="!timer.selectedMinutes" type="button" class="experiment-timer__control" aria-label="Start 90 minute timer" @click="timer.selectDuration(90)"><Play :size="14" /></button>
    <button v-else type="button" class="experiment-timer__control" aria-label="Reset timer" @click="timer.reset"><RotateCcw :size="14" /></button>
  </div>
</template>

<style scoped>
.experiment-timer { display: flex; align-items: center; gap: .4rem; min-height: 2rem; padding: .25rem .5rem; border: 1px solid var(--border); border-radius: .5rem; background: var(--card); color: var(--muted-foreground); font-size: .75rem; }
.experiment-timer__icon { color: var(--primary); }
.experiment-timer__label { white-space: nowrap; }
.experiment-timer__control { border: 0; border-radius: .3rem; background: transparent; color: inherit; cursor: pointer; padding: .25rem .35rem; }
.experiment-timer__control:hover { background: var(--accent); color: var(--foreground); }
.experiment-timer__display { min-width: 3.2rem; color: var(--foreground); font-variant-numeric: tabular-nums; text-align: center; }
@media (max-width: 700px) { .experiment-timer__label { display: none; } }
</style>
