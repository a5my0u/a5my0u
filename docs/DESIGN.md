# Obsidian Emerald — design specification

## Direction

An understated black-silk identity with emerald accents and charcoal data cards.
The username is the primary identity. English prose stays selectable Markdown.
There is no tagline, footer, contact information, social link, rank, trophy,
visitor counter, 3D graph, or invented project.

| Role | Value |
| --- | --- |
| Background | `#0D0D0D` |
| Card | `#171717` |
| Border | `#303030` |
| Primary / secondary text | `#F5F5F5` / `#A1A1AA` |
| Accent | `#34D399` |
| Snake only | `#FBBF24` |

Numbered sections retain the requested numbering; section 04 is absent while no
featured project is selected. The verified public website repository currently
contains an introductory HTML/CSS/JavaScript exercise. It is included in public
language statistics but is not represented as a substantial portfolio project.

## Dark Silk

The original silk texture was generated for this project with OpenAI ImageGen,
then optimized with Pillow into `assets/header/silk-texture.jpg` (1800 × 600).
The JPEG is embedded in each SVG as data, so no external image or font server is
needed. Typography is actual SVG text with system sans-serif fallbacks.

Recreation prompt (a concise description of the generation brief):

> A premium wide black silk / satin banner. Deep charcoal shadows, physically
> believable fabric folds and subdued cinematic specular highlights. Leave the
> left half dark and quiet for typography. Concentrate depth and restrained,
> faint emerald reflections toward the right. Natural continuous composition,
> no text, logos, geometry, circuitry, particles, neon, or green background.

The shipped texture, rather than another stochastic generation, is the source
for reproducible builds. This AI-created texture is not a stock photograph and
does not carry a third-party stock-image license. No broader legal claim about
exclusive rights is made.

Desktop: 1200 × 320. Mobile: 600 × 360. A 16-second moving reflection affects
only the right side; text remains fixed. Each size has animated and static SVGs.
`picture` selects the mobile version and a reduced-motion static version. The
README also provides a manually expandable static header.

## Cards and layout

- About: three 360 × 174 SVGs shown at 270px, wrapping naturally.
- Tech: four 560 × 382 cards shown at 410px; 24px source labels and consistent
  44px logo plates. Brand silhouettes and colors are retained. Dark marks remain
  paired with clearly legible technology names. See [asset terms](THIRD_PARTY.md).
- Analytics: two 560 × 520 desktop SVGs, side by side when space permits.
  Dedicated 320px mobile SVGs retain the 2 × 2 KPIs and stack donut/legend.
- Snake: desktop calendar 960 × 226; mobile calendar wraps consecutive weeks
  into blocks of up to 14 weeks. Both contain the same actual dates and counts.
- Cards use 18px source-radius corners, 1px borders, generous internal spacing.

The README uses supported HTML image/picture/details elements and Markdown,
without page CSS, scripts, iframe, or fixed table columns. The preview's CSS
approximates GitHub's Markdown surface and is not part of the published README.
GitHub controls the surrounding page background and actual container width.

## Motion and accessibility

Only the header reflection and 56-second gold snake animate. Reduced-motion
styles hide the moving snake and preserve the real calendar. Zero activity
renders genuinely empty cells; it does not create decorative green activity.
Every image has descriptive alt text and SVG title/description. Daily calendar
cells also carry their date and count in SVG titles. Data definitions remain
selectable text below the analytics. Percentages represent code bytes, not skill.

Desktop and mobile widths are selected by viewport media queries. A narrow
desktop container still scales the desktop images until the viewport breakpoint
is reached; GitHub README does not offer arbitrary container-query CSS. Actual
GitHub sanitization, proxying, and animation behavior require a reviewed deploy.

## Editing

Edit `config/profile.json`, then run the relevant generator in SETUP.md.
Header geometry is in `generate_header.py`; card layouts are in their matching
Python generator. Replace the silk texture via `--texture path/to/image.png`.
The two previous assets `assets/header.svg` and `assets/web-experiments.svg` are
preserved unchanged and no longer referenced by the new README.
