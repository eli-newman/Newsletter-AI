"""
Analytics tracking for newsletter opens, clicks, and processing times
"""
import os
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import hashlib

class AnalyticsTracker:
    def __init__(self, storage_type: str = "file"):
        """
        Initialize analytics tracker
        
        Args:
            storage_type: "file" for local file storage, "sheets" for Google Sheets
        """
        self.storage_type = storage_type
        self.tracking_dir = Path("analytics")
        self.tracking_dir.mkdir(exist_ok=True)
        
        # Processing time tracking
        self.processing_times = {}
        self.start_time = None
        
    def start_processing(self, pipeline_name: str = "newsletter_pipeline"):
        """Start tracking processing time"""
        self.start_time = time.time()
        self.processing_times[pipeline_name] = {
            "start": self.start_time,
            "stages": {}
        }
    
    def track_stage(self, stage_name: str, duration: Optional[float] = None):
        """Track time for a specific pipeline stage"""
        if not self.start_time:
            return
        
        if duration is None:
            duration = time.time() - (self.processing_times.get("newsletter_pipeline", {}).get("last_stage_end", self.start_time))
        
        if "stages" not in self.processing_times.get("newsletter_pipeline", {}):
            self.processing_times["newsletter_pipeline"]["stages"] = {}
        
        self.processing_times["newsletter_pipeline"]["stages"][stage_name] = duration
        self.processing_times["newsletter_pipeline"]["last_stage_end"] = time.time()
    
    def end_processing(self) -> Dict[str, Any]:
        """End processing and return total time"""
        if not self.start_time:
            return {}
        
        total_time = time.time() - self.start_time
        self.processing_times["newsletter_pipeline"]["total_time"] = total_time
        self.processing_times["newsletter_pipeline"]["end"] = time.time()
        
        return self.processing_times["newsletter_pipeline"]
    
    def generate_tracking_id(self, email: str, article_link: Optional[str] = None) -> str:
        """Generate unique tracking ID for email/link"""
        base = f"{email}:{datetime.now().isoformat()}"
        if article_link:
            base += f":{article_link}"
        return hashlib.md5(base.encode()).hexdigest()[:16]
    
    def create_tracking_pixel_url(self, email: str, newsletter_id: str) -> str:
        """Create tracking pixel URL for email open tracking"""
        tracking_id = self.generate_tracking_id(email, newsletter_id)
        # In production, update this to your actual tracking endpoint
        # For local testing, use: http://localhost:5000/track/open/{tracking_id}
        tracking_domain = os.getenv("TRACKING_DOMAIN", "https://your-tracking-domain.com")
        return f"{tracking_domain}/track/open/{tracking_id}"
    
    def record_email_sent(self, email: str, newsletter_id: str, subject: str):
        """Record that an email was sent"""
        event = {
            "type": "email_sent",
            "email": email,
            "newsletter_id": newsletter_id,
            "subject": subject,
            "timestamp": datetime.now().isoformat()
        }
        self._save_event(event)
    
    def record_email_open(self, tracking_id: str, user_agent: Optional[str] = None, ip: Optional[str] = None):
        """Record email open event"""
        event = {
            "type": "email_open",
            "tracking_id": tracking_id,
            "user_agent": user_agent,
            "ip": ip,
            "timestamp": datetime.now().isoformat()
        }
        self._save_event(event)
    
    # Link click tracking removed for privacy/trust
    
    def _save_event(self, event: Dict[str, Any]):
        """Save analytics event to storage"""
        if self.storage_type == "file":
            # Save to daily log file
            today = datetime.now().strftime("%Y-%m-%d")
            log_file = self.tracking_dir / f"events_{today}.jsonl"
            
            with open(log_file, 'a') as f:
                f.write(json.dumps(event) + '\n')
        elif self.storage_type == "sheets":
            # TODO: Implement Google Sheets storage
            pass
    
    def get_daily_stats(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for a specific date"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        log_file = self.tracking_dir / f"events_{date}.jsonl"
        if not log_file.exists():
            return {
                "date": date,
                "emails_sent": 0,
                "emails_opened": 0,
                "links_clicked": 0,
                "open_rate": 0.0,
                "click_rate": 0.0
            }
        
        events = []
        with open(log_file, 'r') as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))
        
        emails_sent = len([e for e in events if e.get("type") == "email_sent"])
        emails_opened = len([e for e in events if e.get("type") == "email_open"])
        
        open_rate = (emails_opened / emails_sent * 100) if emails_sent > 0 else 0.0
        
        return {
            "date": date,
            "emails_sent": emails_sent,
            "emails_opened": emails_opened,
            "open_rate": round(open_rate, 2),
            "processing_time": self.processing_times.get("newsletter_pipeline", {}).get("total_time")
        }
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing time statistics"""
        return self.processing_times.get("newsletter_pipeline", {})

# Global tracker instance
_tracker = None

def get_tracker() -> AnalyticsTracker:
    """Get or create global tracker instance"""
    global _tracker
    if _tracker is None:
        _tracker = AnalyticsTracker()
    return _tracker

