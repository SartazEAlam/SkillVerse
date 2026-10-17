# Security — SkillVerse

This document defines the security requirements, threat model, and mitigation strategies for SkillVerse.

---

## Authentication and Authorization

### Authentication
- **Password hashing:** bcrypt with a minimum work factor of 12.
- **JWT access tokens:** Short-lived (15 minutes). Signed with a strong secret (HS256 minimum) or asymmetric key (RS256 preferred for production).
- **Refresh tokens:** Stored hashed in the database. Rotated on each use. Revocable.
- **OAuth 2.0:** PKCE (Proof Key for Code Exchange) flow for social authentication (Google initially; endpoints `GET /api/v1/auth/oauth/{provider}/authorize` and `POST /api/v1/auth/oauth/{provider}/callback`). Clients generate a cryptographically random `code_verifier` and SHA-256 `code_challenge` (S256). An unpredictable `state` parameter is verified server-side against CSRF.
- **Email verification:** Required before full platform access. Tokens expire in 24 hours.
- **Password reset:** Time-limited tokens (1 hour). One active reset token per user. Previous tokens invalidated on use.
- **Rate limiting on auth endpoints:**
  - Login: 10 attempts per 15 minutes per IP/email combination.
  - Registration: 5 per hour per IP.
  - Password reset: 3 per hour per email.
  - OAuth authorization & callback: 10 attempts per 15 minutes per IP.

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

## Untrusted Content Handling

### User-Generated Content
- **Lesson text (creator-authored):** Sanitized HTML with allowlisted tags. No scripts, iframes or external resources.
- **Learner bios and comments:** Plain text or limited markdown. No HTML.
- **Code in submissions:** Stored as plain text. Never rendered as executable HTML in the platform UI. Displayed in syntax-highlighted code blocks.

### Rendering Safety
- React's JSX escaping prevents XSS in most contexts.
- `dangerouslySetInnerHTML` used **only** for sanitized lesson content, with DOMPurify or similar.
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
