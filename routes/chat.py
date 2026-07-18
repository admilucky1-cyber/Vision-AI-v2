"""
Chat router for AI Intelligence Hub.
Real-Time Agentic RAG: Auto-injects fresh web data + uploaded files.
"""
from fastapi import APIRouter, Form, UploadFile, File
from fastapi.responses import JSONResponse
from services.llm import ask_ai
from services.multimodal import process_uploaded_file
from services.search import search_web, is_search_needed, auto_search_context, get_current_info
from services.self_optimizer import optimizer
import traceback
import time
import hashlib
from datetime import datetime

router = APIRouter()

# In-memory RAG cache
rag_cache = {}

@router.post("/chat/send")
async def chat_send(
    message: str = Form(...),
    files: list[UploadFile] = File(default=[]),
    model: str = Form("auto")
):
    start_time = time.time()
    
    try:
        extra_context = ""
        file_names = []

        # ========================================================
        # 1. RAG: Process uploaded files (Current Data)
        # ========================================================
        if files:
            print(f"📄 Processing {len(files)} file(s) for RAG...")
            file_texts = []
            
            for file in files:
                try:
                    file_names.append(file.filename)
                    content = await process_uploaded_file(file)
                    
                    # Cache for multi-turn chat
                    cache_key = hashlib.md5((file.filename + content[:500]).encode()).hexdigest()
                    rag_cache[cache_key] = {
                        "filename": file.filename,
                        "content": content,
                        "timestamp": time.time()
                    }
                    # Keep cache small
                    if len(rag_cache) > 5:
                        oldest = min(rag_cache.keys(), key=lambda k: rag_cache[k]["timestamp"])
                        del rag_cache[oldest]
                    
                    file_texts.append(f"[Uploaded File: {file.filename}]\n{content}")
                    print(f"   ✅ Cached: {file.filename} ({len(content)} chars)")
                except Exception as e:
                    print(f"   ❌ Failed: {file.filename} - {e}")
                    file_texts.append(f"[File: {file.filename}] Could not process.")
            
            if file_texts:
                extra_context += "\n\n".join(file_texts)

        # ========================================================
        # 2. AUTO REAL-TIME WEB SEARCH (ALWAYS FRESH)
        # ========================================================
        
        # Always inject current date/time so the AI knows when "today" is
        current_time_context = f"[CURRENT DATE & TIME: {get_current_info()}]"
        extra_context = current_time_context + "\n" + extra_context
        
        # 2a. Auto-detect if search is needed (Current events, news, prices, etc.)
        real_time_results = auto_search_context(message, extra_context)
        if real_time_results and not real_time_results.startswith("[Web search unavailable"):
            extra_context += f"\n\n[REAL-TIME LIVE DATA FROM WEB]\n{real_time_results}"
            print(f"🌐 Auto real-time data injected ({len(real_time_results)} chars)")
        
        # 2b. Explicit search triggers
        if is_search_needed(message):
            print(f"🔍 Explicit web search triggered for: '{message[:80]}...'")
            try:
                # Force fresh search (no cache)
                web_results = search_web(message, max_results=5, use_cache=False)
                if web_results and not web_results.startswith("[No search"):
                    extra_context += f"\n\n[DEDICATED WEB SEARCH RESULTS]\n{web_results}"
                    print(f"   ✅ Search results added ({len(web_results)} chars)")
                else:
                    print(f"   ⚠️ Search returned no results: {web_results[:100] if web_results else 'None'}")
            except Exception as e:
                print(f"   ❌ Search error: {e}")

        # ========================================================
        # 3. GET AI TEXT RESPONSE (Injects ALL context)
        # ========================================================
        print(f"🤖 Calling AI model: {model}...")
        print(f"   Message: '{message[:80]}...'")
        print(f"   Total Context Size: {len(extra_context)} chars")
        
        reasoning = optimizer.get_reasoning_recommendation(message)
        answer = ask_ai(question=message, context=extra_context, backend=model)
        response_time = time.time() - start_time

        # ========================================================
        # 4. RECORD TO OPTIMIZER
        # ========================================================
        try:
            from services.llm import detect_subject
            subject = detect_subject(message, extra_context)
            optimizer.learn_from_interaction(
                question=message,
                answer=answer[:500],
                subject=subject,
                provider=model,
                success=not answer.startswith("[Error"),
                response_time=response_time,
                image_count=0,
            )
        except Exception as e:
            print(f"Learning error: {e}")

        print("=" * 60)
        print(f"✅ FINAL RESPONSE DELIVERED")
        print(f"   Text: {len(answer)} chars")
        print(f"   Time: {response_time:.1f}s")
        print("=" * 60)

        return {
            "answer": answer,
            "model_used": model,
            "context_length": len(extra_context),
            "response_time": round(response_time, 2),
            "reasoning_style": reasoning["style"],
            "rag_files_loaded": len(files),
            "search_performed": bool(real_time_results or is_search_needed(message)),
            "current_time": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"❌ FATAL CHAT ERROR:")
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": f"Server error: {str(e)}"})