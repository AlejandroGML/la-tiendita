# Tiendavirtual Premium — Hybrid Design System

> Category: Technical Documentation
> Dark-mode-native immersive design for technical study guides. Linear's precision
> dark canvas as the base, Stripe's blue-tinted atmospheric shadows for depth,
> and selective gradient accents for cinematic moments. Built for landing-page-style
> documentation with scroll storytelling.

## 1. Visual Theme & Atmosphere

This system is a dark-mode-native canvas where technical content emerges from
near-blackness with engineered precision. The base is Linear's darkness philosophy:
a near-black canvas (`#08090a`) with an imperceptible blue-cool undertone, where
information density is managed through subtle gradations of white opacity rather
than color variation. Content doesn't sit ON the background — it emerges FROM it,
like starlight.

Layered on top is Stripe's shadow philosophy: multi-layer, blue-tinted shadows
(`rgba(94,106,210,0.15)`) that create atmospheric depth on dark surfaces.
Where most dark themes suffer from invisible black-on-black shadows, this system
uses brand-colored glow shadows that make cards appear to float in a violet
twilight. The shadow color (`94,106,210`) ties directly to the indigo brand
palette, making even elevation feel on-brand.

Typography combines two philosophies: Inter Variable with `"cv01", "ss03"`
OpenType features (Linear's geometric identity) at weight 510 for UI and body,
dropping to weight 300 (Stripe's whisper-weight) for display headlines. The
result is headlines that feel ethereal and whispered — authority without shouting
— paired with UI text that has subtle, confident emphasis.

Gradient accents (ruby `#ea2261` to magenta `#f96bee` to purple `#533afd`) appear
ONLY in cinematic moments: hero sections, section transitions, and the active
state of interactive diagrams. The 90% of the UI is strictly achromatic with a
single indigo accent. This restraint makes the gradient moments feel earned.

**Key Characteristics:**
- Dark-mode-native: `#08090a` canvas, `#0f1011` panels, `#191a1b` elevated surfaces
- Inter Variable with `"cv01", "ss03"` globally — geometric alternates for identity
- Dual weight system: 300 (Stripe whisper-display) + 510 (Linear signature UI)
- Blue-tinted glow shadows: `rgba(94,106,210,0.15)` for atmospheric card depth
- Semi-transparent white borders: `rgba(255,255,255,0.05)` to `rgba(255,255,255,0.08)`
- Brand accent: indigo-violet `#5e6ad2` / `#7170ff` (Linear) + purple `#533afd` (Stripe CTA)
- Gradient decorative: ruby-to-magenta-to-purple for hero and transitions only
- SourceCodePro for code at 12px/500 with generous 2.00 line-height
- Luminance stacking for depth: `rgba(255,255,255,0.02)` to `0.05` background steps

## 2. Color Palette & Roles

### Background Surfaces
- **Canvas Black** (`#08090a`): The deepest background — hero sections, page canvas. Near-pure black with an imperceptible blue-cool undertone. This IS the whitespace.
- **Panel Dark** (`#0f1011`): Sidebar, code blocks, recessed panels. One step up from canvas.
- **Surface Elevated** (`#191a1b`): Card backgrounds, dropdowns, elevated components.
- **Hover Surface** (`#28282c`): The lightest dark surface — hover states, active rows.
- **Brand Dark** (`#1c1e54`): Deep indigo for immersive brand sections and section transitions. Not black — a saturated navy that creates rhythm.

### Text & Content
- **Primary Text** (`#f7f8f8`): Near-white with a barely-warm cast. NEVER use pure `#ffffff` — it causes eye strain on dark backgrounds.
- **Secondary Text** (`#d0d6e0`): Cool silver-gray for body text, descriptions, table content.
- **Tertiary Text** (`#8a8f98`): Muted gray for metadata, placeholders, captions.
- **Quaternary Text** (`#62666d`): Most subdued — timestamps, disabled states, subtle labels.

### Brand & Accent
- **Brand Indigo** (`#5e6ad2`): Primary brand color — CTA backgrounds, brand marks, key interactive surfaces. Linear's signature.
- **Accent Violet** (`#7170ff`): Brighter variant for links, active states, selected items.
- **Accent Hover** (`#828fff`): Lighter, more saturated for hover states.
- **Stripe Purple** (`#533afd`): More saturated purple for primary CTAs — Stripe's confidence. Use when you need more visual weight than Brand Indigo.
- **Purple Hover** (`#4434d4`): Darker purple for CTA hover states.

### Gradient Accents (decorative only)
- **Hero Gradient** (`linear-gradient(135deg, #ea2261 0%, #f96bee 40%, #533afd 100%)`): Ruby to magenta to purple. Hero overlays, section transitions. Use SPARINGLY.
- **Brand Section Gradient** (`linear-gradient(180deg, #1c1e54 0%, #08090a 100%)`): Indigo fading to canvas black. Section dividers.
- **Accent Glow** (`radial-gradient(circle, rgba(94,106,210,0.15) 0%, transparent 70%)`): Soft indigo glow behind interactive elements.

### Status Colors
- **Emerald** (`#10b981`): Success — quiz correct answers, completion states.
- **Emerald Text** (`#108c3d`): Success badge text.
- **Ruby** (`#ea2261`): Error/destructive — quiz wrong answers, danger callouts. Also serves as gradient origin.

### Border & Divider
- **Border Subtle** (`rgba(255,255,255,0.05)`): Ultra-subtle — default border, barely visible structure.
- **Border Standard** (`rgba(255,255,255,0.08)`): Standard border for cards, inputs, code blocks.
- **Border Elevated** (`rgba(255,255,255,0.12)`): More visible borders for emphasized containers.
- **Border Accent** (`rgba(113,112,255,0.3)`): Violet-tinted border for active/selected states.
- **Border Solid** (`#23252a`): Solid dark border for prominent separations (rare).

## 3. Typography Rules

### Font Family
- **Primary**: `Inter Variable`, fallbacks: `SF Pro Display, -apple-system, system-ui, Segoe UI, Roboto, sans-serif`
- **Monospace**: `SourceCodePro`, fallbacks: `SFMono-Regular, ui-monospace, Menlo`
- **OpenType Features**: `"cv01", "ss03"` enabled globally — cv01 provides single-story 'a', ss03 adjusts letterforms for geometric character. Add `"tnum"` for tabular numbers in stats/metrics.

### Hierarchy

| Role | Font | Size | Weight | Line Height | Letter Spacing | Notes |
|------|------|------|--------|-------------|----------------|-------|
| Display Hero | Inter Variable | 64px (4.00rem) | 300 | 1.05 | -1.408px | Hero headlines, whisper-weight authority |
| Display | Inter Variable | 48px (3.00rem) | 300 | 1.10 | -1.056px | Section headlines, cinematic moments |
| Heading 1 | Inter Variable | 32px (2.00rem) | 510 | 1.15 | -0.704px | Major section titles |
| Heading 2 | Inter Variable | 24px (1.50rem) | 510 | 1.30 | -0.288px | Sub-section headings |
| Heading 3 | Inter Variable | 20px (1.25rem) | 590 | 1.30 | -0.24px | Feature titles, card headers |
| Body Large | Inter Variable | 18px (1.13rem) | 400 | 1.60 | -0.165px | Introduction text, lead paragraphs |
| Body | Inter Variable | 16px (1.00rem) | 400 | 1.60 | normal | Standard reading text |
| Body Emphasis | Inter Variable | 16px (1.00rem) | 510 | 1.60 | normal | Emphasized body, UI labels |
| Body Strong | Inter Variable | 16px (1.00rem) | 590 | 1.60 | normal | Strong emphasis in content |
| Small | Inter Variable | 15px (0.94rem) | 400 | 1.60 | -0.165px | Secondary body text |
| Caption | Inter Variable | 13px (0.81rem) | 400-510 | 1.50 | -0.13px | Metadata, timestamps, table headers |
| Label | Inter Variable | 12px (0.75rem) | 400-590 | 1.40 | normal | Button text, small labels |
| Micro | Inter Variable | 11px (0.69rem) | 510 | 1.40 | normal | Tiny labels, overline |
| Mono Body | SourceCodePro | 12px (0.75rem) | 500 | 2.00 | normal | Code blocks — generous line-height |
| Mono Bold | SourceCodePro | 12px (0.75rem) | 700 | 2.00 | normal | Bold code, keywords |
| Mono Label | SourceCodePro | 12px (0.75rem) | 500 | 2.00 | normal | Technical labels, uppercase |

### Principles
- **Dual weight system**: Weight 300 (Stripe) for display headlines creates ethereal, whispered authority. Weight 510 (Linear) for UI and body creates subtle emphasis without heaviness. These NEVER mix — display is always 300, UI is always 510.
- **Compression at scale**: Display sizes use progressively tighter letter-spacing. Below 24px, spacing relaxes toward normal.
- **OpenType as identity**: `"cv01", "ss03"` are non-negotiable. Without them, it's generic Inter, not this system's Inter.
- **Three-tier weight for UI**: 400 (reading), 510 (emphasis/UI), 590 (strong emphasis). Weight 300 appears ONLY in display contexts.
- **NEVER use weight 700** on Inter Variable. The maximum is 590. SourceCodePro can use 700 for code contrast.

## 4. Component Stylings

### Buttons

**Primary CTA (Stripe Purple)**
- Background: `#533afd`
- Text: `#ffffff`
- Padding: 8px 16px
- Radius: 6px
- Font: 16px Inter Variable weight 510, `"cv01", "ss03"`
- Hover: `#4434d4` background + `--shadow-glow-purple`
- Use: Primary actions ("Explore architecture", "Start quiz")

**Ghost Button (Linear default)**
- Background: `rgba(255,255,255,0.02)`
- Text: `#d0d6e0`
- Radius: 6px
- Border: `1px solid rgba(255,255,255,0.08)`
- Hover: background shifts to `rgba(255,255,255,0.05)`
- Use: Secondary actions, navigation

**Brand Indigo Button**
- Background: `#5e6ad2`
- Text: `#ffffff`
- Radius: 6px
- Hover: `#7170ff` + `--shadow-glow`
- Use: Brand moments, featured CTAs

**Pill Button**
- Background: transparent
- Text: `#d0d6e0`
- Radius: 9999px
- Border: `1px solid #23252a`
- Font: 12px weight 510
- Use: Tags, filter chips, status indicators, quiz options

### Cards & Containers
- Background: `rgba(255,255,255,0.02)` to `rgba(255,255,255,0.04)` — NEVER solid, always translucent
- Border: `1px solid rgba(255,255,255,0.08)` standard
- Radius: 8px (standard), 12px (featured/panel)
- Shadow (standard): luminance stepping — no shadow, just border
- Shadow (elevated/featured): `rgba(94,106,210,0.15) 0px 30px 45px -30px, rgba(0,0,0,0.3) 0px 18px 36px -18px`
- Shadow (glow on hover): `0 0 40px rgba(94,106,210,0.2)`
- Hover: subtle background opacity increase + glow shadow appears

### Code Blocks
- Background: `#0f1011` (Panel Dark)
- Border: `1px solid rgba(255,255,255,0.08)`
- Radius: 8px
- Font: SourceCodePro 12px weight 500, line-height 2.00
- Header bar: `rgba(255,255,255,0.03)` bg with language label in 12px weight 510
- Copy button: top-right, ghost button style

### Badges & Pills
**Success (quiz correct)**
- Background: `rgba(16,185,129,0.15)`
- Text: `#10b981`
- Border: `1px solid rgba(16,185,129,0.3)`
- Radius: 4px
- Glow: `0 0 20px rgba(16,185,129,0.2)`

**Error (quiz wrong)**
- Background: `rgba(234,34,97,0.15)`
- Text: `#ea2261`
- Border: `1px solid rgba(234,34,97,0.3)`
- Radius: 4px

**Neutral Tag**
- Background: transparent
- Text: `#d0d6e0`
- Border: `1px solid #23252a`
- Radius: 9999px
- Font: 12px weight 510

### Diagram Nodes (architecture diagram)
**Inactive node**
- Background: `rgba(255,255,255,0.04)`
- Border: `1px solid rgba(255,255,255,0.08)`
- Text: `#8a8f98`

**Active node (scroll-highlighted)**
- Background: `#5e6ad2`
- Border: `1px solid #7170ff`
- Text: `#f7f8f8`
- Shadow: `0 0 30px rgba(113,112,255,0.4)` — indigo glow

**Dimmed node (not active)**
- Opacity: 0.3

### Callouts (why, tip, warning, danger)
**Why-box**
- Background: `rgba(94,106,210,0.06)`
- Border-left: `3px solid #5e6ad2`
- Radius: 0px 8px 8px 0px

**Tip**
- Background: `rgba(16,185,129,0.06)`
- Border-left: `3px solid #10b981`

**Warning**
- Background: `rgba(234,34,97,0.06)`
- Border-left: `3px solid #ea2261`

**Danger**
- Background: `rgba(234,34,97,0.1)`
- Border-left: `3px solid #ea2261`
- Glow: `0 0 20px rgba(234,34,97,0.1)`

## 5. Layout Principles

### Spacing System
- Base unit: 8px
- Scale: 4px, 8px, 12px, 16px, 20px, 24px, 32px, 40px, 48px, 64px, 80px
- Section vertical padding: 80px+ (generous — darkness provides natural separation)
- Card internal padding: 24-32px

### Grid & Container
- Max content width: 1080px (reading-optimized, not too wide)
- Hero: centered single-column with generous vertical padding
- Feature sections: full-width with internal max-width constraint
- Cards: 2-3 column grids for decision/comparison cards
- Diagrams: full-width within max-content

### Whitespace Philosophy
- **Darkness as space**: Empty space isn't white — it's absence. The near-black background IS the whitespace.
- **Compressed headlines, expanded surroundings**: Display text at 64px with -1.408px tracking is dense and compressed, sitting within vast dark padding. The contrast creates tension.
- **Section isolation**: Each section separated by 80px+ with no visible dividers — the dark background provides natural separation.
- **Rhythm via brand sections**: Every 3-4 sections, insert a `#1c1e54` brand section to break monotony and create cinematic cadence.

### Border Radius Scale
- Micro (2px): Inline badges, toolbar buttons
- Small (4px): Badges, small elements
- Button (6px): Buttons, inputs, functional elements
- Card (8px): Cards, dropdowns, code blocks
- Panel (12px): Panels, featured cards, section containers
- Pill (9999px): Chips, tags, status indicators

## 6. Depth & Elevation

| Level | Treatment | Use |
|-------|-----------|-----|
| Flat | No shadow, `#08090a` bg | Page background, deepest canvas |
| Surface | `rgba(255,255,255,0.02)` bg + `1px solid rgba(255,255,255,0.08)` border | Standard cards, containers |
| Elevated | `rgba(255,255,255,0.04)` bg + blue-tinted shadow | Featured cards, hover states |
| Glow | `0 0 40px rgba(94,106,210,0.2)` | Active/featured elements, diagram nodes |
| Inset | `rgba(0,0,0,0.2) 0px 0px 12px 0px inset` | Recessed panels, code blocks |
| Dialog | Multi-layer: blue-tinted far + black near | Modals, command palette |

**Shadow Philosophy**: On dark surfaces, traditional shadows are invisible. This system uses TWO techniques: (1) Linear's luminance stepping — depth communicated through background opacity (`0.02` to `0.04`), and (2) Stripe's blue-tinted glow shadows — `rgba(94,106,210,0.15)` that creates atmospheric depth because the shadow color is brand-tinted, not neutral black. The glow technique (`0 0 40px`) is reserved for active/interactive elements, creating a "spotlight" effect.

## 7. Do's and Don'ts

### Do
- Use Inter Variable with `"cv01", "ss03"` on ALL text — these features are identity
- Use weight 300 for display headlines and weight 510 for UI/body
- Build on near-black backgrounds: `#08090a` for canvas, `#0f1011` for panels
- Use semi-transparent white borders (`rgba(255,255,255,0.05-0.08)`) for structure
- Apply blue-tinted glow shadows (`rgba(94,106,210,...)`) for elevated elements
- Use `#f7f8f8` for primary text — not pure white
- Reserve gradients (ruby-to-magenta) for hero and transitions ONLY
- Use luminance stepping for card depth: `rgba(255,255,255,0.02)` to `0.04`
- Apply negative letter-spacing at display sizes
- Use SourceCodePro at 12px/500 with line-height 2.00 for code

### Don't
- Don't use pure white (`#ffffff`) as text — `#f7f8f8` prevents eye strain
- Don't use solid colored backgrounds for cards — transparency is the system
- Don't use weight 700 on Inter Variable — maximum is 590
- Don't use neutral gray/black shadows on dark surfaces — tint with indigo `rgba(94,106,210,...)`
- Don't apply gradients to body text, buttons, or navigation chrome
- Don't skip the OpenType features — without them, it's generic Inter
- Don't use positive letter-spacing at display sizes — always negative
- Don't introduce warm colors (orange, yellow) into UI chrome
- Don't use large border-radius (16px+) on cards or buttons — max 12px for panels
- Don't use visible/opaque solid dark borders — always semi-transparent white

## 8. Responsive Behavior

### Breakpoints
| Name | Width | Key Changes |
|------|-------|-------------|
| Mobile | <640px | Single column, 48px section padding, 32px display text |
| Tablet | 640-768px | Two-column grids begin, moderate padding |
| Desktop Small | 768-1024px | Full card grids, expanded padding |
| Desktop | 1024-1280px | Standard layout, full navigation |
| Large Desktop | >1280px | Generous margins, max-content constraint |

### Collapsing Strategy
- Hero: 64px to 48px to 32px display text, weight 300 maintained
- Navigation: horizontal links to hamburger at 768px
- Feature cards: 3-column to 2-column to single column
- Section spacing: 80px+ to 48px on mobile
- Diagrams: maintain readability, may reduce node count visible

## 9. Agent Prompt Guide

### Quick Color Reference
- Primary CTA: Stripe Purple (`#533afd`)
- Brand accent: Indigo (`#5e6ad2`) / Violet (`#7170ff`)
- Page Background: Canvas Black (`#08090a`)
- Panel Background: Panel Dark (`#0f1011`)
- Surface: Elevated (`#191a1b`)
- Heading text: Primary White (`#f7f8f8`)
- Body text: Silver Gray (`#d0d6e0`)
- Muted text: Tertiary Gray (`#8a8f98`)
- Border (default): `rgba(255,255,255,0.08)`
- Card glow: `0 0 40px rgba(94,106,210,0.2)`
- Gradient hero: `linear-gradient(135deg, #ea2261, #f96bee, #533afd)`

### Example Component Prompts
- "Create a hero section on `#08090a` canvas. Headline at 64px Inter Variable weight 300, line-height 1.05, letter-spacing -1.408px, color `#f7f8f8`, font-feature-settings `'cv01', 'ss03'`. Subtitle at 18px weight 400, color `#8a8f98`. Purple CTA button (`#533afd`, 6px radius, 8px 16px padding) and ghost button (`rgba(255,255,255,0.02)` bg, `rgba(255,255,255,0.08)` border). Hero gradient overlay: `linear-gradient(135deg, rgba(234,34,97,0.08), rgba(249,107,238,0.05), rgba(83,58,253,0.08))`."
- "Design a decision card on dark background: `rgba(255,255,255,0.02)` background, `1px solid rgba(255,255,255,0.08)` border, 8px radius. Title at 20px Inter Variable weight 590, color `#f7f8f8`. Body at 15px weight 400, color `#8a8f98`. Hover: glow shadow `0 0 40px rgba(94,106,210,0.2)`."
- "Build a code block: `#0f1011` background, `1px solid rgba(255,255,255,0.08)` border, 8px radius. SourceCodePro 12px weight 500, line-height 2.00. Header bar `rgba(255,255,255,0.03)` with language label in 12px weight 510."
- "Create a section transition: gradient background `linear-gradient(180deg, #1c1e54 0%, #08090a 100%)`, 80px vertical padding. Section title at 48px Inter Variable weight 300, letter-spacing -1.056px, `#f7f8f8`."

### Iteration Guide
1. Always set `font-feature-settings: "cv01", "ss03"` on all Inter text
2. Display = weight 300, UI = weight 510, strong = weight 590 — never 700
3. Card depth: luminance stepping (`rgba(255,255,255,0.02)` to `0.04`) + glow shadow on hover
4. Shadows are ALWAYS blue-tinted (`rgba(94,106,210,...)`) or glow-based — never neutral black
5. Gradients appear ONLY in hero, transitions, and active diagram nodes
6. Borders are always semi-transparent white, never solid dark colors
7. SourceCodePro for code, Inter Variable for everything else
