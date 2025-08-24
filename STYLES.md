## Purpose

This document captures the visual design tokens and common patterns used in the frontend (`/frontend`) so contributors have a single, small reference for colors, typography, and component conventions.

## Quick checklist

- Inspect Tailwind tokens in `tailwind.config.js` — Done
- Extract primary color palette and dark (UI) palette — Done
- Capture typography and commonly used utility classes — Done
- Add short notes on component patterns and accessibility — Done

## Where this info came from

- `frontend/tailwind.config.js` — primary and dark color scales and the `mono` font family.
- `frontend/src/components/MessageComponents.tsx` and `frontend/src/App.tsx` — real usage examples (message bubbles, headers, code blocks, badges).
- `frontend/src/main.tsx` — imports `index.css` (verify presence when working locally).

If you want a deeper visual audit (fonts, exported assets, or a color contrast report) I can run that next.

## Color palette (tokens)

Use Tailwind token names from `tailwind.config.js` in classes like `bg-primary-500`, `text-dark-900`, etc.

- Primary (green scale)
	- primary-50:  #f0fdf4
	- primary-100: #dcfce7
	- primary-200: #bbf7d0
	- primary-300: #86efac
	- primary-400: #4ade80
	- primary-500: #22c55e (brand / primary action)
	- primary-600: #16a34a
	- primary-700: #15803d
	- primary-800: #166534
	- primary-900: #14532d
	- primary-950: #052e16

- Dark / UI neutrals (used for backgrounds, panels, borders)
	- dark-50:  #f8fafc
	- dark-100: #f1f5f9
	- dark-200: #e2e8f0
	- dark-300: #cbd5e1
	- dark-400: #94a3b8
	- dark-500: #64748b
	- dark-600: #475569
	- dark-700: #334155
	- dark-800: #1e293b
	- dark-900: #0f172a (app background)
	- dark-950: #020617

Notes:
- Use `primary-500` for primary buttons, active states, and prominent badges.
- Use `dark-900` / `dark-800` for app backgrounds and high-contrast panels; lighter `dark-*` steps are used for borders, muted text, and subtle UI surfaces.

## Typography

- Monospaced stack: `font-mono` is defined as: `JetBrains Mono`, `Fira Code`, `Consolas`, `monospace` (used for inline code, argument blocks and function names).
- The app relies primarily on Tailwind's default sans-serif stack for UI copy (no custom `sans` family defined in config).
- Common utility classes seen in the codebase:
	- `text-sm`, `text-xs`, `text-xl`, `text-xl font-bold` — for headings, metadata and small helper text
	- `leading-relaxed` — body line-height for message content
	- `font-medium`, `font-bold` — for emphasis in message headers and badges

Recommendations:
- Keep body copy at least `text-sm` (14px) for small UI text and `text-base` (16px) for primary reading areas.
- Use `font-mono` for code and terminal-like outputs; prefer `text-xs` or `text-sm` for preformatted code blocks with `overflow-x-auto`.

## Common utilities & component tokens

Below are patterns recurring across `App.tsx` and `MessageComponents.tsx` and suggested tokenized usage.

- App background / shell
	- container: `min-h-screen bg-dark-900 text-gray-100` (dark background with near-white text)
	- header: `bg-gray-900 border-b border-gray-800 p-4`

- Badges / status
	- connected: `bg-green-600` (used for small icon background)
	- status dot classes: `w-2 h-2 rounded-full bg-green-500` or `bg-red-500` for error

- Message bubbles and cards
	- agent success/response: `bg-green-900/20 border border-green-700/50 rounded-lg p-4`
	- function-call: `bg-blue-900/20 border border-blue-700/50 rounded-lg p-4`
	- content text: `text-gray-200` or `text-green-100` inside panels

- Code and pre blocks
	- inline code: `bg-gray-800 px-1 py-0.5 rounded text-green-300 text-sm`
	- code blocks: `bg-gray-800 rounded-lg p-4 border border-gray-700 overflow-x-auto`

- Tables / lists / blockquote inside message content (Markdown)
	- tables: `min-w-full border-collapse border border-gray-700`
	- th: `bg-gray-800 text-green-400 font-medium`
	- blockquote: `border-l-4 border-green-500 pl-4 italic text-gray-300 bg-gray-800 py-2 rounded-r`

## Spacing and radii

- Reused spacing classes observed:
	- padding: `p-2`, `p-4` for card content; `pb-32` for chat bottom spacing
	- rounded corners: `rounded`, `rounded-lg`, `rounded-full` for icons

Guideline: prefer the existing Tailwind spacing scale. Use `rounded-lg` for cards and `rounded`/`rounded-full` for small UI elements and avatars.

## Accessibility notes

- Contrast: the app uses a dark theme. When adding new colors, ensure text over background meets WCAG AA where it matters (buttons, labels). Use `primary-500` on light backgrounds or `primary-600`/`primary-700` for small text on dark backgrounds.
- Focus states: ensure interactive elements get visible focus rings. Prefer `focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-400` or similar.
- Motion: streaming UI (typing/streaming indicators) should respect reduced-motion preferences where possible.

## Component examples (token -> class examples)

- Primary button (solid): `bg-primary-500 hover:bg-primary-600 text-white rounded-md px-4 py-2`
- Secondary button (outline / neutral): `border border-dark-700 text-gray-100 bg-transparent rounded-md px-3 py-2`
- Code block: `bg-gray-800 rounded-lg p-4 border border-gray-700 overflow-x-auto font-mono text-sm`

## Notes for contributors

- Prefer Tailwind utility classes and the tokens defined in `tailwind.config.js` (e.g. `primary-500`, `dark-900`).
- When introducing new color roles, add them to `tailwind.config.js` so they become reusable tokens across the app.
- The app imports `./index.css` in `frontend/src/main.tsx` — verify `index.css` locally if you plan to add global styles.

## Next steps (optional)

- Run a contrast audit and list any low-contrast combinations.
- Add a small visual token file or a tiny Storybook/Vite page showing the palettes and components.

---
