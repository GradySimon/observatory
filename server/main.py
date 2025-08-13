#!/usr/bin/env python3

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
import io
import pyarrow as pa
from reddit_election_night_2024 import get_reddit_df

app = FastAPI(title="Observatory API - Simple", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global data storage
reddit_df = None

class RedditComment(BaseModel):
    id: str
    author: str
    created_utc: int
    subreddit: str
    parent_id: str
    link_id: str
    score: int
    body: str

class RedditCommentsResponse(BaseModel):
    comments: List[RedditComment]
    total: int
    page: int
    per_page: int

@app.on_event("startup")
async def startup_event():
    """Load Reddit data on startup."""
    global reddit_df
    print("Loading Reddit data...")
    reddit_df = get_reddit_df()
    print(f"Loaded {reddit_df.shape[0]} comments")

@app.get("/")
async def root():
    return {"message": "Observatory API - Simple"}

@app.get("/reddit/comments")
async def get_reddit_comments(
    page: int = 1,
    per_page: int = 100,
    subreddit: Optional[str] = None,
    author: Optional[str] = None,
    min_score: Optional[int] = None,
    format: str = "json"
):
    """Get paginated Reddit comments with filtering."""
    global reddit_df
    
    if reddit_df is None:
        return {"error": "No data loaded"}
    
    # Apply filters
    filtered_df = reddit_df
    
    if subreddit:
        filtered_df = filtered_df.filter(filtered_df["subreddit"] == subreddit)
    
    if author:
        filtered_df = filtered_df.filter(filtered_df["author"] == author)
    
    if min_score is not None:
        filtered_df = filtered_df.filter(filtered_df["score"] >= min_score)
    
    # Sort by score descending
    filtered_df = filtered_df.sort("score", descending=True)
    
    total = filtered_df.shape[0]
    
    # Pagination
    offset = (page - 1) * per_page
    paginated_df = filtered_df.slice(offset, per_page)
    
    if format.lower() == "arrow":
        # Return Arrow format
        # Convert to Arrow table with metadata
        arrow_df = paginated_df.to_arrow()
        
        # Add metadata columns
        arrow_df = arrow_df.append_column(
            'total', pa.array([total] * len(arrow_df))
        ).append_column(
            'page', pa.array([page] * len(arrow_df))
        ).append_column(
            'per_page', pa.array([per_page] * len(arrow_df))
        )
        
        # Serialize to IPC format (Feather)
        buffer = io.BytesIO()
        with pa.ipc.new_file(buffer, arrow_df.schema) as writer:
            writer.write_table(arrow_df)
        
        return Response(
            content=buffer.getvalue(),
            media_type="application/vnd.apache.arrow.file",
            headers={
                "X-Total-Count": str(total),
                "X-Page": str(page),
                "X-Per-Page": str(per_page)
            }
        )
    else:
        # Return JSON format
        comments = []
        for row in paginated_df.to_dicts():
            comments.append(RedditComment(**row))
        
        return RedditCommentsResponse(
            comments=comments,
            total=total,
            page=page,
            per_page=per_page
        )

@app.get("/reddit/subreddits")
async def get_subreddits():
    """Get list of unique subreddits."""
    global reddit_df
    
    if reddit_df is None:
        return []
    
    subreddits = reddit_df.select("subreddit").unique().to_series().to_list()
    return sorted(subreddits)

@app.get("/reddit/loading-status")
async def get_reddit_loading_status():
    """Get the current loading status of Reddit data."""
    global reddit_df
    
    if reddit_df is None:
        return {
            "is_loading": False,
            "progress": 0,
            "message": "No data loaded",
            "total_processed": 0,
            "total_matched": 0,
            "rate": 0
        }
    else:
        return {
            "is_loading": False,
            "progress": 100,
            "message": f"Sample data loaded ({reddit_df.shape[0]} comments)",
            "total_processed": reddit_df.shape[0],
            "total_matched": reddit_df.shape[0],
            "rate": 0
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)