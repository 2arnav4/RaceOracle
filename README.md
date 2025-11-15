# Race Oracle – F1 Telemetry Dashboard

A modern, competitive race simulation dashboard built with React + Vite and pure CSS.

## Features

- **3-panel responsive layout**: Sidebar + Race Visualizer + Leaderboard & Telemetry
- **Race Visualizer**: SVG track with animated agent markers, zoom/pan controls
- **Live Leaderboard**: F1-style table with position, lap times, speed, and status
- **Telemetry Panel**: Status bars, speed graph, and event log
- **Scenario Config Modal**: Pre-sim configuration for track and agents
- **Pure CSS**: No Tailwind – component-level `.css` files with CSS variables
- **Glassmorphism**: Frosted glass panels with blur and transparency
- **Dark Mode Only**: Sleek, futuristic racing UI aesthetic

## Tech Stack

- **React 18** – UI library
- **Vite** – build tool & dev server
- **lucide-react** – modern icon set
- **Pure CSS** – no frameworks, using CSS variables & animations

## Project Structure

```
src/
├── components/
│   ├── AppLayout/          # Main layout grid
│   ├── Sidebar/            # Collapsible nav
│   ├── RaceVisualizer/     # SVG track & agents
│   ├── Leaderboard/        # F1 table
│   ├── TelemetryPanel/     # Tabs, bars, events
│   └── ScenarioConfigModal/# Pre-sim config
├── styles/
│   ├── variables.css       # CSS variables & theme
│   └── globals.css         # Global styles & animations
├── App.jsx                 # Root component
├── App.css                 # App entry styles
└── main.jsx                # React entry point
```

## Getting Started

### Install dependencies

```bash
npm install
```

### Run dev server

```bash
npm run dev
```

Opens automatically at `http://localhost:5173`

### Build for production

```bash
npm run build
```

Preview build:

```bash
npm run preview
```

## Customization

All colors and spacing use CSS variables defined in `src/styles/variables.css`:

```css
:root {
  --bg-main: #0d0f14;
  --accent-primary: #00FFD1;
  --accent-warning: #FFB400;
  /* ...and more */
}
```

Modify these to change the entire theme instantly across all components.

## Components Overview

### Sidebar
- Icon nav with collapse state
- Tooltip on hover (collapsed mode)
- Frosted glass style

### RaceVisualizer
- SVG track polygon with agents
- Smooth agent motion (requestAnimationFrame)
- Zoom/pan controls

### Leaderboard
- Sorted agent list by lap & time
- Alternating row colors
- Position badges with glow

### TelemetryPanel
- **Status Tab**: Battery, engine temp, tire wear bars + metrics
- **Speed Tab**: Line graph (placeholder SVG)
- **Events Tab**: Terminal-like event log

### ScenarioConfigModal
- Track selection
- Editable agent list (name, strategy)
- Blurred backdrop, glowing start button

## Animations & Interactions

- **Hover glow**: Drop-shadow filter on buttons & icons
- **Slide transitions**: Sidebar collapse, modal fade
- **Rank bump**: Leaderboard position changes animate
- **Shimmer**: Loading skeleton effect
- **Smooth bars**: Animated fill widths

## Mock Data

All components are wired with mock state and placeholder data:
- Example agents with ID, position, heading, speed, lap data
- Mock telemetry (battery, temp, wear)
- Event log entries

Agents animate continuously for demo purposes.

## Notes

- **No external frameworks**: Pure CSS only – no Tailwind, Bootstrap, etc.
- **Responsive**: Adapts from laptop (13") to tablet/mobile layouts
- **Accessible**: Semantic HTML, focus states, proper contrast
- **Modular**: Each component is independent and reusable
- **Easy to extend**: Add new panels, modify colors, tweak animations via CSS vars

---

Built with ❤️ for racing fans and AI enthusiasts. Let's go racing! 🏎️⚡
