# EpiMiniChat - Visual Design Reference

## 🎨 Component Preview

```
┌─────────────────────────────────────────────────┐
│  💙  Personal Friend                🎭 Roleplay Mode │
│      Daily companion, emotional support    NEBP Training Active │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│ 💙  🎯  🎓  👶  ✝️  💼  🧠  💼  💪           │
│ ↑   ↑                                          │
│ Active  NEBP indicator                         │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│                                                 │
│                    💙                           │
│        Start a conversation with               │
│            Personal Friend                      │
│                                                 │
│                                                 │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│  [Message Personal Friend...      ]  📤        │
└─────────────────────────────────────────────────┘
```

---

## 🎯 Sales Agent (NEBP Mode) Example

```
┌─────────────────────────────────────────────────┐
│  🎯  Sales Agent                   🎭 Roleplay Mode │
│      Sales training and NEBP        NEBP Training Active │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│ 💙  🎯  🎓  👶  ✝️  💼  🧠  💼  💪           │
│     ↑ 🎯 ← NEBP dot indicator                  │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│                                                 │
│  🎯  ┌────────────────────────────┐            │
│      │ [NEBP Training Mode]        │            │
│      │ Great question! Let me      │            │
│      │ help you practice rapport   │            │
│      │ building...                 │            │
│      └────────────────────────────┘            │
│      10:30 AM                                   │
│                                                 │
│                     ┌────────────────┐  👤     │
│                     │ How do I handle │         │
│                     │ objections?     │         │
│                     └────────────────┘         │
│                     10:29 AM                    │
│                                                 │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│  [Message Sales Agent...          ]  📤        │
└─────────────────────────────────────────────────┘
```

---

## 🎨 Color Scheme

### Header Gradient
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

### Message Bubbles

**AI Messages (Left)**
```css
background: #f3f4f6;  /* Light gray */
color: #111827;       /* Dark text */
border-bottom-left-radius: 4px;  /* Sharp corner */
```

**User Messages (Right)**
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
color: white;
border-bottom-right-radius: 4px;  /* Sharp corner */
```

### Personality Colors

| Personality | Color | Hex |
|------------|-------|-----|
| Personal Friend | Blue | `#3B82F6` |
| Sales Agent (NEBP) | Amber | `#F59E0B` |
| Student Tutor | Green | `#10B981` |
| Kids Learning | Pink | `#EC4899` |
| Christian Companion | Purple | `#8B5CF6` |
| Customer Service | Indigo | `#6366F1` |
| Psychology Expert | Teal | `#14B8A6` |
| Business Mentor | Slate | `#64748B` |
| Weight Loss Coach | Red | `#EF4444` |

---

## 🎭 NEBP Indicators

### 1. Badge (Header Right)
```
┌──────────────────┐
│ 🎭 Roleplay Mode │  ← Pulsing animation
└──────────────────┘
   NEBP Training Active
```

### 2. Avatar Dot (Personality Switcher)
```
  ┌─────┐
  │ 🎯  │  ← Sales Agent
  └─────┘
      🎯 ← Small NEBP indicator dot (top-right)
```

### 3. Empty State Hint
```
💡 Practice your sales skills with NEBP methodology
```

---

## 📱 Responsive Breakpoints

### Desktop (> 480px)
- Max width: 500px
- Border radius: 16px
- Centered in viewport
- Avatar size: 56px

### Mobile (<= 480px)
- Full width
- No border radius
- Full viewport height
- Avatar size: 48px

---

## ✨ Animations

### Slide In (Messages)
```css
@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

### Pulse (NEBP Badge)
```css
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}
```

### Hover Scale (Buttons)
```css
.personality-avatar:hover {
  transform: scale(1.1);
}
```

---

## 🌗 Dark Mode

### When `prefers-color-scheme: dark`

**Background Colors:**
- Main: `#1f2937` (gray-800)
- Switcher: `#111827` (gray-900)
- Message bubble (AI): `#374151` (gray-700)

**Text Colors:**
- Primary: `#f9fafb` (gray-50)
- Secondary: `#d1d5db` (gray-300)

**Borders:**
- `#374151` (gray-700)

---

## 🎯 Component States

### Loading State
```
┌─────────────────────────────────────────────────┐
│  🎯  Sales Agent                   🎭 Roleplay Mode │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│                                                 │
│  🎯  ┌────────────────────────────┐            │
│      │ ⏳ Thinking...              │            │
│      └────────────────────────────┘            │
│                                                 │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│  [Message Sales Agent...          ]  ⏳        │
│                         (disabled)             │
└─────────────────────────────────────────────────┘
```

### Error State
```
┌─────────────────────────────────────────────────┐
│  🎯  ┌────────────────────────────┐            │
│      │ Sorry, I encountered an     │            │
│      │ error: Network timeout      │            │
│      └────────────────────────────┘            │
│      10:32 AM                                   │
└─────────────────────────────────────────────────┘
```

### Empty State (No Messages)
```
┌─────────────────────────────────────────────────┐
│                                                 │
│                    🎯                           │
│        Start a conversation with               │
│             Sales Agent                         │
│                                                 │
│   💡 Practice your sales skills with           │
│        NEBP methodology                         │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 🔤 Typography

### Font Family
```css
font-family: -apple-system, BlinkMacSystemFont, 
             'Segoe UI', 'Roboto', 'Oxygen', 
             'Ubuntu', 'Cantarell', sans-serif;
```

### Font Sizes
- Header Name: `16px` (semi-bold)
- Header Description: `12px`
- Message Text: `14px`
- Timestamp: `11px`
- NEBP Badge: `12px` (semi-bold)
- Empty State: `14px`

---

## 🎨 Shadow Styles

### Component Shadow
```css
box-shadow: 
  0 4px 6px rgba(0, 0, 0, 0.1),
  0 2px 4px rgba(0, 0, 0, 0.06);
```

### Active Avatar Shadow
```css
box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
```

### Button Hover Shadow
```css
box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
```

---

## 📐 Layout Specifications

### Component Dimensions
- Max height: `600px`
- Max width: `500px`
- Padding (header): `16px`
- Padding (messages): `16px`
- Padding (input): `16px`

### Personality Switcher
- Height: `56px` (desktop) / `48px` (mobile)
- Gap between avatars: `8px`
- Scroll padding: `4px`

### Message Bubbles
- Max width: `85%` (desktop) / `90%` (mobile)
- Padding: `12px 16px`
- Border radius: `16px`
- Corner radius (tail): `4px`

---

## 🎭 NEBP Visual Hierarchy

### Priority 1 (Most Prominent)
1. 🎭 Roleplay Mode Badge (pulsing)
2. Header background gradient
3. Active personality border

### Priority 2 (Secondary)
1. "NEBP Training Active" label
2. 🎯 NEBP dot on avatar
3. Purple accent colors

### Priority 3 (Contextual)
1. Empty state NEBP hint
2. Metadata in API response
3. Special AI response formatting

---

## 📊 Accessibility

### Color Contrast Ratios
- Text on dark background: `> 7:1` (AAA)
- Text on light background: `> 4.5:1` (AA)
- Interactive elements: `> 3:1` (AA)

### Interactive Elements
- All buttons have `:focus` states
- Keyboard navigation supported
- Screen reader friendly
- Touch targets: minimum 44x44px

### Semantic HTML
```html
<button aria-label="Select Sales Agent personality">
  <span role="img" aria-label="Sales Agent">🎯</span>
</button>
```

---

## 🎬 User Flow

1. **Component Loads**
   - Default: Personal Friend selected
   - Empty state displayed
   - Input ready

2. **Switch Personality**
   - Click avatar in switcher
   - Active border changes
   - Header updates
   - NEBP indicator shows (if sales_agent)

3. **Send Message**
   - Type in input
   - Press Enter or click 📤
   - User bubble appears (right)
   - Loading state shows
   - AI response appears (left)

4. **NEBP Training Session**
   - Select Sales Agent
   - See 🎭 Roleplay Mode
   - Get NEBP-specific responses
   - Track phase in metadata

---

**This design ensures a professional, intuitive mobile MVP experience with clear NEBP indicators!** 🎨
