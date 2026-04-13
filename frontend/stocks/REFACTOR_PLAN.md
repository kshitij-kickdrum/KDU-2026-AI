# Frontend Refactor Plan

## Root Cause

Codex built a developer dashboard (light mode, flat MUI cards, exposed technical fields).
Stitch designed a premium dark trading terminal (dark navy, glassmorphism, sidebar nav, 3 pages).

---

## What Changes

### 1. Theme (theme.ts)
- Switch to dark mode (`#0f131c` background)
- Primary: cyan `#00d2ff` / `#47d6ff`
- Tertiary/success: green `#00fd9b`
- Error: `#ffb4ab`
- Fonts: Inter (headline/body) + Space Grotesk (labels/uppercase)
- Border radius: 2px default, 8px xl (stitch uses very subtle rounding)
- Remove all light-mode overrides

### 2. SCSS Variables (styles/abstracts/_variables.scss)
- Replace all light-mode color vars with stitch design tokens
- Add glassmorphism mixin: `backdrop-filter: blur(20px)`, `background: rgba(49,53,63,0.4)`
- Add glow shadow utilities
- Add Space Grotesk uppercase label style

### 3. App Structure — 3 Pages instead of 1 dashboard
Replace single `DashboardPage` with proper routing:

```
src/
  features/
    run-agent/          ← Page 1 (was DashboardPage)
    trade-approval/     ← Page 2 (new)
    session-history/    ← Page 3 (was StateInspector)
  shared/
    layout/
      Sidebar.tsx       ← new
      TopNav.tsx        ← new
      AppLayout.tsx     ← new
```

### 4. Run Agent Page (Page 1)
**Remove:**
- Thread ID field (auto-generate with `uuid` on submit)
- Custom Prompt field (internal detail)
- "Session State Inspector" section

**Keep & restyle:**
- Portfolio holdings editor → styled as stitch's bento grid (left 40%, right 60%)
- Currency selector → stitch's dark select with expand_more icon
- Stock symbol field → stitch's "Primary Ticker" with live connection indicator
- Run Agent button → gradient cyan button with shimmer hover effect
- Portfolio total footer → `$XX,XXX.XX` in large Space Grotesk font

**Add:**
- Hero header: "Initiate Strategic Agent" with cyan accent word
- System status footer strip (3 cards: Agent Core, Execution Latency, Risk Guard)
- Background glow blobs (fixed position, pointer-events-none)

### 5. Trade Approval Page (Page 2)
**This page is entirely new.** It shows when `status === "awaiting_approval"`.

**Add:**
- Status banner pill: "Status: Pending Verification" with pulsing green dot
- Session ID display (auto-generated, shown as read-only)
- Large recommendation card: "The agent recommends: BUY TSLA" in huge gradient text
- AI reasoning terminal (fake log output showing agent's decision trace)
- Approve button (green, full width)
- Reject button (red/outline, full width)
- Contextual data strip: Market Impact, Slippage, Est. Profit, Network Fee

**Navigation:** After run returns `awaiting_approval`, auto-navigate to this page.

### 6. Session History Page (Page 3)
**Replace StateInspector with proper history page.**

**Remove:**
- Raw "Thread ID" input label
- Developer-style state dump

**Add:**
- Page header: "Session History" with subtitle
- Search bar (pill shape, dark background) with "Look Up" button
- Main result card (70%): session ID, status badge, portfolio totals, trade log timeline
- Sidebar (30%): previous session cards with status badges
- Trade log as timeline (colored dots, timestamps, action descriptions)

### 7. Sidebar Navigation (shared/layout/Sidebar.tsx)
- Fixed left, 256px wide, `bg-slate-950`
- User avatar + "Alpha Trader / Pro Account"
- Nav items: Dashboard, Analytics (active), Signals, Settings
- Active item: cyan text + `bg-cyan-400/10` + right border `border-cyan-400`
- "New Trade" button at bottom
- Hidden on mobile

### 8. Top Navigation (shared/layout/TopNav.tsx)
- Fixed top, `bg-slate-900/60 backdrop-blur-xl`
- Logo: "Stock Trading Agent" in cyan
- Nav links: "Run Agent" | "Session History"
- Sensors icon button (right)
- Cyan glow shadow: `shadow-[0_0_40px_rgba(71,214,255,0.08)]`

### 9. Redux State (uiSlice.ts)
**Remove:**
- `threadId` from RunDraft (auto-generate on submit)
- `prompt` from RunDraft (not user-facing)
- `stateInspectorThreadId` (replaced by session history search)

**Add:**
- `currentPage: 'run-agent' | 'trade-approval' | 'session-history'`
- `sessionHistorySearch: string`
- `activeSessionId: string` (auto-generated thread_id)

### 10. UX Flow
```
User opens app
  → Run Agent page (default)
  → Fills portfolio + symbol + currency
  → Clicks "Run Agent"
  → Loading state with step messages
  → If status === "awaiting_approval":
      → Auto-navigate to Trade Approval page
  → If status === "completed":
      → Show result inline (portfolio total, trade log)
  → On Trade Approval page:
      → Click "Approve" or "Reject"
      → Show result
  → Session History page:
      → Search by session ID
      → View past runs
```

---

## Files to Delete
- `features/dashboard/` (entire folder — replace with new structure)

## Files to Create
- `features/run-agent/RunAgentPage.tsx`
- `features/run-agent/RunAgentPage.module.scss`
- `features/run-agent/components/SessionParameters.tsx`
- `features/run-agent/components/PortfolioHoldings.tsx`
- `features/run-agent/components/SystemStatusStrip.tsx`
- `features/trade-approval/TradeApprovalPage.tsx`
- `features/trade-approval/TradeApprovalPage.module.scss`
- `features/trade-approval/components/RecommendationCard.tsx`
- `features/trade-approval/components/AgentReasoningTerminal.tsx`
- `features/trade-approval/components/ApprovalActions.tsx`
- `features/session-history/SessionHistoryPage.tsx`
- `features/session-history/SessionHistoryPage.module.scss`
- `features/session-history/components/SessionResultCard.tsx`
- `features/session-history/components/TradeLogTimeline.tsx`
- `features/session-history/components/RecentSessionsSidebar.tsx`
- `shared/layout/AppLayout.tsx`
- `shared/layout/Sidebar.tsx`
- `shared/layout/TopNav.tsx`
- `shared/layout/AppLayout.module.scss`

## Files to Update
- `app/theme.ts` — full dark mode rewrite
- `styles/abstracts/_variables.scss` — stitch design tokens
- `styles/abstracts/_mixins.scss` — glassmorphism, glow mixins
- `store/slices/uiSlice.ts` — remove threadId/prompt, add page routing
- `App.tsx` — add AppLayout + page routing
