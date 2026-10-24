# API Reference — SkillVerse

All endpoints are prefixed with `/api/v1`. The API uses JSON for request and response bodies. Authentication uses Bearer JWT tokens in the `Authorization` header.

## Conventions

### Authentication
- Endpoints marked 🔓 require a valid JWT access token.
- Endpoints marked 🔓🛡️ require a specific role (creator, admin).
- Public endpoints are marked 🌐.

### Pagination
List endpoints return paginated results:
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "has_next": true
}
```
Query parameters: `?page=1&page_size=20`

### Error Responses
All errors follow a consistent structure:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable description",
    "details": [
      { "field": "email", "message": "Invalid email format" }
    ]
  }
}
```

Standard error codes:
| HTTP Status | Code | Description |
|---|---|---|
| 400 | VALIDATION_ERROR | Invalid request data |
| 401 | UNAUTHORIZED | Missing or invalid token |
| 403 | FORBIDDEN | Insufficient permissions |
| 404 | NOT_FOUND | Resource does not exist |
| 409 | CONFLICT | Resource state conflict (e.g., duplicate) |
| 422 | UNPROCESSABLE_ENTITY | Valid syntax but semantic error |
| 429 | RATE_LIMITED | Too many requests |
| 500 | INTERNAL_ERROR | Server error |

### Idempotency
Write operations that create resources accept an optional `Idempotency-Key` header. Repeating a request with the same key within 24 hours returns the original response without creating duplicates.

---

## System & Health

### `GET /api/v1/health` 🌐
System liveness and dependency readiness check.
```json
// Response 200 (healthy)
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-10-17T21:30:00Z",
  "services": {
    "database": "connected",
    "redis": "connected",
    "storage": "connected"
  }
}
// Response 503 (degraded)
{
  "status": "degraded",
  "version": "1.0.0",
  "timestamp": "2026-10-17T21:30:00Z",
  "services": {
    "database": "connected",
    "redis": "disconnected",
    "storage": "connected"
  }
}
```

---

## Authentication & Profiles

### `POST /api/v1/auth/register` 🌐
Register a new account.
```json
// Request
{ "email": "user@example.com", "password": "secureP@ss1", "display_name": "Alex" }
// Response 201
{ "user": { "id": "uuid", "email": "...", "role": "learner", "email_verified": false } }
```
- Sends verification email.
- Password: minimum 8 characters, at least one uppercase, one digit, one special character.

### `POST /api/v1/auth/login` 🌐
```json
// Request
{ "email": "user@example.com", "password": "secureP@ss1" }
// Response 200
{
  "access_token": "jwt...",
  "refresh_token": "rt...",
  "expires_in": 900,
  "user": { "id": "uuid", "email": "user@example.com", "role": "learner", "email_verified": false }
}
```
- Rate limited: 10 attempts per 15 minutes per IP.
- Note on token transport: In Phase 2, tokens are returned in the JSON response body and stored in browser `localStorage`. For production hardening (Phase 5), the refresh token will transition to an `HttpOnly; Secure; SameSite=Lax` cookie and the access token will be held in client memory (see [docs/SECURITY.md](file:///d:/SkillVerse/docs/SECURITY.md)).

### `POST /api/v1/auth/refresh` 🌐
```json
// Request
{ "refresh_token": "rt..." }
// Response 200
{
  "access_token": "jwt...",
  "refresh_token": "rt_new...",
  "expires_in": 900,
  "user": { "id": "uuid", "email": "user@example.com", "role": "learner", "email_verified": false }
}
```
- Single-use token rotation: The supplied refresh token is immediately revoked upon use, and a new token pair is issued.

### `POST /api/v1/auth/logout` 🔓
Revokes all active refresh tokens for the authenticated user across all sessions and invalidates current client-held refresh tokens. Requires Bearer access token authentication.
```json
// Response 200
{ "message": "Successfully logged out." }
```

### `POST /api/v1/auth/verify-email` 🌐
```json
{ "token": "verification-token" }
```
```json
// Response 200
{ "message": "Email verified successfully." }
```

### `POST /api/v1/auth/forgot-password` 🌐
```json
{ "email": "user@example.com" }
```
Always returns 200 (no email enumeration).

### `POST /api/v1/auth/reset-password` 🌐
```json
{ "token": "reset-token", "new_password": "newP@ss1" }
```

### `GET /api/v1/auth/oauth/{provider}/authorize` 🌐
Initiates OAuth 2.0 authorization with PKCE (Proof Key for Code Exchange) flow (e.g., `provider = google`).
Query parameters:
- `code_challenge`: SHA-256 hash of client's code verifier (BASE64URL-encoded).
- `code_challenge_method`: Must be `S256`.
- `redirect_uri`: Frontend callback redirect URL.

```json
// Response 200
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...&response_type=code&scope=openid%20email%20profile&redirect_uri=...&state=csrf-token&code_challenge=...&code_challenge_method=S256",
  "state": "csrf-token"
}
```

### `POST /api/v1/auth/oauth/{provider}/callback` 🌐
Exchange authorization code and PKCE code_verifier for SkillVerse session tokens.
```json
// Request
{
  "code": "4/0AdQt8qh...",
  "code_verifier": "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk",
  "state": "csrf-token"
}
// Response 200
{
  "access_token": "jwt...",
  "refresh_token": "rt...",
  "expires_in": 900,
  "user": { "id": "uuid", "email": "user@example.com", "role": "learner", "email_verified": true }
}
```
- Validates anti-CSRF state token.
- Exchanges code and verifier with provider; links or provisions user and profile.

### `GET /api/v1/users/me` 🔓
Returns the authenticated user's profile.

### `PATCH /api/v1/users/me` 🔓
```json
{ "display_name": "New Name", "bio": "Updated bio", "timezone": "Asia/Kolkata" }
```

### `PATCH /api/v1/users/me/preferences` 🔓
```json
{ "theme": "dark", "reduced_motion": true }
```

### `GET /api/v1/users/me/export` 🔓
Export all user personal data, enrollments, progress, attempts, submissions, and portfolio items (GDPR portability compliance).
```json
// Response 200
{
  "manifest": {
    "export_id": "uuid",
    "generated_at": "2026-10-17T21:30:00Z",
    "user_id": "uuid",
    "format_version": "1.0",
    "included_sections": ["user", "profile", "enrollments", "lesson_progress", "activity_attempts", "skill_mastery", "achievements", "project_submissions", "portfolio"]
  },
  "user": { "id": "uuid", "email": "user@example.com", "role": "learner", "created_at": "..." },
  "profile": { "display_name": "Alex", "bio": "...", "timezone": "Asia/Kolkata" },
  "enrollments": [ ... ],
  "lesson_progress": [ ... ],
  "activity_attempts": [ ... ],
  "skill_mastery": [ ... ],
  "achievements": [ ... ],
  "project_submissions": [ ... ],
  "portfolio": { ... }
}
```

### `DELETE /api/v1/users/me` 🔓
Request user account deletion (initiates soft-delete with 30-day recovery grace period).
```json
// Request
{ "password": "secureP@ss1" }
// Response 200
{
  "status": "pending_deletion",
  "grace_period_days": 30,
  "scheduled_deletion_at": "2026-11-16T21:30:00Z",
  "message": "Account scheduled for deletion. You can reactivate by logging in within 30 days."
}
```
- Sets `users.deleted_at = NOW()` and revokes all active refresh tokens.
- Permanent deletion and data anonymization occur automatically after 30 days.

---

## Disciplines & Skill Taxonomy (Phase 3 Implemented)

### `GET /api/v1/disciplines` 🌐
List all active disciplines ordered by presentation sort order.
```json
// Response 200 OK
[
  {
    "id": "uuid",
    "slug": "technology",
    "name": "Technology",
    "description": "Software engineering, computer systems, and digital tooling.",
    "icon": "code",
    "sort_order": 1,
    "is_active": true,
    "created_at": "2026-10-21T18:00:00Z",
    "skills_count": 5
  }
]
```

### `GET /api/v1/disciplines/{slug}` 🌐
Retrieve discipline details by slug with all active contained skills.
```json
// Response 200 OK
{
  "id": "uuid",
  "slug": "technology",
  "name": "Technology",
  "description": "...",
  "icon": "code",
  "sort_order": 1,
  "is_active": true,
  "created_at": "2026-10-21T18:00:00Z",
  "skills_count": 5,
  "skills": [
    {
      "id": "uuid",
      "slug": "web-principles",
      "name": "How the Web Works",
      "difficulty_level": "FOUNDATIONAL",
      "icon": null,
      "sort_order": 1
    }
  ]
}
```

### `POST /api/v1/disciplines` 🔓🛡️
Create a new discipline (admin privilege required).
```json
// Request
{
  "slug": "technology",
  "name": "Technology",
  "description": "Optional description",
  "icon": "code",
  "sort_order": 1
}
// Response 201 Created
{ "id": "uuid", "slug": "technology", "name": "Technology", "skills_count": 0, ... }
```

### `GET /api/v1/skills` 🌐
List active skills with optional filtering by discipline, difficulty level, or search term.
- Query parameters:
  - `discipline`: Filter by discipline slug (e.g. `?discipline=technology`)
  - `difficulty`: Filter by `FOUNDATIONAL`, `INTERMEDIATE`, or `ADVANCED`
  - `search`: Search query matching name, slug, or description
```json
// Response 200 OK
[
  {
    "id": "uuid",
    "slug": "html-semantics",
    "name": "HTML Structure & Semantics",
    "description": "...",
    "discipline_id": "uuid",
    "discipline_slug": "technology",
    "discipline_name": "Technology",
    "parent_skill_id": null,
    "difficulty_level": "FOUNDATIONAL",
    "icon": null,
    "sort_order": 2,
    "is_active": true,
    "created_at": "2026-10-21T18:00:00Z"
  }
]
```

### `GET /api/v1/skills/{slug}` 🌐
Retrieve full skill detail including direct prerequisite skills and unlocked dependent skills.
```json
// Response 200 OK
{
  "id": "uuid",
  "slug": "css-layouts",
  "name": "CSS & Responsive Layouts",
  "description": "Flexbox, CSS Grid, media queries.",
  "discipline_id": "uuid",
  "discipline_slug": "technology",
  "discipline_name": "Technology",
  "difficulty_level": "INTERMEDIATE",
  "prerequisites": [
    { "id": "uuid", "slug": "html-semantics", "name": "HTML Structure & Semantics", "difficulty_level": "FOUNDATIONAL" }
  ],
  "unlocked_skills": [],
  "courses_count": 1
}
```

### `GET /api/v1/skills/taxonomy/map` 🌐
Retrieve full active graph structure (nodes, edges, disciplines) for the interactive Skill Map visualizer.
```json
// Response 200 OK
{
  "nodes": [
    {
      "id": "uuid",
      "slug": "web-principles",
      "name": "How the Web Works",
      "discipline_slug": "technology",
      "difficulty_level": "FOUNDATIONAL",
      "description": "...",
      "icon": null
    }
  ],
  "edges": [
    { "source": "uuid-prerequisite-skill", "target": "uuid-dependent-skill" }
  ],
  "disciplines": [ ... ]
}
```

### `POST /api/v1/skills` 🔓🛡️
Create a new skill (creator or admin required).
```json
// Request
{
  "slug": "docker-containers",
  "name": "Docker & Containerization",
  "discipline_id": "uuid",
  "difficulty_level": "INTERMEDIATE",
  "description": "Container architecture and multi-stage builds."
}
```

### `PATCH /api/v1/skills/{skill_id}` 🔓🛡️
Update skill properties (creator or admin required).

### `POST /api/v1/skills/{skill_id}/prerequisites` 🔓🛡️
Establish a directed prerequisite dependency (`skill_id` requires `prerequisite_skill_id`).
- Validations:
  - Cannot depend on self (400)
  - Prerequisite must exist (404)
  - No duplicate relationship (409)
  - Rejects circular dependency cycles via BFS cycle detection (400 `CIRCULAR_DEPENDENCY`)
```json
// Request
{ "prerequisite_skill_id": "uuid-prerequisite" }
// Response 201 Created
{ "skill_id": "uuid", "prerequisite_skill_id": "uuid-prerequisite", "created_at": "..." }
```

### `DELETE /api/v1/skills/{skill_id}/prerequisites/{prerequisite_id}` 🔓🛡️
Remove a directed prerequisite relationship (creator or admin required). Returns 204 No Content.

---

## Course Catalog (Public Discovery) (Phase 3 Implemented)

### `GET /api/v1/courses` 🌐
Search and filter published courses in the public catalog.
- Strictly excludes drafts (`status == 'DRAFT'`), unapproved, and archived (`status == 'ARCHIVED'`) courses.
- Only courses with `status == 'PUBLISHED'` and an active published version snapshot (`is_active == true`) are returned.
- Query parameters:
  - `discipline`: Filter by discipline slug (e.g. `?discipline=technology`)
  - `difficulty`: Filter by `BEGINNER`, `INTERMEDIATE`, or `ADVANCED`
  - `search`: Search query across title, slug, and short_description
  - `page`: Page number (default: 1, min: 1)
  - `limit`: Items per page (default: 10, max: 50)
```json
// Response 200 OK
{
  "items": [
    {
      "id": "uuid",
      "slug": "web-development-foundations",
      "title": "Web Development Foundations",
      "short_description": "Master the architectural building blocks of modern web engineering.",
      "discipline_id": "uuid",
      "discipline_slug": "technology",
      "discipline_name": "Technology",
      "difficulty_level": "BEGINNER",
      "estimated_duration_minutes": 360,
      "cover_image_url": null,
      "status": "PUBLISHED",
      "version_number": 1,
      "skills": [
        { "id": "uuid", "slug": "html-semantics", "name": "HTML Structure & Semantics", "difficulty_level": "FOUNDATIONAL" }
      ]
    }
  ],
  "total": 3,
  "page": 1,
  "limit": 10,
  "pages": 1
}
```

### `GET /api/v1/courses/{slug}` 🌐
Retrieve full curriculum (modules, lesson outlines, learning objectives) from the **current published version**.
- Returns 404 for draft or archived courses.
```json
// Response 200 OK
{
  "id": "uuid",
  "slug": "web-development-foundations",
  "title": "Web Development Foundations",
  "short_description": "...",
  "full_description": "...",
  "discipline_id": "uuid",
  "discipline_slug": "technology",
  "discipline_name": "Technology",
  "difficulty_level": "BEGINNER",
  "estimated_duration_minutes": 360,
  "status": "PUBLISHED",
  "version_number": 1,
  "published_at": "2026-10-21T18:00:00Z",
  "learning_objectives": [
    "Explain the client-server request-response lifecycle and DNS resolution."
  ],
  "skills": [ ... ],
  "modules": [
    {
      "id": "uuid",
      "title": "How the Web Works",
      "description": "Protocols, browsers, IP addressing, DNS resolution.",
      "sort_order": 1,
      "lessons": [
        {
          "id": "uuid",
          "slug": "web-architecture",
          "title": "Clients, Servers, and HTTP Requests",
          "description": "Understanding URLs, HTTP methods, headers.",
          "learning_objectives": [ ... ],
          "estimated_minutes": 30,
          "sort_order": 1,
          "content_version": 1,
          "blocks": [ ... ]
        }
      ]
    }
  ]
}
```

### `GET /api/v1/courses/{course_slug}/lessons/{lesson_slug}` 🌐
Retrieve individual lesson details and structured content blocks from the active published version.
```json
// Response 200 OK
{
  "id": "uuid",
  "slug": "web-architecture",
  "title": "Clients, Servers, and HTTP Requests",
  "description": "...",
  "learning_objectives": [ ... ],
  "estimated_minutes": 30,
  "sort_order": 1,
  "content_version": 1,
  "blocks": [
    {
      "id": "uuid",
      "block_type": "heading",
      "content": { "level": 2, "text": "Clients, Servers, and HTTP Requests" },
      "sort_order": 1
    },
    {
      "id": "uuid",
      "block_type": "text",
      "content": { "format": "markdown", "text": "In this lesson..." },
      "sort_order": 2
    },
    {
      "id": "uuid",
      "block_type": "callout",
      "content": { "variant": "key_concept", "title": "Core Principle", "text": "..." },
      "sort_order": 3
    }
  ]
}
```

---

## Course Authoring & Version Publishing (Phase 3 Implemented)

### `POST /api/v1/courses` 🔓🛡️
Create a new course aggregate and its initial working draft (version 0). Creator or admin privilege required.
```json
// Request
{
  "slug": "cloud-architecture",
  "title": "Cloud Architecture Systems",
  "short_description": "Scalable cloud patterns on modern infrastructure.",
  "full_description": "Comprehensive guide to distributed systems.",
  "discipline_id": "uuid",
  "difficulty_level": "INTERMEDIATE",
  "estimated_duration_minutes": 300,
  "learning_objectives": ["Design multi-region systems"],
  "skill_ids": ["uuid-skill-1"]
}
```

### `GET /api/v1/courses/{course_id}/draft` 🔓🛡️
Retrieve the current working draft. If the course is published and has no open draft, this clones the published snapshot into a new working draft. Only the owner or admin can view drafts.

### `PATCH /api/v1/courses/{course_id}` 🔓🛡️
Update course aggregate metadata and draft objectives.

### `POST /api/v1/courses/{course_id}/draft/modules` 🔓🛡️
Add a module to the working draft.
```json
// Request
{ "title": "Module 1: Foundations", "description": "Intro", "sort_order": 1 }
```

### `PATCH /api/v1/courses/{course_id}/draft/modules/{module_id}` 🔓🛡️
Update draft module metadata.

### `DELETE /api/v1/courses/{course_id}/draft/modules/{module_id}` 🔓🛡️
Delete a module and its lessons from the working draft.

### `POST /api/v1/courses/{course_id}/draft/modules/{module_id}/lessons` 🔓🛡️
Add a lesson unit to a draft module.
```json
// Request
{ "slug": "lesson-1", "title": "Lesson 1", "estimated_minutes": 20, "sort_order": 1 }
```

### `PATCH /api/v1/courses/{course_id}/draft/lessons/{lesson_id}` 🔓🛡️
Update lesson outline metadata.

### `PUT /api/v1/courses/{course_id}/draft/lessons/{lesson_id}/content` 🔓🛡️
Atomically replace content blocks for a draft lesson with a validated `LessonContentDocument`.
- Validates block schemas, rich-text tags, and media host allowlists.
```json
// Request
{
  "document": {
    "schema_version": "1.0",
    "learning_objectives": ["Understand DNS"],
    "blocks": [
      { "id": "b1", "type": "heading", "data": { "level": 2, "text": "DNS Resolution" } },
      { "id": "b2", "type": "text", "data": { "format": "markdown", "text": "How recursive resolvers work." } },
      { "id": "b3", "type": "callout", "data": { "variant": "key_concept", "title": "TTL", "text": "Time-to-live controls caching." } }
    ]
  }
}
```

### `POST /api/v1/courses/{course_id}/publish` 🔓🛡️
Atomically snapshot and publish the working draft into an immutable published version.
- Enforces validations: at least 1 module, every module has at least 1 lesson, every lesson has at least 1 validated content block, non-empty learning objectives.
- Allocates next version number transactionally (v1, v2, ...).
- Stamps `published_at`, `publisher_id`, `changelog`.
- Sets `is_active = true` and updates `course.current_version_id`.
- Deactivates previous versions while preserving their historical snapshots intact.
```json
// Request
{ "changelog": "Initial course release v1.0" }
// Response 200 OK
{
  "course_id": "uuid",
  "version_id": "uuid",
  "version_number": 1,
  "published_at": "2026-10-21T18:00:00Z",
  "publisher_id": "uuid",
  "changelog": "Initial course release v1.0"
}
```

### `POST /api/v1/courses/{course_id}/unpublish` 🔓🛡️
Transition course status to `DRAFT`, immediately removing it from public catalog discovery while keeping all historical published versions in the database.

### `POST /api/v1/courses/{course_id}/archive` 🔓🛡️
Transition course status to `ARCHIVED`, removing it from discovery and preventing edits.

---

## Course & Lesson Retrieval

### `POST /api/v1/courses/{course_slug}/enroll` 🔓
Enroll the authenticated user in the current active version of the course.
```json
// Response 201
{ "enrollment": { "id": "uuid", "course_version_id": "uuid", "enrolled_at": "..." } }
```
- Idempotent: re-enrolling returns the existing enrollment.

### `GET /api/v1/enrollments` 🔓
List the authenticated user's enrollments with progress summaries.

### `GET /api/v1/enrollments/{enrollment_id}` 🔓
Enrollment detail with full module/lesson structure and progress.

### `GET /api/v1/enrollments/{enrollment_id}/lessons/{lesson_id}` 🔓
Full lesson content: blocks (text, code examples, media) and activity references.
- Authorization: user must be enrolled in the course version containing this lesson.

### `POST /api/v1/enrollments/{enrollment_id}/lessons/{lesson_id}/start` 🔓
Mark lesson as started (creates lesson_progress record if not exists).

### `POST /api/v1/enrollments/{enrollment_id}/lessons/{lesson_id}/complete` 🔓
Mark lesson as completed.
- Validation: all required activities in the lesson must be passed.

---

## Activity Attempts & Interactive Assessments (Phase 5 Implemented)

### `GET /api/v1/activities/{activity_id}` 🌐
Retrieve public activity definition.
- **Security Invariant:** Confidential answer keys (`answer_key`), hidden test cases, and internal rubric solutions are strictly stripped on the server before delivery.

```json
// Response 200 OK
{
  "id": "uuid",
  "lesson_id": "uuid",
  "activity_type": "single_choice",
  "title": "HTML5 Primary Landmark",
  "instructions": "Select the correct semantic element...",
  "configuration": {
    "options": [
      { "id": "opt-main", "text": "<main> — the dominant content landmark" },
      { "id": "opt-div", "text": "<div id='content'> — a generic container" }
    ]
  },
  "max_attempts": 3,
  "sort_order": 1,
  "passing_score": 70.0,
  "created_at": "2026-10-24T00:00:00Z",
  "updated_at": "2026-10-24T00:00:00Z"
}
```

### `GET /api/v1/lessons/{lesson_id}/activities` 🌐 / 🔓
List all interactive activities configured for a lesson.
- If unauthenticated, returns activity summaries with `attempts_count: 0`.
- If authenticated, calculates and returns the current learner's `best_score`, `passed` status, attempt counts, and `can_retry`.

```json
// Response 200 OK
[
  {
    "id": "uuid",
    "lesson_id": "uuid",
    "activity_type": "single_choice",
    "title": "HTML5 Primary Landmark",
    "instructions": "...",
    "sort_order": 1,
    "max_attempts": 3,
    "passing_score": 70.0,
    "best_score": 100.0,
    "passed": true,
    "attempts_count": 1,
    "can_retry": true
  }
]
```

### `POST /api/v1/activities/{activity_id}/attempts` 🔓
Submit a learner attempt for server-authoritative grading and recording.
- **Security Invariants:**
  - Enforces `max_attempts` limit. Exceeding returns `400 Bad Request` with code `RETRY_LIMIT_EXCEEDED`.
  - Scores and feedback are calculated strictly on the server; client-provided scores are never trusted.
  - Submissions are validated deterministically against available activity options/identifiers.

```json
// Request Payloads by Activity Type:

// 1. Single Choice:
{ "submission": { "selected_option_id": "opt-main" } }

// 2. Multiple Select:
{ "submission": { "selected_option_ids": ["lm-header", "lm-main"] } }

// 3. True / False:
{ "submission": { "selected_boolean": true } }

// 4. Short Answer:
{ "submission": { "text": "time blocking" } }

// 5. Fill in the Blank:
{ "submission": { "answers": { "blank1": "nav", "blank2": "main" } } }

// 6. Ordering:
{ "submission": { "ordered_item_ids": ["star-s", "star-t", "star-a", "star-r"] } }

// 7. Matching:
{ "submission": { "pairs": { "task-server": "quad-1", "task-strategy": "quad-2" } } }

// 8. Scenario:
{ "submission": { "selected_decision_id": "dec-bluf" } }

// 9. Code Exercise:
{ "submission": { "code": "def solve(): return 4", "language": "python" } }
```

```json
// Response 201 Created (Deterministic Graded Response)
{
  "id": "uuid",
  "user_id": "uuid",
  "activity_id": "uuid",
  "attempt_number": 1,
  "status": "graded",
  "submission": { "selected_option_id": "opt-main" },
  "result": { "selected_option_id": "opt-main", "is_correct": true },
  "score": 100.0,
  "max_score": 100.0,
  "passed": true,
  "feedback": {
    "is_correct": true,
    "message": "Correct! Well done.",
    "explanation": "<main> represents the dominant content of the <body>."
  },
  "started_at": "2026-10-24T00:00:00Z",
  "completed_at": "2026-10-24T00:00:00Z",
  "can_retry": true,
  "attempts_remaining": 2
}
```

### `GET /api/v1/activities/{activity_id}/attempts` 🔓
Retrieve the current authenticated user's attempt history for this activity, sorted latest first.

```json
// Response 200 OK
{
  "activity_id": "uuid",
  "total_attempts": 2,
  "max_attempts": 3,
  "can_retry": true,
  "attempts": [
    {
      "id": "uuid",
      "attempt_number": 2,
      "status": "graded",
      "score": 100.0,
      "passed": true,
      ...
    }
  ]
}
```

### `GET /api/v1/activities/{activity_id}/attempts/{attempt_id}` 🔓
Retrieve details of a specific attempt.
- **Cross-User Authorization:** Learners can only view their own attempts. Attempts by other users return `403 Forbidden` (`FORBIDDEN`). Admins can inspect any attempt.

### `POST /api/v1/activities` 🔓🛡️ (creator/admin)
Author a new interactive activity along with its confidential grading configuration.
- **Answer Key Protection:** The `answer_key` is persisted securely to `grading_configs` and omitted from the returned `ActivityDetailResponse`.

---

## Assessment Results

### `GET /api/v1/enrollments/{enrollment_id}/results` 🔓
Summary of all activity results within an enrollment.
```json
{
  "modules": [
    {
      "module_id": "uuid",
      "title": "HTML Basics",
      "lessons": [
        {
          "lesson_id": "uuid",
          "title": "Your First Page",
          "activities": [
            { "activity_id": "uuid", "type": "code_exercise", "best_score": 100, "passed": true, "attempts": 2 }
          ]
        }
      ]
    }
  ],
  "overall_score": 87.5,
  "completed_activities": 12,
  "total_activities": 15
}
```

---

## Learner Progress & Mastery

### `GET /api/v1/progress/dashboard` 🔓
Aggregated dashboard data: active enrollments, recent activity, skill mastery, achievements.

### `GET /api/v1/progress/skills` 🔓
Skill mastery overview for the authenticated user.
```json
{
  "skills": [
    { "skill_id": "uuid", "name": "HTML", "mastery_level": 85.0, "last_assessed_at": "..." },
    { "skill_id": "uuid", "name": "CSS", "mastery_level": 42.0, "last_assessed_at": "..." }
  ]
}
```

### `GET /api/v1/progress/achievements` 🔓
List earned achievements.

### `GET /api/v1/progress/recommendations` 🔓
Personalized course and skill recommendations based on current mastery and goals.

---

## AI Tutoring

### `POST /api/v1/ai/tutor` 🔓
Ask the AI tutor a question within a lesson context.
```json
// Request
{
  "lesson_id": "uuid",
  "activity_id": "uuid (optional)",
  "question": "Why does my CSS flexbox not center vertically?",
  "context": { "recent_code": "...(optional)" }
}
// Response 200
{
  "response": "To center vertically with flexbox, you need...",
  "suggestions": ["Try adding align-items: center", "Check the container height"],
  "usage": { "tokens_used": 450 }
}
```

### `POST /api/v1/ai/feedback` 🔓
Request AI feedback on an open-ended submission.
```json
// Request
{
  "activity_id": "uuid",
  "attempt_id": "uuid"
}
// Response 202
{ "status": "processing", "estimated_seconds": 15 }
```
- Result delivered through attempt polling or WebSocket.

### Rate Limits
- AI tutoring: 30 requests per hour per user.
- AI feedback: 10 requests per hour per user.
- Limits configurable per role.

---

## Projects & Portfolios

### `GET /api/v1/projects/{project_id}` 🔓
Project details and requirements.

### `POST /api/v1/projects/{project_id}/submissions` 🔓
Create or update a project submission.
```json
{
  "content": { "files": [...], "description": "...", "live_url": "..." }
}
```

### `POST /api/v1/projects/{project_id}/submissions/{submission_id}/submit` 🔓
Submit for evaluation (changes status from draft to submitted).

### `GET /api/v1/portfolios/me` 🔓
Get authenticated user's portfolio configuration and items.

### `PATCH /api/v1/portfolios/me` 🔓
Update portfolio settings (visibility, slug, bio).

### `GET /api/v1/portfolios/{slug}` 🌐
View a public portfolio.

---

## Course Creation & Publication (Creator Role)

### `POST /api/v1/creator/courses` 🔓🛡️ (creator)
Create a new course draft.

### `GET /api/v1/creator/courses` 🔓🛡️ (creator)
List courses owned by the authenticated creator.

### `PUT /api/v1/creator/courses/{course_id}/versions/{version_id}/modules` 🔓🛡️ (creator)
Update module structure for a draft version.

### `PUT /api/v1/creator/courses/{course_id}/versions/{version_id}/modules/{module_id}/lessons/{lesson_id}` 🔓🛡️ (creator)
Update lesson content and blocks.

### `POST /api/v1/creator/courses/{course_id}/versions/{version_id}/submit-for-review` 🔓🛡️ (creator)
Submit a course version for review.

### `POST /api/v1/admin/reviews/{review_id}/decide` 🔓🛡️ (admin)
Approve or reject a course version.
```json
{ "decision": "approved", "comments": "Looks great, minor suggestion on module 3." }
```

### `POST /api/v1/creator/courses/{course_id}/versions/{version_id}/publish` 🔓🛡️ (creator)
Publish an approved course version (makes it the active version).

---

## Request Validation Rules

1. **All request bodies** are validated against Pydantic schemas. Invalid requests receive 400 with field-level error details.
2. **Path parameters** (UUIDs, slugs) are validated for format before database lookup.
3. **Query parameters** have documented defaults and maximum values (e.g., `page_size` max 100).
4. **File uploads** are validated for type, size and content (see SECURITY.md).
5. **String inputs** are trimmed and length-limited. HTML is sanitized in user-generated content.

## Authorization Enforcement

Every endpoint performs server-side authorization:
- **Enrollment-gated content:** Lesson and activity endpoints verify the user has an active enrollment.
- **Ownership checks:** Profile, portfolio and creator endpoints verify resource ownership.
- **Role checks:** Creator and admin endpoints verify user role.
- **Cross-resource validation:** Activity attempts verify the activity belongs to a lesson in the user's enrolled course version.
