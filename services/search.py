"""
Vision AI v2.0 - Web Search Service
====================================
Multi-engine real-time search with intelligent caching.

Engines:
- Tavily API (primary): Advanced AI search with answers
- DuckDuckGo (backup): No API key needed
- Wikipedia (quick facts): Instant summaries

Features:
- Auto-caching with TTL
- Forced real-time mode
- Multi-engine fallback
"""

import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# ==========================================================
# CONFIGURATION
# ==========================================================
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
CACHE_FILE = Path("search_cache.json")
CACHE_DURATION = 3600  # 1 hour
MAX_CACHE_SIZE = 100

# ==========================================================
# TAVILY CLIENT
# ==========================================================
try:
    from tavily import TavilyClient
    tavily = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None
except ImportError:
    tavily = None

# ==========================================================
# CACHE MANAGEMENT
# ==========================================================
class SearchCache:
    """Persistent search cache with TTL and LRU eviction."""

    def __init__(self, cache_file: Path = CACHE_FILE, duration: int = CACHE_DURATION):
        self._cache_file = cache_file
        self._duration = duration
        self._cache = self._load()

    def _load(self) -> dict:
        if self._cache_file.exists():
            try:
                with open(self._cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save(self):
        try:
            with open(self._cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, indent=2)
        except IOError:
            pass

    def get(self, query: str) -> Optional[str]:
        key = query.lower().strip()
        entry = self._cache.get(key)
        if entry and time.time() - entry.get("timestamp", 0) < self._duration:
            return entry.get("results")
        return None

    def set(self, query: str, results: str):
        key = query.lower().strip()
        self._cache[key] = {"results": results, "timestamp": time.time()}

        # LRU eviction
        if len(self._cache) > MAX_CACHE_SIZE:
            oldest = sorted(self._cache.items(), key=lambda x: x[1]["timestamp"])[:10]
            for k, _ in oldest:
                del self._cache[k]

        self._save()

    def clear(self):
        self._cache.clear()
        if self._cache_file.exists():
            self._cache_file.unlink()

search_cache = SearchCache()

# ==========================================================
# SEARCH FUNCTIONS
# ==========================================================

def search_tavily(query: str, max_results: int = 5) -> Optional[str]:
    """Search using Tavily API."""
    if not tavily:
        return None

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

        return "\n\n".join(parts) if parts else None
    except Exception as e:
        print(f"Tavily error: {e}")
        return None

def search_duckduckgo(query: str, max_results: int = 5) -> Optional[str]:
    """Search using DuckDuckGo Instant Answer API."""
    try:
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1,
        }
        headers = {"User-Agent": "VisionAI/2.0"}
        
        resp = requests.get(url, params=params, headers=headers, timeout=10)
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

        return "\n\n".join(parts) if parts else None
    except requests.exceptions.Timeout:
        print("DuckDuckGo search timed out.")
        return None
    except Exception as e:
        print(f"DuckDuckGo error: {e}")
        return None

def search_wikipedia(query: str) -> Optional[str]:
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
        headers = {"User-Agent": "VisionAI/2.0"}
        
        resp = requests.get(search_url, params=params, headers=headers, timeout=10)
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
    except requests.exceptions.Timeout:
        print("Wikipedia search timed out.")
        return None
    except Exception as e:
        print(f"Wikipedia error: {e}")
        return None

# ==========================================================
# MAIN SEARCH FUNCTION
# ==========================================================

def search_web(query: str, max_results: int = 5, use_cache: bool = True) -> str:
    """
    Multi-engine web search with auto-fallback.

    Args:
        query: Search query
        max_results: Maximum results to return
        use_cache: Use cached results if available

    Returns:
        Formatted search results or error message
    """
    # 🔥 Force bypass cache for real-time data queries
    if "weather" in query.lower() or "time" in query.lower() or "date" in query.lower():
        use_cache = False

    if use_cache:
        cached = search_cache.get(query)
        if cached:
            print(f"🔍 Returning cached results for: {query}")
            return cached

    print(f"🔍 Performing fresh web search for: {query}")

    results = None

    # Try Tavily first
    if tavily:
        print("   Trying Tavily API...")
        results = search_tavily(query, max_results)
        if results:
            print("   ✅ Tavily returned results.")
            if use_cache:
                search_cache.set(query, results)
            return results

    # Fallback to DuckDuckGo
    if not results:
        print("   Trying DuckDuckGo...")
        results = search_duckduckgo(query, max_results)
        if results:
            print("   ✅ DuckDuckGo returned results.")
            if use_cache:
                search_cache.set(query, results)
            return results

    # Fallback to Wikipedia
    if not results:
        print("   Trying Wikipedia...")
        results = search_wikipedia(query)
        if results:
            print("   ✅ Wikipedia returned results.")
            if use_cache:
                search_cache.set(query, results)
            return results

    if not results:
        print("   ❌ All search engines failed.")
        results = "[No search results found. All search engines unavailable.]"
        if use_cache:
            search_cache.set(query, results)

    return results

# ==========================================================
# UTILITY FUNCTIONS
# ==========================================================

def is_search_needed(message: str) -> bool:
    """Determine if a message needs web search."""
    triggers = [
        "news", "latest", "today", "current", "recent", "breaking",
        "this year", "this month", "this week", "happening", "trending",
        "who is", "what is", "when did", "where is", "how many",
        "how much", "how old", "stock", "weather", "price", "cost",
        "2024", "2025", "2026", "2027", "2028",
        "real-time", "live", "ongoing", "search", "find", "look up",
    ]
    return any(trigger in message.lower() for trigger in triggers)

def get_current_info() -> str:
    """Get current date and time."""
    now = datetime.now()
    return f"{now.strftime('%A, %B %d, %Y')} | {now.strftime('%I:%M %p')}"

def auto_search_context(message: str, extra_context: str = "") -> Optional[str]:
    """Auto-detect if search is needed and return fresh results."""
    triggers = [
        "latest", "current", "today", "now", "recent", "news", "update",
        "2025", "2026", "real-time", "live", "happening", "trending",
        "weather", "stock", "price", "score", "result",
        "who is", "what is", "how many", "how much", "when did",
    ]

    combined = (message + " " + extra_context).lower()

    if any(trigger in combined for trigger in triggers):
        return search_web(message, max_results=5, use_cache=False)

    return None

def clear_search_cache():
    """Clear the search cache."""
    search_cache.clear()
    return "Search cache cleared"