"""
Tests for main pipeline
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from rss_feed_summarizer.pipeline import run_pipeline


class TestPipeline:
    """Test pipeline execution"""
    
    @patch('rss_feed_summarizer.pipeline.RSSFetcher')
    @patch('rss_feed_summarizer.pipeline.filter_articles')
    @patch('rss_feed_summarizer.pipeline.filter_relevant_articles')
    @patch('rss_feed_summarizer.pipeline.generate_daily_overview')
    @patch('rss_feed_summarizer.pipeline.categorize_by_topic')
    @patch('rss_feed_summarizer.pipeline.rank_articles_by_importance')
    @patch('rss_feed_summarizer.pipeline.generate_article_summaries')
    @patch('rss_feed_summarizer.pipeline.use_distributor')
    def test_pipeline_success(
        self,
        mock_distributor,
        mock_summaries,
        mock_ranking,
        mock_categorize,
        mock_overview,
        mock_relevance,
        mock_keyword_filter,
        mock_fetcher,
        sample_articles
    ):
        """Test successful pipeline execution"""
        # Setup mocks
        mock_fetcher_instance = Mock()
        mock_fetcher_instance.fetch_articles.return_value = sample_articles
        mock_fetcher.return_value = mock_fetcher_instance
        
        mock_keyword_filter.return_value = sample_articles
        mock_relevance.return_value = sample_articles
        mock_overview.return_value = "Test daily overview"
        
        categorized = [
            {**article, 'category': 'TOOLS_AND_FRAMEWORKS'} 
            for article in sample_articles
        ]
        mock_categorize.return_value = categorized
        
        mock_ranking.return_value = sample_articles[:2]
        mock_summaries.return_value = sample_articles
        
        mock_distributor.return_value = {
            'filepath': 'output/test.md',
            'markdown': '# Test',
            'email': {'success': True, 'sent': 1}
        }
        
        # Run pipeline
        result = run_pipeline()
        
        assert result['success'] == True
        assert 'distribution' in result
        assert 'stats' in result
        assert result['stats']['started'] == len(sample_articles)
    
    @patch('rss_feed_summarizer.pipeline.RSSFetcher')
    def test_pipeline_no_articles(self, mock_fetcher):
        """Test pipeline with no articles"""
        mock_fetcher_instance = Mock()
        mock_fetcher_instance.fetch_articles.return_value = []
        mock_fetcher.return_value = mock_fetcher_instance
        
        result = run_pipeline()
        
        assert result['success'] == False
        assert result['reason'] == "No articles fetched"
    
    @patch('rss_feed_summarizer.pipeline.RSSFetcher')
    @patch('rss_feed_summarizer.pipeline.filter_articles')
    def test_pipeline_no_keyword_filtered(self, mock_keyword_filter, mock_fetcher, sample_articles):
        """Test pipeline with no articles passing keyword filter"""
        mock_fetcher_instance = Mock()
        mock_fetcher_instance.fetch_articles.return_value = sample_articles
        mock_fetcher.return_value = mock_fetcher_instance
        
        mock_keyword_filter.return_value = []
        
        result = run_pipeline()
        
        assert result['success'] == False
        assert result['reason'] == "No articles passed keyword filtering"
    
    @patch('rss_feed_summarizer.pipeline.RSSFetcher')
    @patch('rss_feed_summarizer.pipeline.filter_articles')
    @patch('rss_feed_summarizer.pipeline.filter_relevant_articles')
    def test_pipeline_no_relevant_articles(self, mock_relevance, mock_keyword_filter, mock_fetcher, sample_articles):
        """Test pipeline with no relevant articles"""
        mock_fetcher_instance = Mock()
        mock_fetcher_instance.fetch_articles.return_value = sample_articles
        mock_fetcher.return_value = mock_fetcher_instance
        
        mock_keyword_filter.return_value = sample_articles
        mock_relevance.return_value = []
        
        result = run_pipeline()
        
        assert result['success'] == False
        assert result['reason'] == "No relevant articles after filtering"
    
    @patch('rss_feed_summarizer.pipeline.RSSFetcher')
    @patch('rss_feed_summarizer.pipeline.filter_articles')
    @patch('rss_feed_summarizer.pipeline.filter_relevant_articles')
    @patch('rss_feed_summarizer.pipeline.generate_daily_overview')
    @patch('rss_feed_summarizer.pipeline.categorize_by_topic')
    @patch('rss_feed_summarizer.pipeline.rank_articles_by_importance')
    @patch('rss_feed_summarizer.pipeline.generate_article_summaries')
    @patch('rss_feed_summarizer.pipeline.use_distributor')
    def test_pipeline_with_email_recipients(
        self,
        mock_distributor,
        mock_summaries,
        mock_ranking,
        mock_categorize,
        mock_overview,
        mock_relevance,
        mock_keyword_filter,
        mock_fetcher,
        sample_articles
    ):
        """Test pipeline with email recipients"""
        mock_fetcher_instance = Mock()
        mock_fetcher_instance.fetch_articles.return_value = sample_articles
        mock_fetcher.return_value = mock_fetcher_instance
        
        mock_keyword_filter.return_value = sample_articles
        mock_relevance.return_value = sample_articles
        mock_overview.return_value = "Test overview"
        
        categorized = [
            {**article, 'category': 'TOOLS_AND_FRAMEWORKS'} 
            for article in sample_articles
        ]
        mock_categorize.return_value = categorized
        
        mock_ranking.return_value = sample_articles
        mock_summaries.return_value = sample_articles
        mock_distributor.return_value = {'filepath': 'test.md', 'markdown': '# Test', 'email': {}}
        
        result = run_pipeline(email_recipients=['test@example.com'])
        
        assert result['success'] == True
        # Verify distributor was called with email recipients
        mock_distributor.assert_called_once()
        call_args = mock_distributor.call_args
        assert call_args[1]['email_recipients'] == ['test@example.com']

