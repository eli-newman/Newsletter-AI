#!/usr/bin/env python3
"""
Simple tracking server for email opens and clicks
Run this server to enable tracking functionality
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from flask import Flask, redirect, request, send_file
    from distribution.analytics import get_tracker
    import io
    
    app = Flask(__name__)
    tracker = get_tracker()
    
    # 1x1 transparent PNG pixel
    TRANSPARENT_PIXEL = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
    
    @app.route('/track/open/<tracking_id>')
    def track_open(tracking_id):
        """Track email open"""
        tracker.record_email_open(
            tracking_id,
            user_agent=request.headers.get('User-Agent'),
            ip=request.remote_addr
        )
        # Return 1x1 transparent pixel
        return send_file(
            io.BytesIO(TRANSPARENT_PIXEL),
            mimetype='image/png',
            as_attachment=False
        )
    
    # Link click tracking removed for privacy/trust
    
    @app.route('/health')
    def health():
        """Health check endpoint"""
        return {"status": "ok"}, 200
    
    if __name__ == '__main__':
        print("🚀 Starting tracking server on http://localhost:5000")
        print("📊 Tracking endpoints:")
        print("   - Email opens: http://localhost:5000/track/open/<id>")
        print("   - Link clicks: http://localhost:5000/track/click/<id>")
        print("\n⚠️  Update TRACKING_DOMAIN in .env to use this server")
        app.run(host='0.0.0.0', port=5000, debug=False)
        
except ImportError:
    print("❌ Flask not installed. Install with: pip install flask")
    print("   Or use an external tracking service")
    sys.exit(1)

