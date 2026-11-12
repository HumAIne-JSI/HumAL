<script setup lang="ts">
interface Props {
  title?: boolean
  description?: boolean
  action?: boolean
  lines?: number
}

const props = withDefaults(defineProps<Props>(), {
  title: true,
  description: false,
  action: false,
  lines: 3,
})
</script>

<template>
  <div
    class="skeleton-card"
    role="status"
    aria-label="Card loading"
  >
    <!-- Header section -->
    <div v-if="title || description || action" class="skeleton-card__header">
      <div class="skeleton-card__header-content">
        <div v-if="title" class="skeleton-card__title" />
        <div v-if="description" class="skeleton-card__description" />
      </div>
      <div v-if="action" class="skeleton-card__action" />
    </div>

    <!-- Content section: placeholder lines -->
    <div class="skeleton-card__content">
      <div
        v-for="i in lines"
        :key="i"
        class="skeleton-card__line"
        :class="{ 'skeleton-card__line--last': i === lines }"
      />
    </div>

    <!-- Footer section: optional action area placeholder -->
    <div class="skeleton-card__footer" />
  </div>
</template>

<style scoped lang="scss">
.skeleton-card {
  display: flex;
  flex-direction: column;
  background-color: var(--card);
  color: var(--card-foreground);
  border-radius: var(--radius);
  border: 1px solid var(--border);
  overflow: hidden;
}

.skeleton-card__header {
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: start;
  gap: 0.375rem;
  padding: 1.5rem 1.5rem 0;
}

.skeleton-card__header-content {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  min-width: 0;
}

.skeleton-card__title {
  height: 1.5rem;
  width: 60%;
  background-color: var(--muted);
  border-radius: 0.25rem;
  animation: shimmer 2s infinite;

  @media (prefers-reduced-motion: reduce) {
    animation: none;
    opacity: 0.6;
  }
}

.skeleton-card__description {
  height: 1rem;
  width: 70%;
  background-color: var(--muted);
  border-radius: 0.25rem;
  animation: shimmer 2s infinite;

  @media (prefers-reduced-motion: reduce) {
    animation: none;
    opacity: 0.6;
  }
}

.skeleton-card__action {
  width: 2.5rem;
  height: 2.5rem;
  background-color: var(--muted);
  border-radius: 0.25rem;
  animation: shimmer 2s infinite;

  @media (prefers-reduced-motion: reduce) {
    animation: none;
    opacity: 0.6;
  }
}

.skeleton-card__content {
  flex: 1;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-width: 0;
}

.skeleton-card__line {
  height: 1rem;
  background-color: var(--muted);
  border-radius: 0.25rem;
  animation: shimmer 2s infinite;

  &--last {
    width: 85%;
  }

  @media (prefers-reduced-motion: reduce) {
    animation: none;
    opacity: 0.6;
  }
}

.skeleton-card__footer {
  height: 3rem;
  background-color: var(--muted);
  border-radius: 0;
  margin-top: auto;
  animation: shimmer 2s infinite;

  @media (prefers-reduced-motion: reduce) {
    animation: none;
    opacity: 0.6;
  }
}

@keyframes shimmer {
  0%,
  100% {
    opacity: 0.4;
  }
  50% {
    opacity: 0.7;
  }
}
</style>
