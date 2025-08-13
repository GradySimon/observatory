# Tiltfile for Observatory project

# FastAPI server
local_resource(
    "server",
    serve_cmd="cd server && uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload",
    labels=["backend"],
)

# Next.js client
local_resource("client", serve_cmd="cd client && pnpm run dev", labels=["frontend"])
