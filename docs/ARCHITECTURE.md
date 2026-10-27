# Architecture — SkillVerse

## Overview

SkillVerse uses a **modular monolith** backend architecture with a **single-page application** frontend. This provides the structural boundaries of a service-oriented system without the operational complexity of microservices, while enabling a rich, interactive learning experience in the browser.

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser                              │
│  React + TypeScript SPA (Vite)                              │
│  ┌───────────┬──────────┬───────────┬────────────────────┐  │
│  │ Shell &   │ Course   │ Activity  │ Dashboard &        │  │
│  │ Navigation│ Viewer   │ Workspace │ Portfolio          │  │
│  └───────────┴──────────┴───────────┴────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS / REST API (JSON)
┌──────────────────────▼──────────────────────────────────────┐
│                   API Gateway / Reverse Proxy               │
│                   (Nginx or Caddy)                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────┐
│                FastAPI Application (Python)                  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                   API Layer (Routers)                  │  │
│  │ health │ auth │ users │ skills │ courses │ activities  │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │                 Service Layer                          │  │
│  │  auth_service │ course_service │ activity_service │ …  │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │                 Domain Models                          │  │
│  │  SQLAlchemy ORM models │ Pydantic schemas              │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │              Infrastructure Layer                      │  │
│  │  database │ cache │ storage │ ai_client │ queue        │  │
│  └────────────────────────────────────────────────────────┘  │
└─────┬──────────┬──────────┬──────────┬───────────────────────┘
      │          │          │          │
      ▼          ▼          ▼          ▼
 PostgreSQL    Redis    Object      Code Execution
                        Storage     Sandbox (Docker)
```

---

## Frontend Architecture

### Technology
- **React 18+** with TypeScript (strict mode).
- **Vite** for development server and production builds.
- **Tailwind CSS** for utility-first styling with a custom design system.
- **shadcn/ui + Radix UI** for accessible, unstyled UI primitives.
- **Motion for React** (formerly Framer Motion) for purposeful animations.
- **React Router** for client-side routing.

### Structure
```
frontend/src/
├── app/                # App root, routing, providers
├── components/         # Shared UI components
│   ├── ui/            # Design system primitives (shadcn/ui)
│   └── layout/        # Shell, navigation, footer
├── features/          # Feature modules
│   ├── auth/          # Authentication flows
│   ├── courses/       # Course discovery and viewing
│   ├── lessons/       # Lesson rendering
│   ├── activities/    # Activity workspaces (code editor, quiz, etc.)
│   ├── dashboard/     # Learner dashboard
│   ├── portfolio/     # Portfolio and projects
│   └── skill-map/     # Interactive skill visualization
├── hooks/             # Shared React hooks
├── services/          # API client and external integrations
├── stores/            # Client-side state management
├── types/             # Shared TypeScript types
└── utils/             # Utility functions
```

### Key Design Decisions

**Feature-based organization:** Code is grouped by domain feature rather than by technical layer. Each feature module contains its own components, hooks and types. Shared utilities live in top-level directories.

**Server state management:** React Query (TanStack Query) for all API data fetching and caching. Local UI state uses React's built-in `useState` / `useReducer`. No global state library unless a clear need emerges.

**Component composition:** UI primitives from shadcn/ui are customized through the design system. Feature components compose these primitives without reimplementing accessibility behavior.

### Universal Lesson Workspace Architecture (Phase 4)

The Phase 4 lesson workspace decouples content interpretation from rendering, providing a consistent learning experience across programming, business, communication, and design courses without discipline-specific forks:

```
                  ┌─────────────────────────────────────────────────────────┐
                  │                 GET /api/v1/courses/:slug               │
                  │       GET /api/v1/courses/:courseSlug/lessons/:lessonSlug│
                  └────────────────────────────┬────────────────────────────┘
                                               │ JSON Payload
                                               ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               LessonWorkspace Controller                               │
│  - Stale Request Invalidation (AbortController)                                        │
│  - Route Parameter Synchronization (/learn/:courseSlug/:lessonSlug)                    │
│  - Keyboard Shortcut Coordinator (ArrowLeft / ArrowRight)                              │
│  - Demo Fallback Isolation (explicit "Demo Track" vs. API 500 error display)           │
├───────────────────────────────┬────────────────────────────────────────────────────────┤
│     LessonWorkspaceHeader     │                     LessonSidebar                      │
│ - Course breadcrumb context   │ - Module collapse / expand state                       │
│ - Published version indicator │ - Active lesson highlighting (aria-current="page")     │
│ - Progress counter (1 / 3)    │ - Mobile sliding drawer with backdrop & Esc close      │
├───────────────────────────────┴────────────────────────────────────────────────────────┤
│                                    LessonContent                                       │
│  - Lesson description, metadata, and learning objectives callout                       │
│  - Bounded Next/Previous controls (safe Course Overview transitions)                   │
│                                               │                                        │
│                                               ▼                                        │
│                                 Universal LessonRenderer                               │
│                   Defensive block dispatch sorted by sort_order                        │
│   ┌───────────────┬────────────────┬────────────────┬──────────────────────────────┐   │
│   │ HeadingBlock  │   TextBlock    │   ListBlock    │      CodeExampleBlock        │   │
│   │ (h2, h3, h4)  │ (safe inline md│ (ordered/unord)│ (syntax highlight, copy btn) │   │
│   ├───────────────┼────────────────┼────────────────┼──────────────────────────────┤   │
│   │ CalloutBlock  │   ImageBlock   │   VideoBlock   │        UnknownBlock          │   │
│   │ (key concepts)│ (alt, loading) │ (embed allow)  │ (diagnostic non-crashing)    │   │
│   └───────────────┴────────────────┴────────────────┴──────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

- **Defensive Block Dispatch:** Each content block is typed via `TypedLessonBlock` (`types/lesson.ts`) and rendered by a dedicated component in `features/lessons/blocks/`.
- **Unknown Block Containment:** Unrecognized block types render a diagnostic warning card rather than throwing an exception or unmounting the tree.
- **Strict Stale Request Protection:** In-flight network requests are bound to an `AbortController`. When learners quickly navigate between lessons or modules, obsolete network responses are aborted before touching component state.

### Creator Studio & Course Authoring Architecture (Phase 7)

Phase 7 introduces the Creator Studio (`frontend/src/features/creator/` and `pages/CreatorStudioPage.tsx`, `pages/CourseEditorPage.tsx`), providing a unified workspace for course creation, curriculum management, structured content block authoring, visual interactive activity configuration, pre-publish validation, and isolated preview.

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    Creator Studio Suite                                 │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│  CreatorStudioPage (/creator)                                                           │
│  - Metrics overview (Total Courses, Drafts in Progress, Published)                      │
│  - Real-time search by title/slug, filter by status (All, Drafts, Published)            │
│  - Draft course initialization modal (discipline & skills taxonomy selector)            │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│  CourseEditorPage (/creator/courses/:courseId)                                          │
│  ┌──────────────────────────────┬────────────────────────────────────────────────────┐  │
│  │       CurriculumTree         │                  Authoring Workspace               │  │
│  │ - Interactive modules tree   │  [Metadata] [Content Blocks] [Activities] [Valid]  │  │
│  │ - Add/rename/delete module   ├────────────────────────────────────────────────────┤  │
│  │ - Add/rename/delete lesson   │ CourseMetadataEditor                               │  │
│  │ - Reorder modules/lessons    │ - Difficulty, duration, tags, objectives           │  │
│  │ - Active lesson selection    ├────────────────────────────────────────────────────┤  │
│  │                              │ LessonBlocksEditor                                 │  │
│  │                              │ - Structured blocks CRUD (heading, text, list,     │  │
│  │                              │   code, callout, image, video embed)               │  │
│  │                              ├────────────────────────────────────────────────────┤  │
│  │                              │ ActivityAuthoringPanel & ActivityEditorModal       │  │
│  │                              │ - 9 type-aware config forms with secret answer key │  │
│  │                              │ - Live simulated preview with instant feedback     │  │
│  │                              ├────────────────────────────────────────────────────┤  │
│  │                              │ ValidationPanel & PublishModal                     │  │
│  │                              │ - Server-authoritative blocking error/warning check│  │
│  │                              │ - Changelog entry & immutable version publication  │  │
│  └──────────────────────────────┴────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│  Non-Destructive Learner Preview (/creator/courses/:courseId/preview/:lessonSlug?)      │
│  - Reuses learner-facing LessonWorkspace, LessonHeader, LessonSidebar, LessonContent     │
│  - Prominent amber preview banner with "Back to Editor" navigation                      │
│  - Complete progress & mastery isolation: progress mutations completely bypassed        │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Backend Architecture

### Technology
- **Python 3.12+**
- **FastAPI** for HTTP API.
- **Pydantic v2** for request/response validation.
- **SQLAlchemy 2.x** with async support for ORM.
- **Alembic** for database migrations.
- **PostgreSQL 16+** for primary data store.

### Module Structure (Modular Monolith)
```
backend/app/
├── main.py                 # FastAPI application factory
├── config.py               # Settings from environment
├── dependencies.py         # FastAPI dependency injection
├── middleware/              # CORS, auth, rate limiting
├── modules/
│   ├── auth/               # Authentication & authorization
│   │   ├── router.py       # API endpoints
│   │   ├── service.py      # Business logic
│   │   ├── models.py       # SQLAlchemy models
│   │   ├── schemas.py      # Pydantic schemas
│   │   └── __init__.py
│   ├── users/              # User profiles and preferences
│   ├── skills/             # Skill taxonomy and prerequisites
│   ├── courses/            # Courses, modules, lessons
│   ├── activities/         # Activity engine and grading
│   ├── progress/           # Enrollment, progress, mastery
│   ├── projects/           # Projects and portfolio
│   ├── ai/                 # AI tutor integration
│   └── admin/              # Administrative operations
├── infrastructure/
│   ├── database.py         # DB session management
│   ├── cache.py            # Redis client
│   ├── storage.py          # Object storage abstraction
│   ├── queue.py            # Background job queue
│   └── sandbox/            # Code execution sandbox client
└── tests/
```

### Module Boundaries

Each module has a clear responsibility and communicates with other modules through its service interface:

| Module | Responsibility |
|---|---|
| `auth` | Registration, login, token management, password reset |
| `users` | Profile management, preferences, settings |
| `skills` | Skill taxonomy, prerequisites, mastery definitions |
| `courses` | Course catalog, versions, modules, lessons, blocks |
| `activities` | Activity types, configuration, attempt management, grading |
| `progress` | Enrollment, lesson/module/course progress, mastery calculation |
| `projects` | Capstone projects, submissions, portfolio |
| `ai` | AI provider abstraction, tutoring, feedback generation |
| `admin` | Administrative operations, audit, content management |

**Rule:** Modules import only from `infrastructure/` and other modules' service interfaces. Direct cross-module model access is prohibited.

### Phase 3 Domain Architecture (Skills, Content & Versioning)

#### 1. Skill Taxonomy & Prerequisite Directed Acyclic Graph (DAG)
- **Disciplines:** High-level domains (`Technology`, `Communication`, `Personal Productivity`, etc.) organizing skills and courses without requiring discipline-specific database tables.
- **Skills:** Concrete abilities classified by proficiency depth (`FOUNDATIONAL`, `INTERMEDIATE`, `ADVANCED`). Hierarchical categorization is supported via `parent_skill_id`.
- **Prerequisite Dependencies:** Modeled as directed graph edges (`skill_id` requires `prerequisite_skill_id`).
  - Database check constraint `CHECK (skill_id != prerequisite_skill_id)` forbids self-dependencies.
  - Service-level cycle detection executes a breadth-first search (BFS) traversing prerequisite links before insert. If a path from the proposed prerequisite to the dependent skill already exists, the dependency is rejected with a `400 Circular dependency detected` error.
  - Active graph serialization via `GET /api/v1/skills/taxonomy/map` provides node and edge geometry for graph visualizers.

#### 2. Course Aggregate Root & Immutable Version Snapshots
- **Aggregate Root (`Course`):** Stable entity with unique slug, title, primary discipline, difficulty level, and creator ownership. Points to `current_version_id`.
- **Working Draft Copy (`CourseVersion` with `version_number = 0` / `published_at IS NULL`):** Mutable working tree where creators add and reorder modules, lessons, and content blocks.
- **Transactional Publication (`publish_course`):**
  1. Validates entire curriculum (at least 1 module, every module has lessons, every lesson has valid blocks).
  2. Allocates sequential version number (`v1`, `v2`, ...).
  3. Records publication timestamp and publisher ID.
  4. Deactivates previous versions (`is_active = false`) and points `Course.current_version_id` to the newly published version within a single database transaction.
- **Published Version Immutability:** Once `published_at` is stamped, that `CourseVersion` and all child `Module`, `Lesson`, and `LessonBlock` records become permanently immutable. Modifying a published course creates or opens an isolated working draft (cloning modules, lessons, and blocks), ensuring earlier published versions are never altered.

#### 3. Structured Lesson Content Model
- Lessons contain an ordered sequence of typed blocks (`heading`, `text`, `list`, `code_example`, `callout`, `image`, `video`, `activity`).
- Content is stored as validated data interpreted by the client renderer (never raw executable JavaScript or unchecked HTML).
- Rich-text markdown is sanitized with script stripping; video embeds are restricted to whitelisted streaming providers.

### Phase 5 Domain Architecture (Interactive Activity and Assessment Engine)

#### 1. Schema-Driven Activity Data Model & Attempt Tracking
- **Activity Entity (`Activity`):** Polymorphic, schema-driven assessment model supporting 9 activity types (`single_choice`, `multiple_select`, `short_answer`, `true_false`, `fill_in_the_blank`, `ordering`, `matching`, `code_exercise`, `scenario`). Holds public prompt metadata, instructions, options, hints, and optional starter code.
- **Grading Configuration (`GradingConfig`):** Encapsulates confidential answer keys, target ordering, expected matching pairs, blanks, test cases, passing score thresholds, and max attempts. **Strictly segregated** from public activity endpoints to prevent client-side answer sniffing.
- **Learner Attempt (`Attempt`):** Immutable audit record tracking user submissions, submitted payloads, server-computed score, pass/fail status, detailed criteria feedback, duration in seconds, and attempt sequence number (`attempt_number`). Enforces unique attempt sequence per user and activity (`uq_user_activity_attempt`).

#### 2. Server-Authoritative Evaluation Lifecycle & Grading Dispatcher
All grading is calculated strictly on the backend via `GradingEngine` (`backend/app/modules/activities/grading.py`). The client is never trusted to calculate scores or determine pass/fail states:
1. **Validation & Attempt Verification:** `ActivityService.submit_attempt` verifies user authentication and active retry allowance (`attempt_number <= max_attempts`). If maximum retries have been exhausted, submission is rejected with `400 Maximum attempts reached`.
2. **Type Dispatch:** `GradingEngine.grade` routes the submission payload and grading configuration to specialized, deterministic grading algorithms:
   - `single_choice`, `true_false`: Exact match with constant-time comparison.
   - `multiple_select`: Partial credit supported or strict exact set matching based on `allow_partial`.
   - `short_answer`: Whitespace-stripped, case-insensitive comparison with alternative acceptable answers.
   - `fill_in_the_blank`: Positional and named token matching with token-level tolerance.
   - `ordering`: Sequence accuracy based on Spearman/Kendall rank or item position match.
   - `matching`: Association correctness comparing key-value tuples.
   - `scenario`: Multi-criteria rubric matching against structured learner submissions.
   - `code_exercise`: Unit test verification executed via the isolated sandbox runner.
3. **Response Sanitization:** When delivering activity definitions to learners via `GET /api/v1/activities/{id}` or `GET /api/v1/lessons/{id}/activities`, the service layer explicitly strips all grading configs, answer keys, solutions, and hidden test cases, returning only sanitized `ActivityResponse` payloads.

#### 3. Safe Code Execution Sandbox Boundary
SkillVerse strictly prohibits running learner-submitted code in the main API or database processes:
- **Sandbox Runner Interface (`SandboxRunnerInterface`):** An abstract boundary (`backend/app/infrastructure/sandbox/runner.py`) decoupling assessment services from execution backends.
- **Worker & Container Isolation:** In production, code execution requests are dispatched to a message queue and processed by an isolated, non-root Docker sandbox worker with hard cgroup constraints: 10s CPU limit, 256MB memory cap, 10MB disk cap, and disabled outbound networking (`--network none`).
- **Safe Fallback Runner:** When container workers are unconfigured, `IsolatedSandboxRunner` safely records attempts in a `SUBMITTED` state with clear diagnostic guidance rather than executing arbitrary untrusted code via host `exec()` or `eval()`.

#### 4. Lesson Workspace Integration
Activities are seamlessly woven into the learning flow through two complementary modalities:
- **Inline Activity Blocks:** Represented by `ActivityBlockData` (`block_type = "activity"`) within `LessonBlock`, allowing creators to place interactive exercises directly between instructional paragraphs.
- **Lesson Checkpoint Activities:** Standalone activities linked to a lesson via `lesson_id` automatically surfaced in the workspace footer under "Interactive Assessment Checkpoint", prompting learners to demonstrate mastery before proceeding to the next lesson.

### Creator Studio, Draft Lifecycle & Publishing Architecture (Phase 7)

#### 1. Draft Isolation & Branching Model
SkillVerse strictly enforces immutable course versioning (`ADR-006`).
- **Initial Creation:** Creates a course aggregate with an initial draft snapshot (`version_number = 0`, `is_active = false`).
- **Editing Active Courses:** When a creator requests the working draft of a published course (`GET /courses/{id}/draft`), if no working draft exists, the system automatically forks the current published version into a new working draft v0, copying all modules, lessons, content blocks, activities, and grading configurations.
- **Publication:** When published (`POST /courses/{id}/publish`), the draft is validated, promoted to the next version number (`v1`, `v2`, ...), stamped with `publisher_id`, `published_at`, and `changelog`, set as `is_active = true`, and cloned into a fresh v0 working draft for future revisions. Previous published versions remain intact and unmutated.

#### 2. Server-Authoritative Pre-Publish Validation Engine
Validation is executed via `CourseService.validate_draft`:
- **Course Level:** Validates title length, short description, and non-empty `learning_objectives`.
- **Curriculum Level:** Enforces at least 1 module and at least 1 lesson per module.
- **Content Level:** Every lesson must contain at least 1 validated content block (`narrative`, `heading`, `list`, `code_snippet`, `callout`, `image`, `video`).
- **Activity Level:** Interactive activities must have valid passing scores, non-empty answer keys/rubrics, and valid associated skill tags.
- Any blocking error strictly prevents publishing with `422 Unprocessable Entity` (`PUBLISH_VALIDATION_ERROR`).

#### 3. Secrets Segregation & Authoring API
- **Learner Protection:** `GET /activities/{id}` and `GET /lessons/{id}/activities` sanitize and strip `answer_key`, `test_cases`, and `rubric` from public and learner responses.
- **Creator Authoring Access:** `GET /activities/{id}/authoring`, `POST /activities`, `PATCH /activities/{id}`, and `DELETE /activities/{id}` require `require_creator_or_admin` and strictly verify course ownership before exposing or updating grading configurations.

---

## Data Flow

### Typical API Request Flow

```
Browser → API Router → Dependency Injection (auth, db session)
       → Service Layer (business logic, validation)
       → SQLAlchemy ORM (database operations)
       → Response Schema (Pydantic serialization)
       → JSON Response
```

### Activity Submission Flow (Code Exercise)

```
1. Learner writes code in browser editor.
2. Frontend POSTs code to /api/v1/activities/{id}/attempts
3. Auth middleware validates JWT token.
4. Activity service validates the attempt (rate limits, enrollment).
5. Activity service sends code to sandbox queue.
6. Sandbox worker (isolated Docker container):
   a. Receives code + test cases.
   b. Executes code with resource limits (CPU, memory, time).
   c. Runs test cases against output.
   d. Returns results (pass/fail, stdout, errors).
7. Activity service records attempt result.
8. Progress service updates lesson/module completion.
9. Skill mastery is recalculated if relevant thresholds are crossed.
10. Response returned to browser with results and feedback.
```

### AI Tutoring Flow

```
1. Learner asks a question within a lesson context.
2. Frontend POSTs question + lesson context to /api/v1/ai/tutor
3. AI service constructs a prompt with:
   - Lesson content and objectives.
   - Learner's current progress and recent attempts.
   - Guardrails (no direct answers, pedagogical approach).
4. AI provider returns response.
5. AI service filters/validates response.
6. Response + usage logged for audit.
7. Guidance returned to learner.
```

---

## External Integrations

| Integration | Purpose | Phase |
|---|---|---|
| OAuth Provider (Google) | Social sign-in (OAuth 2.0 with PKCE) | Phase 2 |
| AI Provider (OpenAI / configurable) | Tutoring, feedback, recommendations | Phase 8 |
| Object Storage (S3-compatible) | Media, uploads, project files | Phase 2 |
| Email Service (SMTP / Resend) | Account verification, notifications | Phase 2 |
| Code Execution Sandbox | Learner code isolation | Phase 5 |

---

## Background Job Responsibilities

Background workers (using a Redis-backed queue such as `arq` or `celery`) handle:

- **Code execution dispatch:** Sending learner code to sandbox containers and collecting results.
- **AI feedback generation:** Long-running AI calls that exceed synchronous response budgets.
- **Progress recalculation:** Batch updates to skill mastery when scoring rules change.
- **Notification delivery:** Email and in-app notification dispatch.
- **Content indexing:** Search index updates when courses are published.
- **Audit log processing:** Writing detailed audit events without blocking API requests.

---

## Authentication and Authorization

### Authentication
- **Primary:** Email + password with bcrypt hashing.
- **Social:** OAuth 2.0 with PKCE (Proof Key for Code Exchange) flow (Google initially). Mitigates authorization code interception and CSRF via cryptographic challenge/verifier and state verification.
- **Session:** Stateless JWT access tokens (short-lived) + refresh tokens (stored, revocable).
- **Verification:** Email verification required before full access.

### Authorization
- **Role-based:** Learner, Creator, Admin.
- **Resource-based:** Enrollment checks for course access. Ownership checks for profile and portfolio.
- **Enforcement:** Server-side on every API endpoint. Client-side checks are UX only, never trusted.

---

## Code Execution Isolation

Learner-submitted code runs in an **isolated sandbox** completely separate from the main API process.

### Requirements
- **Container isolation:** Each execution in a disposable Docker container.
- **Resource limits:** CPU time (10s max), memory (256MB max), disk (10MB max).
- **Network isolation:** No outbound network access from sandbox containers.
- **Language support:** Initially JavaScript/HTML/CSS. Extensible to Python, SQL.
- **Stateless:** Each execution starts from a clean environment.
- **Result protocol:** Structured JSON result with stdout, stderr, test results, exit code.

### Architecture
```
API → Redis Queue → Sandbox Worker → Docker Container
                                    ├── Learner code
                                    ├── Test runner
                                    └── Resource limits (cgroups)
                  ← Result stored in Redis
API ← Poll / webhook for result
```

---

## Deployment Approach

### Local Development
- **Docker Compose** orchestrating: PostgreSQL, Redis, API server, frontend dev server, sandbox worker.
- Health check endpoint (`GET /api/v1/health`) monitors database, cache, and container readiness.
- Hot reload for both frontend (Vite) and backend (uvicorn --reload).
- `.env.example` with all required environment variables documented.

### Production (Planned)
- Containerized deployment (Docker).
- PostgreSQL managed instance.
- Redis managed instance.
- Object storage (S3-compatible).
- Reverse proxy (Nginx or Caddy) for TLS termination and static file serving.
- Horizontal scaling of API servers and sandbox workers independently.

### CI/CD
- Automated testing on every pull request.
- Linting and type checking (ESLint + tsc for frontend, ruff + mypy for backend).
- Database migration verification.
- Build verification for frontend production bundle.

---

## Architectural Decisions

### ADR-001: Modular Monolith over Microservices
**Decision:** Use a modular monolith for the backend.
**Rationale:** The team is small, the domain boundaries are still evolving, and the operational overhead of microservices (service discovery, distributed tracing, API gateways) is not justified at this stage. Module boundaries within the monolith enforce separation of concerns and allow future extraction if needed.

### ADR-002: REST API over GraphQL
**Decision:** Use versioned REST endpoints.
**Rationale:** The data access patterns are well-defined (course → modules → lessons → activities). REST is simpler to cache, test and document. GraphQL adds complexity in authorization and N+1 prevention that is unnecessary for the current scope.

### ADR-003: Server-Side Rendering Not Required
**Decision:** Use a client-side SPA (Vite + React) without SSR.
**Rationale:** The learning platform is an authenticated application, not a content marketing site. SEO is needed only for public course catalog pages, which can be handled with meta tags and prerendering. SSR adds complexity to deployment and state management.

### ADR-004: Schema-Driven Activity Engine
**Decision:** Activities (code exercises, quizzes, role-play, tasks) are configured through JSON schemas, not implemented as separate subsystems.
**Rationale:** The platform needs to support many activity types across multiple domains. A schema-driven approach means new activity types can be added by defining a configuration schema and a renderer, not by building a new backend subsystem.

### ADR-005: Provider-Neutral AI Layer
**Decision:** AI integrations go through an abstraction layer that is not coupled to a specific provider.
**Rationale:** The AI landscape is evolving rapidly. Coupling to a single provider creates vendor lock-in. The abstraction allows switching providers, using different providers for different tasks, and adding local model support.

### ADR-006: Immutable Course Versions
**Decision:** Published courses are versioned and immutable. Edits create new versions.
**Rationale:** Learners enrolled in a course version should not see their content change mid-course. Progress and grades must reference a specific version. This also enables safe rollback of content changes.

### ADR-007: Universal Cross-Disciplinary Content Block Renderer
**Decision:** Use a single, unified block-dispatch lesson rendering system for all disciplines instead of maintaining separate custom viewers for coding, spoken English, or productivity.
**Rationale:** Maintaining distinct renderers for different subject areas leads to code duplication, inconsistent keyboard accessibility, divergent visual aesthetics, and high maintenance overhead. A schema-driven block model (`heading`, `text`, `list`, `code_example`, `callout`, `image`, `video`) provides full expressive capability across coding and non-coding domains while guaranteeing WCAG 2.2 accessibility, responsive behavior, and robust security sandboxing across the entire curriculum.

### ADR-008: Server-Authoritative Grading & Answer Key Confidentiality
**Decision:** All evaluation, scoring, retry validation, and feedback generation must occur exclusively on the backend server. Answer keys, correct option IDs, expected blanks, and test case assertions must never be transmitted in learner-facing API payloads.
**Rationale:** Client-side grading allows learners to inspect DOM state or network responses to trivially obtain solutions without demonstrating competence. Stripping grading configurations at the service boundary guarantees integrity while ensuring learners receive authoritative, tamper-proof grading records and diagnostic feedback.

### ADR-009: Strict Code Execution Sandbox Boundary
**Decision:** Learner-submitted code must never be executed within the main FastAPI application or host worker processes (strictly forbidding `eval()`, `exec()`, or direct host subprocess invocation). All code execution is isolated behind an explicit `SandboxRunnerInterface` that dispatches jobs to disposable, resource-constrained container environments.
**Rationale:** Untrusted learner code can attempt denial-of-service (CPU spinning, fork bombs, memory exhaustion), unauthorized network access (data exfiltration, SSRF), or filesystem compromise. Decoupling code execution behind an isolated runner boundary ensures platform resilience and system security.

### ADR-010: Evidence-Backed Skill Mastery and Progression Cascade
**Decision:** Base skill mastery levels (`NOT_STARTED`, `LEARNING`, `PRACTICING`, `PROVISIONAL`, `MASTERED`, `NEEDS_REVIEW`) on authenticated, server-verified attempt evidence requiring a minimum number of distinct completed tasks and threshold average scores, while automating progression cascades (attempt passed → lesson progress updated → course progress calculated and completed) through backend domain events.
**Rationale:** Simple binary checkmarks or self-reported completions allow learners to bypass rigorous demonstration of learning outcomes. Requiring multiple distinct assessment tasks prevents learners from grinding a single easy question to falsely claim subject mastery. Automating the progression cascade on the backend ensures tamper-proof progression records that are consistent across the learner dashboard, course view, and skill map.

### ADR-011: Server-Authoritative Draft Validation and Non-Destructive Preview Mode
**Decision:** Require all draft courses to pass backend-authoritative structural and content validation prior to publishing, and support draft inspection through an isolated, non-destructive preview mode that reuses the production learner workspace while strictly preventing learner progression, enrollment creation, or skill mastery mutations.
**Rationale:** Client-only validation allows malformed courses (e.g. empty lessons, orphaned activities, missing passing scores) to be published, breaking learner experiences. Reusing the production `LessonWorkspace` for draft previews ensures complete visual fidelity (WYSIWYG) between authoring and consumption, while bypassing progress tracking endpoints prevents test runs by creators from polluting analytics or awarding unearned credentials.

### ADR-012: Creator Secrets Segregation and Working Draft Isolation
**Decision:** Segregate activity authoring contracts from learner-facing contracts by serving complete configurations (including answer keys, hidden test cases, and rubrics) exclusively through dedicated authoring endpoints protected by `require_creator_or_admin` and course ownership checks. Isolate all authoring edits to version 0 drafts until an explicit publish action promotes them to an immutable version.
**Rationale:** Exposing answer keys on general activity endpoints allows learners to bypass assessments. Conversely, allowing in-place edits to published versions breaks the immutability guarantee for currently enrolled learners. Isolating authoring edits to a clone draft v0 and restricting secrets to verified creators maintains assessment integrity while preserving course version immutability.
