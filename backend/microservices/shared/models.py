"""
Shared data models for microservices
"""

from dataclasses import dataclass, asdict
from typing import Dict, Optional
from datetime import datetime


@dataclass
class Post:
    """Post data model"""
    id: str
    text: str
    country: str
    timestamp: str
    source: str
    url: str
    author: str
    score: int = 0

    def to_dict(self):
        return asdict(self)


@dataclass
class AnalyzedPost:
    """Analyzed post with emotions"""
    id: str
    text: str
    country: str
    timestamp: str
    source: str
    url: str
    author: str
    score: int
    emotions: Dict[str, float]
    top_emotion: str
    confidence: float
    is_collective: bool = True

    def to_dict(self):
        data = asdict(self)
        return data


@dataclass
class CountryEmotions:
    """Country-level aggregated emotions"""
    country: str
    emotions: Dict[str, float]
    top_emotion: str
    total_posts: int
    last_updated: str

    def to_dict(self):
        return asdict(self)
