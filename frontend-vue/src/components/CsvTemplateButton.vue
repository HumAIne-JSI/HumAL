<script setup lang="ts">
import Button from '@/components/ui/Button.vue'
import { Download } from 'lucide-vue-next'
import Papa from 'papaparse'

export interface CsvTemplateButtonProps {
  fields: string[]
  filename?: string
  includeExample?: boolean
}

const props = withDefaults(defineProps<CsvTemplateButtonProps>(), {
  filename: 'template',
  includeExample: true,
})

const exampleData: Record<string, string> = {
  title_anon: 'Cannot connect to VPN',
  description_anon: 'I am getting timeout errors when trying to connect to the company VPN...',
  service_name: 'IT Support',
  service_subcategory_name: 'Network',
  team_name: 'Network Operations',
  last_team_id_name: 'Helpdesk',
  public_log_anon: 'User reported issue at 10:30 AM',
}

const downloadTemplate = () => {
  // Create rows: header + optional example row
  const rows: Record<string, string>[] = []

  if (props.includeExample) {
    // Add example row with only the fields that are requested
    const exampleRow: Record<string, string> = {}
    for (const field of props.fields) {
      exampleRow[field] = exampleData[field] ?? ''
    }
    rows.push(exampleRow)
  }

  // If no example, create empty structure with headers
  const csv =
    rows.length > 0
      ? Papa.unparse(rows)
      : props.fields.join(',') + '\n'

  // Create and trigger download
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${props.filename}.csv`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
</script>

<template>
  <Button variant="ghost" size="sm" @click="downloadTemplate">
    <Download :size="14" />
    Download CSV Template
  </Button>
</template>
