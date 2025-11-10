"""
Cache utilities for tracking LLM cache hits and costs
"""
import sqlite3
import os
from typing import Dict, Any

class CacheTracker:
    """Track cache hits/misses and estimate cost savings"""
    
    def __init__(self, cost_per_call: float = 0.01):
        """
        Initialize cache tracker
        
        Args:
            cost_per_call: Estimated cost per LLM call (default: $0.01)
        """
        self.cost_per_call = cost_per_call
        self.cache_hits = 0
        self.cache_misses = 0
        self.cache_dir = "cache"
        
    def track_cache_hit(self):
        """Record a cache hit"""
        self.cache_hits += 1
    
    def record_hit(self):
        """Record a cache hit (alias for compatibility)"""
        self.track_cache_hit()
        
    def track_cache_miss(self):
        """Record a cache miss"""
        self.cache_misses += 1
    
    def record_miss(self):
        """Record a cache miss (alias for compatibility)"""
        self.track_cache_miss()
        
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total * 100) if total > 0 else 0
        cost_saved = self.cache_hits * self.cost_per_call
        
        return {
            "hits": self.cache_hits,
            "misses": self.cache_misses,
            "total": total,
            "hit_rate": round(hit_rate, 2),
            "cost_saved": round(cost_saved, 4),
            "estimated_savings": f"${cost_saved:.4f}",  # For display compatibility
        }
        
    def reset(self):
        """Reset cache statistics"""
        self.cache_hits = 0
        self.cache_misses = 0

