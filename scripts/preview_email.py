#!/usr/bin/env python3
"""
Preview email HTML with tracking
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from distribution.distributor import MarkdownDistributor
from rss_feed_summarizer.pipeline import run_pipeline

if __name__ == "__main__":
    print("📧 Generating email preview...")
    
    # Run pipeline to get articles
    result = run_pipeline(email_recipients=["test@example.com"])
    
    if result and "distribution" in result:
        distributor = MarkdownDistributor()
        markdown = result['distribution'].get('markdown', '')
        
        # Generate HTML with tracking
        test_email = "eli.newman@du.edu"
        newsletter_id = "20251109-231447"
        html = distributor.markdown_to_html(markdown, email=test_email, newsletter_id=newsletter_id)
        
        # Save preview
        preview_file = Path("output/email_preview.html")
        with open(preview_file, 'w') as f:
            f.write(html)
        
        print(f"✅ Email preview saved to: {preview_file}")
        print(f"\n📊 Tracking Info:")
        print(f"   • Email: {test_email}")
        print(f"   • Newsletter ID: {newsletter_id}")
        print(f"   • Tracking pixel included: Yes")
        print(f"   • Links wrapped with tracking: Yes")
        print(f"\n💡 Open {preview_file} in a browser to see the formatted email")

