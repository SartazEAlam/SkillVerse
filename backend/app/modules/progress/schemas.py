"""Pydantic request and response schemas for enrollments, progression, mastery, and dashboard."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.modules.progress.models import (
    EnrollmentStatus,
    LessonProgressStatus,
    SkillMasteryStatus,
)


class EnrollmentCreate(BaseModel):
    """Payload to enroll in a course."""

    course_slug: str = Field(min_length=1, max_length=200)


class EnrollmentResponse(BaseModel):
    """Enrollment payload including current progress calculations."""

    id: str
    user_id: str
    course_id: str
    course_slug: str
    course_title: str
    course_version_id: str
    version_number: int
    status: EnrollmentStatus
    enrolled_at: datetime
    last_accessed_at: datetime
    completed_at: datetime | None = None
    lessons_total: int = 0
    lessons_completed: int = 0
    progress_percentage: float = 0.0


class LessonProgressResponse(BaseModel):
    """Progress status for a specific lesson."""

    id: str
    enrollment_id: str
    lesson_id: str
    lesson_slug: str
    lesson_title: str
    status: LessonProgressStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None
    last_accessed_at: datetime | None = None
    required_activities_total: int = 0
    required_activities_passed: int = 0
    is_completed: bool = False


class LessonCompleteResponse(BaseModel):
    """Outcome of attempting to complete a lesson."""

    lesson_progress: LessonProgressResponse
    course_completed: bool = False
    newly_earned_achievements: list[AchievementResponse] = Field(default_factory=list)
    message: str = "Lesson marked as complete."


class SkillEvidenceItem(BaseModel):
    """Specific verifiable assessment attempt providing evidence of competency."""

    activity_id: str
    activity_title: str
    activity_type: str
    attempt_id: str
    score: float
    passed: bool
    assessed_at: datetime
    rule: str


class SkillMasteryResponse(BaseModel):
    """Transparent proficiency tier and verified evidence history for a skill."""

    skill_id: str
    skill_slug: str
    skill_name: str
    discipline_slug: str
    discipline_name: str
    difficulty_level: str
    mastery_level: float
    status: SkillMasteryStatus
    evidence: list[SkillEvidenceItem] = Field(default_factory=list)
    last_assessed_at: datetime | None = None
    prerequisites: list[str] = Field(default_factory=list)
    is_unlocked: bool = True


class AchievementResponse(BaseModel):
    """Platform achievement details with optional earned timestamp."""

    id: str
    slug: str
    name: str
    description: str
    icon: str | None = None
    earned: bool = False
    earned_at: datetime | None = None


class ResumeLearningItem(BaseModel):
    """Actionable pointer to the learner's current next lesson."""

    course_slug: str
    course_title: str
    module_title: str
    lesson_slug: str
    lesson_title: str
    estimated_minutes: int | None = None
    progress_percentage: float = 0.0
    last_accessed_at: datetime


class RecommendationItem(BaseModel):
    """Deterministic, explainable next learning action recommendation."""

    id: str
    action_type: str = "explore_next"  # 'continue_course', 'practice_skill', 'take_assessment', 'explore_next'
    type: str = "explore_next"  # API.md and UI backwards-compatible type field
    title: str
    description: str = ""
    reason: str
    link: str = ""
    badge: str | None = None
    course_slug: str | None = None
    lesson_slug: str | None = None
    skill_slug: str | None = None

    @model_validator(mode="before")
    @classmethod
    def sync_type_and_action_type(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Synchronize action_type and type
            if "action_type" in data and not data.get("type"):
                data["type"] = data["action_type"]
            elif "type" in data and not data.get("action_type"):
                data["action_type"] = data["type"]
            if not data.get("type") and not data.get("action_type"):
                data["type"] = "recommendation"
                data["action_type"] = "recommendation"

            # Auto-construct link if missing but course_slug is present
            if not data.get("link") and data.get("course_slug"):
                if data.get("lesson_slug"):
                    data["link"] = f"/learn/{data['course_slug']}/{data['lesson_slug']}"
                else:
                    data["link"] = f"/courses/{data['course_slug']}"
        return data


class PrerequisiteStatusItem(BaseModel):
    """Status of an individual prerequisite requirement."""

    skill_id: str
    skill_slug: str
    skill_name: str
    required_level: str = "PROVISIONAL"
    current_status: SkillMasteryStatus
    satisfied: bool


class CoursePrerequisitesResponse(BaseModel):
    """Evaluation of course prerequisite fulfillment."""

    course_slug: str
    course_title: str
    eligible: bool
    prerequisites: list[PrerequisiteStatusItem] = Field(default_factory=list)
    unmet_prerequisites: list[str] = Field(default_factory=list)


class RecentAttemptItem(BaseModel):
    """Summary of recent assessment attempts for dashboard."""

    activity_id: str
    activity_title: str
    activity_type: str
    score: float | None
    passed: bool | None
    completed_at: datetime | None


class DashboardSummaryResponse(BaseModel):
    """Consolidated learner dashboard overview."""

    enrolled_courses: list[EnrollmentResponse] = Field(default_factory=list)
    in_progress_courses_count: int = 0
    completed_courses_count: int = 0
    resume_learning: ResumeLearningItem | None = None
    skills_learning_count: int = 0
    skills_mastered_count: int = 0
    skills: list[SkillMasteryResponse] = Field(default_factory=list)
    skills_summary: list[SkillMasteryResponse] = Field(default_factory=list)
    recent_attempts: list[RecentAttemptItem] = Field(default_factory=list)
    achievements: list[AchievementResponse] = Field(default_factory=list)
    achievements_earned_count: int = 0
    achievements_total_count: int = 0
    recommendations: list[RecommendationItem] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def sync_skills(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "skills" in data and not data.get("skills_summary"):
                data["skills_summary"] = data["skills"]
            elif "skills_summary" in data and not data.get("skills"):
                data["skills"] = data["skills_summary"]
        return data
