"""
Next-Level Web Search Service - Real-Time Data
===============================================
Multi-engine real-time search with auto-updating:
- Tavily API (primary) - Advanced search with answers
- DuckDuckGo (backup) - No API key needed
- Wikipedia (quick facts) - Instant summaries
- Auto-caching for frequently searched topics
- FORCED real-time mode for latest data
"""

import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

# API Keys
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Initialize clients
tavily = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None

# Cache for frequently searched topics
CACHE_FILE = Path("search_cache.json")
CACHE_DURATION = 3600  # 1 hour


def _load_cache():
    """Load search cache from disk."""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}


def _save_cache(cache):
    """Save search cache to disk."""
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)


def _get_cached(query):
    """Get cached search results if fresh."""
    cache = _load_cache()
    key = query.lower().strip()
    if key in cache:
        entry = cache[key]
        if time.time() - entry.get("timestamp", 0) < CACHE_DURATION:
            return entry.get("results")
    return None


def _set_cache(query, results):
    """Cache search results."""
    cache = _load_cache()
    cache[query.lower().strip()] = {
        "results": results,
        "timestamp": time.time()
    }
    if len(cache) > 100:
        oldest = sorted(cache.items(), key=lambda x: x[1]["timestamp"])[:10]
        for k, _ in oldest:
            del cache[k]
    _save_cache(cache)


def search_web(query: str, max_results: int = 5, use_cache: bool = True) -> str:
    """
    Multi-engine web search with auto-fallback.
    
    Args:
        query: Search query
        max_results: Max results to return
        use_cache: Use cached results if available
    
    Returns:
        Formatted search results
    """
    if use_cache:
        cached = _get_cached(query)
        if cached:
            print(f"Using cached results for: {query[:50]}")
            return cached
    
    results = None
    
    if tavily:
        results = _search_tavily(query, max_results)
    
    if not results:
        results = _search_duckduckgo(query, max_results)
    
    if not results:
        results = _search_wikipedia(query)
    
    if not results:
        results = "[No search results found. All search engines unavailable.]"
    
    _set_cache(query, results)
    
    return results


def _search_tavily(query: str, max_results: int) -> str:
    """Search using Tavily API."""
    try:
        response = tavily.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_answer=True,
            include_raw_content=False,
            include_images=False,
        )
        
        parts = []
        
        if response.get("answer"):
            parts.append(f"Answer: {response['answer']}")
        
        for i, r in enumerate(response.get("results", []), 1):
            title = r.get('title', 'Untitled')
            content = r.get('content', '')
            url = r.get('url', '')
            score = r.get('score', 0)
            parts.append(f"{i}. {title}\n   {content[:300]}\n   Source: {url} (relevance: {score:.0%})")
        
        if parts:
            return "\n\n".join(parts)
        return None
    except Exception as e:
        print(f"Tavily error: {e}")
        return None


def _search_duckduckgo(query: str, max_results: int) -> str:
    """Search using DuckDuckGo Instant Answer API."""
    try:
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1,
        }
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        
        parts = []
        
        if data.get("Abstract"):
            parts.append(f"{data['Abstract']}")
            if data.get("AbstractURL"):
                parts[-1] += f"\n   Source: {data['AbstractURL']}"
        
        for topic in data.get("RelatedTopics", [])[:max_results]:
            if isinstance(topic, dict) and topic.get("Text"):
                parts.append(f"• {topic['Text'][:300]}")
                if topic.get("FirstURL"):
                    parts[-1] += f"\n  Source: {topic['FirstURL']}"
        
        if parts:
            return "\n\n".join(parts)
        return None
    except Exception as e:
        print(f"DuckDuckGo error: {e}")
        return None


def _search_wikipedia(query: str) -> str:
    """Search Wikipedia for quick facts."""
    try:
        search_url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "srlimit": 3,
        }
        resp = requests.get(search_url, params=params, timeout=10)
        data = resp.json()
        
        results = data.get("query", {}).get("search", [])
        if results:
            parts = ["Wikipedia Results:"]
            for r in results[:3]:
                title = r.get("title", "")
                snippet = r.get("snippet", "").replace('<span class="searchmatch">', '').replace('</span>', '')
                url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
                parts.append(f"• {title}: {snippet[:300]}\n  Source: {url}")
            return "\n\n".join(parts)
        return None
    except Exception as e:
        print(f"Wikipedia error: {e}")
        return None


def search_news(topic: str = "world", max_results: int = 5) -> str:
    """Search for latest news on a topic."""
    query = f"latest news {topic} {datetime.now().strftime('%B %Y')}"
    return search_web(query, max_results, use_cache=False)


def search_fact(query: str) -> str:
    """Get a quick fact/answer."""
    results = search_web(query, max_results=1)
    return results


def search_with_date_range(query: str, days: int = 7) -> str:
    """Search for recent information within date range."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    enhanced_query = f"{query} after:{date_str} before:{date_str}"
    return search_web(enhanced_query, max_results=5, use_cache=False)


def get_trending_topics() -> str:
    """Get currently trending topics."""
    return search_news("trending topics today", max_results=5)


def is_search_needed(message: str) -> bool:
    """
    Determine if a message needs web search.
    
    Args:
        message: User's message
        
    Returns:
        bool: True if web search is recommended
    """
    search_triggers = [
        "news", "latest", "today", "current", "recent", "breaking",
        "this year", "this month", "this week", "happening", "trending",
        "just in", "update", "updated",
        "who is", "what is", "when did", "where is", "how many",
        "how much", "how old", "how far", "how long",
        "stock", "weather", "price", "cost", "rate", "value",
        "2024", "2025", "2026", "2027", "2028",
        "real-time", "live", "ongoing", "search", "find", "look up",
        "tell me about", "information on", "details about",
    ]
    
    message_lower = message.lower()
    return any(trigger in message_lower for trigger in search_triggers)


def get_current_info() -> str:
    """Get current date, time, and system information."""
    now = datetime.now()
    return f"{now.strftime('%A, %B %d, %Y')} | {now.strftime('%I:%M %p')} | Timezone: {now.astimezone().tzinfo}"


def clear_cache():
    """Clear the search cache."""
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()
    return "Cache cleared"


# ============================================================
# REAL-TIME SEARCH FUNCTIONS (Force Fresh Data)
# ============================================================

def search_realtime(query: str, max_results: int = 5) -> str:
    """Search with FORCED real-time data - no cache, always fresh."""
    return search_web(query, max_results=max_results, use_cache=False)


def search_with_timestamp(query: str) -> str:
    """Search and include timestamp for recency."""
    now = datetime.now()
    results = search_web(query, max_results=5, use_cache=False)
    return f"Last updated: {now.strftime('%I:%M %p, %B %d, %Y')}\n\n{results}"


def auto_search_context(message: str, extra_context: str = "") -> str:
    """Auto-detect if search is needed and return fresh results."""
    auto_triggers = [
        "latest", "current", "today", "now", "recent", "news", "update",
        "2025", "2026", "real-time", "live", "happening", "trending",
        "weather", "stock", "price", "score", "result",
        "who is", "what is", "how many", "how much", "when did",
    ]
    
    combined = (message + " " + extra_context).lower()
    
    if any(trigger in combined for trigger in auto_triggers):
        print("Auto real-time search triggered")
        return search_web(message, max_results=5, use_cache=False)
    
    return None