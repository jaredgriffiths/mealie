# Workspace Rules for Mealie

This file defines the project-specific rules, guidelines, and behavioral constraints for AI agents interacting with the Mealie repository.

## 📌 Coding Standards

### Backend (Python)
- **Formatting & Linting:** We use `ruff` for code formatting and linting. Always run `ruff format` and `ruff check` on modified files.
- **Python Version:** Use Python 3.12 syntax and feature sets (e.g. advanced type hinting).
- **Type Annotations:** Ensure all new functions and classes are fully typed and pass `mypy`.
- **Comments & Docstrings:** Ensure code is appropriately documented and commented per PEP 257 (docstrings) and PEP 8 (comments).
- **Database Operations:** Database interactions must go through the Repository pattern in `mealie/repos/` instead of executing raw queries or direct session operations inside route handlers or services.
- **Documentation Updates:** When code changes are made, locate and update the appropriate user/developer documentation files inside the [docs/docs/](file:///home/quok/Antigravity/mealie/mealie-1/docs/docs/) directory.

### Frontend (TypeScript / Vue / Nuxt)
- **Framework:** Nuxt 3 (Composition API syntax, `<script setup lang="ts">`).
- **Styling:** Use Vuetify classes and design tokens where possible.
- **Package Manager:** Use `yarn` in the `frontend` directory.

## 🛠️ Common Workflows

### Python Environment
- The environment is managed via `uv`. Activate the virtual environment with `source .venv/bin/activate` or prefix commands with `uv run`.

### Running Tests
- Run backend pytest tests using `uv run pytest`.

### CI/CD & Deployments
- **Branch Management:** Always work on and commit to the `main` branch.
- **Docker Publishing:** Use the root script [publish.sh](file:///home/quok/Antigravity/mealie/mealie-1/publish.sh) to pull the latest official image from GHCR (`ghcr.io/jaredgriffiths/mealie:latest`) and start the production stack on the local LAN.

## 🤖 AI Vibe Coding Reference Maps
To keep the AI pair-programming efficiency high and optimize token usage, we maintain reference files under `.agents/`:
- **API reference maps**: [.agents/api_reference_map.json](file:///home/quok/Antigravity/mealie/mealie-1/.agents/api_reference_map.json)
- **Repository mapping guides**: [.agents/repository_mapping.md](file:///home/quok/Antigravity/mealie/mealie-1/.agents/repository_mapping.md)

**Rule for Agents**: Whenever you create or modify backend routes, API controllers, schemas, or DB repositories, you **must** update the corresponding mapping files under `.agents/` as part of your verification/walkthrough steps.
