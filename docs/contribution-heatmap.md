# Numbered GitHub contribution heatmap

The profile embeds `assets/github-contribution-heatmap.svg`. The Python generator
uses only the standard library and GitHub's official GraphQL API. There are no
runtime packages, JavaScript, external fonts, or remote resources in the SVG.

## Repository audit

The existing repository contains the profile README, `assets/leetcode-streak.svg`,
`scripts/update-leetcode.mjs`, `.github/workflows/update-leetcode.yml`, and the
existing badge audit in `docs/github-badge-audit.md`. `postman/` was an empty
local directory. There is no existing GitHub contribution-calendar generator or
GitHub contribution-data cache.

The README uses github-readme-stats-fast for statistics and languages,
streak-stats.demolab.com for the GitHub streak, and github-activity-graph.vercel.app
for a line activity graph. These remain intact. The line graph is a different
visualization; only one numbered GitHub calendar section was added. The LeetCode
calendar, local streak SVG, badge URLs, and all other sections remain intact,
including the pre-existing uncommitted README edits.

The existing hourly LeetCode workflow queries LeetCode GraphQL and updates its
SVG and README badges. It is unchanged. The new workflow updates only the GitHub
heatmap SVG. The existing Shields badges request caches of 3,600 seconds; other
remote cards and GitHub's image proxy have service-controlled caching. The new
SVG itself is the last successful snapshot, retained on any fetch/validation
failure. No API response or credential is committed by the workflow.

Codebase-memory graph tools were unavailable in this session; repository files
and hidden workflow directories were inspected directly. No graph coverage or
generation claim is made.

## Data contract and calendar boundaries

The query in `scripts/generate_contribution_heatmap.py` requests:

```graphql
query ContributionHeatmap($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays { date contributionCount contributionLevel }
        }
      }
    }
  }
}
```

The period is today in UTC plus the preceding 364 days, including leap days.
`from` is midnight UTC; `to` is the current UTC instant. Today is partial and
may change. Returned `date` strings are authoritative and never converted to
local timestamps. Sunday is the top row, Saturday the bottom, and weeks advance
left to right. Partial first/last weeks have no invented cells outside the period.

Before rendering, the generator checks the complete returned calendar's daily
sum against `totalContributions`, rejects duplicate/invalid dates and counts,
and requires every one of the selected 365 dates. Extra API boundary dates are
trimmed; the displayed total is always the sum of the selected dates. If the
API returned additional nonzero boundary dates, its full-range total could be
larger than the selected-period total. Counts are never inferred from colors.

Positive counts are ranked into nearest-rank quartile thresholds. Equal counts
always receive equal colors; tied distributions may use fewer than four green
shades. GitHub's `contributionLevel` is fetched and validated, while displayed
intensity is computed from this selected period's distribution. Zero cells are
empty; positive values have centered numerical text, shrinking for longer counts.
Light text on the two darker greens and dark text on brighter greens preserve
contrast. Native SVG dimensions and a viewBox let GitHub scale the image to the
README width. On narrow mobile screens, a full-year calendar necessarily makes
the numbers small; visitors can open the SVG at its native size.

## Initial asset: real public-calendar snapshot

No GitHub token was available locally. The initial asset therefore uses actual
counts from GitHub's own public calendar, fetched through Postman CLI on
2026-10-23:

<https://github.com/users/calligraphyguruji/contributions>

The HTML contains dated cells and exact count tooltips. All 365 selected SVG
cells were compared to those dates/counts: **2025-10-24 through 2026-10-23,
1,093 contributions, 74 nonzero days, maximum 120**. GitHub's broader 370-day
calendar also totaled 1,093; the five trimmed days were zero. The SVG description
explicitly identifies this initial snapshot source. No random or test values
were used for the profile asset. The scheduled generator has no HTML scraping
fallback: its first successful authenticated run replaces this snapshot using
GraphQL, with the source description updated accordingly.

This public snapshot does not verify GraphQL authentication, private contribution
visibility, or equivalence to an owner's signed-in calendar. Live authenticated
GraphQL verification remains pending. The Postman Orbit discovery search did not
return a matching official GraphQL endpoint; GitHub's own schema was used.

## GitHub configuration and permissions

1. Commit and push these changes to the repository's default branch.
2. Ensure GitHub Actions is enabled. In Actions, select **Update GitHub
   Contribution Heatmap → Run workflow** to verify the first authenticated run.
3. The workflow explicitly requests only `contents: write`: it needs repository
   read access for checkout and write access to commit the SVG. All unspecified
   token permissions are disabled. It uses the automatically supplied
   `GITHUB_TOKEN` for public calendar queries and pushing; no new secret is
   normally needed. Organization policy or branch protection may still prevent
   direct bot pushes. Use your repository's permitted bot/PR policy if so.
4. If the default token is rejected for the calendar query, optionally create a
   repository Actions secret named **CONTRIBUTIONS_TOKEN** containing a personal
   token owned by `calligraphyguruji`. For public data, a fine-grained token with
   its inherent public read access is sufficient; do not grant repository write
   access to this query token. For private/internal contribution inclusion,
   GitHub documents the optional classic **`read:user`** scope on
   `contributionsCollection`. This publishes numerical private activity in a
   public SVG, so enable it only if intended. Owner/profile privacy settings and
   organization policies can affect visibility. Do not grant broad `repo` scope
   solely for this calendar. The separate `GITHUB_TOKEN` still performs pushes.

The workflow runs daily at **04:23 UTC (09:53 IST)** and supports manual runs.
GitHub may delay scheduled jobs and may disable schedules in inactive public
repositories. Run it manually/re-enable it if necessary.

Concurrency serializes this workflow's runs. The commit step stages only the
SVG, skips identical output, rebases competing branch updates, and retries
non-fast-forward pushes up to three times. It never force-pushes. An actual
same-file merge conflict fails for review. The existing LeetCode workflow does
not itself retry pushes and remains unchanged.

Transient network/5xx failures get bounded exponential retries. Rate-limit
headers are respected when their delay is at most 60 seconds; longer limits
fail the run for a later retry. GraphQL rate-limit errors fail safely as well.
Authentication errors fail immediately. Diagnostics omit tokens and raw response
bodies. Failure before a valid render never replaces the existing asset.

Local authenticated generation:

```bash
# Supply GITHUB_TOKEN securely through your environment; do not put it in this file.
python3 scripts/generate_contribution_heatmap.py
```

## Validation and repeatable tests

```bash
python3 -m unittest discover -s scripts/tests -v
# With actionlint installed:
actionlint .github/workflows/update-contribution-heatmap.yml
```

Six deterministic tests passed. They cover exact labels for zero, one-, two-,
and three-digit counts, all weekday endings, leap years, total validation,
missing/duplicate/invalid data, boundary trimming, SVG bounds/orientation,
XML escaping, and atomic/idempotent writes. Fixture values are test-only and
never used by production generation. The checked-in SVG was separately validated
against GitHub's real public calendar. Missing-token execution returned failure
and preserved the asset. `actionlint` 1.7.12 and `git diff --check` passed.

An optional Postman simulation exercises the actual Python HTTP client with
success, 401, 429, GraphQL errors, malformed JSON, repeated 503s, and a 503 recovery:

```bash
# Terminal 1 (requires Postman CLI 1.70+; no Postman account required):
postman simulation run postman/simulations/contribution-heatmap.sim.yaml --port 4900 --output ndjson
# Terminal 2:
HEATMAP_TEST_ENDPOINT=http://127.0.0.1:4900/github python3 -m unittest discover -s scripts/tests -v
```

The mock encodes the documented response shape with deterministic test counts;
no owner-hosted mock was searched because no Postman API credentials were
configured. The sandbox blocked binding localhost (`EPERM`), so the HTTP
simulation test was skipped here. It is included for execution outside the
sandbox; it is not claimed to have passed. Browser and Quick Look previews were
also blocked by the sandbox. XML and geometry checks passed. GitHub’s official Markdown rendering API
returned HTTP 200 and preserved the inline SVG image embed with
`max-width: 100%`; visual browser review remains pending. No workflow run, push, or deployed profile is claimed.

## Official references

- [GitHub GraphQL calendar fields and contribution visibility](https://docs.github.com/en/graphql/reference/users)
- [GraphQL authentication and requests](https://docs.github.com/en/graphql/guides/forming-calls-with-graphql)
- [GITHUB_TOKEN permissions](https://docs.github.com/en/actions/tutorials/authenticate-with-github_token)
- [GitHub Actions scheduled events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)
