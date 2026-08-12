<script setup lang="ts">
import { computed, ref } from 'vue'
import { Search, X, BookOpen } from 'lucide-vue-next'
import Button from '@/components/ui/Button.vue'
import { TEAM_GUIDE_BY_NAME } from '@/data/teamGuide'
import { useTutorialStore } from '@/stores/useTutorialStore'

const props = defineProps<{
  teams?: string[]
}>()

const emit = defineEmits<{
  (e: 'select', team: string): void
}>()

const isOpen = ref(false)
const searchQuery = ref('')

const tutorial = useTutorialStore()
const tourBlocked = computed(() => tutorial.activeTour !== null)

const entries = computed(() => {
  const available = props.teams ?? Object.keys(TEAM_GUIDE_BY_NAME)
  const query = searchQuery.value.trim().toLowerCase()

  return available
    .map((name) => TEAM_GUIDE_BY_NAME[name] ?? { name, description: 'No description is available for this team.' })
    .filter((entry) => {
      if (!query) return true
      return `${entry.name} ${entry.description}`.toLowerCase().includes(query)
    })
})

function openGuide() {
  if (tourBlocked.value) return
  searchQuery.value = ''
  isOpen.value = true
}

function closeGuide() {
  isOpen.value = false
}

function selectTeam(team: string) {
  emit('select', team)
  closeGuide()
}
</script>

<template>
  <Button
    variant="ghost"
    size="sm"
    type="button"
    data-testid="team-guide-trigger"
    :disabled="tourBlocked"
    :title="tourBlocked ? 'Unavailable during the tour' : undefined"
    @click="openGuide()"
  >
    <BookOpen :size="14" />
    Team guide
  </Button>

  <Teleport to="body">
    <div v-if="isOpen" class="team-guide" data-testid="team-guide">
      <button class="team-guide__backdrop" type="button" aria-label="Close team guide" @click="closeGuide" />
      <section class="team-guide__panel" role="dialog" aria-label="Team guide">
        <header class="team-guide__header">
          <div>
            <h2><BookOpen :size="18" /> Team guide</h2>
            <p>Search the team descriptions before choosing a label.</p>
          </div>
          <Button
            variant="ghost"
            size="icon"
            type="button"
            aria-label="Close team guide"
            @click="closeGuide"
          >
            <X :size="18" />
          </Button>
        </header>

        <div class="team-guide__search">
          <Search :size="15" />
          <input v-model="searchQuery" type="search" placeholder="Search teams and descriptions..." />
          <button v-if="searchQuery" type="button" aria-label="Clear search" @click="searchQuery = ''">
            <X :size="13" />
          </button>
        </div>

        <div class="team-guide__count">
          {{ entries.length }} team{{ entries.length === 1 ? '' : 's' }} shown
        </div>

        <div class="team-guide__list">
          <article v-for="entry in entries" :key="entry.name" class="team-guide__entry">
            <div class="team-guide__entry-heading">
              <h3>{{ entry.name }}</h3>
              <Button variant="outline" size="sm" type="button" @click="selectTeam(entry.name)">
                Use team
              </Button>
            </div>
            <p>{{ entry.description }}</p>
          </article>
          <p v-if="entries.length === 0" class="team-guide__empty">No teams match that search.</p>
        </div>
      </section>
    </div>
  </Teleport>
</template>

<style scoped lang="scss">
.team-guide {
  position: fixed;
  inset: 0;
  z-index: 1000000002;
  display: flex;
  justify-content: flex-end;
}

.team-guide__backdrop {
  position: absolute;
  inset: 0;
  width: 100%;
  border: 0;
  background: rgba(15, 23, 42, 0.38);
  cursor: pointer;
}

.team-guide__panel {
  position: relative;
  display: flex;
  width: min(38rem, 100%);
  height: 100%;
  flex-direction: column;
  background: var(--background);
  border-left: 1px solid var(--border);
  box-shadow: -0.5rem 0 2rem rgba(15, 23, 42, 0.16);
}

.team-guide__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--border);

  h2 {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0;
    font-size: 1.05rem;
  }

  p {
    margin: 0.35rem 0 0;
    color: var(--muted-foreground);
    font-size: 0.8125rem;
  }
}

.team-guide__search {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 1rem 1.25rem 0.5rem;
  padding: 0.5rem 0.625rem;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--input-background);
  color: var(--muted-foreground);

  input {
    min-width: 0;
    flex: 1;
    border: 0;
    outline: 0;
    background: transparent;
    color: var(--foreground);
    font: inherit;
    font-size: 0.875rem;
  }

  button {
    display: inline-flex;
    padding: 0.15rem;
    border: 0;
    background: transparent;
    color: inherit;
    cursor: pointer;
  }
}

.team-guide__count {
  padding: 0 1.25rem 0.5rem;
  color: var(--muted-foreground);
  font-size: 0.75rem;
}

.team-guide__list {
  min-height: 0;
  flex: 1;
  overflow-y: auto;
  padding: 0 1.25rem 1.25rem;
}

.team-guide__entry {
  padding: 0.875rem 0;
  border-top: 1px solid var(--border);

  p {
    margin: 0.5rem 0 0;
    color: var(--muted-foreground);
    font-size: 0.8125rem;
    line-height: 1.55;
  }
}

.team-guide__entry-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;

  h3 {
    margin: 0;
    color: var(--foreground);
    font-size: 0.875rem;
    line-height: 1.35;
  }
}

.team-guide__empty {
  padding: 2rem 0;
  text-align: center;
  color: var(--muted-foreground);
  font-size: 0.875rem;
}

@media (max-width: 640px) {
  .team-guide__entry-heading {
    flex-direction: column;
  }
}
</style>
