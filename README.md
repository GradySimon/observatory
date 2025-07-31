# Observatory

A full-stack application with FastAPI backend and Next.js frontend.

## Project Structure

```
observatory/
├── server/          # FastAPI backend with uv dependency management
│   ├── main.py      # FastAPI application with Pydantic models
│   ├── pyproject.toml
│   └── uv.lock
├── client/          # Next.js frontend with TypeScript and Tailwind
│   ├── src/
│   │   ├── app/     # Next.js 13+ app directory
│   │   ├── components/
│   │   ├── lib/     # API client
│   │   └── stores/  # Zustand state management
│   └── package.json
└── Tiltfile         # Development environment management
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- [pnpm](https://pnpm.io/) for JavaScript package management
- [uv](https://github.com/astral-sh/uv) for Python dependency management
- [Tilt](https://tilt.dev/) for development environment (optional)

### Development

#### Option 1: Using Tilt (Recommended)

```bash
tilt up
```

This will start both services:
- FastAPI server on http://localhost:8000
- Next.js client on http://localhost:3000

#### Option 2: Manual Setup

**Start the FastAPI server:**

```bash
cd server
uv sync
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Start the Next.js client:**

```bash
cd client
pnpm install
pnpm run dev
```

## API Endpoints

- `GET /` - API status
- `GET /items` - List all items
- `GET /items/{id}` - Get specific item
- `POST /items` - Create new item
- `PUT /items/{id}` - Update item
- `DELETE /items/{id}` - Delete item

## Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Pydantic** - Data validation using Python type annotations
- **uvicorn** - ASGI server
- **uv** - Fast Python package installer and resolver

### Frontend
- **Next.js 13+** - React framework with app directory
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **Zustand** - Lightweight state management

### Development
- **Tilt** - Multi-service development environment