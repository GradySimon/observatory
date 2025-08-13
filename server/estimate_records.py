#!/usr/bin/env python3
"""
Sample Reddit zst file to understand content and test filtering.
Shows actual comment data and validates filtering logic.
"""

import pathlib
import json
import zstandard as zstd
import time
from datetime import datetime, timezone

def is_election_night_comment(obj: dict) -> bool:
    """Test version of election night filter."""
    # Only top-level comments (replies to posts, not other comments)
    if obj.get('parent_id', '').startswith('t3_'):
        created_utc = obj.get('created_utc', 0)
        # Election Day (Nov 5, 2024 00:00 UTC) to 3am ET Nov 6 (08:00 UTC)
        election_start = 1730764800  # Nov 5, 2024 00:00 UTC
        election_end = 1730880000    # Nov 6, 2024 08:00 UTC (3am ET)
        
        # All top-level comments in this time range, no other filtering
        return election_start <= created_utc <= election_end
    
    return False

def sample_and_analyze(zst_path: pathlib.Path, sample_records: int = 50000):
    """Sample records and analyze content for filtering validation."""
    
    print(f"📊 Analyzing Reddit data: {zst_path}")
    print(f"🔍 Sampling first {sample_records:,} records...")
    print(f"🎯 Election period: Nov 5, 2024 00:00 UTC to Nov 6, 2024 08:00 UTC")
    
    dctx = zstd.ZstdDecompressor(max_window_size=2**31)
    
    # Track various stats
    total_sampled = 0
    top_level_comments = 0
    election_matches = 0
    date_samples = []
    example_comments = []
    example_election_comments = []
    
    start_time = time.time()
    
    with open(zst_path, "rb") as fh:
        with dctx.stream_reader(fh) as reader:
            import io
            text_stream = io.TextIOWrapper(reader, encoding='utf-8')
            
            try:
                for line in text_stream:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    
                    total_sampled += 1
                    
                    # Collect date samples
                    created_utc = obj.get('created_utc', 0)
                    if created_utc > 0 and len(date_samples) < 20:
                        dt = datetime.fromtimestamp(created_utc, tz=timezone.utc)
                        date_samples.append((created_utc, dt.strftime('%Y-%m-%d %H:%M UTC')))
                    
                    # Check if top-level comment
                    parent_id = obj.get('parent_id', '')
                    is_top_level = parent_id.startswith('t3_')
                    
                    if is_top_level:
                        top_level_comments += 1
                        
                        # Test election filter
                        if is_election_night_comment(obj):
                            election_matches += 1
                            if len(example_election_comments) < 3:
                                dt = datetime.fromtimestamp(created_utc, tz=timezone.utc)
                                example_election_comments.append({
                                    'timestamp': dt.strftime('%Y-%m-%d %H:%M UTC'),
                                    'subreddit': obj.get('subreddit', 'unknown'),
                                    'author': obj.get('author', 'unknown'),
                                    'score': obj.get('score', 0),
                                    'body': obj.get('body', '')[:200] + '...' if len(obj.get('body', '')) > 200 else obj.get('body', '')
                                })
                    
                    # Collect example comments
                    if len(example_comments) < 5:
                        dt = datetime.fromtimestamp(created_utc, tz=timezone.utc) if created_utc > 0 else None
                        example_comments.append({
                            'timestamp': dt.strftime('%Y-%m-%d %H:%M UTC') if dt else 'unknown',
                            'subreddit': obj.get('subreddit', 'unknown'),
                            'parent_id': parent_id,
                            'is_top_level': is_top_level,
                            'body': obj.get('body', '')[:100] + '...' if len(obj.get('body', '')) > 100 else obj.get('body', '')
                        })
                    
                    # Stop when we've sampled enough
                    if total_sampled >= sample_records:
                        break
                        
                    # Show progress
                    if total_sampled % 10000 == 0:
                        elapsed = time.time() - start_time
                        rate = total_sampled / elapsed if elapsed > 0 else 0
                        print(f"   Progress: {total_sampled:,} sampled, {top_level_comments:,} top-level, {election_matches} election matches ({rate:.0f}/sec)")
                
            except Exception as e:
                print(f"❌ Error during sampling: {e}")
                return None
    
    elapsed = time.time() - start_time
    
    print(f"\n📊 Sample Analysis Results:")
    print(f"   Total sampled: {total_sampled:,} comments")
    print(f"   Top-level comments: {top_level_comments:,} ({top_level_comments/total_sampled*100:.1f}%)")
    print(f"   Election matches: {election_matches:,}")
    print(f"   Sample rate: {total_sampled/elapsed:.0f} comments/sec")
    
    print(f"\n📅 Date Range in Sample:")
    if date_samples:
        date_samples.sort()
        print(f"   First: {date_samples[0][1]} (timestamp: {date_samples[0][0]})")
        print(f"   Last:  {date_samples[-1][1]} (timestamp: {date_samples[-1][0]})")
    
    print(f"\n💬 Example Comments:")
    for i, comment in enumerate(example_comments, 1):
        print(f"   {i}. [{comment['timestamp']}] r/{comment['subreddit']} - {'TOP-LEVEL' if comment['is_top_level'] else 'REPLY'}")
        print(f"      Parent: {comment['parent_id']}")
        print(f"      Body: {comment['body']}")
        print()
    
    if example_election_comments:
        print(f"🎯 Election Period Matches:")
        for i, comment in enumerate(example_election_comments, 1):
            print(f"   {i}. [{comment['timestamp']}] r/{comment['subreddit']} by u/{comment['author']} (score: {comment['score']})")
            print(f"      Body: {comment['body']}")
            print()
    else:
        print(f"🎯 No election period matches found in sample")
    
    return {
        "total_sampled": total_sampled,
        "top_level_comments": top_level_comments,
        "election_matches": election_matches,
        "sample_rate": total_sampled/elapsed if elapsed > 0 else 0
    }

if __name__ == "__main__":
    zst_file = pathlib.Path("/Users/grady/reddit-dumps/reddit/comments/RC_2024-11.zst")
    
    if not zst_file.exists():
        print(f"❌ File not found: {zst_file}")
    else:
        sample_and_analyze(zst_file)