# Design system — Cementne košuljice Ivkov

**Mobile-first** · referentni viewport **360px**

## Breakpointi

| Token | px | rem | Upotreba |
|-------|-----|-----|----------|
| `--bp-base` | 360 | 22.5 | Dizajn referenca |
| `--bp-sm` | 390 | 24.375 | Veći telefoni |
| `--bp-md` | 430 | 26.875 | `@media (min-width: 26.875rem)` — dodatni gutter |
| `--bp-tablet` | 768 | 48 | `@media (min-width: 48rem)` |
| `--bp-desktop` | 1024 | 64 | `@media (min-width: 64rem)` |
| `--bp-wide` | 1440 | 90 | `@media (min-width: 90rem)` |

Pravilo: **bazni stilovi = mobil**, zatim `min-width: 48rem` i `min-width: 64rem`. Ne koristiti `max-width` za layout.

## Razmaci

| Nivo | Opseg | Tokeni (primer) |
|------|--------|------------------|
| Mobil | 16–24px | `--space-4` … `--space-6`, `--section-padding-y` |
| Tablet (768+) | 24–40px | `--space-8` … `--space-16` |
| Desktop (1024+) | 40–80px | `--space-16` … `--space-24` |

Semantički: `--gap-inline`, `--gap-block`, `--gap-grid`, `--container-padding-x`, `--section-padding-y`.

## Tipografija

- Mobil: `--font-size-base` 16px, kompaktniji `--font-size-2xl` … `--font-size-5xl`
- Skaliranje na tablet/desktop u `variables.css`
- Fluid: `--type-display`, `--type-h1`, `--type-h2`, `--type-lead`

## Fajlovi

| Fajl | Sadržaj |
|------|---------|
| `variables.css` | Boje, breakpointi, spacing, tipografija, layout |
| `typography.css` | Elementi i prose |
| `utilities.css` | `.u-grid`, `.u-actions`, `.u-section-y`, vidljivost, … |
| `navigation.css` | Zaglavlje, hamburger, slide-in drawer, desktop nav |
| `components.css` | Dugmad, footer, kartice |
| `global.css` | Stranice, forme, blog |
| `bundles/site-core.css` | Produkcijski sync bundle (build skripta) |
| `bundles/site-defer.css` | Produkcijski async bundle (build skripta) |

## Utility klase (primer)

```html
<div class="u-stack u-section-y">
<section class="u-grid u-grid--2-md u-grid--3-lg">
<div class="u-actions">… dugmad …</div>
```

## Brand boje

| Token | Vrednost |
|-------|----------|
| `--color-primary` | `#DD4327` (ivice, fokus, pozadine) |
| `--color-text-accent` | `#F2B705` (tekst) |
| `--color-btn` | `#F2B705` (dugmad) |
| `--color-dark` | `#222222` |
| `--color-accent` | `#FFFFFF` |

Jezik sajta: **srpski (latinica)**.

## Navigacija (`navigation.css` + `site-shell.js`)

- Mobil: hamburger → drawer sa desna, scrim, 44px linkovi
- Desktop (`min-width: 48rem`): horizontalna traka
- Zatvaranje: link, scrim, ×, Escape, resize na desktop
- Fokus: zamka u draweru, povratak na hamburger

## Karuseli (`carousel-core.js`, `carousel-shared.css`)

- Početna / usluge: `carousel_static_image` (statičke WebP iz `static/img/`)
- Touch: swipe + velocity snap; fade + scale animacija
- CLS: `aspect-ratio` rezerva → tačna visina nakon učitavanja
