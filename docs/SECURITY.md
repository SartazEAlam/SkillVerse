# Security — SkillVerse

This document defines the security requirements, threat model, and mitigation strategies for SkillVerse.

---

## Authentication and Authorization

### Authentication
- **Password hashing:** Argon2id (via `pwdlib[argon2]`) with strict complexity enforcement (min 8 chars, uppercase, lowercase, digit, special character).
- **JWT access tokens:** Short-lived (15 minutes). Signed with HS256 using `JWT_SECRET_KEY` (stateless verification per request).
- **Refresh tokens:** Cryptographically secure random 48-byte URL-safe string (`secrets.token_urlsafe(48)`). Stored as SHA-256 hashes in database `refresh_tokens` table. Rotated on each use; revoked upon user logout.
- **OAuth 2.0 PKCE:** PKCE flow for social authentication (Google; endpoints `GET /api/v1/auth/oauth/{provider}/authorize` and `POST /api/v1/auth/oauth/{provider}/callback`). Clients generate a cryptographically random `code_verifier` and SHA-256 `code_challenge` (S256). An unpredictable `state` parameter is verified server-side with 10-minute expiry against CSRF. Redirect URIs are strictly validated against pre-configured whitelist / CORS origins.
- **Email normalization:** All email addresses are normalized (stripped and lowercased) prior to database queries and storage to prevent duplicate registrations and case-sensitivity bypasses.
- **Email verification:** Dev mode logs tokens to console; tokens expire in 24 hours. Token logging strictly suppressed in production environments.
- **Password reset:** Time-limited tokens (1 hour). Initiations always return generic 200 responses to prevent account enumeration.
- **Rate limiting on auth endpoints:** Sliding-window in-memory enforcement with `Retry-After` headers:
  - Login: 10 attempts per 15 minutes per IP.
  - Registration: 5 attempts per hour per IP.
  - Password reset: 3 attempts per hour per email.
  - OAuth authorization & callback: 10 attempts per 15 minutes per IP.

### Token Storage Architecture & Cookie Migration Plan
- **Current Phase 2 Implementation:**
  - Tokens are transmitted via JSON response bodies (`access_token`, `refresh_token`, `expires_in`).
  - Frontend SPA stores tokens in `localStorage` (`skillverse_access_token`, `skillverse_refresh_token`).
  - Automated 401 interception in `frontend/src/services/api.ts` transparently handles refresh rotation and retries queued requests.
- **Known Security Limitation:**
  - Storing tokens in `localStorage` exposes them to potential exfiltration if an XSS vulnerability exists. Additionally, stateless JWT access tokens remain valid until their 15-minute expiration window closes unless a Redis denylist is queried.
- **Production Hardening Migration Plan (Targeted for Phase 5 / Pre-Release):**
  1. *HttpOnly Cookie for Refresh Token:* Transition `refresh_token` to `HttpOnly; Secure; SameSite=Lax; Path=/api/v1/auth; Max-Age=2592000` cookie set by the backend on login/register/refresh.
  2. *In-Memory Access Token:* Keep `access_token` purely in React client memory (AuthContext state), never persisting it to browser storage.
  3. *Silent Boot Refresh:* On application mount / page reload, execute a silent background `POST /api/v1/auth/refresh` with `credentials: 'include'` to hydrate the session.
  4. *CSRF Mitigation:* Protect the cookie-authenticated refresh endpoint using an `X-CSRF-Token` header or double-submit cookie validation.
  5. *Dual-Client Support:* Maintain Authorization header support for future mobile clients (Phase 7+) while enforcing cookies for web browsers.

### Production Environment Invariants & Database Security
- **No Silent SQLite Fallback:** Backend `Settings` strictly validates that when `ENVIRONMENT=production`, `DATABASE_URL` cannot use SQLite. Startup halts immediately with a validation error if PostgreSQL is not specified.
- **Secret Length Enforcement:** Production mode rejects default placeholder keys and enforces a minimum 32-character `JWT_SECRET_KEY`.
- **Database Testing Status:** Automated tests currently execute against SQLite (`test.db`) due to local Docker/PostgreSQL unavailability. **PostgreSQL 16 integration is explicitly marked UNVERIFIED LOCALLY** and must be tested against a live PostgreSQL service in the CI/CD pipeline.

### Authorization
- **Server-side enforcement:** Every API endpoint checks authorization. Client-side checks are UX hints only.
- **Role-based access control (RBAC):** Three roles — Learner, Creator, Admin.
- **Resource-based access control:** Enrollment verification for course content. Ownership verification for profile and portfolio operations.
- **Principle of least privilege:** Default role is Learner. Creator and Admin roles require explicit assignment.
- **No privilege escalation through API:** Role changes require Admin action through a dedicated endpoint with audit logging.

---

## Secret Management

### Requirements
- **No hardcoded secrets.** Database passwords, API keys, JWT secrets, OAuth client secrets, AI provider keys and email service credentials must come from environment variables or a secrets manager.
- **`.env` never committed.** The `.gitignore` includes `.env` and all `.env.*` variants except `.env.example`.
- **`.env.example` committed** with placeholder values and comments describing each variable. No real values.
- **Secret rotation:** Architecture supports rotating JWT signing keys and database passwords without downtime.
- **Logging exclusions:** Secrets, tokens and passwords are never logged, even at debug level.

### Environment Variables (documented in `.env.example`)
```
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/skillverse

# Auth
JWT_SECRET_KEY=change-me-to-a-random-64-char-string
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# AI Provider
AI_PROVIDER=openai
AI_API_KEY=your-ai-api-key

# Object Storage
STORAGE_ENDPOINT=http://localhost:9000
STORAGE_ACCESS_KEY=minioadmin
STORAGE_SECRET_KEY=minioadmin
STORAGE_BUCKET=skillverse

# Email
EMAIL_PROVIDER=smtp
SMTP_HOST=localhost
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=

# Redis
REDIS_URL=redis://localhost:6379/0

# Code Sandbox
SANDBOX_ENABLED=true
SANDBOX_TIMEOUT_SECONDS=10
SANDBOX_MEMORY_LIMIT_MB=256
```

---

## Input Validation

### API Request Validation
- **Pydantic schemas** for all request bodies. Type checking, length limits, format validation.
- **Path parameters:** UUID format validated before database lookup.
- **Query parameters:** Whitelisted fields, bounded ranges (e.g., `page_size` max 100), type-safe parsing.
- **String sanitization:** Leading/trailing whitespace trimmed. Maximum lengths enforced.
- **HTML sanitization:** User-generated rich text (lesson content, bios) sanitized with an allowlist of safe tags and attributes. No `<script>`, `<iframe>`, `on*` event handlers.
- **JSON depth limits:** Nested JSONB fields have maximum depth limits to prevent resource exhaustion.

### Frontend Validation
- Client-side validation mirrors server-side rules for UX feedback.
- **Never trusted as the security boundary.** All validation re-executed server-side.

---

## File Upload Protection

### Allowed Upload Contexts
- Profile avatars.
- Course cover images (creator).
- Project submission files.
- Lesson media (creator).

### Protection Measures
| Measure | Implementation |
|---|---|
| File type validation | Allowlist of MIME types + magic byte verification (not just extension) |
| File size limits | Avatars: 2MB. Course images: 5MB. Project files: 50MB. Configurable per context. |
| Filename sanitization | Strip path traversal characters. Generate new UUID-based filenames. |
| Virus scanning | Integration point for ClamAV or similar (optional, recommended for production) |
| Storage isolation | Uploaded files stored in object storage, not on the application filesystem |
| No direct execution | Uploaded files are never executed or interpreted by the server |
| Access control | Private uploads require signed URLs with expiration |
| Content-Disposition | Force `attachment` disposition for downloads to prevent browser interpretation |

---

## AI Usage Limits and Privacy

### Rate Limits
| Feature | Limit | Window |
|---|---|---|
| AI Tutor questions | 30 | Per hour per user |
| AI Feedback requests | 10 | Per hour per user |
| Total AI calls | 100 | Per day per user |

Limits are configurable per user role. Admin can override for specific users.

### Privacy
- **Data sent to AI providers:** Lesson context, learner's question or submission, activity configuration. **No PII** (name, email) sent to AI providers.
- **Prompt engineering:** System prompts instruct the AI to be pedagogical (guide, don't give direct answers) and to refuse harmful requests.
- **Response filtering:** AI responses are checked for inappropriate content before delivery to the learner.
- **Audit logging:** All AI interactions logged with provider, model, token count and latency. Prompt and response stored for quality review. Logs retained for 90 days.
- **Opt-out:** Learners can disable AI features in their preferences. This disables AI tutoring and AI-assisted feedback.
- **No training on user data:** Contracts with AI providers must prohibit using SkillVerse user interactions for model training.

---

## Learner Data Retention and Deletion

### Data Categories and Retention

| Category | Examples | Retention |
|---|---|---|
| Account data | Email, profile, preferences | Until account deletion |
| Learning progress | Enrollments, lesson progress, mastery | Until account deletion |
| Activity attempts | Submitted code, quiz answers | Until account deletion (learner can delete individual attempts) |
| AI interactions | Tutor questions, AI responses | 90 days, then anonymized |
| Audit logs | Login events, admin actions | 1 year |
| Uploaded files | Avatars, project files | Until deleted by user or account deletion |

### Account Deletion
- Learners can request account deletion through settings.
- **Soft delete** with 30-day grace period (recoverable).
- After grace period: PII removed (email hashed, profile cleared). Learning data anonymized for aggregate analytics. Uploaded files deleted from object storage.
- Creator content that is published and has active enrollments: ownership transferred to admin or unpublished (policy decision pending).

### Data Export
- Learners can export their data (profile, progress, submissions) in JSON format.
- Export includes a manifest file describing what data is included and excluded.

---

## Audit Logging

### Events Logged

| Category | Events |
|---|---|
| Authentication | Login (success/failure), logout, password change, password reset, email verification |
| Authorization | Permission denied events, role changes |
| Data access | Profile views by admin, data export requests |
| Content | Course publication, version changes, content moderation |
| Code execution | Sandbox invocations, resource limit violations, execution errors |
| AI | All AI provider calls, token usage, response filtering events |
| Admin | User role changes, content review decisions, system configuration changes |

### Log Format
```json
{
  "event_type": "user.login.success",
  "user_id": "uuid",
  "resource_type": "session",
  "resource_id": "uuid",
  "ip_address": "192.168.1.1",
  "metadata": { "method": "password", "user_agent": "..." },
  "timestamp": "2026-10-17T15:30:00Z"
}
```

### Storage
- Audit events written to the `audit_events` database table.
- High-volume events (code execution, AI calls) may be written asynchronously through the background job queue to avoid blocking API responses.
- Logs never contain passwords, tokens, full request bodies or PII beyond user IDs.

---

## Untrusted Content Handling & Media Security (Phase 3 Implemented)

### Content Sanitization & Data Safety
- **Structured Block Data Model:** Lessons are never stored as arbitrary HTML blobs or executable code. Lessons consist of strictly typed Pydantic models (`HeadingBlockData`, `TextBlockData`, `ListBlockData`, `CodeExampleBlockData`, `CalloutBlockData`, `ImageBlockData`, `VideoBlockData`).
- **Rich-Text Sanitization (`sanitize_text`):** All markdown and text bodies pass through a server-side sanitizer that explicitly removes `<script>`, `<iframe>`, `<object>`, `<embed>`, inline event handlers (`onload`, `onclick`, `onerror`), and dangerous markup before persistence.
- **URI Scheme Restrictions (`validate_url`):** URLs for images, resources, and video streams must use `http` or `https`. `javascript:` URIs are strictly prohibited and immediately raise a validation error.
- **Video Embed Allowlist:** To prevent malicious iframes and remote content injection, video embed URLs are restricted to verified providers:
  - `youtube.com`, `www.youtube.com`, `youtu.be`
  - `vimeo.com`, `player.vimeo.com`
  - `assets.skillverse.dev` (official CDN)
  - `localhost`, `127.0.0.1` (development environments)
  Unrecognized streaming domains are rejected at API submission time.
- **Accessibility Enforcements:** Image blocks require descriptive `alt_text` (minimum 3 characters) to ensure compliance with WCAG screen reader accessibility standards.

### Authoring & Versioning Authorization
- **Role Requirements:** Taxonomy writes (disciplines, skills, prerequisites) and course authoring require authenticated sessions with `CREATOR` or `ADMIN` roles. Anonymous users are rejected with `401 Unauthorized`; learners are rejected with `403 Forbidden`.
- **Ownership Verification:** A creator can only edit drafts of courses they created (`course.creator_id == current_user.id`). Cross-author tampering is rejected with `403 Forbidden`. Admins possess platform-wide administrative override.
- **Published Version Immutability:** When a course version is published, its database record is stamped with `published_at` and `publisher_id`. Any subsequent write attempt directly targeting that version or its child modules/lessons/blocks raises a `409 Conflict` (`VERSION_IMMUTABLE`). Future curriculum updates must be performed against an isolated cloned draft (`version_number = 0`).

### Rendering Safety
- React's JSX escaping prevents XSS across UI presentation surfaces.
- Lesson blocks are delivered as structured data to be parsed by dedicated UI components, never passed directly to `dangerouslySetInnerHTML`.
- CSP (Content Security Policy) headers restrict script sources, inline scripts and external resources.
- CORS configured to allow only the SkillVerse frontend origin.

---

## Isolated Code Execution Requirements

### Threat Model
Learner-submitted code is **fully untrusted**. It may attempt:
- File system access (read secrets, write malware).
- Network access (exfiltrate data, attack other services).
- Resource exhaustion (CPU, memory, disk).
- Process escape (container breakout).
- Information gathering (environment enumeration).

### Isolation Requirements

| Requirement | Implementation |
|---|---|
| Process isolation | Each execution in a separate, disposable Docker container |
| Filesystem isolation | Read-only root filesystem. Writable tmpfs with size limit (10MB) |
| Network isolation | No outbound network access (Docker network=none) |
| CPU limits | cgroup CPU time limit (10 seconds) |
| Memory limits | cgroup memory limit (256MB, no swap) |
| PID limits | Maximum 64 processes per container |
| User isolation | Code runs as unprivileged user inside the container |
| Seccomp profile | Restricted syscall allowlist |
| No privileged operations | Drop all capabilities |
| Timeout | Hard kill after timeout + 2 second grace |
| Cleanup | Container destroyed after execution. No state persists. |

### Result Protocol
```json
{
  "status": "completed|timeout|error|killed",
  "exit_code": 0,
  "stdout": "...",
  "stderr": "...",
  "test_results": [
    { "name": "test_add", "passed": true, "output": "..." },
    { "name": "test_subtract", "passed": false, "expected": "5", "actual": "3" }
  ],
  "execution_time_ms": 250,
  "memory_used_mb": 12
}
```

---

## Common Abuse Scenarios and Mitigations

| Scenario | Mitigation |
|---|---|
| Credential stuffing | Rate limiting on login. Account lockout after 10 failures. CAPTCHA after 5 failures. |
| Spam account creation | Email verification required. Rate limit registration per IP. CAPTCHA on registration. |
| AI prompt injection | System prompts with guardrails. Response filtering. Usage limits. Audit logging. |
| Code execution abuse | Resource limits. Rate limiting (max 30 executions/hour). Monitoring for anomalous patterns. |
| Content scraping | Rate limiting on public endpoints. CAPTCHA for unauthenticated bulk access. |
| XSS via user content | HTML sanitization. CSP headers. React's default escaping. |
| CSRF | SameSite cookies. CSRF tokens for state-changing operations not using Bearer auth. |
| File upload abuse | Type validation. Size limits. Filename sanitization. Storage isolation. |
| Privilege escalation | Server-side role checks. No client-side role storage. Audit logging of role changes. |
| Data exfiltration via AI | No PII in AI prompts. Response filtering. Audit logging. Provider contracts. |
| Enumeration attacks | UUIDs for resource IDs. Consistent response times for auth operations. No email existence disclosure. |

---

## Phase 4: Content Rendering & Media Security Boundaries

With the introduction of the Universal Lesson Renderer in Phase 4, the frontend implements multi-layered security boundaries to prevent XSS, script injection, and iframe hijack attacks:

### 1. Rich Text & Markdown Sanitization
- **No Unsafe HTML Bypasses:** Content blocks strictly avoid `dangerouslySetInnerHTML` for untrusted user inputs.
- **Script and Handler Stripping:** Text blocks utilize deterministic markdown regex parsing for bold, italics, code, links, and blockquotes. Any injected `<script>`, `<iframe arbitrary>`, `<svg onload=...>`, or `javascript:` URI patterns are stripped or neutralized into inert text nodes.
- **Safe Link Enforcing:** Links generated by markdown parser validate target URLs against approved HTTP/HTTPS protocols, rendering with `rel="noopener noreferrer"`.

### 2. Code Example Display Isolation
- **Display-Only Invariant:** Code examples in Phase 4 are display-only. No learner code or content block code is evaluated in the browser runtime (`eval()`, `new Function()`, or dynamic script insertion).
- **Safe Syntax Highlighting:** Syntax coloring parses code tokens through regular expressions and CSS utility classes, never injecting raw HTML markup.
- **Clipboard Isolation:** Copy-to-clipboard functionality interacts solely with `navigator.clipboard.writeText()` using sanitized text strings.

### 3. Media & Video Embed Sandboxing
- **Provider Allowlist:** External video embedding is restricted to recognized educational providers (YouTube `youtube.com/embed/`, `youtube-nocookie.com/embed/`, and Vimeo `player.vimeo.com/video/`). Unknown video hosts are never rendered as embedded iframes; instead, a safe external link card is rendered.
- **Iframe Sandboxing:** All video iframes enforce `sandbox="allow-scripts allow-same-origin allow-presentation"` and `referrerpolicy="no-referrer-when-downgrade"`. Top-level navigation, popups, and arbitrary form submissions from embedded players are blocked.
- **Image Validation:** Image blocks require meaningful `alt_text` for accessibility and enforce responsive dimensions with error fallbacks preventing broken DOM exploits.

### 4. Stale Request Invalidation & Demo Isolation
- **AbortController Invalidation:** Every lesson route transition instantiates an `AbortController` to cancel in-flight network requests. Out-of-order API responses cannot overwrite active lesson state.
- **Demo Fallback Isolation:** Demo fallback mode is strictly gated to development or explicit demo tracks (`demo-*`). Backend failures (HTTP 500, network timeouts) display a transparent error card with retry capabilities and never mask system errors with demo content.

---

## Phase 5: Code Sandbox Execution Boundary & Assessment Confidentiality

With the introduction of the interactive assessment engine in Phase 5, the platform establishes critical confidentiality and execution boundaries:

### 1. Confidential Answer Keys & Secret Scrubbing
- **Server-Authoritative Evaluation:** All activity grading is executed server-side. Answer keys, correct options, rubrics, and solution benchmarks are never transmitted to client devices.
- **Scrubbed Activity Payloads:** Learner-facing activity endpoints serialize schemas via dedicated learner views (`ActivityLearnerResponse`), stripping `answer_key`, `grading_config`, and reference solutions before sending JSON payloads over the network.
- **Attempt History Isolation:** Attempt records are strictly scoped to the authenticated learner. Cross-user attempt inspection is rejected with `403 Forbidden`.

### 2. Untrusted Learner Code Isolation Boundary
- **Sandbox Boundary Contract:** Untrusted code execution is decoupled from the FastAPI application process via `SandboxRunnerInterface`. Learner code is never evaluated inside the API web worker.
- **Resource Constraints:** Invocations enforce strict cgroup resource constraints (CPU timeout, 256MB memory cap, no swap, unprivileged execution, process count limits).
- **Network Isolation:** Code container workers run with disabled network interfaces (`--network none`) to prevent SSRF, data exfiltration, or lateral network scanning.

---

## Phase 8: AI Tutoring Privacy, Sliding-Window Rate Limits & Opt-Out Enforcement

### 1. User Opt-Out Privacy Enforcement
- **Universal Opt-Out Check:** Learners can disable AI features via their preferences (`ai_opt_out: true`). Both the backend service layer and API routes verify this flag before invoking any AI provider.
- **Disabled Feedback Fallback:** When opt-out is active, AI tutor queries, hint requests, and formative writing feedback return explicit disabled indicators without dispatching external API requests.

### 2. User-Scoped Sliding-Window Rate Limiting
- **In-Memory Window Tracking:** AI interactions enforce sliding-window user-scoped rate limits (30 questions/hr, 10 progressive hints/hr). Requests exceeding limits receive HTTP 429 Too Many Requests with informative `Retry-After` headers.

### 3. Context Sanitization & Ephemeral Telemetry
- **PII & Answer Key Scrubbing:** Prompts sent to AI providers contain only instructional context, learner drafts, and scenario parameters. Confidential answer keys, user real names, and email addresses are strictly excluded.
- **Privacy-First Audit Logging:** The `ai_interactions` table records provider metadata, token usage, latency, and status codes. Raw user prompts and generated completions are not persisted to database tables by default.

---

## Phase 9: Artifact Storage Security, Submission Integrity & Portfolio Privacy Boundaries

With Phase 9, SkillVerse implements capstone project deliverables, learner file uploads, public showcase portfolios, and specialized practice activities. The following security controls govern these capabilities:

### 1. Provider-Neutral Storage Architecture & Key Isolation
- **Storage Abstraction:** The storage layer (`StorageInterface`, `LocalStorageService`) abstracts physical file persistence from application logic.
- **Random UUID Keys:** Uploaded files are never written using original client filenames or user-controlled paths. Each file is assigned a cryptographically random UUID storage key (`storage_key`).
- **Private-by-Default Isolation:** Files are stored in an isolated directory outside the web application document root. No web server statically serves the storage folder directly.

### 2. Binary Magic-Byte & Signature Verification
Every uploaded file undergoes two-tier validation: MIME type check and binary header (magic byte) verification:
- **PDF (`application/pdf`):** Byte offset 0 must match `%PDF-`.
- **PNG (`image/png`):** Byte offset 0 must match `\x89PNG\r\n\x1a\n`.
- **JPEG (`image/jpeg`):** Byte offset 0 must match `\xff\xd8\xff`.
- **WebP (`image/webp`):** Binary header validation requiring `RIFF` at byte offset 0 and `WEBP` at byte offset 8 (minimum 12 bytes). Renamed text files or truncated headers are strictly rejected.
- **ZIP (`application/zip`):** Byte offset 0 must match `PK\x03\x04`, `PK\x05\x06`, or `PK\x07\x08`.
- **Plaintext / Markdown / JSON (`text/plain`, `text/markdown`, `application/json`):** Strict UTF-8 validation and maximum file size enforcement.

### 3. Path Traversal & Base Directory Containment Protection
- **Containment Check (`_is_within_base_dir`):** Local storage operations resolve paths to strict canonical form and verify containment within the storage base directory using `os.path.commonpath` and `Path.is_relative_to`.
- **Attack Prevention:** Strictly rejects directory traversal sequences (`..`), null bytes (`\x00`), sibling directories sharing string prefixes with the base directory, and operations targeting the storage root itself.

### 4. Upload Quotas & Concurrency Protection
- **Per-File & Aggregate Bounds:** Enforces 20MB maximum per file, 50MB aggregate per submission, and maximum 10 files per submission.
- **Upload Rate Limiting:** 10 uploads per hour per user.
- **Dual-Layer Concurrency Strategy:**
  - *PostgreSQL (Production):* Row-level locking via `SELECT ... FOR UPDATE` (`with_for_update()`) on the active submission record within the transaction.
  - *SQLite (Local Harness):* Process-level mutex serialization per submission ID (`_submission_locks` registry) to guarantee thread safety.
- **Transactional Rollback:** Database commit failures or write exceptions automatically unlink newly written storage files to prevent orphaned artifacts.

### 5. 5-Gate Download Authorization Model
Deliverable downloads for anonymous or third-party users require passing five mandatory security gates:
1. **Gate 1 (Portfolio Exists & Public):** The authoring learner's portfolio exists and is marked public (`portfolio.is_public == True`).
2. **Gate 2 (Submission Completed):** The referenced submission has successfully completed evaluation (`submission.status == 'COMPLETED'`).
3. **Gate 3 (Artifact Public):** The artifact itself is explicitly flagged as public (`artifact.is_public == True`).
4. **Gate 4 (Portfolio Item Reference):** A portfolio item exists that specifically references this submission ID or artifact ID.
5. **Gate 5 (Portfolio Item Public):** The referencing portfolio item visibility is set to public (`item.visibility == 'PUBLIC'`).

### 6. Download Response Hardening
- **Forced Download Disposition:** All artifact downloads set `Content-Disposition: attachment; filename="<sanitized>"`.
- **CRLF Sanitization:** Filenames in download headers are stripped of `\r` and `\n` characters to eliminate HTTP response splitting attacks and MIME confusion.

### 7. Submission State Machine Audit & Revision Immutability
- **Authoritative States:** Submissions follow `DRAFT` → `SUBMITTED` → `UNDER_REVIEW` → `EVALUATED` → `COMPLETED` (or `CHANGES_REQUESTED`).
- **Intermediate Audit State:** The `EVALUATED` state records rubric calculations and evaluator feedback before final completion status is determined.
- **Audit History:** Full transition timestamps and reasons are audited in `transition_history`. Prior revisions are preserved immutably via `revision_of_id`.

### 8. Portfolio Privacy & Sanitization
- **Tri-State Visibility:** Portfolios support `PRIVATE`, `UNLISTED`, and `PUBLIC` modes.
- **Access Denial:** Anonymous or non-owner requests to `PRIVATE` portfolios return HTTP 403 Forbidden.
- **Response Sanitization:** Third-party responses include only items with `visibility == 'PUBLIC'`. Internal storage keys, server filesystem paths, and internal evaluator notes are stripped from JSON payloads.
- **Slug Reservation:** Custom slugs are validated (3–100 alphanumeric/dash/underscore chars) and prohibited from matching reserved system routes (`RESERVED_SLUGS`).

### 9. Specialized Practice Non-Execution Invariant
- **No External Code Execution:** Practice activities (`web_practice`) do not fetch, download, or execute arbitrary learner code from external URLs.
- **Safe URL Syntax Validation:** External repository and live demonstration links are validated against safe protocols (`http`, `https`) and domain syntax (`SAFE_URL_REGEX`). Schemes like `javascript:`, `file:`, and `data:` are rejected.

