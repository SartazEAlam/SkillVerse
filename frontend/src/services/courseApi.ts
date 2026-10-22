/**
 * SkillVerse Course & Content API Service.
 *
 * Provides typed methods for accessing the Phase 3 published course catalog,
 * course outlines, and structured lesson content.
 */

import { request } from './api'
import type {
  ApiCourseDetail,
  ApiCoursePaginatedResponse,
  ApiLessonDetail,
} from '../types/catalog'
import { SAMPLE_COURSES } from '../data/courses'

export interface CourseFilterParams {
  discipline?: string
  difficulty?: string
  search?: string
  page?: number
  limit?: number
}

export const courseApi = {
  /**
   * Fetch paginated list of published courses from the public catalog.
   */
  async listPublishedCourses(
    params?: CourseFilterParams,
    signal?: AbortSignal
  ): Promise<ApiCoursePaginatedResponse> {
    const query = new URLSearchParams()
    if (params?.discipline) query.set('discipline', params.discipline)
    if (params?.difficulty) query.set('difficulty', params.difficulty)
    if (params?.search) query.set('search', params.search)
    if (params?.page) query.set('page', String(params.page))
    if (params?.limit) query.set('limit', String(params.limit))

    const qs = query.toString()
    return request<ApiCoursePaginatedResponse>(`/courses${qs ? `?${qs}` : ''}`, { signal })
  },

  /**
   * Fetch full curriculum and modules from the published course version.
   */
  async getPublishedCourse(slug: string, signal?: AbortSignal): Promise<ApiCourseDetail> {
    return request<ApiCourseDetail>(`/courses/${slug}`, { signal })
  },

  /**
   * Fetch individual lesson details and structured content blocks.
   */
  async getPublishedLesson(
    courseSlug: string,
    lessonSlug: string,
    signal?: AbortSignal
  ): Promise<ApiLessonDetail> {
    return request<ApiLessonDetail>(`/courses/${courseSlug}/lessons/${lessonSlug}`, { signal })
  },

  /**
   * Check if a course slug exists in the local demo dataset and return formatted course outline.
   */
  getDemoCourse(slug: string): ApiCourseDetail | null {
    const demo = SAMPLE_COURSES.find(
      (c) => c.slug === slug || c.slug === slug.replace('-development-', '-dev-')
    )
    if (!demo) return null

    return {
      id: demo.id,
      slug: demo.slug,
      title: demo.title,
      short_description: demo.shortDescription,
      full_description: demo.fullDescription,
      discipline_id: demo.categoryId,
      discipline_slug: demo.categoryId,
      discipline_name: demo.categoryName,
      difficulty_level:
        demo.level.toUpperCase() === 'BEGINNER'
          ? 'BEGINNER'
          : demo.level.toUpperCase() === 'INTERMEDIATE'
          ? 'INTERMEDIATE'
          : 'ADVANCED',
      estimated_duration_minutes: demo.estimatedHours * 60,
      cover_image_url: null,
      status: 'PUBLISHED',
      creator_id: 'curriculum-team',
      version_id: 'demo-v1',
      version_number: 1,
      published_at: '2026-10-21T00:00:00Z',
      learning_objectives: demo.learningObjectives,
      skills: demo.skillsTaught.map((s, idx) => ({
        id: `demo-skill-${idx}`,
        slug: s.toLowerCase().replace(/[^a-z0-9]+/g, '-'),
        name: s,
        difficulty_level: 'FOUNDATIONAL',
        sort_order: idx + 1,
      })),
      modules: demo.modules.map((m) => ({
        id: m.id,
        title: m.title,
        description: m.description,
        sort_order: m.sortOrder,
        lessons: m.lessons.map((l, lIdx) => {
          let blocks: ApiLessonDetail['blocks'] = []

          if (l.slug === 'document-structure-semantics' || l.slug === 'document-landmarks') {
            blocks = [
              {
                id: `${l.id}-h1`,
                block_type: 'heading',
                content: { level: 2, text: 'The Role of Semantic Landmarks in Modern Web Architecture' },
                sort_order: 1,
              },
              {
                id: `${l.id}-txt1`,
                block_type: 'text',
                content: {
                  format: 'markdown',
                  text: 'HTML is not merely a visual layout tool—it is the semantic backbone of the World Wide Web. When web pages rely exclusively on unsemantic `<div>` and `<span>` elements, browsers, search engine indexers, and assistive technologies are stripped of crucial structural meaning.\n\nSemantic elements communicate purpose directly to the Accessibility Tree. Assistive tools like screen readers allow users to jump directly between landmark regions (`<main>`, `<nav>`, `<aside>`) without listening to entire pages sequentially.',
                },
                sort_order: 2,
              },
              {
                id: `${l.id}-callout1`,
                block_type: 'callout',
                content: {
                  variant: 'key_concept',
                  title: 'Core Architectural Principle',
                  text: 'A standards-compliant document should contain exactly one visible, top-level `<main>` landmark. Never nest a `<main>` element within `<header>`, `<footer>`, or `<nav>`.',
                },
                sort_order: 3,
              },
              {
                id: `${l.id}-code1`,
                block_type: 'code_example',
                content: {
                  language: 'html',
                  code: `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>SkillVerse Learning Portal</title>
</head>
<body>
  <!-- Global site header with primary navigation -->
  <header role="banner">
    <a href="#main-content" class="skip-link">Skip to main content</a>
    <nav aria-label="Primary Navigation">
      <ul>
        <li><a href="/catalog">Course Catalog</a></li>
        <li><a href="/skills">Skill Matrix</a></li>
        <li><a href="/dashboard">Learner Dashboard</a></li>
      </ul>
    </nav>
  </header>

  <!-- Unique primary content of the document -->
  <main id="main-content">
    <article>
      <header>
        <h1>Building Accessible Web Applications</h1>
        <p>Published on <time datetime="2026-10-22">October 22, 2026</time></p>
      </header>
      <p>Semantic markup transforms passive web pages into navigable software documents.</p>
    </article>

    <!-- Contextually related sidebar -->
    <aside aria-label="Related Resources">
      <h2>Prerequisites</h2>
      <ul>
        <li>HTTP/1.1 and Client-Server Fundamentals</li>
        <li>Browser Critical Rendering Path</li>
      </ul>
    </aside>
  </main>

  <!-- Global footer with copyright and legals -->
  <footer role="contentinfo">
    <p>&copy; 2026 SkillVerse Learning Platform. All rights reserved.</p>
  </footer>
</body>
</html>`,
                  caption: 'Standards-Compliant Semantic Landmark Layout',
                  show_line_numbers: true,
                },
                sort_order: 4,
              },
              {
                id: `${l.id}-h2`,
                block_type: 'heading',
                content: { level: 3, text: 'Native Landmark Elements & Accessibility Roles' },
                sort_order: 5,
              },
              {
                id: `${l.id}-list1`,
                block_type: 'list',
                content: {
                  ordered: false,
                  items: [
                    '`<header>`: Introductory branding or global navigation; maps to the `banner` landmark when a direct child of `<body>`.',
                    '`<nav>`: Navigational link groups; provide an `aria-label` when multiple nav elements exist on a page.',
                    '`<main>`: Encapsulates dominant content unique to this document; only one visible `<main>` per page.',
                    '`<article>`: Self-contained, independently distributable composition (blog post, forum topic, news article).',
                    '`<aside>`: Secondary content complementary to main flow (sidebars, related links, glossaries).',
                    '`<footer>`: Concluding section containing copyrights, legal notices, and author details (`contentinfo` landmark).',
                  ],
                },
                sort_order: 6,
              },
              {
                id: `${l.id}-callout2`,
                block_type: 'callout',
                content: {
                  variant: 'tip',
                  title: 'Pro Tip: Keyboard Skip Links',
                  text: 'Always provide an accessible "Skip to main content" link as the first focusable child of `<body>`. When keyboard users press Tab upon load, the link appears, allowing them to bypass repetitive navigation bars.',
                },
                sort_order: 7,
              },
            ]
          } else if (l.slug === 'accessible-forms-inputs' || l.slug === 'accessible-forms') {
            blocks = [
              {
                id: `${l.id}-h1`,
                block_type: 'heading',
                content: { level: 2, text: 'Constructing Accessible Web Forms' },
                sort_order: 1,
              },
              {
                id: `${l.id}-txt1`,
                block_type: 'text',
                content: {
                  format: 'markdown',
                  text: 'Forms represent the critical interactive interface between users and software. Poor form architecture creates severe usability hurdles—especially for keyboard-only navigators, voice input tools, and screen reader users.\n\nA frequent anti-pattern is replacing `<label>` tags with `placeholder` attributes. Placeholders disappear upon typing, lack sufficient contrast by default, and fail to announce field purposes reliably to assistive technologies.',
                },
                sort_order: 2,
              },
              {
                id: `${l.id}-callout1`,
                block_type: 'callout',
                content: {
                  variant: 'warning',
                  title: 'The Placeholder Anti-Pattern',
                  text: 'Never use the `placeholder` attribute as a substitute for `<label>`. Once a user types even one character, the placeholder disappears, leaving them without context or verification.',
                },
                sort_order: 3,
              },
              {
                id: `${l.id}-code1`,
                block_type: 'code_example',
                content: {
                  language: 'html',
                  code: `<form action="/api/v1/auth/register" method="POST" novalidate>
  <!-- Input with explicit label, hint text, and validation binding -->
  <div class="form-group">
    <label for="learner-email">Email Address <span aria-hidden="true">*</span></label>
    <input
      type="email"
      id="learner-email"
      name="email"
      required
      autocomplete="email"
      aria-required="true"
      aria-describedby="email-hint email-error"
      aria-invalid="false"
      class="input-control"
    />
    <small id="email-hint" class="input-hint">
      We will send your account verification token to this address.
    </small>
    <span id="email-error" class="error-msg" role="alert" aria-live="polite"></span>
  </div>

  <!-- Grouped inputs with fieldset and legend -->
  <fieldset class="form-fieldset">
    <legend>Preferred Learning Discipline</legend>
    <div class="radio-option">
      <input type="radio" id="disc-tech" name="discipline" value="tech" checked />
      <label for="disc-tech">Software Engineering & Web</label>
    </div>
    <div class="radio-option">
      <input type="radio" id="disc-comm" name="discipline" value="communication" />
      <label for="disc-comm">Spoken English & Communication</label>
    </div>
  </fieldset>

  <!-- Submit button with clear accessible name -->
  <button type="submit" class="btn-primary">
    Create Learner Account
  </button>
</form>`,
                  caption: 'Accessible Registration Form with Client-Side Validation',
                  show_line_numbers: true,
                },
                sort_order: 4,
              },
              {
                id: `${l.id}-h2`,
                block_type: 'heading',
                content: { level: 3, text: 'Essential Accessibility Rules for Input Controls' },
                sort_order: 5,
              },
              {
                id: `${l.id}-list1`,
                block_type: 'list',
                content: {
                  ordered: true,
                  items: [
                    '**Explicit Label Binding**: Always pair `label[for]` with `input[id]`. Clicking the label immediately focuses the control and expands hit target size.',
                    '**Programmatic Error Associations**: When validation fails, set `aria-invalid="true"` on the input and reference error messages using `aria-describedby`.',
                    '**Fieldset & Legend for Compound Groups**: Whenever multiple inputs share a single conceptual question (radios, checkboxes), wrap them in a `<fieldset>` with an informative `<legend>`.',
                    '**Semantic Input Types**: Use `type="email"`, `type="tel"`, and `type="number"` to invoke appropriate mobile virtual keyboards and native browser constraint checks.',
                  ],
                },
                sort_order: 6,
              },
              {
                id: `${l.id}-callout2`,
                block_type: 'callout',
                content: {
                  variant: 'tip',
                  title: 'Dynamic Announcements with aria-live',
                  text: 'Use `aria-live="polite"` on error feedback containers. Screen readers will announce dynamic validation messages politely once the current utterance finishes.',
                },
                sort_order: 7,
              },
            ]
          } else if (l.slug === 'html-mastery-quiz' || l.slug === 'accessibility-checkpoint') {
            blocks = [
              {
                id: `${l.id}-h1`,
                block_type: 'heading',
                content: { level: 2, text: 'Markup & Accessibility Quality Audit' },
                sort_order: 1,
              },
              {
                id: `${l.id}-txt1`,
                block_type: 'text',
                content: {
                  format: 'markdown',
                  text: 'Before advancing to CSS layout engines and client-side JavaScript, web engineers perform structured accessibility audits on their markup. A robust HTML document outline ensures that styling and interactivity build upon a compliant foundation.\n\nReview the core compliance checklist below to verify your document structure against WCAG 2.2 Level AA criteria.',
                },
                sort_order: 2,
              },
              {
                id: `${l.id}-callout1`,
                block_type: 'callout',
                content: {
                  variant: 'key_concept',
                  title: 'WCAG 2.2 AA Conformance Target',
                  text: 'All SkillVerse interfaces adhere to WCAG 2.2 Level AA accessibility standards, requiring full keyboard operability, minimum 4.5:1 text contrast ratios, visible focus indicators, and semantic document outlines.',
                },
                sort_order: 3,
              },
              {
                id: `${l.id}-h2`,
                block_type: 'heading',
                content: { level: 3, text: 'Core Markup Audit Checklist' },
                sort_order: 4,
              },
              {
                id: `${l.id}-list1`,
                block_type: 'list',
                content: {
                  ordered: false,
                  items: [
                    '**Heading Hierarchy**: Ensure `<h1>` is followed sequentially by `<h2>`, `<h3>` without skipping levels (e.g. avoid jumping from `<h1>` directly to `<h4>`).',
                    '**Landmark Roles**: Verify exactly one `<main>` landmark exists and primary navigation is identified with `<nav aria-label="...">`.',
                    '**Alternative Text**: Ensure all `<img>` tags provide descriptive `alt` text, or explicit `alt=""` if purely decorative.',
                    '**Form Associations**: Confirm every `<input>`, `<select>`, and `<textarea>` has a corresponding `<label for="...">`.',
                    '**Focus Rings**: Ensure interactive elements maintain a visible, high-contrast focus ring during keyboard Tab navigation.',
                  ],
                },
                sort_order: 5,
              },
              {
                id: `${l.id}-code1`,
                block_type: 'code_example',
                content: {
                  language: 'html',
                  code: `<!-- Verified Accessible Semantic Section -->
<section aria-labelledby="checkpoint-audit-heading">
  <h2 id="checkpoint-audit-heading">Module 1 Compliance Verification</h2>
  <div class="audit-card" role="region" aria-label="Audit summary">
    <p><strong>Status:</strong> All semantic landmarks and form bindings verified.</p>
    <p>Document outline is fully navigable via screen reader rotor and keyboard Tab sequence.</p>
  </div>
</section>`,
                  caption: 'Remediated Semantic HTML Document Section',
                  show_line_numbers: true,
                },
                sort_order: 6,
              },
            ]
          } else {
            // General lesson content with clean, professional educational copy
            const codeSample =
              l.activityType === 'code_exercise'
                ? l.slug.includes('css') || l.slug.includes('grid') || l.slug.includes('flexbox')
                  ? `/* Layout architecture sample for ${l.title} */\n.container {\n  display: flex;\n  justify-content: space-between;\n  align-items: center;\n  gap: 1.5rem;\n}\n\n@media (max-width: 768px) {\n  .container {\n    flex-direction: column;\n    align-items: stretch;\n  }\n}`
                  : `// Core logic implementation for ${l.title}\nfunction initializeModule() {\n  const target = document.querySelector('#content');\n  if (!target) return false;\n  target.setAttribute('aria-busy', 'false');\n  return true;\n}\n\ninitializeModule();`
                : null

            blocks = [
              {
                id: `${l.id}-heading`,
                block_type: 'heading',
                content: { level: 2, text: l.title },
                sort_order: 1,
              },
              {
                id: `${l.id}-text`,
                block_type: 'text',
                content: {
                  format: 'markdown',
                  text: `${l.description}\n\nIn this lesson, you will master the principles of **${l.title}**. Building a reliable mental model of these techniques is essential for developing performant, standards-compliant applications.`,
                },
                sort_order: 2,
              },
              {
                id: `${l.id}-callout`,
                block_type: 'callout',
                content: {
                  variant: 'key_concept',
                  title: 'Core Concept',
                  text: `Mastery of ${l.title} requires continuous hands-on practice. Review each example carefully before applying it to larger projects.`,
                },
                sort_order: 3,
              },
              ...(codeSample
                ? [
                    {
                      id: `${l.id}-code`,
                      block_type: 'code_example' as const,
                      content: {
                        language: l.slug.includes('css') ? 'css' : 'javascript',
                        code: codeSample,
                        caption: `Code Implementation: ${l.title}`,
                        show_line_numbers: true,
                      },
                      sort_order: 4,
                    },
                  ]
                : []),
            ]
          }

          return {
            id: l.id,
            slug: l.slug,
            title: l.title,
            description: l.description,
            learning_objectives: [
              `Understand and apply the core principles of ${l.title}.`,
              'Write clean, accessible, standards-compliant markup and code.',
            ],
            estimated_minutes: l.estimatedMinutes,
            sort_order: lIdx + 1,
            content_version: 1,
            blocks,
          }
        }),
      })),
    }
  },
}
