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

## Skill & Course Discovery

### `GET /api/v1/skills` 🌐
List all skills, optionally filtered by category.
```
?category=programming&search=javascript
```
Response includes prerequisite relationships for skill-map rendering.

### `GET /api/v1/skills/{skill_id}` 🌐
Skill detail with prerequisite tree and associated courses.

### `GET /api/v1/courses` 🌐
Browse published courses.
```
?skill_id=uuid&search=web+development&sort=popular&page=1&page_size=20
```

### `GET /api/v1/courses/{course_slug}` 🌐
Course detail: description, skill, modules overview, estimated time, prerequisites.
- Does **not** include full lesson content (requires enrollment).

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

## Activity Attempts & Submissions

### `GET /api/v1/activities/{activity_id}` 🔓
Activity detail: type, instructions, configuration (starter code, question structure).
- Sensitive configuration (test case expected outputs, rubric answers) is **not** included.

### `POST /api/v1/activities/{activity_id}/attempts` 🔓
Submit an attempt.
```json
// Code exercise
{ "submission": { "code": "function add(a,b) { return a+b; }", "language": "javascript" } }

// Quiz
{ "submission": { "answers": [{ "question_id": "q1", "answer": "B" }] } }

// Conversation practice
{ "submission": { "responses": [{ "prompt_id": "p1", "audio_url": "...", "transcript": "..." }] } }

// Practical task
{ "submission": { "response": "My analysis of the scenario...", "decisions": [...] } }
```

Response (immediate for automated grading):
```json
// Response 201
{
  "attempt": {
    "id": "uuid",
    "attempt_number": 1,
    "score": 85.00,
    "passed": true,
    "result": { "tests_passed": 4, "tests_total": 5, "details": [...] },
    "feedback": { "summary": "...", "hints": [...] }
  }
}
```

Response (async for AI-graded activities):
```json
// Response 202
{
  "attempt": {
    "id": "uuid",
    "attempt_number": 1,
    "status": "evaluating"
  }
}
```

### `GET /api/v1/activities/{activity_id}/attempts` 🔓
List the authenticated user's attempts for this activity.

### `GET /api/v1/activities/{activity_id}/attempts/{attempt_id}` 🔓
Get a specific attempt's details and results.

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
