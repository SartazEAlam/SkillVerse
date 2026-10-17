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
