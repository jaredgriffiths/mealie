---
trigger: always_on
glob: ["archive/android/**", "apps/mobile/**", "frontend/**"]
description: "Guidelines and architecture notes for Android & Mobile PWA integration"
---

# Android & Mobile Client Guidelines

- **Client Execution:** Mobile clients (Android Chrome, iOS Safari) access Mealie via Progressive Web App (PWA) capabilities served from Nuxt 3.
- **Server Agnostic:** The backend container architecture (e.g. `linux/amd64`) executes independently of the client OS. Mobile PWA logic executes entirely within the client's browser environment.
- **Archived Native Code:** The `archive/android/` directory contains historical native code preserved for reference. All active mobile improvements should be made directly in the Nuxt PWA under `frontend/` or `apps/mobile/pwa/`.
