# Featured Projects audit

Audit date: 2026-10-23. Changes are local; nothing was pushed.

## README changes

- Kept the existing two-row, two-column HTML table, project ordering, technology code badges, and action-button images.
- Updated Amazon Clone's demo and preview link to `https://myecommerce-project-clone.vercel.app/`. Its description, technology stack, and repository URL are unchanged.
- Replaced the Rock Paper Scissors card with Bodhi Sakha, including a concise source-backed description and technology stack.
- Added linked, 300 px wide previews directly below all four titles. Each asset is an 800 × 450 WebP with transparent rounded corners baked into the image; no CSS or JavaScript is required.
- All README content outside Featured Projects remains byte-for-byte unchanged.

## Screenshot provenance and limitations

Fresh browser captures were attempted with cached Playwright and the installed Google Chrome. Chrome exited during launch with SIGABRT/EPERM before opening a page. External hosts also failed DNS resolution in the terminal. Existing real screenshots were therefore reused, rather than generating images or adding placeholders.

The source files remain untouched. These are historical interface captures, not proof of the current deployments' appearance or availability.

| New file in `assets/project-previews/` | Existing source | Processing | Bytes |
| --- | --- | --- | ---: |
| `kaushal-nexus.webp` | Sibling `PortFolio/public/images/KaushalNexus-dashboard.png` | Homepage capture cropped to 16:9 | 32,466 |
| `amazon-clone.webp` | Sibling `PortFolio/public/images/amazon-clone.png` | Removed browser toolbar; cropped storefront to 16:9 | 46,882 |
| `leetcode-solutions.webp` | Pictures: `Screenshot 2026-10-15 at 7.51.39 PM.png` | Cropped GitHub repository's Graphs directory, removing browser chrome and macOS dock | 36,110 |
| `bodhi-sakha.webp` | Sibling `PortFolio/public/images/bodhi-sakha.png` | Preserved entire chat interface with narrow white side padding to fit 16:9 | 14,566 |

The Amazon source image shows the old `amazon-clone-beta-bay.vercel.app` deployment in its original toolbar; that toolbar was removed. It cannot establish visual parity with the new deployment. The LeetCode preview shows the actual repository's Graphs directory, not its root homepage or dashboard. Fresh captures of the new Amazon deployment and LeetCode repository homepage remain desirable follow-ups when browser access is available. Small thumbnail text is inherently limited; clicking a preview opens its project.

## Bodhi Sakha evidence

The local checkout at sibling `React Basics/basic-chatbot` identifies itself as Bodhisakha and explicitly documents `https://bodhi-sakha-phi.vercel.app/` as its production URL. Its README and Git `origin` both identify `https://github.com/calligraphyguruji/basic-chatbot` as the source repository. The latest local commit is `4e8129f` (2026-10-11), titled `docs: update production url to bodhi-sakha-phi.vercel.app`.

The stack was checked against that checkout's `package.json`: React 19, Vite, Express 5, Google Gemini SDKs, and PostgreSQL (`pg`). Source evidence includes:

- `src/components/Chatbot.jsx`: streamed-response reader and Deep Thinking control.
- `src/components/Sidebar.jsx`: conversation history and search.
- `server/endpoints/chat.js`: Gemini client and `generateContentStream`.
- `server/endpoints/files.js`: PDF and DOCX extraction with `unpdf` and `mammoth`.
- `server/endpoints/lib/db.js`: PostgreSQL connection pool, with local-storage fallback when no database URL is configured.

The portfolio separately lists a `bodhi-sakha` repository URL and contains conflicting project metadata. The card uses the actual source checkout's remote and README instead. Public accessibility and any subsequent repository rename could not be verified. No deployed chat, upload, authentication, or database behavior was tested; the description is based on source and the existing screenshot, not a live functional test.

## Project destinations and access checks

| Project | Demo | Repository | Result |
| --- | --- | --- | --- |
| KaushalNexus | https://kaushal-nexus.vercel.app | https://github.com/calligraphyguruji/Kaushal-Nexus | Repository readable through web tool; demo unavailable through tool |
| Amazon Clone | https://myecommerce-project-clone.vercel.app/ | https://github.com/calligraphyguruji/myecommerce-project-clone | Demo unavailable through tool; repository fetch returned cache miss; repository link preserved |
| LeetCode Problem Solutions | None; repository-only project | https://github.com/calligraphyguruji/LeetCode-Questions | Repository readable through web tool |
| Bodhi Sakha | https://bodhi-sakha-phi.vercel.app/ | https://github.com/calligraphyguruji/basic-chatbot | Demo unavailable through tool; repository fetch returned cache miss; identity verified locally |

The old Amazon and Rock Paper Scissors demos and Rock Paper Scissors repository were also checked; the web tool could not fetch them. A tool failure or DNS restriction does not prove that a destination is broken. Live HTTP availability of the demos, Amazon repository, Bodhi Sakha repository, and external button/badge images remains unverified.

## Validation

Passed local checks:

- One Featured Projects section; one balanced table with two rows and four cells.
- Four preview references resolve to valid local WebP files, all exactly 800 × 450 and below 150 KB.
- Every local image reference throughout the README exists.
- Preview links and button links match the destination table above.
- Amazon's old demo URL and all Rock Paper Scissors content are absent from Featured Projects.
- Existing descriptions for KaushalNexus, Amazon Clone, and LeetCode are unchanged.
- Other README sections are byte-for-byte unchanged against Git HEAD; no workflows, heatmaps, statistics, or tracking files were edited.
- `git diff --check` passed. The Impeccable mechanical scan returned no findings for `README.md`.
- The optimized screenshots were visually inspected as images.

GitHub browser rendering and desktop/mobile layout were **not verified**. The preserved table uses supported HTML attributes and relative images, but GitHub may horizontally scroll a two-column table on narrow mobile screens. No unsupported responsive CSS was added. Actual browser review remains necessary before claiming visual verification.

## Remaining manual checks

1. Open the three demos and confirm their current availability and appearance.
2. Confirm the publicly accessible Bodhi Sakha repository is still `basic-chatbot`; update it only if the project was renamed or moved.
3. Capture the new Amazon deployment and the LeetCode repository root/dashboard when browser access is available; refresh other historical captures if needed.
4. Review the edited README on GitHub at desktop and mobile widths, including external badge images.
