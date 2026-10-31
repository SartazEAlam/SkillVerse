"""Business logic service for enrollments, progression cascade, skill mastery, and achievements."""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.modules.activities.models import Activity, Attempt
from app.modules.courses.models import (
    Course,
    CourseSkill,
    CourseStatus,
    CourseVersion,
    Lesson,
    Module,
)
from app.modules.progress.models import (
    Achievement,
    Enrollment,
    EnrollmentStatus,
    LessonProgress,
    LessonProgressStatus,
    SkillMastery,
    SkillMasteryStatus,
    UserAchievement,
)
from app.modules.progress.schemas import (
    AchievementResponse,
    CoursePrerequisitesResponse,
    DashboardSummaryResponse,
    EnrollmentResponse,
    LessonCompleteResponse,
    LessonProgressResponse,
    PrerequisiteStatusItem,
    RecentAttemptItem,
    RecommendationItem,
    ResumeLearningItem,
    SkillEvidenceItem,
    SkillMasteryResponse,
)
from app.modules.skills.models import Skill, SkillPrerequisite

logger = logging.getLogger("skillverse.progress")


class ProgressionServiceError(Exception):
    """Domain exception raised by ProgressionService."""

    def __init__(self, message: str, code: str = "PROGRESSION_ERROR", status_code: int = 400, details: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class ProgressionService:
    """Orchestrates enrollments, lesson progress, mastery calculations, and achievement evaluations."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── 1. Course Enrollments ──────────────────────────────────────────────────

    def enroll_user(self, user_id: str, course_slug: str) -> EnrollmentResponse:
        """Enroll the authenticated user in the current active version of a course."""
        course = self.db.scalars(
            select(Course)
            .options(joinedload(Course.current_version), joinedload(Course.discipline))
            .where(Course.slug == course_slug, Course.status == CourseStatus.PUBLISHED)
        ).first()

        if not course:
            raise ProgressionServiceError(
                f"Course '{course_slug}' is not published or unavailable.",
                code="COURSE_NOT_AVAILABLE",
                status_code=404,
            )

        if not course.current_version_id or not course.current_version:
            raise ProgressionServiceError(
                f"Course '{course_slug}' has no published version available.",
                code="NO_PUBLISHED_VERSION",
                status_code=400,
            )

        # Check course prerequisites
        prereq_check = self.check_course_prerequisites(user_id=user_id, course_slug=course_slug)
        if not prereq_check.eligible:
            raise ProgressionServiceError(
                f"Prerequisites for '{course.title}' are not yet satisfied: {', '.join(prereq_check.unmet_prerequisites)}",
                code="PREREQUISITE_NOT_MET",
                status_code=400,
                details={"unmet_prerequisites": prereq_check.unmet_prerequisites},
            )

        # Idempotency check: Return existing enrollment if already active
        existing = self.db.scalars(
            select(Enrollment)
            .options(joinedload(Enrollment.course), joinedload(Enrollment.course_version))
            .where(Enrollment.user_id == user_id, Enrollment.course_id == course.id)
        ).first()

        if existing:
            return self._format_enrollment_response(existing)

        now = datetime.now(UTC)
        enrollment = Enrollment(
            user_id=user_id,
            course_id=course.id,
            course_version_id=course.current_version_id,
            status=EnrollmentStatus.ENROLLED.value,
            enrolled_at=now,
            last_accessed_at=now,
        )
        self.db.add(enrollment)

        try:
            self.db.commit()
            self.db.refresh(enrollment)
        except IntegrityError:
            self.db.rollback()
            # Concurrently created enrollment
            existing = self.db.scalars(
                select(Enrollment)
                .options(joinedload(Enrollment.course), joinedload(Enrollment.course_version))
                .where(Enrollment.user_id == user_id, Enrollment.course_id == course.id)
            ).first()
            if existing:
                return self._format_enrollment_response(existing)
            raise ProgressionServiceError(
                "Failed to complete enrollment due to a concurrency conflict. Please refresh.",
                code="ENROLLMENT_CONFLICT",
                status_code=409,
            )

        # Update skill mastery status for skills taught by this course to LEARNING (if NOT_STARTED)
        self._initialize_course_skills_learning(user_id, course.id)

        # Evaluate potential achievements (e.g., polymath across multiple disciplines)
        self.evaluate_achievements(user_id)

        return self._format_enrollment_response(enrollment)

    def reconcile_enrollment_progress(self, enrollment_id: str) -> bool:
        """Reconcile and recover lesson/course progress from passed attempts if a progression cascade was interrupted."""
        enrollment = self.db.get(Enrollment, enrollment_id)
        if not enrollment:
            return False

        modules = self.db.scalars(
            select(Module)
            .options(joinedload(Module.lessons).joinedload(Lesson.activities))
            .where(Module.course_version_id == enrollment.course_version_id)
            .order_by(Module.sort_order)
        ).unique().all()

        now = datetime.now(UTC)
        any_updated = False

        for mod in modules:
            for les in mod.lessons:
                active_acts = [act for act in les.activities if act.is_active]
                if not active_acts:
                    continue

                all_passed = True
                for act in active_acts:
                    passed_cnt = self.db.scalar(
                        select(func.count(Attempt.id)).where(
                            Attempt.activity_id == act.id,
                            Attempt.user_id == enrollment.user_id,
                            Attempt.passed.is_(True),
                        )
                    )
                    if not passed_cnt or passed_cnt == 0:
                        all_passed = False
                        break

                if all_passed:
                    prog = self.db.scalars(
                        select(LessonProgress).where(
                            LessonProgress.enrollment_id == enrollment.id,
                            LessonProgress.lesson_id == les.id,
                        )
                    ).first()

                    if not prog:
                        prog = LessonProgress(
                            enrollment_id=enrollment.id,
                            user_id=enrollment.user_id,
                            lesson_id=les.id,
                            status=LessonProgressStatus.COMPLETED.value,
                            started_at=now,
                            completed_at=now,
                            last_accessed_at=now,
                        )
                        self.db.add(prog)
                        any_updated = True
                    elif prog.status != LessonProgressStatus.COMPLETED.value:
                        prog.status = LessonProgressStatus.COMPLETED.value
                        prog.completed_at = prog.completed_at or now
                        prog.last_accessed_at = now
                        any_updated = True

        if any_updated:
            self.db.flush()
            self._check_and_update_course_completion(enrollment, now)
            self.db.commit()
            self._recalculate_course_skills(enrollment.user_id, enrollment.course_id)
            self.evaluate_achievements(enrollment.user_id)

        return any_updated

    def get_user_enrollments(self, user_id: str) -> list[EnrollmentResponse]:
        """List all active enrollments for a learner with computed progress percentages."""
        enrollments = self.db.scalars(
            select(Enrollment)
            .options(joinedload(Enrollment.course), joinedload(Enrollment.course_version))
            .where(Enrollment.user_id == user_id)
            .order_by(Enrollment.last_accessed_at.desc())
        ).all()

        for e in enrollments:
            self.reconcile_enrollment_progress(e.id)

        return [self._format_enrollment_response(e) for e in enrollments]

    def get_enrollment_by_id(self, enrollment_id: str, user_id: str) -> EnrollmentResponse:
        """Fetch details of a single enrollment ensuring ownership authorization."""
        enrollment = self.db.scalars(
            select(Enrollment)
            .options(joinedload(Enrollment.course), joinedload(Enrollment.course_version))
            .where(Enrollment.id == enrollment_id)
        ).first()

        if not enrollment:
            raise ProgressionServiceError(
                f"Enrollment '{enrollment_id}' not found.",
                code="ENROLLMENT_NOT_FOUND",
                status_code=404,
            )

        if enrollment.user_id != user_id:
            raise ProgressionServiceError(
                "Forbidden: You do not have permission to access another learner's enrollment.",
                code="FORBIDDEN",
                status_code=403,
            )

        self.reconcile_enrollment_progress(enrollment.id)
        return self._format_enrollment_response(enrollment)

    def get_enrollment_for_course(self, user_id: str, course_id: str) -> Enrollment | None:
        """Fetch enrollment record for a given user and course."""
        return self.db.scalars(
            select(Enrollment)
            .options(joinedload(Enrollment.course), joinedload(Enrollment.course_version))
            .where(Enrollment.user_id == user_id, Enrollment.course_id == course_id)
        ).first()

    # ── 2. Lesson Progress Tracking ──────────────────────────────────────────

    def start_lesson(self, user_id: str, enrollment_id: str, lesson_id: str) -> LessonProgressResponse:
        """Record that a learner has opened and begun interacting with a lesson."""
        enrollment = self._get_verified_enrollment(enrollment_id, user_id)
        lesson = self._get_verified_lesson(lesson_id, enrollment.course_version_id)

        # Reconcile any prior completed activity progression
        self.reconcile_enrollment_progress(enrollment.id)

        now = datetime.now(UTC)

        # Update enrollment activity and status
        enrollment.last_accessed_at = now
        if enrollment.status == EnrollmentStatus.ENROLLED.value:
            enrollment.status = EnrollmentStatus.IN_PROGRESS.value

        # Fetch or create lesson progress
        progress = self.db.scalars(
            select(LessonProgress).where(
                LessonProgress.enrollment_id == enrollment.id,
                LessonProgress.lesson_id == lesson.id,
            )
        ).first()

        if not progress:
            progress = LessonProgress(
                enrollment_id=enrollment.id,
                user_id=user_id,
                lesson_id=lesson.id,
                status=LessonProgressStatus.IN_PROGRESS.value,
                started_at=now,
                last_accessed_at=now,
            )
            self.db.add(progress)
        else:
            progress.last_accessed_at = now
            if progress.status == LessonProgressStatus.NOT_STARTED.value:
                progress.status = LessonProgressStatus.IN_PROGRESS.value
                progress.started_at = progress.started_at or now

        self.db.commit()
        self.db.refresh(progress)

        return self._format_lesson_progress_response(progress, lesson, user_id)

    def complete_lesson(self, user_id: str, enrollment_id: str, lesson_id: str) -> LessonCompleteResponse:
        """Mark a lesson complete after verifying all required interactive activities are passed."""
        enrollment = self._get_verified_enrollment(enrollment_id, user_id)
        lesson = self._get_verified_lesson(lesson_id, enrollment.course_version_id)

        now = datetime.now(UTC)

        # Verify activity requirements
        activities = self.db.scalars(
            select(Activity).where(Activity.lesson_id == lesson.id, Activity.is_active.is_(True))
        ).all()

        if activities:
            # All activities in lesson must have at least one passed attempt
            for act in activities:
                has_passed = self.db.scalar(
                    select(func.count(Attempt.id)).where(
                        Attempt.activity_id == act.id,
                        Attempt.user_id == user_id,
                        Attempt.passed.is_(True),
                    )
                )
                if not has_passed or has_passed == 0:
                    raise ProgressionServiceError(
                        f"Cannot mark lesson '{lesson.title}' complete: Activity '{act.title}' requires a passing score.",
                        code="REQUIRED_ACTIVITIES_INCOMPLETE",
                        status_code=400,
                        details={"unpassed_activity_id": act.id, "unpassed_activity_title": act.title},
                    )

        # Update or create lesson progress
        progress = self.db.scalars(
            select(LessonProgress).where(
                LessonProgress.enrollment_id == enrollment.id,
                LessonProgress.lesson_id == lesson.id,
            )
        ).first()

        if not progress:
            progress = LessonProgress(
                enrollment_id=enrollment.id,
                user_id=user_id,
                lesson_id=lesson.id,
                status=LessonProgressStatus.COMPLETED.value,
                started_at=now,
                completed_at=now,
                last_accessed_at=now,
            )
            self.db.add(progress)
        else:
            progress.status = LessonProgressStatus.COMPLETED.value
            progress.completed_at = progress.completed_at or now
            progress.last_accessed_at = now

        # Update enrollment activity
        enrollment.last_accessed_at = now

        self.db.flush()

        # Check course completion cascade
        course_completed = self._check_and_update_course_completion(enrollment, now)

        self.db.commit()
        self.db.refresh(progress)

        # Recalculate skill mastery for skills taught by this course
        self._recalculate_course_skills(user_id, enrollment.course_id)

        # Evaluate newly unlocked achievements
        new_achievements = self.evaluate_achievements(user_id)

        return LessonCompleteResponse(
            lesson_progress=self._format_lesson_progress_response(progress, lesson, user_id),
            course_completed=course_completed,
            newly_earned_achievements=new_achievements,
            message="Lesson successfully completed!" if not course_completed else "Congratulations! You have completed the entire course!",
        )

    # ── 3. Assessment-Linked Progression Hook ──────────────────────────────────

    def handle_activity_completed(self, attempt: Attempt) -> None:
        """Webhook-like progression hook invoked when an activity attempt is successfully graded."""
        if not attempt.passed:
            return

        activity = self.db.get(Activity, attempt.activity_id)
        if not activity or not activity.lesson_id:
            return

        lesson = self.db.get(Lesson, activity.lesson_id)
        if not lesson:
            return

        # Find module and course version containing this lesson
        module = self.db.get(Module, lesson.module_id)
        if not module:
            return

        # Find user's enrollment for this course version
        enrollment = self.db.scalars(
            select(Enrollment).where(
                Enrollment.user_id == attempt.user_id,
                Enrollment.course_version_id == module.course_version_id,
            )
        ).first()

        if enrollment:
            if enrollment.status == EnrollmentStatus.ENROLLED.value:
                enrollment.status = EnrollmentStatus.IN_PROGRESS.value
            enrollment.last_accessed_at = datetime.now(UTC)

            # Check if all activities for this lesson are now passed
            lesson_activities = self.db.scalars(
                select(Activity).where(Activity.lesson_id == lesson.id, Activity.is_active.is_(True))
            ).all()

            all_passed = True
            for act in lesson_activities:
                passed_cnt = self.db.scalar(
                    select(func.count(Attempt.id)).where(
                        Attempt.activity_id == act.id,
                        Attempt.user_id == attempt.user_id,
                        Attempt.passed.is_(True),
                    )
                )
                if not passed_cnt or passed_cnt == 0:
                    all_passed = False
                    break

            if all_passed:
                # Auto-complete lesson progress
                now = datetime.now(UTC)
                progress = self.db.scalars(
                    select(LessonProgress).where(
                        LessonProgress.enrollment_id == enrollment.id,
                        LessonProgress.lesson_id == lesson.id,
                    )
                ).first()

                if not progress:
                    progress = LessonProgress(
                        enrollment_id=enrollment.id,
                        user_id=attempt.user_id,
                        lesson_id=lesson.id,
                        status=LessonProgressStatus.COMPLETED.value,
                        started_at=now,
                        completed_at=now,
                        last_accessed_at=now,
                    )
                    self.db.add(progress)
                else:
                    progress.status = LessonProgressStatus.COMPLETED.value
                    progress.completed_at = progress.completed_at or now
                    progress.last_accessed_at = now

                self.db.flush()
                self._check_and_update_course_completion(enrollment, now)
                self.db.commit()

        # Recalculate skill mastery for course skills
        course_ver = self.db.get(CourseVersion, module.course_version_id)
        if course_ver:
            self._recalculate_course_skills(attempt.user_id, course_ver.course_id)

        # Trigger achievement evaluation
        self.evaluate_achievements(attempt.user_id)

    # ── 4. Skill Mastery & Evidence Evaluation ─────────────────────────────────

    def get_user_skills_mastery(self, user_id: str) -> list[SkillMasteryResponse]:
        """Fetch mastery status and verified evidence history across all taxonomy skills."""
        skills = self.db.scalars(
            select(Skill)
            .options(joinedload(Skill.discipline), joinedload(Skill.prerequisite_edges))
            .where(Skill.is_active.is_(True))
            .order_by(Skill.sort_order)
        ).unique().all()

        mastery_records = {
            m.skill_id: m
            for m in self.db.scalars(select(SkillMastery).where(SkillMastery.user_id == user_id)).all()
        }

        results: list[SkillMasteryResponse] = []
        for skill in skills:
            record = mastery_records.get(skill.id)
            prereq_ids = [edge.prerequisite_skill_id for edge in skill.prerequisite_edges]
            prereq_names = [edge.prerequisite_skill.name for edge in skill.prerequisite_edges if edge.prerequisite_skill]

            # Check if prerequisites are satisfied
            is_unlocked = True
            for pid in prereq_ids:
                p_rec = mastery_records.get(pid)
                if not p_rec or p_rec.status not in (
                    SkillMasteryStatus.PROVISIONAL.value,
                    SkillMasteryStatus.MASTERED.value,
                ):
                    is_unlocked = False
                    break

            evidence_items: list[SkillEvidenceItem] = []
            if record and record.evidence:
                for item in record.evidence:
                    try:
                        assessed_dt = (
                            datetime.fromisoformat(item["assessed_at"])
                            if isinstance(item["assessed_at"], str)
                            else item["assessed_at"]
                        )
                        evidence_items.append(
                            SkillEvidenceItem(
                                activity_id=item["activity_id"],
                                activity_title=item.get("activity_title", "Assessment"),
                                activity_type=item.get("activity_type", "interactive"),
                                attempt_id=item["attempt_id"],
                                score=float(item.get("score", 0.0)),
                                passed=bool(item.get("passed", False)),
                                assessed_at=assessed_dt,
                                rule=item.get("rule", "verified_assessment"),
                            )
                        )
                    except Exception:
                        continue

            mastery_level = record.mastery_level if record else 0.0
            status = SkillMasteryStatus(record.status) if record else SkillMasteryStatus.NOT_STARTED

            results.append(
                SkillMasteryResponse(
                    skill_id=skill.id,
                    skill_slug=skill.slug,
                    skill_name=skill.name,
                    discipline_slug=skill.discipline.slug if skill.discipline else "",
                    discipline_name=skill.discipline.name if skill.discipline else "",
                    difficulty_level=skill.difficulty_level.value if hasattr(skill.difficulty_level, "value") else str(skill.difficulty_level),
                    mastery_level=mastery_level,
                    status=status,
                    evidence=evidence_items,
                    last_assessed_at=record.last_assessed_at if record else None,
                    prerequisites=prereq_names,
                    is_unlocked=is_unlocked,
                )
            )

        return results

    def _activity_assesses_skill(
        self,
        activity: Activity,
        skill: Skill,
        lesson: Lesson | None = None,
        module: Module | None = None,
        course_skill_ids: list[str] | None = None,
    ) -> bool:
        """Determine whether an activity assesses a specific skill based on established architecture.

        Rules:
        1. Explicit configuration match:
           - If activity.configuration has 'skill_id', matches iff cfg['skill_id'] == skill.id.
           - If activity.configuration has 'skill_slug' or 'skill', matches iff cfg['skill_slug'] == skill.slug.
           - If an explicit skill tag is present and does not match, returns False immediately.
        2. Single-skill course:
           - If the course teaches exactly one skill, all activities in that course assess that sole skill.
        3. Multi-skill course with safe structural correlation:
           - If no explicit skill tag was provided, check if the lesson or module uniquely identifies
             this skill through slug or title tokens (e.g. 'semantic-tags' lesson in 'HTML Structure and Semantics'
             module matches 'html-semantics').
        4. Safe default:
           - If the activity cannot be safely attributed to this specific skill, returns False.
           - Under no circumstances does an un-attributed activity get assigned to all course skills.
        """
        cfg = activity.configuration if isinstance(activity.configuration, dict) else {}

        # 1. Direct explicit configuration match by skill_id
        cfg_skill_id = cfg.get("skill_id")
        if cfg_skill_id is not None:
            return str(cfg_skill_id) == str(skill.id)

        # 2. Direct explicit configuration match by skill_slug
        cfg_skill_slug = cfg.get("skill_slug") or cfg.get("skill")
        if cfg_skill_slug is not None:
            return str(cfg_skill_slug).strip().lower() == str(skill.slug).strip().lower()

        # 3. Course-level associations
        if course_skill_ids is not None:
            # Single-skill course: all activities assess the sole skill taught
            if len(course_skill_ids) == 1 and course_skill_ids[0] == skill.id:
                return True

            # Multi-skill course: safely correlate using structural context (lesson & module)
            if len(course_skill_ids) > 1 and skill.id in course_skill_ids:
                skill_slug_lower = (skill.slug or "").lower()
                skill_name_lower = (skill.name or "").lower()

                les_slug = (lesson.slug or "").lower() if lesson else ""
                les_title = (lesson.title or "").lower() if lesson else ""
                mod_title = (module.title or "").lower() if module else ""
                mod_desc = (module.description or "").lower() if module else ""

                combined_context = f"{les_slug} {les_title} {mod_title} {mod_desc}"

                if skill_slug_lower and skill_slug_lower in combined_context:
                    return True
                if skill_name_lower and skill_name_lower in combined_context:
                    return True

                # Token stem matching for hyphenated skill slugs (e.g., 'html-semantics' -> 'html', 'semantic')
                slug_parts = [p for p in skill_slug_lower.split("-") if len(p) > 2]
                if slug_parts:
                    def _stem(w: str) -> str:
                        if w.endswith("ics"):
                            return w[:-3] + "ic"
                        if w.endswith("s") and len(w) > 3:
                            return w[:-1]
                        return w

                    context_words = re.findall(r"[a-z0-9]+", combined_context)
                    context_stems = {_stem(w) for w in context_words}
                    stemmed_parts = [_stem(p) for p in slug_parts]
                    if all(sp in context_stems for sp in stemmed_parts):
                        return True

                return False

        return False

    def recalculate_skill_mastery(self, user_id: str, skill_id: str) -> SkillMastery:
        """Deterministically recalculate skill mastery from all qualifying assessment attempts."""
        skill = self.db.get(Skill, skill_id)
        if not skill:
            raise ProgressionServiceError(f"Skill '{skill_id}' not found.", code="SKILL_NOT_FOUND", status_code=404)

        # Find all courses teaching this skill
        course_ids = self.db.scalars(
            select(CourseSkill.course_id).where(CourseSkill.skill_id == skill_id)
        ).all()

        course_skills_map: dict[str, list[str]] = {}
        for cid in course_ids:
            sids = self.db.scalars(
                select(CourseSkill.skill_id).where(CourseSkill.course_id == cid)
            ).all()
            course_skills_map[cid] = list(sids)

        # Find user's attempts on activities in lessons within these courses
        stmt = (
            select(Attempt, Activity, Lesson, Module, CourseVersion.course_id)
            .join(Activity, Attempt.activity_id == Activity.id)
            .join(Lesson, Activity.lesson_id == Lesson.id)
            .join(Module, Lesson.module_id == Module.id)
            .join(CourseVersion, Module.course_version_id == CourseVersion.id)
            .where(
                Attempt.user_id == user_id,
                CourseVersion.course_id.in_(course_ids),
                Attempt.score.is_not(None),
            )
            .order_by(Attempt.completed_at.desc())
        )
        raw_attempt_records = self.db.execute(stmt).all()

        # Filter strictly for attempts assessing this specific skill
        attempt_records: list[tuple[Attempt, Activity]] = []
        for att, act, les, mod, c_id in raw_attempt_records:
            c_skill_ids = course_skills_map.get(c_id, [])
            if self._activity_assesses_skill(act, skill, lesson=les, module=mod, course_skill_ids=c_skill_ids):
                attempt_records.append((att, act))

        # Check enrollment in courses teaching this skill
        is_enrolled = (
            self.db.scalar(
                select(func.count(Enrollment.id)).where(
                    Enrollment.user_id == user_id, Enrollment.course_id.in_(course_ids)
                )
            )
            or 0
        ) > 0

        # Formulate verifiable evidence
        distinct_passed_activities: dict[str, tuple[Attempt, Activity]] = {}
        for att, act in attempt_records:
            if att.passed and att.score is not None:
                if act.id not in distinct_passed_activities:
                    distinct_passed_activities[act.id] = (att, act)
                else:
                    # Keep highest score attempt
                    prev_att, _ = distinct_passed_activities[act.id]
                    if (att.score or 0) > (prev_att.score or 0):
                        distinct_passed_activities[act.id] = (att, act)

        evidence_payload: list[dict[str, Any]] = []
        for _act_id, (att, act) in distinct_passed_activities.items():
            evidence_payload.append({
                "activity_id": act.id,
                "activity_title": act.title,
                "activity_type": act.activity_type,
                "attempt_id": att.id,
                "score": att.score,
                "passed": att.passed,
                "assessed_at": att.completed_at.isoformat() if att.completed_at else datetime.now(UTC).isoformat(),
                "rule": "independent_assessment_passed",
            })

        # Calculate mastery level & tier
        passed_count = len(distinct_passed_activities)
        total_attempts = len(attempt_records)

        now = datetime.now(UTC)
        if passed_count >= 2:
            # Evaluated across sufficiently distinct tasks
            avg_score = sum(att.score for att, _ in distinct_passed_activities.values()) / passed_count
            mastery_level = round(min(100.0, avg_score), 1)
            status = SkillMasteryStatus.MASTERED.value if avg_score >= 80.0 else SkillMasteryStatus.PROVISIONAL.value
        elif passed_count == 1:
            att, _ = next(iter(distinct_passed_activities.values()))
            mastery_level = round(float(att.score or 70.0), 1)
            status = SkillMasteryStatus.PROVISIONAL.value
        elif total_attempts > 0:
            mastery_level = 30.0
            status = SkillMasteryStatus.PRACTICING.value
        elif is_enrolled:
            mastery_level = 10.0
            status = SkillMasteryStatus.LEARNING.value
        else:
            mastery_level = 0.0
            status = SkillMasteryStatus.NOT_STARTED.value

        mastery_record = self.db.scalars(
            select(SkillMastery).where(SkillMastery.user_id == user_id, SkillMastery.skill_id == skill_id)
        ).first()

        if not mastery_record:
            mastery_record = SkillMastery(
                user_id=user_id,
                skill_id=skill_id,
                mastery_level=mastery_level,
                status=status,
                evidence=evidence_payload,
                last_assessed_at=now if total_attempts > 0 else None,
            )
            self.db.add(mastery_record)
        else:
            mastery_record.mastery_level = mastery_level
            mastery_record.status = status
            mastery_record.evidence = evidence_payload
            if total_attempts > 0:
                mastery_record.last_assessed_at = now

        self.db.commit()
        self.db.refresh(mastery_record)
        return mastery_record

    # ── 5. Prerequisite Checking ───────────────────────────────────────────────

    def check_course_prerequisites(self, user_id: str | None, course_slug: str) -> CoursePrerequisitesResponse:
        """Inspect whether a learner satisfies all prerequisite skills for a course."""
        course = self.db.scalars(
            select(Course)
            .options(joinedload(Course.skill_associations).joinedload(CourseSkill.skill))
            .where(Course.slug == course_slug)
        ).unique().first()

        if not course:
            raise ProgressionServiceError(f"Course '{course_slug}' not found.", code="COURSE_NOT_FOUND", status_code=404)

        # Gather all skills taught by the course
        course_skill_ids = [cs.skill_id for cs in course.skill_associations]
        if not course_skill_ids:
            return CoursePrerequisitesResponse(course_slug=course.slug, course_title=course.title, eligible=True)

        # Check prerequisite links where dependent skill is in course skills,
        # but prerequisite skill is NOT taught in the course itself
        prereqs = self.db.scalars(
            select(SkillPrerequisite)
            .options(joinedload(SkillPrerequisite.prerequisite_skill))
            .where(
                SkillPrerequisite.skill_id.in_(course_skill_ids),
                SkillPrerequisite.prerequisite_skill_id.notin_(course_skill_ids),
            )
        ).all()

        if not prereqs:
            return CoursePrerequisitesResponse(course_slug=course.slug, course_title=course.title, eligible=True)

        user_mastery_map: dict[str, SkillMastery] = {}
        if user_id:
            prereq_skill_ids = [p.prerequisite_skill_id for p in prereqs]
            user_masteries = self.db.scalars(
                select(SkillMastery).where(
                    SkillMastery.user_id == user_id,
                    SkillMastery.skill_id.in_(prereq_skill_ids),
                )
            ).all()
            user_mastery_map = {m.skill_id: m for m in user_masteries}

        status_items: list[PrerequisiteStatusItem] = []
        unmet: list[str] = []
        eligible = True

        for p in prereqs:
            prereq_skill = p.prerequisite_skill
            rec = user_mastery_map.get(p.prerequisite_skill_id)
            current_status = SkillMasteryStatus(rec.status) if rec else SkillMasteryStatus.NOT_STARTED
            satisfied = current_status in (SkillMasteryStatus.PROVISIONAL, SkillMasteryStatus.MASTERED)

            if not satisfied:
                eligible = False
                unmet.append(prereq_skill.name if prereq_skill else p.prerequisite_skill_id)

            status_items.append(
                PrerequisiteStatusItem(
                    skill_id=p.prerequisite_skill_id,
                    skill_slug=prereq_skill.slug if prereq_skill else "",
                    skill_name=prereq_skill.name if prereq_skill else "Prerequisite Skill",
                    required_level="PROVISIONAL",
                    current_status=current_status,
                    satisfied=satisfied,
                )
            )

        return CoursePrerequisitesResponse(
            course_slug=course.slug,
            course_title=course.title,
            eligible=eligible,
            prerequisites=status_items,
            unmet_prerequisites=unmet,
        )

    # ── 6. Resume Learning & Recommendations ───────────────────────────────────

    def get_resume_learning(self, user_id: str) -> ResumeLearningItem | None:
        """Find the most appropriate incomplete lesson for the learner to resume."""
        enrollments = self.db.scalars(
            select(Enrollment)
            .options(joinedload(Enrollment.course), joinedload(Enrollment.course_version))
            .where(
                Enrollment.user_id == user_id,
                Enrollment.status.in_([EnrollmentStatus.ENROLLED.value, EnrollmentStatus.IN_PROGRESS.value]),
            )
            .order_by(Enrollment.last_accessed_at.desc())
        ).all()

        for enrollment in enrollments:
            # Fetch modules & lessons in sort order
            modules = self.db.scalars(
                select(Module)
                .options(joinedload(Module.lessons))
                .where(Module.course_version_id == enrollment.course_version_id)
                .order_by(Module.sort_order)
            ).unique().all()

            # Completed lesson IDs
            completed_lesson_ids = set(
                self.db.scalars(
                    select(LessonProgress.lesson_id).where(
                        LessonProgress.enrollment_id == enrollment.id,
                        LessonProgress.status == LessonProgressStatus.COMPLETED.value,
                    )
                ).all()
            )

            # Find first non-completed lesson
            for mod in modules:
                sorted_lessons = sorted(mod.lessons, key=lambda les_item: les_item.sort_order)
                for les in sorted_lessons:
                    if les.id not in completed_lesson_ids:
                        total_lessons = sum(len(m.lessons) for m in modules)
                        pct = round((len(completed_lesson_ids) / total_lessons * 100.0), 1) if total_lessons > 0 else 0.0

                        return ResumeLearningItem(
                            course_slug=enrollment.course.slug,
                            course_title=enrollment.course.title,
                            module_title=mod.title,
                            lesson_slug=les.slug,
                            lesson_title=les.title,
                            estimated_minutes=les.estimated_minutes,
                            progress_percentage=pct,
                            last_accessed_at=enrollment.last_accessed_at,
                        )

        return None

    def get_recommendations(self, user_id: str) -> list[RecommendationItem]:
        """Generate explainable, deterministic recommendations based on learner state."""
        recs: list[RecommendationItem] = []

        # 1. Check if there is an active resume-learning lesson
        resume = self.get_resume_learning(user_id)
        if resume:
            recs.append(
                RecommendationItem(
                    id="rec-resume-lesson",
                    action_type="continue_course",
                    type="continue_course",
                    title=f"Continue: {resume.lesson_title}",
                    description=f"Pick up where you left off in {resume.course_title}.",
                    reason="Active course in progress.",
                    link=f"/learn/{resume.course_slug}/{resume.lesson_slug}",
                    badge="In Progress",
                    course_slug=resume.course_slug,
                    lesson_slug=resume.lesson_slug,
                )
            )

        # 2. Check for weak or failed recent assessment attempts
        recent_fail = self.db.scalars(
            select(Attempt)
            .options(joinedload(Attempt.activity))
            .where(Attempt.user_id == user_id, Attempt.passed.is_(False))
            .order_by(Attempt.completed_at.desc())
        ).first()

        if recent_fail and recent_fail.activity and recent_fail.activity.lesson_id:
            lesson = self.db.get(Lesson, recent_fail.activity.lesson_id)
            if lesson:
                module = self.db.get(Module, lesson.module_id)
                course_ver = self.db.get(CourseVersion, module.course_version_id) if module else None
                course = self.db.get(Course, course_ver.course_id) if course_ver else None
                if course:
                    recs.append(
                        RecommendationItem(
                            id=f"rec-retry-{recent_fail.activity.id}",
                            action_type="take_assessment",
                            type="take_assessment",
                            title=f"Retry Assessment: {recent_fail.activity.title}",
                            description="Review key concepts and achieve a passing score to solidify understanding.",
                            reason="Unpassed assessment needs review.",
                            link=f"/learn/{course.slug}/{lesson.slug}",
                            badge="Needs Review",
                            course_slug=course.slug,
                            lesson_slug=lesson.slug,
                        )
                    )

        # 3. Check for skills with mastery gaps (PRACTICING or NEEDS_REVIEW)
        weak_mastery = self.db.scalars(
            select(SkillMastery)
            .options(joinedload(SkillMastery.skill))
            .where(
                SkillMastery.user_id == user_id,
                SkillMastery.status.in_([
                    SkillMasteryStatus.PRACTICING.value,
                    SkillMasteryStatus.NEEDS_REVIEW.value,
                ]),
            )
            .order_by(SkillMastery.mastery_level.asc(), SkillMastery.last_assessed_at.desc().nullslast())
        ).first()

        if weak_mastery and weak_mastery.skill:
            course_skill = self.db.scalars(
                select(CourseSkill)
                .options(joinedload(CourseSkill.course))
                .join(Course, Course.id == CourseSkill.course_id)
                .where(
                    CourseSkill.skill_id == weak_mastery.skill_id,
                    Course.status == CourseStatus.PUBLISHED,
                )
            ).first()

            target_course = course_skill.course if (course_skill and course_skill.course) else None
            status_label = weak_mastery.status.replace("_", " ").title()
            recs.append(
                RecommendationItem(
                    id=f"rec-practice-{weak_mastery.skill.slug}",
                    action_type="practice_skill",
                    type="practice_skill",
                    title=f"Practice Skill: {weak_mastery.skill.name}",
                    description=f"Strengthen your proficiency in {weak_mastery.skill.name} to advance your mastery level.",
                    reason=f"Skill is currently in {status_label} status.",
                    link=f"/courses/{target_course.slug}" if target_course else "/skills",
                    badge="Skill Gap",
                    skill_slug=weak_mastery.skill.slug,
                    course_slug=target_course.slug if target_course else None,
                )
            )

        # 4. Check for unenrolled published courses whose prerequisites are satisfied
        enrolled_course_ids = self.db.scalars(
            select(Enrollment.course_id).where(Enrollment.user_id == user_id)
        ).all()

        available_courses = self.db.scalars(
            select(Course)
            .where(Course.status == CourseStatus.PUBLISHED, Course.id.notin_(enrolled_course_ids))
            .order_by(Course.created_at.asc())
        ).all()

        recommended_course = None
        for candidate in available_courses:
            prereq_status = self.check_course_prerequisites(user_id=user_id, course_slug=candidate.slug)
            if prereq_status.eligible:
                recommended_course = candidate
                break

        if recommended_course:
            recs.append(
                RecommendationItem(
                    id=f"rec-explore-{recommended_course.slug}",
                    action_type="explore_next",
                    type="explore_next",
                    title=f"Start Course: {recommended_course.title}",
                    description=recommended_course.short_description,
                    reason="Recommended based on cross-disciplinary curriculum tracks with satisfied prerequisites.",
                    link=f"/courses/{recommended_course.slug}",
                    badge="Suggested Track",
                    course_slug=recommended_course.slug,
                )
            )

        return recs

    # ── 7. Achievements System ─────────────────────────────────────────────────

    def evaluate_achievements(self, user_id: str) -> list[AchievementResponse]:
        """Evaluate platform achievement rules and award new milestones transactionally."""
        achievements = self.db.scalars(select(Achievement)).all()
        earned_ids = set(
            self.db.scalars(
                select(UserAchievement.achievement_id).where(UserAchievement.user_id == user_id)
            ).all()
        )

        newly_earned: list[AchievementResponse] = []
        now = datetime.now(UTC)

        for ach in achievements:
            if ach.id in earned_ids:
                continue

            should_award = False

            if ach.slug == "first_lesson":
                completed_lessons = (
                    self.db.scalar(
                        select(func.count(LessonProgress.id)).where(
                            LessonProgress.user_id == user_id,
                            LessonProgress.status == LessonProgressStatus.COMPLETED.value,
                        )
                    )
                    or 0
                )
                should_award = completed_lessons >= 1

            elif ach.slug == "fast_learner":
                completed_lessons = (
                    self.db.scalar(
                        select(func.count(LessonProgress.id)).where(
                            LessonProgress.user_id == user_id,
                            LessonProgress.status == LessonProgressStatus.COMPLETED.value,
                        )
                    )
                    or 0
                )
                should_award = completed_lessons >= 3

            elif ach.slug == "first_course":
                completed_courses = (
                    self.db.scalar(
                        select(func.count(Enrollment.id)).where(
                            Enrollment.user_id == user_id,
                            Enrollment.status == EnrollmentStatus.COMPLETED.value,
                        )
                    )
                    or 0
                )
                should_award = completed_courses >= 1

            elif ach.slug == "perfect_score":
                perfect_attempts = (
                    self.db.scalar(
                        select(func.count(Attempt.id)).where(
                            Attempt.user_id == user_id,
                            Attempt.score == 100.0,
                        )
                    )
                    or 0
                )
                should_award = perfect_attempts >= 1

            elif ach.slug == "skill_master":
                mastered_skills = (
                    self.db.scalar(
                        select(func.count(SkillMastery.id)).where(
                            SkillMastery.user_id == user_id,
                            SkillMastery.status == SkillMasteryStatus.MASTERED.value,
                        )
                    )
                    or 0
                )
                should_award = mastered_skills >= 1

            elif ach.slug == "polymath":
                # Enrolled in courses across at least 2 distinct disciplines
                distinct_disciplines = (
                    self.db.scalar(
                        select(func.count(func.distinct(Course.discipline_id)))
                        .join(Enrollment, Enrollment.course_id == Course.id)
                        .where(Enrollment.user_id == user_id)
                    )
                    or 0
                )
                should_award = distinct_disciplines >= 2

            if should_award:
                user_ach = UserAchievement(
                    user_id=user_id,
                    achievement_id=ach.id,
                    earned_at=now,
                )
                self.db.add(user_ach)
                try:
                    self.db.commit()
                    newly_earned.append(
                        AchievementResponse(
                            id=ach.id,
                            slug=ach.slug,
                            name=ach.name,
                            description=ach.description,
                            icon=ach.icon,
                            earned=True,
                            earned_at=now,
                        )
                    )
                except IntegrityError:
                    self.db.rollback()

        return newly_earned

    def get_user_achievements(self, user_id: str) -> list[AchievementResponse]:
        """Fetch full list of platform achievements with earned status for this learner."""
        achievements = self.db.scalars(select(Achievement).order_by(Achievement.created_at.asc())).all()
        user_awards = {
            ua.achievement_id: ua.earned_at
            for ua in self.db.scalars(
                select(UserAchievement).where(UserAchievement.user_id == user_id)
            ).all()
        }

        return [
            AchievementResponse(
                id=a.id,
                slug=a.slug,
                name=a.name,
                description=a.description,
                icon=a.icon,
                earned=a.id in user_awards,
                earned_at=user_awards.get(a.id),
            )
            for a in achievements
        ]

    # ── 8. Consolidated Dashboard Summary ──────────────────────────────────────

    def get_dashboard_summary(self, user_id: str) -> DashboardSummaryResponse:
        """Consolidated aggregation for learner dashboard."""
        enrolled_courses = self.get_user_enrollments(user_id)
        in_progress_cnt = sum(1 for e in enrolled_courses if e.status == EnrollmentStatus.IN_PROGRESS)
        completed_cnt = sum(1 for e in enrolled_courses if e.status == EnrollmentStatus.COMPLETED)

        resume_item = self.get_resume_learning(user_id)

        # Skills summary
        skills_mastery = self.get_user_skills_mastery(user_id)
        learning_cnt = sum(1 for s in skills_mastery if s.status in (SkillMasteryStatus.LEARNING, SkillMasteryStatus.PRACTICING, SkillMasteryStatus.PROVISIONAL))
        mastered_cnt = sum(1 for s in skills_mastery if s.status == SkillMasteryStatus.MASTERED)

        # Recent attempts
        recent_attempts_raw = self.db.scalars(
            select(Attempt)
            .options(joinedload(Attempt.activity))
            .where(Attempt.user_id == user_id)
            .order_by(Attempt.completed_at.desc())
            .limit(5)
        ).all()

        recent_attempts = [
            RecentAttemptItem(
                activity_id=a.activity_id,
                activity_title=a.activity.title if a.activity else "Assessment",
                activity_type=a.activity.activity_type if a.activity else "interactive",
                score=a.score,
                passed=a.passed,
                completed_at=a.completed_at,
            )
            for a in recent_attempts_raw
        ]

        # Achievements
        achievements = self.get_user_achievements(user_id)
        earned_cnt = sum(1 for a in achievements if a.earned)

        # Recommendations
        recommendations = self.get_recommendations(user_id)

        return DashboardSummaryResponse(
            enrolled_courses=enrolled_courses,
            in_progress_courses_count=in_progress_cnt,
            completed_courses_count=completed_cnt,
            resume_learning=resume_item,
            skills_learning_count=learning_cnt,
            skills_mastered_count=mastered_cnt,
            skills=skills_mastery,
            skills_summary=skills_mastery,
            recent_attempts=recent_attempts,
            achievements=achievements,
            achievements_earned_count=earned_cnt,
            achievements_total_count=len(achievements),
            recommendations=recommendations,
        )

    # ── Internal Helper Methods ────────────────────────────────────────────────

    def _get_verified_enrollment(self, enrollment_id: str, user_id: str) -> Enrollment:
        enrollment = self.db.get(Enrollment, enrollment_id)
        if not enrollment:
            raise ProgressionServiceError(f"Enrollment '{enrollment_id}' not found.", code="ENROLLMENT_NOT_FOUND", status_code=404)
        if enrollment.user_id != user_id:
            raise ProgressionServiceError("Forbidden: Unauthorized enrollment access.", code="FORBIDDEN", status_code=403)
        return enrollment

    def _get_verified_lesson(self, lesson_id: str, course_version_id: str) -> Lesson:
        lesson = self.db.get(Lesson, lesson_id)
        if not lesson:
            raise ProgressionServiceError(f"Lesson '{lesson_id}' not found.", code="LESSON_NOT_FOUND", status_code=404)
        module = self.db.get(Module, lesson.module_id)
        if not module or module.course_version_id != course_version_id:
            raise ProgressionServiceError(
                f"Lesson '{lesson_id}' is not part of enrolled course version.",
                code="LESSON_NOT_IN_ENROLLMENT",
                status_code=400,
            )
        return lesson

    def _check_and_update_course_completion(self, enrollment: Enrollment, now: datetime) -> bool:
        modules = self.db.scalars(
            select(Module)
            .options(joinedload(Module.lessons))
            .where(Module.course_version_id == enrollment.course_version_id)
        ).unique().all()

        all_lesson_ids = [les.id for mod in modules for les in mod.lessons]
        if not all_lesson_ids:
            return False

        completed_count = self.db.scalar(
            select(func.count(LessonProgress.id)).where(
                LessonProgress.enrollment_id == enrollment.id,
                LessonProgress.status == LessonProgressStatus.COMPLETED.value,
            )
        ) or 0

        if completed_count >= len(all_lesson_ids):
            enrollment.status = EnrollmentStatus.COMPLETED.value
            enrollment.completed_at = enrollment.completed_at or now
            return True
        elif completed_count > 0 and enrollment.status == EnrollmentStatus.ENROLLED.value:
            enrollment.status = EnrollmentStatus.IN_PROGRESS.value
            return False
        return False

    def _format_enrollment_response(self, enrollment: Enrollment) -> EnrollmentResponse:
        modules = self.db.scalars(
            select(Module)
            .options(joinedload(Module.lessons))
            .where(Module.course_version_id == enrollment.course_version_id)
        ).unique().all()

        total_lessons = sum(len(m.lessons) for m in modules)
        completed_lessons = (
            self.db.scalar(
                select(func.count(LessonProgress.id)).where(
                    LessonProgress.enrollment_id == enrollment.id,
                    LessonProgress.status == LessonProgressStatus.COMPLETED.value,
                )
            )
            or 0
        )

        pct = round((completed_lessons / total_lessons * 100.0), 1) if total_lessons > 0 else 0.0

        return EnrollmentResponse(
            id=enrollment.id,
            user_id=enrollment.user_id,
            course_id=enrollment.course_id,
            course_slug=enrollment.course.slug if enrollment.course else "",
            course_title=enrollment.course.title if enrollment.course else "",
            course_version_id=enrollment.course_version_id,
            version_number=enrollment.course_version.version_number if enrollment.course_version else 1,
            status=EnrollmentStatus(enrollment.status),
            enrolled_at=enrollment.enrolled_at,
            last_accessed_at=enrollment.last_accessed_at,
            completed_at=enrollment.completed_at,
            lessons_total=total_lessons,
            lessons_completed=completed_lessons,
            progress_percentage=pct,
        )

    def _format_lesson_progress_response(
        self, progress: LessonProgress, lesson: Lesson, user_id: str
    ) -> LessonProgressResponse:
        activities = self.db.scalars(
            select(Activity).where(Activity.lesson_id == lesson.id, Activity.is_active.is_(True))
        ).all()

        passed_cnt = 0
        for act in activities:
            cnt = self.db.scalar(
                select(func.count(Attempt.id)).where(
                    Attempt.activity_id == act.id,
                    Attempt.user_id == user_id,
                    Attempt.passed.is_(True),
                )
            )
            if cnt and cnt > 0:
                passed_cnt += 1

        is_completed = progress.status == LessonProgressStatus.COMPLETED.value

        return LessonProgressResponse(
            id=progress.id,
            enrollment_id=progress.enrollment_id,
            lesson_id=progress.lesson_id,
            lesson_slug=lesson.slug,
            lesson_title=lesson.title,
            status=LessonProgressStatus(progress.status),
            started_at=progress.started_at,
            completed_at=progress.completed_at,
            last_accessed_at=progress.last_accessed_at,
            required_activities_total=len(activities),
            required_activities_passed=passed_cnt,
            is_completed=is_completed,
        )

    def _initialize_course_skills_learning(self, user_id: str, course_id: str) -> None:
        skill_ids = self.db.scalars(
            select(CourseSkill.skill_id).where(CourseSkill.course_id == course_id)
        ).all()

        now = datetime.now(UTC)
        for sid in skill_ids:
            record = self.db.scalars(
                select(SkillMastery).where(SkillMastery.user_id == user_id, SkillMastery.skill_id == sid)
            ).first()
            if not record:
                record = SkillMastery(
                    user_id=user_id,
                    skill_id=sid,
                    mastery_level=10.0,
                    status=SkillMasteryStatus.LEARNING.value,
                    evidence=[],
                    last_assessed_at=now,
                )
                self.db.add(record)
        self.db.commit()

    def _recalculate_course_skills(self, user_id: str, course_id: str) -> None:
        skill_ids = self.db.scalars(
            select(CourseSkill.skill_id).where(CourseSkill.course_id == course_id)
        ).all()
        for sid in skill_ids:
            self.recalculate_skill_mastery(user_id, sid)
