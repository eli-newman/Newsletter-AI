# Analytics Setup Guide

## Overview

The analytics system tracks:
1. **Email Opens** - Via tracking pixel (1x1 transparent image)
2. **Link Clicks** - Via URL redirects
3. **Processing Times** - Per-stage timing in the pipeline

## How It Works

### Email Opens
- Each email includes a 1x1 transparent tracking pixel
- When email client loads images, it requests the tracking URL
- This records an "open" event

### Link Clicks
- All article links are wrapped with tracking URLs
- When clicked, redirects to original URL
- Records click event with article title and email

### Processing Times
- Automatically tracked for each pipeline stage
- Shows total time and per-stage breakdown

## Current Implementation

### File-Based Storage (Default)
- Events stored in `analytics/events_YYYY-MM-DD.jsonl`
- Link mappings in `analytics/link_mappings.json`
- Processing stats in memory (can be saved)

### View Analytics
```bash
python scripts/view_analytics.py [days]
# Example: python scripts/view_analytics.py 7
```

## Setting Up Tracking Endpoints

To actually track opens/clicks, you need to set up tracking endpoints:

### Option 1: Simple Flask Server (Recommended for Testing)

Create `scripts/tracking_server.py`:
```python
from flask import Flask, redirect, request
from distribution.analytics import get_tracker

app = Flask(__name__)
tracker = get_tracker()

@app.route('/track/open/<tracking_id>')
def track_open(tracking_id):
    tracker.record_email_open(tracking_id, 
                              user_agent=request.headers.get('User-Agent'),
                              ip=request.remote_addr)
    # Return 1x1 transparent pixel
    pixel = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
    return pixel, 200, {'Content-Type': 'image/png'}

@app.route('/track/click/<tracking_id>')
def track_click(tracking_id):
    original_url = tracker.record_link_click(tracking_id,
                                            user_agent=request.headers.get('User-Agent'),
                                            ip=request.remote_addr)
    if original_url:
        return redirect(original_url, code=302)
    return "Link not found", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### Option 2: Use Existing Service
- Update tracking URLs in `analytics.py` to point to your domain
- Deploy tracking endpoints on your server
- Or use a service like Mailgun, SendGrid (they provide tracking)

## Configuration

Update tracking URLs in `distribution/analytics.py`:
```python
def create_tracking_pixel_url(self, email: str, newsletter_id: str) -> str:
    # Change to your domain
    return f"https://your-domain.com/track/open/{tracking_id}"

def create_tracking_link(self, original_url: str, email: str, article_title: str) -> str:
    # Change to your domain
    return f"https://your-domain.com/track/click/{tracking_id}"
```

## Privacy Notes

- Tracking pixels only work if email client loads images
- Some email clients block images by default
- Users can disable image loading (won't track opens)
- Link clicks are always tracked if links are clicked

## Future Enhancements

1. **Google Sheets Integration** - Store analytics in Sheets
2. **Dashboard** - Web dashboard for viewing analytics
3. **Email Reports** - Weekly analytics summary emails
4. **A/B Testing** - Test different subject lines, formats

