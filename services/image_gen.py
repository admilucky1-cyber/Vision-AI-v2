"""
Vision AI v2.0 - Image & Diagram Generation
=============================================
Multi-engine diagram and chart generation.

Priority:
1. Google Image Search (Real images from the web)
2. Plotly (Clean charts)
3. Matplotlib (Physics graphs)
4. Hugging Face Multi-Model AI (FLUX, SD3.5, FLUX Schnell)
5. Graphviz (Structural diagrams)
6. ASCII Art (Text fallback)
"""

import os
import base64
import io
import logging
import requests
from typing import List, Dict, Optional

logger = logging.getLogger("vision-ai")

# ==========================================================
# OPTIONAL LIBRARY LOADING (Each engine degrades gracefully)
# ==========================================================

# Matplotlib
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    MATPLOTLIB_AVAILABLE = True
except ImportError as e:
    logger.warning(f"matplotlib unavailable, chart generation disabled: {e}")
    MATPLOTLIB_AVAILABLE = False

# Numpy
try:
    import numpy as np
except ImportError:
    np = None

# Pandas
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None
    logger.warning("pandas unavailable, Plotly charts will be disabled.")

# Plotly
try:
    import plotly.express as px
    import plotly.io as pio
    PLOTLY_AVAILABLE = True
except ImportError as e:
    PLOTLY_AVAILABLE = False
    logger.warning(f"plotly unavailable, plotly charts disabled: {e}")

# Graphviz
try:
    import graphviz
    GRAPHVIZ_AVAILABLE = True
except ImportError as e:
    logger.warning(f"graphviz unavailable, flowchart/org-chart diagrams disabled: {e}")
    GRAPHVIZ_AVAILABLE = False

# PIL (Pillow) - For image safety checks
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# ==========================================================
# CONFIGURATION
# ==========================================================
HF_TOKEN = os.getenv("HF_TOKEN")
MIN_IMAGE_SIZE = 8000

# 🟢 Google Custom Search API Config
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_ENGINE_ID = os.getenv("GOOGLE_ENGINE_ID")

# ==========================================================
# QUALITY STANDARDS
# ==========================================================
QUALITY_COLORS = {
    'navy': '#1a5276', 'red': '#e74c3c', 'green': '#27ae60',
    'blue': '#2980b9', 'orange': '#f39c12', 'purple': '#8e44ad',
    'dark': '#2c3e50', 'gray': '#95a5a6', 'light': '#ecf0f1',
}

# ==========================================================
# CONVERSION HELPERS
# ==========================================================
def fig_to_base64(fig) -> str:
    """Convert matplotlib figure to base64 PNG."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=200, facecolor='white', edgecolor='none', bbox_inches='tight')
    buf.seek(0)
    img = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img

def plotly_to_base64(fig) -> str:
    """Convert plotly figure to base64 PNG."""
    try:
        img_bytes = fig.to_image(format="png")
        return base64.b64encode(img_bytes).decode('utf-8')
    except Exception:
        try:
            import plotly.io as pio
            pio.kaleido.scope.default_format = 'png'
            img_bytes = pio.kaleido.scope.transform(fig, format='png')
            return base64.b64encode(img_bytes).decode('utf-8')
        except Exception as e2:
            raise Exception(f"Plotly image conversion failed: {e2}")

# ==========================================================
# 🚀 GOOGLE REAL IMAGE SEARCH
# ==========================================================
async def search_real_image(query: str) -> dict:
    """Searches Google for a real, high-quality image."""
    if not GOOGLE_API_KEY or not GOOGLE_ENGINE_ID:
        return {"success": False, "error": "Google API keys missing"}

    try:
        headers = {"User-Agent": "VisionAI/2.0"}
        
        url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={GOOGLE_ENGINE_ID}&q={query}+diagram&searchType=image&num=1&imgSize=large&safe=off"
        
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()

        # Fallback search term
        if "items" not in data or len(data["items"]) == 0:
            url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={GOOGLE_ENGINE_ID}&q={query}+chart&searchType=image&num=1&imgSize=large&safe=off"
            res = requests.get(url, headers=headers, timeout=10)
            data = res.json()

        if "items" in data and len(data["items"]) > 0:
            image_url = data["items"][0]["link"]
            img_res = requests.get(image_url, headers=headers, timeout=10)
            if img_res.status_code == 200:
                img_b64 = base64.b64encode(img_res.content).decode('utf-8')
                return {"success": True, "image_data": img_b64, "provider": "Google Image Search"}
        
        return {"success": False, "error": "No images found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==========================================================
# PLOTLY RENDERERS (STATISTICAL CHARTS)
# ==========================================================
def draw_bar_chart() -> dict:
    """Generate bar chart."""
    if not (PLOTLY_AVAILABLE and PANDAS_AVAILABLE):
        return {"success": False, "error": "Plotly/pandas not installed"}
    try:
        data = {'Category': ['A', 'B', 'C', 'D'], 'Values': [23, 45, 56, 78]}
        df = pd.DataFrame(data)
        fig = px.bar(df, x='Category', y='Values', title='Bar Chart', color='Category')
        fig.update_layout(template='plotly_white')
        return {"success": True, "image_data": plotly_to_base64(fig), "provider": "Plotly"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def draw_pie_chart() -> dict:
    """Generate pie chart."""
    if not (PLOTLY_AVAILABLE and PANDAS_AVAILABLE):
        return {"success": False, "error": "Plotly/pandas not installed"}
    try:
        data = {'Category': ['X', 'Y', 'Z'], 'Values': [30, 50, 20]}
        df = pd.DataFrame(data)
        fig = px.pie(df, values='Values', names='Category', title='Pie Chart')
        fig.update_layout(template='plotly_white')
        return {"success": True, "image_data": plotly_to_base64(fig), "provider": "Plotly"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def draw_line_chart() -> dict:
    """Generate line chart."""
    if not (PLOTLY_AVAILABLE and PANDAS_AVAILABLE):
        return {"success": False, "error": "Plotly/pandas not installed"}
    try:
        data = {'Year': [2019, 2020, 2021, 2022, 2023], 'Sales': [150, 230, 180, 275, 340]}
        df = pd.DataFrame(data)
        fig = px.line(df, x='Year', y='Sales', title='Line Chart', markers=True)
        fig.update_layout(template='plotly_white')
        return {"success": True, "image_data": plotly_to_base64(fig), "provider": "Plotly"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==========================================================
# MATPLOTLIB RENDERERS (PHYSICS & MATH)
# ==========================================================
def draw_speed_time_graph() -> dict:
    """Generate speed-time graph."""
    if not (MATPLOTLIB_AVAILABLE):
        return {"success": False, "error": "matplotlib not installed"}
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        t, v = [0, 200, 500, 600], [0, 60, 60, 0]
        ax.plot(t, v, QUALITY_COLORS['navy'], linewidth=3)
        ax.fill_between(t, v, alpha=0.1, color='#3498db')
        ax.set_xlabel('Time (s)', fontsize=14, fontweight='bold')
        ax.set_ylabel('Speed (m/s)', fontsize=14, fontweight='bold')
        ax.set_title('Speed-Time Graph', fontsize=18, fontweight='bold', pad=15)
        ax.set_xlim(0, 650)
        ax.set_ylim(0, 75)
        ax.grid(True, alpha=0.3)
        return {"success": True, "image_data": fig_to_base64(fig), "provider": "Matplotlib"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def draw_force_diagram() -> dict:
    """Generate free body diagram."""
    if not (MATPLOTLIB_AVAILABLE):
        return {"success": False, "error": "matplotlib not installed"}
    try:
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.set_xlim(-3.5, 3.5)
        ax.set_ylim(-3.5, 3.5)
        ax.set_aspect('equal')
        ax.axis('off')

        box = patches.FancyBboxPatch((-1.2, -1.2), 2.4, 2.4, boxstyle="round,pad=0.1",
                                     facecolor=QUALITY_COLORS['light'], edgecolor=QUALITY_COLORS['dark'], linewidth=3)
        ax.add_patch(box)
        ax.text(0, 0, 'OBJECT', ha='center', va='center', fontsize=15, fontweight='bold')

        arrows = [
            (0, -1.4, 0, -1.6, QUALITY_COLORS['red'], 'Weight(mg)', 0.3, -2.5),
            (0, 1.4, 0, 1.6, QUALITY_COLORS['green'], 'Normal(N)', 0.3, 2.4),
            (-1.4, 0, -1.6, 0, QUALITY_COLORS['orange'], 'Friction(f)', -3.2, 0.3),
            (1.4, 0, 1.6, 0, QUALITY_COLORS['blue'], 'Applied(F)', 1.6, 0.3),
        ]
        for x1, y1, x2, y2, color, label, tx, ty in arrows:
            ax.arrow(x1, y1, x2, y2, head_width=0.18, head_length=0.25, fc=color, ec=color, linewidth=3, alpha=0.9)
            ax.text(tx, ty, label, fontsize=13, color=color, fontweight='bold', ha='center')

        ax.set_title('Free Body Diagram', fontsize=18, fontweight='bold', pad=25)
        return {"success": True, "image_data": fig_to_base64(fig), "provider": "Matplotlib"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==========================================================
# GRAPHVIZ RENDERERS (STRUCTURAL DIAGRAMS)
# ==========================================================
def draw_flowchart() -> dict:
    """Generate flowchart diagram."""
    if not (GRAPHVIZ_AVAILABLE):
        return {"success": False, "error": "graphviz not installed"}
    try:
        dot = graphviz.Digraph(comment='Process Flow', format='png')
        dot.attr(rankdir='TB', size='8,8', dpi='200')
        dot.node('start', 'Start', shape='ellipse', fillcolor='#7b68ee', fontcolor='white', style='filled')
        dot.node('step1', 'Step 1', shape='box', style='rounded,filled', fillcolor='#ecf0f1')
        dot.node('step2', 'Step 2', shape='box', style='rounded,filled', fillcolor='#ecf0f1')
        dot.node('decision', 'Decision?', shape='diamond', fillcolor='#f39c12', fontcolor='white', style='filled')
        dot.node('step3', 'Step 3', shape='box', style='rounded,filled', fillcolor='#ecf0f1')
        dot.node('end', 'End', shape='ellipse', fillcolor='#27ae60', fontcolor='white', style='filled')
        dot.edge('start', 'step1')
        dot.edge('step1', 'step2')
        dot.edge('step2', 'decision')
        dot.edge('decision', 'step3', label='Yes')
        dot.edge('decision', 'end', label='No')
        dot.edge('step3', 'end')
        img_bytes = dot.pipe()
        return {"success": True, "image_data": base64.b64encode(img_bytes).decode('utf-8'), "provider": "Graphviz"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def draw_org_chart() -> dict:
    """Generate organizational chart."""
    if not (GRAPHVIZ_AVAILABLE):
        return {"success": False, "error": "graphviz not installed"}
    try:
        dot = graphviz.Digraph(comment='Org Chart', format='png')
        dot.attr(rankdir='TB', size='8,8', dpi='200')
        dot.node('CEO', 'CEO', shape='ellipse', fillcolor='#e74c3c', fontcolor='white', style='filled')
        dot.node('CTO', 'CTO', fillcolor='#3498db', fontcolor='white', style='filled')
        dot.node('CFO', 'CFO', fillcolor='#2ecc71', fontcolor='white', style='filled')
        dot.node('Dev', 'Dev Team', shape='box', style='rounded,filled', fillcolor='#ecf0f1')
        dot.node('Ops', 'Ops Team', shape='box', style='rounded,filled', fillcolor='#ecf0f1')
        dot.node('Acc', 'Accounting', shape='box', style='rounded,filled', fillcolor='#ecf0f1')
        dot.edge('CEO', 'CTO')
        dot.edge('CEO', 'CFO')
        dot.edge('CTO', 'Dev')
        dot.edge('CTO', 'Ops')
        dot.edge('CFO', 'Acc')
        img_bytes = dot.pipe()
        return {"success": True, "image_data": base64.b64encode(img_bytes).decode('utf-8'), "provider": "Graphviz"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==========================================================
# 🚀 PROFESSIONAL HUGGING FACE GENERATOR (Multi-Model)
# ==========================================================
async def generate_with_hf(prompt: str, model_index: int = 0) -> dict:
    """
    Generate an image using multiple Hugging Face models.
    Automatically handles queue waiting and fallback models.

    Supported Free Models:
    - black-forest-labs/FLUX.1-dev (Primary)
    - stabilityai/stable-diffusion-3.5-large (High Quality Backup)
    - black-forest-labs/FLUX.1-schnell (Fast Fallback)
    """
    if not HF_TOKEN:
        return {"success": False, "error": "HF_TOKEN not set in .env"}

    MODELS = [
        "black-forest-labs/FLUX.1-dev",
        "stabilityai/stable-diffusion-3.5-large",
        "black-forest-labs/FLUX.1-schnell"
    ]
    
    API_BASE = "https://api-inference.huggingface.co/models"

    for i in range(model_index, len(MODELS)):
        model_id = MODELS[i]
        url = f"{API_BASE}/{model_id}"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        enhanced_prompt = f"Professional educational infographic diagram: {prompt}. Clean white background, sharp English labels, textbook quality."
        payload = {"inputs": enhanced_prompt}

        try:
            print(f"🖼️ Generating image with {model_id}...")
            import asyncio
            response = requests.post(url, headers=headers, json=payload, timeout=90)

            # Handle Hugging Face "Model is loading" queue (503)
            if response.status_code == 503:
                print(f"⏳ {model_id} is loading. Waiting 5 seconds...")
                await asyncio.sleep(5)
                response = requests.post(url, headers=headers, json=payload, timeout=90)

            if response.status_code == 200:
                image_base64 = base64.b64encode(response.content).decode('utf-8')
                
                # Validate image size
                if len(image_base64) > MIN_IMAGE_SIZE:
                    return {
                        "success": True,
                        "image_data": image_base64,
                        "provider": f"Hugging Face ({model_id})"
                    }
                else:
                    print(f"⚠️ {model_id} returned an image that was too small. Trying next model...")
            else:
                print(f"⚠️ {model_id} returned status {response.status_code}. Trying next model...")

        except requests.exceptions.Timeout:
            print(f"⏱️ {model_id} timed out. Trying next model...")
        except Exception as e:
            print(f"❌ Error with {model_id}: {e}. Trying next model...")

    return {"success": False, "error": "All Hugging Face models failed. Please try a simpler prompt."}

async def generate_with_flux(prompt: str) -> dict:
    """Legacy wrapper for backward compatibility."""
    return await generate_with_hf(prompt, model_index=0)

# ==========================================================
# DIAGRAM DETECTION
# ==========================================================
DIAGRAM_KEYWORDS = [
    ("speed-time", ["speed-time", "speed time", "velocity"]),
    ("force-diagram", ["force diagram", "free body"]),
    ("flowchart", ["flowchart", "flow chart"]),
    ("bar-chart", ["bar chart", "bar graph"]),
    ("pie-chart", ["pie chart"]),
    ("line-chart", ["line chart", "line graph"]),
    ("org-chart", ["organizational", "org chart"]),
]

def detect_diagram_types(answer_text: str) -> List[tuple]:
    """Detect diagram types mentioned in text."""
    detected = []
    lower = answer_text.lower()
    for d_type, keywords in DIAGRAM_KEYWORDS:
        if any(kw in lower for kw in keywords):
            detected.append((d_type, keywords[0]))
    return detected[:3]  # Max 3 diagrams

# ==========================================================
# MAIN GENERATOR (UPDATED WITH PROFESSIONAL HF)
# ==========================================================
async def generate_diagram_image(diagram_type: str) -> dict:
    """Generate a diagram image based on type."""
    
    # 🚀 1. Try Real Internet Image first
    try:
        result = await search_real_image(f"{diagram_type.replace('-', ' ')}")
        if result.get("success"):
            return result
    except Exception:
        pass # If Google fails, silently fallback

    # 2. Plotly charts
    if diagram_type == "bar-chart":
        return draw_bar_chart()
    if diagram_type == "pie-chart":
        return draw_pie_chart()
    if diagram_type == "line-chart":
        return draw_line_chart()

    # 3. Matplotlib physics
    if diagram_type == "speed-time":
        return draw_speed_time_graph()
    if diagram_type == "force-diagram":
        return draw_force_diagram()

    # 4. Graphviz structural
    if diagram_type == "flowchart":
        return draw_flowchart()
    if diagram_type == "org-chart":
        return draw_org_chart()

    # 5. HF Multi-Model AI fallback (FLUX, SD3.5, FLUX Schnell)
    prompt = f"Professional educational diagram of {diagram_type.replace('-', ' ')}. Clean white background, English labels."
    result = await generate_with_hf(prompt, model_index=0)
    if result.get("success"):
        return result

    return {"success": False, "error": "All providers failed"}

async def generate_all_diagrams(answer_text: str, subject: str = "general") -> List[dict]:
    """Generate all detected diagrams from answer text."""
    diagram_types = detect_diagram_types(answer_text)
    if not diagram_types:
        return []

    images = []
    for diagram_type, keyword in diagram_types:
        result = await generate_diagram_image(diagram_type)
        if result.get("success"):
            result["keyword"] = keyword
            images.append(result)
    return images