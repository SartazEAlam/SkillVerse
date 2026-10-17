# AGENTS.md — SkillVerse Engineering Rules

This file contains durable development instructions for all contributors and AI-assisted development tools working on the SkillVerse codebase.

---

## Pre-Change Requirements

1. **Inspect the repository** before making changes. Read `README.md`, this file, and any documentation relevant to the area you are modifying.
2. **Preserve existing working functionality.** Never delete, overwrite, reset or replace working code unless you have a documented technical reason and explicit approval.
3. **Check Git status and recent history** before starting work. Understand the current branch, uncommitted changes and recent commits.

## Architecture and Design

4. **Follow approved architecture and API contracts.** All architecture decisions are documented in `docs/ARCHITECTURE.md` and `docs/API.md`. Do not introduce new architectural patterns without documenting the rationale.
5. **Use a modular monolith** for the backend. Do not introduce microservices without a clear, documented technical justification.
6. **Keep business logic separate from route handlers and UI components.** Backend business logic belongs in service modules, not in FastAPI route handlers. Frontend business logic belongs in hooks and services, not in React components.
7. **Build reusable, schema-driven learning activities.** The activity engine must support multiple activity types through configuration, not through one-off implementations for each activity.

## Code Quality

8. **Use TypeScript strict mode** for all frontend code. No `any` types unless explicitly justified with a comment.
9. **Use validated Python schemas** (Pydantic models) for all API inputs and outputs.
10. **Use version-controlled database migrations** (Alembic). Never modify the database schema by hand in any environment.
11. **Write tests alongside implementation.** Every feature must include relevant unit tests. Integration tests are required for API endpoints and critical user flows.
12. **Verify actual behavior** rather than assuming generated files work. Run the tests, check the output, inspect the rendered UI.
13. **Report real test results and limitations.** Never fabricate test output or claim an integration works when it is only a mock.

## Security

14. **Enforce server-side authorization.** Every API endpoint must verify that the authenticated user has permission for the requested action. Never rely on client-side checks alone.
15. **Never commit secrets.** API keys, database passwords, tokens and private keys must be loaded from environment variables or a secrets manager, never hardcoded in source files.
16. **Never execute untrusted learner code in the main API process.** All learner code execution must happen in an isolated sandbox with resource limits, network restrictions and time limits.
17. **Validate and sanitize all inputs.** This includes API request bodies, query parameters, file uploads and any user-provided content rendered in the UI.

## Process

18. **Follow the phased implementation roadmap** defined in `docs/DEVELOPMENT_PLAN.md`. Do not skip phases or implement features from a later phase unless their dependencies are satisfied.
19. **Do not install unnecessary dependencies.** Only add packages that are needed for the current phase of work.
20. **Avoid unrelated refactoring.** Stay focused on the task at hand. Cosmetic or structural changes unrelated to the current objective create unnecessary risk.
21. **Do not create a Git commit unless explicitly requested** by the user or the task definition.
22. **Never expose credentials, API keys or private user data** in logs, error messages, documentation or Git history.
23. **Do not delete or reset databases containing user data** without explicit authorization and a documented backup plan.
24. **Do not generate fake test results** or mark phases as complete when acceptance criteria have not been verified.

## Documentation

25. **Keep documentation in sync with implementation.** When you change code, update the relevant documentation in `docs/`.
26. **Preserve all existing comments and docstrings** that are unrelated to your code changes.
27. **Document architectural decisions** with rationale, alternatives considered and trade-offs.

## File Conventions

- **Frontend code:** `frontend/src/` — React components, hooks, services, types
- **Backend code:** `backend/app/` — FastAPI routers, services, models, schemas
- **Database migrations:** `backend/alembic/versions/`
- **Tests:** colocated with source files or in dedicated `__tests__`/`tests` directories
- **Documentation:** `docs/`
- **Environment variables:** `.env.example` (committed), `.env` (never committed)
