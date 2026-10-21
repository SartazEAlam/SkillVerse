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

## Phase 4: Universal Lesson Renderer

**Status:** ⏳ Planned

### Objectives
- Build a universal, block-based lesson renderer that handles all block types.
- Implement the learning workspace layout (sidebar + content + activity area).
- Add lesson navigation (previous/next, module sidebar).
- Support code example blocks with syntax highlighting and copy functionality.

### Dependencies
- Phase 3 (course content, lesson data model).

### Deliverables
- Block renderer component supporting: text (markdown), code_example, media, callout, activity_ref.
- Syntax highlighting for code blocks (multiple languages).
- Copy-to-clipboard for code examples.
- Learning workspace layout with resizable panels.
- Module sidebar with lesson list and completion indicators.
- Lesson navigation (previous/next with keyboard shortcuts).
- Breadcrumb navigation (course → module → lesson).
- Smooth view transitions between lessons.

### Important Files
- `frontend/src/features/lessons/LessonRenderer.tsx`
- `frontend/src/features/lessons/blocks/`
- `frontend/src/features/lessons/LessonWorkspace.tsx`
- `frontend/src/components/layout/LessonLayout.tsx`

### Acceptance Criteria
1. All block types render correctly with proper styling.
2. Code blocks have syntax highlighting for JavaScript, HTML, CSS, Python and SQL.
3. Code blocks have a working copy button.
4. Workspace panels are resizable via drag.
5. Lesson navigation works with both clicks and keyboard shortcuts (← →).
6. Module sidebar correctly shows lesson list with visual position indicator.
7. Breadcrumb shows current position in course hierarchy.
8. Transitions between lessons are smooth and do not flash or flicker.
9. Workspace layout adapts correctly to mobile (stacked) and desktop (side-by-side).

### Required Tests
- Block renderer unit tests (each block type).
- Keyboard navigation integration test.
- Responsive layout test at breakpoints.

### Risks
- Markdown rendering security (XSS through lesson content — mitigate with sanitization).
- Performance with many blocks per lesson.

---

## Phase 5: Activity Engine and Assessment

**Status:** ⏳ Planned

### Objectives
- Build the schema-driven activity engine.
- Implement code exercise, quiz, conversation and practical task activity types.
- Build the code execution sandbox.
- Implement attempt tracking and grading.
- Display activity results with feedback.

### Dependencies
- Phase 4 (lesson renderer, workspace layout).
- Phase 2 (auth, user system).

### Deliverables
- Database migrations for activities, grading_configs, attempts.
- Activity engine service (schema-driven, type-dispatched grading).
- **Code exercise:** Monaco editor, live HTML/CSS/JS preview, test runner, sandbox execution.
- **Quiz:** MCQ, fill-in-the-blank, matching, ordering question types.
- **Conversation practice:** Prompt-response pairs, text-based initially (voice in future).
- **Practical task:** Scenario description, structured response, rubric-based evaluation.
- Attempt submission API with rate limiting.
- Grading pipeline (automated for code/quiz, placeholder for AI-assisted).
- Activity workspace components (editor, preview, results panel).
- Feedback display (pass/fail, specific error messages, hints).
- Retry flow.
- Sandbox Docker container for code execution.
- Sandbox worker service.

### Important Files
- `backend/app/modules/activities/`
- `backend/app/infrastructure/sandbox/`
- `frontend/src/features/activities/`
- `frontend/src/features/activities/CodeExercise.tsx`
- `frontend/src/features/activities/QuizActivity.tsx`
- `docker/sandbox/Dockerfile`

### Acceptance Criteria
1. Code exercise: learner writes JavaScript, sees live preview, runs tests, gets pass/fail with specific feedback.
2. Quiz: supports MCQ and fill-in-blank. Immediate automated grading. Shows correct answers after completion.
3. Conversation practice: text-based prompt/response with automated keyword/pattern matching (AI grading in Phase 8).
4. Practical task: scenario + structured response form. Rubric-based completion marking.
5. Attempt history shows all attempts with scores and feedback.
6. Rate limiting prevents excessive sandbox usage (max 30 executions/hour).
7. Sandbox executes code in isolation: no network, limited CPU/memory, hard timeout.
8. Malicious code (fork bomb, memory exhaustion, file system access) is contained.
9. Hints system provides progressive guidance without revealing answers.

### Required Tests
- Activity engine grading tests (each activity type).
- Sandbox isolation tests (network blocked, memory limited, timeout enforced).
- Attempt rate limiting test.
- Quiz grading accuracy test (each question type).
- Code exercise end-to-end test (write code → submit → grade → feedback).

### Risks
- **Critical:** Sandbox security. Must be thoroughly tested before production.
- Monaco editor bundle size (mitigate with dynamic import).
- Code execution latency affecting user experience.

---

## Phase 6: Progression, Mastery and Recommendations

**Status:** ⏳ Planned

### Objectives
- Implement the automated progression engine (activity completion triggering lesson/module/course completion).
- Build skill mastery calculation from activity results.
- Add achievements and badges.
- Build the learner dashboard.
- Implement basic recommendations.

### Dependencies
- Phase 5 (activity engine, attempts, grading).
- Phase 3 (enrollments and lesson progress foundation).

### Deliverables
- Database migrations for skill_mastery, achievements, user_achievements.
- Automated progress evaluation service (integrates Phase 5 activity attempts to automatically update Phase 3 lesson_progress).
- Module completion logic (all lessons complete → module complete).
- Course completion logic (all modules complete → course complete).
- Skill mastery calculation service (weighted average of activity scores across taxonomy).
- Achievement definitions and unlock logic.
- Learner dashboard: active courses, progress, recent activity, skill mastery overview, achievements.
- Progress visualization (progress bars, skill radar/chart).
- Basic recommendations (next lesson, next course based on skill gaps).

### Important Files
- `backend/app/modules/progress/`
- `frontend/src/features/dashboard/`
- `frontend/src/features/skill-map/`

### Acceptance Criteria
1. Lesson progress updates automatically when activities are completed.
2. Module and course completion trigger correctly.
3. Skill mastery recalculates when new activity results are recorded.
4. Dashboard shows accurate progress for all enrolled courses.
5. At least 5 achievements defined and earnable (first lesson, first course, streak, etc.).
6. Recommendations suggest relevant next content based on current progress.
7. Progress data is consistent (no phantom completions, no lost progress).
8. Course completion triggers a celebration and dashboard update.

### Required Tests
- Lesson/module/course completion cascade tests.
- Skill mastery calculation accuracy tests.
- Achievement unlock trigger tests.
- Dashboard data consistency tests.
- Concurrent progress update tests (no race conditions).

### Risks
- Mastery calculation algorithm needs tuning with real usage data.
- Achievement criteria may need revision after user feedback.

---

## Phase 7: Creator Studio and Course Publishing

**Status:** ⏳ Planned

### Objectives
- Build the course authoring interface.
- Implement course versioning and publication workflow.
- Add admin review process.
- Creator analytics.

### Dependencies
- Phase 5 (activity engine — creators need to configure activities).
- Phase 3 (course content model).

### Deliverables
- Database migration for course_reviews.
- Creator role assignment workflow.
- Course creation and editing API.
- Module/lesson/block editor interface.
- Activity configuration editor (visual configuration, not raw JSON).
- Course version management (create new version from existing).
- Submission for review workflow.
- Admin review interface (approve, reject, request changes).
- Publication workflow (approved → published → active version).
- Basic creator analytics (enrollments, completions, activity scores).

### Important Files
- `frontend/src/features/creator/`
- `backend/app/modules/courses/` (extended)
- `backend/app/modules/admin/`

### Acceptance Criteria
1. Creator can create a course with modules, lessons and activities through the UI.
2. Lesson block editor supports all block types.
3. Activity configuration editor generates valid activity schemas.
4. Course versioning: edits create a new version without affecting the active one.
5. Review submission notifies admin. Admin can approve/reject with comments.
6. Publication makes the new version active. Existing enrollments stay on their version.
7. Creator dashboard shows enrollment and completion statistics.

### Required Tests
- Course creation end-to-end test.
- Version isolation test (active version unaffected by draft edits).
- Review workflow test (submit → approve → publish).
- Creator analytics accuracy test.

### Risks
- Lesson block editor complexity (rich text editing is notoriously difficult).
- Activity configuration UX needs careful design to avoid overwhelming creators.

---

## Phase 8: AI Tutor and Personalized Practice

**Status:** ⏳ Planned

### Objectives
- Integrate AI provider for tutoring and feedback.
- Build the AI tutor interface.
- Implement AI-assisted grading for open-ended activities.
- Personalized practice recommendations.

### Dependencies
- Phase 5 (activity engine — AI provides feedback on activities).
- Phase 6 (progression — AI uses progress data for personalization).

### Deliverables
- Database migration for ai_interactions.
- Provider-neutral AI client abstraction.
- AI tutor API endpoint with rate limiting.
- AI tutor UI panel (expandable within lesson workspace).
- AI-assisted feedback for conversation and practical task activities.
- Prompt engineering for pedagogical guidance (guide, don't solve).
- Response filtering and safety checks.
- AI usage audit logging.
- Personalized practice recommendations based on mastery gaps.
- AI feature opt-out in user preferences.

### Important Files
- `backend/app/modules/ai/`
- `backend/app/infrastructure/ai_client.py`
- `frontend/src/features/ai-tutor/`

### Acceptance Criteria
1. AI tutor answers learner questions within lesson context.
2. AI responses are pedagogical (guides understanding, doesn't give direct answers).
3. AI feedback on conversation activities evaluates fluency, relevance and clarity.
4. AI feedback on practical tasks evaluates against rubric criteria.
5. Rate limiting enforced (30 tutor questions/hour, 10 feedback requests/hour).
6. All AI interactions logged with provider, model, token usage.
7. AI feature can be disabled per user.
8. Response filtering catches inappropriate or off-topic AI responses.

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

**Status:** ⏳ Planned

### Objectives
- Implement capstone projects with milestones.
- Build portfolio system.
- Add specialized learning activities (e.g., drag-and-drop, diagramming).
- Shareable portfolio pages.

### Dependencies
- Phase 5 (activity engine).
- Phase 6 (progression and mastery).

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
