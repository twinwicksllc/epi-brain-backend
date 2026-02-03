"""
NEBP State Machine
Tracks phases and clarity metrics for siloed product workflows.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

PHASE_DISCOVERY = "discovery"
PHASE_STRATEGY = "strategy"
PHASE_ACTION = "action"

SALES_BOTTLENECK_KEYWORDS = {
    "bottleneck",
    "objection",
    "close",
    "closing",
    "pipeline",
    "lead",
    "leads",
    "quota",
    "conversion",
    "follow up",
    "follow-up",
    "demo",
    "pricing",
    "prospect",
    "revenue"
}

SPIRITUAL_KEYWORDS = {
    "faith",
    "pray",
    "prayer",
    "god",
    "jesus",
    "bible",
    "scripture",
    "church",
    "forgiveness",
    "purpose",
    "sin",
    "grace",
    "worship"
}

EDUCATION_KEYWORDS = {
    "homework",
    "study",
    "exam",
    "test",
    "quiz",
    "math",
    "science",
    "history",
    "essay",
    "reading",
    "problem",
    "grade",
    "algebra",
    "calculus",
    "biology",
    "chemistry",
    "physics",
    "tutor",
    "tutoring"
}

ACTION_KEYWORDS = {
    "next step",
    "plan",
    "action",
    "schedule",
    "implement",
    "practice",
    "try",
    "do",
    "start",
    "commit"
}


class NEBPStateMachine:
    """NEBP phase tracking and clarity metrics engine."""

    @staticmethod
    def _normalize_text(message: str, captured_intent: Optional[str] = None) -> str:
        base = (message or "").lower().strip()
        intent = (captured_intent or "").lower().strip()
        if intent:
            return f"{base} {intent}".strip()
        return base

    @staticmethod
    def _contains_keywords(text: str, keywords: set[str]) -> bool:
        if not text:
            return False
        for keyword in keywords:
            if keyword in text:
                return True
        return False

    @classmethod
    def calculate_clarity_metrics(
        cls,
        message: str,
        discovery_metadata: Optional[Dict[str, Optional[str]]] = None,
        silo_id: Optional[str] = None
    ) -> Dict[str, object]:
        metadata = discovery_metadata or {}
        captured_name = bool(metadata.get("captured_name"))
        captured_intent = bool(metadata.get("captured_intent"))

        combined_text = cls._normalize_text(message, metadata.get("captured_intent"))
        silo_key = (silo_id or "").strip().lower() or None

        silo_focus_identified = False
        if silo_key == "sales":
            silo_focus_identified = cls._contains_keywords(combined_text, SALES_BOTTLENECK_KEYWORDS)
        elif silo_key == "spiritual":
            silo_focus_identified = cls._contains_keywords(combined_text, SPIRITUAL_KEYWORDS)
        elif silo_key == "education":
            silo_focus_identified = cls._contains_keywords(combined_text, EDUCATION_KEYWORDS)
        else:
            silo_focus_identified = False

        action_readiness = cls._contains_keywords(combined_text, ACTION_KEYWORDS)

        total_signals = 2 + (1 if silo_key else 0)
        signal_count = int(captured_name) + int(captured_intent) + (1 if silo_focus_identified else 0)
        topic_clarity_score = round(signal_count / total_signals, 3) if total_signals else 0.0

        return {
            "silo_id": silo_key,
            "name_captured": captured_name,
            "intent_captured": captured_intent,
            "silo_focus_identified": silo_focus_identified,
            "topic_clarity_score": topic_clarity_score,
            "action_readiness": action_readiness,
            "updated_at": datetime.utcnow().isoformat()
        }

    @classmethod
    def update_state(
        cls,
        user,
        message: str,
        discovery_metadata: Optional[Dict[str, Optional[str]]] = None,
        silo_id: Optional[str] = None
    ) -> Dict[str, object]:
        """
        Update the user's NEBP phase and clarity metrics in place.
        Returns the updated clarity metrics.
        """
        if user is None:
            return {}

        current_phase = getattr(user, "nebp_phase", None) or PHASE_DISCOVERY
        metrics = cls.calculate_clarity_metrics(message, discovery_metadata, silo_id=silo_id)

        if current_phase == PHASE_DISCOVERY:
            if metrics.get("name_captured") and metrics.get("intent_captured") and metrics.get("silo_focus_identified"):
                current_phase = PHASE_STRATEGY
        elif current_phase == PHASE_STRATEGY:
            if metrics.get("action_readiness"):
                current_phase = PHASE_ACTION

        user.nebp_phase = current_phase
        user.nebp_clarity_metrics = metrics

        return metrics
