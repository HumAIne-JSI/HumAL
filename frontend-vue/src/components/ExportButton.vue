<script setup lang="ts">
import { ref } from 'vue'
import Button from '@/components/ui/Button.vue'
import { Download, FileSpreadsheet, FileJson, FileText, ChevronDown } from 'lucide-vue-next'
import Papa from 'papaparse'
import * as XLSX from 'xlsx'

export interface ExportButtonProps {
  data: object[]
  filename?: string
  disabled?: boolean
}

const props = withDefaults(defineProps<ExportButtonProps>(), {
  filename: 'export',
  disabled: false,
})

const showMenu = ref(false)

const toggleMenu = () => {
  showMenu.value = !showMenu.value
}

const closeMenu = () => {
  showMenu.value = false
}

const downloadFile = (content: string | Blob, filename: string, type: string) => {
  const blob = content instanceof Blob ? content : new Blob([content], { type })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

const exportCsv = () => {
  const csv = Papa.unparse(props.data)
  downloadFile(csv, `${props.filename}.csv`, 'text/csv;charset=utf-8;')
  closeMenu()
}

const exportJson = () => {
  const json = JSON.stringify(props.data, null, 2)
  downloadFile(json, `${props.filename}.json`, 'application/json')
  closeMenu()
}

const exportExcel = () => {
  const worksheet = XLSX.utils.json_to_sheet(props.data)
  const workbook = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(workbook, worksheet, 'Data')

  // Generate buffer and create blob
  const excelBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' })
  const blob = new Blob([excelBuffer], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  })
  downloadFile(blob, `${props.filename}.xlsx`, '')
  closeMenu()
}

// Close menu when clicking outside
const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as HTMLElement
  if (!target.closest('.export-button')) {
    closeMenu()
  }
}

// Add/remove event listener based on menu state
import { watch, onUnmounted } from 'vue'

watch(showMenu, (isOpen) => {
  if (isOpen) {
    document.addEventListener('click', handleClickOutside)
  } else {
    document.removeEventListener('click', handleClickOutside)
  }
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div class="export-button">
    <Button
      variant="outline"
      :disabled="disabled || data.length === 0"
      @click="toggleMenu"
    >
      <Download :size="16" />
      Export
      <ChevronDown :size="14" />
    </Button>

    <Transition name="fade">
      <div v-if="showMenu" class="export-button__menu">
        <button class="export-button__item" @click="exportCsv">
          <FileText :size="16" />
          Export as CSV
        </button>
        <button class="export-button__item" @click="exportJson">
          <FileJson :size="16" />
          Export as JSON
        </button>
        <button class="export-button__item" @click="exportExcel">
          <FileSpreadsheet :size="16" />
          Export as Excel
        </button>
      </div>
    </Transition>
  </div>
</template>

<style scoped lang="scss">
.export-button {
  position: relative;
  display: inline-block;

  &__menu {
    position: absolute;
    top: 100%;
    right: 0;
    margin-top: 0.25rem;
    min-width: 180px;
    background: var(--popover);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    z-index: 50;
    overflow: hidden;
  }

  &__item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    width: 100%;
    padding: 0.625rem 0.875rem;
    font-size: 0.875rem;
    color: var(--foreground);
    background: transparent;
    border: none;
    cursor: pointer;
    text-align: left;
    transition: background-color 0.15s ease;

    &:hover {
      background: var(--accent);
    }

    &:not(:last-child) {
      border-bottom: 1px solid var(--border);
    }
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
