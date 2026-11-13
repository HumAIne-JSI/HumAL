<script setup lang="ts">
import { computed } from 'vue'
import primaryLogo from '@/assets/images/logo.png'
import secondaryLogo from '@/assets/images/humaine-logo.png'

interface Props {
  width?: number
  height?: number
  variant?: 'primary' | 'secondary'
}

const props = withDefaults(defineProps<Props>(), {
  width: 200,
  variant: 'primary'
})

const logo = computed(() =>
  props.variant === 'secondary'
    ? { src: secondaryLogo, width: 1906, height: 446, alt: 'humAIne' }
    : {
        src: primaryLogo,
        width: 854,
        height: 304,
        alt: 'humAIne - Hybrid Human-AI Decision Support for Enhanced Human Empowerment in Dynamic Situations'
      }
)

const imageHeight = computed(() =>
  props.height ?? Math.round((props.width * logo.value.height) / logo.value.width)
)
</script>

<template>
  <img
    :src="logo.src"
    :alt="logo.alt"
    :width="width"
    :height="imageHeight"
    class="humaine-logo"
  />
</template>

<style lang="scss" scoped>
.humaine-logo {
  display: block;
  max-width: 100%;
  object-fit: contain;
}
</style>
