# SkillVerse

**Cross-disciplinary interactive skill-learning platform.**

SkillVerse is an immersive learning platform that helps people acquire usable skills through practice — not passive content consumption. It supports programming, communication, business, design, productivity and more through chapter-based learning paths, interactive exercises, realistic simulations, verifiable capstone projects, and AI-assisted tutoring.

The platform draws structural inspiration from the chapter-based, try-it-yourself approach of W3Schools, but extends it far beyond coding tutorials to create an integrated ecosystem across multiple disciplines with automated evaluation, verifiable evidence, and public showcase portfolios.

## Development Status

SkillVerse is being developed according to a comprehensive 12-phase engineering roadmap (`docs/DEVELOPMENT_PLAN.md`). Phases 0 through 9 are fully implemented and verified.

- **Phase 0 — Product Specification, Architecture & Engineering Governance** (completed)
  Established the foundational product vision (`docs/PRODUCT.md`), modular monolith architecture (`docs/ARCHITECTURE.md`), relational database schema (`docs/DATABASE.md`), API contracts (`docs/API.md`), security standards (`docs/SECURITY.md`), design system principles (`docs/DESIGN_SYSTEM.md`), and durable development rules (`AGENTS.md`).
- **Phase 1 — Immersive Design System & Frontend Shell** (completed)
  The frontend application shell is implemented with a dark-first design system, responsive navigation, and four main interactive routes (Dashboard, Course Catalog Explore, Interactive Skill Map, and Course Overview with interactive preview).
- **Phase 2 — Backend Foundation, Database Infrastructure & Identity** (completed)
  FastAPI application foundation with SQLAlchemy models, Alembic migrations, Argon2id password hashing, JWT access + refresh token rotation, Google OAuth 2.0 PKCE, rate limiting, and profile management (GDPR export, soft delete). Includes frontend auth integration (Login, Register, Profile, AuthContext).
- **Phase 3 — Cross-Disciplinary Skill Taxonomy, Course Catalog & Versioned Content Model** (completed)
  Domain model and APIs for cross-disciplinary skills, cycle-safe prerequisite DAG, courses, modules, lessons, structured content blocks, and immutable published course versions. Public catalog discovery with filtering (discipline, difficulty), search, and deterministic pagination. Includes idempotent seed script populating 7 disciplines, 15 skills, 12 prerequisite edges, and 3 full representative courses (Web Dev, Spoken English, Personal Productivity) published through the standard versioning service.
- **Phase 4 — Universal Lesson Workspace & Immersive Learning Experience** (completed)
  Universal block-based lesson renderer displaying Phase 3 structured, versioned content (`heading`, `text`, `list`, `code_example` with syntax highlighting and clipboard copy, `callout`, `image`, `video`, and graceful unknown block fallback). Responsive learning workspace layout with collapsible module outline, progress tracking, breadcrumb context, boundary-protected navigation, keyboard shortcuts (`←`/`→`), mobile drawer, and `AbortController` stale response cancellation.
- **Phase 5 — Interactive Activity and Assessment Engine** (completed)
  Schema-driven assessment engine supporting 9 distinct activity types (`single_choice`, `multiple_select`, `short_answer`, `true_false`, `fill_in_the_blank`, `ordering`, `matching`, `code_exercise`, and `scenario`). Server-authoritative grading with answer key confidentiality (secret keys never exposed to clients), retry enforcement (`max_attempts`), and detailed attempt history with cross-user authorization. Safe execution boundary via `SandboxRunnerInterface` preventing untrusted learner code from running in the main API process. Embedded and checkpoint activity rendering integrated seamlessly into the universal lesson workspace.
- **Phase 6 — Learner Progression, Enrollments, Skill Mastery & Progress Dashboard** (completed)
  Full learner progression lifecycle. Authenticated course enrollments bound to immutable course version snapshots (`Enrollment`), with prerequisite DAG validation (`/courses/{slug}/prerequisites`) and duplicate prevention. Durable lesson progress tracking (`LessonProgress`) with server-side gating requiring passed activities. Automated progression cascade (passed assessment attempt triggers lesson start, lesson completion, and overall course completion). Multi-tier, evidence-backed skill mastery system (`SkillMastery`) requiring distinct passed tasks and threshold average scores. Comprehensive learner dashboard (`GET /api/v1/progress/dashboard`) with active enrolled courses, resume learning hero card, skill mastery overview, recent assessment attempts, explainable recommendations, and idempotent achievements (`Achievement`, `UserAchievement`). Dual compatibility across PostgreSQL 16 and SQLite via migration `004_progress_mastery`.
- **Phase 7 — Creator Studio, Course Authoring & Versioned Publishing** (completed)
  End-to-end creator workflow. Managed courses dashboard (`/creator`) with metrics, search, and status filters. Split-pane course authoring workspace (`/creator/courses/:courseId`) with interactive curriculum navigation (add, rename, delete, reorder modules and lessons), course metadata editor with unsaved changes tracking, visual structured content blocks editor (all 7 block types: narrative, heading, list, code snippet, callout, image, video embed), and type-aware interactive activity configuration suite covering all 9 supported activity types with confidential answer keys, rubrics, and live simulated preview. Server-authoritative pre-publish validation (`validate_draft`) enforcing structural and assessment standards. Non-destructive learner-facing draft preview (`/creator/courses/:courseId/preview/:lessonSlug?`) with draft banner, bypassing progress and mastery mutations. Immutable course publishing with automatic working draft v0 branching for subsequent revisions.
- **Phase 8 — AI Tutor and Personalized Recommendations** (completed)
  Provider-neutral AI tutoring and personalized recommendation system supporting pedagogical simulation (`MockAIProvider`) and Google Gemini (`GeminiAIProvider`) via direct REST integration. Sliding-window user-scoped rate limiting (30 questions/hr, 10 hints/hr). Strict opt-out preference enforcement in backend and user profile settings. Interactive slide-over AI Tutor drawer with `Alt+T` shortcut in the universal lesson workspace. Pedagogical 3-tier progressive hint engine (`ActivityContainer`) guiding learners without premature scoring or unearned mastery. Privacy-first telemetry model (`AIInteraction`) via Alembic migration `005_ai_interactions` recording token usage, latency, and status without persisting raw prompts or responses by default. Explainable gap-targeted skill recommendations (`ProgressionService`) with `"Skill Gap"` badges. *Note: Live Google Gemini integration remains unverified locally due to absence of GEMINI_API_KEY; deterministic MockAIProvider is active by default.*
- **Phase 9 — Capstone Projects, Learner Portfolio, Specialized Practice & Verifiable Showcases** (completed)
  Complete practical projects and public portfolio ecosystem:
  - **Structured Projects & Submissions:** Milestone tracking, starter resources, deliverable submission workspace (`/projects/:slug/workspace`), multi-revision history (`revision_of_id`), and evaluator rubric scoring across an authoritative state machine (`DRAFT` → `SUBMITTED` → `UNDER_REVIEW` → `EVALUATED` → `COMPLETED` / `CHANGES_REQUESTED`).
  - **Hardened Artifact Storage:** Provider-neutral storage abstraction (`StorageInterface`, `LocalStorageService`) enforcing server-generated UUID storage keys, binary magic-byte verification (PDF, PNG, JPEG, WebP with `RIFF`/`WEBP` signature, ZIP, TXT, MD, JSON), path containment verification (`_is_within_base_dir`), upload quotas (20MB/file, 50MB/submission, 10 files max), and transactional rollback on failures.
  - **5-Gate Download Authorization:** Anonymous and third-party deliverable downloads are strictly protected by a 5-gate security check requiring a public portfolio, completed submission, public artifact flag, referencing portfolio item, and public item visibility.
  - **Learner Portfolio Showcase:** Individualized portfolio management (`/portfolio`) and shareable public showcase (`/u/:slugOrId/portfolio` & `/portfolio/:slugOrId`) with tri-state visibility (`PRIVATE`, `UNLISTED`, `PUBLIC`), custom URL slug reservation (3–100 alphanumeric characters, collision prevention against `RESERVED_SLUGS`), sanitized public responses, and non-destructive curation of completed project deliverables.
  - **Multi-Evidence Skill Progression:** Verified capstone project completions cascade directly into `SkillMastery` records with revision deduplication, requiring multiple distinct assessment tasks (activities or projects) to attain full `MASTERED` status.
  - **Specialized Practice Activities:** Web Development Practice (`web_practice`) with repository and live demo URL validation without untrusted code execution; Executive Communication Practice (`communication`) supporting BLUF and STAR frameworks; accessible keyboard and screen reader interactions for Ordering and Matching; and formative qualitative AI writing review (`POST /api/v1/ai/communication-feedback`) with strict opt-out compliance. Supported by Alembic migration `006_projects_and_portfolios`.

### Remaining Roadmap Milestones

- **Phase 10 — Security, Deployment and Release Readiness** (⏳ Planned)
  Production security hardening (OWASP Top 10, CSP headers, penetration tests), production Docker multi-stage containers, deployment manifests, database backup/restore procedures, load testing (100 concurrent learners), monitoring, and release verification.
- **Phase 11 — Community and Ecosystem Expansion** (⏳ Planned)
  Community forums, study groups, peer review workflows, creator marketplace and monetization, advanced visual skill graphs, and spaced repetition retention mechanics.

---

## Technology Stack

| Layer | Technology | Status |
|---|---|---|
| Frontend | React 19, TypeScript (strict), Vite, Tailwind CSS v4, Lucide Icons | Implemented (Phases 1–9) |
| Backend | Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic, pwdlib[argon2] | Implemented (Phases 2–9) |
| Database | PostgreSQL 16 (production/Docker), SQLite (local test harness) | Configured & Migrated (`006_projects_and_portfolios` head) |
| Storage | Provider-neutral artifact storage (`StorageInterface`, Local Storage; S3-ready) | Implemented (Phase 9) |
| Cache / Jobs | Redis 7 (docker-compose ready, worker queue foundation) | Configured |
| Code Execution | Isolated sandbox (`SandboxRunnerInterface`, safe container worker boundary) | Implemented boundary (Phase 5) |
| AI | Provider-neutral integration layer (Mock, Gemini REST) | Implemented (Phases 8–9; mock verified, live Gemini unverified without API key) |
| Dev Environment | Docker Compose | Configured |

---

## Repository Structure

```
SkillVerse/
├── docs/                    # Architecture and product documentation
│   ├── PRODUCT.md           # Product vision, personas, requirements
│   ├── ARCHITECTURE.md      # System architecture, ADRs, storage & 5-gate security
│   ├── DATABASE.md          # Relational data models, migrations, constraints
│   ├── API.md               # API endpoint documentation (v1 contracts)
│   ├── DESIGN_SYSTEM.md     # Visual design principles, tokens, dark aesthetic
│   ├── SECURITY.md          # Security policies, storage hardening, isolation
│   └── DEVELOPMENT_PLAN.md  # 12-phase implementation roadmap (Phases 0–11)
├── frontend/                # React + Vite application (Phases 1–9)
│   ├── src/
│   │   ├── app/             # Application entry and React Router definitions
│   │   ├── components/      # Design system primitives & responsive layout shell
│   │   ├── context/         # AuthContext and session state
│   │   ├── data/            # Typed course catalog, skills taxonomy, demo data
│   │   ├── features/        # Feature modules:
│   │   │   ├── activities/  # Activity renderers: code, quiz, web practice, communication, ordering, matching
│   │   │   ├── ai-tutor/    # Slide-over AI Tutor drawer and hint interactions
│   │   │   ├── lessons/     # Block-based universal lesson renderer
│   │   │   ├── portfolio/   # Portfolio profile editor, item cards, modal, share card, public showcase
│   │   │   └── projects/    # Project catalog card, filters, milestones, rubric, workspace, revision history, artifacts
│   │   ├── pages/           # Dashboard, Explore, Skills, Course Overview, Lesson Workspace, Creator Studio, Course Editor, Auth, Profile, Projects, Project Detail, Submission Workspace, Portfolio Management, Public Portfolio
│   │   ├── services/        # API clients: auth, courses, progress, activities, ai, projects, portfolio
│   │   ├── test/            # Vitest unit and integration test suite (13 suites, 118 tests)
│   │   └── types/           # TypeScript contracts for auth, courses, skills, progress, AI, projects, portfolio
│   ├── package.json
│   └── vite.config.ts
├── backend/                 # FastAPI application (Phases 2–9)
│   ├── alembic/             # Versioned database migrations (001–006 head)
│   ├── app/
│   │   ├── infrastructure/  # Database session, rate limiter, AI providers, artifact storage (local/S3)
│   │   │   ├── ai/          # AI provider interface, MockAIProvider, GeminiAIProvider
│   │   │   └── storage/     # StorageInterface, LocalStorageService, storage factory
│   │   ├── modules/         # auth, users, courses, activities, progress, skills, ai, projects
│   │   │   ├── activities/  # Activity models, schemas, and grading engine
│   │   │   ├── ai/          # AI router, schemas, and prompt service
│   │   │   ├── auth/        # Identity, JWT rotation, Google OAuth PKCE
│   │   │   ├── courses/     # Catalog, structured blocks, versioned publishing
│   │   │   ├── progress/    # Enrollments, lesson progress, skill mastery, dashboard
│   │   │   ├── projects/    # Capstones, submissions, artifacts, portfolio showcase
│   │   │   ├── skills/      # Taxonomy DAG, prerequisites, discipline categorization
│   │   │   └── users/       # Profile management, preferences, GDPR export
│   │   ├── config.py        # Pydantic Settings with production invariants
│   │   └── main.py          # FastAPI application entry & CORS middleware
│   ├── tests/               # Pytest test suite (230 tests against SQLite harness)
│   └── pyproject.toml
├── docker-compose.yml       # Local PostgreSQL 16, Redis 7 & API services
├── AGENTS.md                # Engineering rules for AI-assisted development
├── README.md                # This file
└── .gitignore               # Git ignore rules
```

---

## Documentation

- [Product Specification](docs/PRODUCT.md) — Product vision, learner personas, and core requirements
- [Architecture](docs/ARCHITECTURE.md) — System architecture, modular monolith design, and ADRs (ADR-001 through ADR-017)
- [Database Design](docs/DATABASE.md) — Relational schema definitions, constraints, indices, and migration history
- [API Reference](docs/API.md) — Comprehensive v1 REST API endpoint contracts and access control rules
- [Design System](docs/DESIGN_SYSTEM.md) — Dark-first visual aesthetic, color tokens, and accessible primitives
- [Security](docs/SECURITY.md) — Threat modeling, sandbox isolation, storage protection, and 5-gate authorization
- [Development Plan](docs/DEVELOPMENT_PLAN.md) — Phased implementation roadmap with detailed acceptance criteria

---

## Getting Started

### Prerequisites
- Node.js 20+ (v24 recommended) & npm 10+
- Python 3.11+
- Docker Desktop (optional for local PostgreSQL/Redis; SQLite used for local tests when Docker is unavailable)

### Backend Setup & Testing

```bash
# Navigate to the backend workspace
cd backend

# Create and activate a virtual environment
python -m venv .venv
# Windows:
.venv/Scripts/activate
# Linux/macOS:
# source .venv/bin/activate

# Install dependencies in editable mode
pip install -e ".[dev]"

# Configure local environment variables from template
# Windows: copy ..\.env.example .env
# Linux/macOS: cp ../.env.example .env
# (Default configuration activates MockAIProvider and LocalStorageService; no external credentials required)

# Run code style and lint checks with Ruff
ruff check .

# Verify database migrations are aligned with SQLAlchemy models
python -m alembic check

# Seed initial cross-disciplinary taxonomy, representative courses, and achievements
python -m app.seed

# Run automated test suite (230 tests passing against SQLite test database)
pytest

# Start local development server
uvicorn app.main:app --reload --port 8000
```

*Database & Environment Realities:*
- Automated unit and integration tests run against an isolated SQLite test database (`sqlite:///./test.db`).
- Production environments strictly require PostgreSQL (`DATABASE_URL`), validated at application boot. Docker Compose (`docker-compose up`) defines PostgreSQL 16 and Redis 7 services. *Note: Live PostgreSQL 16 integration is unverified locally due to local Docker daemon unavailability and must be verified in CI/CD.*
- AI Tutoring defaults to `MockAIProvider` for deterministic local development. Live Google Gemini (`GeminiAIProvider`) requires a valid `GEMINI_API_KEY` and remains unverified locally.

### Frontend Setup & Development

```bash
# Navigate to the frontend workspace
cd frontend

# Install dependencies
npm install

# Start local development server with hot reload
npm run dev

# Run TypeScript strict type verification
npm run typecheck

# Run Vitest unit and integration test suite (118 tests passing across 13 suites)
npm run test

# Run fast linter (oxlint)
npm run lint

# Build production bundle
npm run build
```

*Frontend Build Note:* `npm run build` succeeds cleanly (`tsc -b && vite build`). The generated production bundle currently includes a standard Vite chunk-size advisory (>500 kB) that is documented in `docs/DEVELOPMENT_PLAN.md` and scheduled for resolution via dynamic route code-splitting in Phase 10.

Once running, open [http://127.0.0.1:5173/](http://127.0.0.1:5173/) in your browser.

---

## License

All rights reserved. License terms to be determined.
