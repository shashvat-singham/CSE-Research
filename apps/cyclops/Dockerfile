# syntax=docker/dockerfile:1.7

# Cyclops — multi-stage build producing a Next.js standalone server.
#
# The standalone output traces only the modules actually imported, so the
# runtime image carries neither the full node_modules tree nor the build
# toolchain. Each stage installs exactly what it needs and nothing more.

# ---------------------------------------------------------------------------
# deps — production + build dependencies, cached on the lockfile alone
# ---------------------------------------------------------------------------
FROM node:22-alpine AS deps
WORKDIR /app

# Copying only the manifests means a source-only change reuses this layer.
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# ---------------------------------------------------------------------------
# builder — compile the app
# ---------------------------------------------------------------------------
FROM node:22-alpine AS builder
WORKDIR /app

ENV NEXT_TELEMETRY_DISABLED=1

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# `output: standalone` is set by BUILD_STANDALONE in next.config.mjs so local
# `next build` stays unaffected.
ENV BUILD_STANDALONE=1
RUN npm run build

# ---------------------------------------------------------------------------
# runner — the shipped image
# ---------------------------------------------------------------------------
FROM node:22-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

# Run unprivileged. node:alpine ships a `node` user (uid 1000) already.
RUN apk add --no-cache curl

COPY --from=builder --chown=node:node /app/public ./public
COPY --from=builder --chown=node:node /app/.next/standalone ./
COPY --from=builder --chown=node:node /app/.next/static ./.next/static

USER node

EXPOSE 3000

# The analyze endpoint exercises the LL(1) engine, so a healthy response means
# the app is actually serving rather than merely listening.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -fsS -X POST http://127.0.0.1:3000/api/analyze \
        -H 'Content-Type: application/json' \
        -d '{"grammar":"S -> a"}' > /dev/null || exit 1

CMD ["node", "server.js"]
