# Sidebar Cropping Fixes

## Problem
The sidebar navigation text was being cropped/cut off when expanded, making labels like "Level 1: Triage & routing" and "Level 2: Resolution support" partially invisible.

## Root Causes
1. **Insufficient width**: Sidebar was set to `20rem` which wasn't enough for the content
2. **Overflow clipping**: `.sidebar { overflow: hidden; }` was cutting off content on all axes
3. **No text overflow handling**: Text elements lacked ellipsis or proper truncation styling
4. **Flex layout issues**: Missing `min-width: 0` on flex items prevented proper overflow handling

## Changes Made

### File: `frontend/src/components/Navigation.vue`

#### 1. Increased Sidebar Width (Line 204)
```scss
// Before
.sidebar-wrapper {
  width: 20rem;
}

// After
.sidebar-wrapper {
  width: 22rem;
}
```
**Reason**: The increased width provides more space for navigation labels and tier descriptions without wrapping or cropping.

#### 2. Fixed Overflow Handling (Line 218-222)
```scss
// Before
.sidebar {
  overflow: hidden;
}

// After
.sidebar {
  overflow-y: auto;
  overflow-x: hidden;
}
```
**Reason**: Split overflow to allow vertical scrolling while preventing horizontal overflow. This ensures content can scroll within bounds without being clipped.

#### 3. Added Text Overflow Handling to Tier Elements (Lines 348-366)
```scss
// Added to .sidebar__tier-text
&__tier-text {
  min-width: 0;
  overflow: hidden;
}

// Added to .sidebar__tier-level
&__tier-level {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

// Added to .sidebar__tier-description
&__tier-description {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
```
**Reason**: Ensures that if text is too long, it gets truncated with ellipsis (`...`) instead of being cropped or wrapping unexpectedly.

#### 4. Fixed Flex Layout for Links (Lines 368-395)
```scss
// Added to .sidebar__link
&__link {
  min-width: 0;
  overflow: hidden;
  
  .sidebar-wrapper--collapsed & {
    overflow: visible;
  }
}
```
**Reason**: `min-width: 0` on flex items allows them to shrink below content size. Overflow is restored to `visible` when collapsed so icon-only view isn't affected.

#### 5. Added Overflow Handling to Link Labels (Lines 397-404)
```scss
// Enhanced .sidebar__label
&__label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}
```
**Reason**: Prevents long navigation labels from causing layout issues; truncates gracefully with ellipsis if needed.

## Result
✅ Sidebar now displays fully expanded without text cropping
✅ Navigation labels are fully visible
✅ Tier descriptions display correctly
✅ Text that's too long is truncated gracefully with ellipsis
✅ Vertical scrolling works properly within the sidebar
✅ Collapsed sidebar (icon-only) remains unaffected
✅ All content maintains proper spacing and alignment

## Verification
- Built successfully with `npm run build` (5.17s, zero errors)
- Tested with both expanded and collapsed sidebar states
- Verified on localhost:5173 dashboard page
- All navigation links and labels display correctly
