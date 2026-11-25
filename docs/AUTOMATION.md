# Public analytics and update design

## Exact data scope

`fetch_github_data.py` uses GitHub REST public endpoints and API version
`2026-03-10`. It does not use authenticated-user repository lists or a calendar
that may combine private contribution aggregates with public activities.

| Metric | Definition |
| --- | --- |
| Commits | Unique SHA values authored by this account on default branches of owned public, non-fork, non-archived repositories, excluding the profile repository. The UTC Git committer date defines the window. |
| Pull requests | Public PRs opened by this account during the window, across public repositories; profile repository excluded. Reviews/comments are excluded. |
| Issues | Public issues opened by this account during the window, across public repositories; PRs and profile repository excluded. |
| Stars | Current total stars on the included owned public repositories; a lifetime stock, not yearly activity. |
| Languages | Sum of GitHub language-byte totals on those repositories. Notebook/generated code can dominate; configurable exclusions apply. |
| Snake cells | Daily commits + opened PRs + opened issues under the above scopes. This is not the native GitHub contribution total. |

The inclusive window is 365 UTC calendar dates ending on the printed as-of date.
The current date is a partial day if the update happens before midnight UTC.
Language shares show the top five languages plus Other when needed; deterministic
largest-remainder rounding makes the displayed one-decimal percentages sum to
100.0%. An empty successful language response means no measured code, while a
failed request never becomes an empty response or zero metric.

Relevant official API references: [commits](https://docs.github.com/en/rest/commits/commits),
[repositories and languages](https://docs.github.com/en/rest/repos/repos),
[search](https://docs.github.com/en/rest/search/search).

## Fetch and failure behavior

- List endpoints paginate. Search intervals exceeding the 1,000-item cap are
  split by date; an unsplittable day fails rather than silently undercounting.
- Timeouts, rate limits and temporary errors have bounded retries. A long rate
  reset fails safely instead of waiting indefinitely. Auth failures are errors.
- Public repository metadata and matching authors are checked before counting.
- Missing fields, duplicate results, incomplete searches and malformed SVGs fail
  the update. Missing numbers are never converted to zero.
- All output is generated and validated before replacing files. Local I/O errors
  trigger rollback; remote publication is a separate single-reference update.
- First-time failures create only explicit, nonnumeric local placeholders for
  missing SVGs. The command still fails, so placeholders are not published.
- Known-good assets are retained after failure. The live README remains pointed
  at the last successful assets-branch commit.

## Publication

`publish_generated.py` validates only unless explicitly passed `--publish`.
The workflow is the intended caller after approved deployment. It writes only
the seven named generated files to `profile-assets`, using the Actions bot
identity. It preserves the branch's other files and commits only if its tree
changes. A non-forced push updates a single reference; a competing branch
advance is rejected rather than overwritten. Workflow concurrency prevents
overlapping scheduled/manual jobs in this repository.

Bot commits are outside the default branch and use the bot identity. The entire
profile repository is also excluded from this dashboard's statistics, avoiding
self-generated activity. Snapshot dates legitimately change daily; identical
same-day renders cause no extra commit.

Tokens are only environment values, used for api.github.com requests and a
GitHub-specific Git HTTP header. They are not put in URLs or persisted in the
repository. Error messages intentionally omit raw remote responses and Git
stderr, which could contain authentication context.

## Snake decision

The official [Platane/snk repository](https://github.com/Platane/snk) was reviewed
at `a041d6c27ba561a39f5be9c26a784812765e434b`. Its calendar input and distribution
did not provide the required independently verified public-only scope and clear
license basis for this bundle. A clear repository license was not found in that
review; this is a limited observation, not a claim about every historical release.

An original small Python renderer therefore consumes the same public snapshot as
the KPIs. No Platane code, action, or dependency is included. The calendar keeps
real date positions, scales emerald cell intensity to real positive counts, and
animates a gold snake that temporarily clears cells. Real zero-activity data
stays empty. Reduced motion preserves the calendar without the moving snake.

## Actions supply chain

Official action revisions were pinned during implementation:

- `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1` (v7.0.1, MIT)
- `actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0` (v7.1.0, MIT)

Static header/logo assets are not rebuilt by the daily job. No third-party stats
image service, private API data, 3D library, or extra secret is required.
Workflow YAML and local behavior have been tested; actual GitHub runner,
permissions, remote push and image proxy behavior remain deployment checks.
