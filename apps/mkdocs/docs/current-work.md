# Current Work

## Project Timeline

**Start:** 2026-03-13 | **Target:** 2026-03-15 | **Status:** In Progress

## Linear Issues

| ID | Title | Priority | Status |
|----|-------|----------|--------|
| HYP-5 | Project Setup & Infrastructure | High | Done |
| HYP-6 | Authentication | High | Done |
| HYP-7 | Excel Upload & Parsing | High | Done |
| HYP-8 | Video Generation Pipeline | Urgent | Todo |
| HYP-9 | Pipeline Orchestration | High | Todo |
| HYP-10 | Web Dashboard | High | In Progress |
| HYP-11 | Downloads & Storage Lifecycle | Medium | Todo |
| HYP-12 | Deployment & Documentation | Medium | Todo |
| HYP-13 | Testing & Handoff | Medium | Todo |

## Current Focus: HYP-10 — Web Dashboard

Dashboard is implemented and refined:
- Dashboard page with stats API, charts (recharts), recent tables
- Batch list, batch detail, video list, video detail pages
- Settings page (master prompt, retention, column defaults)
- Multi-step batch creation dialog (upload → map columns → review)
- Single video creation dialog with prompt from settings

### Recent Refinements (2026-03-14)

**Video Detail Page (`/app/videos/$videoId`):**
- Hero layout: 280px video preview (9:16 aspect) + Details & Statistics cards
- Statistics section: two-column layout (Totals | Per Shot Avg) with vertical separator
- Full-width pipeline section with icon-labeled stage indicator (`StageIndicator variant="full"`)
- Collapsible Prompt & Script section (side-by-side)
- Shots table with expandable rows (image prompt, Ken Burns config, model info)
- Status badge inline with page title
- Export (download link) + Download + Delete buttons with proper disabled states
- Backend: `file_size_bytes`, `width`, `height` columns on Video model + per-shot averages computed server-side

**Delete Confirmation:**
- `ConfirmDeleteDialog` component wrapping `AlertDialog` for all destructive actions
- Applied to: video table dropdown, batch table dropdown, batch detail delete, video detail delete, selection toolbar bulk delete

**Pipeline Indicator:**
- `StageIndicator` has two variants: `compact` (progress bars for tables) and `full` (icon + label pills for detail pages)
- 6 stages: Queued → Audio (TTS) → Segmentation → Image Gen → Assembly → Done

**Codebase Refactoring:**
- Created `/refactor` skill with 25 rules (F-01–F-15 frontend, B-01–B-10 backend, S-01–S-04 shared)
- Ran full audit across frontend and backend
- Normalized import order, removed dead code, enforced theme tokens, consistent patterns

**UI Label Consistency:**
- `generation_time_ms` → displayed as "Video Length" everywhere in the UI

**Next up:**
- Move route-specific components to `_components/` folders
- Unit tests (Vitest) for key components
- Pipeline integration (HYP-8, HYP-9)

## Blockers

_None_
