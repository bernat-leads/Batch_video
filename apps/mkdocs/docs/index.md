# Lead Alliances — Bulk Video Pipeline

## What It Is

A web application that bulk-produces short-form video ads (TikTok/Reels/Shorts format) from Excel scripts for a marketing team. Users upload an Excel file containing 10-100 ad scripts, and the system processes each through a multi-step API pipeline to output finished 9:16 MP4 videos with AI-generated visuals, voiceover, and burned-in captions.

## How It Works

1. User logs in with a shared team password
2. Uploads an Excel file (.xlsx) with ad scripts (columns: `script_id`, `script_text`, optional `voice_id`, `style`)
3. System validates the file and creates a batch job
4. Each script row is processed through the video pipeline via Celery workers (4 in parallel)
5. Dashboard shows real-time progress per video and per batch
6. Completed videos can be downloaded individually or as a ZIP
7. Files auto-expire from storage after 7 days

## Video Pipeline (per script)

```
Script text → ElevenLabs TTS → Claude Segmentation → Gemini Imagen 3 → Remotion Assembly → Upload to R2
```

1. **ElevenLabs TTS** — Convert script to voiceover audio with word-level timestamps
2. **Claude Segmentation** (claude-sonnet-4-6) — Chunk script into 5-8s visual segments, generate image prompts + Ken Burns directions
3. **Gemini Imagen 3** — Generate 1080x1920 images per segment in parallel
4. **Remotion Assembly** — Compose final video with Ken Burns pan/zoom effects, synced audio, and TikTok-style burned-in captions

Output: 1080x1920 H.264 MP4

## Apps

| App | Tech | Description |
|-----|------|-------------|
| `react` | Vite, React, TanStack Router | Dashboard — upload, progress, downloads |
| `api` | FastAPI, SQLAlchemy 2.0 async | Backend API and pipeline orchestration |
| `mkdocs` | MkDocs Material | Developer documentation |
| `storybook` | Storybook 8 | UI component development |
| `email` | React Email | Email templates (optional) |

## Packages

| Package | Description |
|---------|-------------|
| `ui` | Shared shadcn/ui component library |
| `analytics` | PostHog analytics wrapper |
| `email` | Shared email utilities |
| `api-client` | Generated TypeScript client for the FastAPI backend |
| `sentry` | Shared Sentry configuration |

## Core Concepts

| Concept | Description |
|---------|-------------|
| **Batch** | A set of videos created from one Excel upload |
| **Video** | A single script being processed through the pipeline |
| **Shot** | A segment of a video with its own image, timing, and Ken Burns config |
| **Pipeline Stage** | One step in the video generation flow (TTS → segmentation → images → assembly) |
| **Background Processing** | Celery workers process videos via Redis |
| **Storage Lifecycle** | Finished videos stored in Cloudflare R2, auto-deleted after 7 days |

## Infrastructure

| Component | Role |
|-----------|------|
| Redis | Celery broker and result backend |
| PostgreSQL | Primary database |
| Cloudflare R2 | Video and artifact storage |
| Docker | Production deployment on VPS |

## External APIs

| Service | Purpose |
|---------|---------|
| ElevenLabs | Text-to-speech with word-level timestamps |
| Claude (claude-sonnet-4-6) | Script segmentation and image prompt generation |
| Gemini Imagen 3 | AI image generation (1080x1920) |

## Key URLs (Local Development)

| Service | URL |
|---------|-----|
| Frontend | `http://localhost:5173` |
| Backend API | `http://localhost:8000` |
| API Docs | `http://localhost:8000/docs` |
| Storybook | `http://localhost:6006` |
