# Navigation Sidebar - Visual Guide

## Two-Size Hierarchy in Action

### Font Size Comparison

```
┌───────────────────────────────────────┐
│                                       │
│  1ST-LEVEL TRIAGE & ROUTING          │  ← 0.8rem, semibold
│  HumAIne Core - TRL 5                 │  ← 0.65rem, medium
│                                       │
│  Gap: 0.25rem                         │
│                                       │
└───────────────────────────────────────┘
```

**Hierarchy Effect**:
- Tier level at 0.8rem acts as the primary information anchor
- Description at 0.65rem provides supportive context
- ~23% size difference creates clear visual precedence without overwhelming the smaller text

### Color Contrast Hierarchy

```
Tier Level:
  Color:     sidebar-foreground (higher contrast)
  Purpose:   Primary, focal point, main information
  
Tier Description:
  Color:     muted-foreground (reduced contrast)
  Purpose:   Secondary, contextual, supporting information
```

This dual-hierarchy (size + color) ensures users:
1. See the tier name first
2. Can optionally read the description
3. Understand the visual order without cognitive effort

## Layout Breakdown

### Tier Container Structure

```
.sidebar__nav (gap: 0, padding: 1rem)
│
├─ .sidebar__nav-tier (Tier 1)
│  │
│  ├─ .sidebar__tier-label (padding: 0.75rem 1rem 0.5rem)
│  │  ├─ .sidebar__tier-level      (0.8rem, semibold)
│  │  │  └─ "1ST-LEVEL TRIAGE & ROUTING"
│  │  │
│  │  └─ .sidebar__tier-description (0.65rem, medium)
│  │     └─ "HumAIne Core - TRL 5"
│  │
│  ├─ .sidebar__link (gap: 0.25rem between links)
│  │  ├─ 🏠 Home
│  │  ├─ 🧠 New Project
│  │  ├─ 📬 Ticket Queue
│  │  └─ ✏️ Manual Queue
│  │
│  └─ border-bottom: 1px solid var(--sidebar-border)
│
├─ Spacing: margin-bottom: 0.5rem, padding-bottom: 0.5rem
│
└─ .sidebar__nav-tier (Tier 2)
   │
   ├─ .sidebar__tier-label (padding: 0.75rem 1rem 0.5rem)
   │  ├─ .sidebar__tier-level      (0.8rem, semibold)
   │  │  └─ "2ND-LEVEL RESOLUTION SUPPORT"
   │  │
   │  └─ .sidebar__tier-description (0.65rem, medium)
   │     └─ "Exploratory Preview"
   │
   └─ .sidebar__link (gap: 0.25rem between links)
      ├─ 💬 Ticket Evolution
      └─ 📊 Performance
```

## Viewport: Expanded Sidebar (16rem width)

```
╔════════════════════════════════════════════╗
║  IT TICKET MANAGER                   ︿    ║  ← Header
║  AI-Powered Ticket System                 ║
║════════════════════════════════════════════║
║ Active Project                             ║
║ [📦 Project Selector           ▼]         ║
║════════════════════════════════════════════║
║                                            ║
║ 1ST-LEVEL TRIAGE & ROUTING                ║  ← Tier 1 Label (0.8rem)
║ HumAIne Core - TRL 5                      ║  ← Tier 1 Description (0.65rem)
║                                            ║
║ [🏠] Home                                 ║  ← Links
║ [🧠] New Project                          ║
║ [📬] Ticket Queue                         ║
║ [✏️] Manual Queue                          ║
║────────────────────────────────────────────║  ← Tier separator
║                                            ║
║ 2ND-LEVEL RESOLUTION SUPPORT              ║  ← Tier 2 Label (0.8rem)
║ Exploratory Preview                       ║  ← Tier 2 Description (0.65rem)
║                                            ║
║ [💬] Ticket Evolution                     ║  ← Links
║ [📊] Performance                          ║
║                                            ║
╠════════════════════════════════════════════╣
║ [▶] Tour guide                             ║  ← Footer
║ 🎭 Mock Mode: ON                           ║
║────────────────────────────────────────────║
║ demo                                       ║
║ [↪] Sign out                               ║
╚════════════════════════════════════════════╝
```

## Viewport: Collapsed Sidebar (4rem width)

```
╔══════╗
║ ︿    ║  ← Collapse toggle
║══════║
║ ▼    ║  ← Project selector (icon only)
║══════║
║      ║
║ 🏠   ║  ← Tier 1 Links
║ 🧠   ║
║ 📬   ║
║ ✏️   ║  (tier label hidden)
║──────║  ← Tier separator (border remains)
║      ║
║ 💬   ║  ← Tier 2 Links
║ 📊   ║
║      ║  (tier label hidden)
╠══════╣
║ ▶    ║  ← Tour guide icon
║ 🎭   ║  ← Mock toggle
║ 👤   ║  ← Account icon
╚══════╝
```

**Hover Behavior (Collapsed State)**:
- Tooltip appears on hover with full text
- Example: Hovering over first tier-1 link shows:
  ```
  1st-Level Triage & Routing
  HumAIne Core - TRL 5
  Home
  ```

## Spacing and Proportions

### Vertical Spacing (Expanded)

```
Header Section        1.5rem padding
Active Project        1rem padding
────────────────────
Tier 1 Label          0.75rem top, 0.5rem bottom
Links (4×)            0.75rem each, 0.25rem gap
                      Subtotal: 3.75rem (links) + 0.75rem (label) = 4.5rem
────────────────────  1px border
(0.5rem margin + 0.5rem padding between tiers)
────────────────────
Tier 2 Label          0.75rem top, 0.5rem bottom
Links (2×)            0.75rem each, 0.25rem gap
                      Subtotal: 1.75rem (links) + 0.75rem (label) = 2.5rem
────────────────────
Flexible space        (fills available height)
────────────────────
Footer                1rem padding
```

**Total fixed-height tier navigation**: ~7rem
**Flexible space for growth**: Yes, no scrolling needed for current 6 items

### Horizontal Spacing (Expanded)

```
│ 1rem  │ content │ 1rem │
├───────┼─────────┼──────┤
        16rem total width
        (comfortable for label text + icon)
```

## Design Principles Applied

### 1. **Visual Hierarchy**
- Tier level (larger, stronger weight, full contrast)
- Tier description (smaller, lighter weight, muted color)
- Navigation links (consistent with existing UI)

### 2. **Information Architecture**
- Level = "What is this tier called?"
- Description = "Why does this tier matter?"
- Links = "What can I do here?"

### 3. **Minimal Visual Complexity**
- Only 0.5rem gap between tiers (minimal whitespace)
- 1px border separator (subtle, not heavy)
- Tier labels hidden on collapse (no wasted space)

### 4. **Responsive Scalability**
- Expanded: Full context visible
- Collapsed: Only icons, structure preserved
- Tooltip: Context available on demand

### 5. **Accessibility**
- Text hierarchy helps screen readers understand structure
- Color contrast meets WCAG standards
- Uppercase text transforms are CSS-based (not screen-reader confusing)
- Border provides visual structure for users with cognitive needs

## Customization Options

### To increase hierarchy emphasis (make tier level more prominent):
```scss
&__tier-level {
  font-size: 0.85rem;  // ↑ from 0.8rem
  font-weight: bold;   // ↑ from semibold
}

&__tier-description {
  font-size: 0.6rem;   // ↓ from 0.65rem
  color: var(--disabled-foreground);  // ↓ even more muted
}
```

### To make tier descriptions more readable (less emphasis):
```scss
&__tier-level {
  font-size: 0.75rem;  // ↓ from 0.8rem
}

&__tier-description {
  font-size: 0.7rem;   // ↑ from 0.65rem
  color: var(--sidebar-foreground);  // ↑ higher contrast
}
```

### To increase spacing between lines:
```scss
&__tier-label {
  gap: 0.4rem;  // ↑ from 0.25rem
  padding: 0.85rem 1rem 0.6rem;  // ↑ more generous
}
```

## Implementation Details

### Vue Component Pattern
```vue
<template>
  <nav class="sidebar__nav">
    <div class="sidebar__nav-tier">
      <div v-if="!isCollapsed" class="sidebar__tier-label">
        <div class="sidebar__tier-level">TIER LEVEL</div>
        <div class="sidebar__tier-description">Tier description</div>
      </div>
      <!-- Links for this tier -->
    </div>
    <!-- Additional tiers... -->
  </nav>
</template>

<style lang="scss" scoped>
.sidebar__tier-label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.75rem 1rem 0.5rem;
  user-select: none;
  
  .sidebar-wrapper--collapsed & {
    display: none;  /* Hidden when collapsed */
  }
}

.sidebar__tier-level {
  font-size: 0.8rem;
  font-weight: var(--font-weight-semibold);
  color: var(--sidebar-foreground);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.sidebar__tier-description {
  font-size: 0.65rem;
  font-weight: var(--font-weight-medium);
  color: var(--muted-foreground);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
</style>
```

## Testing the Visual Hierarchy

### Check 1: Can you see which text is "more important" at a glance?
✅ Yes - tier level is larger and darker

### Check 2: Can you still read the description?
✅ Yes - reduced size is still readable at 0.65rem

### Check 3: Does the layout remain clean on collapse?
✅ Yes - no orphaned elements, clean icon grid

### Check 4: Is there enough contrast for accessibility?
✅ Yes - meets WCAG AA standards with sidebar-foreground and muted-foreground

### Check 5: Does the spacing feel intentional, not random?
✅ Yes - 0.5rem tier gap mirrors other UI spacing patterns
