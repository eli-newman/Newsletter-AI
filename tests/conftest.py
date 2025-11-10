"""
Pytest configuration and shared fixtures
"""
import pytest
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, patch

@pytest.fixture
def sample_article():
    """Sample article for testing"""
    return {
        'title': 'New AI Model Released',
        'link': 'https://example.com/article1',
        'published': datetime.now() - timedelta(hours=1),
        'summary': 'A new AI model has been released with improved capabilities.',
        'content': 'A new AI model has been released with improved capabilities. This model shows significant improvements in natural language understanding.',
        'source': 'AI News Blog'
    }

@pytest.fixture
def sample_articles(sample_article):
    """List of sample articles"""
    return [
        sample_article,
        {
            'title': 'Machine Learning Framework Update',
            'link': 'https://example.com/article2',
            'published': datetime.now() - timedelta(hours=2),
            'summary': 'Popular ML framework gets major update.',
            'content': 'Popular ML framework gets major update with new features.',
            'source': 'Tech Blog'
        },
        {
            'title': 'Enterprise AI Adoption',
            'link': 'https://example.com/article3',
            'published': datetime.now() - timedelta(hours=3),
            'summary': 'More enterprises adopting AI solutions.',
            'content': 'More enterprises adopting AI solutions for automation.',
            'source': 'Business News'
        }
    ]

@pytest.fixture
def mock_openai_api_key(monkeypatch):
    """Mock OpenAI API key"""
    monkeypatch.setenv('OPENAIAPIKEY', 'test-api-key-12345')

@pytest.fixture
def mock_sheets_credentials(monkeypatch):
    """Mock Google Sheets credentials"""
    mock_creds = {
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "test-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n",
        "client_email": "test@test-project.iam.gserviceaccount.com",
        "client_id": "123456",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test%40test-project.iam.gserviceaccount.com",
        "universe_domain": "googleapis.com"
    }
    monkeypatch.setenv('GOOGLE_SHEETS_CREDENTIALS', str(mock_creds).replace("'", '"'))
    monkeypatch.setenv('SHEET_ID', 'test-sheet-id-12345')

@pytest.fixture
def mock_email_config(monkeypatch):
    """Mock email configuration"""
    monkeypatch.setenv('SMTP_USER', 'test@example.com')
    monkeypatch.setenv('GMAIL_APP_PASSWORD', 'test-password-12345')

@pytest.fixture
def categorized_articles(sample_articles):
    """Sample categorized articles"""
    return {
        'TOOLS_AND_FRAMEWORKS': [sample_articles[1]],
        'MODELS_AND_INFRASTRUCTURE': [sample_articles[0]],
        'ENTERPRISE_AND_MARKET': [sample_articles[2]]
    }

