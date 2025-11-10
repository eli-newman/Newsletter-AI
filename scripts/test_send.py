#!/usr/bin/env python3
"""
Test email send to specific address
"""
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rss_feed_summarizer.pipeline import run_pipeline

if __name__ == "__main__":
    test_email = "eli.newman@du.edu"
    print(f"🧪 Testing email send to: {test_email}")
    print("=" * 80)
    
    try:
        # Run pipeline with test email
        result = run_pipeline(email_recipients=[test_email])
        
        print("\n" + "=" * 80)
        print("✅ Test completed!")
        
        if result and "distribution" in result:
            print(f"📄 Output saved to: {result['distribution']['filepath']}")
            
            # Print email stats
            email_result = result['distribution'].get('email', {})
            if email_result.get('sent', 0) > 0:
                print(f"📧 Email sent successfully!")
                print(f"   Sent: {email_result['sent']}")
                print(f"   Failed: {email_result.get('failed', 0)}")
            else:
                print("⚠️  Email not sent - check configuration")
        
        # Show analytics if available
        try:
            from distribution.analytics import get_tracker
            tracker = get_tracker()
            stats = tracker.get_daily_stats()
            if stats.get('emails_sent', 0) > 0:
                print(f"\n📊 Analytics:")
                print(f"   Emails sent today: {stats['emails_sent']}")
                print(f"   Processing time: {stats.get('processing_time', 0):.2f}s")
        except:
            pass
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

