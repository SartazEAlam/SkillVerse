# SkillVerse

**Cross-disciplinary interactive skill-learning platform.**

SkillVerse is an immersive learning platform that helps people acquire usable skills through practice — not passive content consumption. It supports programming, communication, business, design, productivity and more through chapter-based learning paths, interactive exercises, realistic simulations and AI-assisted tutoring.

## Status

**Phase 1 — Immersive Design System & Frontend Shell** (completed)

The frontend application shell is implemented with a dark-first design system, responsive navigation, and four main interactive routes (Dashboard, Course Catalog Explore, Interactive Skill Map, and Course Overview with interactive preview).

## Planned Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, TypeScript (strict), Vite, Tailwind CSS v4, Lucide Icons |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy 2.x, Alembic (Phase 2+) |
| Database | PostgreSQL (Phase 2+) |
| Cache / Jobs | Redis, background workers (Phase 2+) |
| Code Execution | Isolated sandbox (Docker-based) (Phase 5) |
| AI | Provider-neutral integration layer (Phase 8) |
| Dev Environment | Docker Compose |

## Repository Structure

```
SkillVerse/
├── docs/                    # Architecture and product documentation
│   ├── PRODUCT.md           # Product vision, personas, requirements
│   ├── ARCHITECTURE.md      # System architecture and decisions
│   ├── DATABASE.md          # Data model documentation
│   ├── API.md               # API endpoint documentation
│   ├── DESIGN_SYSTEM.md     # Visual design principles & tokens
│   ├── SECURITY.md          # Security requirements and policies
│   └── DEVELOPMENT_PLAN.md  # Phased implementation roadmap
├── frontend/                # React + Vite application (Phase 1)
│   ├── src/
│   │   ├── app/             # Application entry and React Router definitions
│   │   ├── components/      # Design system primitives & responsive layout shell
│   │   ├── data/            # Typed course catalog, skills taxonomy, and dashboard demo data
│   │   ├── pages/           # Dashboard, Explore, Skills, Course Overview, 404
│   │   ├── test/            # Vitest unit and integration test suite
│   │   └── types/           # TypeScript contracts for courses, skills, and progress
│   ├── package.json
│   └── vite.config.ts
├── backend/                 # FastAPI application (Phase 2+)
├── AGENTS.md                # Engineering rules for AI-assisted development
├── README.md                # This file
└── .gitignore               # Git ignore rules
```

## Documentation

- [Product Specification](docs/PRODUCT.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Database Design](docs/DATABASE.md)
- [API Reference](docs/API.md)
- [Design System](docs/DESIGN_SYSTEM.md)
- [Security](docs/SECURITY.md)
- [Development Plan](docs/DEVELOPMENT_PLAN.md)

## Getting Started

### Prerequisites
- Node.js 20+ (v24 recommended)
- npm 10+

### Frontend Setup & Development

```bash
# Navigate to the frontend workspace
cd frontend

# Install dependencies
npm install

# Start local development server with hot reload
npm run dev

# Run TypeScript strict type verification
npm run typecheck

# Run Vitest unit and integration test suite
npm run test

# Run fast linter (oxlint)
npm run lint

# Build production bundle
npm run build
```

Once running, open [http://127.0.0.1:5173/](http://127.0.0.1:5173/) in your browser.

## License

All rights reserved. License terms to be determined.
