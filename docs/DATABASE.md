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

#### `skills`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | Skill identifier |
| slug | VARCHAR(100) | UNIQUE, NOT NULL | URL-friendly identifier |
| name | VARCHAR(200) | NOT NULL | Human-readable name |
| description | TEXT | NULLABLE | Skill description |
| category | VARCHAR(100) | NOT NULL | Top-level category (e.g., 'programming', 'communication') |
| icon | VARCHAR(100) | NULLABLE | Icon identifier for skill map |
| sort_order | INTEGER | NOT NULL, DEFAULT 0 | Display ordering |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

#### `skill_prerequisites`
| Column | Type | Constraints | Description |
|---|---|---|---|
| skill_id | UUID | FK → skills.id, NOT NULL | The skill that has a prerequisite |
| prerequisite_skill_id | UUID | FK → skills.id, NOT NULL | The required skill |
| | | PK(skill_id, prerequisite_skill_id) | Composite primary key |
| | | CHECK(skill_id ≠ prerequisite_skill_id) | No self-reference |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Link timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update timestamp |

---

### Courses and Content

#### `courses`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | Course identifier |
| slug | VARCHAR(200) | UNIQUE, NOT NULL | URL-friendly identifier |
| title | VARCHAR(300) | NOT NULL | Course title |
| description | TEXT | NULLABLE | Short description |
| cover_image_url | TEXT | NULLABLE | Cover image |
| skill_id | UUID | FK → skills.id, NULLABLE | Primary skill taught |
| creator_id | UUID | FK → users.id, NOT NULL | Course creator |
| status | ENUM('draft','review','published','archived') | NOT NULL, DEFAULT 'draft' | Publication status |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

#### `course_versions`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | Version identifier |
| course_id | UUID | FK → courses.id, NOT NULL | Parent course |
| version_number | INTEGER | NOT NULL | Incrementing version |
| published_at | TIMESTAMPTZ | NULLABLE | When this version went live |
| changelog | TEXT | NULLABLE | Description of changes |
| is_active | BOOLEAN | NOT NULL, DEFAULT false | Currently active version |
| | | UNIQUE(course_id, version_number) | One version number per course |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

#### `modules`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | Module identifier |
| course_version_id | UUID | FK → course_versions.id, NOT NULL | Parent course version |
| title | VARCHAR(300) | NOT NULL | Module title |
| description | TEXT | NULLABLE | Module description |
| sort_order | INTEGER | NOT NULL | Order within course |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

#### `lessons`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | Lesson identifier |
| module_id | UUID | FK → modules.id, NOT NULL | Parent module |
| slug | VARCHAR(200) | NOT NULL | URL-friendly identifier |
| title | VARCHAR(300) | NOT NULL | Lesson title |
| description | TEXT | NULLABLE | Lesson summary |
| estimated_minutes | INTEGER | NULLABLE | Estimated time to complete |
| sort_order | INTEGER | NOT NULL | Order within module |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

#### `lesson_blocks`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | Block identifier |
| lesson_id | UUID | FK → lessons.id, NOT NULL | Parent lesson |
| block_type | VARCHAR(50) | NOT NULL | 'text', 'code_example', 'media', 'activity_ref', 'callout' |
| content | JSONB | NOT NULL | Block content (structure depends on block_type) |
| sort_order | INTEGER | NOT NULL | Order within lesson |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

---

### Activities and Assessment

#### `activities`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | Activity identifier |
| lesson_id | UUID | FK → lessons.id, NOT NULL | Parent lesson |
| activity_type | VARCHAR(50) | NOT NULL | 'code_exercise', 'quiz', 'conversation', 'practical_task' |
| title | VARCHAR(300) | NOT NULL | Activity title |
| instructions | TEXT | NOT NULL | Activity instructions (markdown) |
| configuration | JSONB | NOT NULL | Type-specific config (starter code, test cases, rubric, etc.) |
| max_attempts | INTEGER | NULLABLE | NULL = unlimited |
| sort_order | INTEGER | NOT NULL | Order within lesson |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

#### `grading_configs`
| Column | Type | Constraints | Description |
|---|---|---|---|
| activity_id | UUID | PK, FK → activities.id | One-to-one with activity |
| grading_type | VARCHAR(50) | NOT NULL | 'automated', 'ai_assisted', 'rubric', 'completion' |
| passing_score | DECIMAL(5,2) | NOT NULL, DEFAULT 70.00 | Minimum score to pass (%) |
| rubric | JSONB | NULLABLE | Evaluation rubric for AI/manual grading |
| test_cases | JSONB | NULLABLE | Automated test definitions |
| feedback_config | JSONB | NULLABLE | Hint levels, feedback templates |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Configuration creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update timestamp |

---

### Enrollment and Progress

#### `enrollments`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | Enrollment identifier |
| user_id | UUID | FK → users.id, NOT NULL | Enrolled learner |
| course_version_id | UUID | FK → course_versions.id, NOT NULL | Enrolled course version |
| enrolled_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Enrollment timestamp |
| completed_at | TIMESTAMPTZ | NULLABLE | Completion timestamp |
| | | UNIQUE(user_id, course_version_id) | One enrollment per version |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Record creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update timestamp |

#### `lesson_progress`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | Progress record identifier |
| enrollment_id | UUID | FK → enrollments.id, NOT NULL | Parent enrollment |
| lesson_id | UUID | FK → lessons.id, NOT NULL | The lesson |
| status | ENUM('not_started','in_progress','completed') | NOT NULL, DEFAULT 'not_started' | |
| started_at | TIMESTAMPTZ | NULLABLE | First visit timestamp |
| completed_at | TIMESTAMPTZ | NULLABLE | Completion timestamp |
| | | UNIQUE(enrollment_id, lesson_id) | One progress per lesson per enrollment |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Record creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update timestamp |

#### `attempts`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | Attempt identifier |
| user_id | UUID | FK → users.id, NOT NULL | Attempting learner |
| activity_id | UUID | FK → activities.id, NOT NULL | Target activity |
| attempt_number | INTEGER | NOT NULL | Sequential attempt number |
| submission | JSONB | NOT NULL | What the learner submitted |
| result | JSONB | NULLABLE | Evaluation result (null = pending) |
| score | DECIMAL(5,2) | NULLABLE | Score achieved (%) |
| passed | BOOLEAN | NULLABLE | Whether passing threshold met |
| feedback | JSONB | NULLABLE | Structured feedback |
| started_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| completed_at | TIMESTAMPTZ | NULLABLE | |
| | | UNIQUE(user_id, activity_id, attempt_number) | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Record creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update timestamp |

---

### Skill Mastery and Achievements

#### `skill_mastery`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | Record identifier |
| user_id | UUID | FK → users.id, NOT NULL | Learner |
| skill_id | UUID | FK → skills.id, NOT NULL | Skill |
| mastery_level | DECIMAL(5,2) | NOT NULL, DEFAULT 0.00 | Mastery percentage (0–100) |
| evidence | JSONB | NOT NULL, DEFAULT '[]' | Array of evidence (activity IDs, scores, dates) |
| last_assessed_at | TIMESTAMPTZ | NULLABLE | Last mastery update |
| | | UNIQUE(user_id, skill_id) | One record per user per skill |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Record creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update timestamp |

#### `achievements`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | Achievement definition identifier |
| slug | VARCHAR(100) | UNIQUE, NOT NULL | Unique identifier |
| name | VARCHAR(200) | NOT NULL | Display name |
| description | TEXT | NOT NULL | What the learner did to earn this |
| icon | VARCHAR(100) | NULLABLE | Badge icon identifier |
| criteria | JSONB | NOT NULL | Machine-readable unlock conditions |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Definition creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update timestamp |

#### `user_achievements`
| Column | Type | Constraints | Description |
|---|---|---|---|
| user_id | UUID | FK → users.id, NOT NULL | Learner |
| achievement_id | UUID | FK → achievements.id, NOT NULL | Earned achievement |
| earned_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | When earned |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Record creation timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update timestamp |
| | | PK(user_id, achievement_id) | |

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
