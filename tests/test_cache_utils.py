"""
Tests for cache utilities
"""
import pytest
from rss_feed_summarizer.cache_utils import CacheTracker


class TestCacheTracker:
    """Test CacheTracker class"""
    
    def test_init_default(self):
        """Test default initialization"""
        tracker = CacheTracker()
        assert tracker.cost_per_call == 0.01
        assert tracker.cache_hits == 0
        assert tracker.cache_misses == 0
    
    def test_init_custom_cost(self):
        """Test initialization with custom cost"""
        tracker = CacheTracker(cost_per_call=0.05)
        assert tracker.cost_per_call == 0.05
    
    def test_track_cache_hit(self):
        """Test tracking cache hits"""
        tracker = CacheTracker()
        tracker.track_cache_hit()
        assert tracker.cache_hits == 1
        
        tracker.track_cache_hit()
        assert tracker.cache_hits == 2
    
    def test_track_cache_miss(self):
        """Test tracking cache misses"""
        tracker = CacheTracker()
        tracker.track_cache_miss()
        assert tracker.cache_misses == 1
        
        tracker.track_cache_miss()
        assert tracker.cache_misses == 2
    
    def test_get_stats(self):
        """Test getting statistics"""
        tracker = CacheTracker(cost_per_call=0.02)
        tracker.track_cache_hit()
        tracker.track_cache_hit()
        tracker.track_cache_miss()
        
        stats = tracker.get_stats()
        
        assert stats['hits'] == 2
        assert stats['misses'] == 1
        assert stats['total'] == 3
        assert stats['hit_rate'] == pytest.approx(66.67, rel=0.1)
        assert stats['cost_saved'] == 0.04
    
    def test_get_stats_empty(self):
        """Test stats with no hits or misses"""
        tracker = CacheTracker()
        stats = tracker.get_stats()
        
        assert stats['hits'] == 0
        assert stats['misses'] == 0
        assert stats['total'] == 0
        assert stats['hit_rate'] == 0
        assert stats['cost_saved'] == 0
    
    def test_reset(self):
        """Test resetting statistics"""
        tracker = CacheTracker()
        tracker.track_cache_hit()
        tracker.track_cache_miss()
        
        tracker.reset()
        
        assert tracker.cache_hits == 0
        assert tracker.cache_misses == 0

