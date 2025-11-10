#!/usr/bin/env python3
"""
View analytics for newsletter
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from distribution.analytics import get_tracker
from datetime import datetime, timedelta

def view_analytics(days: int = 7):
    """View analytics for the last N days"""
    tracker = get_tracker()
    
    print("=" * 80)
    print("📊 Newsletter Analytics")
    print("=" * 80)
    
    total_sent = 0
    total_opened = 0
    total_clicked = 0
    
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        stats = tracker.get_daily_stats(date)
        
        if stats["emails_sent"] > 0:
            print(f"\n📅 {date}:")
            print(f"   Emails Sent: {stats['emails_sent']}")
            print(f"   Emails Opened: {stats['emails_opened']} ({stats['open_rate']}%)")
            if stats.get('processing_time'):
                print(f"   Processing Time: {stats['processing_time']:.2f}s")
            
            total_sent += stats['emails_sent']
            total_opened += stats['emails_opened']
    
    if total_sent > 0:
        print("\n" + "=" * 80)
        print("📈 Summary (Last {} days):".format(days))
        print("=" * 80)
        print(f"   Total Emails Sent: {total_sent}")
        print(f"   Total Emails Opened: {total_opened} ({total_opened/total_sent*100:.1f}%)")
    
    # Show processing stats
    processing_stats = tracker.get_processing_stats()
    if processing_stats:
        print("\n" + "=" * 80)
        print("⏱️  Latest Processing Stats:")
        print("=" * 80)
        print(f"   Total Time: {processing_stats.get('total_time', 0):.2f}s")
        if processing_stats.get('stages'):
            print("   Stage Breakdown:")
            for stage, duration in processing_stats['stages'].items():
                print(f"     • {stage}: {duration:.2f}s")

if __name__ == "__main__":
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    view_analytics(days)

