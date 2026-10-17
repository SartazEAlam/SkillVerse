# SkillVerse

**Cross-disciplinary interactive skill-learning platform.**

SkillVerse is an immersive learning platform that helps people acquire usable skills through practice — not passive content consumption. It supports programming, communication, business, design, productivity and more through chapter-based learning paths, interactive exercises, realistic simulations and AI-assisted tutoring.

## Status

**Phase 0 — Planning & Architecture** (current)

No application code has been implemented yet. This repository contains product specifications, architecture documentation and a phased implementation roadmap.

## Planned Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript (strict), Vite, Tailwind CSS, shadcn/ui, Radix UI, Motion |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy 2.x, Alembic |
| Database | PostgreSQL |
| Cache / Jobs | Redis, background workers |
| Code Execution | Isolated sandbox (Docker-based) |
| AI | Provider-neutral integration layer |
| Dev Environment | Docker Compose |

## Repository Structure

```
SkillVerse/
├── docs/                    # Architecture and product documentation
│   ├── PRODUCT.md           # Product vision, personas, requirements
│   ├── ARCHITECTURE.md      # System architecture and decisions
│   ├── DATABASE.md          # Data model documentation
│   ├── API.md               # API endpoint documentation
│   ├── DESIGN_SYSTEM.md     # Visual design principles
│   ├── SECURITY.md          # Security requirements and policies
│   └── DEVELOPMENT_PLAN.md  # Phased implementation roadmap
├── frontend/                # React + Vite application (Phase 1+)
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

Phase 0 is documentation-only. Application setup instructions will be added when implementation begins in Phase 1.

## License

All rights reserved. License terms to be determined.
