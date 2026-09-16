# Stage 1: Build — install deps and compile Angular app
FROM node:24-slim AS builder
WORKDIR /app
# Cap the V8 heap so the build survives a 1 GB VPS (swap absorbs the spikes)
ENV NODE_OPTIONS=--max-old-space-size=1024
# pnpm-workspace.yaml carries the allowBuilds decisions piped into install
COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile
COPY frontend/ ./
RUN pnpm build --configuration production

# Stage 2: Serve — minimal nginx hosting the compiled SPA
FROM nginx:alpine
COPY --from=builder /app/dist/frontend/browser /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
