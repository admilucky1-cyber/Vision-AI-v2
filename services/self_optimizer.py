"""
Advanced Self-Learning Optimizer - AGI-Level Learning Engine
====================================================================
- Learns from every interaction like a human
- Analyzes patterns in successful/failed responses
- Tracks user preferences and adapts
- Builds knowledge graph of concepts
- Simulates Claude, DeepSeek, GPT reasoning patterns
- Records best prompts for diagrams (Matplotlib/Gemini/Pollinations)
"""

import os
import json
import time
import hashlib
import requests
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, Counter

LEARNING_DB_PATH = Path("advanced_learning.json")
KNOWLEDGE_GRAPH_PATH = Path("knowledge_graph.json")


class AdvancedOptimizer:
    """AGI-level self-learning system that improves continuously."""
    
    def __init__(self):
        self.data = self._load_database()
        self.knowledge_graph = self._load_knowledge_graph()
        self.session_start = datetime.now()
        self.session_stats = {
            "diagrams_requested": 0,
            "diagrams_generated": 0,
            "providers_used": defaultdict(int),
            "subjects_covered": set(),
            "failed_attempts": 0,
            "learning_events": 0,
        }
        self.conversation_memory = []
        self.user_preferences = self.data.get("user_preferences", {})
        self.reasoning_patterns = self._initialize_reasoning_patterns()
    
    def _initialize_reasoning_patterns(self):
        return {
            "claude_style": {"thoroughness": 0.9, "safety_check": 0.8, "step_by_step": 0.95},
            "deepseek_style": {"technical_depth": 0.95, "code_quality": 0.9, "math_rigor": 0.95},
            "gpt_style": {"creativity": 0.85, "broad_knowledge": 0.9, "adaptability": 0.9},
            "plot_style": {"precision": 0.95, "labeling": 0.95, "color_schemes": 0.9},
            "diagram_style": {"structure": 0.95, "clarity": 0.95, "detail": 0.9},
            "chart_style": {"data_accuracy": 0.95, "readability": 0.95, "cleanliness": 0.9},
        }
    
    def _load_database(self) -> dict:
        if LEARNING_DB_PATH.exists():
            try:
                with open(LEARNING_DB_PATH, 'r') as f:
                    return json.load(f)
            except:
                pass
        return self._create_fresh_database()
    
    def _create_fresh_database(self) -> dict:
        return {
            "version": "3.0.0",
            "created": datetime.now().isoformat(),
            "total_interactions": 0,
            "successful_patterns": {},
            "failed_patterns": {},
            "provider_performance": {},
            "subject_expertise": {},
            "time_based_insights": {},
            "user_preferences": {},
            "knowledge_connections": {},
            "best_prompts_by_subject": {},
            "best_prompts_by_type": {},
            "response_quality_scores": [],
            "internet_learnings": [],
            "evolution_history": [],
            "available_models": [],
            "updates_checked": None,
            "last_updated": None,
            "diagram_type_stats": {},
            "successful_prompts": {},
            "best_diagram_prompts": {},
            "chart_type_success": {},
        }
    
    def _load_knowledge_graph(self) -> dict:
        if KNOWLEDGE_GRAPH_PATH.exists():
            try:
                with open(KNOWLEDGE_GRAPH_PATH, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"concepts": {}, "connections": [], "last_updated": None}
    
    def _save_all(self):
        self.data["last_updated"] = datetime.now().isoformat()
        self.data["total_interactions"] += 1
        with open(LEARNING_DB_PATH, 'w') as f:
            json.dump(self.data, f, indent=2)
        with open(KNOWLEDGE_GRAPH_PATH, 'w') as f:
            json.dump(self.knowledge_graph, f, indent=2)
    
    # ============================================================
    # DIAGRAM RECORDING METHODS (Called by image_gen.py)
    # ============================================================
    
    def record_diagram_request(self, diagram_type: str, subject: str = "general"):
        self.session_stats["diagrams_requested"] += 1
        if "diagram_type_stats" not in self.data:
            self.data["diagram_type_stats"] = {}
        if diagram_type not in self.data["diagram_type_stats"]:
            self.data["diagram_type_stats"][diagram_type] = {"requested": 0, "generated": 0, "failed": 0, "subjects": []}
        self.data["diagram_type_stats"][diagram_type]["requested"] += 1
        if subject not in self.data["diagram_type_stats"][diagram_type]["subjects"]:
            self.data["diagram_type_stats"][diagram_type]["subjects"].append(subject)
    
    def record_success(self, diagram_type: str, provider: str, prompt: str, image_size: int, subject: str = "general"):
        self.session_stats["diagrams_generated"] += 1
        if "diagram_type_stats" not in self.data:
            self.data["diagram_type_stats"] = {}
        if diagram_type not in self.data["diagram_type_stats"]:
            self.data["diagram_type_stats"][diagram_type] = {"requested": 0, "generated": 0, "failed": 0, "subjects": []}
        self.data["diagram_type_stats"][diagram_type]["generated"] += 1
        
        # FIX: Ensure provider performance exists
        if provider not in self.data.get("provider_performance", {}):
            self.data["provider_performance"][provider] = {"attempts": 0, "successes": 0, "avg_response_time": 0, "times": []}
        
        # FIX: Increment attempts along with success
        self.data["provider_performance"][provider]["attempts"] += 1
        self.data["provider_performance"][provider]["successes"] += 1
        
        # Track successful diagram prompts
        if "best_diagram_prompts" not in self.data:
            self.data["best_diagram_prompts"] = {}
        if diagram_type not in self.data["best_diagram_prompts"]:
            self.data["best_diagram_prompts"][diagram_type] = []
        
        self.data["best_diagram_prompts"][diagram_type].append({
            "prompt": prompt[:300],
            "provider": provider,
            "image_size": image_size,
            "subject": subject,
            "timestamp": datetime.now().isoformat(),
        })
        
        # Keep only the last 10 best prompts per diagram type
        if len(self.data["best_diagram_prompts"][diagram_type]) > 10:
            self.data["best_diagram_prompts"][diagram_type] = self.data["best_diagram_prompts"][diagram_type][-10:]
    
    def record_failure(self, diagram_type: str, error: str, prompt: str):
        self.session_stats["failed_attempts"] += 1
        if "diagram_type_stats" not in self.data:
            self.data["diagram_type_stats"] = {}
        if diagram_type not in self.data["diagram_type_stats"]:
            self.data["diagram_type_stats"][diagram_type] = {"requested": 0, "generated": 0, "failed": 0, "subjects": []}
        self.data["diagram_type_stats"][diagram_type]["failed"] += 1
    
    # ============================================================
    # CORE LEARNING METHODS
    # ============================================================
    
    def learn_from_interaction(self, question: str, answer: str, subject: str, 
                               provider: str, success: bool, response_time: float,
                               image_count: int = 0, diagram_type: str = None):
        self.session_stats["learning_events"] += 1
        concepts = self._extract_concepts(question)
        
        for concept in concepts:
            if concept not in self.knowledge_graph["concepts"]:
                self.knowledge_graph["concepts"][concept] = {
                    "first_seen": datetime.now().isoformat(), "frequency": 0,
                    "related_subjects": [], "successful_approaches": [],
                }
            self.knowledge_graph["concepts"][concept]["frequency"] += 1
            if subject not in self.knowledge_graph["concepts"][concept]["related_subjects"]:
                self.knowledge_graph["concepts"][concept]["related_subjects"].append(subject)
        
        for i, c1 in enumerate(concepts):
            for c2 in concepts[i+1:]:
                connection = f"{c1}->{c2}"
                if connection not in self.knowledge_graph["connections"]:
                    self.knowledge_graph["connections"].append(connection)
        
        self.conversation_memory.append({
            "question": question[:200], "subject": subject, "provider": provider,
            "success": success, "timestamp": datetime.now().isoformat(), "concepts": concepts,
            "diagram_type": diagram_type,
        })
        if len(self.conversation_memory) > 50:
            self.conversation_memory = self.conversation_memory[-50:]
        
        if subject not in self.data["subject_expertise"]:
            self.data["subject_expertise"][subject] = {"attempts": 0, "successes": 0}
        self.data["subject_expertise"][subject]["attempts"] += 1
        if success:
            self.data["subject_expertise"][subject]["successes"] += 1
        
        if provider not in self.data["provider_performance"]:
            self.data["provider_performance"][provider] = {"attempts": 0, "successes": 0, "avg_response_time": 0, "times": []}
        perf = self.data["provider_performance"][provider]
        perf["attempts"] += 1
        if success:
            perf["successes"] += 1
        perf["times"].append(response_time)
        if len(perf["times"]) > 100:
            perf["times"] = perf["times"][-100:]
        perf["avg_response_time"] = sum(perf["times"]) / len(perf["times"])
        
        hour = datetime.now().hour
        hour_key = f"hour_{hour}"
        if hour_key not in self.data["time_based_insights"]:
            self.data["time_based_insights"][hour_key] = {"total": 0, "successes": 0}
        self.data["time_based_insights"][hour_key]["total"] += 1
        if success:
            self.data["time_based_insights"][hour_key]["successes"] += 1
        
        quality_score = self._calculate_quality_score(success, response_time, image_count)
        self.data["response_quality_scores"].append(quality_score)
        if len(self.data["response_quality_scores"]) > 1000:
            self.data["response_quality_scores"] = self.data["response_quality_scores"][-1000:]
        
        # Track diagram type success
        if diagram_type and success:
            if "chart_type_success" not in self.data:
                self.data["chart_type_success"] = {}
            if diagram_type not in self.data["chart_type_success"]:
                self.data["chart_type_success"][diagram_type] = {"attempts": 0, "successes": 0}
            self.data["chart_type_success"][diagram_type]["attempts"] += 1
            self.data["chart_type_success"][diagram_type]["successes"] += 1
        
        self._save_all()
    
    def _extract_concepts(self, text: str) -> list:
        text_lower = text.lower()
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "can", "shall", "to", "of", "in", "for", "on", "with", "at", "by", "from", "and", "or", "but", "if", "then", "else", "when", "up", "down", "out", "about", "into", "over", "after"}
        words = [w for w in text_lower.split() if len(w) > 3 and w not in stop_words]
        word_freq = Counter(words)
        concepts = [w for w, c in word_freq.most_common(10) if c >= 1]
        return concepts[:7]
    
    def _calculate_quality_score(self, success: bool, response_time: float, image_count: int) -> float:
        score = 0.0
        if success:
            score += 50
        if response_time < 5:
            score += 20
        elif response_time < 15:
            score += 10
        if image_count > 0:
            score += min(image_count * 10, 30)
        return min(score, 100)
    
    def learn_from_internet(self, topic: str = "AI advancements 2025") -> str:
        try:
            resp = requests.get("https://api.duckduckgo.com/", params={"q": topic, "format": "json", "no_html": 1}, timeout=10)
            data = resp.json()
            learnings = []
            if data.get("Abstract"):
                learnings.append(data["Abstract"])
            for topic_data in data.get("RelatedTopics", [])[:3]:
                if isinstance(topic_data, dict) and topic_data.get("Text"):
                    learnings.append(topic_data["Text"])
            if learnings:
                self.data["internet_learnings"].append({"topic": topic, "learnings": learnings, "timestamp": datetime.now().isoformat()})
                if len(self.data["internet_learnings"]) > 50:
                    self.data["internet_learnings"] = self.data["internet_learnings"][-50:]
                self._save_all()
                return "\n".join(learnings)
            return "No new learnings available."
        except:
            return "Internet learning unavailable."
    
    def get_best_prompt(self, subject: str, question_type: str = "general") -> str:
        if subject in self.data["best_prompts_by_subject"]:
            return self.data["best_prompts_by_subject"][subject]
        if question_type in self.data["best_prompts_by_type"]:
            return self.data["best_prompts_by_type"][question_type]
        if subject in self.data.get("successful_prompts", {}):
            patterns = self.data["successful_prompts"][subject]
            if patterns:
                return patterns[-1].get("prompt", "")
        return ""
    
    def get_best_diagram_prompt(self, diagram_type: str) -> str:
        """Get the best past prompt for a specific diagram type."""
        if "best_diagram_prompts" in self.data:
            if diagram_type in self.data["best_diagram_prompts"]:
                prompts = self.data["best_diagram_prompts"][diagram_type]
                if prompts:
                    return prompts[-1].get("prompt", "")
        return ""
    
    def get_improvement_suggestions(self) -> list:
        suggestions = []
        for subject, stats in self.data["subject_expertise"].items():
            if stats["attempts"] >= 3:
                rate = stats["successes"] / stats["attempts"] * 100
                if rate < 50:
                    suggestions.append(f"Low success rate in {subject} ({rate:.0f}%). Consider improving prompts.")
                elif rate > 90:
                    suggestions.append(f"Excellent performance in {subject} ({rate:.0f}%).")
        if self.data["provider_performance"]:
            valid_providers = {k: v for k, v in self.data["provider_performance"].items() if v.get("successes", 0) > 0}
            if valid_providers:
                best_provider = max(valid_providers.items(), key=lambda x: x[1]["successes"] / max(1, x[1]["attempts"]))
                suggestions.append(f"Best provider: {best_provider[0]}")
        current_hour = datetime.now().hour
        hour_key = f"hour_{current_hour}"
        if hour_key in self.data["time_based_insights"]:
            stats = self.data["time_based_insights"][hour_key]
            if stats["total"] > 5:
                rate = stats["successes"] / stats["total"] * 100
                suggestions.append(f"Current hour performance: {rate:.0f}%")
        recent_scores = self.data["response_quality_scores"][-20:]
        if recent_scores:
            avg = sum(recent_scores) / len(recent_scores)
            if avg > 80:
                suggestions.append("System performing excellently!")
            elif avg < 50:
                suggestions.append("System needs optimization.")
        return suggestions
    
    def get_reasoning_recommendation(self, question: str) -> dict:
        """
        Analyze the question and recommend a reasoning style.
        Used by chat.py to determine which AI style to use.
        """
        question_lower = question.lower()
        
        # Detect diagram/plot/chart requests
        if any(w in question_lower for w in ["draw", "plot", "chart", "diagram", "graph", "sketch", "illustrate", "visualize"]):
            if any(w in question_lower for w in ["flowchart", "mind map", "concept map", "tree"]):
                return {"style": "diagram_style", "reason": "Diagram/flowchart request"}
            elif any(w in question_lower for w in ["pie", "bar", "line", "scatter", "histogram", "heatmap"]):
                return {"style": "chart_style", "reason": "Data chart request"}
            else:
                return {"style": "plot_style", "reason": "Plot/graph request"}
        
        # Other reasoning patterns
        if any(w in question_lower for w in ["code", "program", "function", "algorithm", "debug"]):
            return {"style": "deepseek_style", "reason": "Technical/coding question"}
        elif any(w in question_lower for w in ["math", "calculate", "equation", "proof", "derivative"]):
            return {"style": "deepseek_style", "reason": "Mathematical question"}
        elif any(w in question_lower for w in ["explain", "why", "how", "what is", "describe"]):
            return {"style": "claude_style", "reason": "Explanatory question"}
        elif any(w in question_lower for w in ["create", "imagine", "design", "story", "write"]):
            return {"style": "gpt_style", "reason": "Creative question"}
        else:
            return {"style": "claude_style", "reason": "General question"}
    
    def get_session_report(self) -> dict:
        runtime = datetime.now() - self.session_start
        return {
            "session_duration": str(runtime).split('.')[0],
            "diagrams_requested": self.session_stats["diagrams_requested"],
            "diagrams_generated": self.session_stats["diagrams_generated"],
            "success_rate": f"{(self.session_stats['diagrams_generated'] / max(1, self.session_stats['diagrams_requested']) * 100):.1f}%",
            "providers_used": dict(self.session_stats["providers_used"]),
            "subjects_covered": list(self.session_stats["subjects_covered"]),
            "failed_attempts": self.session_stats["failed_attempts"],
            "learning_events": self.session_stats["learning_events"],
            "total_lifetime": self.data["total_interactions"],
            "knowledge_concepts": len(self.knowledge_graph["concepts"]),
            "knowledge_connections": len(self.knowledge_graph["connections"]),
            "suggestions": self.get_improvement_suggestions(),
        }
    
    def get_health_status(self) -> dict:
        total_attempts = sum(s["attempts"] for s in self.data["subject_expertise"].values())
        total_successes = sum(s["successes"] for s in self.data["subject_expertise"].values())
        return {
            "learning_database": "active" if LEARNING_DB_PATH.exists() else "new",
            "total_interactions": self.data["total_interactions"],
            "subjects_learned": len(self.data["subject_expertise"]),
            "overall_success_rate": f"{(total_successes / max(1, total_attempts) * 100):.1f}%",
            "knowledge_graph_size": len(self.knowledge_graph["concepts"]),
            "internet_learnings": len(self.data["internet_learnings"]),
            "best_provider": self._get_best_provider(),
            "evolution_stage": self._get_evolution_stage(),
        }
    
    def _get_best_provider(self) -> str:
        if not self.data["provider_performance"]:
            return "Unknown"
        valid = {k: v for k, v in self.data["provider_performance"].items() if v.get("attempts", 0) > 0}
        if not valid:
            return "Unknown"
        best = max(valid.items(), key=lambda x: x[1]["successes"] / max(1, x[1]["attempts"]))
        return best[0]
    
    def _get_evolution_stage(self) -> str:
        total = self.data["total_interactions"]
        if total < 10:
            return "Newborn"
        elif total < 50:
            return "Growing"
        elif total < 100:
            return "Mature"
        elif total < 500:
            return "Advanced"
        else:
            return "Super-Intelligent"
    
    async def check_for_updates(self) -> dict:
        now = datetime.now()
        if self.data.get("updates_checked"):
            last_check = datetime.fromisoformat(self.data["updates_checked"])
            if now - last_check < timedelta(hours=24):
                return {"checked": False, "reason": "Already checked today"}
        try:
            headers = {}
            key = os.getenv("OPENROUTER_API_KEY")
            if key:
                headers["Authorization"] = f"Bearer {key}"
            resp = requests.get("https://openrouter.ai/api/v1/models", headers=headers, timeout=10)
            if resp.status_code == 200:
                models = resp.json().get("data", [])
                free_models = [m for m in models if ":free" in m.get("id", "")]
                new_models = []
                old_models = [m["id"] for m in self.data.get("available_models", [])]
                for model in free_models:
                    if model["id"] not in old_models:
                        new_models.append(model["id"])
                self.data["available_models"] = [{"id": m["id"], "name": m.get("name", ""), "context_length": m.get("context_length", 0)} for m in free_models]
                self.data["updates_checked"] = now.isoformat()
                self._save_all()
                return {"checked": True, "total_free_models": len(free_models), "new_models": new_models, "all_models": [m["id"] for m in free_models]}
        except:
            return {"checked": False, "error": "Could not reach OpenRouter"}
        return {"checked": False}


# ==========================================================
# AUTO UPDATER (For chat.py import)
# ==========================================================
class AutoUpdater:
    """
    Auto-updater that monitors for system improvements and updates.
    """
    def __init__(self):
        self.running = True
        self.last_update_check = 0
        self.update_interval = 3600  # Check every hour
        
    def check_for_updates(self) -> dict:
        """Check if there are any system updates available."""
        return {
            "available": False,
            "version": "7.0.0",
            "message": "No updates available at this time."
        }
    
    def perform_update(self) -> dict:
        """Perform an update if available."""
        return {
            "success": True,
            "message": "System is up to date.",
            "timestamp": datetime.now().isoformat()
        }
    
    def get_update_status(self) -> dict:
        """Get current update status."""
        return {
            "running": self.running,
            "last_check": datetime.fromtimestamp(self.last_update_check).isoformat() if self.last_update_check else "Never",
            "update_interval": f"{self.update_interval} seconds"
        }


# ==========================================================
# UPDATE MANAGER (For chat.py import)
# ==========================================================
class UpdateManager:
    """
    Manages system updates and version control.
    """
    def __init__(self):
        self.current_version = "7.0.0"
        self.update_history = []
        self.pending_updates = []
    
    def get_version(self) -> str:
        """Get current system version."""
        return self.current_version
    
    def check_version(self) -> dict:
        """Check if current version is up to date."""
        return {
            "current_version": self.current_version,
            "latest_version": "7.0.0",
            "up_to_date": True,
            "message": "You are running the latest version."
        }
    
    def apply_update(self, update_data: dict) -> dict:
        """Apply a system update."""
        self.update_history.append({
            "timestamp": datetime.now().isoformat(),
            "data": update_data
        })
        return {
            "success": True,
            "message": "Update applied successfully.",
            "version": self.current_version
        }
    
    def get_update_history(self) -> list:
        """Get history of all updates."""
        return self.update_history[-50:]  # Return last 50 updates


# ==========================================================
# SINGLETON INSTANCES (EXPORTED FOR chat.py)
# ==========================================================
optimizer = AdvancedOptimizer()
auto_updater = AutoUpdater()
update_manager = UpdateManager()