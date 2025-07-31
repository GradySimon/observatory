# Tiltfile for Observatory project

# FastAPI server
local_resource(
    "server",
    serve_cmd="cd server && uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload",
    deps=["server/main.py", "server/pyproject.toml"],
    labels=["backend"]
)

# Next.js client
local_resource(
    "client", 
    serve_cmd="cd client && pnpm run dev",
    deps=["client/src", "client/package.json", "client/next.config.ts"],
    labels=["frontend"]
)
