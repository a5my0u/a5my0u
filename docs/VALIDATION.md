# Validation record

Review date: 2026-11-25 JST. This record distinguishes local verification from
the still-unperformed GitHub deployment.

## Automated checks

`python -m pytest -q`: **68 passed** on Windows / Python 3.14.

Covered behaviors include pagination, duplicate/incomplete responses, public
scope filtering, inclusive date boundaries, retries/timeouts/rate limits,
authentication errors, empty repositories, missing values, language aggregation
and rounding, XML rendering, deterministic outputs, mobile calendar count
preservation, rollback after write failure, nonnumeric initial placeholders,
rejection of active/external generated SVG content, workflow YAML/triggers/
permissions/pins, and local Git history/no-change commit suppression.

Tests use clearly labeled fixtures in `tests/`; production assets use the
separately acquired `assets/generated/public-data.json`. The local Git test uses
a temporary repository and never pushes or contacts GitHub.

`python scripts/publish_generated.py` (without `--publish`) successfully validates
the complete seven-file generated set. No data is sent by this default command.
Rebuilding from the same snapshot reports no changed generated assets.

## Real public snapshot

Public REST requests succeeded without a token. The snapshot as-of date is
2026-11-24 UTC and covers 2025-11-25 through 2026-11-24 inclusive. This is a saved
snapshot, not a claim that the currently viewed profile has refreshed today.

| Value | Result |
| --- | --- |
| Included owned public repositories | 1 |
| Scoped commits / opened PRs / opened issues | 0 / 0 / 0 |
| Current stars | 0 |
| Language bytes | HTML 1,254; JavaScript 990; CSS 557 |
| Displayed shares | 44.8%; 35.3%; 19.9% |
| Calendar | 365 verified dates; 0 scoped events |

The profile repository and its generated updates are excluded. The difference
from native GitHub totals is intentional and documented in the README.

## Browser review

Chrome rendered the actual README through a local Markdown preview at:

- 1280 × 900 desktop viewport, dark and light surfaces.
- 390 × 844 mobile viewport, dark surface.
- 320 × 844 minimum mobile viewport, light surface.
- 1200 × 420 standalone header and 320 × 844 standalone mobile snake.

Checked card wrapping, font sizes, no text overlap, full-width containment,
loaded images, light-theme legibility, and selectable Markdown prose. Browser
DOM checks reported no document horizontal overflow or unloaded images in the
tested main profile widths. Screenshot pixel width can exclude the scrollbar.

The initial desktop month labels overlapped at the partial first month; label
spacing was corrected. Mobile KPIs/languages use separate 320px designs. The
snake was also split into readable week blocks for mobile. Four technology
cards wrap without forcing fixed HTML table columns.

Header screenshots taken at different times showed changed pixels only in the
right reflection area (difference bounding box x=648–1200, y=0–320); the left
text region was identical. The moving snake was visually observed at different
calendar positions, with computed transforms changing and gold segments visible.
Reduced-motion rules and static SVG structure are covered by code inspection
and tests; OS-level reduced-motion switching was not exercised.

Some very dark official brand marks have low contrast on their charcoal plates;
their adjacent names remain legible. Brand colors were preserved rather than
inventing unapproved logo colors. Serif/custom web fonts are not required.

## Not yet verified

- GitHub's actual sanitizer, image proxy and caching for these new SVGs.
- Header texture embedding and SVG motion when served inside GitHub README.
- `picture` media switching and reduced-motion fallback on the live profile.
- Actions execution on Ubuntu/Python 3.13, repository write policy, first branch
  creation, scheduled/manual remote execution, and authenticated remote push.
- Current internship status and achievement publication permission.

These require owner review and, for platform behavior, an approved deployment.
No live GitHub success is claimed. Desktop/mobile screenshots are local previews.
