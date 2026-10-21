# SkillVerse

**Cross-disciplinary interactive skill-learning platform.**

SkillVerse is an immersive learning platform that helps people acquire usable skills through practice — not passive content consumption. It supports programming, communication, business, design, productivity and more through chapter-based learning paths, interactive exercises, realistic simulations and AI-assisted tutoring.

## Status

- **Phase 1 — Immersive Design System & Frontend Shell** (completed)
  The frontend application shell is implemented with a dark-first design system, responsive navigation, and four main interactive routes (Dashboard, Course Catalog Explore, Interactive Skill Map, and Course Overview with interactive preview).
- **Phase 2 — Backend Foundation, Database Infrastructure & Identity** (completed)
  FastAPI application foundation with SQLAlchemy models, Alembic migrations, Argon2id password hashing, JWT access + refresh token rotation, Google OAuth 2.0 PKCE, rate limiting, and profile management (GDPR export, soft delete). Includes frontend auth integration (Login, Register, Profile, AuthContext). *Note: Local automated tests run against SQLite; live PostgreSQL 16 integration is unverified locally due to local Docker daemon unavailability and must be verified in CI/CD.*

## Technology Stack

| Layer | Technology | Status |
|---|---|---|
| Frontend | React 19, TypeScript (strict), Vite, Tailwind CSS v4, Lucide Icons | Implemented (Phase 1 & 2) |
| Backend | Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic, pwdlib[argon2] | Implemented (Phase 2) |
| Database | PostgreSQL 16 (production/Docker), SQLite (local test harness) | Configured |
| Cache / Jobs | Redis 7 (Phase 2 docker-compose ready, Phase 4+ feature use) | Configured |
| Code Execution | Isolated sandbox (Docker-based) | Planned (Phase 5) |
| AI | Provider-neutral integration layer | Planned (Phase 8) |
| Dev Environment | Docker Compose | Configured |

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
├── frontend/                # React + Vite application (Phases 1 & 2)
│   ├── src/
│   │   ├── app/             # Application entry and React Router definitions
│   │   ├── components/      # Design system primitives & responsive layout shell
│   │   ├── context/         # AuthContext and session state
│   │   ├── data/            # Typed course catalog, skills taxonomy, and dashboard demo data
│   │   ├── pages/           # Dashboard, Explore, Skills, Course Overview, Login, Register, Profile, 404
│   │   ├── services/        # API client and token refresh interceptors
│   │   ├── test/            # Vitest unit and integration test suite
│   │   └── types/           # TypeScript contracts for auth, courses, skills, and progress
│   ├── package.json
│   └── vite.config.ts
├── backend/                 # FastAPI application (Phase 2)
│   ├── alembic/             # Versioned database migrations
│   ├── app/
│   │   ├── infrastructure/  # Database session, rate limiter
│   │   ├── modules/         # auth (identity, tokens, oauth) & users (profile, gdpr)
│   │   ├── config.py        # Pydantic Settings with production invariants
│   │   └── main.py          # FastAPI application entry & CORS middleware
│   ├── tests/               # Pytest unit and integration test suite (SQLite test harness)
│   └── pyproject.toml
├── docker-compose.yml       # Local PostgreSQL 16, Redis 7 & API services
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
- Node.js 20+ (v24 recommended) & npm 10+
- Python 3.11+
- Docker Desktop (optional for local PostgreSQL/Redis; SQLite used for local tests when Docker is unavailable)

### Backend Setup & Testing

```bash
# Navigate to the backend workspace
cd backend

# Create and activate a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

# Install dependencies in editable mode
pip install -e ".[dev]"

# Run code style and lint checks with Ruff
ruff check .

# Run all automated tests (executes 46 tests against SQLite test database)
pytest

# Start local development server
uvicorn app.main:app --reload --port 8000
```

*Database Note:* Automated tests use an isolated SQLite test database (`sqlite:///./test.db`). Production environments strictly require PostgreSQL (`DATABASE_URL`), enforced via configuration validator. Docker Compose (`docker-compose up`) starts PostgreSQL 16 and Redis 7.

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

# Run Vitest unit and integration test suite (23 tests)
npm run test

# Run fast linter (oxlint)
npm run lint

# Build production bundle
npm run build
```

Once running, open [http://127.0.0.1:5173/](http://127.0.0.1:5173/) in your browser.

## License

All rights reserved. License terms to be determined.
