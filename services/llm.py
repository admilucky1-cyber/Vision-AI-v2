"""
Vision AI v2.0 - AI Provider Router
====================================
Multi-provider LLM integration with intelligent failover.
Supports Gemini, DeepSeek, Groq, and OpenRouter with auto-routing.

Priority Order (Auto Mode):
1. Gemini 1.5 Pro (Primary - 2M context, highest free limits)
2. Gemini 1.5 Flash (Secondary - 2M context, fast)
3. DeepSeek V3 (Free powerful backup)
4. Gemini 2.5 Flash (Ultra-reliable)
5. Groq Llama 3.3 (Speed fallback)
6. OpenRouter Free Models (Last resort)
"""

import os
import re
import requests
import json
from typing import Optional, Dict, List
from dotenv import load_dotenv

load_dotenv()

# ==========================================================
# PROVIDER CONFIGURATION
# ==========================================================

# Gemini Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_AVAILABLE = False

try:
    import google.genai as genai
    if GOOGLE_API_KEY:
        gemini_client = genai.Client(api_key=GOOGLE_API_KEY)
        GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# DeepSeek Configuration
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_AVAILABLE = bool(DEEPSEEK_API_KEY)

# Groq Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_AVAILABLE = bool(GROQ_API_KEY)

# OpenRouter Configuration
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_AVAILABLE = bool(OPENROUTER_KEY)

# ==========================================================
# MODEL DEFINITIONS
# ==========================================================

GEMINI_MODELS = {
    # 🔥 Updated to prioritize models with the highest free limits and largest context
    "gemini-1.5-pro": {"name": "Gemini 1.5 Pro", "tokens": 2000000, "priority": 1},
    "gemini-1.5-flash": {"name": "Gemini 1.5 Flash", "tokens": 2000000, "priority": 2},
    "gemini-2.5-flash": {"name": "Gemini 2.5 Flash", "tokens": 1048576, "priority": 3},
    "gemini-2.5-pro": {"name": "Gemini 2.5 Pro", "tokens": 1048576, "priority": 4},
    "gemini-2.0-flash": {"name": "Gemini 2.0 Flash", "tokens": 1048576, "priority": 5},
}

OPENROUTER_MODELS = [
    {"id": "meta-llama/llama-3.3-70b-instruct:free", "name": "Llama 3.3 70B", "tokens": 131072},
    {"id": "google/gemma-4-31b-it:free", "name": "Gemma 4 31B", "tokens": 131072},
    {"id": "qwen/qwen3-next-80b-a3b-instruct:free", "name": "Qwen3 Next 80B", "tokens": 131072},
    {"id": "nousresearch/hermes-3-llama-3.1-405b:free", "name": "Hermes 3 405B", "tokens": 131072},
    {"id": "openai/gpt-oss-120b:free", "name": "GPT-OSS 120B", "tokens": 131072},
]

# ==========================================================
# SUBJECT DETECTION
# ==========================================================

SUBJECT_KEYWORDS = {
    "english": ["english", "grammar", "ielts", "toefl", "vocabulary", "essay", "writing", "reading", "comprehension", "sentence", "verb", "tense", "noun", "adjective", "adverb", "preposition"],
    "physics": ["physics", "force", "velocity", "acceleration", "magnetic", "electric", "circuit", "wave", "energy", "momentum", "gravity", "newton", "ohm", "voltage", "refraction", "quantum", "speed", "motion", "mass", "friction", "pressure", "density", "frequency", "wavelength"],
    "chemistry": ["chemistry", "chemical", "reaction", "molecule", "atom", "element", "compound", "acid", "base", "organic", "periodic", "bond", "ion", "catalyst", "equilibrium", "oxidation", "reduction", "titration", "solution", "concentration", "ph", "electrolysis"],
    "biology": ["biology", "cell", "dna", "protein", "gene", "organism", "photosynthesis", "respiration", "enzyme", "mitosis", "meiosis", "evolution", "ecology", "anatomy", "physiology", "species", "ecosystem", "bacteria", "virus", "plant", "animal", "organ", "tissue"],
    "mathematics": ["math", "algebra", "calculus", "geometry", "trigonometry", "equation", "function", "derivative", "integral", "matrix", "vector", "probability", "statistics", "theorem", "angle", "triangle", "circle", "graph", "coordinate", "polynomial"],
    "engineering": ["engineering", "mechanical", "civil", "electrical", "structural", "thermodynamic", "fluid", "material", "design", "manufacturing", "circuit", "signal", "control system", "motor", "generator", "transformer", "load", "stress", "strain"],
    "computer_science": ["programming", "algorithm", "code", "software", "hardware", "database", "network", "ai", "machine learning", "data structure", "python", "java", "c++", "web", "app", "function", "class", "object", "api", "server", "client"],
    "medicine": ["medicine", "diagnosis", "treatment", "symptom", "disease", "surgery", "pharma", "clinical", "patient", "anatomy", "pathology", "radiology", "cardiology", "neurology", "pediatrics"],
    "history": ["history", "ancient", "medieval", "modern", "war", "revolution", "empire", "civilization", "century", "timeline", "historical", "king", "queen", "dynasty", "battle", "treaty"],
    "geography": ["geography", "climate", "weather", "map", "continent", "ocean", "river", "mountain", "population", "urban", "rural", "country", "capital", "latitude", "longitude", "equator"],
    "economics": ["economics", "supply", "demand", "market", "inflation", "gdp", "finance", "investment", "trade", "monetary", "fiscal", "business", "cost", "revenue", "profit"],
    "literature": ["literature", "poem", "novel", "story", "character", "plot", "theme", "author", "poet", "fiction", "drama", "shakespeare", "chapter", "verse", "prose", "narrative", "sonnet", "essay"],
    "religious_studies": ["quran", "bible", "holy", "god", "allah", "prophet", "religion", "islam", "christianity", "hindu", "buddhist", "verse", "scripture", "surah", "ayah", "prayer", "worship", "faith", "spiritual", "mosque", "church", "temple", "torah", "gospel"],
}

def detect_subject(question: str, context: str = "", filename: str = "") -> str:
    """Detect subject from filename, question, and context."""
    if filename:
        filename_lower = filename.lower()
        for subject, keywords in SUBJECT_KEYWORDS.items():
            if any(kw in filename_lower for kw in keywords):
                return subject

    combined = (question + " " + context[:5000]).lower()
    scores = {}
    for subject, keywords in SUBJECT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in combined)
        if score > 0:
            scores[subject] = score

    return max(scores, key=scores.get) if scores else "general"

# ==========================================================
# PROMPT ENGINEERING (UPDATED FOR CONVERSATIONAL TONE)
# ==========================================================

def get_professional_prompt(subject: str) -> str:
    """
    Get subject-specific system prompt.
    Forces a warm, natural, and human-like conversational tone.
    """
    
    # 🔥 Updated to remove "expert educator" and "dictionary style"
    base_rules = """
You are a friendly, helpful, and natural conversational assistant. 
You must follow these rules STRICTLY:

1. BE CONVERSATIONAL: Do not start with "As an expert educator" or provide dictionary definitions.
2. RESPOND NATURALLY: Talk like a human friend. Use "I", "you", and contractions (don't, can't, I'll).
3. SIMPLE & CLEAR: Use short paragraphs. Use bullet points only when listing items.
4. POLISHED ANSWER: Give a complete, warm, and thoughtful response. Do not just give a 3-word answer.
5. LANGUAGE: If the user speaks in Urdu, reply in Pure Pakistani Urdu. If they speak in English, reply in warm, natural English.
6. CONTEXT: ALWAYS refer to the provided context and uploaded files when answering. Do not give generic answers if context exists.
"""
    return base_rules

# ==========================================================
# AI PROVIDER FUNCTIONS
# ==========================================================

def ask_gemini(question: str, context: str = "", model_id: str = "gemini-1.5-pro") -> Optional[str]:
    """Send question to Gemini API."""
    try:
        import google.genai as genai
        
        if not GEMINI_AVAILABLE or not GOOGLE_API_KEY:
            return None

        client = genai.Client(api_key=GOOGLE_API_KEY)
        subject = detect_subject(question, context)
        system_prompt = get_professional_prompt(subject)

        prompt = f"""{system_prompt}

Context:
{context[:50000]}

User Question:
{question}

Provide a natural, warm, and thoughtful response."""

        response = client.models.generate_content(model=model_id, contents=prompt)
        if response and response.text:
            return response.text.strip()
        return None
    except Exception as e:
        print(f"Gemini error: {str(e)[:100]}")
        return None

def ask_deepseek(question: str, context: str = "") -> Optional[str]:
    """Send question to DeepSeek API."""
    if not DEEPSEEK_AVAILABLE:
        return None

    try:
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": get_professional_prompt("general")},
                {"role": "user", "content": f"Context: {context[:4000]}\n\nQuestion: {question}"}
            ],
            "temperature": 0.7,
            "max_tokens": 4096,
        }

        resp = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=payload, timeout=45)

        if resp.status_code == 200:
            data = resp.json()
            if "choices" in data and len(data["choices"]) > 0:
                result = data["choices"][0]["message"]["content"].strip()
                if result and len(result) > 20:
                    return result
        return None
    except Exception as e:
        print(f"DeepSeek error: {str(e)[:100]}")
        return None

def ask_groq(question: str, context: str = "") -> Optional[str]:
    """Send question to Groq API."""
    if not GROQ_AVAILABLE:
        return None

    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": get_professional_prompt("general")},
                {"role": "user", "content": f"Context: {context[:4000]}\n\nQuestion: {question}"}
            ],
            "temperature": 0.7,
            "max_tokens": 4096,
        }

        resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=30)

        if resp.status_code == 200:
            data = resp.json()
            if "choices" in data and len(data["choices"]) > 0:
                result = data["choices"][0]["message"]["content"].strip()
                if result and len(result) > 20:
                    return result
        return None
    except Exception as e:
        print(f"Groq error: {str(e)[:100]}")
        return None

def ask_openrouter(question: str, context: str = "") -> Optional[str]:
    """Send question to OpenRouter free models."""
    if not OPENROUTER_AVAILABLE:
        return None

    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://vision-ai.app",
        "X-Title": "Vision AI",
    }

    for model_info in OPENROUTER_MODELS:
        try:
            payload = {
                "model": model_info["id"],
                "messages": [
                    {"role": "system", "content": get_professional_prompt("general")},
                    {"role": "user", "content": f"Context: {context[:4000]}\n\nQuestion: {question}"}
                ],
                "temperature": 0.7,
                "max_tokens": 4096,
            }

            resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=30)

            if resp.status_code == 200:
                data = resp.json()
                if "choices" in data and len(data["choices"]) > 0:
                    result = data["choices"][0]["message"]["content"].strip()
                    if result and len(result) > 20:
                        return result
        except:
            continue

    return None

# ==========================================================
# MAIN AI ROUTER
# ==========================================================

def ask_ai(question: str, context: str = "", backend: str = "auto") -> str:
    """
    Universal AI router with intelligent failover.

    Args:
        question: User question
        context: Additional context (RAG, search results)
        backend: Preferred backend (auto, gemini, groq, deepseek, openrouter)

    Returns:
        AI-generated response or error message
    """
    print(f"\n{'='*50}")
    print(f"AI Request: {question[:80]}...")
    print(f"Backend: {backend}")
    print(f"{'='*50}")

    providers = []

    if backend == "auto":
        # 🔥 Updated priority list: Gemini 1.5 Pro is now first
        providers = [
            ("gemini-1.5-pro", lambda q, c: ask_gemini(q, c, "gemini-1.5-pro")),
            ("gemini-1.5-flash", lambda q, c: ask_gemini(q, c, "gemini-1.5-flash")),
            ("deepseek", ask_deepseek),
            ("gemini-2.5-flash", lambda q, c: ask_gemini(q, c, "gemini-2.5-flash")),
            ("gemini-2.5-pro", lambda q, c: ask_gemini(q, c, "gemini-2.5-pro")),
            ("gemini-2.0-flash", lambda q, c: ask_gemini(q, c, "gemini-2.0-flash")),
            ("groq", ask_groq),
            ("openrouter", ask_openrouter),
        ]
    elif backend == "gemini":
        providers = [
            ("gemini-1.5-pro", lambda q, c: ask_gemini(q, c, "gemini-1.5-pro")),
            ("gemini-1.5-flash", lambda q, c: ask_gemini(q, c, "gemini-1.5-flash")),
            ("gemini-2.5-flash", lambda q, c: ask_gemini(q, c, "gemini-2.5-flash")),
            ("gemini-2.5-pro", lambda q, c: ask_gemini(q, c, "gemini-2.5-pro")),
            ("gemini-2.0-flash", lambda q, c: ask_gemini(q, c, "gemini-2.0-flash")),
        ]
    elif backend == "deepseek":
        providers = [("deepseek", ask_deepseek)]
    elif backend == "groq":
        providers = [("groq", ask_groq)]
    elif backend == "openrouter":
        providers = [("openrouter", ask_openrouter)]
    else:
        providers = [
            ("gemini-1.5-pro", lambda q, c: ask_gemini(q, c, "gemini-1.5-pro")),
            ("gemini-1.5-flash", lambda q, c: ask_gemini(q, c, "gemini-1.5-flash")),
            ("deepseek", ask_deepseek),
            ("groq", ask_groq),
        ]

    for provider_name, provider_func in providers:
        try:
            result = provider_func(question, context)
            if result and len(result) > 20 and not result.startswith("[Error"):
                print(f"  Success: {provider_name} ({len(result)} chars)")
                return result
        except Exception as e:
            print(f"  {provider_name} failed: {str(e)[:80]}")
            continue

    return "[Error: All AI models unavailable. Please check your API keys and internet connection.]"

# ==========================================================
# GEMINI IMAGE GENERATION
# ==========================================================

async def generate_image_gemini(prompt: str, model_id: str = "gemini-1.5-pro") -> dict:
    """Generate image using Gemini."""
    if not GEMINI_AVAILABLE:
        return {"success": False, "error": "Gemini not available"}

    try:
        import base64
        import google.genai as genai
        
        client = genai.Client(api_key=GOOGLE_API_KEY)

        enhanced_prompt = (
            f"Generate a professional educational diagram: {prompt}. "
            f"Clean white background, English labels only, textbook quality, "
            f"bold fonts, clear lines, professional design, high resolution."
        )

        response = client.models.generate_content(model=model_id, contents=enhanced_prompt)

        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    image_base64 = base64.b64encode(part.inline_data.data).decode('utf-8')
                    if len(image_base64) > 1000:
                        return {"success": True, "image_data": image_base64, "provider": f"Gemini ({model_id})"}

        return {"success": False, "error": "No image in response"}
    except Exception as e:
        return {"success": False, "error": str(e)}