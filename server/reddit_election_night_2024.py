# reddit_election_night_2024.py
# Python ≥ 3.10  •  pip install torrentp polars zstandard tqdm

from __future__ import annotations

import datetime as dt
import json
import pathlib
import shutil
import tempfile
from typing import Callable, Iterator

import polars as pl
import zstandard as zstd
from tqdm.auto import tqdm

# Optional torrent support
try:
    from torrentp import TorrentDownloader

    TORRENT_AVAILABLE = True
except ImportError:
    TORRENT_AVAILABLE = False
    TorrentDownloader = None

# --------------------------------------------------------------------
# 1.  Configuration
# --------------------------------------------------------------------
DATA_DIR = pathlib.Path("~/reddit-dumps").expanduser()

# Use bundled torrent file
MODULE_DIR = pathlib.Path(__file__).parent
TORRENT_FILE = MODULE_DIR / "data" / "reddit-2024-11.torrent"
ELECTION_START = dt.datetime(2024, 11, 5, 0, 0, 0, tzinfo=dt.timezone.utc)
ELECTION_END = dt.datetime(2024, 11, 6, 6, 0, 0, tzinfo=dt.timezone.utc)
COMMENT_FILENAME = "reddit/comments/RC_2024-11.zst"  # inside the torrent


# --------------------------------------------------------------------
# 2.  Torrent download helper
# --------------------------------------------------------------------
def download_dump(magnet_or_url: str, target_dir: pathlib.Path) -> pathlib.Path:
    """Download the torrent if we don't have it yet and return the .zst path."""
    if not TORRENT_AVAILABLE:
        raise ImportError(
            "torrentp package not available. Install with: pip install torrentp"
        )

    target_dir.mkdir(parents=True, exist_ok=True)
    zst_path = target_dir / COMMENT_FILENAME
    if zst_path.exists():
        print(f"Found existing file: {zst_path}")
        return zst_path

    print(f"File not found at {zst_path}")
    print("Please download the torrent manually using a CLI client:")
    print(f"  aria2c '{magnet_or_url}' -d '{target_dir}'")
    print("  or")
    print(f"  transmission-cli '{magnet_or_url}' -w '{target_dir}'")
    print(f"Expected file location: {zst_path}")
    
    raise FileNotFoundError(
        f"Reddit data file not found. Please download the torrent manually to: {zst_path}"
    )


# --------------------------------------------------------------------
# 3.  Streaming loader -> Polars
# --------------------------------------------------------------------
def stream_jsonlines(zst_path: pathlib.Path) -> Iterator[dict]:
    """Yield dicts **on‑the‑fly** without unpacking the whole archive."""
    dctx = zstd.ZstdDecompressor(max_window_size=2**31)
    with open(zst_path, "rb") as fh:
        with dctx.stream_reader(fh) as reader:
            # Use TextIOWrapper to handle the decompressed stream as text
            import io
            text_stream = io.TextIOWrapper(reader, encoding='utf-8')
            try:
                for line in text_stream:
                    line = line.strip()
                    if not line:
                        continue
                    yield json.loads(line)
            except Exception as e:
                print(f"Error reading stream: {e}")
                raise


def load_reddit_comments(
    zst_path: pathlib.Path,
    row_pred: Callable[[dict], bool] | None = None,
    projected_fields: tuple[str, ...] = (
        "id",
        "author",
        "created_utc",
        "subreddit",
        "parent_id",
        "link_id",
        "score",
        "body",
    ),
    progress_callback: Callable[[int, int, float], None] | None = None,
) -> pl.DataFrame:
    """Convert NDJSON → Polars, selecting rows *and* columns as we stream."""

    def rows():
        import time
        start_time = time.time()
        processed_count = 0
        filtered_count = 0
        
        print(f"📡 Starting to stream Reddit data from: {zst_path}")
        print(f"🔍 Filtering criteria: {row_pred.__name__ if row_pred else 'None (all rows)'}")
        
        for obj in tqdm(stream_jsonlines(zst_path), desc="📊 Processing", unit=" comments"):
            processed_count += 1
            
            if row_pred is None or row_pred(obj):
                filtered_count += 1
                # project + cast here to keep memory low
                yield {k: obj[k] for k in projected_fields}
                
            # Log progress every 100k processed comments
            if processed_count % 100000 == 0:
                elapsed = time.time() - start_time
                rate = processed_count / elapsed
                print(f"📈 Progress: {processed_count:,} processed, {filtered_count:,} matched ({rate:.0f} comments/sec)")
                
                # Call progress callback if provided
                if progress_callback:
                    progress_callback(processed_count, filtered_count, rate)
        
        total_elapsed = time.time() - start_time
        final_rate = processed_count / total_elapsed
        print(f"✅ Streaming complete: {processed_count:,} total processed, {filtered_count:,} matched in {total_elapsed:.1f}s ({final_rate:.0f} comments/sec)")

    # Polars can ingest an iterator of dicts
    return pl.from_dicts(rows())


# --------------------------------------------------------------------
# 4.  Example election‑night predicates & transforms
# --------------------------------------------------------------------
def is_top_level_election_night(obj: dict) -> bool:
    """True ⇔ top‑level comment *and* timestamp inside the window."""
    ts = dt.datetime.fromtimestamp(obj["created_utc"], tz=dt.timezone.utc)
    return obj["parent_id"].startswith("t3_") and ELECTION_START <= ts < ELECTION_END


# --------------------------------------------------------------------
# 5.  High‑level convenience façade
# --------------------------------------------------------------------
def get_reddit_df(
    torrent_source: str = None,
    dest_dir: pathlib.Path = DATA_DIR,
    row_pred: Callable[[dict], bool] = is_top_level_election_night,
    use_sample_data: bool = False,
    progress_callback: Callable[[int, int, float], None] | None = None,
) -> pl.DataFrame:
    """Download (if necessary) + load + filter = Polars DF."""
    if use_sample_data:
        print("Using sample data (requested)")
        return get_sample_data()

    # First, check for pre-processed parquet files (much faster!)
    processed_dir = dest_dir / "processed"
    parquet_path = processed_dir / "election_comments.parquet"
    
    if parquet_path.exists():
        print(f"🚀 Found pre-processed parquet file: {parquet_path}")
        print("Loading optimized data (this should be very fast)...")
        try:
            df = pl.read_parquet(parquet_path)
            print(f"✅ Loaded {df.shape[0]:,} pre-processed comments from parquet")
            return df
        except Exception as e:
            print(f"⚠️  Error loading parquet file: {e}")
            print("Falling back to raw data processing...")

    # Fallback to raw data processing
    # Use bundled torrent file by default
    if not torrent_source:
        if TORRENT_FILE.exists():
            torrent_source = str(TORRENT_FILE)
            print(f"Using bundled torrent file: {TORRENT_FILE}")
        else:
            print("No torrent file found, using sample data")
            return get_sample_data()

    # Check if raw data exists
    zst_path = dest_dir / COMMENT_FILENAME
    if zst_path.exists():
        print(f"Found existing Reddit raw data: {zst_path}")
        print("⚠️  This will take several minutes to process. Consider running the download script with processing enabled.")
        return load_reddit_comments(zst_path, row_pred=row_pred, progress_callback=progress_callback)

    print(f"Reddit data not found at: {zst_path}")
    print("Please run the download script first:")
    print(f"  ./server/scripts/download_reddit_data")
    print("Falling back to sample data for development...")
    return get_sample_data()


def get_sample_data() -> pl.DataFrame:
    """Generate sample Reddit election data for development."""
    import random

    subreddits = [
        "politics",
        "Conservative",
        "news",
        "worldnews",
        "PoliticalDiscussion",
    ]
    authors = [f"user_{i}" for i in range(100)]

    sample_comments = []
    base_time = ELECTION_START.timestamp()

    for i in range(1000):
        timestamp = base_time + random.randint(
            0, int((ELECTION_END - ELECTION_START).total_seconds())
        )
        sample_comments.append(
            {
                "id": f"comment_{i}",
                "author": random.choice(authors),
                "created_utc": int(timestamp),
                "subreddit": random.choice(subreddits),
                "parent_id": f"t3_post_{random.randint(1, 100)}",
                "link_id": f"t3_post_{random.randint(1, 100)}",
                "score": random.randint(-50, 500),
                "body": f"Sample election comment {i}. This is discussing the 2024 election results and various political topics.",
            }
        )

    return pl.from_dicts(sample_comments)


# --------------------------------------------------------------------
# 6.  Usage example
# --------------------------------------------------------------------
if __name__ == "__main__":
    df = get_reddit_df()
    print(df.shape)
    print(df.head())

    # …later you can plug in *any* transformation:
    #   df2 = get_reddit_df(row_pred=lambda o: o["subreddit"] == "politics")
