<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { toast } from 'vue-sonner'
import Card from '@/components/ui/Card.vue'
import Input from '@/components/ui/Input.vue'
import Button from '@/components/ui/Button.vue'
import HumaineLogo from '@/components/HumaineLogo.vue'
import { useAuthStore } from '@/stores/useAuthStore'
import { ApiError } from '@/types/api'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

type Mode = 'login' | 'register'
const mode = ref<Mode>('login')

const username = ref('')
const password = ref('')
const submitting = ref(false)

const title = computed(() => (mode.value === 'login' ? 'Sign in' : 'Create account'))
const submitLabel = computed(() => (mode.value === 'login' ? 'Sign in' : 'Register & sign in'))
const canSubmit = computed(
  () => username.value.trim().length > 0 && password.value.length > 0 && !submitting.value,
)

const redirectTarget = computed(() => {
  const r = route.query.redirect
  return typeof r === 'string' && r.startsWith('/') ? r : '/'
})

function switchMode(next: Mode) {
  mode.value = next
}

const handleSubmit = async () => {
  if (!canSubmit.value) return
  submitting.value = true
  try {
    const credentials = { username: username.value.trim(), password: password.value }
    if (mode.value === 'register') {
      await authStore.registerAndLogin(credentials)
      toast.success('Account created', { description: `Welcome, ${credentials.username}` })
    } else {
      await authStore.login(credentials)
      toast.success('Signed in', { description: `Welcome back, ${credentials.username}` })
    }
    await router.replace(redirectTarget.value)
  } catch (e) {
    const message =
      e instanceof ApiError ? e.detail : e instanceof Error ? e.message : 'Authentication failed'
    toast.error(mode.value === 'login' ? 'Sign in failed' : 'Registration failed', {
      description: message,
    })
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="login">
    <Card class="login__card">
      <div class="login__brand">
        <HumaineLogo class="login__logo" />
        <p class="login__subtitle">Human-in-the-loop Active Learning</p>
      </div>

      <div class="login__tabs" role="tablist">
        <button
          type="button"
          role="tab"
          class="login__tab"
          :class="{ 'login__tab--active': mode === 'login' }"
          :aria-selected="mode === 'login'"
          @click="switchMode('login')"
        >
          Sign in
        </button>
        <button
          type="button"
          role="tab"
          class="login__tab"
          :class="{ 'login__tab--active': mode === 'register' }"
          :aria-selected="mode === 'register'"
          @click="switchMode('register')"
        >
          Register
        </button>
      </div>

      <form class="login__form" @submit.prevent="handleSubmit">
        <h1 class="login__title">{{ title }}</h1>

        <label class="login__field">
          <span class="login__label">Username</span>
          <Input
            v-model="username"
            name="username"
            autocomplete="username"
            placeholder="your username"
            :required="true"
          />
        </label>

        <label class="login__field">
          <span class="login__label">Password</span>
          <Input
            v-model="password"
            name="password"
            type="password"
            :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
            placeholder="your password"
            :required="true"
          />
        </label>

        <Button type="submit" :loading="submitting" :disabled="!canSubmit" class="login__submit">
          {{ submitLabel }}
        </Button>
      </form>

      <p class="login__hint">
        Access is optional — the backend falls back to a shared system user when you are not
        signed in, but owner-only features require an account.
      </p>
    </Card>
  </div>
</template>

<style scoped lang="scss">
.login {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100%;
  padding: 2rem 1rem;

  &__card {
    width: 100%;
    max-width: 24rem;
    padding: 2rem;
  }

  &__brand {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
    text-align: center;
  }

  &__logo {
    height: 2.5rem;
  }

  &__subtitle {
    font-size: 0.8125rem;
    color: var(--muted-foreground);
  }

  &__tabs {
    display: flex;
    gap: 0.25rem;
    padding: 0.25rem;
    margin-bottom: 1.5rem;
    background-color: var(--muted);
    border-radius: var(--radius);
  }

  &__tab {
    flex: 1;
    padding: 0.5rem;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--muted-foreground);
    background: transparent;
    border: none;
    border-radius: calc(var(--radius) - 2px);
    cursor: pointer;

    &--active {
      color: var(--foreground);
      background-color: var(--background);
      box-shadow: 0 1px 2px rgb(0 0 0 / 0.08);
    }
  }

  &__form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  &__title {
    font-size: 1.25rem;
    font-weight: 600;
    margin: 0;
  }

  &__field {
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
  }

  &__label {
    font-size: 0.8125rem;
    font-weight: 500;
    color: var(--foreground);
  }

  &__submit {
    margin-top: 0.5rem;
  }

  &__hint {
    margin-top: 1.25rem;
    font-size: 0.75rem;
    line-height: 1.4;
    color: var(--muted-foreground);
  }
}
</style>
