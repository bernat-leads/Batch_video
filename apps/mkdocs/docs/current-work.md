# Current Work

## Project Timeline

**Start:** 2026-03-13 | **Target:** 2026-03-15 | **Status:** In Progress

## Linear Issues

| ID | Title | Priority | Status |
|----|-------|----------|--------|
| HYP-5 | Project Setup & Infrastructure | High | In Progress |
| HYP-6 | Authentication | High | Todo |
| HYP-7 | Excel Upload & Parsing | High | Todo |
| HYP-8 | Video Generation Pipeline | Urgent | Todo |
| HYP-9 | Pipeline Orchestration | High | Todo |
| HYP-10 | Web Dashboard | High | Todo |
| HYP-11 | Downloads & Storage Lifecycle | Medium | Todo |
| HYP-12 | Deployment & Documentation | Medium | Todo |
| HYP-13 | Testing & Handoff | Medium | Todo |

## Implementation Order

1. **HYP-5** — Project Setup & Infrastructure (monorepo, Docker, env vars)
2. **HYP-6** — Authentication (shared password)
3. **HYP-7** — Excel Upload & Parsing (drag & drop, validation, defaults)
4. **HYP-8** — Video Generation Pipeline (ElevenLabs → Claude → Gemini → Remotion)
5. **HYP-9** — Pipeline Orchestration (Celery chains, 4 workers, retries, status tracking)
6. **HYP-10** — Web Dashboard (batch progress, real-time status, thumbnails)
7. **HYP-11** — Downloads & Storage Lifecycle (presigned URLs, ZIP, 7-day expiry)
8. **HYP-12** — Deployment & Documentation (production Docker, VPS docs)
9. **HYP-13** — Testing & Handoff (E2E validation, client demo)

## Blockers

_None_
