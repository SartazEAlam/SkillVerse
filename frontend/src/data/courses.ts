import type { Course } from '../types/course'

export const SAMPLE_COURSES: Course[] = [
  {
    id: 'course-web-dev',
    slug: 'web-dev-foundations',
    title: 'Web Development Foundations',
    shortDescription: 'Build modern responsive web pages with HTML5, semantic structure, modern CSS layouts, and interactive JavaScript.',
    fullDescription: 'Learn web development through structured hands-on coding exercises. Starting from foundational markup to interactive DOM manipulation, every chapter combines direct explanation with live in-browser code challenges and automated test verification.',
    categoryId: 'tech',
    categoryName: 'Programming & Web',
    level: 'Beginner',
    estimatedHours: 12,
    modulesCount: 3,
    lessonsCount: 9,
    skillsTaught: ['HTML5 Semantic Markup', 'CSS Flexbox & Grid', 'JavaScript DOM Basics'],
    learningObjectives: [
      'Structure clean, accessible web pages using semantic HTML elements.',
      'Construct fluid, responsive layouts using modern CSS Flexbox and Grid.',
      'Add dynamic browser interactivity with clean JavaScript event listeners.',
      'Understand browser rendering, accessibility standards, and responsive breakpoints.'
    ],
    modules: [
      {
        id: 'mod-html-structure',
        title: 'Module 1: Semantic HTML & Document Architecture',
        description: 'Understand the skeleton of the web. Learn semantic tags, accessibility attributes, forms, and validation.',
        sortOrder: 1,
        lessons: [
          {
            id: 'les-html-1',
            slug: 'document-structure-semantics',
            title: 'Document Structure & Semantic Tags',
            estimatedMinutes: 20,
            activityType: 'code_exercise',
            description: 'Convert unsemantic <div> soups into accessible header, main, section, and article architectures.'
          },
          {
            id: 'les-html-2',
            slug: 'accessible-forms-inputs',
            title: 'Accessible Forms & Client-Side Validation',
            estimatedMinutes: 25,
            activityType: 'code_exercise',
            description: 'Build robust forms with explicit labels, correct input types, and required constraint validations.'
          },
          {
            id: 'les-html-3',
            slug: 'html-mastery-quiz',
            title: 'Markup & Accessibility Checkpoint',
            estimatedMinutes: 15,
            activityType: 'quiz',
            description: 'Validate your understanding of heading levels, ARIA landmark roles, and image alternatives.'
          }
        ]
      },
      {
        id: 'mod-css-layouts',
        title: 'Module 2: Modern CSS Layouts (Flexbox & Grid)',
        description: 'Master two-dimensional layouts, alignment, responsive units, and media queries without layout hacks.',
        sortOrder: 2,
        lessons: [
          {
            id: 'les-css-1',
            slug: 'flexbox-in-practice',
            title: 'Flexbox Alignment & Spacing',
            estimatedMinutes: 30,
            activityType: 'code_exercise',
            description: 'Implement navigation bars, centered hero elements, and dynamic wrap rows using flex-grow and justify-content.'
          },
          {
            id: 'les-css-2',
            slug: 'css-grid-dashboards',
            title: 'CSS Grid Systems & Card Matrices',
            estimatedMinutes: 35,
            activityType: 'code_exercise',
            description: 'Define auto-fill responsive card grids using repeat(), minmax(), and named grid areas.'
          },
          {
            id: 'les-css-3',
            slug: 'responsive-design-check',
            title: 'Responsive Breakpoints Evaluation',
            estimatedMinutes: 20,
            activityType: 'practical_task',
            description: 'Refactor a desktop-only layout to seamlessly adapt across 360px mobile, 768px tablet, and 1200px widescreen.'
          }
        ]
      },
      {
        id: 'mod-js-basics',
        title: 'Module 3: JavaScript DOM Interactivity',
        description: 'Bring static pages to life by listening to events, querying elements, and updating user interfaces.',
        sortOrder: 3,
        lessons: [
          {
            id: 'les-js-1',
            slug: 'dom-selection-manipulation',
            title: 'Querying & Manipulating the DOM',
            estimatedMinutes: 30,
            activityType: 'code_exercise',
            description: 'Select elements with querySelector, mutate textContent, toggle classLists, and render dynamic lists.'
          },
          {
            id: 'les-js-2',
            slug: 'event-driven-ui',
            title: 'Event Listeners & Form Submissions',
            estimatedMinutes: 30,
            activityType: 'code_exercise',
            description: 'Capture click, submit, and keydown events while preventing standard page reload behaviors.'
          },
          {
            id: 'les-js-3',
            slug: 'web-foundations-capstone',
            title: 'Capstone: Interactive Task Tracker',
            estimatedMinutes: 45,
            activityType: 'practical_task',
            description: 'Combine HTML, CSS Grid, and JavaScript event delegation to create a complete task manager.'
          }
        ]
      }
    ]
  },
  {
    id: 'course-spoken-english',
    slug: 'spoken-english-communication',
    title: 'Spoken English and Professional Communication',
    shortDescription: 'Master clear articulation, workplace conversational etiquette, presentation delivery, and confident meeting participation.',
    fullDescription: 'Develop real communicative competence in professional environments. Unlike passive grammar exercises, this course focuses on active simulation: practicing meetings, pitching ideas, summarizing complex points concisely, and handling challenging questions with tact and poise.',
    categoryId: 'communication',
    categoryName: 'Communication',
    level: 'Beginner',
    estimatedHours: 10,
    modulesCount: 3,
    lessonsCount: 8,
    skillsTaught: ['Active Listening', 'Meeting Facilitation', 'Concise Articulation', 'Persuasive Delivery'],
    learningObjectives: [
      'Communicate complex project updates clearly in under two minutes.',
      'Handle disagreements professionally using diplomatic reframing techniques.',
      'Structure presentation openings and conclusions for maximum audience retention.',
      'Lead and participate in collaborative meetings with structured agendas and summaries.'
    ],
    modules: [
      {
        id: 'mod-comm-1',
        title: 'Module 1: Workplace Speaking & Daily Standups',
        description: 'Clear, concise verbal updates. How to communicate what you did, what is next, and what blockers you have.',
        sortOrder: 1,
        lessons: [
          {
            id: 'les-comm-1',
            slug: 'effective-standup-updates',
            title: 'The 90-Second Standup Update',
            estimatedMinutes: 20,
            activityType: 'conversation',
            description: 'Practice structured vocal updates using the Context-Action-Result format with real-time feedback.'
          },
          {
            id: 'les-comm-2',
            slug: 'asking-clarifying-questions',
            title: 'Asking High-Impact Clarifying Questions',
            estimatedMinutes: 25,
            activityType: 'conversation',
            description: 'Master open-ended questioning frameworks when project requirements or deadlines are ambiguous.'
          },
          {
            id: 'les-comm-3',
            slug: 'clarity-articulation-quiz',
            title: 'Communication Nuance & Tone Checkpoint',
            estimatedMinutes: 15,
            activityType: 'quiz',
            description: 'Identify passive-aggressive versus constructive phrasing in standard team correspondence.'
          }
        ]
      },
      {
        id: 'mod-comm-2',
        title: 'Module 2: Presentation & Storytelling Frameworks',
        description: 'Organize ideas into compelling narratives. Maintain vocal variety, pacing, and executive presence.',
        sortOrder: 2,
        lessons: [
          {
            id: 'les-comm-4',
            slug: 'hook-story-offer-structure',
            title: 'Hook, Journey, Conclusion Framework',
            estimatedMinutes: 30,
            activityType: 'practical_task',
            description: 'Craft a 3-minute project presentation introduction that captures executive stakeholder interest immediately.'
          },
          {
            id: 'les-comm-5',
            slug: 'handling-qa-deflection',
            title: 'Handling Tough Questions Under Pressure',
            estimatedMinutes: 25,
            activityType: 'conversation',
            description: 'Role-play responding to critical stakeholder pushback while maintaining collaborative composure.'
          }
        ]
      },
      {
        id: 'mod-comm-3',
        title: 'Module 3: Cross-Disciplinary Negotiation & Alignment',
        description: 'Bridge gaps between engineering, design, and business teams with empathetic alignment strategies.',
        sortOrder: 3,
        lessons: [
          {
            id: 'les-comm-6',
            slug: 'diplomatic-reframing',
            title: 'The Art of Diplomatic Reframing',
            estimatedMinutes: 25,
            activityType: 'conversation',
            description: 'Reframe defensive client objections into shared technical problem-solving opportunities.'
          },
          {
            id: 'les-comm-7',
            slug: 'cross-functional-alignment',
            title: 'Consensus Building in Deadlocked Meetings',
            estimatedMinutes: 30,
            activityType: 'practical_task',
            description: 'Evaluate a multi-stakeholder scenario and produce a synthesis memo that aligns conflicting priorities.'
          },
          {
            id: 'les-comm-8',
            slug: 'communication-capstone',
            title: 'Capstone: Executive Project Briefing',
            estimatedMinutes: 40,
            activityType: 'practical_task',
            description: 'Deliver an end-to-end simulated verbal and written briefing on a high-stakes product milestone.'
          }
        ]
      }
    ]
  },
  {
    id: 'course-productivity',
    slug: 'personal-productivity',
    title: 'Personal Productivity and Systems Thinking',
    shortDescription: 'Build enduring task architectures, manage cognitive load, defeat friction, and optimize deep work routines.',
    fullDescription: 'Ditch superficial productivity hacks. This course teaches systematic time allocation, prioritization matrix methods (Eisenhower & Pareto), attention hygiene, and sustainable personal workflows designed for knowledge workers and creators.',
    categoryId: 'productivity',
    categoryName: 'Productivity & Systems',
    level: 'Intermediate',
    estimatedHours: 8,
    modulesCount: 3,
    lessonsCount: 7,
    skillsTaught: ['Time Blocking', 'Cognitive Load Optimization', 'Prioritization Matrices', 'System Audit'],
    learningObjectives: [
      'Design a weekly cadence based on energy cycles rather than clock hours.',
      'Filter incoming requests using high-leverage decision matrices.',
      'Eliminate friction points causing chronic procrastination and context-switching.',
      'Conduct a 30-day productivity system audit to iterate personal workflows.'
    ],
    modules: [
      {
        id: 'mod-prod-1',
        title: 'Module 1: Attention Architecture & Deep Work',
        description: 'Understand attention economics, context switching costs, and the psychology of continuous partial attention.',
        sortOrder: 1,
        lessons: [
          {
            id: 'les-prod-1',
            slug: 'context-switching-audit',
            title: 'The Real Cost of Context Switching',
            estimatedMinutes: 20,
            activityType: 'reading',
            description: 'Analyze cognitive reload times and compute your daily fragmented focus coefficient.'
          },
          {
            id: 'les-prod-2',
            slug: 'designing-deep-work-blocks',
            title: 'Designing Protected Deep Work Blocks',
            estimatedMinutes: 25,
            activityType: 'practical_task',
            description: 'Construct a weekly schedule that preserves uninterrupted 90-minute creative and technical sprints.'
          }
        ]
      },
      {
        id: 'mod-prod-2',
        title: 'Module 2: Prioritization & Decision Frameworks',
        description: 'Separate the genuinely critical from the loudly urgent using proven analytical filtering tools.',
        sortOrder: 2,
        lessons: [
          {
            id: 'les-prod-3',
            slug: 'eisenhower-pareto-matrices',
            title: 'Calibrating Eisenhower & 80/20 Rules',
            estimatedMinutes: 25,
            activityType: 'practical_task',
            description: 'Categorize 20 realistic incoming workplace demands into delegate, eliminate, defer, or execute.'
          },
          {
            id: 'les-prod-4',
            slug: 'saying-no-gracefully',
            title: 'Boundary Enforcement & Graceful Rejections',
            estimatedMinutes: 20,
            activityType: 'conversation',
            description: 'Practice rejecting non-essential meeting invites and low-value asks with respectful firmness.'
          },
          {
            id: 'les-prod-5',
            slug: 'prioritization-checkpoint',
            title: 'Leverage & Priority Assessment',
            estimatedMinutes: 15,
            activityType: 'quiz',
            description: 'Test your ability to spot false emergencies and prioritize compound-return initiatives.'
          }
        ]
      },
      {
        id: 'mod-prod-3',
        title: 'Module 3: Building Frictionless Execution Engines',
        description: 'Translate priorities into friction-free daily execution using digital and physical environment design.',
        sortOrder: 3,
        lessons: [
          {
            id: 'les-prod-6',
            slug: 'friction-audit-elimination',
            title: 'Friction Audit: Spotting Startup Hesitation',
            estimatedMinutes: 30,
            activityType: 'practical_task',
            description: 'Identify micro-barriers in your morning launch ritual and eliminate 3 unnecessary friction points.'
          },
          {
            id: 'les-prod-7',
            slug: 'productivity-operating-system',
            title: 'Capstone: Personal Operating System Manual',
            estimatedMinutes: 45,
            activityType: 'practical_task',
            description: 'Synthesize your task intake, calendar architecture, and weekly review protocol into a 1-page operating manual.'
          }
        ]
      }
    ]
  },
  {
    id: 'course-ui-ux',
    slug: 'ui-ux-design-systems',
    title: 'UI/UX Design Systems and Spatial Hierarchy',
    shortDescription: 'Master color harmony, typography scales, component atomic structures, and accessible interface ergonomics.',
    fullDescription: 'Explore the principles of premium digital product design. Learn how to craft design tokens, manage whitespace, build reusable component libraries, and ensure rigorous WCAG accessibility standards across digital interfaces.',
    categoryId: 'design',
    categoryName: 'Design & Creativity',
    level: 'Intermediate',
    estimatedHours: 9,
    modulesCount: 2,
    lessonsCount: 5,
    skillsTaught: ['Design Token Architecture', 'Spatial Hierarchy', 'Color Theory & Contrast', 'Design System Ergonomics'],
    learningObjectives: [
      'Establish a mathematically consistent 4px/8px spacing and typography scale.',
      'Select and validate high-contrast, functional dark and light palettes meeting WCAG AA.',
      'Design accessible interactive component states (hover, focus, active, disabled).',
      'Document design systems so engineers and designers collaborate without friction.'
    ],
    modules: [
      {
        id: 'mod-design-1',
        title: 'Module 1: Typography & Spatial Rhythms',
        description: 'Scale hierarchies, line heights, letter-spacing, and vertical grid alignment principles.',
        sortOrder: 1,
        lessons: [
          {
            id: 'les-des-1',
            slug: 'modular-type-scales',
            title: 'Constructing Mathematical Type Scales',
            estimatedMinutes: 25,
            activityType: 'practical_task',
            description: 'Select base font sizes and geometric ratios to define responsive desktop and mobile hierarchies.'
          },
          {
            id: 'les-des-2',
            slug: 'whitespace-alignment-rules',
            title: 'Whitespace as an Active Structural Tool',
            estimatedMinutes: 30,
            activityType: 'practical_task',
            description: 'Redesign a cluttered dashboard layout applying 4px baseline grid principles.'
          }
        ]
      },
      {
        id: 'mod-design-2',
        title: 'Module 2: Color Semantics & Component Tokens',
        description: 'Design tokens that map directly into CSS variables for themeable product foundations.',
        sortOrder: 2,
        lessons: [
          {
            id: 'les-des-3',
            slug: 'functional-color-palettes',
            title: 'Functional vs Decorative Color Palettes',
            estimatedMinutes: 25,
            activityType: 'quiz',
            description: 'Audit an existing application interface to eliminate unpurposed decorative colors.'
          },
          {
            id: 'les-des-4',
            slug: 'interactive-state-matrix',
            title: 'The Complete Interactive State Matrix',
            estimatedMinutes: 30,
            activityType: 'practical_task',
            description: 'Specify explicit default, hover, focus-visible, and disabled states for button and input primitives.'
          },
          {
            id: 'les-des-5',
            slug: 'design-tokens-capstone',
            title: 'Capstone: Mini Design System Specification',
            estimatedMinutes: 40,
            activityType: 'practical_task',
            description: 'Deliver a structured design token manifest ready for developer handoff.'
          }
        ]
      }
    ]
  },
  {
    id: 'course-critical-thinking',
    slug: 'critical-thinking-problem-solving',
    title: 'Critical Thinking and First-Principles Problem Solving',
    shortDescription: 'Deconstruct complex dilemmas, spot cognitive biases, model trade-offs, and make sound decisions under uncertainty.',
    fullDescription: 'Become an exceptional problem solver. This course breaks down first-principles reasoning, mental models, cognitive bias mitigation, and structured root-cause analysis across technology, business, and everyday challenges.',
    categoryId: 'thinking',
    categoryName: 'Productivity & Systems',
    level: 'Advanced',
    estimatedHours: 8,
    modulesCount: 2,
    lessonsCount: 5,
    skillsTaught: ['First-Principles Reasoning', 'Root-Cause Analysis', 'Cognitive Bias Mitigation', 'Decision Trees'],
    learningObjectives: [
      'Deconstruct complex assumptions down to their fundamental truths.',
      'Apply the 5 Whys and Ishikawa diagrams to diagnose root causes.',
      'Identify and neutralize confirmation bias and sunk-cost fallacies in strategic decisions.',
      'Quantify risk and expected outcomes using decision tree matrices.'
    ],
    modules: [
      {
        id: 'mod-think-1',
        title: 'Module 1: Mental Models & First Principles',
        description: 'Reason from first principles rather than by analogy. Strip problems of inherited assumptions.',
        sortOrder: 1,
        lessons: [
          {
            id: 'les-th-1',
            slug: 'reasoning-from-first-principles',
            title: 'Deconstructing Analogous Thinking',
            estimatedMinutes: 25,
            activityType: 'reading',
            description: 'Learn how innovators break down established industry dogmas into core physics and economic realities.'
          },
          {
            id: 'les-th-2',
            slug: 'five-whys-root-cause',
            title: 'Root-Cause Analysis via The 5 Whys',
            estimatedMinutes: 30,
            activityType: 'practical_task',
            description: 'Analyze an operational system failure and trace symptomatic errors to root systemic causes.'
          }
        ]
      },
      {
        id: 'mod-think-2',
        title: 'Module 2: Cognitive Biases & Decision Matrices',
        description: 'Shield decisions against emotional distortions, herd mentality, and commitment traps.',
        sortOrder: 2,
        lessons: [
          {
            id: 'les-th-3',
            slug: 'spotting-cognitive-biases',
            title: 'Cognitive Bias Diagnostic',
            estimatedMinutes: 20,
            activityType: 'quiz',
            description: 'Spot availability heuristics, framing effects, and anchoring traps in realistic project deliberations.'
          },
          {
            id: 'les-th-4',
            slug: 'decision-trees-uncertainty',
            title: 'Expected Value & Decision Trees',
            estimatedMinutes: 35,
            activityType: 'practical_task',
            description: 'Map out two competing architectural proposals factoring probability, cost, and consequence.'
          },
          {
            id: 'les-th-5',
            slug: 'critical-thinking-capstone',
            title: 'Capstone: Executive Crisis Decision Memo',
            estimatedMinutes: 45,
            activityType: 'practical_task',
            description: 'Synthesize incomplete data to author a definitive, logically sound strategic course of action.'
          }
        ]
      }
    ]
  }
]

export const COURSE_CATEGORIES = [
  { id: 'all', name: 'All Disciplines' },
  { id: 'tech', name: 'Programming & Web' },
  { id: 'communication', name: 'Communication' },
  { id: 'productivity', name: 'Productivity & Systems' },
  { id: 'design', name: 'Design & Creativity' }
]
