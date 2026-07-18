# ==========================================================
# DIAGRAM PROMPTS - FOR CHAT AI REFERENCE
# ==========================================================
DIAGRAM_PROMPTS = {
    "flowchart": "Create a professional flowchart diagram showing the flow of data or process steps. Use standard flowchart symbols like rectangles for processes, diamonds for decisions, and arrows for flow direction. Include clear labels and a title at the top. Clean, minimalist design on a white background.",
    "mindmap": "Create a colorful mind map diagram with a central topic in the middle and radiating branches for subtopics. Use different colors for each branch. Include icons and small text labels. Modern, clean design with a white background.",
    "timeline": "Create a horizontal timeline diagram showing events in chronological order. Use a central line with milestone markers. Include dates, event names, and brief descriptions. Clean, professional design with a white background.",
    "venn": "Create a Venn diagram with overlapping circles showing the relationship between sets. Label each circle and the intersection areas. Use different colors for each set. Clean, educational design with a white background.",
    "bar_chart": "Create a bar chart showing data comparison. Include labeled axes with titles, a legend, and data values on top of bars. Use a clean, professional color palette. White background with grid lines.",
    "pie_chart": "Create a pie chart showing data distribution. Include a legend for each slice, percentages in each slice, and a title. Use a clean, modern color palette. White background.",
    "line_chart": "Create a line chart showing trends over time. Include labeled axes with titles, a legend, data points, and a title. Use a clean, professional color palette. White background with grid lines.",
    "architecture_diagram": "Create a system architecture diagram showing components, services, databases, and their interactions. Use boxes for components, cylinders for databases, and arrows for data flow. Clean, technical design with a white background.",
    "network_diagram": "Create a network topology diagram showing devices, connections, and labels. Use icons for different device types (servers, routers, switches, clients). Clean, technical design with a white background.",
    "sequence_diagram": "Create a UML sequence diagram showing interactions between components over time. Use lifelines, activation bars, and message arrows. Include clear labels for each component and message. Clean, technical design with a white background.",
    "class_diagram": "Create a UML class diagram showing classes, attributes, methods, and relationships. Use standard UML notation with compartments for class name, attributes, and methods. Include inheritance and association arrows. Clean, technical design with a white background.",
    "er_diagram": "Create an Entity-Relationship diagram showing entities, attributes, and relationships. Use rectangles for entities, ovals for attributes, and diamonds for relationships. Include cardinality labels. Clean, technical design with a white background.",
    "gantt_chart": "Create a Gantt chart showing project tasks, timelines, and dependencies. Include task names on the left, horizontal bars for each task, and dates on the x-axis. Use different colors for different task categories. Clean, professional design with a white background.",
    "scatter_plot": "Create a scatter plot showing data points on a Cartesian plane. Include labeled axes, a title, and a legend. Use clean, modern colors. White background with grid lines.",
    "heatmap": "Create a heatmap showing data intensity using colors. Include labeled axes, a color legend, and a title. Use a professional color palette. Clean, modern design with a white background.",
    "decision_tree": "Create a decision tree diagram showing choices and outcomes. Use rectangles for decision nodes, circles for chance nodes, and lines for branches. Include labels for each branch. Clean, professional design with a white background.",
    "organizational_chart": "Create an organizational chart showing hierarchy and reporting structure. Use boxes for each position with names and titles. Use lines to show reporting relationships. Clean, professional design with a white background.",
    "swimlane_diagram": "Create a swimlane diagram showing process steps across different departments or roles. Use horizontal lanes for each role, and flow arrows between steps. Include clear labels. Clean, professional design with a white background.",
    "data_flow_diagram": "Create a data flow diagram showing how data moves through a system. Use circles for processes, rectangles for external entities, and arrows for data flows. Include clear labels. Clean, technical design with a white background.",
    "state_machine": "Create a state machine diagram showing states and transitions. Use rounded rectangles for states, arrows for transitions, and labels for events. Include start and end states. Clean, technical design with a white background.",
    "component_diagram": "Create a UML component diagram showing software components and their dependencies. Use rectangles for components, dashed lines for dependencies, and circles for interfaces. Clean, technical design with a white background.",
    "package_diagram": "Create a UML package diagram showing packages and their relationships. Use rectangles with folders for packages, and lines for dependencies. Clean, technical design with a white background.",
    "activity_diagram": "Create a UML activity diagram showing workflow steps. Use rounded rectangles for activities, diamonds for decisions, and arrows for flow. Include start and end nodes. Clean, technical design with a white background.",
    "use_case_diagram": "Create a UML use case diagram showing actors and use cases. Use stick figures for actors, ovals for use cases, and lines for relationships. Clean, technical design with a white background.",
    "deployment_diagram": "Create a UML deployment diagram showing physical deployment of components. Use 3D boxes for nodes, rectangles for components, and lines for communication paths. Clean, technical design with a white background.",
    "fishbone_diagram": "Create a fishbone (Ishikawa) diagram showing cause and effect. Use a central spine with branches for categories (People, Process, Equipment, etc.) and sub-branches for specific causes. Clean, professional design with a white background.",
    "kanban_board": "Create a Kanban board diagram showing workflow stages (To Do, In Progress, Done) with cards for each task. Use different colors for task priority. Clean, modern design with a white background.",
    "burn_down_chart": "Create a burn-down chart showing work remaining vs time. Include a y-axis for work remaining, x-axis for days, actual line, and ideal line. Clean, professional design with a white background.",
    "network_topology": "Create a network topology diagram showing devices (routers, switches, servers, clients) and connections. Use icons for devices and lines for connections. Clean, technical design with a white background.",
    "cloud_architecture": "Create a cloud architecture diagram showing cloud services, compute resources, storage, networking, and security components. Use cloud icons and clean labels. Modern, technical design with a white background.",
}

# ==========================================================
# IMAGE GENERATION - LIGHTWEIGHT HYBRID
# ==========================================================
# Priority:
#   1. Plotly (Clean charts)
#   2. Matplotlib (Physics graphs)
#   3. Hugging Face FLUX (All other AI visuals)
#   4. Graphviz (Only called for flowcharts/trees if AI fails)

import os
import base64
import io
import urllib.parse
import requests
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.io as pio
import graphviz

# ==========================================================
# HUGGING FACE FLUX CONFIG
# ==========================================================
HUGGING_FACE_TOKEN = os.getenv("HF_TOKEN")
HF_API_FLUX = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev"

# ==========================================================
# QUALITY STANDARDS
# ==========================================================
MIN_IMAGE_SIZE = 8000
QUALITY_COLORS = {
    'navy': '#1a5276', 'red': '#e74c3c', 'green': '#27ae60',
    'blue': '#2980b9', 'orange': '#f39c12', 'purple': '#8e44ad',
    'dark': '#2c3e50', 'gray': '#95a5a6', 'light': '#ecf0f1',
}

# ==========================================================
# PLOTLY STATIC CONFIG
# ==========================================================
pio.kaleido.scope.default_format = 'png'
pio.kaleido.scope.default_width = 800
pio.kaleido.scope.default_height = 500

def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=200, facecolor='white', edgecolor='none', bbox_inches='tight')
    buf.seek(0)
    img = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img

def plotly_to_base64(fig):
    img_bytes = fig.to_image(format="png")
    return base64.b64encode(img_bytes).decode('utf-8')

def authenticate_quality(image_data: str, diagram_type: str) -> bool:
    if len(image_data) < MIN_IMAGE_SIZE:
        return False
    return True

# ==========================================================
# GRAPHVIZ RENDERERS (FALLBACK FOR TREES/FLOWCHARTS)
# ==========================================================
def draw_flowchart():
    try:
        dot = graphviz.Digraph(comment='Process Flow', format='png')
        dot.attr(rankdir='TB', size='8,8', dpi='200')
        dot.node('start', 'Start', shape='ellipse', fillcolor='#7b68ee', fontcolor='white')
        dot.node('step1', 'Step 1')
        dot.node('step2', 'Step 2')
        dot.node('decision', 'Decision?', shape='diamond', fillcolor='#f39c12')
        dot.node('step3', 'Step 3')
        dot.node('end', 'End', shape='ellipse', fillcolor='#27ae60', fontcolor='white')
        dot.edge('start', 'step1')
        dot.edge('step1', 'step2')
        dot.edge('step2', 'decision')
        dot.edge('decision', 'step3', label='Yes')
        dot.edge('decision', 'end', label='No')
        img_bytes = dot.pipe()
        image_base64 = base64.b64encode(img_bytes).decode('utf-8')
        return {"success": True, "image_data": image_base64, "provider": "Graphviz (Flowchart)"}
    except:
        return None

def draw_sentence_tree():
    try:
        dot = graphviz.Digraph(comment='Sentence Structure', format='png')
        dot.attr(rankdir='TB', size='8,8', dpi='200')
        dot.node('S', 'Sentence', fillcolor='#7b68ee', fontcolor='white')
        dot.node('NP', 'Noun Phrase', fillcolor='#2980b9', fontcolor='white')
        dot.node('VP', 'Verb Phrase', fillcolor='#27ae60', fontcolor='white')
        dot.node('Det', 'Determiner\nThe')
        dot.node('N', 'Noun\ncat')
        dot.node('V', 'Verb\nsat')
        dot.node('PP', 'Prep Phrase', fillcolor='#8e44ad', fontcolor='white')
        dot.node('Prep', 'Preposition\non')
        dot.node('NP2', 'Noun Phrase', fillcolor='#2980b9', fontcolor='white')
        dot.node('Det2', 'Determiner\nthe')
        dot.node('N2', 'Noun\nmat')
        dot.edge('S', 'NP')
        dot.edge('S', 'VP')
        dot.edge('NP', 'Det')
        dot.edge('NP', 'N')
        dot.edge('VP', 'V')
        dot.edge('VP', 'PP')
        dot.edge('PP', 'Prep')
        dot.edge('PP', 'NP2')
        dot.edge('NP2', 'Det2')
        dot.edge('NP2', 'N2')
        img_bytes = dot.pipe()
        image_base64 = base64.b64encode(img_bytes).decode('utf-8')
        return {"success": True, "image_data": image_base64, "provider": "Graphviz (Sentence Tree)"}
    except:
        return None

def draw_org_chart():
    try:
        dot = graphviz.Digraph(comment='Org Chart', format='png')
        dot.attr(rankdir='TB', size='8,8', dpi='200')
        dot.node('CEO', 'CEO', shape='ellipse', fillcolor='#e74c3c', fontcolor='white')
        dot.node('CTO', 'CTO', fillcolor='#3498db', fontcolor='white')
        dot.node('CFO', 'CFO', fillcolor='#2ecc71', fontcolor='white')
        dot.node('Dev', 'Dev Team')
        dot.node('Ops', 'Ops Team')
        dot.node('Acc', 'Accounting')
        dot.edge('CEO', 'CTO')
        dot.edge('CEO', 'CFO')
        dot.edge('CTO', 'Dev')
        dot.edge('CTO', 'Ops')
        dot.edge('CFO', 'Acc')
        img_bytes = dot.pipe()
        image_base64 = base64.b64encode(img_bytes).decode('utf-8')
        return {"success": True, "image_data": image_base64, "provider": "Graphviz (Org Chart)"}
    except:
        return None

# ==========================================================
# PLOTLY RENDERERS (STATISTICAL & FINANCIAL CHARTS)
# ==========================================================
def draw_bar_chart():
    data = {'Category': ['A', 'B', 'C', 'D'], 'Values': [23, 45, 56, 78]}
    df = pd.DataFrame(data)
    fig = px.bar(df, x='Category', y='Values', title='Bar Chart', color='Category')
    fig.update_layout(template='plotly_white')
    image_base64 = plotly_to_base64(fig)
    return {"success": True, "image_data": image_base64, "provider": "Plotly (Bar Chart)"}

def draw_pie_chart():
    data = {'Category': ['X', 'Y', 'Z'], 'Values': [30, 50, 20]}
    df = pd.DataFrame(data)
    fig = px.pie(df, values='Values', names='Category', title='Pie Chart')
    fig.update_layout(template='plotly_white')
    image_base64 = plotly_to_base64(fig)
    return {"success": True, "image_data": image_base64, "provider": "Plotly (Pie Chart)"}

def draw_line_chart():
    data = {'Year': [2019, 2020, 2021, 2022, 2023], 'Sales': [150, 230, 180, 275, 340]}
    df = pd.DataFrame(data)
    fig = px.line(df, x='Year', y='Sales', title='Line Chart', markers=True)
    fig.update_layout(template='plotly_white')
    image_base64 = plotly_to_base64(fig)
    return {"success": True, "image_data": image_base64, "provider": "Plotly (Line Chart)"}

# ==========================================================
# MATPLOTLIB RENDERERS (PHYSICS & MATH)
# ==========================================================
def draw_speed_time_graph():
    fig, ax = plt.subplots(figsize=(10, 6))
    t, v = [0, 200, 500, 600], [0, 60, 60, 0]
    ax.plot(t, v, QUALITY_COLORS['navy'], linewidth=3)
    ax.fill_between(t, v, alpha=0.1, color='#3498db')
    ax.set_xlabel('Time (s)', fontsize=16, fontweight='bold', color=QUALITY_COLORS['dark'])
    ax.set_ylabel('Speed (m/s)', fontsize=16, fontweight='bold', color=QUALITY_COLORS['dark'])
    ax.set_title('Speed-Time Graph', fontsize=20, fontweight='bold', color='#1a1a2e', pad=15)
    ax.set_xlim(0, 650)
    ax.set_ylim(0, 75)
    return {"success": True, "image_data": fig_to_base64(fig)}

def draw_force_diagram():
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_xlim(-3.5, 3.5)
    ax.set_ylim(-3.5, 3.5)
    ax.set_aspect('equal')
    ax.axis('off')
    box = patches.FancyBboxPatch((-1.2, -1.2), 2.4, 2.4, boxstyle="round,pad=0.1", facecolor=QUALITY_COLORS['light'], edgecolor=QUALITY_COLORS['dark'], linewidth=3)
    ax.add_patch(box)
    ax.text(0, 0, 'OBJECT', ha='center', va='center', fontsize=15, fontweight='bold', color=QUALITY_COLORS['dark'])
    arrows = [
        (0, -1.4, 0, -1.6, QUALITY_COLORS['red'], 'Weight\n(mg)', 0.3, -2.5),
        (0, 1.4, 0, 1.6, QUALITY_COLORS['green'], 'Normal\n(N)', 0.3, 2.4),
        (-1.4, 0, -1.6, 0, QUALITY_COLORS['orange'], 'Friction\n(f)', -3.2, 0.3),
        (1.4, 0, 1.6, 0, QUALITY_COLORS['blue'], 'Applied\n(F)', 1.6, 0.3),
    ]
    for x1, y1, x2, y2, color, label, tx, ty in arrows:
        ax.arrow(x1, y1, x2, y2, head_width=0.18, head_length=0.25, fc=color, ec=color, linewidth=3, alpha=0.9)
        ax.text(tx, ty, label, fontsize=13, color=color, fontweight='bold', ha='center')
    ax.set_title('Free Body Diagram', fontsize=20, fontweight='bold', color='#1a1a2e', pad=25)
    return {"success": True, "image_data": fig_to_base64(fig)}

# ==========================================================
# HUGGING FACE FLUX GENERATOR (AI GENERATION)
# ==========================================================
async def generate_with_flux(prompt: str) -> dict:
    if not HUGGING_FACE_TOKEN:
        return {"success": False, "error": "HF_TOKEN not set in .env file"}
    try:
        headers = {"Authorization": f"Bearer {HUGGING_FACE_TOKEN}"}
        enhanced_prompt = f"Professional educational infographic diagram: {prompt}. Clean white background, sharp English labels, textbook quality."
        print(f"🖼️ Hugging Face FLUX: generating...")
        response = requests.post(HF_API_FLUX, headers=headers, json={"inputs": enhanced_prompt}, timeout=60)
        if response.status_code != 200:
            return {"success": False, "error": f"Hugging Face error: HTTP {response.status_code}"}
        image_base64 = base64.b64encode(response.content).decode('utf-8')
        if len(image_base64) > MIN_IMAGE_SIZE:
            return {"success": True, "image_data": image_base64, "provider": "Hugging Face FLUX"}
        return {"success": False, "error": "Generated image was too small"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==========================================================
# ROUTER & DETECTION
# ==========================================================
def detect_diagram_types(answer_text: str) -> list:
    detected = []
    lower = answer_text.lower()
    detection_rules = [
        ("speed-time", "speed-time"), ("speed time", "speed-time"), ("velocity", "speed-time"),
        ("force diagram", "force-diagram"), ("free body", "force-diagram"), 
        ("magnetic", "magnetic-field"), ("field lines", "magnetic-field"),
        ("wave", "wave-diagram"), ("amplitude", "wave-diagram"), ("wavelength", "wave-diagram"),
        ("refraction", "refraction"), ("light ray", "refraction"), 
        ("circuit", "circuit-diagram"), ("resistor", "circuit-diagram"), ("battery", "circuit-diagram"),
        ("half-life", "half-life"), ("decay", "half-life"), ("radioactive", "half-life"),
        ("convection", "convection"), ("heater", "convection"),
        ("energy transfer", "energy-transfer"), ("sankey", "energy-transfer"),
        ("generator", "generator"), ("transformer", "transformer"),
        ("flowchart", "flowchart"), ("flow chart", "flowchart"), 
        ("sentence", "sentence-tree"), ("tree", "sentence-tree"),
        ("organizational", "org-chart"), ("org chart", "org-chart"),
        ("bar", "bar-chart"), ("pie", "pie-chart"), ("line", "line-chart"),
        ("mind map", "mind-map"), ("concept map", "mind-map"),
        ("anatomy", "anatomical-diagram"), ("timeline", "timeline"),
        ("graph", "graph"), ("chart", "graph"), ("diagram", "graph")
    ]
    for keyword, d_type in detection_rules:
        if keyword in lower and d_type not in [d[0] for d in detected]:
            detected.append((d_type, keyword))
    return detected

# ==========================================================
# MAIN GENERATOR
# ==========================================================
async def generate_diagram_image(diagram_type: str) -> dict:
    # 1. PLOTLY: Charts
    if diagram_type == "bar-chart": return draw_bar_chart()
    if diagram_type == "pie-chart": return draw_pie_chart()
    if diagram_type == "line-chart": return draw_line_chart()

    # 2. MATPLOTLIB: Physics
    if diagram_type in ["speed-time", "force-diagram", "magnetic-field", "wave-diagram", "refraction", "circuit-diagram", "half-life", "convection", "energy-transfer", "generator", "transformer", "graph"]:
        func = {"speed-time": draw_speed_time_graph, "force-diagram": draw_force_diagram}.get(diagram_type)
        if func:
            try:
                result = func()
                if result.get("success"):
                    result["type"] = diagram_type
                    return result
            except:
                pass

    # 3. HUGGING FACE FLUX: Everything else
    prompt = f"Professional educational diagram of {diagram_type.replace('-', ' ')}. Clean white background, English labels."
    result = await generate_with_flux(prompt)
    if result.get("success"):
        result["type"] = diagram_type
        return result

    # 4. GRAPHVIZ: Structural diagrams (Only if Flux fails)
    if diagram_type == "flowchart":
        result = draw_flowchart()
        if result: return result
    if diagram_type == "sentence-tree":
        result = draw_sentence_tree()
        if result: return result
    if diagram_type == "org-chart":
        result = draw_org_chart()
        if result: return result

    return {"success": False, "error": "All providers failed"}

async def generate_all_diagrams(answer_text: str, subject: str = "general") -> list:
    diagram_types = detect_diagram_types(answer_text)
    if not diagram_types: return []
    
    stem_subjects = ["physics", "chemistry", "biology", "mathematics", "engineering"]
    if subject not in stem_subjects:
        subject_diagram_map = {
            "english": ["sentence-tree", "mind-map", "timeline"],
            "computer_science": ["flowchart", "org-chart", "graph"],
            "history": ["timeline"],
            "geography": ["mind-map"],
            "medicine": ["anatomical-diagram"],
            "economics": ["bar-chart", "line-chart", "pie-chart"],
            "general": ["graph", "mind-map", "flowchart"],
        }
        allowed = subject_diagram_map.get(subject, subject_diagram_map["general"])
        diagram_types = [(d, k) for d, k in diagram_types if d in allowed]

    diagram_types = diagram_types[:3]
    images = []
    for diagram_type, keyword in diagram_types:
        result = await generate_diagram_image(diagram_type)
        if result.get("success"):
            result["keyword"] = keyword
            images.append(result)
    return images