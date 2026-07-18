import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# GEMINI CONFIGURATION (Your Key - PRIMARY)
# ============================================================
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_AVAILABLE = False

if GOOGLE_API_KEY:
    try:
        import google.genai as genai
        client = genai.Client(api_key=GOOGLE_API_KEY)
        GEMINI_AVAILABLE = True
        print("Gemini AI configured (Primary - Unlimited Free) [google-genai]")
    except ImportError:
        print("Install: pip install google-genai")
    except Exception as e:
        print(f"Gemini config error: {e}")

# ============================================================
# DEEPSEEK CONFIGURATION (NEW - Your Free Key)
# ============================================================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_AVAILABLE = bool(DEEPSEEK_API_KEY)

if DEEPSEEK_AVAILABLE:
    print("DeepSeek AI configured (Priority Backup - Free)")

# ============================================================
# GROQ CONFIGURATION (Backup)
# ============================================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_AVAILABLE = bool(GROQ_API_KEY)

# Try to use langchain if available
try:
    from langchain_groq import ChatGroq
    print("Groq LangChain configured (Backup)")
except ImportError:
    print("Groq LangChain not installed (will use direct API call)")

# ============================================================
# OPENROUTER CONFIGURATION (Last Resort)
# ============================================================
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")

OPENROUTER_FREE_MODELS = [
    {"name": "Llama 3.3 70B", "id": "meta-llama/llama-3.3-70b-instruct:free", "tokens": 131072},
    {"name": "Gemma 4 31B", "id": "google/gemma-4-31b-it:free", "tokens": 131072},
    {"name": "Qwen3 Next 80B", "id": "qwen/qwen3-next-80b-a3b-instruct:free", "tokens": 131072},
    {"name": "Hermes 3 405B", "id": "nousresearch/hermes-3-llama-3.1-405b:free", "tokens": 131072},
    {"name": "GPT-OSS 120B", "id": "openai/gpt-oss-120b:free", "tokens": 131072},
]

# ============================================================
# GEMINI TEXT MODELS (Your Key)
# ============================================================
GEMINI_TEXT_MODELS = [
    {"name": "Gemini 2.5 Pro", "id": "gemini-2.5-pro", "tokens": 1048576, "desc": "Best quality, 1M tokens, unlimited free"},
    {"name": "Gemini 2.5 Flash", "id": "gemini-2.5-flash", "tokens": 1048576, "desc": "Fast, 1M tokens, unlimited free"},
    {"name": "Gemini 2.0 Flash", "id": "gemini-2.0-flash", "tokens": 1048576, "desc": "Reliable, 1M tokens, unlimited free"},
]

# ============================================================
# GEMINI IMAGE MODELS (Your Key)
# ============================================================
GEMINI_IMAGE_MODELS = [
    {"name": "Gemini 2.5 Flash Image", "id": "gemini-2.5-flash-image", "desc": "Best free image generation"},
    {"name": "Gemini 3 Pro Image", "id": "gemini-3-pro-image-preview", "desc": "Latest image model"},
    {"name": "Gemini 3.1 Flash Image", "id": "gemini-3.1-flash-image-preview", "desc": "Fast image generation"},
    {"name": "Nano Banana Pro", "id": "nano-banana-pro-preview", "desc": "Specialized image model"},
]

# ============================================================
# FILENAME-BASED SUBJECT DETECTION (Highest Priority)
# ============================================================
def detect_subject_from_filename(filename: str) -> str:
    """Detect subject from filename keywords with highest priority."""
    filename_lower = filename.lower()
    
    filename_rules = [
        (["english", "grammar", "ielts", "toefl", "esl", "efl", "language", "writing", "reading", "speaking", "listening", "vocabulary", "essay", "comprehension", "sentence", "punctuation", "verb", "tense", "noun", "adjective", "adverb", "preposition"], "english"),
        (["physics", "physical", "mechanic"], "physics"),
        (["chemistry", "chemical", "organic chem"], "chemistry"),
        (["biology", "biological", "bio", "zoology", "botany"], "biology"),
        (["math", "maths", "mathematics", "algebra", "calculus", "geometry", "trigonometry", "arithmetic"], "mathematics"),
        (["computer", "programming", "coding", "python", "java", "software", "algorithm", "data structure", "web development"], "computer_science"),
        (["history", "historical", "ancient", "medieval", "modern history", "world war"], "history"),
        (["geography", "geographical", "world map", "atlas"], "geography"),
        (["economics", "economic", "economy", "macro", "micro"], "economics"),
        (["quran", "islam", "islamic", "bible", "christian", "hindu", "buddhist", "religious", "religion", "theology", "torah", "gospel", "spiritual", "faith", "worship"], "religious_studies"),
        (["literature", "literary", "poem", "poetry", "novel", "fiction", "drama", "shakespeare", "prose", "sonnet"], "literature"),
        (["medicine", "medical", "anatomy", "surgery", "clinical", "pharma", "pathology", "diagnosis", "treatment"], "medicine"),
        (["engineering", "engineer", "mechanical", "civil", "electrical", "structural", "manufacturing"], "engineering"),
        (["architecture", "architect", "building design", "floor plan", "blueprint"], "architecture"),
        (["art", "drawing", "painting", "design", "graphic", "sketch", "portrait", "landscape", "color theory"], "arts"),
        (["business", "management", "marketing", "finance", "accounting", "entrepreneur"], "economics"),
    ]
    
    for keywords, subject in filename_rules:
        if any(kw in filename_lower for kw in keywords):
            return subject
    
    return None

# ============================================================
# UNIVERSAL SUBJECT DETECTION
# ============================================================
def detect_subject(question: str, context: str, filename: str = "") -> str:
    """Auto-detect the subject from filename, question, and context."""
    
    # 1. Check filename first (highest priority)
    if filename:
        subject = detect_subject_from_filename(filename)
        if subject:
            return subject
    
    # 2. Check question text and context
    combined = (question + " " + context[:5000]).lower()
    
    subjects = {
        "english": ["english", "grammar", "ielts", "toefl", "esl", "language", "writing", "reading", "speaking", "listening", "vocabulary", "essay", "comprehension", "sentence", "punctuation", "verb", "tense", "noun", "adjective", "adverb", "preposition", "conjunction", "paragraph", "composition", "summary", "letter writing", "report writing"],
        "physics": ["physics", "force", "velocity", "acceleration", "magnetic", "electric", "circuit", "wave", "energy", "momentum", "gravity", "newton", "ohm", "voltage", "refraction", "nuclear", "quantum", "thermodynamic", "speed", "motion", "mass", "weight", "friction", "tension", "pressure", "density", "frequency", "wavelength"],
        "chemistry": ["chemistry", "chemical", "reaction", "molecule", "atom", "element", "compound", "acid", "base", "organic", "periodic", "bond", "ion", "catalyst", "equilibrium", "oxidation", "reduction", "titration", "solution", "concentration", "ph", "electrolysis"],
        "biology": ["biology", "cell", "dna", "protein", "gene", "organism", "photosynthesis", "respiration", "enzyme", "mitosis", "meiosis", "evolution", "ecology", "anatomy", "physiology", "species", "ecosystem", "bacteria", "virus", "plant", "animal", "organ", "tissue"],
        "mathematics": ["math", "algebra", "calculus", "geometry", "trigonometry", "equation", "function", "derivative", "integral", "matrix", "vector", "probability", "statistics", "theorem", "angle", "triangle", "circle", "graph", "coordinate", "polynomial"],
        "engineering": ["engineering", "mechanical", "civil", "electrical", "structural", "thermodynamic", "fluid", "material", "design", "manufacturing", "circuit", "signal", "control system", "motor", "generator", "transformer", "load", "stress", "strain"],
        "architecture": ["architecture", "building", "design", "floor plan", "facade", "structure", "construction", "blueprint", "spatial", "aesthetic", "urban", "landscape", "interior", "elevation", "section", "perspective"],
        "computer_science": ["programming", "algorithm", "code", "software", "hardware", "database", "network", "ai", "machine learning", "data structure", "python", "java", "c++", "web", "app", "function", "class", "object", "api", "server", "client"],
        "medicine": ["medicine", "diagnosis", "treatment", "symptom", "disease", "surgery", "pharma", "clinical", "patient", "anatomy", "pathology", "radiology", "cardiology", "neurology", "pediatrics"],
        "arts": ["art", "painting", "drawing", "sculpture", "design", "color", "composition", "aesthetic", "creative", "visual", "graphic", "illustration", "sketch", "portrait", "landscape"],
        "economics": ["economics", "supply", "demand", "market", "inflation", "gdp", "finance", "investment", "trade", "monetary", "fiscal", "business", "cost", "revenue", "profit"],
        "history": ["history", "ancient", "medieval", "modern", "war", "revolution", "empire", "civilization", "century", "timeline", "historical", "king", "queen", "dynasty", "battle", "treaty"],
        "geography": ["geography", "climate", "weather", "map", "continent", "ocean", "river", "mountain", "population", "urban", "rural", "country", "capital", "latitude", "longitude", "equator", "pole"],
        "literature": ["literature", "poem", "novel", "story", "character", "plot", "theme", "author", "poet", "fiction", "drama", "shakespeare", "chapter", "verse", "prose", "narrative", "sonnet", "essay"],
        "religious_studies": ["quran", "bible", "holy", "god", "allah", "prophet", "religion", "islam", "christianity", "hindu", "buddhist", "verse", "scripture", "surah", "ayah", "prayer", "worship", "faith", "spiritual", "mosque", "church", "temple", "torah", "gospel"],
    }
    
    scores = {}
    for subject, keywords in subjects.items():
        score = sum(1 for kw in keywords if kw in combined)
        if score > 0:
            scores[subject] = score
    
    if scores:
        return max(scores, key=scores.get)
    return "general"


# ============================================================
# DIAGRAM INSTRUCTIONS (UPDATED TO ASCII ART)
# ============================================================
def get_diagram_instructions(subject: str) -> str:
    """Return subject-specific diagram instructions (Now forces ASCII Art)."""
    
    # Force the AI to create text-based ASCII art instead of requesting images
    ascii_instruction = """
CRITICAL RULE: DO NOT request image generation. Instead, draw professional ASCII diagrams directly in the response using text characters. Use ` characters to format the ASCII diagram.
"""
    
    if subject == "english":
        return f"""{ascii_instruction}
## English Specific Instructions:
- For sentence structures, use ASCII trees.
- For timelines, use ASCII horizontal lines.
- For word maps, use ASCII branching text.
- Example phrase: "Here is the ASCII diagram of the sentence structure:"
```
Sentence
├── Noun Phrase
│   ├── Det: The
│   └── Noun: cat
└── Verb Phrase
    ├── Verb: sat
    └── Prep Phrase
        ├── Prep: on
        └── Noun Phrase
            ├── Det: the
            └── Noun: mat
```"""
    elif subject == "physics":
        return f"""{ascii_instruction}
## Physics Specific Instructions:
- For motion, draw ASCII speed-time graphs using '-', '/', and '\'.
- For circuits, draw ASCII circuit diagrams using '--', '|', and '='.
- For forces, draw ASCII free body diagrams with arrows ('^', 'v', '<', '>').
- Example phrase: "Here is the ASCII speed-time graph:"
```
Speed (m/s)
  60 |                    _________
     |                   /         \
  40 |                  /           \
     |                 /             \
  20 |                /               \
     |               /                 \
   0 |______________/___________________\_____ Time (s)
       0    100   200   300   400   500   600
```"""
    else:
        return f"""{ascii_instruction}
## General Instructions:
- For processes, draw ASCII flowcharts using '|', '-', and '+'.
- For organizational charts, use ASCII tree structures.
- For graphs, use ASCII line/bar charts with '|', '-', and '#'.
- Example phrase: "Here is the ASCII flowchart of the process:"
```
[Start] 
   |
   v
[Step 1]
   |
   v
[Decision] ---> [End]
   |
   v
[Step 2]
```"""


# ============================================================
# PROMPT SUGGESTIONS
# ============================================================
def get_prompt_suggestions(subject: str) -> list:
    """Get prompt suggestions based on detected subject."""
    suggestions = {
        "english": [
            "Explain all grammar rules with structure diagrams, tense timelines, and sentence charts.",
            "Create vocabulary maps, writing structure diagrams, and comprehension flowcharts.",
            "Teach English concepts with visual diagrams, tables, and organized study guides.",
        ],
        "physics": [
            "Solve all physics problems with motion graphs, force diagrams, and circuit schematics.",
            "Draw speed-time graphs, free body diagrams, and magnetic field diagrams for every question.",
            "Explain each physics concept with labeled diagrams and step-by-step calculations.",
        ],
        "general": [
            "Solve this completely with step-by-step solutions and relevant diagrams.",
            "Explain this topic with clear visual diagrams and professional illustrations.",
            "Draw relevant diagrams, charts, and figures for better understanding.",
        ],
    }
    return suggestions.get(subject, suggestions["general"])


# ============================================================
# GEMINI CALL (Primary - Unlimited Free)
# ============================================================
def ask_gemini(question: str, context: str = "", model_id: str = "gemini-2.5-flash") -> str:
    """Send question to Gemini using google-genai library."""
    if not GEMINI_AVAILABLE:
        return None
    
    try:
        client = genai.Client(api_key=GOOGLE_API_KEY)
        
        has_document = len(context.strip()) > 100
        subject = detect_subject(question, context)
        
        # STEM subjects get professional prompt with diagrams
        stem_subjects = ["physics", "chemistry", "biology", "mathematics", "engineering", "computer_science"]
        
        # Check if this question needs factual/search data
        needs_facts = any(t in question.lower() for t in [
            "current", "latest", "today", "now", "who is", "what is the",
            "president", "prime minister", "weather", "stock", "price",
            "2025", "2026", "year", "recent", "news", "age", "born"
        ])
        
        # Auto-inject search results if needed and not already present
        if needs_facts and "[REAL-TIME" not in context and "[Real-time" not in context:
            try:
                from services.search import search_web
                search_results = search_web(question, max_results=3, use_cache=False)
                if search_results and not search_results.startswith("[No search"):
                    context = f"[AUTO-SEARCHED LIVE DATA]\n{search_results}\n\n{context}"
                    print(f"  Auto-search injected for: {question[:80]}")
            except:
                pass
        
        # Build prompt based on context
        if has_document and subject in stem_subjects:
            diagram_instructions = get_diagram_instructions(subject)
            system_prompt = get_professional_prompt(subject, diagram_instructions)
            prompt = f"""{system_prompt}

Subject: {subject.replace('_', ' ')}
Context from uploaded document:
{context[:50000]}

User's request:
{question}

Provide a comprehensive, well-structured, professional response NOW."""
        elif has_document:
            prompt = f"""You are an expert {subject.replace('_', ' ')} teacher.

Use tables, clear headings, examples, and professional formatting.
Context from document:
{context[:50000]}

User's request: {question}

Provide a well-structured response with tables, examples, and clear explanations. DO NOT use physics/STEM formatting."""
        elif needs_facts:
            prompt = f"""You have access to real-time information. Answer accurately based on the data.

{context[:10000]}

User: {question}

Provide a direct, accurate answer. Use tables if helpful."""
        else:
            solve_triggers = ["solve", "answer", "question", "paper", "exam", "problem", "calculate", "explain", "what is", "find", "determine", "show", "prove", "derive", "work out", "draw", "diagram"]
            is_solving = any(t in question.lower() for t in solve_triggers)
            
            if is_solving and subject in stem_subjects:
                diagram_instructions = get_diagram_instructions(subject)
                system_prompt = get_professional_prompt(subject, diagram_instructions)
                prompt = f"""{system_prompt}

Subject: {subject.replace('_', ' ')}
Context: {context[:10000]}

User's request: {question}

Provide a comprehensive, well-structured, professional response."""
            else:
                prompt = f"""You are a helpful, friendly AI assistant named AI Intelligence Hub.

Context: {context[:5000]}

User: {question}

Provide a helpful, natural response. If this is just a greeting or casual chat, respond naturally."""
        
        # Send request to Gemini using the new library
        response = client.models.generate_content(
            model=model_id,
            contents=prompt
        )
        
        if response and response.text:
            print(f"  Gemini ({model_id}) - {len(response.text)} chars")
            return response.text.strip()
        return None
    except Exception as e:
        error_str = str(e)
        print(f"  Gemini ({model_id}) error: {error_str[:100]}")
        return None


# ============================================================
# DEEPSEEK CALL (NEW - Priority Backup)
# ============================================================
def ask_deepseek(question: str, context: str = "") -> str:
    """Send question to DeepSeek - Free, powerful backup."""
    if not DEEPSEEK_AVAILABLE:
        return None
    
    try:
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json",
        }
        
        # Use DeepSeek V3 model (fast and powerful)
        model_id = "deepseek-chat"
        
        payload = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": f"Context: {context[:4000]}\n\nQuestion: {question}"}
            ],
            "temperature": 0.7,
            "max_tokens": 4096,
        }
        
        resp = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=45
        )
        
        if resp.status_code == 200:
            data = resp.json()
            if "choices" in data and len(data["choices"]) > 0:
                result = data["choices"][0]["message"]["content"].strip()
                if result and len(result) > 20:
                    print(f"  DeepSeek (V3) - {len(result)} chars")
                    return result
        else:
            print(f"  DeepSeek HTTP {resp.status_code}")
            return None
            
    except Exception as e:
        print(f"  DeepSeek error: {str(e)[:100]}")
        return None


# ============================================================
# GROQ CALL (Backup - Fast)
# ============================================================
def ask_groq(question: str, context: str = "") -> str:
    """Send question to Groq - Fast backup."""
    if not GROQ_API_KEY:
        return None
    
    try:
        # Try using LangChain first (if installed)
        try:
            from langchain_groq import ChatGroq
            llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7, api_key=GROQ_API_KEY)
            prompt = f"Context: {context[:4000]}\n\nQuestion: {question}\n\nProvide a helpful response."
            response = llm.invoke(prompt)
            if response and response.content:
                print(f"  Groq (LangChain) - {len(response.content)} chars")
                return response.content.strip()
        except:
            # Fallback to direct API request
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "You are a helpful AI assistant."},
                    {"role": "user", "content": f"Context: {context[:4000]}\n\nQuestion: {question}"}
                ],
                "temperature": 0.7,
                "max_tokens": 4096,
            }
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            if resp.status_code == 200:
                data = resp.json()
                if "choices" in data and len(data["choices"]) > 0:
                    result = data["choices"][0]["message"]["content"].strip()
                    if result and len(result) > 20:
                        print(f"  Groq (Direct API) - {len(result)} chars")
                        return result
            else:
                print(f"  Groq HTTP {resp.status_code}")
        return None
    except Exception as e:
        print(f"  Groq error: {str(e)[:100]}")
        return None


# ============================================================
# OPENROUTER CALL (Last Resort)
# ============================================================
def ask_openrouter(question: str, context: str = "") -> str:
    """Send question to OpenRouter verified free models."""
    if not OPENROUTER_KEY:
        return None
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5001",
        "X-Title": "AI Intelligence Hub"
    }
    
    for model_info in OPENROUTER_FREE_MODELS:
        try:
            model_id = model_info["id"]
            model_name = model_info["name"]
            print(f"  Trying: {model_name}...")
            
            payload = {
                "model": model_id,
                "messages": [{"role": "user", "content": f"Context: {context[:4000]}\n\nQuestion: {question}"}],
                "temperature": 0.7,
                "max_tokens": 4096
            }
            
            resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=30)
            
            if resp.status_code == 200:
                data = resp.json()
                if "choices" in data and len(data["choices"]) > 0:
                    result = data["choices"][0]["message"]["content"].strip()
                    if result and len(result) > 20:
                        print(f"  OpenRouter ({model_name}) - {len(result)} chars")
                        return result
            else:
                print(f"  {model_name} HTTP {resp.status_code}")
                continue
        except:
            continue
    
    return None


# ============================================================
# MAIN AI ROUTER - AUTO SWITCH (Gemini First, DeepSeek Next)
# ============================================================
def ask_ai(question: str, context: str = "", backend: str = "auto") -> str:
    """
    Universal AI router - tries ALL providers in priority order:
    1. Gemini 2.5 Flash (your key - fast, reliable, unlimited free)
    2. Gemini 2.5 Pro (your key - best quality, may hit quota)
    3. DeepSeek V3 (your free key - powerful backup)
    4. Gemini 2.0 Flash (your key - most reliable)
    5. Groq (fast backup)
    6. OpenRouter free models (last resort)
    """
    print(f"\n{'='*50}")
    print(f"🤖 AI Request: {question[:80]}...")
    print(f"🔄 Backend: {backend}")
    print(f"{'='*50}")

    # Priority 1: Gemini 2.5 Flash first (most reliable)
    if GEMINI_AVAILABLE and backend in ["auto", "gemini", "gemini-flash"]:
        result = ask_gemini(question, context, "gemini-2.5-flash")
        if result and len(result) > 20:
            return result
    
    # Priority 2: Gemini 2.5 Pro (best quality)
    if GEMINI_AVAILABLE and backend in ["auto", "gemini", "gemini-pro"]:
        result = ask_gemini(question, context, "gemini-2.5-pro")
        if result and len(result) > 20:
            return result
    
    # Priority 3: DeepSeek V3 (powerful free backup)
    if DEEPSEEK_AVAILABLE and backend in ["auto", "deepseek"]:
        result = ask_deepseek(question, context)
        if result and len(result) > 20:
            return result
    
    # Priority 4: Gemini 2.0 Flash (most reliable)
    if GEMINI_AVAILABLE and backend in ["auto", "gemini", "gemini-flash"]:
        result = ask_gemini(question, context, "gemini-2.0-flash")
        if result and len(result) > 20:
            return result
    
    # Priority 5: Groq (fast, free)
    if GROQ_API_KEY and backend in ["auto", "groq"]:
        result = ask_groq(question, context)
        if result and len(result) > 20:
            return result
    
    # Priority 6: OpenRouter free models
    if OPENROUTER_KEY and backend in ["auto"]:
        result = ask_openrouter(question, context)
        if result and len(result) > 20 and not result.startswith("[Error"):
            return result
    
    return "[Error: All AI models unavailable. Check your internet and API keys.]"


# ============================================================
# GEMINI IMAGE GENERATION (Your Key - Free)
# ============================================================
async def generate_image_gemini(prompt: str, model_id: str = "gemini-2.5-flash-image") -> dict:
    """Generate image using Gemini's free image generation."""
    if not GEMINI_AVAILABLE:
        return {"success": False, "error": "Gemini not available"}
    
    try:
        import base64
        client = genai.Client(api_key=GOOGLE_API_KEY)
        
        enhanced_prompt = (
            f"Generate a professional educational diagram: {prompt}. "
            f"Clean white background, English labels only, textbook quality, "
            f"bold fonts, clear lines, professional design, high resolution."
        )
        
        response = client.models.generate_content(
            model=model_id,
            contents=enhanced_prompt
        )
        
        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    image_base64 = base64.b64encode(part.inline_data.data).decode('utf-8')
                    if len(image_base64) > 1000:
                        print(f"  Gemini Image ({model_id}) - {len(image_base64)} chars")
                        return {"success": True, "image_data": image_base64, "provider": f"Gemini ({model_id})"}
        
        return {"success": False, "error": "No image in response"}
    except Exception as e:
        print(f"  Gemini Image error: {str(e)[:80]}")
        return {"success": False, "error": str(e)}


# ============================================================
# UNIVERSAL PROFESSIONAL PROMPT SYSTEM (OPTIMIZED & CLEAN)
# ============================================================
def get_professional_prompt(subject: str, diagram_instructions: str) -> str:
    """
    Returns a subject-specific, clean, and actionable system prompt.
    """

    # Base core rules applied to ALL subjects
    base_rules = """
## Core Response Rules (Strictly Follow):
1. **Structure:** Use clear headings, bullet points, and numbered steps. 
2. **Clarity:** Explain complex concepts step-by-step. Do not skip reasoning.
3. **Formatting:** Use **bold** for key terms, > blockquotes for important notes, and `code` blocks for formulas, code, or ASCII diagrams.
4. **Tables:** Use markdown tables to compare data, concepts, or lists.
5. **Depth:** Provide comprehensive, detailed explanations. Do not give shallow or generic answers.
6. **Visuals:** ALWAYS include a labeled ASCII diagram inside triple backticks (`) to visualize the concept, using the instructions provided.
"""
    
    # Subject-specific formatting
    if subject in ["physics", "chemistry", "biology", "mathematics", "engineering", "computer_science"]:
        return f"""{base_rules}

## Subject: {subject.replace('_', ' ')}
## Role: Expert Tutor & Educator

### Special Instructions for STEM Subjects:
- **Step-by-step solutions:** Show every calculation and unit.
- **Formulas:** Display equations clearly in code blocks.
- **Data:** Use tables for data comparison and organization.
- **Diagrams:** {diagram_instructions}
- **Final Answer:** Always provide a summarized conclusion box.

Now, provide a professional, well-structured, and detailed response to the user's request."""
    
    elif subject in ["english", "literature", "history", "geography", "religious_studies", "economics", "arts"]:
        return f"""{base_rules}

## Subject: {subject.replace('_', ' ')}
## Role: Expert Educator & Humanities Teacher

### Special Instructions for Humanities:
- **Structure:** Use clear headings for different sections.
- **Examples:** Provide relevant examples for every concept.
- **Tables:** Use tables to compare classifications, eras, or themes.
- **Diagrams:** {diagram_instructions}
- **Depth:** Explore the cultural, ethical, or historical context of the topic.

Now, provide a professional, well-structured, and detailed response to the user's request."""
    
    elif subject == "medicine":
        return f"""{base_rules}

## Subject: Medicine
## Role: Clinical Educator & Medical Instructor

### Special Instructions for Medicine:
- **Clinical focus:** Use diagnostic tables and anatomical descriptions.
- **Procedures:** Explain step-by-step medical procedures clearly.
- **Diagrams:** {diagram_instructions}
- **Professionalism:** Maintain a precise and clinical tone.
- **Note:** Do NOT use generic physics or engineering diagrams.

Now, provide a professional, well-structured, and detailed response to the user's request."""
    
    else:
        return f"""{base_rules}

## Subject: {subject.replace('_', ' ')}
## Role: Professional Educator

### Instructions:
- Tailor your response to the subject matter provided.
- Use examples and structured formatting.
- {diagram_instructions}

Now, provide a comprehensive, well-structured, and detailed professional response."""
