#!/usr/bin/env python3
"""
RSS Feed Summarizer Runner
Fetches subscribers from Google Sheets and runs the pipeline
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rss_feed_summarizer.pipeline import run_pipeline
from distribution import get_all_subscribers

if __name__ == "__main__":
    print("🚀 Starting RSS Feed Summarizer...")
    
    try:
        # Get subscribers from Google Sheets
        print("📊 Fetching subscribers from Google Sheets...")
        subscribers = get_all_subscribers()
        
        if not subscribers:
            print("⚠️  No active subscribers found. Running pipeline without email distribution.")
            result = run_pipeline()
        else:
            print(f"✅ Found {len(subscribers)} active subscriber(s)")
            result = run_pipeline(email_recipients=subscribers)
        
        print("✅ Pipeline completed successfully!")
        
        if result and "distribution" in result:
            print(f"📄 Output saved to: {result['distribution']['filepath']}")
            
            # Print email stats if available
            email_result = result['distribution'].get('email', {})
            if email_result.get('sent', 0) > 0:
                print(f"📧 Emails sent: {email_result['sent']}/{email_result['sent'] + email_result.get('failed', 0)}")
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
