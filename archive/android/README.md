# Archived Native Android Application

This directory contains the archived source code, Gradle configurations, and Android SDK components for the native Mealie Android companion app (`io.mealie.companion`).

## Rationale
Native Android app development has been archived in favor of maintaining Progressive Web App (PWA) capabilities (`frontend/` and `apps/mobile/pwa/`). 

## Active PWA Alternatives
- **Primary Nuxt 3 PWA (`frontend/`)**: Fully functional offline support, service workers, and manifest installation on iOS and Android devices.
- **Companion PWA (`apps/mobile/pwa/`)**: Standalone Vite companion PWA.

## Data Safety
- **Zero Database Schema Impact**: Mealie's backend database (SQLite / PostgreSQL) operates independently of the native mobile app code.
- **Data Integrity**: Archiving this mobile code does not affect any existing user recipes, shopping lists, meal plans, or user accounts.
