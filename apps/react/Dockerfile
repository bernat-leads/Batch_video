FROM node:20-alpine AS base
RUN corepack enable && corepack prepare pnpm@10.11.0 --activate

FROM base AS builder
WORKDIR /app

ARG PUBLIC_API_URL
ARG PUBLIC_SITE_URL
ENV PUBLIC_API_URL=$PUBLIC_API_URL
ENV PUBLIC_SITE_URL=$PUBLIC_SITE_URL

# Copy root workspace files
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml turbo.json ./
COPY tooling/ ./tooling/
COPY packages/ ./packages/
COPY apps/react/ ./apps/react/
RUN pnpm install --frozen-lockfile
RUN pnpm --filter react build

FROM nginx:alpine AS runner
COPY --from=builder /app/apps/react/dist /usr/share/nginx/html
COPY apps/react/nginx.conf /etc/nginx/nginx.conf.template
COPY apps/react/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENV PORT=80
ENV BACKEND_URL=http://localhost:8000

ENTRYPOINT ["/docker-entrypoint.sh"]
