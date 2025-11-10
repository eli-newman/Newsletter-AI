#!/usr/bin/env python3
"""Test script to read names/emails from the database"""
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import directly to avoid circular imports
import gspread
from google.oauth2.service_account import Credentials

def test_read_db():
    """Test reading all records from the database"""
    try:
        # Load credentials from .env file directly
        env_path = Path(__file__).parent / '.env'
        if not env_path.exists():
            raise ValueError(".env file not found")
        
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        # Find the line with GOOGLE_SHEETS_CREDENTIALS=
        start_idx = None
        for i, line in enumerate(lines):
            if line.strip().startswith('GOOGLE_SHEETS_CREDENTIALS='):
                start_idx = i
                break
        
        if start_idx is None:
            raise ValueError("GOOGLE_SHEETS_CREDENTIALS not found in .env")
        
        # Extract JSON (from { to matching })
        json_lines = []
        brace_count = 0
        for i in range(start_idx, len(lines)):
            line = lines[i]
            if i == start_idx:
                # Extract everything after =
                json_part = line.split('=', 1)[1].strip()
                json_lines.append(json_part)
                brace_count = json_part.count('{') - json_part.count('}')
            else:
                # Remove leading spaces but keep structure
                stripped = line.rstrip()
                json_lines.append(stripped)
                brace_count += stripped.count('{') - stripped.count('}')
                if brace_count == 0:
                    break
        
        credentials_json = '\n'.join(json_lines)
        
        # Parse JSON credentials
        try:
            credentials_info = json.loads(credentials_json)
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON. Extracted text:\n{credentials_json[:200]}...")
            raise ValueError(f"Invalid JSON in GOOGLE_SHEETS_CREDENTIALS: {e}")
        
        # Define the scope
        scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Create credentials object
        credentials = Credentials.from_service_account_info(
            credentials_info, 
            scopes=scope
        )
        
        # Authorize and open the sheet
        gc = gspread.authorize(credentials)
        sheet_id = os.getenv('SHEET_ID')
        if not sheet_id:
            # Try reading from .env file directly
            env_path = Path(__file__).parent / '.env'
            if env_path.exists():
                with open(env_path, 'r') as f:
                    for line in f:
                        if line.strip().startswith('SHEET_ID='):
                            sheet_id = line.split('=', 1)[1].strip()
                            break
        if not sheet_id:
            raise ValueError("SHEET_ID not found")
        
        sheet = gc.open_by_key(sheet_id).sheet1
        
        # Get all records
        all_records = sheet.get_all_records()
        
        print(f"\n📊 Database Records ({len(all_records)} total):")
        print("=" * 80)
        
        # Show headers
        headers = sheet.row_values(1)
        print(f"Columns: {headers}")
        print("-" * 80)
        
        # Show all records
        for idx, record in enumerate(all_records, start=1):
            print(f"\nRecord {idx}:")
            for key, value in record.items():
                print(f"  {key}: {value}")
        
        # Get active subscribers (emails/names)
        print("\n" + "=" * 80)
        print("📧 Active Subscribers (Emails/Names):")
        print("-" * 80)
        active_count = 0
        for record in all_records:
            # Check both possible column names (Email/email, Active/subscribed)
            email = record.get('Email', record.get('email', '')).strip()
            is_active = (
                record.get('Active', record.get('subscribed', '')).upper() == 'TRUE' or
                record.get('subscribed', '').upper() == 'TRUE'
            )
            
            if is_active and email:
                active_count += 1
                print(f"  {active_count}. {email}")
        
        print(f"\n✅ Successfully read {active_count} active subscribers")
        return True
        
    except Exception as e:
        print(f"❌ Error reading database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_read_db()

