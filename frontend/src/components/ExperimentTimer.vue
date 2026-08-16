<script setup lang="ts">
import { computed } from 'vue'
import { RotateCcw, Timer } from 'lucide-vue-next'
import { useExperimentTimerStore } from '@/stores/useExperimentTimerStore'

const durations = [30, 60, 90] as const
const timer = useExperimentTimerStore()

const displayTime = computed(() => `${String(Math.floor(timer.remainingSeconds / 60)).padStart(2, '0')}:${String(timer.remainingSeconds % 60).padStart(2, '0')}`)
</script>

<template>
  <div class="experiment-timer" aria-label="Experiment timer">
    <Timer :size="15" class="experiment-timer__icon" />
    <span class="experiment-timer__label">Experiment timer</span>
    <div class="experiment-timer__durations">
      <button v-for="minutes in durations" :key="minutes" type="button" class="experiment-timer__duration" :class="{ 'experiment-timer__duration--active': timer.selectedMinutes === minutes }" :aria-label="`Set ${minutes} minute timer`" @click="timer.selectDuration(minutes)">{{ minutes }}m</button>
    </div>
    <strong v-if="timer.selectedMinutes" class="experiment-timer__display">{{ displayTime }}</strong>
    <button v-if="timer.selectedMinutes" type="button" class="experiment-timer__control" aria-label="Reset timer" @click="timer.reset"><RotateCcw :size="14" /></button>
  </div>
</template>

<style scoped>
.experiment-timer { display: flex; align-items: center; gap: .4rem; min-height: 2rem; padding: .25rem .5rem; border: 1px solid var(--border); border-radius: .5rem; background: var(--card); color: var(--muted-foreground); font-size: .75rem; }
.experiment-timer__icon { color: var(--primary); }
.experiment-timer__label { white-space: nowrap; }
.experiment-timer__durations { display: flex; gap: .15rem; }
.experiment-timer__duration, .experiment-timer__control { border: 0; border-radius: .3rem; background: transparent; color: inherit; cursor: pointer; padding: .25rem .35rem; }
.experiment-timer__duration:hover, .experiment-timer__control:hover, .experiment-timer__duration--active { background: var(--accent); color: var(--foreground); }
.experiment-timer__display { min-width: 3.2rem; color: var(--foreground); font-variant-numeric: tabular-nums; text-align: center; }
@media (max-width: 700px) { .experiment-timer__label { display: none; } }
</style>
