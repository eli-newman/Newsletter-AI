"""
Tests for Google Sheets database integration
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from distribution.sheets_db import SheetsSubscriberDB, validate_email, get_all_subscribers


class TestEmailValidation:
    """Test email validation function"""
    
    def test_valid_email(self):
        """Test valid email addresses"""
        assert validate_email('test@example.com') == True
        assert validate_email('user.name@domain.co.uk') == True
        assert validate_email('test+tag@example.com') == True
    
    def test_invalid_email(self):
        """Test invalid email addresses"""
        assert validate_email('invalid-email') == False
        assert validate_email('@example.com') == False
        assert validate_email('test@') == False
        assert validate_email('test@.com') == False
        assert validate_email('') == False


class TestSheetsSubscriberDB:
    """Test SheetsSubscriberDB class"""
    
    @patch('distribution.sheets_db.gspread')
    @patch('distribution.sheets_db.Credentials')
    def test_init_success(self, mock_credentials, mock_gspread, mock_sheets_credentials):
        """Test successful initialization"""
        mock_gc = Mock()
        mock_sheet = Mock()
        mock_gc.open_by_key.return_value.sheet1 = mock_sheet
        mock_sheet.row_values.return_value = ['Email', 'Subscribed Date', 'Active']
        mock_gspread.authorize.return_value = mock_gc
        
        db = SheetsSubscriberDB()
        assert db.sheet is not None
    
    def test_init_missing_credentials(self, monkeypatch):
        """Test initialization with missing credentials"""
        monkeypatch.delenv('GOOGLE_SHEETS_CREDENTIALS', raising=False)
        
        with pytest.raises(ValueError, match="GOOGLE_SHEETS_CREDENTIALS"):
            SheetsSubscriberDB()
    
    def test_init_missing_sheet_id(self, monkeypatch):
        """Test initialization with missing sheet ID"""
        monkeypatch.setenv('GOOGLE_SHEETS_CREDENTIALS', '{"type": "service_account"}')
        monkeypatch.delenv('SHEET_ID', raising=False)
        
        with pytest.raises(ValueError, match="SHEET_ID"):
            with patch('distribution.sheets_db.gspread'):
                SheetsSubscriberDB()
    
    @patch('distribution.sheets_db.gspread')
    @patch('distribution.sheets_db.Credentials')
    def test_add_subscriber_success(self, mock_credentials, mock_gspread, mock_sheets_credentials):
        """Test adding a subscriber successfully"""
        mock_gc = Mock()
        mock_sheet = Mock()
        mock_sheet.col_values.return_value = ['Email']  # No existing emails
        mock_gc.open_by_key.return_value.sheet1 = mock_sheet
        mock_gspread.authorize.return_value = mock_gc
        
        db = SheetsSubscriberDB()
        result = db.add_subscriber('new@example.com')
        
        assert result['success'] == True
        assert result['email'] == 'new@example.com'
        mock_sheet.append_row.assert_called_once()
    
    @patch('distribution.sheets_db.gspread')
    @patch('distribution.sheets_db.Credentials')
    def test_add_subscriber_duplicate(self, mock_credentials, mock_gspread, mock_sheets_credentials):
        """Test adding duplicate subscriber"""
        mock_gc = Mock()
        mock_sheet = Mock()
        mock_sheet.col_values.return_value = ['Email', 'existing@example.com']
        mock_gc.open_by_key.return_value.sheet1 = mock_sheet
        mock_gspread.authorize.return_value = mock_gc
        
        db = SheetsSubscriberDB()
        result = db.add_subscriber('existing@example.com')
        
        assert result['success'] == False
        assert 'already subscribed' in result['message'].lower()
    
    @patch('distribution.sheets_db.gspread')
    @patch('distribution.sheets_db.Credentials')
    def test_add_subscriber_invalid_email(self, mock_credentials, mock_gspread, mock_sheets_credentials):
        """Test adding subscriber with invalid email"""
        mock_gc = Mock()
        mock_sheet = Mock()
        mock_gc.open_by_key.return_value.sheet1 = mock_sheet
        mock_gspread.authorize.return_value = mock_gc
        
        db = SheetsSubscriberDB()
        result = db.add_subscriber('invalid-email')
        
        assert result['success'] == False
        assert 'invalid' in result['message'].lower()
    
    @patch('distribution.sheets_db.gspread')
    @patch('distribution.sheets_db.Credentials')
    def test_get_all_subscribers(self, mock_credentials, mock_gspread, mock_sheets_credentials):
        """Test getting all active subscribers"""
        mock_gc = Mock()
        mock_sheet = Mock()
        mock_sheet.get_all_records.return_value = [
            {'Email': 'active1@example.com', 'Active': 'TRUE'},
            {'Email': 'active2@example.com', 'Active': 'TRUE'},
            {'Email': 'inactive@example.com', 'Active': 'FALSE'},
        ]
        mock_gc.open_by_key.return_value.sheet1 = mock_sheet
        mock_gspread.authorize.return_value = mock_gc
        
        db = SheetsSubscriberDB()
        subscribers = db.get_all_subscribers()
        
        assert len(subscribers) == 2
        assert 'active1@example.com' in subscribers
        assert 'active2@example.com' in subscribers
        assert 'inactive@example.com' not in subscribers
    
    @patch('distribution.sheets_db.gspread')
    @patch('distribution.sheets_db.Credentials')
    def test_remove_subscriber(self, mock_credentials, mock_gspread, mock_sheets_credentials):
        """Test removing a subscriber"""
        mock_gc = Mock()
        mock_sheet = Mock()
        mock_cell = Mock()
        mock_cell.row = 2
        mock_sheet.find.return_value = mock_cell
        mock_gc.open_by_key.return_value.sheet1 = mock_sheet
        mock_gspread.authorize.return_value = mock_gc
        
        db = SheetsSubscriberDB()
        result = db.remove_subscriber('test@example.com')
        
        assert result['success'] == True
        mock_sheet.update_cell.assert_called_once_with(2, 3, "FALSE")


class TestConvenienceFunctions:
    """Test convenience functions"""
    
    @patch('distribution.sheets_db.SheetsSubscriberDB')
    def test_get_all_subscribers_function(self, mock_db_class, mock_sheets_credentials):
        """Test get_all_subscribers convenience function"""
        mock_db = Mock()
        mock_db.get_all_subscribers.return_value = ['test@example.com']
        mock_db_class.return_value = mock_db
        
        subscribers = get_all_subscribers()
        assert subscribers == ['test@example.com']

