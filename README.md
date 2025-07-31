# [WIP] AI FP&A Analyst

An AI native FP&A analyst that runs in your terminal and works with your file system and Google Sheets. It automates financial analysis, builds charts, and writes commentary.

Designed to be lightweight, flexible, and composable, this agent fits into the tools you already use. No clunky FP&A software, no vendor lock-in, just AI that works where finance work happens.

## Features

- ✔️ Find and download annual reports, earnings releases, presentations from a company websites
- ✔️ Pull public company financial data from Yahoo Finance into Google Sheets
- ✔️ Read sheets from your Google Drive
- ✔️ Analyze income statements and provide create commentary and charts in a report
- 🚧 Customised dashboards
- 🚧 Pull financials from your ERP or data warehouse
- 🚧 Conduct benchmarking analysis

## Installation

### Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Google Cloud project with OAuth2 credentials for Google Workspace access

### Setup

```bash
# Clone and install dependencies
git clone <repository-url>
cd finance-ai-analyst
pip install -r requirements.txt

# Set up configuration
cp config.json.example config.json
```

### Configuration Setup

1. **Add OpenAI API Key**
   Edit `config.json` and replace `"your-openai-api-key-here"` with your actual OpenAI API key.

2. **Set up Google OAuth2**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a project and enable: Google Sheets API, Google Docs API, Google Drive API
   - Create OAuth2 credentials (Desktop application)
   - Download the JSON file and replace the `GOOGLE_OAUTH_CREDENTIALS_JSON` section in `config.json`

3. **First Run Authentication**
   - Run `python app.py` - it will open a browser for Google authentication
   - Grant permissions to access your Google Workspace
   - Authentication token is saved locally in `token.pickle` for future use

4. **External Connectors Setup (Optional)**
   - For Xero integration, add credentials to `config.json` and run `python setup_xero_oauth.py`
   - See `connectors/README.md` for detailed setup instructions

## Run in Terminal

```bash
python app.py
```

The agent will start an interactive chat session where you can ask it to analyze your financial data, create reports, or perform any FP&A tasks.
