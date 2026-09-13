# Mealie AI Reference Map & Repository Index

This reference map enables instant navigation across backend repositories, API routes, schemas, and PWA frontend modules for high token efficiency.

## 🧭 Directory & Module Quick-Lookup Index

```
Mealie Core Architecture Index
├── mealie/              (Python FastAPI Backend)
│   ├── routes/          (API Controllers / Route Handlers)
│   ├── schema/          (Pydantic Schemas / Request & Response Models)
│   ├── repos/           (SQLAlchemy DB Repositories - AllRepositories)
│   ├── services/        (Business Logic & Service Layer)
│   └── core/            (Configuration, Settings & Directories)
├── frontend/            (Nuxt 3 Vue PWA Application)
│   ├── app/pages/       (Vue Page Components & URL Routes)
│   ├── app/components/  (Reusable UI Components)
│   ├── app/composables/ (API Client & Pinia State Hooks)
│   └── nuxt.config.ts   (PWA & Vite Settings)
├── apps/mobile/pwa/     (Standalone Companion PWA)
└── archive/             (Archived Reference Code: firebase/, android/)
```

---

## 🗄️ SQLAlchemy Model to Repository Mappings

This index documents the correct mappings between SQLAlchemy models and the attributes available on Mealie's repository factory wrapper `AllRepositories` (instantiated as `self.repos`).

| Domain Model / Context | Repository Instance Attribute | Source Class File |
|---|---|---|
| **Recipes** | `self.repos.recipes` | `mealie/repos/repository_recipes.py` |
| **Shopping Lists** | `self.repos.group_shopping_lists` | `mealie/repos/repository_shopping_list.py` |
| **Meal Plans** | `self.repos.meals` | `mealie/repos/repository_meals.py` |
| **Users** | `self.repos.users` | `mealie/repos/repository_users.py` |
| **Groups** | `self.repos.groups` | `mealie/repos/repository_group.py` |
| **Households** | `self.repos.households` | `mealie/repos/repository_household.py` |
| **AI Providers** | `self.repos.group_ai_providers` | `mealie/repos/repository_ai_provider.py` |
| **Cookbooks** | `self.repos.cookbooks` | `mealie/repos/repository_cookbooks.py` |

> [!WARNING]
> **Common Pitfall**: Do **NOT** use `self.repos.shopping_lists` or `self.repos.meal_plans`. Doing so will raise an `AttributeError` at runtime. Refer to the mapping above.

---

## 🕷️ Web Scraper Strategies & Anti-Bot Architecture

Mealie uses a multi-tiered scraping engine to ingest web recipes automatically:

| Component / Strategy | File Path | Description |
|---|---|---|
| **`safe_scrape_html()`** | `mealie/services/scraper/scraper_strategies.py` | Multi-signature TLS handshake browser impersonation (`httpx-curl-cffi`), realistic headers, and anti-bot challenge block page detection (Akamai, Cloudflare, DataDome). |
| **`RecipeScraperABC`** | `mealie/services/scraper/scraper_strategies.py` | Native scraper for Australian Broadcasting Corporation (`abc.net.au/news/...`). Parses Next.js `__NEXT_DATA__` structured recipe JSON and semantic HTML DOM fallbacks for title, ingredients with sections, instructions, timings, yield, and high-res imagery. |
| **`RecipeScraperColes`** | `mealie/services/scraper/scraper_strategies.py` | Native scraper for `coles.com.au`. Parses Adobe Experience Manager (AEM) JSON components for title, ingredients with sections, method steps, yields, prep/cook times, and images. |
| **`RecipeScraperPackage`** | `mealie/services/scraper/scraper_strategies.py` | Standard `schema.org/Recipe` `ld+json` scraper via `recipe-scrapers` library. |
| **`RecipeScraperOpenAI`** | `mealie/services/scraper/scraper_strategies.py` | AI-assisted fallback scraper when structured `ld+json` is missing. |

---

## ⚡ Docker Build & Architecture Performance Settings

- **Layer Caching**: `docker/Dockerfile` copies `package.json` & `yarn.lock` before source code and uses `--mount=type=cache,target=/usr/local/share/.cache/yarn` to cache package downloads across builds.
- **Single Architecture Target (`linux/amd64`)**: `.github/workflows/dev-live-publish.yml` targets `platforms: linux/amd64` to eliminate QEMU software emulation overhead for x86_64 LAN servers.
- **Client PWA Compatibility**: Mobile devices (iOS/Android) run the PWA web application in client browsers. Restricting server container binaries to `linux/amd64` has zero impact on mobile devices.


