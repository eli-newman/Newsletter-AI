#!/usr/bin/env python3
"""
View OpenAI API cost tracking reports
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cost_tracking import CostTracker
import argparse
from datetime import datetime, timedelta

def main():
    parser = argparse.ArgumentParser(description="View OpenAI API cost tracking")
    parser.add_argument("--date", type=str, help="View costs for specific date (YYYY-MM-DD)")
    parser.add_argument("--days", type=int, default=7, help="View costs for last N days (default: 7)")
    parser.add_argument("--summary", action="store_true", help="Show summary for last N days")
    
    args = parser.parse_args()
    
    tracker = CostTracker()
    
    if args.date:
        # Show specific date
        tracker.print_daily_report(args.date)
    elif args.summary:
        # Show summary
        summary = tracker.get_cost_summary(args.days)
        print(f"\n💰 COST SUMMARY - Last {summary['period_days']} Days")
        print("=" * 60)
        print(f"Total Cost: ${summary['total_cost']:.6f}")
        print("-" * 60)
        
        for day in summary['daily_breakdown']:
            print(f"\n{day['date']}: ${day['total_cost']:.6f}")
            for agent in day['by_agent']:
                print(f"  • {agent['agent']}: ${agent['cost']:.6f} ({agent['calls']} calls)")
        
        print("=" * 60)
    else:
        # Show today's costs
        tracker.print_daily_report()

if __name__ == "__main__":
    main()

