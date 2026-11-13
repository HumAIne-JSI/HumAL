<script setup lang="ts">
import { ref, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { toast } from "vue-sonner";
import Input from "@/components/ui/Input.vue";
import Button from "@/components/ui/Button.vue";
import HumaineLogo from "@/components/HumaineLogo.vue";
import { useAuthStore } from "@/stores/useAuthStore";
import { ApiError } from "@/types/api";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

type Mode = "login" | "register";
const mode = ref<Mode>("login");

const username = ref("");
const password = ref("");
const submitting = ref(false);

const title = computed(() =>
  mode.value === "login" ? "Sign in" : "Create account",
);
const submitLabel = computed(() =>
  mode.value === "login" ? "Sign in" : "Register & sign in",
);
const canSubmit = computed(
  () =>
    username.value.trim().length > 0 &&
    password.value.length > 0 &&
    !submitting.value,
);

const redirectTarget = computed(() => {
  const r = route.query.redirect;
  return typeof r === "string" && r.startsWith("/") ? r : "/";
});

function switchMode(next: Mode) {
  mode.value = next;
}

const handleSubmit = async () => {
  if (!canSubmit.value) return;
  submitting.value = true;
  try {
    const credentials = {
      username: username.value.trim(),
      password: password.value,
    };
    if (mode.value === "register") {
      await authStore.registerAndLogin(credentials);
      toast.success("Account created", {
        description: `Welcome, ${credentials.username}`,
      });
    } else {
      await authStore.login(credentials);
      toast.success("Signed in", {
        description: `Welcome back, ${credentials.username}`,
      });
    }
    await router.replace(redirectTarget.value);
  } catch (e) {
    const message =
      e instanceof ApiError
        ? e.detail
        : e instanceof Error
          ? e.message
          : "Authentication failed";
    toast.error(
      mode.value === "login" ? "Sign in failed" : "Registration failed",
      {
        description: message,
      },
    );
  } finally {
    submitting.value = false;
  }
};
</script>

<template>
  <div class="login">
    <section class="login__access" aria-label="Account access">
      <div class="login__access-content">
        <div class="login__brand">
          <HumaineLogo
            class="login__logo"
            :width="854"
            :height="304"
          />
          <p class="login__subtitle">AI-Assisted Ticket Labeling</p>
        </div>

        <div class="login__tabs" role="group" aria-label="Choose an account action">
          <button
            type="button"
            class="login__tab"
            :class="{ 'login__tab--active': mode === 'login' }"
            :aria-pressed="mode === 'login'"
            @click="switchMode('login')"
          >
            Sign in
          </button>
          <button
            type="button"
            class="login__tab"
            :class="{ 'login__tab--active': mode === 'register' }"
            :aria-pressed="mode === 'register'"
            @click="switchMode('register')"
          >
            Register
          </button>
        </div>

        <form class="login__form" @submit.prevent="handleSubmit">
          <div class="login__form-heading">
            <h1 class="login__title">{{ title }}</h1>
            <p class="login__form-copy">
              {{
                mode === "login"
                  ? "Sign in to continue to your workspace."
                  : "Create an account to get started."
              }}
            </p>
          </div>

          <label class="login__field">
            <span class="login__label">Username</span>
            <Input
              v-model="username"
              name="username"
              autocomplete="username"
              placeholder="Enter your username"
              :required="true"
            />
          </label>

          <label class="login__field">
            <span class="login__label">Password</span>
            <Input
              v-model="password"
              name="password"
              type="password"
              :autocomplete="
                mode === 'login' ? 'current-password' : 'new-password'
              "
              placeholder="Enter your password"
              :required="true"
            />
          </label>

          <Button
            type="submit"
            :loading="submitting"
            :disabled="!canSubmit"
            class="login__submit"
          >
            {{ submitLabel }}
          </Button>
        </form>
      </div>
    </section>
  </div>
</template>

<style scoped lang="scss">
.login {
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

  &__access-content {
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

  &__subtitle {
    margin: 0;
    color: var(--muted-foreground);
    font-size: 0.75rem;
  }

  &__tabs {
    display: flex;
    gap: 1.25rem;
    margin-bottom: 1.75rem;
    border-bottom: 1px solid #e6e5df;
  }

  &__tab {
    position: relative;
    padding: 0 0 0.7rem;
    border: 0;
    color: var(--muted-foreground);
    background: transparent;
    cursor: pointer;
    font-size: 0.85rem;
    font-weight: 500;
    transition: color 0.15s ease;

    &--active {
      color: var(--foreground);

      &::after {
        position: absolute;
        right: 0;
        bottom: -1px;
        left: 0;
        height: 2px;
        border-radius: 2px 2px 0 0;
        background: var(--primary);
        content: '';
      }
    }

    &:focus-visible {
      border-radius: 0.15rem;
      outline: 2px solid var(--ring);
      outline-offset: 4px;
    }
  }

  &__form {
    display: flex;
    flex-direction: column;
    gap: 1.1rem;
  }

  &__form-heading {
    margin-bottom: 0.1rem;
  }

  &__title {
    margin: 0;
    color: #25342d;
    font-size: 1.45rem;
    font-weight: 600;
    letter-spacing: -0.035em;
  }

  &__form-copy {
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

  @media (max-width: 480px) {
    &__access {
      padding: 2.5rem 1.5rem;
    }
  }
}
</style>
