"""Idempotent seed script for SkillVerse cross-disciplinary taxonomy and representative courses."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

import app.modules.activities.models  # noqa: F401
from app.infrastructure.database import SessionLocal
from app.modules.auth.models import User, UserProfile, UserRole
from app.modules.auth.security import hash_password
from app.modules.courses.content_schemas import (
    CalloutBlockData,
    CodeExampleBlockData,
    HeadingBlockData,
    LessonBlock,
    LessonContentDocument,
    TextBlockData,
)
from app.modules.courses.models import Course, CourseDifficulty, CourseStatus
from app.modules.courses.service import CourseService
from app.modules.progress.models import Achievement
from app.modules.skills.models import Discipline, SkillDifficulty, SkillPrerequisite
from app.modules.skills.service import SkillService

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s")
logger = logging.getLogger("skillverse.seed")


# ── Seed Data Definitions ──────────────────────────────────────────────────

DISCIPLINE_DEFINITIONS = [
    {
        "slug": "technology",
        "name": "Technology",
        "description": "Software engineering, computer systems, web architecture, and digital tooling.",
        "icon": "code",
        "sort_order": 1,
    },
    {
        "slug": "communication",
        "name": "Communication",
        "description": "Verbal articulation, interpersonal communication, professional presentations, and persuasion.",
        "icon": "message-square",
        "sort_order": 2,
    },
    {
        "slug": "personal-productivity",
        "name": "Personal Productivity",
        "description": "Goal setting, cognitive focus, energy management, and iterative daily planning.",
        "icon": "check-circle",
        "sort_order": 3,
    },
    {
        "slug": "business",
        "name": "Business",
        "description": "Strategy, market analysis, organizational design, and product lifecycle management.",
        "icon": "briefcase",
        "sort_order": 4,
    },
    {
        "slug": "creativity-and-design",
        "name": "Creativity and Design",
        "description": "Visual hierarchy, human-computer interaction, typography, and creative problem solving.",
        "icon": "palette",
        "sort_order": 5,
    },
    {
        "slug": "critical-thinking",
        "name": "Critical Thinking",
        "description": "Formal logic, mental models, cognitive bias mitigation, and evidence evaluation.",
        "icon": "brain",
        "sort_order": 6,
    },
    {
        "slug": "financial-literacy",
        "name": "Financial Literacy",
        "description": "Personal finance, budgeting, risk management, and economic principles.",
        "icon": "dollar-sign",
        "sort_order": 7,
    },
]

SKILL_DEFINITIONS = [
    # Technology Skills
    {
        "slug": "web-principles",
        "name": "How the Web Works",
        "discipline_slug": "technology",
        "difficulty": SkillDifficulty.FOUNDATIONAL,
        "description": "HTTP request-response lifecycle, DNS, client-server models, and browsers.",
        "sort_order": 1,
    },
    {
        "slug": "html-semantics",
        "name": "HTML Structure & Semantics",
        "discipline_slug": "technology",
        "difficulty": SkillDifficulty.FOUNDATIONAL,
        "description": "Semantic markup, accessibility, document outlines, and forms.",
        "sort_order": 2,
    },
    {
        "slug": "css-layouts",
        "name": "CSS & Responsive Layouts",
        "discipline_slug": "technology",
        "difficulty": SkillDifficulty.INTERMEDIATE,
        "description": "Flexbox, CSS Grid, media queries, and responsive container queries.",
        "sort_order": 3,
    },
    {
        "slug": "javascript-basics",
        "name": "JavaScript Foundations",
        "discipline_slug": "technology",
        "difficulty": SkillDifficulty.INTERMEDIATE,
        "description": "Execution contexts, DOM manipulation, asynchronous event loops, and ES modules.",
        "sort_order": 4,
    },
    {
        "slug": "devtools-debugging",
        "name": "Browser Tools & Debugging",
        "discipline_slug": "technology",
        "difficulty": SkillDifficulty.INTERMEDIATE,
        "description": "Breakpoints, network analysis, performance profiling, and console debugging.",
        "sort_order": 5,
    },
    # Communication Skills
    {
        "slug": "clear-expression",
        "name": "Speaking Confidence & Clear Expression",
        "discipline_slug": "communication",
        "difficulty": SkillDifficulty.FOUNDATIONAL,
        "description": "Vocal pacing, structural clarity, tone moderation, and message synthesis.",
        "sort_order": 1,
    },
    {
        "slug": "conversational-fluency",
        "name": "Everyday Conversations",
        "discipline_slug": "communication",
        "difficulty": SkillDifficulty.FOUNDATIONAL,
        "description": "Small talk, open-ended prompts, empathetic listening, and conversational rhythm.",
        "sort_order": 2,
    },
    {
        "slug": "active-listening",
        "name": "Asking Questions & Active Listening",
        "discipline_slug": "communication",
        "difficulty": SkillDifficulty.INTERMEDIATE,
        "description": "Probing inquiries, paraphrasing for comprehension, and non-verbal feedback.",
        "sort_order": 3,
    },
    {
        "slug": "workplace-communication",
        "name": "Professional & Workplace Communication",
        "discipline_slug": "communication",
        "difficulty": SkillDifficulty.INTERMEDIATE,
        "description": "Meeting facilitation, executive summaries, status updates, and conflict de-escalation.",
        "sort_order": 4,
    },
    {
        "slug": "presentation-skills",
        "name": "Interviews & Presentations",
        "discipline_slug": "communication",
        "difficulty": SkillDifficulty.ADVANCED,
        "description": "Storytelling frameworks, structured interview responses (STAR), and persuasive speaking.",
        "sort_order": 5,
    },
    # Personal Productivity Skills
    {
        "slug": "goal-setting",
        "name": "Goals & Priorities",
        "discipline_slug": "personal-productivity",
        "difficulty": SkillDifficulty.FOUNDATIONAL,
        "description": "OKRs, outcome definition, priority filtering, and high-leverage focus.",
        "sort_order": 1,
    },
    {
        "slug": "task-planning",
        "name": "Task Planning & Decomposition",
        "discipline_slug": "personal-productivity",
        "difficulty": SkillDifficulty.FOUNDATIONAL,
        "description": "Breaking large deliverables into discrete actionable tasks and backlog grooming.",
        "sort_order": 2,
    },
    {
        "slug": "time-energy-management",
        "name": "Time & Energy Management",
        "discipline_slug": "personal-productivity",
        "difficulty": SkillDifficulty.INTERMEDIATE,
        "description": "Chronotype alignment, time-blocking, circadian energy curves, and rest cycles.",
        "sort_order": 3,
    },
    {
        "slug": "focus-distraction-control",
        "name": "Distraction Management",
        "discipline_slug": "personal-productivity",
        "difficulty": SkillDifficulty.INTERMEDIATE,
        "description": "Attention shielding, context-switching reduction, and digital hygiene.",
        "sort_order": 4,
    },
    {
        "slug": "reflection-review",
        "name": "Weekly Reviews & Planning",
        "discipline_slug": "personal-productivity",
        "difficulty": SkillDifficulty.ADVANCED,
        "description": "Continuous feedback loops, retro analysis, and adaptive weekly replanning.",
        "sort_order": 5,
    },
]

PREREQUISITE_LINKS = [
    ("html-semantics", "web-principles"),
    ("css-layouts", "html-semantics"),
    ("javascript-basics", "html-semantics"),
    ("devtools-debugging", "javascript-basics"),
    ("conversational-fluency", "clear-expression"),
    ("active-listening", "conversational-fluency"),
    ("workplace-communication", "active-listening"),
    ("presentation-skills", "workplace-communication"),
    ("task-planning", "goal-setting"),
    ("time-energy-management", "task-planning"),
    ("focus-distraction-control", "time-energy-management"),
    ("reflection-review", "focus-distraction-control"),
]


# ── Seed Functions ─────────────────────────────────────────────────────────


def get_or_create_seed_creator(db: Session) -> User:
    """Ensure an official creator user exists to own seed courses."""
    creator = db.scalars(select(User).where(User.email == "curriculum@skillverse.org")).first()
    if creator:
        return creator

    creator = User(
        email="curriculum@skillverse.org",
        password_hash=hash_password("CurriculumCreator2026!"),
        role=UserRole.CREATOR,
        email_verified=True,
    )
    db.add(creator)
    db.flush()

    profile = UserProfile(
        user_id=creator.id,
        display_name="SkillVerse Curriculum Team",
        bio="Official curriculum architect team creating cross-disciplinary master tracks.",
    )
    db.add(profile)
    db.commit()
    db.refresh(creator)
    logger.info("Created seed creator user: curriculum@skillverse.org")
    return creator


def seed_taxonomy(db: Session) -> dict[str, str]:
    """Idempotently seed disciplines, skills, and prerequisite graph edges."""
    skill_service = SkillService(db)
    discipline_map: dict[str, str] = {}
    skill_map: dict[str, str] = {}

    # Seed Disciplines
    for disc_data in DISCIPLINE_DEFINITIONS:
        disc = skill_service.get_discipline_by_slug(disc_data["slug"], only_active=False)
        if not disc:
            disc = skill_service.create_discipline(
                slug=disc_data["slug"],
                name=disc_data["name"],
                description=disc_data["description"],
                icon=disc_data["icon"],
                sort_order=disc_data["sort_order"],
            )
            logger.info("Created discipline: %s", disc.name)
        discipline_map[disc.slug] = disc.id

    # Seed Skills
    for s_data in SKILL_DEFINITIONS:
        skill = skill_service.get_skill_by_slug(s_data["slug"], only_active=False)
        if not skill:
            skill = skill_service.create_skill(
                slug=s_data["slug"],
                name=s_data["name"],
                discipline_id=discipline_map[s_data["discipline_slug"]],
                description=s_data["description"],
                difficulty_level=s_data["difficulty"],
                sort_order=s_data["sort_order"],
            )
            logger.info("Created skill: %s", skill.name)
        skill_map[skill.slug] = skill.id

    # Seed Prerequisites
    for target_slug, prereq_slug in PREREQUISITE_LINKS:
        target_id = skill_map[target_slug]
        prereq_id = skill_map[prereq_slug]
        existing = db.scalars(
            select(SkillPrerequisite).where(
                SkillPrerequisite.skill_id == target_id,
                SkillPrerequisite.prerequisite_skill_id == prereq_id,
            )
        ).first()
        if not existing:
            try:
                skill_service.add_prerequisite(target_id, prereq_id)
                logger.info("Linked prerequisite: %s -> requires %s", target_slug, prereq_slug)
            except Exception as e:
                logger.warning("Could not link %s -> %s: %s", target_slug, prereq_slug, e)

    return skill_map


def build_sample_lesson_document(
    title: str, concept: str, code_sample: str | None = None
) -> LessonContentDocument:
    """Build a valid LessonContentDocument with verified blocks."""
    blocks = [
        LessonBlock(
            id="blk-heading",
            type="heading",
            data=HeadingBlockData(level=2, text=title).model_dump(),
        ),
        LessonBlock(
            id="blk-text",
            type="text",
            data=TextBlockData(
                format="markdown",
                text=f"In this lesson, we explore **{title}** with actionable principles and clear demonstrations.\n\n{concept}",
            ).model_dump(),
        ),
        LessonBlock(
            id="blk-callout",
            type="callout",
            data=CalloutBlockData(
                variant="key_concept",
                title="Core Principle",
                text="Mastering the foundational mental model allows you to reason about edge cases effortlessly.",
            ).model_dump(),
        ),
    ]

    if code_sample:
        blocks.append(
            LessonBlock(
                id="blk-code",
                type="code_example",
                data=CodeExampleBlockData(
                    language="javascript" if "javascript" in title.lower() else "html",
                    code=code_sample,
                    caption="Example code demonstration",
                ).model_dump(),
            )
        )

    return LessonContentDocument(
        schema_version="1.0",
        learning_objectives=[f"Understand and apply core concepts of {title}."],
        blocks=blocks,
    )


def seed_course_a_web_development(
    db: Session, creator_id: str, discipline_id: str, skill_map: dict[str, str]
) -> None:
    """Seed Course A: Web Development Foundations (Published v1)."""
    course_service = CourseService(db)
    slug = "web-development-foundations"
    existing = course_service.db.scalars(select(Course).where(Course.slug == slug)).first()
    if existing:
        if existing.status == CourseStatus.PUBLISHED:
            logger.info("Course A ('%s') already exists and is published.", slug)
            return
        logger.info("Cleaning up incomplete previous draft of Course A ('%s')...", slug)
        db.delete(existing)
        db.commit()

    relevant_skills = [
        skill_map["web-principles"],
        skill_map["html-semantics"],
        skill_map["css-layouts"],
        skill_map["javascript-basics"],
        skill_map["devtools-debugging"],
    ]

    course = course_service.create_course(
        creator_id=creator_id,
        slug=slug,
        title="Web Development Foundations",
        short_description="Master the architectural building blocks of modern web engineering: HTML5, responsive CSS, JavaScript, and browser debugging.",
        full_description=(
            "A comprehensive, hands-on path through modern web engineering. "
            "Learn how the web protocol works, construct accessible semantic documents, build responsive multi-column layouts, "
            "and manipulate the DOM with modern ES JavaScript."
        ),
        discipline_id=discipline_id,
        difficulty_level=CourseDifficulty.BEGINNER,
        estimated_duration_minutes=360,
        learning_objectives=[
            "Explain the client-server request-response lifecycle and DNS resolution.",
            "Write accessible, standards-compliant semantic HTML5 documents.",
            "Architect responsive user interfaces using modern Flexbox and CSS Grid.",
            "Program dynamic client-side interactions with vanilla JavaScript.",
            "Debug live web applications using browser developer tools.",
        ],
        skill_ids=relevant_skills,
    )

    modules_data = [
        (
            "How the Web Works",
            "Protocols, browsers, IP addressing, DNS resolution, and the HTTP request-response cycle.",
            [
                (
                    "web-architecture",
                    "Clients, Servers, and HTTP Requests",
                    "Understanding URLs, HTTP methods, headers, and response status codes.",
                    None,
                ),
                (
                    "browser-pipeline",
                    "The Critical Rendering Path",
                    "How browsers parse HTML to DOM, CSS to CSSOM, and render pixels.",
                    None,
                ),
            ],
        ),
        (
            "HTML Structure and Semantics",
            "Building accessible document outlines with native HTML5 structural elements.",
            [
                (
                    "semantic-tags",
                    "Semantic Elements vs Generic Divs",
                    "Using main, nav, article, section, and header for accessibility and SEO.",
                    "<header>\n  <nav>\n    <a href='/'>SkillVerse</a>\n  </nav>\n</header>",
                ),
                (
                    "forms-and-inputs",
                    "Accessible Web Forms",
                    "Form validation, labels, input types, and keyboard navigation.",
                    None,
                ),
            ],
        ),
        (
            "CSS and Responsive Layout",
            "From box model fundamentals to fluid responsive layouts with Flexbox and Grid.",
            [
                (
                    "box-model-flexbox",
                    "The Box Model and Flexbox Alignment",
                    "Margin, border, padding, flex-direction, and justify-content.",
                    None,
                ),
                (
                    "css-grid-media",
                    "CSS Grid and Responsive Breakpoints",
                    "Defining fractional columns, auto-fill grids, and responsive media queries.",
                    None,
                ),
            ],
        ),
        (
            "JavaScript Foundations",
            "Core language constructs, variables, functions, and the event-driven DOM API.",
            [
                (
                    "js-dom-events",
                    "DOM Querying and Event Listeners",
                    "Selecting elements and reacting to user interactions safely.",
                    "document.querySelector('button').addEventListener('click', (e) => {\n  console.log('Action triggered');\n});",
                ),
                (
                    "async-fetch",
                    "Working with Asynchronous Data",
                    "Promises, async/await, and fetching data from backend REST APIs.",
                    None,
                ),
            ],
        ),
        (
            "Browser Tools and Debugging",
            "Mastering Chrome DevTools to inspect elements, audit network waterfalls, and set breakpoints.",
            [
                (
                    "devtools-inspector",
                    "Elements & Network Inspector",
                    "Inspecting computed styles and monitoring asset payload weights.",
                    None,
                ),
                (
                    "devtools-breakpoints",
                    "Source Debugging and Breakpoints",
                    "Setting conditional breakpoints and stepping through execution.",
                    None,
                ),
            ],
        ),
        (
            "Build a Responsive Portfolio",
            "Capstone project combining semantic HTML, responsive CSS Grid, and interactive JavaScript.",
            [
                (
                    "portfolio-planning",
                    "Portfolio Architecture and Wireframes",
                    "Structuring a multi-section personal portfolio website.",
                    None,
                ),
                (
                    "portfolio-build",
                    "Building and Auditing the Portfolio",
                    "Assembling the site and running Lighthouse accessibility checks.",
                    None,
                ),
            ],
        ),
    ]

    for mod_order, (mod_title, mod_desc, lessons) in enumerate(modules_data, start=1):
        module = course_service.add_module_to_draft(
            course_id=course.id,
            user_id=creator_id,
            title=mod_title,
            description=mod_desc,
            sort_order=mod_order,
        )
        for les_order, (les_slug, les_title, les_desc, code_ex) in enumerate(lessons, start=1):
            lesson = course_service.add_lesson_to_draft(
                course_id=course.id,
                module_id=module.id,
                user_id=creator_id,
                slug=les_slug,
                title=les_title,
                description=les_desc,
                sort_order=les_order,
            )
            doc = build_sample_lesson_document(les_title, les_desc, code_ex)
            course_service.update_lesson_content(
                course_id=course.id,
                lesson_id=lesson.id,
                user_id=creator_id,
                document=doc,
            )

    # Publish Course A formally using the transactional versioning service
    version = course_service.publish_course(
        course_id=course.id,
        publisher_id=creator_id,
        changelog="Initial curriculum publication v1.0.0",
    )
    logger.info("Published Course A ('%s') as version %d", course.title, version.version_number)


def seed_course_b_spoken_english(
    db: Session, creator_id: str, discipline_id: str, skill_map: dict[str, str]
) -> None:
    """Seed Course B: Spoken English and Communication (Published v1)."""
    course_service = CourseService(db)
    slug = "spoken-english-communication"
    existing = course_service.db.scalars(select(Course).where(Course.slug == slug)).first()
    if existing:
        if existing.status == CourseStatus.PUBLISHED:
            logger.info("Course B ('%s') already exists and is published.", slug)
            return
        logger.info("Cleaning up incomplete previous draft of Course B ('%s')...", slug)
        db.delete(existing)
        db.commit()

    relevant_skills = [
        skill_map["clear-expression"],
        skill_map["conversational-fluency"],
        skill_map["active-listening"],
        skill_map["workplace-communication"],
        skill_map["presentation-skills"],
    ]

    course = course_service.create_course(
        creator_id=creator_id,
        slug=slug,
        title="Spoken English and Communication",
        short_description="Develop natural verbal confidence, clear pronunciation, structured workplace articulation, and high-impact interview presence.",
        full_description=(
            "Designed for non-native speakers and professionals looking to enhance verbal clarity and executive presence. "
            "Master everyday conversation rhythms, professional meetings, asking high-value questions, and structured interview techniques."
        ),
        discipline_id=discipline_id,
        difficulty_level=CourseDifficulty.INTERMEDIATE,
        estimated_duration_minutes=300,
        learning_objectives=[
            "Overcome hesitation and speak with steady pacing and vocal variety.",
            "Engage in fluid everyday conversations and initiate natural dialogues.",
            "Structure thoughts spontaneously using proven framing techniques.",
            "Lead and participate effectively in professional workplace discussions.",
            "Deliver persuasive presentations and excel in competency interviews.",
        ],
        skill_ids=relevant_skills,
    )

    modules_data = [
        (
            "Speaking Confidence and Clear Expression",
            "Overcoming vocal inhibition, managing pacing, and projecting clarity.",
            [
                (
                    "vocal-clarity",
                    "Pacing, Pauses, and Thought Chunking",
                    "Delivering ideas in digestible rhythmic chunks rather than rushing.",
                    None,
                ),
                (
                    "overcoming-hesitation",
                    "Managing Filler Words and Hesitation",
                    "Replacing 'um' and 'like' with deliberate pauses and breath support.",
                    None,
                ),
            ],
        ),
        (
            "Everyday Conversations",
            "Casual greetings, initiating small talk, and active verbal reciprocity.",
            [
                (
                    "small-talk-art",
                    "The Art of Engaging Small Talk",
                    "Finding common ground and keeping informal interactions natural and warm.",
                    None,
                ),
                (
                    "active-dialogue",
                    "Active Listening and Reciprocal Sharing",
                    "Validating what others say before introducing your perspective.",
                    None,
                ),
            ],
        ),
        (
            "Asking Questions and Expressing Opinions",
            "Diplomatic inquiry, constructive dissent, and sharing reasoned viewpoints.",
            [
                (
                    "powerful-questions",
                    "Asking High-Value Questions",
                    "Open-ended vs closed inquiries to unblock conversations.",
                    None,
                ),
                (
                    "expressing-dissent",
                    "Diplomatic Disagreement and Framing",
                    "Using softening language to present alternative viewpoints professionally.",
                    None,
                ),
            ],
        ),
        (
            "Professional and Workplace Communication",
            "Executive briefings, cross-functional alignment, and concise email/verbal updates.",
            [
                (
                    "bluf-framework",
                    "Bottom Line Up Front (BLUF)",
                    "Leading with outcomes before diving into supporting context.",
                    None,
                ),
                (
                    "meeting-presence",
                    "Effective Meeting Contributions",
                    "Interjecting with confidence and summarizing action items clearly.",
                    None,
                ),
            ],
        ),
        (
            "Interviews and Presentations",
            "Persuasive storytelling, narrative arcs, and structured interview frameworks.",
            [
                (
                    "star-framework",
                    "Mastering the STAR Method",
                    "Structuring behavioural responses with Situation, Task, Action, and Result.",
                    None,
                ),
                (
                    "presentation-delivery",
                    "Engaging Audience Presentations",
                    "Hooking listeners in the first 60 seconds and delivering memorable conclusions.",
                    None,
                ),
            ],
        ),
        (
            "Simulated Interview Practice",
            "Putting skills into practice with interactive scenarios and feedback reviews.",
            [
                (
                    "mock-scenario",
                    "Realistic Interview Scenarios",
                    "Handling tricky questions, salary inquiries, and technical deep-dives.",
                    None,
                ),
                (
                    "performance-review",
                    "Self-Assessment and Improvement Loops",
                    "Recording and auditing your own speech for continuous growth.",
                    None,
                ),
            ],
        ),
    ]

    for mod_order, (mod_title, mod_desc, lessons) in enumerate(modules_data, start=1):
        module = course_service.add_module_to_draft(
            course_id=course.id,
            user_id=creator_id,
            title=mod_title,
            description=mod_desc,
            sort_order=mod_order,
        )
        for les_order, (les_slug, les_title, les_desc, code_ex) in enumerate(lessons, start=1):
            lesson = course_service.add_lesson_to_draft(
                course_id=course.id,
                module_id=module.id,
                user_id=creator_id,
                slug=les_slug,
                title=les_title,
                description=les_desc,
                sort_order=les_order,
            )
            doc = build_sample_lesson_document(les_title, les_desc, code_ex)
            course_service.update_lesson_content(
                course_id=course.id,
                lesson_id=lesson.id,
                user_id=creator_id,
                document=doc,
            )

    version = course_service.publish_course(
        course_id=course.id,
        publisher_id=creator_id,
        changelog="Initial publication of Spoken English Master Track v1.0.0",
    )
    logger.info("Published Course B ('%s') as version %d", course.title, version.version_number)


def seed_course_c_personal_productivity(
    db: Session, creator_id: str, discipline_id: str, skill_map: dict[str, str]
) -> None:
    """Seed Course C: Personal Productivity (Published v1 with a working draft v2)."""
    course_service = CourseService(db)
    slug = "personal-productivity"
    existing = course_service.db.scalars(select(Course).where(Course.slug == slug)).first()
    if existing:
        if existing.status == CourseStatus.PUBLISHED:
            logger.info("Course C ('%s') already exists and is published.", slug)
            return
        logger.info("Cleaning up incomplete previous draft of Course C ('%s')...", slug)
        db.delete(existing)
        db.commit()

    relevant_skills = [
        skill_map["goal-setting"],
        skill_map["task-planning"],
        skill_map["time-energy-management"],
        skill_map["focus-distraction-control"],
        skill_map["reflection-review"],
    ]

    course = course_service.create_course(
        creator_id=creator_id,
        slug=slug,
        title="Personal Productivity: Systems Over Willpower",
        short_description="Build resilient time, attention, and task architectures to consistently deliver high-impact cognitive work without burnout.",
        full_description=(
            "Move from reactive firefighting to intentional execution. "
            "Learn how to align daily tasks with quarterly outcomes, protect deep-work focus blocks, "
            "and execute a weekly review rhythm that keeps you ahead of your commitments."
        ),
        discipline_id=discipline_id,
        difficulty_level=CourseDifficulty.BEGINNER,
        estimated_duration_minutes=240,
        learning_objectives=[
            "Distinguish high-leverage priorities from low-value busywork.",
            "Decompose complex, intimidating goals into clear next physical actions.",
            "Schedule tasks according to personal cognitive energy curves.",
            "Establish an environmental focus shield to eliminate digital distractions.",
            "Conduct structured 30-minute weekly reviews to reset and realign.",
        ],
        skill_ids=relevant_skills,
    )

    modules_data = [
        (
            "Goals and Priorities",
            "Setting outcome-driven objectives and pruning non-essential commitments.",
            [
                (
                    "prioritization-matrix",
                    "The Eisenhower & Leverage Matrix",
                    "Categorizing work by urgency versus leverage.",
                    None,
                ),
                (
                    "defining-outcomes",
                    "Defining Done and Clear Finish Lines",
                    "Translating ambiguous desires into verifiable milestones.",
                    None,
                ),
            ],
        ),
        (
            "Task Planning",
            "Deconstructing big projects into immediate physical next actions.",
            [
                (
                    "task-decomposition",
                    "Breaking Big Projects into Actionable Steps",
                    "Transforming 'Write thesis' into 15-minute bite-sized steps.",
                    None,
                ),
                (
                    "single-source-truth",
                    "Maintaining a Trusted Task Inbox",
                    "Capturing tasks outside your brain so cognitive capacity stays free.",
                    None,
                ),
            ],
        ),
        (
            "Time and Energy Management",
            "Time blocking, ultradian rhythms, and protecting your most creative hours.",
            [
                (
                    "energy-auditing",
                    "Discovering Your Peak Energy Windows",
                    "Mapping your morning, afternoon, and evening biological rhythms.",
                    None,
                ),
                (
                    "calendar-time-blocking",
                    "Proactive Time Blocking on the Calendar",
                    "Allocating sacred focus blocks before meetings consume your week.",
                    None,
                ),
            ],
        ),
        (
            "Distraction Management",
            "Guarding attention, batching communication, and creating deep work rituals.",
            [
                (
                    "digital-shielding",
                    "Eliminating Cognitive Distractions",
                    "Managing notifications, tab hygiene, and batching email checks.",
                    None,
                ),
                (
                    "deep-work-rituals",
                    "Creating High-Focus Starting Rituals",
                    "Lowering activation energy to start difficult focus sessions.",
                    None,
                ),
            ],
        ),
        (
            "Weekly Reviews",
            "The keystone habit that prevents tasks from falling through the cracks.",
            [
                (
                    "review-checklist",
                    "The 5-Step Weekly Review Rhythm",
                    "Clearing inboxes, auditing past calendar, and choosing next week's focus.",
                    None,
                ),
                (
                    "retro-iteration",
                    "Reflecting and Calibrating Strategy",
                    "Identifying what worked, what failed, and adjusting without guilt.",
                    None,
                ),
            ],
        ),
        (
            "Build a Practical Weekly Plan",
            "Synthesizing your personal operating system into an active weekly roadmap.",
            [
                (
                    "building-your-system",
                    "Assembling Your Personal Operating System",
                    "Combining task tool, calendar, and review checklist into harmony.",
                    None,
                ),
                (
                    "iterative-refinement",
                    "Sustaining the Habit Long-Term",
                    "Staying resilient when plans get interrupted by life.",
                    None,
                ),
            ],
        ),
    ]

    for mod_order, (mod_title, mod_desc, lessons) in enumerate(modules_data, start=1):
        module = course_service.add_module_to_draft(
            course_id=course.id,
            user_id=creator_id,
            title=mod_title,
            description=mod_desc,
            sort_order=mod_order,
        )
        for les_order, (les_slug, les_title, les_desc, code_ex) in enumerate(lessons, start=1):
            lesson = course_service.add_lesson_to_draft(
                course_id=course.id,
                module_id=module.id,
                user_id=creator_id,
                slug=les_slug,
                title=les_title,
                description=les_desc,
                sort_order=les_order,
            )
            doc = build_sample_lesson_document(les_title, les_desc, code_ex)
            course_service.update_lesson_content(
                course_id=course.id,
                lesson_id=lesson.id,
                user_id=creator_id,
                document=doc,
            )

    version = course_service.publish_course(
        course_id=course.id,
        publisher_id=creator_id,
        changelog="Initial publication of Personal Productivity Master Track v1.0.0",
    )
    logger.info("Published Course C ('%s') as version %d", course.title, version.version_number)

    # Open a draft for Course C to demonstrate active draft working copy alongside published v1
    draft_v2 = course_service.get_or_create_draft(course_id=course.id)
    course_service.add_module_to_draft(
        course_id=course.id,
        user_id=creator_id,
        title="Bonus: Advanced Automation & Tooling (Draft)",
        description="Upcoming module testing automation workflows for weekly reviews.",
        sort_order=7,
    )
    logger.info(
        "Created active working draft for Course C (v%d draft open, published v%d intact).",
        draft_v2.version_number,
        version.version_number,
    )


def seed_phase5_activities(db: Session) -> None:
    """Idempotently seed representative Phase 5 interactive activities across the 3 course tracks."""
    from app.modules.activities.models import Activity, ActivityType, GradingConfig, GradingType
    from app.modules.courses.models import Lesson, LessonBlock

    logger.info("Seeding Phase 5 interactive activities across course tracks...")

    activities_spec = [
        # ── 1. Web Development Foundations ─────────────────────────────────
        {
            "lesson_slugs": ["semantic-tags", "document-landmarks"],
            "skill_slug": "html-semantics",
            "activity_type": ActivityType.SINGLE_CHOICE.value,
            "title": "HTML5 Primary Landmark",
            "instructions": "Select the correct semantic element that represents the unique, dominant content of the document body.",
            "configuration": {
                "options": [
                    {"id": "opt-main", "text": "<main> — the dominant content landmark"},
                    {"id": "opt-div", "text": "<div id='content'> — a non-semantic generic container"},
                    {"id": "opt-article", "text": "<article> — self-contained syndicatable composition"},
                    {"id": "opt-section", "text": "<section> — generic standalone thematic section"},
                ]
            },
            "max_attempts": 3,
            "sort_order": 1,
            "passing_score": 70.0,
            "answer_key": {"correct_option_id": "opt-main"},
            "feedback_config": {
                "summary": "<main> represents the dominant content of the <body> and must only appear once per page without hidden attribute.",
                "explanations": {
                    "opt-main": "Correct! <main> is the authoritative landmark for assistive technologies and search crawlers.",
                    "opt-div": "Incorrect. <div> has no semantic meaning in the accessibility tree.",
                },
            },
        },
        {
            "lesson_slugs": ["semantic-tags", "document-landmarks"],
            "skill_slug": "html-semantics",
            "activity_type": ActivityType.MULTIPLE_SELECT.value,
            "title": "Accessible Document Landmark Elements",
            "instructions": "Select all elements that establish native accessible landmarks in HTML5.",
            "configuration": {
                "options": [
                    {"id": "lm-header", "text": "<header> (banner landmark when top-level)"},
                    {"id": "lm-nav", "text": "<nav> (navigation landmark)"},
                    {"id": "lm-main", "text": "<main> (main landmark)"},
                    {"id": "lm-footer", "text": "<footer> (contentinfo landmark when top-level)"},
                    {"id": "lm-div", "text": "<div> (generic container)"},
                    {"id": "lm-span", "text": "<span> (inline phrase container)"},
                ]
            },
            "max_attempts": 3,
            "sort_order": 2,
            "passing_score": 70.0,
            "answer_key": {"correct_option_ids": ["lm-header", "lm-nav", "lm-main", "lm-footer"]},
            "feedback_config": {
                "summary": "header, nav, main, and footer provide native landmark roles; div and span are non-semantic.",
            },
        },
        {
            "lesson_slugs": ["semantic-tags", "document-landmarks"],
            "skill_slug": "html-semantics",
            "activity_type": ActivityType.FILL_IN_THE_BLANK.value,
            "title": "HTML5 Semantic Landmark Elements",
            "instructions": "Fill in the missing HTML element names in the passage below.",
            "configuration": {
                "template": "A standard web document uses the [blank-main] element for dominant unique content, and the [blank-nav] element for navigational link lists.",
                "blanks": [
                    {"id": "blank-main", "hint": "<main> or main"},
                    {"id": "blank-nav", "hint": "<nav> or nav"},
                ],
            },
            "max_attempts": 3,
            "sort_order": 3,
            "passing_score": 70.0,
            "answer_key": {
                "blanks": {
                    "blank-main": {
                        "accepted_answers": ["<main>", "main"],
                        "case_sensitive": False,
                    },
                    "blank-nav": {
                        "accepted_answers": ["<nav>", "nav"],
                        "case_sensitive": False,
                    },
                }
            },
            "feedback_config": {
                "summary": "<main> isolates primary document content; <nav> isolates navigational menus.",
                "explanation": "Native semantic HTML elements provide accessible landmarks without requiring redundant ARIA role attributes.",
            },
        },
        {
            "lesson_slugs": ["forms-and-inputs", "accessible-forms"],
            "skill_slug": "html-semantics",
            "activity_type": ActivityType.CODE_EXERCISE.value,
            "title": "Accessible Form Input & Label Pair",
            "instructions": "Write an accessible HTML form input paired with an explicit <label> using matching 'for' and 'id' attributes.",
            "configuration": {
                "language": "html",
                "task_description": "Construct an input of type 'email' with an associated <label> element for screen reader accessibility.",
                "starter_code": "<form>\n  <!-- Write your label and input here -->\n</form>",
            },
            "max_attempts": None,
            "sort_order": 1,
            "passing_score": 70.0,
            "answer_key": {"test_cases": []},
            "feedback_config": {"summary": "Validates explicit label-for pairing for WCAG 2.1 compliance."},
        },
        # ── 2. Spoken English and Communication ────────────────────────────
        {
            "lesson_slugs": ["bluf-framework", "handling-interruptions", "executive-summary"],
            "skill_slug": "workplace-communication",
            "activity_type": ActivityType.SCENARIO.value,
            "title": "Executive Interruption Decision",
            "instructions": "Evaluate the meeting situation and choose the optimal communication strategy.",
            "configuration": {
                "scenario_text": "During an executive presentation, a VP interrupts slide 2: 'What is the projected timeline slippage and the mitigation cost?'",
                "decisions": [
                    {
                        "id": "dec-bluf",
                        "title": "Bottom Line Up Front (BLUF) Answer",
                        "description": "Answer directly: 'We project a 2-week slip and $15,000 mitigation cost. Here are the two key drivers.'",
                    },
                    {
                        "id": "dec-defer",
                        "title": "Defer until Slide 8",
                        "description": "Request that they hold their question until the timeline section later in the deck.",
                    },
                    {
                        "id": "dec-preamble",
                        "title": "Historical Context First",
                        "description": "Explain supplier shipment difficulties in detail before delivering the numbers.",
                    },
                ],
            },
            "max_attempts": 2,
            "sort_order": 1,
            "passing_score": 70.0,
            "answer_key": {
                "best_decision_id": "dec-bluf",
                "acceptable_decision_ids": [],
            },
            "feedback_config": {
                "summary": "Executives value direct answers first (BLUF). Deferring or giving long preambles breeds impatience.",
            },
        },
        {
            "lesson_slugs": ["star-framework", "star-method"],
            "skill_slug": "presentation-skills",
            "activity_type": ActivityType.ORDERING.value,
            "title": "STAR Response Methodology Sequence",
            "instructions": "Arrange the four components of a behavioral interview answer in chronological order.",
            "configuration": {
                "items": [
                    {"id": "star-s", "text": "Situation: Establish the context, challenge, and stakeholders."},
                    {"id": "star-t", "text": "Task: Clarify your explicit responsibility and objective."},
                    {"id": "star-a", "text": "Action: Detail the specific initiatives YOU executed."},
                    {"id": "star-r", "text": "Result: Quantify the outcome, metrics improved, and lessons learned."},
                ]
            },
            "max_attempts": 3,
            "sort_order": 1,
            "passing_score": 70.0,
            "answer_key": {"correct_order": ["star-s", "star-t", "star-a", "star-r"]},
            "feedback_config": {
                "summary": "STAR proceeds linearly from context (S) to goal (T) to personal action (A) to quantified impact (R).",
            },
        },
        # ── 3. Personal Productivity ───────────────────────────────────────
        {
            "lesson_slugs": ["high-leverage-outcomes"],
            "skill_slug": "goal-setting",
            "activity_type": ActivityType.MATCHING.value,
            "title": "Eisenhower Matrix Quadrant Classification",
            "instructions": "Match each daily scenario to its proper Eisenhower Matrix quadrant.",
            "configuration": {
                "left_items": [
                    {"id": "task-server", "text": "Production server down during peak business hours"},
                    {"id": "task-strategy", "text": "Quarterly skill acquisition and deep system design"},
                    {"id": "task-phone", "text": "Unscheduled vendor phone call on non-urgent tools"},
                    {"id": "task-browse", "text": "Compulsive social media scrolling when fatigued"},
                ],
                "right_items": [
                    {"id": "quad-1", "text": "Quadrant 1: Urgent & Important (Do First)"},
                    {"id": "quad-2", "text": "Quadrant 2: Not Urgent & Important (Schedule & Protect)"},
                    {"id": "quad-3", "text": "Quadrant 3: Urgent & Not Important (Delegate/Decline)"},
                    {"id": "quad-4", "text": "Quadrant 4: Not Urgent & Not Important (Eliminate)"},
                ],
            },
            "max_attempts": 3,
            "sort_order": 1,
            "passing_score": 70.0,
            "answer_key": {
                "pairs": {
                    "task-server": "quad-1",
                    "task-strategy": "quad-2",
                    "task-phone": "quad-3",
                    "task-browse": "quad-4",
                }
            },
            "feedback_config": {
                "summary": "Quadrant 2 is the core driver of long-term leverage; Quadrant 1 requires immediate execution.",
            },
        },
        {
            "lesson_slugs": ["calendar-timeblocking"],
            "skill_slug": "focus-distraction-control",
            "activity_type": ActivityType.TRUE_FALSE.value,
            "title": "Cognitive Context-Switching Principle",
            "instructions": "Evaluate whether the statement is true or false based on attention science.",
            "configuration": {
                "statement": "Switching attention back and forth between deep programming and email alerts incurs no cognitive residue penalty."
            },
            "max_attempts": 2,
            "sort_order": 1,
            "passing_score": 70.0,
            "answer_key": {"correct_boolean": False},
            "feedback_config": {
                "explanation": "False. Dr. Sophie Leroy's attention residue research proves that cognitive switching leaves residual focus on the prior task, significantly degrading accuracy.",
            },
        },
        {
            "lesson_slugs": ["calendar-timeblocking"],
            "skill_slug": "time-energy-management",
            "activity_type": ActivityType.SHORT_ANSWER.value,
            "title": "Focus Scheduling Technique",
            "instructions": "Enter the term used for allocating uninterrupted calendar slots to dedicated high-leverage tasks.",
            "configuration": {
                "prompt": "What scheduling practice dedicates sacred focus blocks to specific priorities on your calendar?",
                "placeholder": "e.g., time blocking",
                "max_length": 100,
            },
            "max_attempts": 3,
            "sort_order": 2,
            "passing_score": 70.0,
            "answer_key": {
                "accepted_answers": ["time blocking", "time-blocking", "timeboxing", "time boxing"],
                "case_sensitive": False,
            },
            "feedback_config": {
                "explanation": "'Time blocking' or 'timeboxing' is the gold standard for protecting focus windows against reactive calendar drift.",
            },
        },
    ]

    for spec in activities_spec:
        # Find matching lessons across courses (might be in multiple versions/modules)
        target_slugs = spec.get("lesson_slugs") or [spec["lesson_slug"]]
        lessons = db.scalars(select(Lesson).where(Lesson.slug.in_(target_slugs))).all()
        if not lessons:
            logger.warning("No lesson found with slugs %s", target_slugs)
            continue

        for lesson in lessons:
            # Check if activity already exists for this lesson
            existing_act = db.scalars(
                select(Activity).where(Activity.lesson_id == lesson.id, Activity.title == spec["title"])
            ).first()

            config = dict(spec["configuration"])
            if "skill_slug" in spec and "skill_slug" not in config:
                config["skill_slug"] = spec["skill_slug"]

            if existing_act:
                # Ensure existing activity configuration stores skill_slug
                if "skill_slug" in spec:
                    curr_cfg = dict(existing_act.configuration or {})
                    if curr_cfg.get("skill_slug") != spec["skill_slug"]:
                        curr_cfg["skill_slug"] = spec["skill_slug"]
                        existing_act.configuration = curr_cfg
            else:
                act = Activity(
                    lesson_id=lesson.id,
                    activity_type=spec["activity_type"],
                    title=spec["title"],
                    instructions=spec["instructions"],
                    configuration=config,
                    max_attempts=spec.get("max_attempts"),
                    sort_order=spec.get("sort_order", 0),
                )
                db.add(act)
                db.flush()

                cfg = GradingConfig(
                    activity_id=act.id,
                    grading_type=GradingType.AUTOMATED.value,
                    passing_score=spec.get("passing_score", 70.0),
                    answer_key=spec["answer_key"],
                    feedback_config=spec.get("feedback_config"),
                )
                db.add(cfg)
                db.flush()

                # Add LessonBlock if not present
                existing_block = db.scalars(
                    select(LessonBlock).where(
                        LessonBlock.lesson_id == lesson.id,
                        LessonBlock.block_type == "activity",
                    )
                ).all()

                has_block = any(b.content.get("activity_id") == act.id for b in existing_block)
                if not has_block:
                    sort_order = len(lesson.blocks) + 1
                    block = LessonBlock(
                        lesson_id=lesson.id,
                        block_type="activity",
                        content={
                            "activity_id": act.id,
                            "title": act.title,
                            "instructions": act.instructions,
                        },
                        sort_order=sort_order,
                    )
                    db.add(block)

                logger.info("Attached Activity '%s' to lesson '%s'", act.title, lesson.slug)

    db.commit()


def seed_phase6_achievements(db: Session) -> None:
    """Seed standard platform achievements idempotently."""
    achievements_spec = [
        {
            "slug": "first_lesson",
            "name": "First Step",
            "description": "Completed your first lesson on SkillVerse.",
            "icon": "award",
            "criteria": {"type": "lesson_count", "threshold": 1},
        },
        {
            "slug": "fast_learner",
            "name": "Active Learner",
            "description": "Completed three lessons across your enrolled tracks.",
            "icon": "zap",
            "criteria": {"type": "lesson_count", "threshold": 3},
        },
        {
            "slug": "first_course",
            "name": "Course Finisher",
            "description": "Satisfied all curriculum requirements and completed an entire course.",
            "icon": "trophy",
            "criteria": {"type": "course_completion", "threshold": 1},
        },
        {
            "slug": "perfect_score",
            "name": "Sharpshooter",
            "description": "Achieved a 100% score on an interactive learning assessment.",
            "icon": "target",
            "criteria": {"type": "assessment_score", "threshold": 100.0},
        },
        {
            "slug": "skill_master",
            "name": "Mastery Unlocked",
            "description": "Demonstrated verified, multi-task evidence to achieve Mastered status in a skill.",
            "icon": "shield-check",
            "criteria": {"type": "skill_mastery", "status": "MASTERED"},
        },
        {
            "slug": "polymath",
            "name": "Cross-Disciplinary Thinker",
            "description": "Enrolled in courses across at least two distinct disciplines.",
            "icon": "sparkles",
            "criteria": {"type": "discipline_count", "threshold": 2},
        },
    ]

    for spec in achievements_spec:
        existing = db.scalars(select(Achievement).where(Achievement.slug == spec["slug"])).first()
        if not existing:
            ach = Achievement(
                slug=spec["slug"],
                name=spec["name"],
                description=spec["description"],
                icon=spec["icon"],
                criteria=spec["criteria"],
            )
            db.add(ach)
            logger.info("Seeded Achievement '%s'", spec["name"])
    db.commit()


def run_seed() -> None:
    """Execute complete idempotent seed."""
    logger.info("Starting SkillVerse Database Seeding...")
    db = SessionLocal()
    try:
        creator = get_or_create_seed_creator(db)
        skill_map = seed_taxonomy(db)

        # Retrieve discipline IDs
        tech_disc = db.scalars(select(Discipline).where(Discipline.slug == "technology")).first()
        comm_disc = db.scalars(select(Discipline).where(Discipline.slug == "communication")).first()
        prod_disc = db.scalars(
            select(Discipline).where(Discipline.slug == "personal-productivity")
        ).first()

        assert tech_disc and comm_disc and prod_disc, "Required disciplines missing after seeding"

        # Seed the three representative course tracks
        seed_course_a_web_development(db, creator.id, tech_disc.id, skill_map)
        seed_course_b_spoken_english(db, creator.id, comm_disc.id, skill_map)
        seed_course_c_personal_productivity(db, creator.id, prod_disc.id, skill_map)

        # Seed Phase 5 representative interactive activities
        seed_phase5_activities(db)

        # Seed Phase 6 platform achievements
        seed_phase6_achievements(db)

        logger.info(
            "Database Seeding Completed Successfully! All 3 courses, taxonomy, activities, and achievements initialized."
        )
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
