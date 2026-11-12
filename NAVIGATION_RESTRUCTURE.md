# Navigation Sidebar Restructure

## Overview
The navigation sidebar has been restructured into two distinct tiers with clear visual separation and minimal gap, supporting the ticket evolution workflow from triage & routing to resolution support. Tier labels use a **two-size hierarchy** to emphasize the tier level first, with a descriptive subtitle underneath in reduced size.

## Changes Made

### 1. Template Structure (Navigation.vue)
- Divided the navigation into two `sidebar__nav-tier` containers
- Each tier displays a hierarchical label (hidden when sidebar is collapsed):
  - **Tier Level** (larger, 0.8rem): Main tier name in uppercase
  - **Tier Description** (smaller, 0.65rem): Contextual information underneath

#### Tier 1 Structure
```
1ST-LEVEL TRIAGE & ROUTING    ← 0.8rem, semibold, sidebar-foreground (higher contrast)
HumAIne Core - TRL 5          ← 0.65rem, medium, muted-foreground (recessive)
```

#### Tier 2 Structure
```
2ND-LEVEL RESOLUTION SUPPORT  ← 0.8rem, semibold, sidebar-foreground (higher contrast)
Exploratory Preview           ← 0.65rem, medium, muted-foreground (recessive)
```

### 2. Tier Organization

#### Tier 1: Core Triage & Routing (TRL 5 - Technology Readiness Level)
- Home (/)
- New Project (/training)
- Ticket Queue (/queue)
- Manual Queue (/manual)

**Purpose**: Initial ticket assessment and classification. Core features at production readiness (TRL 5).

#### Tier 2: Resolution Support (Exploratory Preview)
- Ticket Evolution (/ticket-resolution)
- Performance (/analytics)

**Purpose**: Enhanced resolution and analytics capabilities. Preview features still in exploration phase.

### 3. Script Logic (Vue 3 Composition API)
```typescript
// Split nav items into two tiers
// Tier 1: Home, New Project, Ticket Queue, Manual Queue (core triage and routing)
// Tier 2: Ticket Evolution, Performance (exploratory/resolution support)
const tier1Items = computed(() =>
  navItems.filter(item =>
    ['/', '/training', '/queue', '/manual'].includes(item.path)
  )
)

const tier2Items = computed(() =>
  navItems.filter(item =>
    ['/ticket-resolution', '/analytics'].includes(item.path)
  )
)
```

- Computed properties ensure dynamic filtering and reactive updates
- Maintains single source of truth in router configuration
- Easily extensible: add/remove routes by modifying filter arrays

### 4. Styling - Two-Level Hierarchy

#### `.sidebar__tier-label` (Container)
```scss
display: flex;
flex-direction: column;
gap: 0.25rem;
padding: 0.75rem 1rem 0.5rem;
user-select: none;
```
- Stacks level and description vertically
- Minimal gap (0.25rem) between the two text lines
- Adequate padding for readability
- Hidden when sidebar is collapsed

#### `.sidebar__tier-level` (Primary/Tier Name)
```scss
font-size: 0.8rem;          ← Larger, draws attention first
font-weight: semibold;      ← Stronger visual weight
color: sidebar-foreground;  ← Higher contrast with background
text-transform: uppercase;
letter-spacing: 0.05em;
```
- **Visual Purpose**: Main anchor point; users see this first
- Size and weight create visual hierarchy
- Foreground color ensures readability

#### `.sidebar__tier-description` (Secondary/Context)
```scss
font-size: 0.65rem;           ← Smaller, subordinate
font-weight: medium;          ← Lighter than level
color: muted-foreground;      ← Lower contrast, recessive
text-transform: uppercase;
letter-spacing: 0.05em;
```
- **Visual Purpose**: Provides context without competing for attention
- Reduced size and muted color keeps focus on tier level
- Maintains visual hierarchy and information flow

### 5. Tier Separation Styling

#### `.sidebar__nav-tier` (Tier Container)
```scss
display: flex;
flex-direction: column;
gap: 0.25rem;                    ← Minimal spacing between links

&:not(:last-child) {
  margin-bottom: 0.5rem;         ← Breathing room between tiers
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--sidebar-border);  ← Clear separator
}
```
- Creates vertical separation without excessive whitespace
- Border serves as visual divider between tiers
- 0.5rem spacing combines margin and padding for optimal visual weight

### 6. Responsive Behavior
- **Expanded Sidebar (16rem)**: Full tier labels and descriptions visible
- **Collapsed Sidebar (4rem)**: 
  - Tier labels hidden (`display: none`)
  - Navigation links show only icons, stacked vertically
  - Tier structure preserved invisibly via CSS
  - Tier border separator remains invisible

## Visual Comparison

### Expanded Sidebar (16rem)
```
┌──────────────────────────────────────┐
│ 1ST-LEVEL TRIAGE & ROUTING           │
│ HumAIne Core - TRL 5                 │
├──────────────────────────────────────┤
│ 🏠 Home                              │
│ 🧠 New Project                       │
│ 📬 Ticket Queue                      │
│ ✏️  Manual Queue                      │
├──────────────────────────────────────┤
│ 2ND-LEVEL RESOLUTION SUPPORT         │
│ Exploratory Preview                  │
├──────────────────────────────────────┤
│ 💬 Ticket Evolution                  │
│ 📊 Performance                       │
└──────────────────────────────────────┘
```

**Hierarchy Effect**:
- Tier level (larger text) catches the eye first
- Tier description (smaller text) provides context after
- Clear visual separation between tiers
- Minimal vertical gap preserves screen real estate

### Collapsed Sidebar (4rem)
```
┌────┐
│ 🏠 │
│ 🧠 │
│ 📬 │
│ ✏️  │
├────┤
│ 💬 │
│ 📊 │
└────┘
```

- Icons only (no text labels)
- Tier border separator invisible but maintains structure
- Tooltip on hover shows full tier name + description
- Compact, clean appearance

## Technical Details

**Files Modified**:
- `frontend/src/components/Navigation.vue`
  - Template: Split navigation into two `sidebar__nav-tier` blocks with hierarchical labels
  - Script: Added `tier1Items` and `tier2Items` computed properties
  - Styles: Added `&__tier-label`, `&__tier-level`, and `&__tier-description` rules

**CSS Class Structure**:
```
.sidebar__nav
├── .sidebar__nav-tier (Tier 1)
│   ├── .sidebar__tier-label
│   │   ├── .sidebar__tier-level
│   │   └── .sidebar__tier-description
│   ├── .sidebar__link × 4
├── .sidebar__nav-tier (Tier 2)
│   ├── .sidebar__tier-label
│   │   ├── .sidebar__tier-level
│   │   └── .sidebar__tier-description
│   ├── .sidebar__link × 2
```

**Font Size Ratio** (creates visual hierarchy):
- Tier level: 0.8rem
- Tier description: 0.65rem
- Link label: 0.875rem
- Ratio: 0.8:0.65 = 1.23× larger (~23% size increase)

**Color Contrast** (supports visual hierarchy):
- Tier level: sidebar-foreground (primary)
- Tier description: muted-foreground (reduced)
- Creates recessive effect for description

**Backward Compatibility**: ✅ Yes
- Existing router configuration unchanged
- CSS class structure extended, not modified
- All existing functionality preserved
- Responsive collapse behavior maintained
- No breaking changes to component API

**Build Status**: ✅ Passed
- Vue 3 type checking: OK
- Vite build: OK (0 errors)
- All assets compiled successfully

## Future Extensibility

### To add new routes to either tier:
1. Add the route to `src/router/index.ts`
2. Add the route path to the corresponding tier array:
   ```typescript
   const tier1Items = computed(() =>
     navItems.filter(item =>
       ['/', '/training', '/queue', '/manual', '/new-route'].includes(item.path)
     )
   )
   ```
3. Navigation automatically updates

### To customize tier label styling:
- Adjust `.sidebar__tier-level` for tier name appearance
- Adjust `.sidebar__tier-description` for description appearance
- Modify font sizes, weights, and colors as needed
- No layout structure changes required

### To adjust tier hierarchy emphasis:
- Increase `.sidebar__tier-level` font size (e.g., 0.85rem) for more prominence
- Decrease `.sidebar__tier-description` font size (e.g., 0.6rem) for more subtlety
- Adjust `gap: 0.25rem` in `sidebar__tier-label` for more/less spacing

## Design Rationale

The two-size hierarchy in tier labels serves multiple purposes:

1. **Information Architecture**: Tier level (what it is) is primary; description (why it matters) is secondary
2. **Cognitive Load**: Users scan tier level first, then optionally read description
3. **Space Efficiency**: Stacked text uses minimal horizontal space while remaining scannable
4. **Visual Consistency**: Matches existing UI patterns (header/subtitle, title/caption)
5. **Accessibility**: Hierarchy helps users with cognitive or vision needs navigate more easily
6. **Responsive**: Scales gracefully to collapsed state without losing information structure
