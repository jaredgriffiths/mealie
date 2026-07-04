# Mealie Project Baseline

This document baselines the technologies, frameworks, architecture, and folder structure of the **Mealie** project to help AI agents navigate and contribute to the codebase effectively.

---

## 🚀 Technology Stack

### Backend
- **Language:** Python >= 3.12 (specifically configured with `requires-python = ">=3.12,<3.13"`)
- **Web Framework:** FastAPI (REST API backend)
- **Database ORM:** SQLAlchemy (v2) with Alembic for database migrations
- **Validation:** Pydantic (v2)
- **Package & Environment Manager:** `uv` (using `pyproject.toml` and `uv.lock`)

### Frontend
- **Language:** TypeScript
- **Framework:** Nuxt 3 / Vue 3
- **UI Library:** Vuetify
- **Package Manager:** `yarn`

---

## 🏗️ Architecture & Codebase Structure

### Backend (`/mealie`)
The backend is structured into a typical layered API architecture:
- [mealie/app.py](file:///home/quok/Antigravity/mealie/mealie-1/mealie/app.py) & [mealie/main.py](file:///home/quok/Antigravity/mealie/mealie-1/mealie/main.py): Entry points.
- [mealie/routes/](file:///home/quok/Antigravity/mealie/mealie-1/mealie/routes/): FastAPI routers representing individual REST API endpoints.
- [mealie/services/](file:///home/quok/Antigravity/mealie/mealie-1/mealie/services/): Core business logic orchestrating operations.
- [mealie/repos/](file:///home/quok/Antigravity/mealie/mealie-1/mealie/repos/): Repository pattern wrappers handles database query execution (SQLAlchemy).
- [mealie/db/](file:///home/quok/Antigravity/mealie/mealie-1/mealie/db/): SQLAlchemy engine, sessions, models, and base classes.
- [mealie/schema/](file:///home/quok/Antigravity/mealie/mealie-1/mealie/schema/): Pydantic schemas for request/response serialization/deserialization.
- [mealie/core/](file:///home/quok/Antigravity/mealie/mealie-1/mealie/core/): Application configurations, settings, security, and constants.
- [mealie/alembic/](file:///home/quok/Antigravity/mealie/mealie-1/mealie/alembic/): Alembic database migrations.

### Frontend (`/frontend`)
The Nuxt 3 frontend application folder structure is as follows:
- [frontend/app/](file:///home/quok/Antigravity/mealie/mealie-1/frontend/app/): Vue/Nuxt pages, components, composables, and state management.
- [frontend/nuxt.config.ts](file:///home/quok/Antigravity/mealie/mealie-1/frontend/nuxt.config.ts): Nuxt configuration.

---

## 🤖 Agent Guidelines & Directory

Workspace customization resources for AI agents are located under the [.agents/](file:///home/quok/Antigravity/mealie/mealie-1/.agents/) directory.

- **Workspace Rules:** [.agents/AGENTS.md](file:///home/quok/Antigravity/mealie/mealie-1/.agents/AGENTS.md) contains project-specific instructions and style preferences for agents.
- **Workspace Skills:** [.agents/skills/](file:///home/quok/Antigravity/mealie/mealie-1/.agents/skills/) holds custom capabilities or guides relevant to this project.

---

## 🔁 CI/CD & Deployment Pipeline

To ensure quality and structure when releasing updates:
1. **Branch Protection & Development:** All feature/dev updates must be committed to the `dev` branch rather than directly to `mealie-next`.
2. **Dev Publication (Localhost):** The [dev-publish.sh](file:///home/quok/Antigravity/mealie/mealie-1/dev-publish.sh) script switches to `dev`, commits/pushes changes, and builds the Docker image locally on the localhost Docker daemon (`mealie:dev`).
3. **Live Publication (GHCR):** The [live-publish.sh](file:///home/quok/Antigravity/mealie/mealie-1/live-publish.sh) script merges `dev` into `mealie-next` and pushes it to GitHub, which triggers the GitHub Actions workflow at [.github/workflows/dev-live-publish.yml](file:///home/quok/Antigravity/mealie/mealie-1/.github/workflows/dev-live-publish.yml) to automatically build the Docker image and publish it to the GitHub Container Registry (`ghcr.io/<username>/mealie:latest`). Your LAN server can then pull directly from GHCR.



