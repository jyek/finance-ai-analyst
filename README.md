# Finance AI Analyst

An experimental finance AI analyst that works alongside you in Google Workspace to extract and analyze financial data.

## Features

✔️ Connect to your Google Drive, read and create Google Sheets and Google Docs
✔️ Pull public company financial data from Yahoo Finance into Google Sheets
✔️ Analyze a spreadsheet and save commentary to Google Docs
🚧 Run benchmarking analysis across companies with traceable formulas
🚧 Analyse an income statement, create commentary and charts to analyze trends
💡 Pull private financial data from BigQuery or your data warehouse into Google Sheets

## Installation

```bash
pip install finance-ai-analyst
```

## Quick Start

### 1. Set up Configuration

You can set up your API keys and configuration in two ways:

#### Option A: Using the OAuth2 Setup Script (Recommended)

```bash
python setup_oauth.py
```

This will guide you through setting up your OAuth2 credentials interactively.

#### Option B: Manual Configuration

1. Copy the example configuration file:
```bash
cp config.json.example config.json
```

2. Edit `config.json` with your API keys:
```json
{
  "OPENAI_API_KEY": "your-openai-api-key-here",
  "GOOGLE_OAUTH_CREDENTIALS_JSON": {
    "installed": {
      "client_id": "your-client-id.apps.googleusercontent.com",
      "project_id": "your-project-id",
      "auth_uri": "https://accounts.google.com/o/oauth2/auth",
      "token_uri": "https://oauth2.googleapis.com/token",
      "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
      "client_secret": "your-client-secret",
      "redirect_uris": ["http://localhost"]
    }
  }
}
```

3. Set up Google OAuth2 credentials:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Google Sheets API and Google Docs API
   - Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
   - Choose "Desktop application" as the application type
   - Download the JSON file and copy its contents to your `config.json`

#### Option C: Environment Variables

You can also set environment variables directly:

```bash
export OPENAI_API_KEY="your-openai-api-key"
export GOOGLE_OAUTH_CREDENTIALS_JSON='{"installed":{"client_id":"your-client-id","project_id":"your-project-id","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"your-client-secret","redirect_uris":["http://localhost"]}}'
```

### 2. Basic Usage

```python
import autogen
from finance_ai_analyst import FinanceAnalystAgent
from config import get_config

# Load configuration
config = get_config()  # Uses config.json or environment variables

# Get LLM configuration
llm_config = config.llm_config

# Create the Finance Analyst agent
finance_agent = FinanceAnalystAgent.create_agent(
    llm_config=llm_config,
    human_input_mode="NEVER"
)

# Create a user proxy
user_proxy = FinanceAnalystAgent.create_user_proxy()

# Start a conversation
user_proxy.initiate_chat(
    finance_agent,
    message="Create a Google Sheet with income statement data for AAPL, MSFT, and GOOGL for 2024."
)
```

### 3. Advanced Usage with Datasets

```python
# Create a dataset from an existing Google Sheet
result = finance_agent.run(
    "Save a dataset from the Google Sheet 'Financial_Data' worksheet 'AAPL' "
    "with field column 'Metric' and period columns ['2022', '2023', '2024']. "
    "Name the dataset 'apple_financials'."
)

# Create a document with dynamic datapoints
result = finance_agent.run(
    "Create a Google Doc titled 'Apple Financial Report' and insert datapoints "
    "for Total Revenue 2023 and Net Income 2023 from the 'apple_financials' dataset."
)
```

## Examples

### Example 1: Create Income Statement Sheet

```python
# Create a Google Sheet with income statement data for multiple companies
task = """
Create a Google Sheet with income statement data for the following companies:
- Apple (AAPL)
- Microsoft (MSFT) 
- Google (GOOGL)

Use the year 2024 and create separate worksheets for each company.
"""

result = finance_agent.run(task)
```

### Example 2: Run Financial Analysis

```python
# Run benchmarking analysis on an existing sheet
task = """
Analyze the Google Sheet 'Tech_Companies_Income_Statements_2024' and:
1. Run benchmarking analysis for 2022-2024
2. Compute Net Profit Margin ratios for all companies
3. Create a summary document with the results
"""

result = finance_agent.run(task)
```

### Example 3: Dataset Management

```python
# Save and use datasets
task = """
1. Save a dataset from the 'AAPL' worksheet in 'Tech_Companies_Income_Statements_2024'
2. Create a financial report document
3. Insert datapoints for Total Revenue and Net Income for 2023
4. Refresh all datapoints to show actual values
"""

result = finance_agent.run(task)
```

## Package Structure

```
finance_ai_analyst/
├── __init__.py                 # Main package initialization
├── agents/                     # Agent implementations
│   ├── __init__.py
│   └── finance_analyst.py      # Finance Analyst agent
├── tools/                      # Utility tools
│   ├── __init__.py
│   ├── workspace.py           # Google Workspace utilities
│   ├── spreadsheet.py         # Financial data management
│   └── dataset_manager.py     # Dataset and datapoint management
├── setup.py                   # Package setup configuration
├── requirements.txt           # Dependencies
├── README.md                  # Documentation
├── LICENSE                    # MIT License
├── .gitignore                 # Git ignore rules
└── examples/
    └── basic_usage.py         # Usage examples
```

## API Reference

### FinanceAnalystAgent

The main agent class that provides all Google Workspace capabilities.

#### Methods

- `create_agent()` - Create a Finance Analyst agent
- `create_user_proxy()` - Create a user proxy agent

### Tools Package

#### WorkspaceUtils

Utilities for Google Docs and Google Sheets operations.

**Key Methods:**
- `create_google_doc()` - Create a new Google Doc
- `read_google_doc()` - Read content from a Google Doc
- `update_google_doc()` - Update a Google Doc
- `list_my_sheets()` - List accessible Google Sheets
- `read_worksheet()` - Read data from a worksheet
- `create_chart()` - Create charts from sheet data

#### SpreadsheetUtils

Utilities for financial data management in Google Sheets.

**Key Methods:**
- `create_empty_sheet()` - Create a new Google Sheet
- `get_income_stmt_to_sheet()` - Import income statement data
- `run_benchmarking()` - Run benchmarking analysis
- `compute_financial_ratios()` - Compute financial ratios

#### DatasetManager

Utilities for managing datasets and datapoints.

**Key Methods:**
- `save_dataset_from_sheet()` - Save a dataset from a Google Sheet
- `insert_datapoint_into_doc()` - Insert datapoints into Google Docs
- `refresh_datapoints_in_doc()` - Refresh datapoints in documents
- `list_datasets()` - List all available datasets
- `get_datapoint()` - Get a specific datapoint value

## Configuration

The project uses a centralized configuration system that supports multiple ways to set up API keys and settings.

### Configuration Options

1. **Config File** (`config.json`) - Recommended for development
2. **Environment Variables** - Recommended for production
3. **Interactive Setup** - Use `python setup_config.py`

### Configuration Keys

- `OPENAI_API_KEY` - Your OpenAI API key
- `GOOGLE_OAUTH_CREDENTIALS_JSON` - Google OAuth2 client credentials JSON (not service account)
- `LLM_MODEL` - LLM model to use (default: "gpt-4")
- `LLM_TEMPERATURE` - LLM temperature setting (default: 0.1)
- `LLM_TIMEOUT` - LLM timeout in seconds (default: 120)

### Using the Configuration

```python
from config import get_config

# Load configuration
config = get_config()  # Uses config.json or environment variables
# OR
config = get_config("path/to/config.json")  # Use specific config file

# Access configuration values
api_key = config.openai_api_key
llm_config = config.llm_config

# Validate configuration
if config.validate():
    print("Configuration is valid!")
```

### OAuth2 Authentication

The package uses OAuth2 user authentication (not service accounts). When you first run the application, it will:

1. Open a browser window for you to authenticate with your Google account
2. Ask for permission to access your Google Drive, Sheets, and Docs
3. Save the authentication token locally for future use

**Required OAuth Scopes:**
- `https://www.googleapis.com/auth/drive` - Access to Google Drive
- `https://www.googleapis.com/auth/spreadsheets` - Access to Google Sheets
- `https://www.googleapis.com/auth/documents` - Access to Google Docs

**Note:** The authentication token is stored locally in `token.pickle` and will be reused automatically. You only need to authenticate once per device.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License - see the [LICENSE](LICENSE) file for details.

**Key Terms:**
- ✅ **Free for personal, non-commercial use**
- ✅ **Can be shared and adapted with attribution**
- ❌ **Commercial use requires explicit permission**
- ❌ **Must give credit to the original author**

For commercial licensing inquiries, please contact the copyright holder.

## Support

For support and questions:
- Open an issue on GitHub
- Check the documentation
- Review the examples
