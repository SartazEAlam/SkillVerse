import type { Skill, SkillCategory } from '../types/skill'

export const SKILL_CATEGORIES: SkillCategory[] = [
  {
    id: 'tech',
    name: 'Programming & Web',
    description: 'Core web standards, responsive layout engines, and interactive browser execution.',
    color: '#8B5CF6' // violet
  },
  {
    id: 'communication',
    name: 'Spoken Communication',
    description: 'Workplace articulation, active listening, executive updates, and diplomatic mediation.',
    color: '#06B6D4' // cyan
  },
  {
    id: 'productivity',
    name: 'Productivity & Systems',
    description: 'Deep work preservation, decision trees, time allocation, and systematic workflow design.',
    color: '#10B981' // emerald
  },
  {
    id: 'design',
    name: 'Design & Visual Hierarchy',
    description: 'Design token systems, spatial rhythm, accessible contrast, and component ergonomics.',
    color: '#F59E0B' // amber
  }
]

export const SAMPLE_SKILLS: Skill[] = [
  // Programming & Web (Track 1)
  {
    id: 'skill-html',
    slug: 'semantic-html',
    name: 'Semantic HTML5',
    categoryId: 'tech',
    level: 'Foundational',
    description: 'Accessible document landmark roles, semantic containers, and client-side form constraints.',
    prerequisites: [],
    unlockedSkills: ['skill-css-flex', 'skill-js-dom'],
    courseSlugs: ['web-dev-foundations'],
    sampleMasteryPct: 85,
    x: 16,
    y: 13
  },
  {
    id: 'skill-css-flex',
    slug: 'css-flexbox-grid',
    name: 'CSS Flexbox & Grid',
    categoryId: 'tech',
    level: 'Intermediate',
    description: 'Two-dimensional fluid layouts, responsive container queries, and auto-fit card grids.',
    prerequisites: ['skill-html'],
    unlockedSkills: ['skill-responsive-arch'],
    courseSlugs: ['web-dev-foundations'],
    sampleMasteryPct: 65,
    x: 50,
    y: 7
  },
  {
    id: 'skill-js-dom',
    slug: 'javascript-dom',
    name: 'JavaScript DOM Basics',
    categoryId: 'tech',
    level: 'Intermediate',
    description: 'Event delegation, DOM selection, class list mutations, and dynamic element rendering.',
    prerequisites: ['skill-html'],
    unlockedSkills: ['skill-async-web'],
    courseSlugs: ['web-dev-foundations'],
    sampleMasteryPct: 45,
    x: 50,
    y: 19
  },
  {
    id: 'skill-responsive-arch',
    slug: 'responsive-architecture',
    name: 'Responsive Architecture',
    categoryId: 'tech',
    level: 'Advanced',
    description: 'Multi-screen accessibility, fluid typography clamps, and layout performance tuning.',
    prerequisites: ['skill-css-flex'],
    unlockedSkills: [],
    courseSlugs: ['web-dev-foundations'],
    sampleMasteryPct: 30,
    x: 84,
    y: 7
  },
  {
    id: 'skill-async-web',
    slug: 'async-browser-apis',
    name: 'Async Browser APIs',
    categoryId: 'tech',
    level: 'Advanced',
    description: 'Fetch client interaction, Promises, local caching, and state synchronization.',
    prerequisites: ['skill-js-dom'],
    unlockedSkills: [],
    courseSlugs: ['web-dev-foundations'],
    sampleMasteryPct: 15,
    x: 84,
    y: 19
  },

  // Spoken Communication (Track 2)
  {
    id: 'skill-active-listening',
    slug: 'active-listening',
    name: 'Active Listening & Inquiry',
    categoryId: 'communication',
    level: 'Foundational',
    description: 'Reflective listening, high-impact clarifying questions, and neutral tone verification.',
    prerequisites: [],
    unlockedSkills: ['skill-standup-articulation'],
    courseSlugs: ['spoken-english-communication'],
    sampleMasteryPct: 75,
    x: 16,
    y: 38
  },
  {
    id: 'skill-standup-articulation',
    slug: 'concise-articulation',
    name: 'Concise Articulation',
    categoryId: 'communication',
    level: 'Intermediate',
    description: 'Context-Action-Result format verbal updates delivered with clarity in under 90 seconds.',
    prerequisites: ['skill-active-listening'],
    unlockedSkills: ['skill-executive-briefing', 'skill-diplomatic-negotiation'],
    courseSlugs: ['spoken-english-communication'],
    sampleMasteryPct: 60,
    x: 50,
    y: 38
  },
  {
    id: 'skill-executive-briefing',
    slug: 'executive-briefing',
    name: 'Executive Presentations',
    categoryId: 'communication',
    level: 'Advanced',
    description: 'Hook-Story-Conclusion presentation delivery, vocal projection, and handling adversarial Q&A.',
    prerequisites: ['skill-standup-articulation'],
    unlockedSkills: [],
    courseSlugs: ['spoken-english-communication'],
    sampleMasteryPct: 40,
    x: 84,
    y: 32
  },
  {
    id: 'skill-diplomatic-negotiation',
    slug: 'diplomatic-reframing',
    name: 'Diplomatic Reframing',
    categoryId: 'communication',
    level: 'Advanced',
    description: 'Navigating deadlocked stakeholder conflict by reframing objections into shared problem-solving.',
    prerequisites: ['skill-standup-articulation'],
    unlockedSkills: [],
    courseSlugs: ['spoken-english-communication'],
    sampleMasteryPct: 20,
    x: 84,
    y: 44
  },

  // Productivity & Systems (Track 3)
  {
    id: 'skill-time-audit',
    slug: 'attention-audit',
    name: 'Attention Economics',
    categoryId: 'productivity',
    level: 'Foundational',
    description: 'Context-switch cost calculations, cognitive load monitoring, and friction recognition.',
    prerequisites: [],
    unlockedSkills: ['skill-deep-work', 'skill-priority-matrices'],
    courseSlugs: ['personal-productivity'],
    sampleMasteryPct: 70,
    x: 16,
    y: 63
  },
  {
    id: 'skill-deep-work',
    slug: 'deep-work-architecture',
    name: 'Deep Work Architecture',
    categoryId: 'productivity',
    level: 'Intermediate',
    description: 'Protected uninterrupted focus blocks and environmental distraction elimination protocols.',
    prerequisites: ['skill-time-audit'],
    unlockedSkills: ['skill-personal-os'],
    courseSlugs: ['personal-productivity'],
    sampleMasteryPct: 55,
    x: 50,
    y: 57
  },
  {
    id: 'skill-priority-matrices',
    slug: 'decision-matrices',
    name: 'Prioritization Matrices',
    categoryId: 'productivity',
    level: 'Intermediate',
    description: 'Calibrated Eisenhower urgency/importance grids and Pareto 80/20 leverage allocation.',
    prerequisites: ['skill-time-audit'],
    unlockedSkills: ['skill-personal-os'],
    courseSlugs: ['personal-productivity', 'critical-thinking-problem-solving'],
    sampleMasteryPct: 50,
    x: 50,
    y: 69
  },
  {
    id: 'skill-personal-os',
    slug: 'personal-operating-system',
    name: 'Systemic Workflows (OS)',
    categoryId: 'productivity',
    level: 'Advanced',
    description: 'End-to-end task intake, weekly review cadence, and friction-free morning execution engines.',
    prerequisites: ['skill-deep-work', 'skill-priority-matrices'],
    unlockedSkills: [],
    courseSlugs: ['personal-productivity'],
    sampleMasteryPct: 35,
    x: 84,
    y: 63
  },

  // Design Systems (Track 4)
  {
    id: 'skill-type-rhythm',
    slug: 'spatial-hierarchy',
    name: 'Spatial Rhythm & Grid',
    categoryId: 'design',
    level: 'Foundational',
    description: 'Base-4 spacing scales, mathematical font hierarchies, and proportional content padding.',
    prerequisites: [],
    unlockedSkills: ['skill-design-tokens'],
    courseSlugs: ['ui-ux-design-systems'],
    sampleMasteryPct: 60,
    x: 16,
    y: 88
  },
  {
    id: 'skill-design-tokens',
    slug: 'design-tokens-wcag',
    name: 'Design Tokens & WCAG',
    categoryId: 'design',
    level: 'Intermediate',
    description: 'Semantic CSS variable mapping, accessible WCAG 2.1 AA contrast ratios, and theme tokens.',
    prerequisites: ['skill-type-rhythm'],
    unlockedSkills: [],
    courseSlugs: ['ui-ux-design-systems'],
    sampleMasteryPct: 40,
    x: 50,
    y: 88
  }
]
