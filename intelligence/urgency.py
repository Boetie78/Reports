"""Urgency classification for executive decision objects."""
from __future__ import annotations


def urgency_from_score(score: int) -> str:
    if score >= 85:
        return "Immediate"
    if score >= 70:
        return "This Week"
    if score >= 50:
        return "This Month"
    if score >= 25:
        return "Monitor"
    return "Ignore"
