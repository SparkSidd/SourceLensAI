---
name: SourceLens AI
colors:
  surface: '#101416'
  surface-dim: '#101416'
  surface-bright: '#363a3c'
  surface-container-lowest: '#0b0f11'
  surface-container-low: '#191c1e'
  surface-container: '#1d2022'
  surface-container-high: '#272a2d'
  surface-container-highest: '#323538'
  on-surface: '#e0e3e6'
  on-surface-variant: '#bcc8d1'
  inverse-surface: '#e0e3e6'
  inverse-on-surface: '#2d3133'
  outline: '#86929a'
  outline-variant: '#3d484f'
  surface-tint: '#75d1ff'
  primary: '#92d9ff'
  on-primary: '#003548'
  primary-container: '#00c2ff'
  on-primary-container: '#004c66'
  inverse-primary: '#006688'
  secondary: '#4fddba'
  on-secondary: '#00382c'
  secondary-container: '#03b595'
  on-secondary-container: '#003f33'
  tertiary: '#66e0f8'
  on-tertiary: '#00363f'
  tertiary-container: '#44c4db'
  on-tertiary-container: '#004e59'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#c2e8ff'
  primary-fixed-dim: '#75d1ff'
  on-primary-fixed: '#001e2b'
  on-primary-fixed-variant: '#004d67'
  secondary-fixed: '#70f9d6'
  secondary-fixed-dim: '#4fddba'
  on-secondary-fixed: '#002019'
  on-secondary-fixed-variant: '#005141'
  tertiary-fixed: '#a3eeff'
  tertiary-fixed-dim: '#5bd6ee'
  on-tertiary-fixed: '#001f25'
  on-tertiary-fixed-variant: '#004e5a'
  background: '#101416'
  on-background: '#e0e3e6'
  surface-variant: '#323538'
typography:
  display-xl:
    fontFamily: Space Grotesk
    fontSize: 72px
    fontWeight: '700'
    lineHeight: '1.1'
    letterSpacing: -0.04em
  headline-lg:
    fontFamily: Space Grotesk
    fontSize: 40px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Space Grotesk
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.2'
  headline-md:
    fontFamily: Space Grotesk
    fontSize: 24px
    fontWeight: '500'
    lineHeight: '1.3'
  body-lg:
    fontFamily: Geist
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Geist
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.5'
  label-mono:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: '1.0'
    letterSpacing: 0.05em
  meta-sm:
    fontFamily: Geist
    fontSize: 13px
    fontWeight: '500'
    lineHeight: '1.4'
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  gutter: 24px
  margin-desktop: 48px
  margin-mobile: 16px
  panel-gap: 1px
---

## Brand & Style

The design system is engineered for elite-level cognitive throughput, blending high-stakes intelligence aesthetics with cinematic editorial clarity. It targets investigative researchers, analysts, and technologists who require massive data density without the cognitive fatigue of legacy systems.

The visual style is **Cinematic Minimalist with Technical Brutalist accents**. It leverages an asymmetrical composition to guide the eye through complex information hierarchies. The interface feels like a sophisticated OSINT (Open Source Intelligence) dashboard—precise, cold, and authoritative—but refined through smooth motion and layered glass-like surfaces. The emotional response is one of absolute control, focused calm, and intellectual superiority.

## Colors
The palette is rooted in a **Deep Charcoal and Navy Black** foundation to minimize eye strain during long-form research. 

- **Primary Accents (#00C2FF):** Used for active intelligence states, primary call-to-actions, and "Source Verified" indicators.
- **Secondary Accents (#5BE7C4):** Reserved for technical metadata, high-confidence relevance scores, and successful system operations.
- **Alerts (#FFB86B):** A muted gold rather than a harsh red, used to signal information conflicts, low-trust scores, or divergent data paths.

Layering is achieved through varying degrees of charcoal saturation rather than traditional shadows, creating a sense of physical depth within a digital void.

## Typography
The typographic hierarchy emphasizes the contrast between **Editorial Impact** and **Technical Precision**.

- **Space Grotesk** is used for headlines and primary UI headers, giving the interface a modern, geometric, and slightly "sci-fi" editorial feel.
- **Geist** handles the heavy lifting for body copy, providing exceptional legibility at small sizes and high densities.
- **JetBrains Mono** is utilized for metadata, system status, timestamps, and confidence scores, reinforcing the feeling of a live intelligence feed.

All technical labels should be uppercase with slight tracking (letter-spacing) to enhance the "terminal" aesthetic.

## Layout & Spacing
This design system utilizes an **Asymmetrical Fixed Grid** model. The primary research canvas (left/center) follows a wide 8-column span, while intelligence feeds and metadata rails (right) occupy a tighter 4-column span.

Spacing is disciplined and follows a 4px baseline. To emphasize the "layered" OSINT aesthetic, panels are often separated by **1px hairline borders** instead of wide gutters, creating a high-density "instrument cluster" feel. Content should be grouped into logical "Intelligence Blocks" with consistent internal padding of 24px.

## Elevation & Depth
Depth is not communicated via shadows, but through **Tonal Stacking and Backdrop Blurs**. 

1.  **Base Layer (#0D0F12):** The infinite void. Used for the primary background.
2.  **Surface Layer (#151922):** The main workspace.
3.  **Raised Panels (#1B2029):** Floating utility panels and active source cards. These use a 1px solid border (#262F3D) to define edges.
4.  **Overlays:** Modal dialogs and the ORION companion use a heavy glassmorphism effect (Backdrop Blur: 20px) with a 10% opacity white inner stroke to simulate reinforced glass.

## Shapes
The shape language is **Precision-Engineered Softness**. Most UI elements use a subtle 4px (0.25rem) corner radius to maintain a professional, sharp-edged look while avoiding the harshness of true 0px corners.

- **Source Cards:** Use `rounded-lg` (8px) to distinguish them from the structural grid.
- **Interactive Inputs:** Use `rounded-sm` (4px).
- **ORION Companion:** The AI avatar is the only exception, utilizing perfectly circular or fluid, organic geometric paths to represent "living" intelligence.

## Components

### Source Cards
Cards represent individual data points or documents. They feature a **JetBrains Mono** header for the trust score (e.g., `TRUST_LVL: HIGH`) and a primary headline in **Space Grotesk**. The background should be slightly lighter than the workspace to signify interactability.

### Live Intelligence Feeds
Terminal-style scrolling lists. Text should be compact (`meta-sm`) with mono-spaced timestamps. Use primary accent (#00C2FF) for new entries that "flash" briefly before settling into the muted secondary text color.

### Buttons & Controls
Primary buttons are high-contrast: #00C2FF background with #0D0F12 text. Secondary buttons are "Ghost" style—1px borders with no fill, utilizing hover states that trigger a subtle inner glow rather than a color change.

### ORION AI Companion
A minimal, holographic geometric entity. It should occupy a corner of the screen or float near the cursor during research. Use the tertiary color (#6EE7FF) with a slight "flicker" animation (opacity 0.8 to 1.0) to indicate processing.

### Adaptive Research Modes
- **Academic:** Shifts secondary accents to soft purples; expands line-height for long-form reading.
- **Technical:** Increases density; minimizes margins; shifts accents to #5BE7C4.
- **Investigative:** Highlights "Conflicts" using the Alert color (#FFB86B) and enables the asymmetrical split-view for cross-referencing.