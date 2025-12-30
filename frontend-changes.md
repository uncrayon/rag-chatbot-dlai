# Frontend Changes: Theme Toggle Button

## Overview
Added a dark/light theme toggle button to the RAG chatbot frontend with smooth transitions and full accessibility support.

## Changes Made

### 1. HTML Structure (`frontend/index.html`)

**Header Modifications:**
- Made the header visible (was previously hidden)
- Restructured header with flexbox layout:
  - Left side: App title "Course Materials Assistant"
  - Right side: Theme toggle button
- Added theme toggle button with:
  - Sun icon (for light theme)
  - Moon icon (for dark theme)
  - Inline SVG icons for better control and performance
  - Proper ARIA attributes for accessibility

**Key HTML Addition:**
```html
<header class="app-header">
    <div class="header-left">
        <h1>Course Materials Assistant</h1>
    </div>
    <div class="header-right">
        <button id="themeToggle" class="theme-toggle" aria-label="Toggle theme" tabindex="0" role="button">
            <!-- Sun and Moon SVG icons -->
        </button>
    </div>
</header>
```

### 2. CSS Styling (`frontend/style.css`)

**Theme Variables:**
- Added light theme color palette using `[data-theme="light"]` selector
- Light theme colors:
  - Background: `#ffffff` (white)
  - Surface: `#f8fafc` (light slate)
  - Primary: `#2563eb` (same blue as dark theme)
  - Text primary: `#0f172a` (dark)
  - Text secondary: `#475569` (medium gray)
  - Border: `#e2e8f0` (light gray)

**Smooth Transitions:**
- Added global 0.3s ease transitions for:
  - `background-color`
  - `color`
  - `border-color`
  - `box-shadow`

**Header Styling:**
- Created `.app-header` with flexbox layout
- Styled header title with proper sizing
- Added responsive header layout

**Toggle Button Styling:**
- Circular button (40px × 40px)
- Hover effect: scale(1.05) transform
- Active effect: scale(0.95) transform
- Focus ring: 3px blue ring for keyboard navigation
- Icon rotation animation (180deg) when toggling
- Icons fade in/out with opacity transitions

**Icon State Logic:**
- Dark theme: Moon icon visible, sun icon hidden
- Light theme: Sun icon visible, moon icon hidden
- Smooth rotation on theme change

### 3. JavaScript Functionality (`frontend/script.js`)

**Early Theme Initialization:**
- Added IIFE (Immediately Invoked Function Expression) to load theme before DOM
- Prevents flash of wrong theme on page load
- Reads theme from localStorage or defaults to 'dark'

**Theme Toggle Functions:**

1. **`initThemeToggle()`**
   - Sets up event listeners on the toggle button
   - Handles click events
   - Handles keyboard events (Enter and Space keys)
   - Called during DOM initialization

2. **`toggleTheme()`**
   - Switches between dark and light themes
   - Updates `data-theme` attribute on `<html>` element
   - Saves preference to localStorage
   - Updates aria-label for screen readers

**Implementation Details:**
```javascript
// Early initialization (before DOM loads)
(function initThemeEarly() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
})();

// Toggle function
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}
```

## Features Implemented

### ✓ Design & Aesthetics
- Icon-based toggle with sun/moon symbols
- Circular button matching existing design language
- Smooth 0.3s transitions between themes
- Professional light and dark color palettes
- Positioned in top-right of header

### ✓ User Experience
- Instant theme switching
- No page reload required
- Theme preference persists across sessions
- No flash of wrong theme on page load
- Visual feedback on hover and click

### ✓ Accessibility
- Full keyboard navigation support
- Tab key to focus on toggle
- Enter or Space to activate
- ARIA labels for screen readers
- 3px focus ring for visibility
- Proper button semantics with `role="button"`

### ✓ Technical Implementation
- CSS custom properties for theming
- localStorage for persistence
- Early script execution prevents flash
- Smooth CSS transitions
- Clean separation of concerns

## How to Use

### For Users:
1. **Click** the toggle button in the top-right corner to switch themes
2. **Keyboard**: Tab to the button, press Enter or Space to toggle
3. Theme preference is automatically saved and restored on next visit

### For Developers:
- Theme is controlled by `data-theme` attribute on `<html>` element
- Values: `"dark"` (default) or `"light"`
- All colors use CSS custom properties from `:root` or `[data-theme="light"]`
- Theme preference stored in localStorage under key `'theme'`

## Files Modified

1. **`frontend/index.html`**
   - Added header structure with toggle button
   - Included SVG icons for sun/moon

2. **`frontend/style.css`**
   - Added light theme variables
   - Added global smooth transitions
   - Added header and toggle button styles
   - Added icon animation styles

3. **`frontend/script.js`**
   - Added early theme initialization
   - Added theme toggle functions
   - Added keyboard event handlers

## Browser Compatibility

- Works in all modern browsers
- Uses standard CSS custom properties
- localStorage API (widely supported)
- SVG icons (universal support)
- No external dependencies

## Performance

- No impact on initial load time
- Theme applied before first paint (no flash)
- Lightweight implementation (~50 lines CSS, ~30 lines JS)
- Uses CSS transitions (GPU accelerated)
- Icons are inline SVG (no HTTP requests)

## Testing Checklist

- ✓ Toggle button visible in header
- ✓ Clicking toggles between themes
- ✓ Icons rotate and swap correctly
- ✓ Colors change smoothly (0.3s transition)
- ✓ Theme persists after page reload
- ✓ Keyboard navigation works (Tab, Enter, Space)
- ✓ Focus ring visible when tabbing
- ✓ No flash of wrong theme on load
- ✓ Works with all existing chat functionality
- ✓ Responsive on mobile devices
