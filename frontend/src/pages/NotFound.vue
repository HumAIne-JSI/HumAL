<script setup lang="ts">
import { useRoute } from 'vue-router'
import { onMounted } from 'vue'
import { Home } from 'lucide-vue-next'
import Button from '@/components/ui/Button.vue'

const route = useRoute()

onMounted(() => {
  console.error('404 Error: User attempted to access non-existent route:', route.path)
})
</script>

<template>
  <div class="not-found">
    <div class="not-found__content">
      <h1 class="not-found__code">404</h1>
      <p class="not-found__message">Oops! Page not found</p>
      <p class="not-found__description">
        The page you're looking for doesn't exist or has been moved.
      </p>
      <RouterLink to="/" class="not-found__link">
        <Button variant="default">
          <Home :size="18" />
          Return to Home
        </Button>
      </RouterLink>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.not-found {
  display: flex;
  min-height: calc(100vh - 8rem);
  align-items: center;
  justify-content: center;
  padding: 2rem;

  &__content {
    text-align: center;
    max-width: 400px;
  }

  &__code {
    font-size: 6rem;
    font-weight: 700;
    color: var(--color-primary, #3b82f6);
    line-height: 1;
    margin-bottom: 0.5rem;
  }

  &__message {
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--color-text-primary, #1f2937);
    margin-bottom: 0.5rem;
  }

  &__description {
    font-size: 1rem;
    color: var(--color-text-secondary, #6b7280);
    margin-bottom: 1.5rem;
  }

  &__link {
    text-decoration: none;
  }
}
</style>
