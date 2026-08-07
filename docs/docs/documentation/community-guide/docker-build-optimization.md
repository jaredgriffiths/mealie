# Docker Build Performance & Architecture Optimization

This guide documents the container build optimizations and architecture targeting decisions implemented in Mealie.

## Build Performance Strategy

### 1. Dependency Layer Caching
In `docker/Dockerfile`, the frontend dependency manifest files (`package.json` and `yarn.lock`) are copied into the builder stage **before** copying application source code:

```dockerfile
COPY frontend/package.json frontend/yarn.lock ./
RUN --mount=type=cache,target=/usr/local/share/.cache/yarn \
    yarn install --prefer-offline --frozen-lockfile --non-interactive
```

- **Benefit**: Docker caches the `yarn install` layer permanently across builds. Modifying frontend components or pages no longer re-downloads Node packages.

### 2. Single-Architecture Target (`linux/amd64`)
In `.github/workflows/dev-live-publish.yml`, the build pipeline is configured for `platforms: linux/amd64`:

- **Rationale**: Eliminates multi-architecture QEMU CPU emulation overhead during GitHub Actions workflow runs.
- **Client PWA Compatibility**: Mobile browsers (iOS Safari, Android Chrome) execute the Progressive Web App (PWA) client-side. Server container architecture (`linux/amd64`) has zero impact on mobile devices or client PWA performance.
