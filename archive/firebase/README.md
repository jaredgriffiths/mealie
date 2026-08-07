# Archived Firebase Integration

This folder contains the archived source code, schemas, routes, and sidecar daemon for the Firebase Sync Bridge.

## Context & Rationale
Firebase sync capabilities were archived in favor of using standard Progressive Web App (PWA) capabilities (`@vite-pwa/nuxt`). 

## Data Safety
- **Database Safety**: Mealie's primary database (SQLite / PostgreSQL) operates independently of Firebase. Firebase was purely an optional sidecar sync daemon.
- **Zero Database Schema Impact**: No database tables or Alembic migrations were ever used by Firebase (state was managed solely via configuration JSON files in `DATA_DIR`).
- **Data Integrity**: Archiving this module does not modify, delete, or alter any user recipes, shopping lists, meal plans, or account data in Mealie.

## Archived Structure
- `admin_firebase_bridge.py`: Admin controller route definitions for configuring Firebase.
- `firebase_bridge.py`: Pydantic schema models for Firebase bridge settings.
- `firebase_bridge_service.py`: Service layer managing configuration JSON reading/writing.
- `sync-worker/`: Python sidecar daemon for syncing SQLite/Postgres changes to Firestore.
- `docker-compose.bridge.yml`: Docker compose configuration for running the sidecar daemon.
