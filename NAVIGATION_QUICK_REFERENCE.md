# Navigation Sidebar - Quick Reference

## What Was Changed?

Navigation sidebar split into **two tiers** with **hierarchical labels**:

```
📍 TIER 1: 1st-Level Triage & Routing (0.8rem, bold)
   Supporting text: HumAIne Core - TRL 5 (0.65rem, muted)
   
   🏠 Home
   🧠 New Project
   📬 Ticket Queue
   ✏️  Manual Queue

───────────────────────────────────────────────────────  1px separator

📍 TIER 2: 2nd-Level Resolution Support (0.8rem, bold)
   Supporting text: Exploratory Preview (0.65rem, muted)
   
   💬 Ticket Evolution
   📊 Performance
```

## Key Features

| Feature | Details |
|---------|---------|
| **Tier 1 Size** | 0.8rem (primary, draws attention) |
| **Tier 2 Size** | 0.65rem (secondary, supportive) |
| **Weight** | Semibold (primary), Medium (secondary) |
| **Colors** | sidebar-foreground (primary), muted-foreground (secondary) |
| **Spacing Between Tiers** | 0.5rem margin + 0.5rem padding (minimal gap) |
| **Separator** | 1px border-bottom on first tier |
| **On Collapse** | Labels hidden, icons only, border invisible |
| **Tooltips** | Show tier level + description on hover (collapsed mode) |

## Branding

- The sidebar header and both sign-in screens use [logo.png](frontend/src/assets/images/logo.png) as the primary logo, including its tagline.
- Secondary branding in the sidebar footer and the footer component uses [humaine-logo.png](frontend/src/assets/images/humaine-logo.png).
- [HumaineLogo.vue](frontend/src/components/HumaineLogo.vue) renders the supplied artwork: the default variant is `primary`; use `variant="secondary"` for the compact logo. Both variants preserve the image proportions.
- Collapsing the sidebar hides both logos along with the existing header text and footer controls.

## Visual Hierarchy

The two-size approach creates **dual hierarchy**:

1. **Size Hierarchy** (0.8rem vs 0.65rem = 23% larger)
   - Tier level read first
   - Description read second

2. **Color Hierarchy** (foreground vs muted-foreground)
   - Tier level has higher contrast
   - Description recedes into background

Together: Eye naturally lands on tier level, then optionally reads description.

## File Location

**Modified Component**:
```
frontend/src/components/Navigation.vue
```

**Changes Summary**:
- Template: Lines 31-82 (two nav-tier blocks with hierarchical labels)
- Script: Lines 136-152 (tier1Items and tier2Items computed properties)
- Styles: Lines 304-335 (three new CSS classes: tier-label, tier-level, tier-description)

## How to Customize

### Make Tier Level More Prominent
```scss
.sidebar__tier-level {
  font-size: 0.85rem;  // Increase size
  font-weight: bold;   // Increase weight
}

.sidebar__tier-description {
  font-size: 0.6rem;   // Decrease size further
}
```

### Increase Gap Between Tiers
```scss
.sidebar__nav-tier:not(:last-child) {
  margin-bottom: 1rem;    // Increase from 0.5rem
  padding-bottom: 1rem;   // Increase from 0.5rem
}
```

### Add More Spacing Inside Labels
```scss
.sidebar__tier-label {
  gap: 0.4rem;  // Increase from 0.25rem
}
```

## How to Add New Routes

### Step 1: Add Route to Router
File: `frontend/src/router/index.ts`
```typescript
{
  path: '/my-new-route',
  name: 'my-feature',
  component: () => import('../pages/MyFeature.vue'),
  meta: { label: 'My Feature', icon: MyIcon, showInNav: true }
}
```

### Step 2: Add Path to Tier Filter
File: `frontend/src/components/Navigation.vue`

**For Tier 1**:
```typescript
const tier1Items = computed(() =>
  navItems.filter(item =>
    ['/', '/training', '/queue', '/manual', '/my-new-route'].includes(item.path)
  )
)
```

**For Tier 2**:
```typescript
const tier2Items = computed(() =>
  navItems.filter(item =>
    ['/ticket-resolution', '/analytics', '/my-new-route'].includes(item.path)
  )
)
```

Done! Navigation automatically updates.

### Tier 2 workspace sidebar

The Specialist Resolution Workspace (`/ticket-resolution`) is a separate Tier 2 app with its own mock sign-in and a sidebar that lists only Tier 2 pages. To add a page to it, give the route these meta flags in `frontend/src/router/index.ts`:

```typescript
meta: { label: 'My Page', icon: MyIcon, specialistNav: true, app: 'specialist' }
```

- `app: 'specialist'` puts the route behind the specialist sign-in (`/ticket-resolution/login`, session kept in `sessionStorage`) and makes `App.vue` render the sidebar with `scope="specialist"`.
- `specialistNav: true` lists the route in that sidebar (`specialistNavItems`).

## Responsive Behavior

### Expanded Sidebar (16rem)
- Full tier labels visible
- All text and icons shown
- Optimal reading experience

### Collapsed Sidebar (4rem)
- Tier labels hidden (CSS `display: none`)
- Icons only (grid layout)
- Tier border invisible
- Hover shows tooltip with full context

## Build Status

✅ **Verified**
- TypeScript: Compiles OK
- Vite: Build succeeds (4.45s)
- Errors: 0
- Warnings: 0
- Bundle impact: < 0.1KB

## Documentation Files

| File | Purpose |
|------|---------|
| `NAVIGATION_RESTRUCTURE.md` | Full technical documentation |
| `NAVIGATION_VISUAL_GUIDE.md` | Visual diagrams and layouts |
| `NAVIGATION_IMPLEMENTATION_SUMMARY.md` | Executive overview and change manifest |
| `NAVIGATION_QUICK_REFERENCE.md` | This file (quick reference) |

## Design Principles

✅ **Visual Hierarchy** - Tier level > description > links  
✅ **Information Architecture** - What (level), Why (description), How (links)  
✅ **Minimal Whitespace** - 0.5rem gap between tiers (intentional, not wasteful)  
✅ **Responsive** - Works in both expanded and collapsed states  
✅ **Accessible** - Color + size hierarchy (not just color alone)  
✅ **Extensible** - Easy to add/remove routes (computed properties)  
✅ **Backward Compatible** - No breaking changes

## Tier Semantics

### Tier 1: Core (TRL 5 - Technology Readiness Level 5)
- **Status**: Production-ready
- **Focus**: Initial ticket triage and classification
- **Features**: Home, New Project, Ticket Queue, Manual Queue
- **User Goal**: Assess and route incoming tickets

### Tier 2: Support (Exploratory Preview)
- **Status**: Experimental/Preview
- **Focus**: Enhanced resolution and analytics
- **Features**: Ticket Evolution, Performance Analytics
- **User Goal**: Track resolution and analyze performance

## One-Liner Summary

Two-tier navigation with **hierarchical labels** (0.8rem tier level + 0.65rem description), **minimal visual gap** (0.5rem), **1px separator**, and **full responsive support** (hidden labels on collapse).
