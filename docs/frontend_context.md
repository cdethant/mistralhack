# UI/UX Design System: Minimalist Desktop Modern
**Goal:** Create a high-fidelity, distraction-free interface that feels native to both macOS (Aqua/Glass) and Arch Linux (Wayland/Hyprland).

## 1. Aesthetic Principles
- **Functional Minimalism:** If a pixel doesn't serve a purpose, remove it.
- **Breathable White Space:** Use generous padding (16px, 24px, 32px) to separate logic blocks.
- **Subtle Depth:** Avoid heavy shadows. Use 1px borders or very soft ambient occlusion for elevation.
- **Micro-animations:** Transitions should be <200ms and use "ease-out" or "cubic-bezier".

## 2. Visual Tokens
- **Palette (Dark Mode focus):** - Background: #0F0F0F (Deep Charcoal)
  - Surface: #1A1A1A (Slightly lighter for cards)
  - Accent: #3B82F6 (Electric Blue) or #A78BFA (Soft Violet)
  - Text: #F3F4F6 (Primary), #9CA3AF (Secondary)
- **Typography:**
  - Sans-serif stack: "Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", Roboto, sans-serif.
  - Weights: Regular (400) for body, Semi-bold (600) for headers.
- **Corner Radius:** - Buttons/Inputs: 8px
  - Containers/Modals: 12px

## 3. Component Guidelines
- **Buttons:** Ghost or Outline styles by default. Filled styles only for Primary Actions.
- **Inputs:** No background; bottom-border only or a very subtle 1px border. Glow on focus.
- **Scrollbars:** Hidden or "thin" styled to match the background (no bulky default bars).

## 4. Platform Specifics (Electron)
- **macOS:** Use `titleBarStyle: 'hiddenInset'` and ensure a 20px top-margin for traffic lights.
- **Wayland:** Use system-native font rendering. Avoid custom window decorations if the user is using a Tiling Window Manager (TWM).