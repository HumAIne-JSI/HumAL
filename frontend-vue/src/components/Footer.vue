<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { Home, Brain, Target, MessageSquareText, Zap, Github, Mail, ExternalLink } from 'lucide-vue-next'
import HumaineLogo from './HumaineLogo.vue'

const currentYear = new Date().getFullYear()

const navLinks = [
  { path: '/', label: 'Home', icon: Home },
  { path: '/training', label: 'Model Training', icon: Brain },
  { path: '/dispatching', label: 'Dispatch Labeling', icon: Target },
  { path: '/ticket-resolution', label: 'Ticket Resolution', icon: MessageSquareText },
  { path: '/inference', label: 'Inference', icon: Zap },
]
</script>

<template>
  <footer class="footer">
    <div class="footer__container">
      <div class="footer__grid">
        <!-- Brand Section -->
        <div class="footer__brand">
          <div class="footer__logo">
            <HumaineLogo :width="150" :height="45" />
          </div>
          <p class="footer__description">
            Advanced machine learning platform for intelligent ticket classification and routing using active learning algorithms.
          </p>
          <div class="footer__social">
            <a
              href="mailto:contact@humaine.ai"
              class="footer__social-link"
              aria-label="Email"
            >
              <Mail :size="20" />
            </a>
            <a
              href="https://github.com/humaine"
              target="_blank"
              rel="noopener noreferrer"
              class="footer__social-link"
              aria-label="GitHub"
            >
              <Github :size="20" />
            </a>
            <a
              href="https://humaine.ai"
              target="_blank"
              rel="noopener noreferrer"
              class="footer__social-link"
              aria-label="Website"
            >
              <ExternalLink :size="20" />
            </a>
          </div>
        </div>

        <!-- Navigation Links -->
        <div class="footer__nav">
          <h4 class="footer__heading">Platform</h4>
          <ul class="footer__list">
            <li v-for="link in navLinks" :key="link.path">
              <RouterLink :to="link.path" class="footer__link">
                <component :is="link.icon" :size="16" />
                <span>{{ link.label }}</span>
              </RouterLink>
            </li>
          </ul>
        </div>

        <!-- Resources -->
        <div class="footer__resources">
          <h4 class="footer__heading">Resources</h4>
          <ul class="footer__list">
            <li>
              <a href="#" class="footer__link">Documentation</a>
            </li>
            <li>
              <a href="#" class="footer__link">API Reference</a>
            </li>
            <li>
              <a href="#" class="footer__link">Support</a>
            </li>
          </ul>
        </div>
      </div>

      <div class="footer__bottom">
        <p>&copy; {{ currentYear }} HumAIne. All rights reserved.</p>
      </div>
    </div>
  </footer>
</template>

<style lang="scss" scoped>
.footer {
  background-color: #f8fafc;
  border-top: 1px solid #e2e8f0;
  margin-top: 4rem;
  padding: 3rem 0 1.5rem;

  &__container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 1.5rem;
  }

  &__grid {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr;
    gap: 2rem;

    @media (max-width: 768px) {
      grid-template-columns: 1fr;
    }
  }

  &__brand {
    max-width: 400px;
  }

  &__logo {
    margin-bottom: 1rem;
  }

  &__description {
    color: #64748b;
    font-size: 0.875rem;
    line-height: 1.6;
    margin-bottom: 1rem;
  }

  &__social {
    display: flex;
    gap: 1rem;
  }

  &__social-link {
    color: #64748b;
    transition: color 0.2s;

    &:hover {
      color: #3b82f6;
    }
  }

  &__heading {
    font-weight: 600;
    font-size: 0.875rem;
    margin-bottom: 1rem;
    color: #1e293b;
  }

  &__list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  &__link {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: #64748b;
    font-size: 0.875rem;
    text-decoration: none;
    transition: color 0.2s;

    &:hover {
      color: #3b82f6;
    }
  }

  &__bottom {
    margin-top: 2rem;
    padding-top: 1.5rem;
    border-top: 1px solid #e2e8f0;
    text-align: center;

    p {
      color: #94a3b8;
      font-size: 0.875rem;
    }
  }
}
</style>
