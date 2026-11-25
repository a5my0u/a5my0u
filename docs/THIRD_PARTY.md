# Third-party assets and licenses

Reviewed on 2026-11-25. This document covers the technology-logo subsystem only;
other project dependencies are documented in SETUP.md and AUTOMATION.md.

## Vendored icon source

Fourteen SVG logo silhouettes are vendored from the official
[Simple Icons repository](https://github.com/simple-icons/simple-icons) at the
verified revision `d59bb32d4f94b1aa8c7cef9d264280d35d5f8f97`.
The exact asset URLs, original source URLs, original brand colors, display colors,
individual license metadata and SHA-256 hashes are recorded in
`assets/icons/metadata.json`. No CDN is needed at render time.

Simple Icons is distributed under CC0-1.0. A copy of its license and disclaimer
is included in `assets/icons/SIMPLE_ICONS_LICENSE.md` and
`assets/icons/SIMPLE_ICONS_DISCLAIMER.md`. The CC0 dedication applies to the icon
collection's rights; it does not grant or waive third-party trademark rights.
The [Simple Icons disclaimer](https://github.com/simple-icons/simple-icons/blob/d59bb32d4f94b1aa8c7cef9d264280d35d5f8f97/DISCLAIMER.md)
explicitly distinguishes these rights.

The icons identify technologies used by the profile owner. They are secondary to
the profile identity, are not the user's own logo, and do not imply endorsement.
Silhouette geometry and aspect ratios are preserved, without glow, animation,
gradients or decorative effects. Fill colors follow the source's brand metadata.
GitHub uses the official white color alternative for contrast on charcoal;
[GitHub's brand toolkit](https://brand.github.com/foundations/logo) permits
white/black logo forms and emphasizes high contrast. The local icon remains in
its source form; the permitted display fill is applied by the card renderer.

## Specific attributions

| Asset | Attribution / terms |
| --- | --- |
| Git | Git logo by Jason Long, [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/), obtained through Simple Icons. Geometry is unchanged; rendered at a smaller size in the supplied brand red. [Official logo source](https://git-scm.com/community/logos). |
| HTML5 | HTML5 logo by W3C, [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/), obtained through Simple Icons. Geometry is unchanged; rendered at a smaller size in the supplied brand orange. [Official logo and license](https://www.w3.org/html/logo/). |
| JavaScript | The community JS logo is MIT licensed; the pinned origin is recorded in the metadata. Its original copyright and permission notice are retained in `assets/icons/JAVASCRIPT_LICENSE.txt`. [Pinned license](https://github.com/voodootikigod/logo.js/blob/1544bdeed6d618a6cfe4f0650d04ab8d9cfa76d9/LICENSE). |
| Python | Python and the two-snakes logo are trademarks of the Python Software Foundation. The [official logo page](https://www.python.org/community/logos/) permits use to identify use of Python; no endorsement is claimed. |
| NumPy | [NumPy press kit](https://numpy.org/press-kit/) and [logo guidelines](https://github.com/numpy/numpy/blob/main/branding/logo/logoguidelines.md). The original brand color is retained; the nearby text label supplies the readable identification on a dark background. |
| GitHub | GitHub and Invertocat are GitHub, Inc. trademarks. [Logo usage and color guidelines](https://brand.github.com/foundations/logo). |
| PyTorch, scikit-learn, pandas, Jupyter, Spring Boot, Thymeleaf, Google Colab, pytest | Source and available brand-guideline links are retained per logo in `assets/icons/metadata.json`. No additional trademark license is asserted. |

## Text-only entries

No unrelated or invented icon substitutes are used. These technologies are
rendered as their exact names:

| Technology | Reason |
| --- | --- |
| Java / Oracle Database | Oracle-logo redistribution and trademark permissions were not established for these composite portfolio cards. |
| Visual Studio Code | The [official guidelines](https://code.visualstudio.com/brand) disallow icon/name lockups and adding a background to the icon. The product name is used without an icon. |
| C | No single standards-body-owned language logo was verified; the pinned icon set's mark is community-sourced. |
| SQL | A language standard, not a specific database vendor. |
| CSS3 | The pinned set provides the newer CSS logo, not a CSS3 mark. The requested technology is not silently relabeled. |
| Matplotlib / LightGBM / CatBoost | A logo with verified redistribution terms was not included in the vetted asset set. Text keeps these technologies represented without making a rights claim. |

The text-only decision is limited to this asset bundle. It does not assert that a
technology has no logo or that all uses of its logo are prohibited.

## Maintenance

`python scripts/generate_tech_stack.py` regenerates the four cards from
`config/profile.json` and the local icons. It performs no network requests.
Every logo file is checked against its recorded hash. If replacing an icon,
review the new source and terms and update its metadata and hash together.
An unrecognized technology fails clearly rather than substituting a random logo.

All four cards are 560 × 382 pixels. Use ordinary adjacent `img` elements at a
nominal width of 410 pixels in README so they wrap on narrow screens; do not put
them in a fixed two-column HTML table. Labels are 24px in the SVG, and exact
technology names should also be available in the image alt text.
