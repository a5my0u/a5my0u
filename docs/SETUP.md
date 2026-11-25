# Setup and maintenance

This repository contains the reviewed Obsidian Emerald profile source.
Local review screenshots and unpublished biography drafts are intentionally not
part of the public repository. See DEPLOYMENT.md for live deployment status.

## Local setup

Use Python 3.13 or newer and Git. Tested locally with Python 3.14. The workflow
targets Python 3.13 on Ubuntu; execution on that runner remains unverified.

```sh
python -m venv .venv
# Activate .venv using your shell's normal activation command.
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q
```

The scheduled fetch/render pipeline itself uses Python's standard library.
Pillow is only needed when preparing a replacement texture. Pytest/PyYAML are
test dependencies; markdown-it-py builds the offline preview.

## Build and preview

Run commands from this repository root:

```sh
python scripts/generate_header.py
python scripts/generate_tech_stack.py
python scripts/generate_readme.py
python scripts/update_profile.py
python scripts/build_preview.py
```

Open `previews/profile-dark.html`, `previews/profile-light.html`, or
`previews/header.html`. For a local web preview:

```sh
python -m http.server 8766 --bind 127.0.0.1
```

To reproduce the shipped analytics without network access:

```sh
python scripts/update_profile.py --snapshot assets/generated/public-data.json
```

Do not edit the generated README or SVGs by hand. Change the config/source and
regenerate. The default README references the included local assets, so it is
usable before an assets branch exists.

## Initial deployment — only after owner approval

1. Review the README, screenshots, pending biography items and workflow.
2. Apply the files on a reviewed work branch in `a5my0u/a5my0u`. Preserve the
   existing source files and commit history. Do not upload the `previews/`
   directory, local environments, caches, or secrets.
3. After the owner approves the change to the default branch, install the
   workflow there. Keep the local-image README for this first deployment.
4. Run **Update public profile assets** manually in Actions. A successful run
   creates `profile-assets` with all seven generated files in one Git commit.
5. Verify those raw assets and the workflow result, then run:

   ```sh
   python scripts/generate_readme.py --generated-branch profile-assets
   ```

6. Review and deploy that README change. It now reads the updating images from
   the assets branch. Check the live profile at desktop/mobile widths and in
   both themes. Inspect header motion, embedded texture, image proxy caching,
   mobile picture sources, and reduced-motion fallback.

This order prevents initial broken raw URLs. Do not switch the README to the
assets branch before it has a successful complete generation.

## Authentication and settings

Public API reads can work without a token, as verified for the shipped snapshot.
Actions supplies its built-in `GITHUB_TOKEN` to increase the rate limit and
publish to the same repository. No personal token or extra repository secret is
required by this implementation. The job requests `contents: write`; repository
or organization policy must allow that permission and writes to `profile-assets`.
If policy blocks it, review the precise policy failure instead of adding a broad
personal token. Never put a token in config, README, a command argument, or a log.

The cron is `0 23 * * *`: 23:00 UTC, approximately 08:00 JST the next day.
GitHub scheduled runs are best effort, so exact execution time is not guaranteed.
The schedule needs the workflow on the default branch. Manual execution is also
enabled. [GitHub schedule documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).

## Content changes

| Change | Location / command |
| --- | --- |
| Bio, experience, palette, tech list | `config/profile.json`; regenerate affected static assets and README |
| Current internship | Confirm dates/current status, then set `publish: true`, `confirmation_required: false` |
| Achievement | Confirm exact work, numbers, phrasing and permission; add approved `text` and change both flags |
| Featured projects | Add up to four verified public entries with `repository`, `visibility: public`, `description`, `technologies` |
| Repository/language exclusions | `analytics.exclude_repositories`, `exclude_languages`; rerun update |
| Header texture | `python scripts/generate_header.py --texture path/to/texture.png` |
| Icon replacement | Verify source/terms, replace local SVG and update the metadata hash; regenerate tech cards |
| Scheduled time | Edit workflow cron in UTC; review and deploy |

If the live README uses `profile-assets`, pass `--generated-branch profile-assets`
each time you regenerate it. The default is intentionally the safe local mode.

## Dependency licenses

| Component | Version / revision | License and purpose |
| --- | --- | --- |
| Pillow | 12.0.0 | HPND / Pillow license; local texture preparation |
| pytest | 9.1.1 | MIT; tests |
| PyYAML | 6.0.3 | MIT; workflow syntax tests |
| markdown-it-py | 4.0.0 | MIT; offline HTML preview |
| mdurl | 0.1.2 (transitive preview dependency) | MIT; URL parsing |
| actions/checkout | v7.0.1, pinned SHA in workflow | MIT; source checkout |
| actions/setup-python | v7.1.0, pinned SHA in workflow | MIT; runner Python |
| Simple Icons | pinned revision in THIRD_PARTY.md | CC0 collection plus brand-specific rights |

Upstream licenses: [Pillow](https://github.com/python-pillow/Pillow/blob/12.0.0/LICENSE),
[pytest](https://github.com/pytest-dev/pytest/blob/main/LICENSE),
[PyYAML](https://github.com/yaml/pyyaml/blob/main/LICENSE),
[markdown-it-py](https://github.com/executablebooks/markdown-it-py/blob/master/LICENSE),
[mdurl](https://github.com/executablebooks/mdurl/blob/master/LICENSE),
[checkout](https://github.com/actions/checkout/blob/main/LICENSE),
[setup-python](https://github.com/actions/setup-python/blob/main/LICENSE).

The project does not add a blanket open-source license to the owner's profile
or imply that third-party trademarks are freely licensed. Icon attribution and
the available source notices are retained in THIRD_PARTY.md and assets/icons/.
