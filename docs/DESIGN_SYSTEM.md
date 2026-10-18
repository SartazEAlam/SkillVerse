# Design System — SkillVerse

This document defines the visual direction, component conventions and interaction principles for SkillVerse. **Phase 0 defines principles and direction only.** Final design tokens (exact color values, spacing scales, font sizes) will be implemented in Phase 1.

---

## Visual Direction

SkillVerse should feel **immersive, focused and premium** — a workspace for learning, not a content catalog.

### Core Aesthetic
- **Dark foundation:** A deep, muted dark background as the primary surface. This reduces eye strain during long learning sessions and makes interactive elements stand out.
- **Strategic color accents:** Violet and cyan as primary accent colors, used sparingly to guide attention — highlights, active states, progress indicators and interactive affordances.
- **Clean spatial hierarchy:** Generous whitespace, clear content regions and consistent alignment. Every element earns its place.
- **Typography-driven:** Strong typographic hierarchy makes content scannable and readable. The text is the product.

### What to Avoid
- Generic template-style dashboards with grids of identical cards.
- Excessive glassmorphism or blur effects that reduce readability.
- Unnecessary 3D effects or heavy visual decoration.
- Animations that interrupt or delay the learning experience.
- Overly busy layouts that compete with lesson content for attention.

### Theme Strategy & Light Theme Guidance
- **Dark-Theme-First Foundation (Phase 1):** SkillVerse launches with an immersive, dark-first interface as the primary workspace aesthetic. Dark theme is prioritized to minimize eye strain during long interactive study and coding sessions, establish a modern developer/creator atmosphere, and maximize contrast for syntax-highlighted code editors and canvas visualizations.
- **Light Theme Support Planned (Phase 6+):** A light theme is **planned** for Phase 6 alongside learner personalization and accessibility settings (`PATCH /api/v1/users/me/preferences` with `{"theme": "light"}`). It is not discarded or excluded.
- **Architectural Implementation Guardrails:**
  - All styles and UI components created in Phase 1 must strictly reference semantic design tokens and CSS variables (e.g., `bg-background-base`, `text-text-primary`, `border-border-subtle`, `bg-accent-primary`) mapped via Tailwind CSS.
  - Hardcoding hex values or dark-specific utility classes (e.g., `bg-slate-900`, `text-white`) inside individual React components is strictly prohibited.
  - When light theme is activated in Phase 6, it will be achieved cleanly by overriding CSS variable values under a `[data-theme="light"]` selector without requiring component rewrites.

---

## Color Principles

### Implemented Design Tokens (Phase 1)

All components in SkillVerse reference semantic design tokens configured via Tailwind CSS v4 and CSS variables in `src/index.css`:

| CSS Variable | Tailwind Token | Dark Theme Value (Phase 1) | Light Theme Value (Phase 6) | Purpose |
|---|---|---|---|---|
| `--bg-base` | `bg-bg-base` | `#0B0F17` | `#F8FAFC` | Primary viewport surface |
| `--bg-elevated` | `bg-bg-elevated` | `#111726` | `#FFFFFF` | Sidebar, dialog modals, elevated cards |
| `--bg-surface` | `bg-bg-surface` | `#172033` | `#F1F5F9` | Interactive chips, inner panels, table rows |
| `--bg-inset` | `bg-bg-inset` | `#070A10` | `#E2E8F0` | Input controls, progress tracks, code areas |
| `--text-primary` | `text-text-primary` | `#F8FAFC` | `#0F172A` | Page titles, card headers, high-contrast labels |
| `--text-secondary` | `text-text-secondary` | `#94A3B8` | `#475569` | Body text, chapter outlines, descriptions |
| `--text-muted` | `text-text-muted` | `#64748B` | `#94A3B8` | Timestamps, lesson indices, mono metadata |
| `--border-subtle` | `border-border-subtle` | `rgba(255, 255, 255, 0.08)` | `rgba(0, 0, 0, 0.08)` | Section boundaries, card outlines |
| `--border-medium` | `border-border-medium` | `rgba(255, 255, 255, 0.16)` | `rgba(0, 0, 0, 0.16)` | Hover borders, active cards, modal dividers |
| `--border-focus` | `border-border-focus` | `#8B5CF6` | `#7C3AED` | Keyboard focus indicator outline |
| `--accent-violet` | `text-accent-violet`, `bg-accent-violet` | `#8B5CF6` | `#7C3AED` | Primary brand accent, primary CTA buttons |
| `--accent-violet-glow`| `shadow-accent-violet` | `rgba(139, 92, 246, 0.25)` | `rgba(124, 58, 237, 0.2)` | Interactive button & node elevation glow |
| `--accent-cyan` | `text-accent-cyan`, `bg-accent-cyan` | `#06B6D4` | `#0891B2` | Secondary accent, progress bars, active highlights |
| `--state-success` | `text-state-success`, `bg-state-success` | `#10B981` | `#059669` | Passed exercises, foundational mastery, streak dots |
| `--state-warning` | `text-state-warning`, `bg-state-warning` | `#F59E0B` | `#D97706` | Goal streaks, checkpoint quizzes |
| `--state-error` | `text-state-error`, `bg-state-error` | `#EF4444` | `#DC2626` | Validation errors, failed checks |

**Principle:** Colors serve functional roles. Every color in the system has a defined purpose. Decorative color without semantic meaning is avoided.

### Contrast Requirements
- All text meets WCAG 2.1 AA contrast ratios (4.5:1 for body text, 3:1 for large text and UI components).
- Interactive elements feature a visible focus indicator ring (`focus-visible:ring-2 focus-visible:ring-accent-violet`).

---

## Typography Principles

### Font Selection Direction
- **Headings:** A modern, slightly geometric sans-serif (candidates: Inter, Outfit, or similar).
- **Body text:** The same family or a highly readable companion at regular weight.
- **Code:** A monospace font optimized for code readability (candidates: JetBrains Mono, Fira Code).

### Hierarchy
- Clear size differentiation between heading levels (at least 1.2× ratio between adjacent levels).
- Body text sized for extended reading comfort (16px minimum on desktop, 15px minimum on mobile).
- Line height: 1.5–1.7 for body text, 1.2–1.3 for headings.
- Limit to 2–3 font weights to maintain visual consistency.

### Conventions
- Headings: Sentence case (not ALL CAPS, not Title Case everywhere).
- Labels and buttons: Sentence case.
- Code and technical terms: Monospace inline.

---

## Spacing and Layout Rules

### Spacing Scale
Use a consistent spacing scale based on a 4px base unit:
- `xs`: 4px — tight spacing within compact components.
- `sm`: 8px — default gap between related elements.
- `md`: 16px — section padding, form field spacing.
- `lg`: 24px — between distinct content sections.
- `xl`: 32px — major section separation.
- `2xl`: 48px — page-level spacing.
- `3xl`: 64px — hero sections, major visual breaks.

### Layout
- **Content width:** Maximum ~1200px for lesson content. Full-width for workspace layouts (code editor + preview).
- **Sidebar:** Collapsible navigation sidebar, ~260px when expanded.
- **Responsive breakpoints:**
  - Mobile: 360px–767px
  - Tablet: 768px–1023px
  - Desktop: 1024px+
  - Wide: 1440px+

### Grid
- Use CSS Grid for page layouts.
- Use Flexbox for component-level alignment.
- Lesson content uses a single-column layout for readability (max ~720px content width).
- Workspace layouts (code editor) use split-pane arrangements.

---

## Component Conventions

### General Principles
1. **Composition over configuration:** Build complex UI by composing simple, focused components rather than creating monolithic components with many props.
2. **Accessible by default:** Use Radix UI primitives for interactive components (dialogs, dropdowns, tabs, tooltips). These handle ARIA attributes, keyboard navigation and focus management.
3. **Consistent API patterns:** Components follow consistent prop naming (`variant`, `size`, `disabled`, `className`).
4. **No inline styles:** All styling through Tailwind utility classes and CSS custom properties.

### Component Categories

| Category | Examples | Approach |
|---|---|---|
| **Primitives** | Button, Input, Badge, Avatar | shadcn/ui + Radix UI, customized to design system |
| **Layout** | Shell, Sidebar, Header, ContentArea | Custom components using CSS Grid/Flexbox |
| **Navigation** | NavMenu, Breadcrumb, CourseNav | Radix NavigationMenu + custom structure |
| **Content** | LessonBlock, CodeExample, Callout | Domain-specific, render from JSON block data |
| **Activities** | CodeEditor, QuizForm, ConversationPanel | Complex workspace components per activity type |
| **Data Display** | ProgressBar, SkillRadar, MasteryBadge | Domain-specific visualization components |
| **Feedback** | Toast, Alert, HintPanel | Notification and guidance components |

### Interactive States
Every interactive element must define these states:
- **Default** — base appearance.
- **Hover** — subtle visual change (background shift, underline, shadow).
- **Focus** — visible focus ring (keyboard navigation).
- **Active/Pressed** — brief press feedback.
- **Disabled** — reduced opacity, no pointer events.
- **Loading** — spinner or skeleton, preserving layout dimensions.

---

## Motion Principles

### Philosophy
Animation serves **function**, not decoration. Every animation must answer: "What does this help the learner understand?"

### Appropriate Uses
- **Transitions between views:** Smooth crossfade or slide when navigating between lessons.
- **State changes:** Progress bars filling, checkmarks appearing on completion.
- **Reveal:** Content appearing as you scroll or expand sections.
- **Feedback:** Shake on validation error, bounce on success.
- **Orientation:** Sidebar expanding/collapsing to show layout change.

### Duration Guidelines
| Motion Type | Duration | Easing |
|---|---|---|
| Micro-interactions (button hover, toggle) | 100–150ms | ease-out |
| State transitions (expand, reveal) | 200–300ms | ease-in-out |
| View transitions (page, panel) | 300–400ms | ease-in-out |
| Complex sequences (skill map, onboarding) | 400–600ms | custom spring |

### Constraints
- **Never block interaction** with an animation. Learners must be able to click through transitions.
- **Respect `prefers-reduced-motion`.** When the OS or browser signals reduced motion preference:
  - Remove all non-essential animations.
  - Replace transitions with instant state changes.
  - Keep only critical feedback indicators (loading spinners).
- **No parallax** on lesson content pages.
- **No auto-playing animations** that distract from reading.

---

## Responsive Behavior

### Mobile (360px–767px)
- Single-column layout.
- Bottom navigation bar for primary navigation.
- Full-screen modals instead of sidebars.
- Stacked workspace panels (editor above preview).
- Touch-friendly tap targets (minimum 44×44px).

### Tablet (768px–1023px)
- Optional sidebar (collapsed by default, overlay on toggle).
- Side-by-side workspace panels when landscape.
- Adjusted typography scale.

### Desktop (1024px+)
- Persistent sidebar navigation.
- Side-by-side workspace panels.
- Full interaction patterns (hover states, tooltips).

### Principles
- **Content first.** Responsive design serves readability and usability, not layout symmetry.
- **Progressive enhancement.** Start with the mobile layout and add complexity for larger screens.
- **No horizontal scrolling** except in code blocks and tables.

---

## Accessibility Requirements

### WCAG 2.1 AA Compliance
- **Perceivable:** All content accessible to screen readers. Images have alt text. Videos have captions (when added).
- **Operable:** Full keyboard navigation. No keyboard traps. All interactive elements focusable.
- **Understandable:** Clear labels, instructions and error messages. Consistent navigation.
- **Robust:** Semantic HTML. Proper heading hierarchy. ARIA attributes where needed.

### Specific Requirements
1. **Focus management:** When views change (lesson navigation, activity completion), focus moves to the new content area.
2. **Skip links:** "Skip to main content" link at the top of every page.
3. **Form accessibility:** Labels associated with inputs. Error messages linked to fields. Required fields indicated.
4. **Color independence:** Information is never conveyed by color alone. Use icons, text or patterns alongside color.
5. **Reduced motion:** All animations respect `prefers-reduced-motion` media query.
6. **High contrast:** The design must remain usable in forced-colors / high-contrast modes.
7. **Screen reader announcements:** Dynamic content changes (progress updates, toast notifications) use ARIA live regions.

---

## Skill-Map Interaction Principles

The skill map is an interactive visualization showing cross-disciplinary skill relationships, prerequisites, and learner progression.

### Implemented Architecture (Phase 1)
- **Deterministic Multi-Track Swimlanes:** In "All Disciplines" mode, skills are separated into 4 distinct horizontal swimlanes (Programming & Web, Spoken Communication, Productivity & Systems, Design & Visual Hierarchy). Each lane features subtle category badges and dashed dividers, preventing cross-discipline node collisions.
- **Directional Cubic Bezier Connections:** Directed prerequisite-to-unlock edges are rendered via SVG paths with smooth S-curves (`M x1 y1 C ...`) and directional arrowhead markers (`#arrow-default`, `#arrow-unlocks`, `#arrow-prereq`) terminating at card borders.
- **Dynamic Interaction Highlighting:** Selecting any node highlights outgoing unlocks in violet (`#8B5CF6`) and incoming prerequisites in cyan (`#06B6D4`), elevating active elements to `z-20`.
- **Responsive Layout:** The graph maintains minimum readable dimensions (`min-w-[720px]`) within an `overflow-x-auto` wrapper on mobile viewports (with a swipe hint), avoiding crushed cards.
- **Accessible Structured Tree Alternative:** A toggle switcher allows learners and assistive technology users to switch from the visual graph to an accessible, semantically structured category card list with full prerequisite trees and keyboard accessibility.
- **Visual Encoding of Mastery:** Node cards display level dots (green for Foundational, cyan for Intermediate, violet for Advanced), full wrapped titles (`line-clamp-2`), and labeled demonstration mastery scores.
- **Discipline Filter Isolation:** Filtering by discipline recalculates layout coordinates to center the selected track with generous vertical breathing room, cleanly isolating relevant nodes and connection paths.

---

## Learning-Workspace Design Principles

The learning workspace is the primary environment where learners study lessons and complete activities.

### Layout Structure
```
┌─────────────────────────────────────────────────────────┐
│  Course Nav (breadcrumb) │ Lesson Title     │ Progress  │
├─────────┬───────────────────────────────────────────────┤
│ Module  │                                               │
│ Sidebar │  Lesson Content Area                          │
│ (collap-│  ┌─────────────────────────────────────────┐  │
│  sible) │  │ Instructional blocks                    │  │
│         │  │ (text, code examples, media)            │  │
│         │  ├─────────────────────────────────────────┤  │
│         │  │ Activity Workspace                      │  │
│         │  │ ┌──────────────┬──────────────────────┐ │  │
│         │  │ │ Editor/Input │ Preview/Results      │ │  │
│         │  │ └──────────────┴──────────────────────┘ │  │
│         │  ├─────────────────────────────────────────┤  │
│         │  │ Feedback / Hints Panel                  │  │
│         │  └─────────────────────────────────────────┘  │
│         │                                               │
│         │  ◄ Previous Lesson      Next Lesson ►         │
├─────────┴───────────────────────────────────────────────┤
│  AI Tutor (expandable panel / overlay)                  │
└─────────────────────────────────────────────────────────┘
```

### Principles
1. **Lesson content is the focus.** The workspace exists to support the lesson, not to surround it with chrome.
2. **Activities are inline.** Activities appear within the lesson flow, not on separate pages. Learners don't lose context.
3. **Resizable workspace panels.** Code editor and preview panes are drag-resizable.
4. **Persistent navigation context.** The sidebar shows the learner's position within the module. The breadcrumb shows position within the course.
5. **Non-intrusive AI tutor.** The AI tutor is accessible but not persistent. It appears in an expandable panel or slide-over, not as a chatbot bubble on every page.
6. **Feedback is immediate and specific.** Activity results appear in-place with clear pass/fail status, specific error messages for failed tests, and actionable hints.
