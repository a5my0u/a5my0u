# Deployment

The profile owner approved publication on 2026-11-25 JST.
The source preserves the previous assets and commit history. Local review files
and unconfirmed biography entries are excluded from this public repository.

## Initial update verified

[Initial Actions run](https://github.com/a5my0u/a5my0u/actions/runs/45615640221)
completed successfully on 2026-11-25. Its test, public API fetch, SVG rendering,
and asset publication steps all succeeded on Ubuntu / Python 3.13.
The `profile-assets` branch contains all six expected SVGs and `public-data.json`.
The initial automated snapshot is dated 2026-11-25 UTC and includes 365 days.

The README now references that branch for both desktop images and mobile
picture sources. Failed future runs retain the last successful branch version.
The user-approved one-time push trigger was removed after this successful run.
The only remaining triggers are the daily `0 23 * * *` UTC schedule
(approximately 08:00 JST the next day) and `workflow_dispatch`.

The owner confirmed being a third-year undergraduate student; the configuration
and generated English introduction both reflect that information.

The live initial profile was checked at desktop and mobile widths, including
image loading and responsive picture selection. See SETUP.md for maintenance;
VALIDATION.md records the earlier local validation and pre-deployment limitations.
