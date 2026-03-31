import { ref } from 'vue'
import type { QueueTicket, TicketStatus } from '@/stores/useTicketQueueStore'

// Flag to enable mock data (can be toggled in dev mode)
export const useMockData = ref(import.meta.env.DEV && !import.meta.env.VITE_USE_REAL_API)

export function setUseMockData(enabled: boolean) {
  useMockData.value = enabled
}

// Sample data for realistic mock tickets
const SAMPLE_TITLES = [
  'Unable to connect to VPN from home office',
  'Outlook keeps crashing when opening attachments',
  'Request for new laptop - current one too slow',
  'Password reset needed for SAP system',
  'Printer on 3rd floor not working',
  'Need access to SharePoint project folder',
  'Software installation request: Visual Studio Code',
  'Email not syncing on mobile device',
  'Computer running very slow after Windows update',
  'Cannot access network drive Z:',
  'Monitor flickering intermittently',
  'Request for additional RAM upgrade',
  'Teams meeting audio not working',
  'Need to recover deleted files from last week',
  'New employee onboarding - IT setup required',
  'Zoom integration with Outlook calendar failing',
  'Two-factor authentication app not receiving codes',
  'WiFi connection dropping frequently',
  'Adobe Creative Suite license expiring',
  'Request for external hard drive for backups',
]

const SAMPLE_DESCRIPTIONS = [
  'Since this morning, I have been unable to establish a VPN connection. The client shows "connecting" but times out after 30 seconds. I have tried restarting my router and computer.',
  'Every time I try to open a PDF or Word attachment in Outlook, the application freezes and then crashes. This started after the latest Microsoft update.',
  'My current laptop is 5 years old and struggles to run the necessary applications for my work. Requesting approval for a new device.',
  'I have forgotten my SAP password and need it reset. The self-service portal is not accepting my security questions.',
  'The HP LaserJet on the 3rd floor near conference room A is showing a paper jam error but there is no visible jam.',
  'I need read/write access to the Marketing 2024 folder on SharePoint for the upcoming campaign work.',
  'Please install Visual Studio Code on my workstation for development work. Manager approval already obtained.',
  'My company email is not syncing to my iPhone since yesterday. I have tried removing and re-adding the account.',
  'After the recent Windows update (KB5012170), my computer takes 5+ minutes to boot and applications are very slow.',
  'I am getting "network path not found" when trying to access the Z: drive. Other colleagues can access it fine.',
  'My Dell monitor screen flickers every few minutes. It seems worse when the room is warm.',
  'Current 8GB RAM is insufficient for running multiple VMs. Requesting upgrade to 32GB.',
  'In Teams meetings, others cannot hear me. I have checked microphone settings and it appears to be working in the test.',
  'I accidentally deleted some important Excel files from my Documents folder last Thursday. Can these be recovered?',
  'New hire starting Monday needs full IT setup: laptop, email, badges, and software access.',
  'Calendar events created in Zoom do not appear in Outlook, and vice versa. Integration seems broken.',
  'Microsoft Authenticator stopped showing verification codes. Have tried reinstalling the app.',
  'WiFi keeps disconnecting every 15-20 minutes requiring me to reconnect. Using Windows 11.',
  'Our Adobe CC team license expires next month. Please initiate renewal process.',
  'Need a portable external drive for taking large project files to client meetings.',
]

const TEAMS = [
  'Desktop Support',
  'Network Team',
  'Security',
  'Application Support',
  'Infrastructure',
  'Help Desk L1',
  'Help Desk L2',
]

const CATEGORIES = ['Hardware', 'Software', 'Network', 'Access', 'Email', 'Security']

const STATUSES: TicketStatus[] = ['unlabeled', 'pending-review', 'auto-classified', 'resolved']

function randomFromArray<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)] as T
}

function randomConfidence(): number {
  // Generate confidence with bias toward middle values
  const base = Math.random()
  // Apply curve to get more realistic distribution
  return Math.round((0.3 + base * 0.65) * 100) / 100
}

function randomDate(daysBack: number = 30): Date {
  const now = new Date()
  const pastDate = new Date(now.getTime() - Math.random() * daysBack * 24 * 60 * 60 * 1000)
  return pastDate
}

function generateTicketId(): string {
  return `TKT-${Math.floor(10000 + Math.random() * 90000)}`
}

/**
 * Generate a single mock ticket
 */
export function generateMockTicket(overrides?: Partial<QueueTicket>): QueueTicket {
  const id = generateTicketId()
  const titleIndex = Math.floor(Math.random() * SAMPLE_TITLES.length)
  const status = randomFromArray(STATUSES)
  const confidence = status === 'unlabeled' ? undefined : randomConfidence()
  const team = status === 'resolved' || status === 'auto-classified' ? randomFromArray(TEAMS) : undefined

  return {
    id,
    ref: id,
    title: SAMPLE_TITLES[titleIndex] ?? 'Untitled Ticket',
    description: SAMPLE_DESCRIPTIONS[titleIndex % SAMPLE_DESCRIPTIONS.length] ?? '',
    team,
    category: randomFromArray(CATEGORIES),
    status,
    confidence,
    prediction: confidence ? randomFromArray(TEAMS) : undefined,
    timestamp: randomDate(),
    originalData: {
      Ref: id,
      Title_anon: SAMPLE_TITLES[titleIndex],
      Description_anon: SAMPLE_DESCRIPTIONS[titleIndex % SAMPLE_DESCRIPTIONS.length],
      'Team->Name': team,
    },
    ...overrides,
  }
}

/**
 * Generate a batch of mock tickets with realistic distribution
 */
export function generateMockTickets(count: number = 50): QueueTicket[] {
  const tickets: QueueTicket[] = []

  // Distribution: 40% unlabeled, 25% pending-review, 20% auto-classified, 15% resolved
  const distribution: { status: TicketStatus; weight: number }[] = [
    { status: 'unlabeled', weight: 0.4 },
    { status: 'pending-review', weight: 0.25 },
    { status: 'auto-classified', weight: 0.2 },
    { status: 'resolved', weight: 0.15 },
  ]

  for (let i = 0; i < count; i++) {
    // Weighted random status selection
    const rand = Math.random()
    let cumulative = 0
    let selectedStatus: TicketStatus = 'unlabeled'

    for (const { status, weight } of distribution) {
      cumulative += weight
      if (rand < cumulative) {
        selectedStatus = status
        break
      }
    }

    const titleIndex = i % SAMPLE_TITLES.length
    const confidence = selectedStatus === 'unlabeled' ? undefined : randomConfidence()
    const team = selectedStatus === 'resolved' || selectedStatus === 'auto-classified' 
      ? randomFromArray(TEAMS) 
      : undefined

    tickets.push({
      id: generateTicketId(),
      ref: `TKT-${10000 + i}`,
      title: SAMPLE_TITLES[titleIndex] ?? 'Untitled Ticket',
      description: SAMPLE_DESCRIPTIONS[titleIndex % SAMPLE_DESCRIPTIONS.length] ?? '',
      team,
      category: randomFromArray(CATEGORIES),
      status: selectedStatus,
      confidence,
      prediction: confidence ? randomFromArray(TEAMS) : undefined,
      timestamp: randomDate(),
      originalData: {
        Ref: `TKT-${10000 + i}`,
        Title_anon: SAMPLE_TITLES[titleIndex],
        Description_anon: SAMPLE_DESCRIPTIONS[titleIndex % SAMPLE_DESCRIPTIONS.length],
        'Team->Name': team,
      },
    })
  }

  // Sort by timestamp (newest first) by default
  tickets.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())

  return tickets
}

/**
 * Get mock teams list
 */
export function getMockTeams(): string[] {
  return [...TEAMS]
}

/**
 * Get mock categories list
 */
export function getMockCategories(): string[] {
  return [...CATEGORIES]
}
