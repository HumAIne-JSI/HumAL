<script setup lang="ts">
export interface CardProps {
  variant?: 'default' | 'outline' | 'elevated'
  padding?: 'none' | 'sm' | 'default' | 'lg'
}

const props = withDefaults(defineProps<CardProps>(), {
  variant: 'default',
  padding: 'default',
})
</script>

<template>
  <div
    :class="['card', `card-v-${props.variant}`, `card-p-${props.padding}`]"
    data-slot="card"
  >
    <!-- Header section: renders when title, description, or action slots are provided -->
    <div
      v-if="$slots.title || $slots.description || $slots.action"
      class="card__header"
      data-slot="card-header"
    >
      <div class="card__header-content">
        <h4 v-if="$slots.title" class="card__title" data-slot="card-title">
          <slot name="title" />
        </h4>
        <p v-if="$slots.description" class="card__description" data-slot="card-description">
          <slot name="description" />
        </p>
      </div>
      <div v-if="$slots.action" class="card__action" data-slot="card-action">
        <slot name="action" />
      </div>
    </div>

    <!-- Content section: default slot -->
    <div v-if="$slots.default" class="card__content" data-slot="card-content">
      <slot />
    </div>

    <!-- Footer section -->
    <div v-if="$slots.footer" class="card__footer" data-slot="card-footer">
      <slot name="footer" />
    </div>
  </div>
</template>

<style scoped lang="scss">
.card {
  display: flex;
  flex-direction: column;
  background-color: var(--card);
  color: var(--card-foreground);
  border-radius: var(--radius);
  overflow: hidden;
  min-width: 0;

  // Variants
  &-v-default {
    border: 1px solid var(--border);
  }

  &-v-outline {
    border: 1px solid var(--border);
    background-color: transparent;
  }

  &-v-elevated {
    box-shadow:
      0 1px 3px rgba(0, 0, 0, 0.1),
      0 1px 2px rgba(0, 0, 0, 0.06);
  }

  // Padding variants for content
  &-p-none .card__content {
    padding: 0;
  }

  &-p-sm .card__content {
    padding: 0.75rem;
  }

  &-p-default .card__content {
    padding: 1.5rem;

    &:first-of-type {
      padding-top: 1.5rem;
    }

    &:last-of-type {
      padding-bottom: 1.5rem;
    }
  }

  &-p-lg .card__content {
    padding: 2rem;

    &:first-of-type {
      padding-top: 2rem;
    }

    &:last-of-type {
      padding-bottom: 2rem;
    }
  }

  // Header
  &__header {
    display: grid;
    grid-template-columns: 1fr auto;
    align-items: start;
    gap: 1rem;
    padding: 1.5rem 1.5rem 1.25rem;
    border-bottom: 1px solid var(--border);

    &-content {
      display: flex;
      flex-direction: column;
      gap: 0.375rem;
      min-width: 0;
    }
  }

  &__title {
    margin: 0;
    line-height: 1.2;
    font-size: 1rem;
    font-weight: 600;
    color: var(--foreground);
  }

  &__description {
    margin: 0;
    font-size: 0.875rem;
    color: var(--muted-foreground);
    line-height: 1.4;
  }

  &__action {
    grid-column-start: 2;
    grid-row: 1 / span 2;
    align-self: start;
    justify-self: end;
  }

  // Content
  &__content {
    flex: 1;
    min-width: 0;
    overflow: hidden;
  }

  // Footer
  &__footer {
    display: flex;
    align-items: center;
    padding: 1.25rem 1.5rem 1.5rem;
    border-top: 1px solid var(--border);
  }
}
</style>
