
---

## `design_notes.md`
```markdown
# Design Notes

## Static vs JS Fallback
- Strategy: Fetch static HTML first using `httpx`. Parse it and extract sections. If the aggregated text length across parsed sections is small (< 300 characters) we consider the static fetch insufficient and fallback to Playwright for JS rendering.
- Rationale: Many marketing/SPA pages hide content until rendering; this heuristic keeps static fetch fast for plain sites and falls back only when needed.

## Wait Strategy for JS
- We use Playwright with `wait_until="networkidle"` as a primary wait.
- Additionally:
  - Small fixed sleeps when clicking overlays or after scrolls (0.5–1.0s).
  - When navigating to paginated pages we wait for `networkidle`.
- Details: After navigation we try to close overlays, click a few tab-like elements, perform `max_scrolls` scrolls (default 3), and look for `rel=next` or "Next" anchors to follow up to 2 pages.

## Click & Scroll Strategy
- Click flows implemented:
  - Heuristics that click elements matching `[role="tab"]`, `button:has-text('Load more')`, and common overlay close buttons.
- Scroll / pagination approach:
  - Execute `window.scrollTo(0, document.body.scrollHeight)` up to `max_scrolls` times. Wait 1s after each scroll.
  - Follow `a[rel='next']` and "Next" links up to 2 additional pages.
- Stop conditions:
  - Max scrolls (3), max paginated pages (3), and a navigation timeout (30s per navigation).

## Section Grouping & Labels
- Primary grouping: semantic landmarks (`header`, `nav`, `main`, `section`, `article`, `footer`).
- Fallback: group by top headings (`h1`–`h3`) and their parent containers.
- Label derivation:
  - Use the first heading in the section (if present).
  - If absent, derive label from first 5–7 words of the section text.

## Noise Filtering & Truncation
- We attempt to click/dismiss overlays using common selectors (close buttons, cookie banners) heuristically.
- `rawHtml` is truncated to 2000 characters; set `truncated: true` when truncated.
- Timeout behaviour: HTTP requests have a timeout; Playwright navigation default timeout is 30s. All errors are collected in `errors[]` with phase tags like `fetch`, `render`, `parse`.
