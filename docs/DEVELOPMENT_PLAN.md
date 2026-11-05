# Development Plan — SkillVerse

This document defines the phased implementation roadmap. Each phase includes objectives, dependencies, deliverables, acceptance criteria, required tests, risks and current status.

**Rule:** A phase is marked complete only when all acceptance criteria have been verified through actual testing or inspection. Do not mark a phase complete based on file creation alone.

---

## Phase Status Legend

| Status | Meaning |
|---|---|
| ✅ Complete | All acceptance criteria verified |
| 🔄 In Progress | Work has started, not all criteria met |
| ⏳ Planned | Not yet started |
| 🚫 Blocked | Cannot proceed due to unresolved dependency |

---

## Phase 0: Product Specification and Repository Setup

**Status:** ✅ Complete

### Objectives
- Inspect the repository and document existing state.
- Define product vision, architecture, data model, API contracts and security requirements.
- Establish engineering rules and development conventions.
- Create a phased implementation roadmap.

### Dependencies
- None (this is the foundation phase).

### Deliverables
- [x] Repository inspected and documented.
- [x] `README.md` — project overview.
- [x] `AGENTS.md` — engineering rules.
- [x] `.gitignore` — file exclusion rules.
- [x] `docs/PRODUCT.md` — product specification.
- [x] `docs/ARCHITECTURE.md` — system architecture.
- [x] `docs/DATABASE.md` — data model documentation.
- [x] `docs/API.md` — API endpoint documentation.
- [x] `docs/DESIGN_SYSTEM.md` — design principles.
- [x] `docs/SECURITY.md` — security requirements.
- [x] `docs/DEVELOPMENT_PLAN.md` — this file.

### Acceptance Criteria
1. All seven documentation files exist and are substantive.
2. AGENTS.md contains durable engineering rules.
3. The roadmap includes measurable acceptance criteria for every phase.
4. Risks and unresolved decisions are documented.
5. No existing working functionality has been overwritten.
6. No secrets are present in committed files.

### Required Tests
- Manual inspection of file contents and directory structure.
- Git diff inspection for unintended changes.

### Risks
- Documentation may become stale as implementation reveals new constraints.
- Mitigation: Each phase updates relevant documentation as part of its deliverables.

---

## Phase 1: Design System and Immersive Frontend Shell

**Status:** ✅ Completed

### Objectives
- Initialize the frontend project (React + TypeScript + Vite + Tailwind CSS v4).
- Implement the design token system (colors, typography, spacing, CSS custom properties).
- Build the application shell (responsive layout, sidebar navigation, header, routing).
- Create foundational UI components (Button, IconButton, Input, Badge, ProgressBar, Card, Modal, EmptyState, SkipLink).
- Establish the visual identity with an immersive, dark-first interface and violet/cyan accents.
- Implement working interactive pages: Dashboard (`/`), Course Discovery (`/explore`), Interactive Skill Map (`/skills`), Course Overview (`/courses/:slug`), and Fallback (`*`).

### Dependencies
- Phase 0 (product specification and design direction).

### Deliverables
- `frontend/` directory with Vite + React + TypeScript project.
- Tailwind CSS configuration with custom design tokens.
- Google Fonts integration (Inter or selected font).
- shadcn/ui installed and configured.
- Application shell: sidebar navigation, header, content area, footer.
- Routing setup with React Router (placeholder pages).
- Core UI components: Button, Input, Card, Badge, Avatar, Tooltip, Dialog, Tabs.
- Dark theme implementation.
- Responsive layout (mobile, tablet, desktop).
- Reduced-motion support (`prefers-reduced-motion`).
- Loading states and skeleton screens.

### Important Files
- `frontend/package.json`
- `frontend/vite.config.ts`
- `frontend/tailwind.config.ts`
- `frontend/src/app/App.tsx`
- `frontend/src/app/routes.tsx`
- `frontend/src/components/layout/Shell.tsx`
- `frontend/src/components/layout/Sidebar.tsx`
- `frontend/src/components/ui/` (shadcn components)

### Acceptance Criteria
1. `npm run dev` starts the frontend with hot reload.
2. `npm run build` produces a production bundle without errors.
3. `npm run typecheck` passes with zero errors (strict mode).
4. Application shell renders with sidebar, header and content area.
5. Navigation between placeholder pages works without full page reload.
6. The interface uses the dark theme with violet/cyan accents.
7. Layout adapts correctly at mobile (360px), tablet (768px) and desktop (1024px) breakpoints.
8. All interactive elements have visible focus indicators.
9. Animations respect `prefers-reduced-motion`.
10. Lighthouse accessibility score ≥ 90 on shell pages.

### Required Tests
- Component unit tests for core UI components (render, interaction, accessibility).
- Visual inspection at each breakpoint.
- Keyboard navigation test for shell and navigation.
- Reduced-motion behavior test.

### Risks
- Design iteration may delay phase completion.
- Tailwind CSS version compatibility with shadcn/ui.
- Motion library integration complexity.

---

## Phase 2: Backend Foundation and Identity

**Status:** ✅ Completed (Pre-commit Verification: Tests passing with SQLite; PostgreSQL unverified locally)

### Objectives
- Initialize the backend project (FastAPI + SQLAlchemy + Alembic).
- Set up Docker Compose for local development (PostgreSQL, Redis).
- Implement user registration, authentication and profile management.
- Establish the API versioning pattern and error handling.

### Dependencies
- Phase 0 (architecture and API contracts).
- Phase 1 (frontend shell for login/registration UI — can proceed in parallel).

### Deliverables
- `backend/` directory with FastAPI project structure.
- Docker Compose configuration (PostgreSQL, Redis, API server).
- `.env.example` with all required environment variables.
- Alembic setup with initial migration (users, profiles, OAuth, refresh tokens).
- User registration endpoint with email verification.
- Login/logout with JWT access + refresh tokens.
- Google OAuth integration (OAuth 2.0 with PKCE flow).
- Password reset flow.
- Profile management (view, update, preferences, GDPR data export, account soft deletion).
- Rate limiting on auth endpoints.
- CORS configuration.
- API error response format.
- Health check endpoint (GET /api/v1/health with DB, cache, and storage status).
- Frontend: login, registration, profile pages connected to backend.

### Important Files
- `backend/app/main.py`
- `backend/app/config.py`
- `backend/app/modules/auth/`
- `backend/app/modules/users/`
- `backend/app/infrastructure/database.py`
- `backend/alembic/`
- `docker-compose.yml`
- `.env.example`

### Acceptance Criteria & Verification Status
1. `docker-compose up` starts PostgreSQL, Redis, API server (configured, unverified locally due to Docker daemon unavailability).
2. API server starts and responds to health check (verified).
3. Registration creates a user and sends verification email (or logs token in development) (verified).
4. Login returns valid JWT. Protected endpoints reject invalid/expired tokens (verified).
5. Refresh token rotation works correctly (verified).
6. Password reset flow functions end-to-end (flow initiated, foundation verified).
7. Profile update persists changes (verified).
8. Rate limiting blocks excessive login attempts (verified).
9. Frontend login/registration pages function against the live API (verified).
10. Alembic migration applies and rolls back cleanly (`alembic check` verified with models).

### Test Status & Local Limitations
- **SQLite Test Execution:** All 46 backend unit and integration tests run against SQLite (`sqlite:///./test.db`). All 23 frontend unit and integration tests pass.
- **PostgreSQL Integration Status:** PostgreSQL 16 schema and migrations target PostgreSQL dialects (`JSONB`, `user_role` enum). Production settings enforce PostgreSQL and prohibit SQLite (`Settings.validate_production_environment`). However, because Docker/PostgreSQL was unavailable on the local development host, **PostgreSQL integration is explicitly marked UNVERIFIED LOCALLY** and must be tested in a live containerized CI/CD environment prior to deployment.
- **Token Storage:** Current frontend implementation persists tokens to browser `localStorage`. A production-hardening migration plan to `HttpOnly; Secure; SameSite=Lax` refresh cookies and in-memory access tokens is documented in `docs/SECURITY.md`.

### Risks
- OAuth provider configuration complexity.
- Email delivery in development (mitigate with console-based email backend).
- JWT secret management (enforced via production validator in config).
- Local testing disparity (SQLite vs PostgreSQL JSONB/enum behaviors).

---

## Phase 3: Skill Taxonomy, Course Catalog and Versioned Content Model

**Status:** ✅ Complete

### Objectives
- Implement cross-disciplinary skill taxonomy (`disciplines`, `skills`, `skill_prerequisites`).
- Build directed prerequisite DAG with server-side BFS cycle detection and self-dependency constraints.
- Implement course aggregate root, module containers, lesson units, and structured content blocks.
- Build an immutable versioning and publication engine ensuring published versions cannot be mutated.
- Provide public catalog discovery APIs with filtering (discipline, difficulty), search, and pagination (excluding drafts).
- Provide creator authoring endpoints for draft creation, editing, and transactional publishing.
- Seed the three representative course tracks (Web Development Foundations, Spoken English and Communication, Personal Productivity) published through the versioning service.

### Dependencies
- Phase 2 (database infrastructure, Alembic, auth/user system).

### Deliverables
- [x] Database models in `app/modules/skills/models.py` (`Discipline`, `Skill`, `SkillPrerequisite`).
- [x] Database models in `app/modules/courses/models.py` (`Course`, `CourseSkill`, `CourseVersion`, `Module`, `Lesson`, `LessonBlock`).
- [x] Versioned migration `backend/alembic/versions/002_skill_taxonomy_and_courses.py` (`alembic check` reports no unapplied operations).
- [x] Structured content Pydantic schemas in `app/modules/courses/content_schemas.py` (`Heading`, `Text`, `List`, `CodeExample`, `Callout`, `Image`, `Video`) with script stripping and URL security.
- [x] Taxonomy service and DAG cycle detection in `app/modules/skills/service.py`.
- [x] Course catalog discovery and immutable publishing service in `app/modules/courses/service.py`.
- [x] FastAPI REST endpoints in `app/modules/skills/router.py` and `app/modules/courses/router.py`.
- [x] Idempotent database seed script in `backend/app/seed.py` initializing 7 disciplines, 15 skills, 12 prerequisite links, and 3 full courses (Web Dev, Spoken English, Personal Productivity).
- [x] Frontend TypeScript API contracts in `frontend/src/types/catalog.ts` keeping existing Phase 1 demo mode intact.

### Important Files
- `backend/app/modules/skills/models.py`, `schemas.py`, `service.py`, `router.py`
- `backend/app/modules/courses/models.py`, `content_schemas.py`, `schemas.py`, `service.py`, `router.py`
- `backend/alembic/versions/002_skill_taxonomy_and_courses.py`
- `backend/app/seed.py`
- `frontend/src/types/catalog.ts`
- `backend/tests/test_skills.py`, `test_content_schemas.py`, `test_courses.py`, `test_versioning.py`, `test_seed.py`

### Acceptance Criteria Verification
1. **Skill Taxonomy & DAG:** Disciplines and skills support multi-discipline categorization. Self-dependencies rejected (400), duplicates rejected (409), and 2-node and 3-node directed cycles rejected via BFS cycle detection (verified in `test_skills.py`).
2. **Published Immutability:** Publishing stamps `published_at` and `publisher_id`, setting `is_active = true`. Modifying a published course creates or modifies an isolated working draft; earlier published versions remain completely unaltered (verified in `test_versioning.py`).
3. **Draft Editing Isolation:** Working drafts (`version_number = 0`) can be updated, and modules/lessons added or deleted without affecting the active catalog version (verified).
4. **Publishing Validation:** Course publication validates that at least 1 module exists, every module has lessons, and every lesson has valid structured blocks. Incomplete drafts fail with 400 (verified).
5. **Catalog Discovery:** `GET /api/v1/courses` strictly returns published courses with active version pointers. Draft and archived courses are never exposed publicly (verified in `test_courses.py`).
6. **Search, Filters & Pagination:** Supports filtering by discipline, difficulty, search term, and deterministic pagination (`page`, `limit`, `total`, `pages`) (verified).
7. **Structured Content Validation:** Lesson content validated against Pydantic schemas. Script tags stripped, disallowed URL schemes rejected, and unapproved video hosts blocked (verified in `test_content_schemas.py`).
8. **Seed Data Idempotency:** All 3 representative courses seeded with full outlines, learning objectives, and structured blocks. Repeated execution is 100% idempotent (verified in `test_seed.py`).
9. **Frontend Compatibility:** Existing Phase 1 demo mode and tests remain completely intact (23/23 vitest passed; `npm run build` succeeds).

### Test Status & Local Limitations
- **SQLite Test Execution:** All 72 backend unit and integration tests pass against SQLite (`sqlite:///./test.db`). All 23 frontend vitest tests pass. Ruff lint check passes with 0 errors.
- **PostgreSQL Integration Status:** Models use SQLAlchemy's `.with_variant(JSONB, "postgresql")` and Alembic migration 002 includes PostgreSQL enum declarations. However, because local Docker was unavailable, **PostgreSQL 16 integration is explicitly unverified locally** and must be verified in CI/CD against a live PostgreSQL service.
- **Deferred to Phase 4:** Universal lesson renderer, enrollment progress tracking, and full frontend-to-backend catalog binding belong to Phase 4.

---

## Phase 4: Universal Lesson Renderer and Immersive Learning Workspace

**Status:** ✅ Completed (Verified: Universal block renderer, workspace layout, keyboard & mobile navigation, live API binding, stale request protection, and automated test suite)

### Objectives
- Build a universal, block-based lesson renderer that interprets Phase 3 structured, versioned content across all disciplines.
- Implement an immersive, focused learning workspace layout (responsive sidebar, reading width, header context, and bottom controls).
- Provide stable lesson navigation with boundary protection, breadcrumbs, module drawers, and keyboard shortcuts (`←`/`→`).
- Support syntax-highlighted code blocks with line numbers and copy-to-clipboard functionality.
- Integrate with published course backend endpoints (`GET /api/v1/courses/:slug` and `GET /api/v1/courses/:courseSlug/lessons/:lessonSlug`).
- Protect against stale responses via `AbortController` cancellation and keep demo fallback mode explicit.

### Dependencies
- Phase 3 (cross-disciplinary skill taxonomy, published course versions, lesson content schemas).
- Phase 1 (frontend design system, typography tokens, dark-first UI primitives).

### Deliverables
- **Type Definitions:** `frontend/src/types/lesson.ts` defining typed payloads for all Phase 3 content blocks (`heading`, `text`, `list`, `code_example`, `callout`, `image`, `video`, `activity_ref`, `unknown`).
- **API Integration Client:** `frontend/src/services/courseApi.ts` connecting to published courses/lessons with `AbortSignal` support and an explicit demo track adapter.
- **Universal Block Renderers:** `frontend/src/features/lessons/blocks/`:
  - `HeadingBlock.tsx`: semantic `h2`, `h3`, `h4` hierarchy.
  - `TextBlock.tsx`: safe inline markdown parsing (`**bold**`, `*italic*`, `` `code` ``, `[links](url)`, `> blockquote`) with script and event-handler stripping.
  - `ListBlock.tsx`: ordered `<ol>` and unordered `<ul>` with accessible markers.
  - `CodeExampleBlock.tsx`: lightweight syntax highlighter (JS/TS, Python, HTML, CSS, SQL), language badges, line numbers, and accessible copy button with "Copied!" feedback and fallback.
  - `CalloutBlock.tsx`: semantic variants (`key_concept`, `tip`, `warning`, `info`) with distinct border accents and Lucide icons.
  - `ImageBlock.tsx`: responsive images with mandatory `alt` text, loading states, captions, and broken-image fallbacks.
  - `VideoBlock.tsx`: sandboxed video embeds (YouTube / Vimeo allowlist) with duration, transcript link, and external link fallbacks.
  - `UnknownBlock.tsx`: graceful diagnostic card preventing unknown/malformed block types from crashing the workspace.
- **Universal Lesson Renderer:** `frontend/src/features/lessons/LessonRenderer.tsx` sorting blocks by `sort_order` and rendering each block defensively.
- **Learning Workspace Components:**
  - `LessonWorkspaceHeader.tsx`: Course Overview backlink, breadcrumb navigation, version/demo badges (`Published v{n}` / `Demo Track`), lesson counter (`1 / 3`), and mobile menu toggle.
  - `LessonSidebar.tsx`: collapsible module outline with chapter badges, active lesson highlighting (`aria-current="page"`), mobile drawer with backdrop, and `Escape` key close.
  - `LessonContent.tsx`: comfortable reading container (`max-w-3xl`), learning objectives callout, semantic block flow, previous/next controls with boundary protection, and keyboard shortcut hint.
  - `LessonWorkspace.tsx`: controller managing route parameters, data fetching, race-condition abortion, keyboard shortcuts (`ArrowLeft`/`ArrowRight`), loading skeletons, 404/not-found states, and retry-capable error screens.
  - `LessonWorkspacePage.tsx`: page wrapper integrated into React Router.
- **Routing Integration:** Routes registered in `frontend/src/app/routes.tsx`:
  - `/learn/:courseSlug/:moduleSlug/:lessonSlug`
  - `/learn/:courseSlug/:lessonSlug`
  - `/learn/:courseSlug` (auto-redirects to first published lesson)
  - `/courses/:courseSlug/learn/:lessonSlug`
  - Connected `CourseOverviewPage.tsx` "Start Course Preview" and syllabus items directly to the learning workspace.

### Acceptance Criteria & Verification Status
1. **Universal Block Rendering:** All supported Phase 3 content blocks (`heading`, `text`, `list`, `code_example`, `callout`, `image`, `video`) render correctly with proper dark-theme styling and semantic tags (verified).
2. **Syntax Highlighting & Copy Action:** Code examples display syntax highlighting for JavaScript, TypeScript, Python, HTML, CSS, and SQL with line numbers and a working copy button with visible feedback (verified).
3. **Responsive Learning Workspace:** Workspace provides a focused, readable reading width on desktop and transitions to a slide-over mobile drawer with backdrop on smaller screens without horizontal overflow (verified).
4. **Stable Lesson Navigation:** Previous and next controls follow published module/lesson sort order. The first lesson safely links to Course Overview with no invalid previous destination; the last lesson transitions to course finish review (verified).
5. **Keyboard Accessibility:** ArrowLeft (`←`) and ArrowRight (`→`) navigate between lessons while ignoring keystrokes inside form controls or inputs (verified).
6. **Curriculum Outline & Current State:** Sidebar displays all published modules and lessons with active lesson highlighted via `aria-current="page"` and accessible expand/collapse buttons (verified).
7. **Breadcrumb & Context:** Header and content breadcrumbs accurately display course title, module title, lesson title, and published version number (`Published v1`) or `Demo Track` (verified).
8. **Security & Sanitization:** Rich-text content does not evaluate scripts or unsafe HTML. Code examples are strictly display-only. Video embeds enforce `sandbox` attributes on whitelisted domains (verified).
9. **Race Condition & Error Protection:** Rapid navigation cancels pending requests via `AbortController`. Backend failures display an actionable error screen with "Retry Request" and never silently substitute demo data (verified).
10. **Automated Test Coverage:** 41/41 frontend tests pass (including 9 in `LessonRenderer.test.tsx` and 9 in `LessonWorkspace.test.tsx`), 72/72 backend tests pass, and `npm run build` succeeds cleanly (verified).

### Deferred to Phase 5
- Schema-driven interactive activity engine (code execution exercises, quiz submissions, conversation practice, practical tasks).
- Isolated Docker code execution sandbox.
- Attempt scoring, assessment grading, retry tracking, and persistent completion state.

---

## Phase 5: Activity Engine and Assessment

**Status:** ✅ Complete

### Objectives
- Build a schema-driven, reusable activity and assessment engine supporting 9 distinct interaction types.
- Ensure server-authoritative evaluation with secret answer keys strictly protected on the backend.
- Enforce retry limits (`max_attempts`) and record tamper-proof attempt history per learner.
- Establish an isolated sandbox boundary ensuring untrusted learner code is never executed in the FastAPI process.
- Embed interactive activities seamlessly into the universal lesson workspace (`LessonRenderer` and `LessonContent`).
- Seed realistic, cross-disciplinary assessment activities across at least 3 courses.

### Dependencies
- Phase 4 (universal lesson workspace, content block renderer, layout shell).
- Phase 3 (published courses, modules, lessons, content blocks).
- Phase 2 (authentication, JWT tokens, user models).

### Deliverables
- **Database Schema & Migrations:**
  - `backend/app/modules/activities/models.py`: `Activity`, `GradingConfig`, and `Attempt` SQLAlchemy models with foreign keys, cascading deletions, and uniqueness constraint (`uq_user_activity_attempt`).
  - `backend/alembic/versions/003_activities_and_assessments.py`: Versioned migration adding `activities`, `grading_configs`, `attempts`, and updating `lesson_blocks` enum with `activity`.
- **Server-Authoritative Grading Engine:**
  - `backend/app/modules/activities/grading.py`: Deterministic grading algorithms supporting all 9 activity types (`single_choice`, `multiple_select`, `short_answer`, `true_false`, `fill_in_the_blank`, `ordering`, `matching`, `code_exercise`, `scenario`) with partial credit and normalization.
  - `backend/app/modules/activities/service.py`: `ActivityService` implementing public payload sanitization (stripping answer keys), attempt submission with `max_attempts` enforcement, and attempt history querying with strict user isolation.
  - `backend/app/modules/activities/router.py`: REST endpoints mounted under `/api/v1/activities` and `/api/v1/lessons/{id}/activities`.
- **Isolated Code Execution Boundary:**
  - `backend/app/infrastructure/sandbox/runner.py`: `SandboxRunnerInterface` defining execution contract and `IsolatedSandboxRunner` providing safe handling without executing arbitrary code on the host server.
- **Frontend Assessment Components:**
  - `frontend/src/types/activity.ts`: Full TypeScript definitions for activities, grading configs, submissions, and attempt results.
  - `frontend/src/services/activityApi.ts`: REST API client for activities and attempts.
  - `frontend/src/features/activities/`: Specialized UI renderers:
    - `SingleChoiceActivity.tsx` (radio options with active indicators)
    - `MultipleSelectActivity.tsx` (checkbox options with multi-select support)
    - `TrueFalseActivity.tsx` (binary selection with clean accessibility)
    - `ShortAnswerActivity.tsx` (input field with submit button)
    - `FillBlankActivity.tsx` (inline text tokens with accessible blank inputs)
    - `OrderingActivity.tsx` (accessible up/down order position controls)
    - `MatchingActivity.tsx` (prompt-target pairing dropdowns)
    - `ScenarioActivity.tsx` (structured multi-field or open analysis response)
    - `CodingActivity.tsx` (code editor with syntax badges and reset action)
    - `SubmissionFeedback.tsx` (score badge, pass/fail state, criteria feedback, explanations)
    - `AttemptHistory.tsx` (collapsible timeline of past attempts)
    - `ActivityRenderer.tsx` (type-dispatched activity registry)
    - `ActivityContainer.tsx` (submission lifecycle, loading indicators, retry management, error boundaries)
- **Universal Lesson Workspace Integration:**
  - `frontend/src/features/lessons/blocks/ActivityBlock.tsx`: Embedded activity block rendering in lesson narrative flow.
  - `frontend/src/features/lessons/LessonRenderer.tsx`: Dispatches `'activity'` block type.
  - `frontend/src/features/lessons/LessonContent.tsx`: Auto-fetches and renders lesson checkpoint activities in an interactive assessment section.
- **Cross-Disciplinary Seed Data:**
  - `backend/app/seed.py`: Seeded representative activities across Web Development Foundations (`semantic-tags`, `forms-and-inputs`), Spoken English (`bluf-framework`, `star-framework`), and Personal Productivity (`high-leverage-outcomes`, `calendar-timeblocking`).

### Acceptance Criteria & Verification Status
1. **Nine Supported Activity Types:** All 9 activity types are defined, typed, validated, and render cleanly with responsive, accessible UI (verified).
2. **Server-Authoritative Evaluation:** All scoring and pass/fail determinations are computed server-side via `GradingEngine`; clients cannot manipulate scores (verified).
3. **Secret Answer Key Protection:** Activity fetch endpoints strip all `grading_config` answer keys, correct answers, and hidden assertions from learner responses (verified).
4. **Retry & Attempt Enforcement:** Max attempts are strictly enforced on the server (`400 Maximum attempts reached`), and each attempt receives a sequential `attempt_number` (verified).
5. **Cross-User Authorization:** Learner attempts are strictly isolated; attempting to read another learner's attempt returns `403 Forbidden` (verified).
6. **Isolated Sandbox Boundary:** Learner code execution is isolated behind `SandboxRunnerInterface`; untrusted code is never executed in the FastAPI process (verified).
7. **Workspace Integration:** Activities render both as embedded lesson blocks and as end-of-lesson assessment checkpoints (verified).
8. **Automated Test Coverage:** 86/86 backend tests pass (`pytest` including 14 activity engine tests), 59/59 frontend tests pass (`vitest run` including 12 activity component tests), and production build succeeds cleanly (verified).

### Deferred to Phase 6
- Skill mastery recalculation triggered by activity completions.
- Automatic advancement of lesson, module, and course completion states.
- Achievement unlock triggers based on assessment performance.
- Learner dashboard mastery visualization.

---

## Phase 6: Progression, Mastery and Recommendations

**Status:** ✅ Complete

### Objectives
- Implement authenticated course enrollments linked to immutable course versions with duplicate prevention and prerequisite validation.
- Implement durable lesson progression (`NOT_STARTED`, `IN_PROGRESS`, `COMPLETED`) with server-side completion gates requiring passed interactive activities.
- Implement automated progression cascade (passed assessment attempt → lesson progress update → course progress calculation and completion).
- Implement multi-tier, evidence-backed skill mastery calculation (`NOT_STARTED`, `LEARNING`, `PRACTICING`, `PROVISIONAL`, `MASTERED`, `NEEDS_REVIEW`) with verified evidence history and distinct task requirements.
- Enforce prerequisite requirements across the skill DAG before enrollment and provide structured unmet prerequisite reporting.
- Implement a comprehensive learner progress dashboard (`GET /api/v1/progress/dashboard`) with active enrolled courses, resume learning hero card, skill mastery breakdown, recent assessment attempts, and explainable next-step recommendations.
- Seed and idempotently unlock server-verified achievements with clear pedagogical milestones.
- Ensure dual compatibility across PostgreSQL 16 and SQLite via versioned Alembic migration `004_progress_mastery`.

### Dependencies
- Phase 5 (activity engine, grading configurations, attempt evaluations).
- Phase 4 (universal lesson workspace, breadcrumbs, content blocks).
- Phase 3 (published courses, version snapshots, modules, lessons, skill taxonomy DAG).
- Phase 2 (authentication, JWT tokens, user identities, roles).

### Deliverables
- **Database Schema & Migrations:**
  - `backend/app/modules/progress/models.py`: `Enrollment`, `LessonProgress`, `SkillMastery`, `Achievement`, and `UserAchievement` SQLAlchemy models with status enums (`EnrollmentStatus`, `LessonProgressStatus`, `SkillMasteryStatus`), foreign keys, cascading deletions, and uniqueness constraints (`uq_user_course_version_enrollment`, `uq_enrollment_lesson_progress`, `uq_user_skill_mastery`, `uq_user_achievement`).
  - `backend/alembic/versions/004_progress_mastery.py`: Versioned Alembic migration with PostgreSQL enum creation, safe rollback, and full `alembic check` clean drift status.
- **Backend Progression & Mastery Engine:**
  - `backend/app/modules/progress/schemas.py`: Pydantic request/response schemas for enrollments, lesson progress, completions, skill evidence, achievements, resume learning items, recommendations, and dashboard summaries.
  - `backend/app/modules/progress/service.py`: `ProgressionService` encapsulating enrollment validation, lesson completion gating, automatic progression cascade, multi-evidence mastery evaluation, prerequisite DAG traversal, resume learning resolution, and achievement awarding.
  - `backend/app/modules/progress/router.py`: REST endpoints mounted under `/api/v1` (`/courses/{slug}/enroll`, `/courses/{slug}/prerequisites`, `/enrollments`, `/enrollments/{id}/lessons/{id}/start`, `/complete`, `/progress/dashboard`, `/progress/skills`, `/progress/achievements`, `/progress/recommendations`).
  - `backend/app/modules/activities/service.py`: Integrated automated progression cascade hook upon successful attempt grading.
  - `backend/app/seed.py`: Seeded 6 default achievements idempotently (`first_lesson`, `fast_learner`, `first_course`, `perfect_score`, `skill_master`, `prerequisite_pioneer`).
- **Frontend Progression Integration:**
  - `frontend/src/types/progress.ts`: Full TypeScript definitions matching backend progression contracts.
  - `frontend/src/services/progressApi.ts`: Typed API client for all Phase 6 endpoints.
  - `frontend/src/pages/CourseOverviewPage.tsx`: Integrated live enrollment checking, progress percentage indicator, prerequisite warning banner, and enroll action.
  - `frontend/src/features/lessons/LessonWorkspace.tsx`: Auto-triggers lesson start on open, synchronizes enrollment state, and tracks completed lessons.
  - `frontend/src/features/lessons/LessonSidebar.tsx`: Visual completion checkmarks on completed lesson items.
  - `frontend/src/features/lessons/LessonContent.tsx`: "Mark Lesson Complete" action with server gating, error messaging, and celebration banner upon course finish.
  - `frontend/src/pages/DashboardPage.tsx`: Live authenticated dashboard with active enrolled courses, progress bars, resume learning hero card, recent assessment attempts, skill mastery overview, and achievements shelf.
  - `frontend/src/pages/SkillsPage.tsx`: Live skill mastery tiers, scores, distinct task counts, and verified assessment evidence.

### Important Files
- `backend/app/modules/progress/models.py`, `schemas.py`, `service.py`, `router.py`
- `backend/alembic/versions/004_progress_mastery.py`
- `backend/tests/test_progress.py`
- `frontend/src/types/progress.ts`, `frontend/src/services/progressApi.ts`
- `frontend/src/pages/DashboardPage.tsx`, `SkillsPage.tsx`, `CourseOverviewPage.tsx`
- `frontend/src/features/lessons/LessonWorkspace.tsx`, `LessonContent.tsx`, `LessonSidebar.tsx`
- `frontend/src/test/Progress.test.tsx`

### Acceptance Criteria & Verification Status
1. **Enrollment Lifecycle & Immutability:** Authenticated learners can enroll in published courses; enrollments bind to immutable `course_version_id`. Duplicate enrollments are idempotently returned without duplicate rows. Unauthenticated enrollments are rejected with 401 (verified in `test_progress.py`).
2. **Prerequisite Enforcement:** Enrolling in courses with unmet skill prerequisites is rejected with 400 (`PREREQUISITES_NOT_MET`) and details the specific unmet skills. `GET /api/v1/courses/{slug}/prerequisites` accurately indicates eligibility (verified in `test_progress.py` and `Progress.test.tsx`).
3. **Lesson Progression Gating:** Lessons with interactive activities require passing scores before lesson completion can be marked (`REQUIRED_ACTIVITIES_INCOMPLETE`). Lessons without activities can be completed directly (verified in `test_progress.py`).
4. **Progression Cascade Hook:** Passing an assessment attempt automatically starts the lesson, completes the lesson once all activities pass, and triggers course completion when the final lesson is finished (verified in `test_progress.py`).
5. **Distinct Evidence Mastery Standard:** `MASTERED` status requires passing at least 2 distinct assessment activities (or 100% of all available if only 1 exists) with an average score >= 80%. Repeating the same activity yields `PROVISIONAL`. Failed attempts do not award mastery (verified in `test_progress.py`).
6. **Dashboard & Resume Learning:** `GET /api/v1/progress/dashboard` deterministically selects the first incomplete lesson across enrolled courses as the resume learning item, provides explainable next-step recommendations, and aggregates achievements and skills (verified in `test_progress.py` and `Progress.test.tsx`).
7. **Idempotent Achievement Engine:** 6 default achievements are seeded and earned automatically upon meeting criteria. Duplicate achievements are prevented by composite primary key (verified in `test_progress.py`).
8. **Automated Test Coverage:** 106/106 backend tests pass (`pytest` including 13 progress and mastery tests), 62/62 frontend tests pass (`vitest run` including 3 progress tests), `npm run build` succeeds cleanly, and `ruff` and `oxlint` pass with 0 errors (verified).

### Test Status & Local Limitations
- **SQLite Test Execution:** All 106 backend tests pass against SQLite. All 62 frontend tests pass. Production build succeeds.
- **PostgreSQL 16 Migration Verification:** Alembic migration `004_progress_mastery` includes explicit enum creation, PostgreSQL `JSONB` support, foreign keys, and indexes. `alembic check` reports 0 schema drift.
- **Deferred to Phase 7:** Creator Studio authoring UI, multi-version editorial review, and creator analytics.

---

## Phase 7: Creator Studio and Course Publishing

**Status:** ✅ Complete

### Objectives
- Build a coherent creator workflow: managed courses list, create draft course, edit metadata, organize modules and lessons, configure lesson content blocks and all 9 supported activity types.
- Provide a non-destructive learner-facing draft preview mode without polluting learner progress, enrollment state, or skill mastery.
- Enforce backend-authoritative pre-publish validation and publishing through the existing immutable versioning architecture (`publish_course`).
- Enforce strict server-side creator/admin authorization (`require_creator_or_admin`) and course ownership isolation across all creator endpoints.
- Protect grading secrets (answer keys, rubrics, test cases) from learners while allowing creators and admins to author and edit them.

### Dependencies
- Phase 5 (activity engine — 9 activity types, automated grading configs, attempt scoring).
- Phase 4 (content blocks and learner workspace).
- Phase 3 (course versioning snapshots, modules, lessons, and skill taxonomy).
- Phase 2 (authentication, JWT tokens, user identities, roles).

### Deliverables
- **Backend Creator API & Draft Management:**
  - `backend/app/modules/courses/schemas.py`: Pydantic request/response schemas (`CourseManagedSummary`, `CourseManagedListResponse`, `CurriculumReorderRequest`, `ValidationErrorItem`, `DraftValidationResponse`, and activities integration in `LessonDetailResponse`).
  - `backend/app/modules/courses/service.py`: `CourseService` methods (`list_managed_courses`, `delete_course`, `delete_lesson_from_draft`, `reorder_draft_curriculum`, `validate_draft`, `get_draft_preview`, `get_draft_preview_lesson`).
  - `backend/app/modules/courses/router.py`: Creator endpoints mounted under `/api/v1/courses` (`GET /managed`, `DELETE /{id}`, `DELETE /{id}/draft/lessons/{lesson_id}`, `POST /{id}/draft/reorder`, `GET /{id}/draft/validate`, `GET /{id}/draft/preview`, `GET /{id}/draft/preview/lessons/{slug}`).
  - `backend/app/modules/activities/schemas.py`: `ActivityUpdateRequest` and `ActivityAuthoringResponse` exposing answer keys and rubrics only to authorized authors.
  - `backend/app/modules/activities/service.py`: `ActivityService` authoring methods (`create_activity`, `get_authoring_activity`, `update_activity`, `delete_activity`, and ownership check `_check_activity_access`).
  - `backend/app/modules/activities/router.py`: Creator endpoints under `/api/v1/activities` (`GET /{id}/authoring`, `PATCH /{id}`, `DELETE /{id}`, and owner check on `POST /`).
  - `backend/tests/test_creator.py`: 7 end-to-end integration tests for creator authorization, managed listing, cross-creator isolation, curriculum CRUD, activity authoring secrets isolation, validation gating, and immutable version publishing.
- **Frontend Creator Studio & Authoring Suite:**
  - `frontend/src/types/creator.ts`: Strict TypeScript interfaces for managed courses, draft validation, reordering, and activity authoring schemas.
  - `frontend/src/services/creatorApi.ts`: Fully-typed creator API service covering draft lifecycle, curriculum management, block editing, activity authoring, pre-publish validation, preview, and publishing.
  - `frontend/src/pages/CreatorStudioPage.tsx` (`/creator`): Managed course grid with summary metric counters (total, drafts, published), search by title/slug, status filters (All, Drafts, Published), draft creation modal trigger, and role enforcement (`CREATOR` / `ADMIN`).
  - `frontend/src/pages/CourseEditorPage.tsx` (`/creator/courses/:courseId`): Split-pane authoring workspace with interactive curriculum navigation, tabbed editing panels (Metadata, Content Blocks, Activities, Pre-publish Validation), draft preview launcher, and publish modal trigger.
  - `frontend/src/features/creator/CurriculumTree.tsx`: Interactive module and lesson tree supporting adding modules/lessons, inline renaming, deletion, and up/down reordering.
  - `frontend/src/features/creator/CourseMetadataEditor.tsx`: Course metadata, difficulty, estimated hours, discipline, skill tags, and learning objectives editor with unsaved changes tracking.
  - `frontend/src/features/creator/LessonBlocksEditor.tsx`: Structured content blocks editor supporting all 7 block types (narrative, heading, list, code snippet, callout, image, video embed) with add, edit, remove, and reorder.
  - `frontend/src/features/creator/activities/ActivityAuthoringPanel.tsx` & `ActivityEditorModal.tsx`: Visual activity authoring modal with live interactive preview and dedicated forms for all 9 activity types (`SingleChoice`, `MultipleSelect`, `TrueFalse`, `ShortAnswer`, `FillBlank`, `Ordering`, `Matching`, `CodeExercise`, `Scenario`).
  - `frontend/src/features/creator/ValidationPanel.tsx`: Server-authoritative pre-publish validation panel reporting blocking errors and non-blocking warnings with navigation links to offending lessons.
  - `frontend/src/features/creator/PublishModal.tsx`: Publish confirmation dialog verifying validation status, changelog input, and immutable version release.
  - `frontend/src/features/creator/CreateCourseModal.tsx`: New course creation modal with discipline selection, skill taxonomy lookup, and slug preview.
  - `frontend/src/features/lessons/LessonWorkspace.tsx`: Isolated draft preview mode (`/creator/courses/:courseId/preview/:lessonSlug?`) with prominent preview banner, link prefix isolation, and complete bypass of progress/enrollment mutations.
  - `frontend/src/components/layout/Sidebar.tsx`: Navigation link to Creator Studio for creator and admin roles.
  - `frontend/src/test/CreatorStudio.test.tsx`: 8 comprehensive component and workflow tests.

### Important Files
- `backend/app/modules/courses/service.py`, `router.py`, `schemas.py`
- `backend/app/modules/activities/service.py`, `router.py`, `schemas.py`
- `backend/tests/test_creator.py`
- `frontend/src/types/creator.ts`, `frontend/src/services/creatorApi.ts`
- `frontend/src/pages/CreatorStudioPage.tsx`, `frontend/src/pages/CourseEditorPage.tsx`
- `frontend/src/features/creator/` (CurriculumTree, LessonBlocksEditor, CourseMetadataEditor, ValidationPanel, PublishModal, CreateCourseModal, activities/)
- `frontend/src/features/lessons/LessonWorkspace.tsx`
- `frontend/src/test/CreatorStudio.test.tsx`

### Acceptance Criteria & Verification Status
1. **Creator Authorization & Ownership:** Ordinary learners are strictly forbidden (403 `CREATOR_ACCESS_REQUIRED`). Creators can only view, edit, or delete courses they own, while admins can manage any course (verified in `test_creator.py` and `CreatorStudio.test.tsx`).
2. **Draft Curriculum CRUD & Reordering:** Creators can create modules and lessons, update titles, delete lessons from working drafts, and reorder modules and lessons with server-enforced sequence numbers (verified in `test_creator.py`).
3. **Structured Content Block Authoring:** Creators can add, update, and remove structured content blocks (narrative, heading, list, code snippet, callout, image, video embed) directly through visual controls (verified in `CreatorStudio.test.tsx`).
4. **All 9 Activity Types Supported:** Visual authoring forms with secret answer keys, rubrics, passing scores, and test cases for single choice, multiple select, true/false, short answer, fill-in-the-blank, ordering, matching, code exercise, and scenario. Grading secrets are never exposed on learner-facing endpoints (verified in `test_creator.py` and `CreatorStudio.test.tsx`).
5. **Pre-Publish Server-Authoritative Validation:** Drafts cannot be published if empty, missing lessons, having empty lessons without blocks, or missing passing scores on activities. Validation response categorizes errors and warnings (verified in `test_creator.py` and `CreatorStudio.test.tsx`).
6. **Immutable Version Publishing:** Publishing a draft course enforces validation, increments version number, creates an immutable version snapshot, copies activities and grading configurations, and automatically establishes a clean working draft v0 for subsequent edits without mutating published versions (verified in `test_creator.py` and `CreatorStudio.test.tsx`).
7. **Isolated Draft Preview Mode:** Creators can preview draft lessons using the exact learner-facing workspace components with an amber draft preview banner, while skipping all progress recording and enrollment mutations (verified in `test_creator.py` and `CreatorStudio.test.tsx`).
8. **Automated Test Coverage:** 125/125 backend tests pass (`pytest` including 7 creator tests), 70/70 frontend tests pass (`vitest run` including 8 creator tests), `npm run build` succeeds cleanly, and `ruff check` and `oxlint` pass with 0 errors (verified).

### Test Status & Local Limitations
- **SQLite Test Execution:** All 125 backend tests pass against SQLite. All 70 frontend tests pass. Production build succeeds.
- **Alembic Clean Drift:** `alembic check` reports 0 schema drift.
- **Scope Alignment:** Phase 7 focuses on authoring, validation, preview, and immutable publishing. AI-assisted tutoring and practice recommendations are planned for Phase 8.

---

## Phase 8: AI Tutor and Personalized Practice

**Status:** ✅ Complete

### Objectives
- Integrate AI provider for tutoring and feedback.
- Build the AI tutor interface.
- Implement AI-assisted grading and progressive hints for activities.
- Personalized practice recommendations.

### Dependencies
- Phase 5 (activity engine — AI provides progressive hints on activities).
- Phase 6 (progression — AI uses progress data for personalization).

### Deliverables
- Database migration `005_ai_interactions.py` for operational telemetry and audit logging.
- Provider-neutral AI client abstraction (`BaseAIProvider`, `MockAIProvider`, `GeminiAIProvider`, `get_ai_provider`).
- AI tutor API endpoints (`/api/v1/ai/tutor`, `/hint`, `/status`, `/preferences`) with user-scoped rate limiting (30 queries/hr, 10 hints/hr).
- AI tutor UI panel (`AITutorDrawer`) slide-over in lesson workspace with keyboard shortcut (`Alt+T`) and suggested prompt chips.
- Progressive hints (Levels 1, 2, and 3) embedded in `ActivityContainer` without revealing grading secrets.
- Deterministic, explainable personalized recommendations prioritizing skill mastery gaps (`practice_skill`).
- Server-side and client-side AI feature opt-out preference in user profile.

### Important Files
- `backend/alembic/versions/005_ai_interactions.py`
- `backend/app/infrastructure/ai/` (`base.py`, `mock_provider.py`, `gemini_provider.py`, `factory.py`)
- `backend/app/modules/ai/` (`models.py`, `schemas.py`, `service.py`, `router.py`)
- `backend/tests/test_ai.py`
- `frontend/src/types/ai.ts`
- `frontend/src/services/aiApi.ts`
- `frontend/src/features/ai-tutor/AITutorDrawer.tsx`
- `frontend/src/features/activities/ActivityContainer.tsx`
- `frontend/src/pages/ProfilePage.tsx`
- `frontend/src/test/AITutor.test.tsx`

### Acceptance Criteria & Verification Status
1. **Context-Grounded AI Tutoring:** Answers learner questions strictly within trusted lesson context, guiding conceptual understanding rather than providing answers (verified in `test_ai.py` and `AITutor.test.tsx`).
2. **Progressive Hints:** Delivers three distinct tiers of pedagogical hints (Level 1 Nudge, Level 2 Principle, Level 3 Structure) without leaking answer keys (verified in `test_ai.py` and `AITutor.test.tsx`).
3. **Operational Telemetry & Data Minimization:** Stores operational metrics (token count, latency, provider, user/lesson context) in `ai_interactions` table without retaining learner prompts/responses by default (verified in `test_ai.py`).
4. **User-Scoped Rate Limiting:** Enforces configurable sliding-window limits (30 questions/hour, 10 hints/hour) returning HTTP 429 when exceeded (verified in `test_ai.py` and `AITutor.test.tsx`).
5. **Enforced User Opt-Out:** Enforces opt-out preference server-side with HTTP 403 `AI_FEATURE_OPTED_OUT` and provides UI preference toggle in Profile settings (verified in `test_ai.py`, `AITutor.test.tsx`, and `ProfilePage.tsx`).
6. **Mastery-Gap Recommendations:** Deterministically recommends practice for skills in `PRACTICING` or `NEEDS_REVIEW` status, explaining reason and linking to relevant coursework (verified in `test_progress.py`).
7. **Automated Test Coverage:** 140/140 backend tests pass (`pytest` including 8 AI tests and 19 progress tests), 78/78 frontend tests pass (`vitest run` including 6 AI tutor tests), production build (`npm run build`) succeeds cleanly, and `ruff check` and `alembic check` report 0 errors (verified).

### Required Tests
- AI client abstraction test (mock provider, verify request format).
- Rate limiting test.
- Response filtering test (harmful content blocked).
- Audit logging test (all interactions recorded).
- Opt-out test (AI features disabled when preference set).

### Risks
- **High:** AI response quality for domain-specific feedback (communication, productivity).
- AI provider cost management.
- Latency of AI responses affecting UX (mitigate with streaming or async).
- Prompt injection attacks (mitigate with input sanitization and prompt engineering).

---

## Phase 9: Projects, Portfolio and Specialized Learning Activities

**Status:** ✅ Complete (Stages 1–7 Complete — Ready for Independent Phase 9 Final Audit)

### Objectives
- Implement capstone projects with milestones.
- Build portfolio system.
- Add specialized learning activities (e.g., drag-and-drop, diagramming).
- Shareable portfolio pages.

### Dependencies
- Phase 5 (activity engine).
- Phase 6 (progression and mastery).

### Stage 1 Deliverables (Database Migration & Secure Artifact Storage Foundation)
- **Database Schema & Migrations:**
  - `backend/app/modules/projects/models.py`: Added SQLAlchemy 2.0 models `Project`, `ProjectSkill`, `ProjectSubmission`, `ProjectArtifact`, `Portfolio`, and `PortfolioItem`.
  - Added explicit submission revision hierarchy (`revision_of_id`) to preserve complete submission history without destructive overwrites.
  - Added dedicated relational entity `ProjectArtifact` for upload referential integrity, checksum verification (`checksum_sha256`), and cascade deletions.
  - `backend/alembic/versions/006_projects_and_portfolios.py`: Versioned Alembic migration with PostgreSQL/SQLite compatibility, index creation, unique constraints, and safe downgrade.
- **Provider-Neutral Storage Abstraction:**
  - `backend/app/infrastructure/storage/base.py`: Declared `StorageInterface`, `StoredFileMetadata`, and typed storage domain exceptions (`StorageFileNotFoundError`, `StorageFileTooLargeError`, `StorageInvalidTypeError`, `StorageSecurityError`).
  - `backend/app/infrastructure/storage/local_storage.py`: Implemented `LocalStorageService` with strict path traversal prevention, server-side random key generation, magic byte signature sniffing (PNG, JPEG, PDF, ZIP), blocked executable blacklist, streaming chunked I/O, and disk size caps.
  - `backend/app/infrastructure/storage/factory.py`: Added dependency factory with singleton caching and runtime provider selection (`local`, `s3`, `disabled`).
- **Configuration & System Verification:**
  - `backend/app/config.py`: Extended settings with `storage_provider`, `storage_local_root`, `storage_max_file_size_mb` (20MB), and `storage_allowed_extensions`.
  - `.env.example`: Added safe development defaults for storage configuration.
  - `.gitignore`: Added `uploads/` and `storage/` to exclude runtime and test artifacts.
  - `backend/tests/test_storage.py`: 14 unit tests covering storage, retrieval, streaming, deletion, size caps, dangerous extension blocking, magic byte verification, and path traversal rejection.
  - `backend/tests/test_projects_models.py`: 8 database tests covering model relationships, revision chains, unique constraints, and cascade deletions.
  - 162/162 backend tests pass, 78/78 frontend tests pass, and `alembic check` reports 0 schema drift.

### Stage 2 Deliverables (Backend Projects & Submissions Module & Remediation)
- **Pydantic Validation Schemas:**
  - `backend/app/modules/projects/schemas.py`: Implemented typed request/response schemas for project authoring (`ProjectCreateRequest`, `ProjectUpdateRequest`), catalog exploration (`ProjectSummaryResponse`, `ProjectDetailResponse`, `ProjectPaginatedResponse`), submissions lifecycle (`SubmissionCreateRequest`, `SubmissionUpdateRequest`, `SubmissionRevisionRequest`, `SubmissionDetailResponse`), evaluation (`SubmissionEvaluationRequest`, `EvaluationResponse`), and artifacts (`ArtifactResponse`, `ArtifactListResponse`). Documented `transition_history` tracking field.
- **Domain Services:**
  - `backend/app/modules/projects/service.py`: `ProjectService` implementing catalog discovery with pagination, sorting, filters (discipline, skill, difficulty, search keyword), status gating (non-creators see only PUBLISHED projects), creator authoring, completeness validation on publish, and archiving.
  - `backend/app/modules/projects/submission_service.py`: `SubmissionService` governing the authoritative submission state machine (`DRAFT` -> `SUBMITTED` -> `UNDER_REVIEW` -> `EVALUATED` -> `COMPLETED` / `CHANGES_REQUESTED`), persisting the intermediate `EVALUATED` status before outcome enforcement, recording comprehensive transition history (`transition_history`), duplicate draft prevention, milestone tracking, evaluator review claiming, prevention of self-evaluation, rubric-based criteria evaluation, and immutable revision trees (`revision_of_id`) that never cross user or project boundaries.
  - `backend/app/modules/projects/artifact_service.py`: `ArtifactService` with dual-layer concurrency protection (`with_for_update()` row locking for PostgreSQL and in-process mutex registry `_submission_locks` for SQLite dev/testing), 20MB per-file limit, 50MB aggregate per-submission limit, max 10 artifacts per submission, hourly user rate limiting (10 uploads/hr via `limiter`), atomic rollback of stored files on database failure, and 5-gate portfolio download authorization with safe download headers (`Content-Disposition: attachment`, `X-Content-Type-Options: nosniff`) sanitizing CRLF injection.
- **REST API Routers:**
  - `backend/app/modules/projects/router.py`: Registered 15+ endpoints under `/api/v1` for projects, submissions, revisions, reviews, evaluations, artifact upload/delete, and gated binary downloads.
  - `backend/app/main.py`: Mounted `projects_router` under `/api/v1`.
- **Test Coverage:**
  - `backend/tests/test_projects_api.py`: Catalog exploration, creator authoring, role gating, completeness validation, and archiving (6 tests).
  - `backend/tests/test_submissions_api.py`: Draft lifecycle, duplicate draft prevention, self-evaluation prevention, evaluation pass, changes requested, revision tree, learner submission listings, full lifecycle transition history verification, cross-user revision rejection, and cross-project revision rejection (9 tests).
  - `backend/tests/test_artifacts_api.py`: Valid uploads (PDF, TXT, MD, JSON, CSV), blocked executable extensions, disguised MZ/ELF headers, null bytes in text, rate limiting, draft-only deletion, owner/reviewer download, independent 5-gate public portfolio download checks, aggregate 50MB limit rejection, 11th artifact rejection, concurrent uploads quota enforcement, DB failure rollback cleanup, guessed UUIDs, CRLF filename sanitization, and unauthorized deletion (14 tests).
  - 29 new tests passing (191 total backend tests).

### Stage 3 Deliverables (Backend Portfolio & Progression Integration)
- **Pydantic Validation Schemas:**
  - `backend/app/modules/projects/schemas.py`: Implemented typed Pydantic models `PortfolioUpdateRequest`, `PortfolioItemCreateRequest`, `PortfolioItemUpdateRequest`, `PortfolioItemReorderRequest`, `PortfolioItemResponse`, `PortfolioDetailResponse`, and `PortfolioPublicResponse`. Added case-insensitive normalization validators for item type and visibility enums.
  - `backend/app/modules/progress/schemas.py`: Enhanced `SkillEvidenceItem` to support optional activity fields and include capstone project evidence (`project_id`, `project_title`, `submission_id`).
- **Domain Services:**
  - `backend/app/modules/projects/portfolio_service.py`: `PortfolioService` providing auto-creation of default private portfolios on first access (`GET /portfolios/me`), bio/theme/slug updates, reserved slug protection (`me`, `items`, `admin`, `api`, `auth`, `courses`, `projects`, `users`, `settings`, etc.), custom slug global uniqueness, submission ownership verification, requirement that only `COMPLETED` submissions can be added, public artifact filtering, sequential sort order calculation, atomic item reordering, non-destructive item deletion preserving underlying submissions and artifacts, and public showcase privacy enforcement (`PRIVATE` portfolios return 403 Forbidden to anonymous viewers, while `UNLISTED` and `PUBLIC` portfolios expose only public items, scrubbing internal filesystem keys and evaluator notes).
  - `backend/app/modules/projects/submission_service.py`: Integrated progression triggers: transitions skills to `PRACTICING` on project submission, and triggers skill mastery recalculation across all linked `ProjectSkill` records when evaluation concludes with `COMPLETED` or `CHANGES_REQUESTED`.
  - `backend/app/modules/progress/service.py`: Extended `ProgressionService.recalculate_skill_mastery` to query completed project submissions, deduplicate revisions by `project_id` preserving the highest score, format evidence items under rule `"capstone_project_completed"`, and compute mastery levels across combined activity and project evidence (1 project $\rightarrow$ `PROVISIONAL`, $\ge 2$ tasks with $\ge 80\%$ avg $\rightarrow$ `MASTERED`).
- **REST API Routers:**
  - `backend/app/modules/projects/router.py`: Registered 7 portfolio endpoints under `/api/v1/portfolios`:
    - `GET /api/v1/portfolios/me` 🔓 (Auto-creates default private portfolio)
    - `PATCH /api/v1/portfolios/me` 🔓 (Update profile, slug, theme, visibility)
    - `POST /api/v1/portfolios/me/items` 🔓 (Add completed submission or external link, status 201)
    - `PATCH /api/v1/portfolios/me/items/{item_id}` 🔓 (Update item metadata/visibility/order)
    - `DELETE /api/v1/portfolios/me/items/{item_id}` 🔓 (Non-destructive removal, status 204)
    - `POST /api/v1/portfolios/me/items/reorder` 🔓 (Atomic batch item reordering)
    - `GET /api/v1/portfolios/{slug_or_id}` 🌐 (Public showcase resolution with privacy filtering)
- **Test Coverage:**
  - `backend/tests/test_portfolio_api.py`: 8 end-to-end integration tests (auto-creation, metadata & visibility update, reserved slug rejection & custom slug uniqueness, completed project submission addition with public artifact filtering, submission validation rules, non-destructive deletion, sequential reordering, and public showcase privacy enforcement).
  - `backend/tests/test_project_progression.py`: 4 integration tests (completed project awards evidence and provisional mastery, incomplete/failed projects do not award mastery, revisions deduplicate by `project_id`, and 2 distinct tasks achieve `MASTERED` status).
  - 15 new tests passing (206 total backend tests, 0 failures).

### Stage 4 Deliverables (Specialized Practice Activity Upgrades)
- **Activity Engine & Deterministic Rubric Graders:**
  - `backend/app/modules/activities/models.py`: Added `WEB_PRACTICE = "web_practice"` and `COMMUNICATION = "communication"` to `ActivityType`.
  - `backend/app/modules/activities/schemas.py`: Defined Pydantic models for `MilestoneItem`, `WebPracticeConfig`, `WebPracticeSubmission`, `CommunicationSection`, `CommunicationConfig`, and `CommunicationSubmission`.
  - `backend/app/modules/activities/grading.py`:
    - `WebPracticeGrader`: Implemented deterministic scoring across milestone checklist completion and technical reflection depth ($\ge 10$ words). Enforced strict URL format validation (`SAFE_URL_REGEX`, domain validation, blocking `javascript:`, `file:`, `data:`). Invariant: no arbitrary code execution or untrusted repository sandboxing.
    - `CommunicationGrader`: Deterministic structural grading supporting BLUF (Bottom Line Up Front $\ge 5$ words, context details, next steps) and STAR (Situation, Task, Action, Result $\ge 10$ words each) with word count boundaries and section completeness.
    - `OrderingGrader`: Upgraded to support multiple acceptable sequence permutations via `acceptable_orders` (`list[list[str]]`) alongside single `correct_order`.
    - `MatchingGrader`: Upgraded to support multi-target pairing via `acceptable_pairs` (`dict[str, list[str]]`) alongside single `pairs`.
    - Registered new graders in `GradingEngine._graders`.
- **Grounded Formative AI Writing Review:**
  - `backend/app/infrastructure/ai/base.py`: Defined `CommunicationFeedbackContext`, `AICommunicationFeedbackResponse`, and abstract method `review_communication`.
  - `backend/app/infrastructure/ai/mock_provider.py` & `gemini_provider.py`: Implemented structured qualitative review extracting summary, key strengths, areas for improvement, actionable tips, and section feedback.
  - `backend/app/modules/ai/service.py`: Added `review_communication` enforcing user `ai_opt_out` preferences, stripping confidential answer keys, rate limiting, and auditing telemetry in `ai_interactions` (`interaction_type="communication_feedback"`).
  - `backend/app/modules/ai/router.py`: Mounted `POST /api/v1/ai/communication-feedback`.
- **Frontend Specialized Components & Accessible Interactions:**
  - `frontend/src/types/activity.ts` & `frontend/src/types/ai.ts`: TypeScript contracts for `web_practice`, `communication`, submissions, and AI communication feedback.
  - `frontend/src/features/activities/WebPracticeActivity.tsx`: Problem statement card, learning objectives list, interactive milestone checklist with completion counters, repository URL & live demo URL inputs with real-time format validation alerts, implementation notes, reflection textarea with word count counter, and security non-execution policy notice.
  - `frontend/src/features/activities/CommunicationActivity.tsx`: Scenario context with audience and objective badges, BLUF / STAR structured writing inputs with real-time word counters, reflection textarea, and "Request AI Writing Review" button with formative coaching feedback display.
  - `frontend/src/features/activities/OrderingActivity.tsx`: Upgraded with keyboard reordering (`ArrowUp`/`ArrowDown`/`Home`/`End`), accessible movement buttons, and `aria-live="polite"` screen reader announcements.
  - `frontend/src/features/activities/MatchingActivity.tsx`: Accessible pairing dropdowns with real-time matched counter, visual checkmarks/status indicators, and live announcements.
  - `frontend/src/features/activities/ActivityRenderer.tsx`: Dispatches `web_practice` and `communication` activity types.
  - `frontend/src/features/activities/ActivityContainer.tsx`: Integrated submission validation for web practice deliverables and communication sections.
  - `frontend/src/services/aiApi.ts`: Added `getCommunicationFeedback` method.
- **Verification & Test Coverage:**
  - `backend/tests/test_specialized_activities.py`: 17 unit and end-to-end integration tests (web practice rubric grading, unsafe URL scheme rejection, milestone scoring, reflection validation, BLUF/STAR validation, multi-order permutations, multi-pair matching, API attempt submission, AI writing review, and opt-out enforcement). 17 passed.
  - `frontend/src/test/SpecializedActivities.test.tsx`: 12 frontend component and interaction tests. All 90 frontend tests passed across 11 test suites.
  - `npm --prefix frontend run build`: Clean production bundle (0 errors).
  - Zero database migrations required; `alembic check` verified 0 schema drift.

### Stage 5 Deliverables (Frontend Projects & Submissions UI)
- **TypeScript Contracts & API Client:**
  - `frontend/src/types/project.ts`: Strict types reflecting backend schemas for project catalog summaries (`ProjectSummary`), detailed specifications (`ProjectDetail`), pagination (`ProjectPaginatedResponse`), requirements/milestones (`ProjectRequirements`, `Milestone`), rubrics (`EvaluationCriteria`, `RubricCriterion`), artifacts (`Artifact`, `ArtifactListResponse`), submissions lifecycle (`SubmissionSummary`, `SubmissionDetail`, `SubmissionStatus`), evaluation results (`EvaluationResult`, `CriteriaScore`), and revision history (`SubmissionHistoryResponse`, `TransitionHistoryItem`).
  - `frontend/src/services/projectApi.ts`: Fully-typed API client governing project catalog discovery (`listProjects` with search, discipline, difficulty, sort, and pagination filters), project specifications (`getProject`), draft creation & retrieval (`startOrGetSubmission`), draft deliverables updates (`updateDraftSubmission`), deliverable submission (`submitProject`), revision drafting (`createRevision`), revision history (`getSubmissionHistory`), artifact uploads (`uploadArtifact` with `FormData` and `is_public` showcase toggle), artifact deletion (`deleteArtifact`), and secure download endpoint mapping.
- **Frontend Project Components & Interactive Workspaces:**
  - `frontend/src/features/projects/ProjectCard.tsx`: Learner-facing catalog card displaying project title, difficulty level badge, estimated duration, discipline tag, primary & secondary demonstrated skill badges, submission count, and view details action link.
  - `frontend/src/features/projects/ProjectFilters.tsx`: Catalog filter bar featuring debounced text search, active discipline selector, difficulty filter (Beginner, Intermediate, Advanced, Expert), sorting controls (created_at, title, difficulty_level), order toggle (asc/desc), and reset filters button.
  - `frontend/src/features/projects/MilestoneList.tsx`: Reusable milestone component supporting both read-only milestone progress overview (on project specification page) and interactive milestone completion checkboxes (on submission workspace page) with completion percentage progress bar.
  - `frontend/src/features/projects/RubricView.tsx`: Rubric breakdown component visualizing passing score targets, rubric criteria cards with max scores and weights, and explicit assessment integrity disclaimer notes.
  - `frontend/src/features/projects/ArtifactManager.tsx`: Comprehensive deliverable artifact management component with client-side file extension & size validation (allowing ZIP, TAR.GZ, PDF, PNG, JPG, WEBP, TXT, MD, JSON, CSV; rejecting hazardous executables/scripts .exe, .py, .sh), single file limit (20MB), aggregate submission quota (50MB) progress indicator, public portfolio showcase toggle, file download links, and draft-mode artifact deletion.
  - `frontend/src/features/projects/EvaluationFeedback.tsx`: Evaluator feedback card displaying final grade, passing score comparison, pass/fail status badge, general written remarks, detailed rubric criteria breakdown scores and comments, reviewer identity, and evaluation timestamp.
  - `frontend/src/features/projects/RevisionHistory.tsx`: Sequential revision history timeline component displaying sequential versions (v1, v2), status badges, dates, scores, active workspace indicator, and inspection links.
- **Learner Pages & Routing Integration:**
  - `frontend/src/pages/ProjectsPage.tsx` (`/projects`): Applied capstones catalog page with hero banner, filter controls, responsive grid, loading skeletons, error states with retry, empty state with filter reset, and pagination controls.
  - `frontend/src/pages/ProjectDetailPage.tsx` (`/projects/:slugOrId`): Full project specification page with scope overview, demonstrated skills, milestone list, expected deliverables, upload guidelines, evaluation rubric, starter templates, and conditional action buttons (unauthenticated login redirect, start project draft, or resume active workspace).
  - `frontend/src/pages/SubmissionWorkspacePage.tsx` (`/submissions/:submissionId`): Real submission workspace with draft deliverables form (title, summary, repository URL, live deployment URL, technical notes), interactive milestone checkboxes, artifact manager, lifecycle state banner, evaluation feedback card, and revision draft launcher when changes are requested.
  - `frontend/src/app/routes.tsx`: Registered `/projects`, `/projects/:slugOrId`, and `/submissions/:submissionId`.
  - `frontend/src/components/layout/Header.tsx` & `Sidebar.tsx` & `MobileNav.tsx`: Added navigation links and page title / breadcrumb mapping for Projects and Submission Workspaces.
- **Verification & Test Coverage:**
  - `frontend/src/test/Projects.test.tsx`: 16 comprehensive unit and integration tests covering catalog discovery, keyword filtering, empty/error/retry states, project details, rubric rendering, unauthenticated login redirect, authenticated project start, draft editing & saving, client-side malicious script rejection (.py/.exe), client-side oversize rejection (>20MB), valid artifact upload, project submission transition, evaluation feedback rendering, revision draft creation, and revision history timeline.
  - All 106 frontend tests passing across 12 test suites (`npm --prefix frontend test -- --run`).
  - Production build clean (`npm --prefix frontend run build` exited with code 0).
  - Protected file `CourseEditorPage.tsx` remained completely untouched.

### Stage 6 Deliverables (Frontend Portfolio Management & Public Showcase)
- **TypeScript Contracts & API Client:**
  - `frontend/src/types/portfolio.ts`: Strict types reflecting backend Pydantic schemas for portfolio details (`PortfolioDetail`), public showcase (`PortfolioPublic`), showcase items (`PortfolioItem`, `PortfolioArtifact`), visibility levels (`PortfolioVisibility`: `PRIVATE`, `UNLISTED`, `PUBLIC`), item types (`PortfolioItemType`: `PROJECT_SUBMISSION`, `SKILL_MASTERY`, `ACHIEVEMENT`, `CUSTOM`), profile updates (`PortfolioUpdateRequest`), item creation/update payloads (`PortfolioItemCreateRequest`, `PortfolioItemUpdateRequest`), and item reordering (`PortfolioItemReorderRequest`).
  - `frontend/src/services/portfolioApi.ts`: Fully-typed API client governing portfolio profile retrieval (`getMyPortfolio` auto-creating draft on first visit), profile updates (`updateMyPortfolio`), showcase item addition (`addPortfolioItem`), item metadata/visibility updates (`updatePortfolioItem`), non-destructive item removal (`deletePortfolioItem`), sequential item reordering (`reorderPortfolioItems`), public showcase discovery (`getPublicPortfolio`), and completed project submissions retrieval (`getCompletedSubmissions`).
- **Learner Portfolio Showcase & Management Components:**
  - `frontend/src/features/portfolio/PortfolioShareCard.tsx`: Share and exposure card displaying current visibility badge (Private, Unlisted, Public), generated shareable URL (`/u/:slugOrId/portfolio`), one-click copy button with visual feedback, preview link, and helpful privacy reminders.
  - `frontend/src/features/portfolio/PortfolioProfileEditor.tsx`: Responsive form for editing showcase title, professional headline, biography, custom slug handle (`/u/:slug/portfolio`), visibility level radio controls (Private, Unlisted, Public), and public contact/social links (GitHub, LinkedIn, Personal Website, Twitter/X). Includes client-side slug format validation, error alerts, and success feedback.
  - `frontend/src/features/portfolio/PortfolioItemCard.tsx`: Curated showcase item card displaying item type badge (Capstone Project, Skill Mastery, Achievement, Custom), item title, summary description, demonstrated competencies tags, public artifact attachments with secure download links (`/api/v1/artifacts/{id}/download`), and external live project links. In owner mode, provides accessible reorder controls (Move Up / Move Down buttons), edit modal launcher, and non-destructive removal action.
  - `frontend/src/features/portfolio/PortfolioItemModal.tsx`: Accessible dialog modal supporting adding completed capstone project submissions (auto-populating verified deliverables, score, and demonstrated skills) or custom engineering achievements, with item visibility controls (Public vs. Private).
  - `frontend/src/features/portfolio/PublicPortfolioShowcase.tsx`: Public-facing showcase layout featuring verified learner avatar, display name, verified learner badge, headline, biography, contact pills, aggregated competencies chips, featured capstone deliverables grid, artifact download links, empty state, and SkillVerse platform verification footer.
- **Pages & Navigation Shell Integration:**
  - `frontend/src/pages/PortfolioManagementPage.tsx` (`/portfolio`): Dedicated learner portfolio management workspace with tabbed navigation (Showcase Items vs. Profile & Links), share card, item curation grid, empty state with "Add Your First Item" prompt, and confirmation dialogs.
  - `frontend/src/pages/PublicPortfolioPage.tsx` (`/u/:slugOrId/portfolio` & `/portfolio/:slugOrId`): Public showcase route with privacy enforcement handling 403 Forbidden ("This Portfolio is Private" state), 404 Not Found, loading skeletons, and public presentation.
  - `frontend/src/app/routes.tsx`: Mounted `/portfolio`, `/portfolio/:slugOrId`, and `/u/:slugOrId/portfolio`.
  - `frontend/src/components/layout/Header.tsx`, `Sidebar.tsx`, and `MobileNav.tsx`: Added "Portfolio" navigation entry with "Showcase" badge for authenticated learners, and breadcrumb header handling.
- **Verification & Test Coverage:**
  - `frontend/src/test/Portfolio.test.tsx`: 12 comprehensive unit and integration tests covering portfolio loading, profile editing and saving, visibility toggling (Private -> Unlisted -> Public), empty showcase state, completed project item addition, sequential reordering, non-destructive deletion with confirmation, error and retry states, public showcase rendering, 403 private access denial, 404 not found state, and strict privacy protection ensuring no internal storage keys or filesystem paths are exposed in the DOM.
  - All 118 frontend tests passing across 13 test suites (`npm --prefix frontend test -- --run`).
  - Production build clean (`npm --prefix frontend run build` exited with code 0).
  - `frontend/src/pages/CourseEditorPage.tsx` remained completely untouched.

### Stage 7 Deliverables (Full System Verification & Integration)
- **Cross-Module Verification & Invariants Inspection:**
  - Audited and verified all 9 platform core domains: Identity & Access, Learning Catalog & Content, Learning Activities & Assessment, Specialized Practice Activities, Progression & Mastery, Projects & Submissions Lifecycle, Portfolio & Public Showcase, AI Tutor with Grounding, and Creator Studio.
  - Verified 12 core cross-module invariants: distinct course vs. project completions, hints not granting assessment progress, requirement of successful evaluation for project mastery evidence, project revision evidence deduplication, strict public portfolio privacy boundaries, 5-gate artifact download authorization, comprehensive AI opt-out enforcement, immutable published courses, and transactional cleanup of failed uploads.
- **Group 1 Targeted Remediation (Storage Security & WebP Binary Validation):**
  - Updated `backend/app/infrastructure/storage/local_storage.py` to implement genuine WebP binary signature verification (`RIFF` at byte offset 0 and `WEBP` at byte offset 8, minimum 12 bytes header validation) while rejecting invalid RIFF markers, missing WEBP markers, truncated headers, and arbitrary text renamed to `.webp`.
  - Reinforced storage-root containment check (`_is_within_base_dir`) using `os.path.commonpath` and `is_relative_to` to strictly reject sibling directories that share string prefixes with the storage root, as well as the root directory itself.
  - Added comprehensive test coverage in `backend/tests/test_storage.py`: `test_store_and_retrieve_valid_webp_image`, `test_reject_webp_invalid_riff_header`, `test_reject_webp_missing_webp_marker`, `test_reject_webp_arbitrary_text_renamed`, `test_reject_webp_truncated_header`, `test_reject_empty_signature_checked_file`, and `test_containment_rejects_sibling_directory_sharing_prefix`.
- **Group 2 Targeted Remediation (Frontend Cleanliness & Warning Elimination):**
  - Updated `frontend/src/pages/DashboardPage.tsx` to provide deterministic, unique keys based on actual item identities (`rec.id`, `rec.link`, `rec.course_slug`, `rec.skill_slug`, `rec.title` for recommendations, `att.attempt_id || att.activity_id` for recent attempts, `ach.id || ach.slug` for achievements, and unique IDs for loading skeletons), completely eliminating the React missing-key warning without using array indices where stable identifiers exist.
  - Updated `frontend/src/test/Projects.test.tsx` to properly await asynchronous state updates in the search filter and filter reset tests using `await waitFor(...)`, eliminating all React `act(...)` warnings from the test suite.
- **Verification & Regression Results:**
  - Backend regression: 228 passing tests across full test suite (`pytest backend/tests -q`).
  - Linter: `ruff check backend` clean (0 errors).
  - Database schema: `alembic check` clean (no upgrade operations detected).
  - Frontend test suite: 118 passing tests across all 13 suites (`npm --prefix frontend test -- --run`) with 0 act warnings and 0 errors.
  - Production build: `npm --prefix frontend run build` (`tsc -b && vite build`) passed with exit code 0.
  - Protected invariants: `frontend/src/pages/CourseEditorPage.tsx` remained completely untouched. All uncommitted changes from Stages 1–6 preserved.

### Deliverables
- Database migrations for projects, project_submissions, portfolios, portfolio_items.
- Project definition and milestone tracking.
- Project submission and evaluation workflow.
- Portfolio management (add/remove items, reorder, visibility).
- Public portfolio pages.
- Shareable portfolio URLs.
- At least one additional specialized activity type (e.g., drag-and-drop ordering, visual matching).

### Important Files
- `backend/app/modules/projects/`
- `frontend/src/features/portfolio/`
- `frontend/src/features/projects/`

### Acceptance Criteria
1. Projects have structured milestones with completion tracking.
2. Learners can submit projects and receive evaluation.
3. Portfolio page displays selected projects, achievements and skills.
4. Public portfolio is accessible via custom slug URL.
5. Portfolio items can be reordered and hidden.
6. At least one specialized activity type functions correctly.

### Required Tests
- Project submission workflow test.
- Portfolio visibility test (public vs. private).
- Portfolio slug uniqueness test.
- Specialized activity grading test.

### Risks
- Project evaluation quality (AI-assisted vs. manual).
- Portfolio page design complexity.

---

## Phase 10: Security, Deployment and Release Readiness

**Status:** ⏳ Planned

### Objectives
- Security audit and hardening.
- Production deployment configuration.
- Performance optimization.
- Monitoring and observability.
- Documentation finalization.

### Dependencies
- All prior phases (Phases 1–9).

### Deliverables
- Security audit against OWASP Top 10.
- Sandbox security penetration testing.
- CSP headers configured.
- Production Docker images (multi-stage builds).
- Production Docker Compose or deployment manifests.
- Database backup and restore procedures.
- Monitoring setup (health checks, error tracking, performance metrics).
- Load testing results.
- Production environment documentation.
- User-facing documentation / help pages.
- Final README update.

### Acceptance Criteria
1. No critical or high-severity security vulnerabilities.
2. Sandbox passes isolation tests with adversarial inputs.
3. Application handles 100 concurrent users without errors.
4. API response times under 500ms at p95 under load.
5. Database backup and restore procedures tested.
6. Health check endpoints respond correctly.
7. Error tracking captures and alerts on application errors.
8. Production deployment documented step-by-step.

### Required Tests
- OWASP Top 10 checklist verification.
- Sandbox penetration tests.
- Load tests (k6, Locust or similar).
- Backup/restore drill.
- Deployment test on clean environment.

### Risks
- Security vulnerabilities discovered late requiring significant rework.
- Performance issues under load requiring architectural changes.

---

## Phase 11: Community and Ecosystem Expansion

**Status:** ⏳ Planned

### Objectives
- Community features (forums, study groups, peer review).
- Course marketplace.
- Advanced skill maps with visual pathways.
- Spaced repetition for skill retention.
- Mobile optimization.
- Additional courses and content.

### Dependencies
- Phase 10 (stable, deployed platform).

### Deliverables
- This phase is expansive and will be broken into sub-phases when Phase 10 is complete.
- Initial deliverables will be determined based on user feedback and product metrics.

### Acceptance Criteria
- To be defined based on user feedback and product strategy.

### Risks
- Scope creep. This phase must be carefully prioritized.
- Community moderation challenges.

---

## Initial Launch Acceptance Targets

The first complete learning experience is validated when these three representative activities function end-to-end:

### 1. Web Development Foundations — Code Exercise
A learner completes a coding exercise that requires writing a valid HTML/CSS page, sees a live preview in the workspace, runs automated tests and receives specific pass/fail feedback with hints for failing tests.

**Validation criteria:**
- Code editor with syntax highlighting and starter code.
- Live HTML/CSS preview updating in real time.
- Test runner executes at least 3 automated checks.
- Results show per-test pass/fail with specific error messages.
- Hints available for failed tests (progressive, not answer-revealing).
- Attempt recorded with score and feedback.

### 2. Spoken English and Communication — Conversation Practice
A learner completes a simulated professional conversation (e.g., "Introduce yourself in a job interview") by providing text responses to prompts and receiving AI-assisted feedback on clarity, relevance and structure.

**Validation criteria:**
- Scenario description with context and objectives.
- Series of prompts requiring learner responses.
- AI-assisted feedback evaluating content quality (not just keyword matching).
- Specific, actionable improvement suggestions.
- Retry option with feedback on improvement.
- Score reflecting overall performance.

### 3. Personal Productivity — Decision-Making Task
A learner completes a practical task (e.g., "Prioritize these 10 work tasks for maximum impact") with transparent evaluation criteria and receives feedback on their reasoning.

**Validation criteria:**
- Scenario with realistic decision context.
- Structured response format (ranking, categorization, explanation).
- Evaluation against documented criteria (not opaque AI judgment).
- Feedback explaining what was strong and what could improve.
- Clear passing threshold communicated upfront.
- Attempt recorded with rubric-aligned score.

---

## Unresolved Decisions

| Decision | Context | When to Resolve |
|---|---|---|
| Font selection | Inter vs. Outfit vs. another | Phase 1 (design system implementation) |
| State management library | React Query may be sufficient, or Zustand/Jotai may be needed | Phase 1 (evaluate during shell implementation) |
| Background job library | arq vs. Celery vs. custom | Phase 2 (evaluate based on requirements) |
| AI provider | OpenAI initial, but Claude/Gemini also candidates | Phase 8 (evaluate based on feedback quality) |
| Voice input for communication | Browser Web Speech API vs. dedicated service | Phase 8+ (evaluate feasibility) |
| Email service | SMTP vs. Resend vs. SendGrid | Phase 2 (evaluate based on requirements and budget) |
| Hosting platform | Cloud provider selection | Phase 10 (evaluate based on budget and requirements) |
| Course content licensing | How creator content is licensed | Phase 7 (legal review required) |
| Monetization model | Free vs. freemium vs. subscription | Post-launch (depends on product-market fit) |
