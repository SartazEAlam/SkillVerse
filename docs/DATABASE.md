# Database Design — SkillVerse

This document describes the planned relational data model. **Phase 0 is documentation only** — these tables will be implemented incrementally through version-controlled Alembic migrations in later phases.

## Design Principles

1. **Referential integrity:** All relationships enforced through foreign keys.
2. **Soft deletion:** Records use `deleted_at` timestamps rather than hard deletion where user data is involved.
3. **Audit timestamps:** Every table has `created_at` and `updated_at` columns, ensuring complete lifecycle auditability. Strictly append-only logs (`audit_events`) require only `created_at` as historical log entries are immutable.
4. **UUIDs for public identifiers:** Primary keys use UUIDs to prevent enumeration attacks. Internal joins may use integer sequences for performance.
5. **Immutable versions:** Published course content is versioned and immutable.
6. **Normalized design:** Avoid duplication. Denormalize only with documented justification for performance.

---

## Entity Relationship Overview

```
Users ──────┬──> Enrollments ──> CourseVersions ──> Courses
            │         │
            │         ▼
            │    LessonProgress ──> Lessons ──> Modules ──> CourseVersions
            │         │
            │         ▼
            │    Attempts ──> Activities ──> Lessons
            │
            ├──> SkillMastery ──> Skills
            │
            ├──> Projects ──> Submissions
            │
            ├──> Achievements
            │
            └──> Portfolio

Skills ──> SkillPrerequisites (self-referencing)
Courses ──> CourseVersions ──> Modules ──> Lessons ──> LessonBlocks
                                                    └──> Activities ──> GradingConfig
```

---

## Table Definitions

### Users and Identity

#### `users`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | Unique user identifier |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Login email |
| password_hash | VARCHAR(255) | NULLABLE | bcrypt hash (null for OAuth-only users) |
| email_verified | BOOLEAN | NOT NULL, DEFAULT false | Whether email is verified |
| role | ENUM('learner','creator','admin') | NOT NULL, DEFAULT 'learner' | User role |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Registration timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update timestamp |
| deleted_at | TIMESTAMPTZ | NULLABLE | Soft deletion timestamp |

#### `user_profiles`
| Column | Type | Constraints | Description |
|---|---|---|---|
| user_id | UUID | PK, FK → users.id | One-to-one with user |
| display_name | VARCHAR(100) | NOT NULL | Public display name |
| avatar_url | TEXT | NULLABLE | Profile image URL |
| bio | TEXT | NULLABLE | Short biography |
| timezone | VARCHAR(50) | NULLABLE | User's timezone |
| preferences | JSONB | NOT NULL, DEFAULT '{}' | UI preferences (theme, language, etc.) |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Profile creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update timestamp |

#### `oauth_accounts`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | Record identifier |
| user_id | UUID | FK → users.id, NOT NULL | Owning user |
| provider | VARCHAR(50) | NOT NULL | OAuth provider name ('google') |
| provider_user_id | VARCHAR(255) | NOT NULL | User ID from provider |
| | | UNIQUE(provider, provider_user_id) | One account per provider |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Link timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update timestamp |

#### `refresh_tokens`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | Token identifier |
| user_id | UUID | FK → users.id, NOT NULL | Token owner |
| token_hash | VARCHAR(255) | NOT NULL, UNIQUE | SHA-256 hash of refresh token |
| expires_at | TIMESTAMPTZ | NOT NULL | Expiration timestamp |
| revoked_at | TIMESTAMPTZ | NULLABLE | Revocation timestamp |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Issue timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update / revocation timestamp |

---

### Skills and Taxonomy

### Skills and Taxonomy (Phase 3 Implemented)

#### `disciplines`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID (CHAR(36)) | PK | Unique discipline identifier |
| slug | VARCHAR(100) | UNIQUE, NOT NULL, INDEX | Stable URL-friendly slug (e.g. 'technology', 'communication') |
| name | VARCHAR(200) | NOT NULL | Human-readable discipline name |
| description | TEXT | NULLABLE | Detailed description of the field |
| icon | VARCHAR(100) | NULLABLE | Lucide icon identifier for UI navigation |
| sort_order | INTEGER | NOT NULL, DEFAULT 0 | Display ordering |
| is_active | BOOLEAN | NOT NULL, DEFAULT true | Active / visibility toggle |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update timestamp |

#### `skills`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID (CHAR(36)) | PK | Unique skill identifier |
| slug | VARCHAR(100) | UNIQUE, NOT NULL, INDEX | Stable unique slug |
| name | VARCHAR(200) | NOT NULL | Human-readable skill name |
| description | TEXT | NULLABLE | Capability description |
| discipline_id | UUID (CHAR(36)) | FK → disciplines.id, NOT NULL, ON DELETE RESTRICT | Owning discipline |
| parent_skill_id | UUID (CHAR(36)) | FK → skills.id, NULLABLE, ON DELETE SET NULL | Optional hierarchical parent |
| difficulty_level | ENUM('FOUNDATIONAL','INTERMEDIATE','ADVANCED') | NOT NULL, DEFAULT 'FOUNDATIONAL' | Target competency depth |
| icon | VARCHAR(100) | NULLABLE | Icon identifier for Skill Map visualizer |
| sort_order | INTEGER | NOT NULL, DEFAULT 0 | Presentation order |
| is_active | BOOLEAN | NOT NULL, DEFAULT true | Active / visibility toggle |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update timestamp |

#### `skill_prerequisites`
| Column | Type | Constraints | Description |
|---|---|---|---|
| skill_id | UUID (CHAR(36)) | FK → skills.id, NOT NULL, ON DELETE CASCADE | Dependent skill requiring prerequisite |
| prerequisite_skill_id | UUID (CHAR(36)) | FK → skills.id, NOT NULL, ON DELETE CASCADE | Prerequisite skill required first |
| | | PK(skill_id, prerequisite_skill_id) | Composite primary key |
| | | CHECK(skill_id != prerequisite_skill_id) | Database check constraint preventing self-dependencies |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Relationship establishment timestamp |

*Cycle Detection:* Enforced in service layer via breadth-first graph traversal preventing directed cycles prior to insert.

---

### Courses, Content, and Versioning (Phase 3 Implemented)

#### `courses`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID (CHAR(36)) | PK | Stable course aggregate root identifier |
| slug | VARCHAR(200) | UNIQUE, NOT NULL, INDEX | Stable course catalog slug |
| title | VARCHAR(300) | NOT NULL | Course title |
| short_description | TEXT | NOT NULL | Brief catalog summary |
| full_description | TEXT | NULLABLE | Detailed course description |
| discipline_id | UUID (CHAR(36)) | FK → disciplines.id, NOT NULL, ON DELETE RESTRICT | Primary academic/vocational discipline |
| difficulty_level | ENUM('BEGINNER','INTERMEDIATE','ADVANCED') | NOT NULL, DEFAULT 'BEGINNER' | Target learner experience |
| estimated_duration_minutes | INTEGER | NULLABLE | Total estimated study duration in minutes |
| cover_image_url | TEXT | NULLABLE | Optional cover illustration/banner |
| status | ENUM('DRAFT','PUBLISHED','ARCHIVED') | NOT NULL, DEFAULT 'DRAFT', INDEX | Aggregate lifecycle state |
| creator_id | UUID (CHAR(36)) | FK → users.id, NOT NULL, ON DELETE RESTRICT | Author / owner user ID |
| current_version_id | UUID (CHAR(36)) | FK → course_versions.id, NULLABLE, ON DELETE SET NULL | Pointer to current active published version |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Aggregate creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update timestamp |

#### `course_skills`
| Column | Type | Constraints | Description |
|---|---|---|---|
| course_id | UUID (CHAR(36)) | FK → courses.id, NOT NULL, ON DELETE CASCADE | Parent course |
| skill_id | UUID (CHAR(36)) | FK → skills.id, NOT NULL, ON DELETE CASCADE | Mapped skill taught |
| is_primary | BOOLEAN | NOT NULL, DEFAULT false | Whether this is the primary skill taught |
| | | PK(course_id, skill_id) | Composite primary key |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Association timestamp |

#### `course_versions`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID (CHAR(36)) | PK | Version snapshot identifier |
| course_id | UUID (CHAR(36)) | FK → courses.id, NOT NULL, ON DELETE CASCADE | Parent course aggregate |
| version_number | INTEGER | NOT NULL | 0 for mutable draft; 1, 2, 3... for immutable published |
| title | VARCHAR(300) | NOT NULL | Version-specific course title |
| description | TEXT | NULLABLE | Version-specific description |
| learning_objectives | JSON / JSONB | NOT NULL, DEFAULT '[]' | List of measurable learning outcomes |
| published_at | TIMESTAMPTZ | NULLABLE | Timestamp when published (NULL = working draft) |
| publisher_id | UUID (CHAR(36)) | FK → users.id, NULLABLE, ON DELETE SET NULL | User who published this version |
| changelog | TEXT | NULLABLE | Release notes / changelog for this version |
| is_active | BOOLEAN | NOT NULL, DEFAULT false | Whether this is the active published version |
| | | UNIQUE(course_id, version_number) | Unique version numbers per course |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Version snapshot creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update timestamp |

*Immutability Rule:* When `published_at` is set, the `CourseVersion` and all child `Module`, `Lesson`, and `LessonBlock` records become strictly immutable. Modifications are rejected with 409 Conflict. Further edits occur on an isolated cloned draft (`version_number = 0`).

#### `modules`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID (CHAR(36)) | PK | Module identifier |
| course_version_id | UUID (CHAR(36)) | FK → course_versions.id, NOT NULL, ON DELETE CASCADE | Parent course version snapshot |
| title | VARCHAR(300) | NOT NULL | Module title |
| description | TEXT | NULLABLE | Module description |
| sort_order | INTEGER | NOT NULL | Deterministic sequence order |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update timestamp |

#### `lessons`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID (CHAR(36)) | PK | Lesson unit identifier |
| module_id | UUID (CHAR(36)) | FK → modules.id, NOT NULL, ON DELETE CASCADE | Parent module |
| slug | VARCHAR(200) | NOT NULL | Unique lesson slug within module |
| title | VARCHAR(300) | NOT NULL | Lesson title |
| description | TEXT | NULLABLE | Lesson summary |
| learning_objectives | JSON / JSONB | NOT NULL, DEFAULT '[]' | Lesson-level learning outcomes |
| estimated_minutes | INTEGER | NULLABLE | Estimated completion time in minutes |
| sort_order | INTEGER | NOT NULL | Deterministic position in module |
| content_version | INTEGER | NOT NULL, DEFAULT 1 | Incrementing revision counter for content updates |
| | | UNIQUE(module_id, slug) | Unique slug per parent module |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update timestamp |

#### `lesson_blocks`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID (CHAR(36)) | PK | Block identifier |
| lesson_id | UUID (CHAR(36)) | FK → lessons.id, NOT NULL, ON DELETE CASCADE | Parent lesson |
| block_type | VARCHAR(50) | NOT NULL | Validated block type ('heading','text','list','code_example','callout','image','video') |
| content | JSON / JSONB | NOT NULL | Validated, sanitized block-specific payload |
| sort_order | INTEGER | NOT NULL | Block sequence within lesson |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Block creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update timestamp |

---

### Activities and Assessment

#### `activities`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID (CHAR(36)) | PK | Unique activity identifier |
| lesson_id | UUID (CHAR(36)) | FK → lessons.id, NULLABLE, ON DELETE CASCADE | Associated lesson (indexed) |
| activity_type | VARCHAR(50) | NOT NULL | Type: `single_choice`, `multiple_select`, `short_answer`, `true_false`, `fill_in_the_blank`, `ordering`, `matching`, `code_exercise`, `scenario` |
| title | VARCHAR(300) | NOT NULL | Activity display title |
| instructions | TEXT | NOT NULL | Task instructions and learner prompt |
| configuration | JSON / JSONB | NOT NULL, DEFAULT '{}' | Sanitized public configuration (options, items, statements, starter code) |
| max_attempts | INTEGER | NULLABLE | Max allowed submissions (NULL = unlimited) |
| sort_order | INTEGER | NOT NULL, DEFAULT 0 | Sorting order within lesson |
| is_active | BOOLEAN | NOT NULL, DEFAULT true | Active flag for soft deletion/archival |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Activity creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update timestamp |

#### `grading_configs`
| Column | Type | Constraints | Description |
|---|---|---|---|
| activity_id | UUID (CHAR(36)) | PK, FK → activities.id, ON DELETE CASCADE | One-to-one with parent activity |
| grading_type | VARCHAR(50) | NOT NULL, DEFAULT 'automated' | `automated`, `ai_assisted`, `rubric`, `completion` |
| passing_score | FLOAT | NOT NULL, DEFAULT 70.0 | Passing threshold percentage (0.0–100.0) |
| answer_key | JSON / JSONB | NOT NULL, DEFAULT '{}' | **Confidential server-authoritative key** (never exposed in public API) |
| rubric | JSON / JSONB | NULLABLE | Criteria definitions for subjective/manual review |
| test_cases | JSON / JSONB | NULLABLE | Sandbox test cases for code execution |
| feedback_config | JSON / JSONB | NULLABLE | Explanations, hints, and feedback messages |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Configuration creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update timestamp |

---

### Enrollment and Progress (Phase 6 Implemented)

#### `enrollments`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID (CHAR(36)) | PK | Unique enrollment identifier |
| user_id | UUID (CHAR(36)) | FK → users.id, NOT NULL, ON DELETE CASCADE | Enrolled learner (indexed) |
| course_id | UUID (CHAR(36)) | FK → courses.id, NOT NULL, ON DELETE CASCADE | Associated course aggregate (indexed) |
| course_version_id | UUID (CHAR(36)) | FK → course_versions.id, NOT NULL, ON DELETE CASCADE | Immutable published course version snapshot (indexed) |
| status | ENUM('ENROLLED','IN_PROGRESS','COMPLETED','DROPPED') | NOT NULL, DEFAULT 'ENROLLED' | Active enrollment lifecycle state |
| enrolled_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Enrollment creation timestamp |
| last_accessed_at | TIMESTAMPTZ | NULLABLE | Most recent lesson access timestamp |
| completed_at | TIMESTAMPTZ | NULLABLE | Course completion timestamp |
| | | UNIQUE(user_id, course_id) | One active enrollment per user per course |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Record creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update timestamp |

#### `lesson_progress`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID (CHAR(36)) | PK | Progress record identifier |
| enrollment_id | UUID (CHAR(36)) | FK → enrollments.id, NOT NULL, ON DELETE CASCADE | Parent course enrollment (indexed) |
| lesson_id | UUID (CHAR(36)) | FK → lessons.id, NOT NULL, ON DELETE CASCADE | Target lesson (indexed) |
| status | ENUM('NOT_STARTED','IN_PROGRESS','COMPLETED') | NOT NULL, DEFAULT 'NOT_STARTED' | Lesson progress status |
| started_at | TIMESTAMPTZ | NULLABLE | First access timestamp |
| completed_at | TIMESTAMPTZ | NULLABLE | Completion timestamp (gated by activity pass) |
| last_accessed_at | TIMESTAMPTZ | NULLABLE | Most recent visit timestamp |
| | | UNIQUE(enrollment_id, lesson_id) | Unique progress record per lesson per enrollment |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Record creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update timestamp |

#### `attempts`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID (CHAR(36)) | PK | Unique attempt identifier |
| user_id | UUID (CHAR(36)) | FK → users.id, NOT NULL, ON DELETE CASCADE | Submitting learner (indexed) |
| activity_id | UUID (CHAR(36)) | FK → activities.id, NOT NULL, ON DELETE CASCADE | Target activity (indexed) |
| attempt_number | INTEGER | NOT NULL | Sequential attempt counter (1, 2, ...) |
| status | VARCHAR(50) | NOT NULL, DEFAULT 'graded' | `in_progress`, `submitted`, `graded`, `review_required` |
| submission | JSON / JSONB | NOT NULL, DEFAULT '{}' | Untrusted learner submission payload |
| result | JSON / JSONB | NULLABLE | Server-calculated evaluation result |
| score | FLOAT | NULLABLE | Score achieved percentage (0.0–100.0) |
| max_score | FLOAT | NOT NULL, DEFAULT 100.0 | Maximum potential score |
| passed | BOOLEAN | NULLABLE | Pass threshold achievement status |
| feedback | JSON / JSONB | NULLABLE | Server-authoritative learner feedback & breakdown |
| started_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Attempt start timestamp |
| completed_at | TIMESTAMPTZ | NULLABLE | Evaluation completion timestamp |
| | | UNIQUE(user_id, activity_id, attempt_number) | Strict sequential attempt uniqueness |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Record creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update timestamp |

---

### Skill Mastery and Achievements (Phase 6 Implemented)

#### `skill_mastery`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID (CHAR(36)) | PK | Record identifier |
| user_id | UUID (CHAR(36)) | FK → users.id, NOT NULL, ON DELETE CASCADE | Evaluated learner (indexed) |
| skill_id | UUID (CHAR(36)) | FK → skills.id, NOT NULL, ON DELETE CASCADE | Target taxonomy skill (indexed) |
| mastery_score | FLOAT | NOT NULL, DEFAULT 0.0 | Average evaluation score (0.0–100.0) |
| status | ENUM('NOT_STARTED','LEARNING','PRACTICING','PROVISIONAL','MASTERED','NEEDS_REVIEW') | NOT NULL, DEFAULT 'NOT_STARTED' | Evidence-backed mastery tier |
| evidence_count | INTEGER | NOT NULL, DEFAULT 0 | Count of passed assessment attempts |
| evidence_data | JSON / JSONB | NOT NULL, DEFAULT '[]' | Verified evidence history array (attempt IDs, scores, dates) |
| last_evaluated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last mastery calculation timestamp |
| | | UNIQUE(user_id, skill_id) | One mastery record per user per skill |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Record creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update timestamp |

#### `achievements`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID (CHAR(36)) | PK | Unique achievement identifier |
| slug | VARCHAR(100) | UNIQUE, NOT NULL | Deterministic achievement key (e.g. `first_lesson`) |
| title | VARCHAR(200) | NOT NULL | Display name |
| description | TEXT | NOT NULL | Learner unlock description |
| icon | VARCHAR(100) | NULLABLE | Lucide icon identifier |
| criteria_type | VARCHAR(50) | NOT NULL | Criterion category (`LESSONS_COMPLETED`, `COURSES_COMPLETED`, `PERFECT_SCORE`, `SKILLS_MASTERED`) |
| criteria_threshold | INTEGER | NOT NULL, DEFAULT 1 | Numeric target required for unlock |
| criteria_data | JSON / JSONB | NOT NULL, DEFAULT '{}' | Additional unlock specifications |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Record creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update timestamp |

#### `user_achievements`
| Column | Type | Constraints | Description |
|---|---|---|---|
| user_id | UUID (CHAR(36)) | FK → users.id, NOT NULL, ON DELETE CASCADE | Recipient learner |
| achievement_id | UUID (CHAR(36)) | FK → achievements.id, NOT NULL, ON DELETE CASCADE | Unlocked achievement |
| earned_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Timestamp when unlock was granted |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Record creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update timestamp |
| | | PK(user_id, achievement_id) | Idempotent composite primary key |

---

### Projects and Portfolio

#### `projects`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | Project identifier |
| course_version_id | UUID | FK → course_versions.id, NOT NULL | Associated course |
| title | VARCHAR(300) | NOT NULL | Project title |
| description | TEXT | NOT NULL | Project brief |
| requirements | JSONB | NOT NULL | Structured requirements and milestones |
| evaluation_criteria | JSONB | NOT NULL | How the project is evaluated |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

#### `project_submissions`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | Submission identifier |
| project_id | UUID | FK → projects.id, NOT NULL | Target project |
| user_id | UUID | FK → users.id, NOT NULL | Submitting learner |
| content | JSONB | NOT NULL | Submission content/files references |
| status | ENUM('draft','submitted','evaluated','published') | NOT NULL, DEFAULT 'draft' | |
| evaluation | JSONB | NULLABLE | Evaluation results and feedback |
| score | DECIMAL(5,2) | NULLABLE | Score if applicable |
| submitted_at | TIMESTAMPTZ | NULLABLE | |
| evaluated_at | TIMESTAMPTZ | NULLABLE | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

#### `portfolios`
| Column | Type | Constraints | Description |
|---|---|---|---|
| user_id | UUID | PK, FK → users.id | One portfolio per user |
| is_public | BOOLEAN | NOT NULL, DEFAULT false | Whether portfolio is publicly accessible |
| custom_slug | VARCHAR(100) | UNIQUE, NULLABLE | Custom URL slug |
| bio_override | TEXT | NULLABLE | Portfolio-specific bio |
| settings | JSONB | NOT NULL, DEFAULT '{}' | Display settings |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Portfolio creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update timestamp |

#### `portfolio_items`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | Item identifier |
| user_id | UUID | FK → portfolios.user_id, NOT NULL | Portfolio owner |
| item_type | VARCHAR(50) | NOT NULL | 'project_submission', 'achievement', 'skill_mastery' |
| reference_id | UUID | NOT NULL | ID of the referenced item |
| sort_order | INTEGER | NOT NULL | Display order |
| is_visible | BOOLEAN | NOT NULL, DEFAULT true | Whether to show in public portfolio |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Item creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update timestamp |

---

### Course Creation and Review

#### `course_reviews`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | Review record identifier |
| course_version_id | UUID | FK → course_versions.id, NOT NULL | Version under review |
| reviewer_id | UUID | FK → users.id, NOT NULL | Reviewing admin/editor |
| status | ENUM('pending','approved','rejected','needs_changes') | NOT NULL | Review outcome |
| comments | TEXT | NULLABLE | Reviewer comments |
| reviewed_at | TIMESTAMPTZ | NULLABLE | Review completion |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Review record creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update timestamp |

---

### AI and Audit

#### `ai_interactions`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | Interaction identifier |
| user_id | UUID | FK → users.id, NOT NULL | User who triggered AI |
| interaction_type | VARCHAR(50) | NOT NULL | 'tutor_question', 'feedback_request', 'recommendation' |
| context | JSONB | NOT NULL | Lesson/activity context sent to AI |
| prompt | TEXT | NOT NULL | Prompt sent to AI provider |
| response | TEXT | NULLABLE | AI response received |
| provider | VARCHAR(50) | NOT NULL | AI provider used |
| model | VARCHAR(100) | NOT NULL | Model identifier |
| tokens_used | INTEGER | NULLABLE | Total tokens consumed |
| latency_ms | INTEGER | NULLABLE | Response time |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

#### `audit_events`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | Event identifier |
| user_id | UUID | FK → users.id, NULLABLE | Actor (null for system events) |
| event_type | VARCHAR(100) | NOT NULL | e.g., 'user.login', 'course.published', 'code.executed' |
| resource_type | VARCHAR(50) | NULLABLE | e.g., 'course', 'attempt', 'user' |
| resource_id | UUID | NULLABLE | ID of affected resource |
| metadata | JSONB | NOT NULL, DEFAULT '{}' | Additional event data |
| ip_address | INET | NULLABLE | Client IP |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Event timestamp |

**Index:** `audit_events(event_type, created_at)`, `audit_events(user_id, created_at)`

---

## Key Indexes (Planned)

| Table | Index | Purpose |
|---|---|---|
| users | email | Login lookup |
| courses | slug | URL routing |
| courses | skill_id | Skill-based discovery |
| lessons | module_id, sort_order | Lesson ordering |
| lesson_blocks | lesson_id, sort_order | Block rendering |
| activities | lesson_id, sort_order | Activity ordering |
| enrollments | user_id | User's courses |
| lesson_progress | enrollment_id | Progress queries |
| attempts | user_id, activity_id | Attempt history |
| skill_mastery | user_id | Dashboard queries |
| audit_events | user_id, created_at | User audit trail |
| audit_events | event_type, created_at | Event analysis |

---

## Foreign Key Cascade Rules

The following cascade behaviors apply to foreign key relationships:

| Parent Table | Child Table | On Delete Behavior | Rationale |
|---|---|---|---|
| users (soft delete) | user_profiles, enrollments, lesson_progress, attempts, skill_mastery, user_achievements, portfolios | No cascade (all records retained) | User data retained during 30-day soft-delete grace period. Auth middleware denies access while `deleted_at IS NOT NULL`. |
| users (hard delete post-grace) | user_profiles, oauth_accounts, refresh_tokens, portfolios, portfolio_items | CASCADE | Identity, authentication credentials, and personal portfolio data are permanently purged. |
| users (hard delete post-grace) | enrollments, lesson_progress, attempts, skill_mastery, user_achievements, project_submissions | Anonymize (SET user_id to NULL or reassign to sentinel anonymous UUID) | Preserves course completion percentages, pass rates, grading statistics, and platform analytics without retaining PII. |
| courses | course_versions | RESTRICT | Cannot delete a course that has published versions or draft records. Course must be marked 'archived'. |
| course_versions (with enrollments) | enrollments | RESTRICT | A course version with active or historical enrollments cannot be deleted; it must be deactivated (`is_active = false`) to protect learner history. |
| course_versions (draft / no enrollments) | modules | CASCADE | Version content is a single atomic unit. |
| modules | lessons | CASCADE | Module content is a single unit. |
| lessons | lesson_blocks | CASCADE | Lesson content blocks belong to their lesson. |
| lessons | activities | CASCADE | Activities belong to their parent lesson. |
| activities | grading_configs | CASCADE | Grading configuration is part of the activity. |
| activities | attempts | RESTRICT | Cannot delete an activity with existing learner attempts (activity must be archived/deactivated). |
| projects | project_submissions | RESTRICT | Cannot delete a project that has learner submissions. |

**Rule:** Cascade deletes only flow downward through draft/unreferenced content hierarchies (`course_version` → `module` → `lesson` → `block`/`activity` → `grading_config`). Learner records and published learning histories are never cascade-deleted; they are either soft-deleted, anonymized or protected by RESTRICT constraints.

---

## Migration Strategy

- All schema changes are managed through **Alembic** migrations.
- Migrations are version-controlled and reviewed before application.
- Destructive changes (column drops, table drops) require explicit approval and a data migration plan.
- Each phase adds only the tables it needs. The full schema above is the target, not the initial state.

### Phase-by-Phase Table Introduction

| Phase | Tables Added |
|---|---|
| Phase 2 | users, user_profiles, oauth_accounts, refresh_tokens |
| Phase 3 | skills, skill_prerequisites, courses, course_versions, modules, lessons, lesson_blocks, enrollments, lesson_progress |
| Phase 5 | activities, grading_configs, attempts |
| Phase 6 | skill_mastery, achievements, user_achievements |
| Phase 7 | course_reviews |
| Phase 8 | ai_interactions |
| Phase 9 | projects, project_submissions, portfolios, portfolio_items |
| All phases | audit_events (extended incrementally) |

> **Note:** `enrollments` and `lesson_progress` are introduced in Phase 3 because the enrollment API and module-sidebar progress indicators are Phase 3 deliverables. Skill mastery and achievements remain in Phase 6, where the progression engine is fully built.
