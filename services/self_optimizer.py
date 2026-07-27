"""
Vision AI v2.0 - Self-Learning Optimizer
==========================================
AGI-level learning engine that improves from every interaction.

Features:
- Interaction tracking and pattern analysis
- Knowledge graph construction
- Provider performance monitoring
- Prompt optimization
- Auto-update checking
- Automatic data recovery & backup
"""

import os
import json
import time
import hashlib
import requests
import threading
from pathlib import Path
from datetime import datetime, timedelta, timezone
from collections import defaultdict, Counter
from typing import Dict, List, Optional

LEARNING_DB_PATH = Path("advanced_learning.json")
KNOWLEDGE_GRAPH_PATH = Path("knowledge_graph.json")
BACKUP_INTERVAL = 30  # Save data every 30 interactions

class AdvancedOptimizer:
    """Self-learning system for continuous improvement."""

    def __init__(self):
        self.data = self._load_database()
        self.knowledge_graph = self._load_knowledge_graph()
        self.session_start = datetime.now(timezone.utc)
        self.session_stats = {
            "diagrams_requested": 0,
            "diagrams_generated": 0,
            "providers_used": defaultdict(int),
            "subjects_covered": set(),
            "failed_attempts": 0,
            "learning_events": 0,
        }
        self.conversation_memory = []
        self._interaction_counter = 0
        self._auto_save_timer = None

    def _load_database(self) -> dict:
        """Load the learning database with auto-recovery on corruption."""
        if LEARNING_DB_PATH.exists():
            try:
                with open(LEARNING_DB_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print("⚠️ advanced_learning.json corrupted. Recreating fresh database...")
                return self._create_fresh_database()
            except Exception:
                pass
        return self._create_fresh_database()

    def _create_fresh_database(self) -> dict:
        return {
            "version": "2.0.0",
            "created": datetime.now(timezone.utc).isoformat(),
            "total_interactions": 0,
            "provider_performance": {},
            "subject_expertise": {},
            "user_preferences": {},
            "knowledge_connections": {},
            "response_quality_scores": [],
            "internet_learnings": [],
            "diagram_type_stats": {},
            "best_diagram_prompts": {},
        }

    def _load_knowledge_graph(self) -> dict:
        if KNOWLEDGE_GRAPH_PATH.exists():
            try:
                with open(KNOWLEDGE_GRAPH_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print("⚠️ knowledge_graph.json corrupted. Recreating fresh graph...")
                return {"concepts": {}, "connections": [], "last_updated": None}
            except Exception:
                pass
        return {"concepts": {}, "connections": [], "last_updated": None}

    def _save_all(self):
        """Atomically save both databases."""
        self.data["last_updated"] = datetime.now(timezone.utc).isoformat()
        self.data["total_interactions"] += 1
        try:
            # Save to a temporary file first, then rename for atomicity
            temp_db = LEARNING_DB_PATH.with_suffix(".tmp")
            with open(temp_db, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2)
            temp_db.rename(LEARNING_DB_PATH)

            temp_graph = KNOWLEDGE_GRAPH_PATH.with_suffix(".tmp")
            with open(temp_graph, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge_graph, f, indent=2)
            temp_graph.rename(KNOWLEDGE_GRAPH_PATH)
        except Exception as e:
            print(f"⚠️ Failed to save optimizer data: {e}")

    def _auto_save(self):
        """Auto-save every BACKUP_INTERVAL interactions."""
        self._interaction_counter += 1
        if self._interaction_counter % BACKUP_INTERVAL == 0:
            self._save_all()
            print(f"💾 Auto-saved optimizer data ({self._interaction_counter} interactions)")

    def learn_from_interaction(self, question: str, answer: str, subject: str,
                               provider: str, success: bool, response_time: float,
                               image_count: int = 0, diagram_type: str = None):
        """Record interaction for learning."""
        self.session_stats["learning_events"] += 1

        # ✅ Atomicity Check: Ensure subject is never empty
        safe_subject = subject if subject else "general"
        safe_provider = provider if provider else "unknown"

        # Update subject expertise
        if safe_subject not in self.data["subject_expertise"]:
            self.data["subject_expertise"][safe_subject] = {"attempts": 0, "successes": 0}
        self.data["subject_expertise"][safe_subject]["attempts"] += 1
        if success:
            self.data["subject_expertise"][safe_subject]["successes"] += 1

        # Update provider performance
        if safe_provider not in self.data["provider_performance"]:
            self.data["provider_performance"][safe_provider] = {"attempts": 0, "successes": 0, "times": [], "scores": []}
        perf = self.data["provider_performance"][safe_provider]
        perf["attempts"] += 1
        if success:
            perf["successes"] += 1
        perf["times"].append(response_time)
        if len(perf["times"]) > 100:
            perf["times"] = perf["times"][-100:]
        perf["avg_response_time"] = sum(perf["times"]) / len(perf["times"])

        # Quality score
        score = 0.0
        if success:
            score += 50
        if response_time < 5:
            score += 20
        elif response_time < 15:
            score += 10
        if image_count > 0:
            score += min(image_count * 10, 30)
        final_score = min(score, 100)
        self.data["response_quality_scores"].append(final_score)
        if len(self.data["response_quality_scores"]) > 1000:
            self.data["response_quality_scores"] = self.data["response_quality_scores"][-1000:]

        # Store score per provider for smarter recommendations
        perf["scores"].append(final_score)
        if len(perf["scores"]) > 100:
            perf["scores"] = perf["scores"][-100:]
        perf["avg_score"] = sum(perf["scores"]) / len(perf["scores"])

        # Track conversation memory (limited to prevent memory bloat)
        self.conversation_memory.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "question": question[:200],
            "provider": safe_provider,
            "success": success,
        })
        if len(self.conversation_memory) > 100:
            self.conversation_memory = self.conversation_memory[-100:]

        # Auto-save
        self._auto_save()

    def get_reasoning_recommendation(self, question: str) -> dict:
        """Recommend reasoning style based on question."""
        q = question.lower()
        if any(w in q for w in ["draw", "plot", "chart", "diagram", "graph"]):
            if any(w in q for w in ["flowchart", "mind map", "tree", "org chart"]):
                return {"style": "diagram_style", "reason": "Diagram request"}
            elif any(w in q for w in ["pie", "bar", "line", "scatter"]):
                return {"style": "chart_style", "reason": "Data chart request"}
            return {"style": "plot_style", "reason": "Plot request"}
        elif any(w in q for w in ["code", "program", "function", "algorithm", "debug"]):
            return {"style": "deepseek_style", "reason": "Technical question"}
        elif any(w in q for w in ["math", "calculate", "equation", "proof", "solve"]):
            return {"style": "deepseek_style", "reason": "Mathematical question"}
        elif any(w in q for w in ["explain", "why", "how", "what is", "describe"]):
            return {"style": "claude_style", "reason": "Explanatory question"}
        return {"style": "claude_style", "reason": "General question"}

    def get_provider_recommendation(self, subject: str = None) -> str:
        """
        Recommend the best AI provider based on historical performance.
        Returns the provider name with the highest average score.
        """
        providers = self.data.get("provider_performance", {})
        if not providers:
            return "auto"

        best_provider = None
        best_score = -1.0

        for provider, stats in providers.items():
            avg_score = stats.get("avg_score", 0)
            if avg_score > best_score:
                best_score = avg_score
                best_provider = provider

        return best_provider if best_provider else "auto"

    def get_session_report(self) -> dict:
        """Generate session summary report."""
        runtime = datetime.now(timezone.utc) - self.session_start
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
            "suggestions": self.get_improvement_suggestions(),
            "top_provider": self.get_provider_recommendation(),
        }

    def get_health_status(self) -> dict:
        """Get optimizer health status."""
        total_attempts = sum(s["attempts"] for s in self.data["subject_expertise"].values())
        total_successes = sum(s["successes"] for s in self.data["subject_expertise"].values())
        return {
            "learning_database": "active" if LEARNING_DB_PATH.exists() else "new",
            "total_interactions": self.data["total_interactions"],
            "subjects_learned": len(self.data["subject_expertise"]),
            "overall_success_rate": f"{(total_successes / max(1, total_attempts) * 100):.1f}%",
            "knowledge_graph_size": len(self.knowledge_graph["concepts"]),
            "internet_learnings": len(self.data["internet_learnings"]),
            "evolution_stage": self._get_evolution_stage(),
            "auto_save_enabled": True,
            "backup_interval": BACKUP_INTERVAL,
        }

    def get_improvement_suggestions(self) -> List[str]:
        """Generate improvement suggestions."""
        suggestions = []
        for subject, stats in self.data["subject_expertise"].items():
            if stats["attempts"] >= 3:
                rate = stats["successes"] / stats["attempts"] * 100
                if rate < 50:
                    suggestions.append(f"Low success rate in {subject} ({rate:.0f}%). Review prompts.")
                elif rate > 90:
                    suggestions.append(f"Excellent performance in {subject} ({rate:.0f}%).")
        return suggestions

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
        return "Super-Intelligent"

# Singleton
optimizer = AdvancedOptimizer()