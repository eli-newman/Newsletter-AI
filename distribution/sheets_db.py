"""
Google Sheets integration for email subscription management
"""
import os
import json
from datetime import datetime
from typing import List, Dict, Any
import re

try:
    import gspread
    from google.oauth2.service_account import Credentials
    SHEETS_AVAILABLE = True
except ImportError:
    SHEETS_AVAILABLE = False
    print("Warning: gspread not installed. Install with 'pip install gspread google-auth'")

def validate_email(email: str) -> bool:
    """Simple email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

class SheetsSubscriberDB:
    def __init__(self):
        """Initialize Google Sheets connection"""
        if not SHEETS_AVAILABLE:
            raise ImportError("gspread not installed. Install with 'pip install gspread google-auth'")
        
        # Load credentials from environment variable
        credentials_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
        if not credentials_json:
            raise ValueError("GOOGLE_SHEETS_CREDENTIALS environment variable not set")
        
        try:
            # Parse JSON credentials
            credentials_info = json.loads(credentials_json)
            
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
            self.gc = gspread.authorize(credentials)
            self.sheet_id = os.getenv('SHEET_ID')
            if not self.sheet_id:
                raise ValueError("SHEET_ID environment variable not set")
            
            self.sheet = self.gc.open_by_key(self.sheet_id).sheet1
            
            # Ensure headers exist
            self._ensure_headers()
            
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON in GOOGLE_SHEETS_CREDENTIALS")
        except Exception as e:
            raise Exception(f"Failed to connect to Google Sheets: {str(e)}")
    
    def _ensure_headers(self):
        """Ensure the sheet has proper headers"""
        try:
            # Check if headers exist
            headers = self.sheet.row_values(1)
            if not headers or headers[0].lower() != 'email':
                # Add headers matching actual sheet structure
                self.sheet.insert_row(['email', 'subscribed', 'timestamp', 'unsubscribed_at'], 1)
        except Exception as e:
            print(f"Warning: Could not ensure headers: {e}")
    
    def add_subscriber(self, email: str) -> Dict[str, Any]:
        """
        Add a new subscriber to the sheet
        
        Args:
            email: Email address to add
            
        Returns:
            Dict with success status and message
        """
        if not validate_email(email):
            return {
                "success": False,
                "message": "Invalid email format",
                "email": email
            }
        
        try:
            # Check if email already exists
            existing_emails = self.sheet.col_values(1)  # Column A (Email)
            if email.lower() in [e.lower() for e in existing_emails]:
                return {
                    "success": False,
                    "message": "Email already subscribed",
                    "email": email
                }
            
            # Add new subscriber with actual sheet structure
            # Format timestamp to match sheet format: 2025-10-29T22:34:54.102Z
            now = datetime.now()
            timestamp = now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"
            self.sheet.append_row([email, "TRUE", timestamp, ""])
            
            return {
                "success": True,
                "message": "Successfully subscribed!",
                "email": email
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to add subscriber: {str(e)}",
                "email": email
            }
    
    def get_all_subscribers(self) -> List[str]:
        """
        Get all active subscriber emails
        
        Returns:
            List of email addresses
        """
        try:
            # Get all data
            all_data = self.sheet.get_all_records()
            
            # Filter for active subscribers using actual column names
            active_emails = []
            for row in all_data:
                # Check 'subscribed' column (case-insensitive) and 'email' column
                subscribed = row.get('subscribed', row.get('Subscribed', '')).upper()
                email = row.get('email', row.get('Email', '')).strip()
                
                if (subscribed == 'TRUE' and 
                    email and
                    validate_email(email)):
                    active_emails.append(email)
            
            return active_emails
            
        except Exception as e:
            print(f"Error getting subscribers: {e}")
            return []
    
    def remove_subscriber(self, email: str) -> Dict[str, Any]:
        """
        Mark a subscriber as inactive (soft delete)
        
        Args:
            email: Email address to remove
            
        Returns:
            Dict with success status and message
        """
        try:
            # Find the row with this email
            cell = self.sheet.find(email, in_column=1)
            if not cell:
                return {
                    "success": False,
                    "message": "Email not found",
                    "email": email
                }
            
            # Update the subscribed column to FALSE (column 2) and set unsubscribed_at timestamp (column 4)
            now = datetime.now()
            unsubscribed_timestamp = now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"
            self.sheet.update_cell(cell.row, 2, "FALSE")  # Column B (subscribed)
            self.sheet.update_cell(cell.row, 4, unsubscribed_timestamp)  # Column D (unsubscribed_at)
            
            return {
                "success": True,
                "message": "Successfully unsubscribed",
                "email": email
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to remove subscriber: {str(e)}",
                "email": email
            }

# Convenience functions for easy import
def add_subscriber(email: str) -> Dict[str, Any]:
    """Add a subscriber (convenience function)"""
    db = SheetsSubscriberDB()
    return db.add_subscriber(email)

def get_all_subscribers() -> List[str]:
    """Get all subscribers (convenience function)"""
    db = SheetsSubscriberDB()
    return db.get_all_subscribers()

def remove_subscriber(email: str) -> Dict[str, Any]:
    """Remove a subscriber (convenience function)"""
    db = SheetsSubscriberDB()
    return db.remove_subscriber(email)