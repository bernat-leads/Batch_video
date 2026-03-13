# Template — Application Overview

## What It Is

This is a production-ready SaaS monorepo template built on a Next.js + FastAPI + LangGraph stack. It provides a conversational AI agent interface, user authentication, subscription management, CMS-driven landing pages, and a background task processing pipeline — ready to be customized for any domain.

## How It Works

1. A user signs up and authenticates via email/password or Google OAuth
2. They are gated behind a subscription paywall (Polar), then gain access to the dashboard
3. The user starts a chat conversation with the AI agent
4. The LangGraph agent orchestrates multi-turn conversations via the CopilotKit AG-UI protocol
5. Background tasks (Celery + Redis) handle any async processing triggered during or after conversations
6. Results can be surfaced across dedicated dashboard pages
7. All UI content is internationalized and CMS-driven (Payload CMS)

## Apps

| App | Tech | Description |
|-----|------|-------------|
| `nextjs` | Next.js 15, React 19, Payload CMS | Main frontend and CMS admin |
| `fastapi` | FastAPI, SQLAlchemy 2.0 async | Backend API and AI agent |
| `astro` | Astro | Public landing page |
| `mkdocs` | MkDocs Material | Developer documentation |
| `storybook` | Storybook 8 | UI component development and docs |
| `keycloak-theme` | Keycloakify | Custom auth UI theme |
| `email` | React Email | Transactional email templates |

## Packages

| Package | Description |
|---------|-------------|
| `ui` | Shared shadcn/ui component library |
| `analytics` | PostHog analytics wrapper |
| `email` | Shared email sending utilities |
| `api-client` | Generated TypeScript client for the FastAPI backend |
| `sentry` | Shared Sentry configuration |
| `eslint-config` | Shared ESLint configuration |
| `prettier-config` | Shared Prettier configuration |
| `typescript-config` | Shared TypeScript configuration |

## Core Concepts

| Concept | Description |
|---------|-------------|
| **CopilotKit Agent** | AI chat interface powered by LangGraph and the AG-UI protocol |
| **Background Processing** | Celery worker tasks run asynchronously via Redis |
| **Payload CMS** | Content management embedded in the Next.js app, used for pages and structured data |
| **Subscription Gating** | Polar handles plan selection and payment; the protected layout enforces access |
| **i18n** | next-intl with configurable locales; content translation powered by the LLM layer |

## Infrastructure

| Component | Role |
|-----------|------|
| Traefik | Reverse proxy and local SSL termination |
| Redis | Celery broker and result backend |
| PostgreSQL | Primary database (two instances: app + Payload CMS) |
| MailCatcher | Local SMTP server for catching dev emails |

## Observability

- **Sentry** — error tracking (frontend + backend)
- **PostHog** — product analytics
- **Langfuse** — LLM call tracing and observability

## Features

- User authentication (email/password, Google OAuth via Better Auth)
- AI chat agent (LangGraph + CopilotKit AG-UI)
- Subscription management and paywalling (Polar)
- Background task processing (Celery + Redis)
- CMS-driven content (Payload CMS)
- Internationalization (next-intl, configurable locales)
- E2E test suite (Playwright)
- Backend unit tests (pytest)
- Component development environment (Storybook)
- Transactional email templates (React Email + MailCatcher)

## Key URLs (Local Development)

| Service | URL |
|---------|-----|
| Frontend | `http://localhost:3000` |
| Backend API | `http://localhost:8000` |
| CMS Admin | `http://localhost:3000/admin` |
| API Docs | `http://localhost:8000/docs` |
| MailCatcher | `http://localhost:1080` |
| Storybook | `http://localhost:6006` |
