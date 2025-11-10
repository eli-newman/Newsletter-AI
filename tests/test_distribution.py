"""
Tests for distribution module
"""
import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from distribution.distributor import MarkdownDistributor, use_distributor


class TestMarkdownDistributor:
    """Test MarkdownDistributor class"""
    
    def test_init(self, tmp_path):
        """Test distributor initialization"""
        output_dir = str(tmp_path / "output")
        distributor = MarkdownDistributor(output_dir=output_dir)
        assert distributor.output_dir == output_dir
        assert os.path.exists(output_dir)
    
    def test_format_articles(self, sample_articles, categorized_articles):
        """Test article formatting"""
        distributor = MarkdownDistributor()
        markdown = distributor.format_articles(
            sample_articles,
            categorized_articles,
            daily_overview="Test overview"
        )
        
        assert isinstance(markdown, str)
        assert "# AI News Digest" in markdown
        assert "Daily Overview" in markdown
        assert "New AI Model Released" in markdown
    
    def test_format_articles_no_overview(self, sample_articles, categorized_articles):
        """Test formatting without daily overview"""
        distributor = MarkdownDistributor()
        markdown = distributor.format_articles(
            sample_articles,
            categorized_articles
        )
        
        assert isinstance(markdown, str)
        assert "New AI Model Released" in markdown
    
    def test_save_markdown(self, sample_articles, categorized_articles, tmp_path):
        """Test saving markdown to file"""
        output_dir = str(tmp_path / "output")
        distributor = MarkdownDistributor(output_dir=output_dir)
        
        markdown = distributor.format_articles(sample_articles, categorized_articles)
        filepath = distributor.save_markdown(markdown)
        
        assert os.path.exists(filepath)
        assert filepath.endswith('.md')
        
        with open(filepath, 'r') as f:
            content = f.read()
            assert "New AI Model Released" in content
    
    def test_clean_html(self):
        """Test HTML cleaning"""
        distributor = MarkdownDistributor()
        
        html_text = "<p>Test content</p><br/>More content"
        cleaned = distributor._clean_html(html_text)
        
        assert "<p>" not in cleaned
        assert "<br/>" not in cleaned
        assert "Test content" in cleaned
    
    @patch('distribution.distributor.markdown')
    def test_markdown_to_html(self, mock_markdown):
        """Test markdown to HTML conversion"""
        mock_markdown.markdown.return_value = "<h1>Test</h1>"
        
        distributor = MarkdownDistributor()
        html = distributor.markdown_to_html("# Test")
        
        assert isinstance(html, str)
        assert "<html>" in html
        assert "<body>" in html
    
    @patch('distribution.distributor.smtplib.SMTP_SSL')
    @patch('distribution.distributor.rss_feed_summarizer.config')
    def test_send_email_smtp_success(self, mock_config, mock_smtp, sample_articles, categorized_articles, mock_email_config):
        """Test successful email sending"""
        # Mock config
        mock_config.DISTRIBUTION = {
            'email': {
                'enabled': True,
                'sender': 'sender@example.com',
                'recipient': 'recipient@example.com',
                'subject': 'Test Subject',
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 465,
                'smtp_user': 'sender@example.com',
                'smtp_password': 'password123'
            }
        }
        
        # Mock SMTP
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        distributor = MarkdownDistributor()
        markdown = distributor.format_articles(sample_articles, categorized_articles)
        html = distributor.markdown_to_html(markdown)
        
        result = distributor.send_email_smtp(markdown, html, recipients_override=['test@example.com'])
        
        assert result['success'] == True
        assert result['sent'] == 1
    
    @patch('distribution.distributor.rss_feed_summarizer.config')
    def test_send_email_disabled(self, mock_config, sample_articles, categorized_articles):
        """Test email sending when disabled"""
        mock_config.DISTRIBUTION = {
            'email': {
                'enabled': False
            }
        }
        
        distributor = MarkdownDistributor()
        markdown = distributor.format_articles(sample_articles, categorized_articles)
        html = distributor.markdown_to_html(markdown)
        
        result = distributor.send_email_smtp(markdown, html)
        
        assert result['success'] == False
        assert result['sent'] == 0
    
    @patch('distribution.distributor.smtplib.SMTP_SSL')
    @patch('distribution.distributor.rss_feed_summarizer.config')
    def test_distribute(self, mock_config, mock_smtp, sample_articles, categorized_articles, tmp_path, mock_email_config):
        """Test full distribution workflow"""
        mock_config.DISTRIBUTION = {
            'email': {
                'enabled': False  # Disable email for this test
            }
        }
        
        output_dir = str(tmp_path / "output")
        distributor = MarkdownDistributor(output_dir=output_dir)
        
        result = distributor.distribute(
            sample_articles,
            categorized_articles,
            daily_overview="Test overview"
        )
        
        assert 'filepath' in result
        assert 'markdown' in result
        assert 'email' in result
        assert os.path.exists(result['filepath'])


class TestUseDistributor:
    """Test use_distributor convenience function"""
    
    @patch('distribution.distributor.rss_feed_summarizer.config')
    def test_use_distributor(self, mock_config, sample_articles, categorized_articles, tmp_path):
        """Test use_distributor function"""
        mock_config.DISTRIBUTION = {
            'email': {
                'enabled': False
            }
        }
        
        result = use_distributor(
            sample_articles,
            categorized_articles,
            daily_overview="Test"
        )
        
        assert 'filepath' in result
        assert 'markdown' in result

