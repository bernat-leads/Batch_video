FROM node:25-alpine AS base
RUN corepack enable && corepack prepare pnpm@10.11.0 --activate

FROM base AS builder
WORKDIR /app
# Copy root workspace files
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml turbo.json ./
COPY tooling/ ./tooling/
COPY apps/react/ ./apps/react/
RUN pnpm install --frozen-lockfile
RUN pnpm --filter react build

FROM nginx:alpine AS runner
COPY --from=builder /app/apps/react/dist /usr/share/nginx/html
COPY apps/react/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
