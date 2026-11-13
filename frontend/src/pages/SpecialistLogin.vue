<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import HumaineLogo from '@/components/HumaineLogo.vue'
import { useSpecialistAuthStore } from '@/stores/useSpecialistAuthStore'

const WORKSPACE_HOME = '/ticket-resolution'
const WORKSPACE_PATH = /^\/ticket-resolution(?:[/?#]|$)/

const route = useRoute()
const router = useRouter()
const session = useSpecialistAuthStore()

const username = ref('')
const password = ref('')

const canSubmit = computed(() => username.value.trim().length > 0 && password.value.length > 0)

// Only follow redirects that stay inside the workspace.
const redirectTarget = computed(() => {
  const target = route.query.redirect
  return typeof target === 'string' && WORKSPACE_PATH.test(target) ? target : WORKSPACE_HOME
})

async function handleSubmit() {
  if (!canSubmit.value) return
  session.login(username.value.trim())
  await router.replace(redirectTarget.value)
}
</script>

<template>
  <div class="specialist-login">
    <section class="specialist-login__access" aria-label="Specialist workspace sign in">
      <div class="specialist-login__content">
        <div class="specialist-login__brand">
          <HumaineLogo
            class="specialist-login__logo"
            :width="854"
            :height="304"
          />
          <p class="specialist-login__product">Specialist Resolution Workspace · Tier 2 Support</p>
        </div>

        <form class="specialist-login__form" @submit.prevent="handleSubmit">
          <div>
            <h1 class="specialist-login__title">Sign in</h1>
            <p class="specialist-login__copy">
              Resolve routed tickets with replies drafted from similar past tickets.
            </p>
          </div>

          <label class="specialist-login__field">
            <span class="specialist-login__label">Username</span>
            <Input
              v-model="username"
              name="username"
              autocomplete="username"
              placeholder="Enter your username"
              :required="true"
            />
          </label>

          <label class="specialist-login__field">
            <span class="specialist-login__label">Password</span>
            <Input
              v-model="password"
              name="password"
              type="password"
              autocomplete="current-password"
              placeholder="Enter your password"
              :required="true"
            />
          </label>

          <Button type="submit" :disabled="!canSubmit" class="specialist-login__submit">
            Sign in
          </Button>

          <p class="specialist-login__note">
            Demo sign-in: any username and password works. No real authentication takes place.
          </p>
        </form>
      </div>
    </section>
  </div>
</template>

<style scoped lang="scss">
.specialist-login {
  display: grid;
  width: calc(100% + 2rem);
  min-height: 100vh;
  min-height: 100dvh;
  margin: -1rem;
  background: #fbfaf7;

  &__access {
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 0;
    padding: 3rem clamp(2rem, 6vw, 6rem);
  }

  &__content {
    width: min(100%, 24rem);
    margin: auto;
  }

  &__brand {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
    margin-bottom: 2rem;
  }

  &__logo {
    display: block;
    width: min(100%, 30rem);
    height: auto;
  }

  &__product {
    margin: 0;
    color: var(--muted-foreground);
    font-size: 0.75rem;
  }

  &__form {
    display: flex;
    flex-direction: column;
    gap: 1.1rem;
  }

  &__title {
    margin: 0;
    color: #25342d;
    font-size: 1.45rem;
    font-weight: 600;
    letter-spacing: -0.035em;
  }

  &__copy {
    margin: 0.45rem 0 0;
    color: #777a74;
    font-size: 0.82rem;
    line-height: 1.5;
  }

  &__field {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }

  &__label {
    color: #333a35;
    font-size: 0.78rem;
    font-weight: 500;
  }

  &__field :deep(.input) {
    height: 2.75rem;
    border-color: #e4e5df;
    border-radius: 0.55rem;
    background: #fff;
    font-size: 0.875rem;

    &:focus-visible {
      border-color: #87988d;
      box-shadow: 0 0 0 3px rgb(112 135 122 / 15%);
    }
  }

  &__submit {
    width: 100%;
    height: 2.75rem;
    margin-top: 0.15rem;
    border-radius: 0.55rem;
  }

  &__note {
    margin: 0;
    color: var(--muted-foreground);
    font-size: 0.75rem;
    line-height: 1.5;
  }

  @media (max-width: 480px) {
    &__access {
      padding: 2.5rem 1.5rem;
    }
  }
}
</style>
