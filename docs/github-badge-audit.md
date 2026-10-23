# GitHub profile badge audit — 2026-10-21

## 1. Root cause analysis

| Component | Root cause / finding | Evidence | Status |
| --- | --- | --- | --- |
| Followers | No defect found. Existing native Shields route works. | HTTP 200, SVG `FOLLOWERS: 4`; GitHub public user API returns `followers: 4`. | Preserved byte-for-byte. |
| Stars | Screenshot shows an image delivery failure, but it is not currently reproducible. No incorrect route, username, or metric was found. The original origin and original GitHub Camo URL both return valid `STARS: 15`. | HTTP 200 and `image/svg+xml` for both paths; summing `stargazers_count` over all 16 public owned repositories also yields 15. | Existing service retained; OWNER scope and caching made explicit. Exact historical delivery failure remains unproven. |
| Repositories | A transient error occurred in the Shields badge path, not an invalid GitHub field or username. The original URL first returned an error SVG, then recovered without any source change. | At 16:07:22 UTC the original URL returned HTTP 200 with `REPOSITORIES: INVALID`; GitHub's API returned `public_repos: 16`. At 16:11:15 UTC the identical original URL returned `REPOSITORIES: 16`. | Supported equivalent selector and cache policy applied; final origin and GitHub Camo return 16. |

The exact internal reason Shields originally produced `invalid` is not exposed
in its HTTP response or `.json` diagnostic response. The evidence is consistent
with a temporary upstream/service/cache failure. It does **not** establish a
GitHub rate limit, bad authentication, deprecated service, or malformed JSONPath.
In particular, the original `$.public_repos` syntax is valid: a minimal badge
using it returned 16, as did the original full URL when retried. Bracket notation
is an equivalent supported selector, not a correction of invalid JSONPath.

No claim is made that these small changes can permanently eliminate third-party
outages. They provide a fresh stable badge identity and an explicit cache policy,
while retaining the working services and metrics. A larger scheduled SVG
publishing system is not justified by the observed transient incident.

### Repository scope inspected

Original tracked structure:

```text
README.md
.github/workflows/update-leetcode.yml
scripts/update-leetcode.mjs
assets/leetcode-streak.svg
```

All four files were read. The script and hourly workflow exclusively fetch
LeetCode data and update the LeetCode card/badges; they do not generate the three
GitHub header badges. The tracked inventory and hidden-file scan found no other
profile automation, environment/configuration files, dependency manifests, or
badge generators. No private environment values or credentials were read.

The knowledge graph was consulted and coverage checked. The SVG is excluded
from graph indexing and was read directly. No index completeness claim is made.
The existing uncommitted LeetCode badge URL change from the earlier task was
preserved exactly.

### Rendering and metric trace

```text
README centered <p> with three clickable <a>/<img> elements
  → GitHub Markdown sanitization and Camo image proxy
  → img.shields.io badge route
  → GitHub data
  → SVG returned through Camo to the browser
```

- Followers: `/github/followers/calligraphyguruji` uses Shields' maintained
  GitHub integration; public API comparison uses `/users/calligraphyguruji`.
- Stars: `/github/stars/calligraphyguruji` invokes Shields'
  `GithubTotalStarService`, which queries GitHub GraphQL and sums stargazers over
  repositories with OWNER affiliation. It measures stars **received** by owned
  repositories, not repositories the user has starred and not just the profile
  repository. Shields caps the calculation at the 200 most-starred repositories;
  there are currently 16 public owned repositories, so the cap does not affect
  this comparison. Forks are not silently excluded from the owned-repository sum.
- Repositories: `/badge/dynamic/json` retrieves
  `https://api.github.com/users/calligraphyguruji`, extracts `public_repos`, and
  renders it. This is a public repository count; it excludes private repositories.

Sources: [Shields user-stars contract](https://shields.io/badges/git-hub-users-stars),
[Shields stars implementation](https://github.com/badges/shields/blob/master/services/github/github-total-star.service.js),
[dynamic JSON contract](https://shields.io/badges/dynamic-json-badge),
[dynamic JSON implementation](https://github.com/badges/shields/blob/master/services/dynamic/json-path.js),
[GitHub public user API](https://docs.github.com/en/rest/users/users#get-a-user),
[GitHub image proxy](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-anonymized-urls).

## 2. Files modified

- `README.md`: exactly two header image URLs changed in this task. Stars now
  explicitly uses `affiliations=OWNER`. Repositories uses `$['public_repos']`.
  Both request `cacheSeconds=3600`. No numbers are embedded in either badge URL.
  Colors, labels, existing logo, image attributes, order, anchors, spacing, and
  centered container remain unchanged. Followers is untouched.
- `docs/github-badge-audit.md`: this report, including the observed recovery and
  limitations rather than an unsupported claim about the provider's internals.

No workflow, script, generated asset, profile information, or other README
section was changed. No new production dependency or secret was introduced.

## 3. Before versus after

### GitHub Stars

Before:

```html
<img src="https://img.shields.io/github/stars/calligraphyguruji?label=Stars&style=for-the-badge&color=0e75b6" alt="GitHub Stars"/>
```

After:

```html
<img src="https://img.shields.io/github/stars/calligraphyguruji?affiliations=OWNER&label=Stars&style=for-the-badge&color=0e75b6&cacheSeconds=3600" alt="GitHub Stars"/>
```

### GitHub Repositories

Before:

```html
<img src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Fusers%2Fcalligraphyguruji&query=%24.public_repos&label=Repositories&style=for-the-badge&color=0e75b6&logo=github" alt="GitHub Repositories"/>
```

After:

```html
<img src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Fusers%2Fcalligraphyguruji&query=%24%5B%27public_repos%27%5D&label=Repositories&style=for-the-badge&color=0e75b6&logo=github&cacheSeconds=3600" alt="GitHub Repositories"/>
```

## 4. Test results

All requests below were actually made using Postman CLI 1.75.0, without an
Authorization header. Curl DNS resolution failed for GitHub and Shields in this
sandbox; Postman's request client successfully reached them. The badge checks
validate SVG content and its value, not HTTP 200 alone.

| Test | Observed result | Status |
| --- | --- | --- |
| Followers value | Origin and GitHub Camo: HTTP 200, `FOLLOWERS: 4`; GitHub API: 4. | Passed |
| Stars value and intended metric | Updated origin and GitHub Camo: HTTP 200, `STARS: 15`; owned-repo REST sum: 15. All 16 repositories fit on one page; no next-page link was present. | Passed |
| Public repository value | Updated origin and GitHub Camo: HTTP 200, `REPOSITORIES: 16`; public user API: 16; owned-repository list length: 16. | Passed |
| Actual image responses | All six final origin/Camo responses have `image/svg+xml`, parse as XML/SVG, contain numeric labels, and contain no script nodes. | Passed |
| Consistent appearance | All SVGs are 28px tall, with label fill `#555` and value fill `#0e75b6`. Existing `for-the-badge` parameters and logo are preserved. | Passed by SVG inspection; no pixel screenshot comparison performed. |
| GitHub rendering | Sent the updated header to `POST https://api.github.com/markdown` in GFM mode. HTTP 200; all three images/anchors and centered paragraph preserved, Camo URLs generated, responsive `max-width: 100%` retained. Then fetched those Camo URLs and checked their SVGs. | Passed |
| Cache policy | Updated Stars and Repositories origins returned `Cache-Control: max-age=3600, s-maxage=3600`. Followers remains at the existing 1800-second policy. | Passed |
| Scope and credentials | Comparing against the start-of-task README changes only the two intended `src` attributes. Followers and the prior LeetCode change are identical. No auth/token query parameters were introduced. Workflow, script, and SVG bytes still match HEAD. | Passed |
| Whitespace | `git diff --check`. | Passed |
| Future live statistic changes | URLs still resolve live data and contain no fixed statistics, but no repositories/stars/followers were changed to manufacture a test. | Configuration verified; future changes not empirically exercised. |
| Published profile after these edits | No commit or push was performed. | Not tested; local changes only. |

The original Repositories `invalid` and subsequent recovery were both observed
**before** editing README. Its earlier error response advertised a 120-second
cache lifetime; the later identical URL returned numeric data. The original
Stars origin and original Camo URL both worked during the audit, so no historical
Stars HTTP status or provider error can be asserted.

A first GitHub renderer request failed with HTTP 400 because Postman's `--body
@file` invocation sent multipart data. It was corrected to a literal JSON body;
the final request returned HTTP 200 and its Camo responses passed all checks.
Some compound/redirected Postman invocations failed with a local keychain error;
only successful direct invocations and their saved responses support the checks
above.

## 5. Long-term reliability

The badges remain dynamic. No login is required to view them, and no repository
secret, custom token, deployment, or new GitHub Actions workflow is required.
Shields maintains its GitHub-backed integrations; the generic repository badge
still depends on an upstream public GitHub REST response. The services remain
subject to GitHub limits, Shields availability, CDN caching, and Camo caching.
A one-hour cache policy reduces repeat requests; it is not an uptime guarantee
or a promise that every upstream update appears within exactly one hour.

The bracket selector and OWNER parameter are stable and meaningful. No random
cache-busting parameter, repeated purge, statistic hardcoding, metric
substitution, new badge service, or new API polling infrastructure was added.

If failures become persistent, capture the badge body, headers, and direct API
response at the same time. Reconsider authenticated scheduled SVG generation
only if that evidence demonstrates sustained failures. At this audit's end,
all final origin and GitHub-rendered proxy badges return correct counts, but the
modified README has **not** been published to the profile.
