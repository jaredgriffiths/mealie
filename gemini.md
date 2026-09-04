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
- [mealie/app.py](file:///home/quok/Antigravity/mealie/mealie/app.py) & [mealie/main.py](file:///home/quok/Antigravity/mealie/mealie/main.py): Entry points.
- [mealie/routes/](file:///home/quok/Antigravity/mealie/mealie/routes/): FastAPI routers representing individual REST API endpoints.
- [mealie/services/](file:///home/quok/Antigravity/mealie/mealie/services/): Core business logic orchestrating operations.
- [mealie/repos/](file:///home/quok/Antigravity/mealie/mealie/repos/): Repository pattern wrappers handles database query execution (SQLAlchemy).
- [mealie/db/](file:///home/quok/Antigravity/mealie/mealie/db/): SQLAlchemy engine, sessions, models, and base classes.
- [mealie/schema/](file:///home/quok/Antigravity/mealie/mealie/schema/): Pydantic schemas for request/response serialization/deserialization.
- [mealie/core/](file:///home/quok/Antigravity/mealie/mealie/core/): Application configurations, settings, security, and constants.
- [mealie/alembic/](file:///home/quok/Antigravity/mealie/mealie/alembic/): Alembic database migrations.

### Frontend (`/frontend`)
The Nuxt 3 frontend application folder structure is as follows:
- [frontend/app/](file:///home/quok/Antigravity/mealie/frontend/app/): Vue/Nuxt pages, components, composables, and state management.
- [frontend/nuxt.config.ts](file:///home/quok/Antigravity/mealie/frontend/nuxt.config.ts): Nuxt configuration.

---

## 🤖 Agent Guidelines & Directory

Workspace customization resources for AI agents are located under the [.agents/](file:///home/quok/Antigravity/mealie/.agents/) directory.

- **Workspace Rules:** [.agents/AGENTS.md](file:///home/quok/Antigravity/mealie/.agents/AGENTS.md) contains project-specific instructions and style preferences for agents.
- **Workspace Skills:** [.agents/skills/](file:///home/quok/Antigravity/mealie/.agents/skills/) holds custom capabilities or guides relevant to this project.

---

## 🔁 CI/CD & Deployment Pipeline

To ensure quality and structure when releasing updates:
1. **Branch Management:** Always work on and commit directly to the `main` branch.
2. **Container Image Publishing:** The [publish.sh](file:///home/quok/Antigravity/mealie/publish.sh) root script verifies git status, stages and commits changes, and pushes to `main`. This triggers the GitHub Actions workflow at [.github/workflows/dev-live-publish.yml](file:///home/quok/Antigravity/mealie/.github/workflows/dev-live-publish.yml) to build and publish the production image to the GitHub Container Registry (`ghcr.io/jaredgriffiths/mealie:latest`).
3. **Deployment on LAN:** Once the GHCR image build finishes, the production stack is updated on the local LAN server (or Portainer.io UI) via `docker compose pull && docker compose up -d`.



