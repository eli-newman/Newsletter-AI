# RSS Feed Summarizer 🤖📰

An intelligent RSS feed processor that uses AI to fetch, filter, rank, summarize, and distribute AI technology news via email to subscribers managed in Google Sheets.

## ✨ Features

- Fetches articles from 20+ AI/tech RSS feeds
- AI-powered content filtering and ranking
- Categorizes articles (Tools, Models, Enterprise, Market)
- Generates concise summaries
- Automatically sends email digests to subscribers from Google Sheets
- Runs daily via GitHub Actions

## 🚀 Setup

### 1. Install Dependencies

```bash
git clone <https://github.com/eli-newman/Newsletter-AI.git)
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and configure:

**Required:**
```env
OPENAIAPIKEY=your_openai_api_key_here
SMTP_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=your_gmail_app_password
GOOGLE_SHEETS_CREDENTIALS={"type":"service_account",...}
SHEET_ID=your_google_sheet_id
```

See `docs/GOOGLE_SHEETS_SETUP.md` for detailed Google Sheets setup instructions.

### 3. Google Sheets Setup

Create a Google Sheet with columns:
- **Email**: Subscriber email addresses
- **Subscribed Date**: Date they subscribed
- **Active**: TRUE/FALSE to enable/disable subscriptions

The script automatically reads active subscribers (where Active=TRUE) and sends them the daily digest.

### 4. GitHub Actions Setup

The workflow runs daily at 9:00 AM UTC. Configure these secrets in your GitHub repository:

- `OPENAIAPIKEY`: Your OpenAI API key
- `SMTP_USER`: Your Gmail address
- `GMAIL_APP_PASSWORD`: Your Gmail app password
- `GOOGLE_SHEETS_CREDENTIALS`: JSON credentials for Google Sheets API
- `SHEET_ID`: Your Google Sheet ID

### 5. Manual Run

```bash
python scripts/run.py
```

## 📊 How It Works

1. **Fetches** articles from RSS feeds
2. **Filters** for AI-relevant content
3. **Categorizes** articles by topic
4. **Ranks** articles by importance
5. **Summarizes** each article
6. **Reads** active subscribers from Google Sheets
7. **Sends** email digests to all active subscribers

## 📁 Project Structure

```
rss-feed-summarizer/
├── rss_feed_summarizer/     # Summarization package (AI pipeline)
│   ├── pipeline.py          # Main pipeline orchestrator
│   ├── fetcher.py            # RSS feed fetcher
│   ├── relevance.py          # Content relevance filter
│   ├── categorization.py     # Article categorization
│   ├── ranking.py            # Article ranking
│   └── summaries.py          # Article summarization
├── distribution/             # Distribution package (email & subscribers)
│   ├── distributor.py        # Email distribution
│   └── sheets_db.py          # Google Sheets integration
├── scripts/
│   └── run.py                # Main runner script
├── .github/workflows/
│   └── daily-digest.yml      # GitHub Actions workflow
└── output/                   # Generated markdown files
```

## 💰 Cost

- **Daily digest**: ~$0.50-2.00 (depending on article volume)
- **With caching**: 50-80% cost reduction on subsequent runs

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.
