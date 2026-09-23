# Edge cases and blast radius

The happy path is what the PR was built for, so it usually works. Regressions come from two other places: **the awkward inputs to the new thing**, and **the old flows that pass through the code you changed**. This file covers finding both, checking them, and showing the checks in the PR.

## Scale it to the risk

| The change | Edge-case pass |
|---|---|
| Copy, docs, a color token, a test-only change | None. Say nothing. |
| A new, isolated component or endpoint | The input checklist below, for that component |
| A condition, guard, gate, query or state that **existing** screens or requests read | The full blast-radius pass. This is where most regressions come from |
| Auth, permissions, feature flags, persistence, caching, anything "on first load" | Full pass, with extra attention to transitions (below) |

## 1. Blast radius: who else goes through the code you changed?

List every existing flow that reads what you touched, and check each one still behaves the same.

1. For each changed condition, flag, query key, prop or shared state, search for its readers (`rg`, "find references"). Count **flows, not files**: "every chat view", "every order page", "every signed-out visitor".
2. For each flow, write one line: what it did before, and what it does now. If you can't say, you haven't checked it.
3. Check the flows your feature **doesn't** target. A sharing feature has to be checked on chats nobody shares. A new admin gate has to be checked for non-admins. A migration has to be checked on old rows.

### Transitions are where it breaks

A condition that's right on first load can still be wrong when one of its inputs changes **mid-session**. Walk each input through its transitions while the screen is already mounted:

- new → saved (a draft or a brand-new record gets its id, "exists" flips to true)
- signed out → in, member → removed, owner → viewer
- loading → loaded → **refetching** (a background refetch must not bring the first-load spinner back)
- empty → first item → many; many → last item removed
- flag off → on during a session; online → offline → online
- stale cache → fresh data; optimistic update → server confirmation or rollback

**A real regression this would have caught.** A feature added sharing to a chat product and hid the chat view behind an ownership query "whenever the chat exists". It shipped with over 300 passing tests, all aimed at sharing. But a brand-new chat is only saved after its first answer, so "exists" flipped from false to true mid-session. That started the ownership query, and while it was pending the whole chat was swapped for a loading state and mounted again. Every new conversation flashed and reloaded right after its first answer. A single capture of the existing flow ("start a chat, send one message, wait for the answer") on main and on the branch would have shown it, because a frame strip makes a one-frame spinner flash obvious.

## 2. Input checklist: frontend

Pick the rows that apply. Not every PR needs every row.

| Area | Cases |
|---|---|
| Interaction states | hover, focus-visible (keyboard), active/pressed, disabled, loading, selected, dragging |
| Content | empty, one, many (scroll, 1,000 rows), very long words and names, long translations (German runs about 30% longer), missing image or avatar, numbers at 0 / negative / huge |
| Language and direction | RTL (`dir="rtl"`: do icons, padding and animation directions mirror?), CJK and emoji widths, pluralization |
| Layout | smallest supported width (320 px), largest, zoom 200%, Dynamic Type or large font size, landscape, split view |
| Theme and motion | light and dark, high contrast, reduced motion, reduced transparency |
| Input methods | keyboard only (tab order, Escape, focus trap and return), screen reader labels, touch (44 px targets, no hover-only affordances) |
| Timing | slow network (skeleton → content without layout shift), double-click and double-submit, navigating away mid-request, the request failing |
| Lifecycle | first load vs return visit, refresh mid-flow, back/forward, a second tab open |

## 3. Input checklist: backend

| Area | Cases |
|---|---|
| Data shape | empty, null or missing fields, huge (pagination, limits), duplicates, unicode, old rows from before a migration |
| Identity | owner, other user, anonymous, removed member, admin or impersonated, cross-tenant |
| Concurrency | two requests at once, retries, idempotency, ordering, a partial failure halfway through |
| Time | timeouts, clock skew, expiry at the boundary, long-running jobs overlapping |
| Rollout | flag on and off, old client against new server (and the reverse), a mixed-version deploy |
| Existing flows | every caller of the changed function or query, especially ones outside the feature |

## 4. Show it in the PR

Add a compact **Edge cases** section after the figures, as a table. One row per case: what you checked, how, and the result. Link to a figure when the check is visual.

```markdown
## Edge cases

| Case | How checked | Result |
|---|---|---|
| New chat, first answer finishes (not shared) | Captured on main and branch, 16 ms frames | No remount, no spinner frame (strip below) |
| Signed out, opens a public link | Playwright, fresh context | Read-only bar, send disabled |
| Owner loses workspace membership mid-session | Test: `revoked_member_sees_read_only` | Read-only after refetch, no reload |
| RTL | `dir="rtl"` still | Arrow and padding mirror ([figure](#rtl)) |
| 60-character title, 320 px | Still | Truncates with ellipsis |
```

- Visual cases get a small figure, or several folded under `<details><summary>Edge cases, visually</summary>`.
- For **"nothing changed" claims on existing flows**, the best evidence is a main-vs-branch capture of that flow that's identical, or that differs only where intended. Say which.
- For a transition, use a frame strip across it. Flashes, remounts and layout jumps show up there and nowhere else.
- List what you **didn't** check under Not in this PR. An honest gap is better than an implied guarantee.
