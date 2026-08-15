# ExtraaEdge homepage — split into 29 standalone sections

`ExtraaEdgeHomepageWithVideoAndOldHeader.html` was one 10,322-line / 1.1 MB page.
It is now split so that **every section has its own HTML file that runs on its own**.

```
extraaedge-sections/
├── index.html                    ← launcher: click any section to open it
├── sections/                     ← 29 runnable section pages
│   ├── 01-header.html
│   ├── 02-quick-toc.html
│   └── …
├── assets/
│   ├── global.css                ← every <style> of the original, in original order
│   └── global-scripts.html       ← the 4 page-wide <script> blocks (reference copy)
├── _original/full-homepage.html  ← untouched original, for diffing
└── sections.json                 ← machine-readable index
```

## How to run a section in VS Code

1. Open the `extraaedge-sections` folder in VS Code.
2. Install the **Live Server** extension (if you do not have it).
3. Right-click any file in `sections/` → **Open with Live Server**.

That section opens on `http://127.0.0.1:5500/…` on its own. Start with `index.html`
if you want a clickable list of all 29.

> Keep the folder structure intact — each section page loads `../assets/global.css`.
> Opening a section with `file://` (double-click) also works, but Live Server is
> recommended because a few widgets use `IntersectionObserver` and iframes.

## Sections

| # | File | Section | Source lines |
|---|------|---------|--------------|
| 01 | `01-header.html` | Site Header & Mobile Menu | 708-1440, 1575-1872, 1931-2073 |
| 02 | `02-quick-toc.html` | Quick Table of Contents (floating) | 2298-2394 |
| 03 | `03-hero.html` | Hero + Book-a-Demo Drawer | 2272-2297, 2395-2516, 2517-2809 |
| 04 | `04-trusted-institutions.html` | Trusted Institutions Logo Marquee | 2810-3076, 9362-9394 |
| 05 | `05-why-extraaedge.html` | Why Institutes Choose ExtraaEdge | 3077-3340 |
| 06 | `06-respond-first-ai.html` | Respond First With AI Agents | 3341-3620 |
| 07 | `07-platform-live-demo.html` | Platform — Live Interactive Demo | 3621-5019 |
| 08 | `08-see-real-crm-popup.html` | See the Real CRM — Booking Popup | 5020-5187 |
| 09 | `09-vidyaai-powered-by.html` | Powered by VidyaAI (embed) | 5394-6212, 9525-9534 |
| 10 | `10-vidya-suite.html` | Meet Vidya AI — Suite | 6481-6882 |
| 11 | `11-architect-mindset.html` | Architect Mindset | 6883-6923 |
| 12 | `12-stories.html` | Customer Stories | 5188-5292, 6924-7060 |
| 13 | `13-mid-cta.html` | Mid-Page CTA — Book a Demo | 7061-7084 |
| 14 | `14-industries.html` | Industries We Serve | 7085-7379 |
| 15 | `15-cro-roi.html` | Why Teams Choose Us + ROI Calculator | 7380-7455 |
| 16 | `16-misc-widgets.html` | Scroll Widgets (divider, progress rail, toast) | 7456-7571 |
| 17 | `17-integrations.html` | Integrations Hub | 7572-7844 |
| 18 | `18-security.html` | Security & Compliance | 7845-7863 |
| 19 | `19-go-live.html` | Go Live in 7 Days | 7913-7931 |
| 20 | `20-switch-crm.html` | Switch From Your Current CRM | 7932-7956 |
| 21 | `21-pricing.html` | Simple Product-Based Pricing | 7957-8007 |
| 22 | `22-faq.html` | FAQ | 8008-8033 |
| 23 | `23-products.html` | Our Products | 8034-8291 |
| 24 | `24-solutions.html` | Solutions | 8401-8532 |
| 25 | `25-resources.html` | Resources & Events | 8533-8709 |
| 26 | `26-blog.html` | Latest From the Blog | 8710-8781 |
| 27 | `27-scroll-progress-cta.html` | Scroll Progress Bar + Sticky Demo Pill | 8979-9054 |
| 28 | `28-footer.html` | Site Footer | 9677-10036 |
| 29 | `29-floating-actions.html` | Floating Actions (WhatsApp / Call / TOC) | 10037-10191 |

## What each section file contains

```
<head>   charset, viewport, the original font/preconnect <link>s, the Lucide
         icon CDN <script>, and <link href="../assets/global.css">
<body>   <main id="main-content"><div class="ee-home">   ← same wrappers as the
             …the section's markup, verbatim…              live page, so descendant
         </div></main>                                     CSS still matches
         …the section's own <script> blocks, verbatim…
         …the 4 page-wide <script> blocks, verbatim…
```

Markup, CSS and JS are copied **byte-for-byte** from the original. Nothing was
rewritten or re-indented.

## Why the CSS is shared instead of per-section

The original page defines its CSS in 65 top-level `<style>` blocks whose *order*
decides the cascade — later blocks (`ee-skin-2026`, `ee-mobile-grids`,
`ee-cta-unify`, …) deliberately override earlier ones, and many of them style
several sections at once. Splitting that per section would silently change how
sections look. So all 65 blocks are concatenated into `assets/global.css` **in the
original document order**, and each block is labelled with its source line:

```css
/* ---- ee-megabar  (source line 1932) ---- */
```

Search that comment to find the block you want to edit.

## Notes / things worth knowing

- **Images and videos** point at absolute `https://www.extraaedge.com/…` URLs, so
  they need an internet connection to appear. Offline they show alt text.
- **Preview harness.** Six sections are `position: fixed` or hidden-until-triggered
  (header, quick TOC, CRM popup, scroll widgets, progress/sticky CTA, floating
  actions). On their own they would render a blank screen, so those files end with
  a small block marked `data-preview-harness` — a note, scroll filler, and for the
  CRM popup a button that opens it. **It is not part of the original page**; delete
  the two `PREVIEW HARNESS` blocks to get the raw section back.
- **Hero + drawer ship together.** The Book-a-Demo drawer (`#admission-form`) has no
  script of its own — it is driven by the hero's IIFE, which looks up `#admission-form`,
  `#eeddBack` and `#eeddClose`. Separating them would leave a drawer that cannot open,
  so both live in `03-hero.html`.
- **Dropped from the section pages:** the page `<title>`, SEO/OpenGraph/Twitter meta,
  canonical + hreflang links, favicons, the PWA manifest and the sitewide JSON-LD.
  They describe the whole homepage, not a section. All of it is still in
  `_original/full-homepage.html`.
- **Dead references are kept as-is.** A few IDs the shared scripts look up
  (`#amsToday`, `#roadmap`, `#spark`, `#toc`, `#rfaCap`, …) do not exist in the
  original page either — those sections were removed earlier. Every lookup is
  guarded, so nothing errors.

## Regenerating

`tools/split_sections.py` rebuilds this whole folder from the original:

```bash
python3 tools/split_sections.py            # uses extraaedge-sections/_original/full-homepage.html
python3 tools/split_sections.py path/to/homepage.html
```

The script asserts that its line-range manifest covers every line of the source, so
a block can never be dropped silently. Verified after generation: all 160 top-level
blocks appear verbatim in the output, all 21 `<section>` elements are byte-identical
to the original, and all 29 pages render in Chromium with balanced tags and no
JavaScript errors.
