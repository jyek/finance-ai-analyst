# Finance AI Analyst

An intelligent finance AI analyst that works alongside you in Google Workspace to extract and analyze financial data.

## Features

✔️ **Google Workspace Integration** - Connect to Drive, Sheets, and Docs
✔️ **Financial Data Analysis** - Pull data from Yahoo Finance
✔️ **Automated Reporting** - Generate professional financial reports
✔️ **Benchmarking & Ratios** - Compare companies with traceable formulas
✔️ **Intelligent Agent** - AutoGen-based Finance Analyst with comprehensive tools
✔️ **Programmatic Access** - Easy integration via Python API

## Installation

### Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Google Cloud project with OAuth2 credentials

### Quick Setup

```bash
# Clone the repository
git clone <repository-url>
cd finance-ai-analyst

# Install Python dependencies
pip install -r requirements.txt
```

## Quick Start

### 1. Set up Configuration

#### Step 1: Copy the configuration template

```bash
cp config.json.example config.json
```

#### Step 2: Add your OpenAI API key

Edit `config.json` and replace `"your-openai-api-key-here"` with your actual OpenAI API key:

```json
{
  "OPENAI_API_KEY": "sk-your-actual-openai-api-key-here",
  ...
}
```

#### Step 3: Set up Google OAuth2 credentials

1. **Go to Google Cloud Console:**
   - Visit [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one

2. **Enable required APIs:**
   - Go to "APIs & Services" → "Library"
   - Search for and enable:
     - Google Sheets API
     - Google Docs API
     - Google Drive API

3. **Create OAuth2 credentials:**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth 2.0 Client IDs"
   - Choose "Desktop application" as the application type
   - Download the JSON file

4. **Add credentials to config.json:**
   - Replace the `GOOGLE_OAUTH_CREDENTIALS_JSON` section in your `config.json` with the contents of the downloaded JSON file

### 2. Basic Usage

```python
import autogen
from agents.finance_analyst import FinanceAnalystAgent
from config import get_config

# Load configuration
config = get_config("config.json")

# Create the Finance Analyst agent
finance_agent = FinanceAnalystAgent.create_agent(
    llm_config=config.llm_config,
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

## Examples

### Example 1: Analyze Income Statement

```python
# Analyze income statement in a Google Sheet
task = """
Analyze the income statement data in the Google Sheet named 'Sample Income Statement'.
Please read the worksheet and provide insights about the financial performance.
"""

result = user_proxy.initiate_chat(
    finance_agent,
    message=task
)
```

### Example 2: Get Income Statements

```python
# Get income statements for specific companies
task = """
Get income statement data for AAPL and GOOGL and save it to a new Google Sheet.
Create separate worksheets for each company.
"""

result = user_proxy.initiate_chat(
    finance_agent,
    message=task
)
```

### Example 3: Run Benchmarking

```python
# Run benchmarking analysis
task = """
Run a benchmarking analysis on the companies in my Google Sheet.
Compare key financial metrics across all companies.
"""

result = user_proxy.initiate_chat(
    finance_agent,
    message=task
)
```

### Agent Capabilities

The Finance AI Analyst can:

- 📊 **Analyze Google Sheets** - Read worksheets, identify important metrics, generate insights
- 📈 **Fetch Financial Data** - Get income statements, balance sheets, cash flow data
- 📝 **Create Reports** - Generate professional Google Docs with analysis
- 🧮 **Calculate Ratios** - Compute profit margins, growth rates, efficiency metrics
- 📊 **Run Benchmarking** - Compare companies across multiple financial metrics
- 💾 **Manage Files** - Save analysis results, charts, and data to Google Drive
- 📋 **Track Analysis** - Maintain notes and previous analysis results

## Troubleshooting

### Common Issues

#### **Configuration Issues**
- **Configuration errors**: Check that `config.json` exists and has valid credentials
- **Agent initialization failed**: Verify OpenAI API key and Google OAuth credentials

#### **Authentication Issues**
- **Google OAuth errors**: Check that required APIs are enabled in Google Cloud Console
- **Token expired**: Delete `token.pickle` and re-authenticate

#### **Dependency Issues**
- **Missing dependencies**: Run `pip install -r requirements.txt`
- **Import errors**: Ensure all required packages are installed

### Development

#### **Extending Agent Capabilities**
Add new tools to `agents/finance_analyst.py` and register them with the agent.

## Advanced Usage

### Programmatic Access

For programmatic access without the web interface:

```python
import autogen
from agents.finance_analyst import FinanceAnalystAgent
from config import get_config

# Load configuration
config = get_config("config.json")

# Create the Finance Analyst agent
finance_agent = FinanceAnalystAgent.create_agent(
    llm_config=config.llm_config,
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

### API Integration

You can also integrate the Finance AI Analyst into your own applications using the REST API:

```python
import requests

# Send a chat message
response = requests.post("http://localhost:8000/chat", json={
    "message": "Analyze my Google Sheets"
})

print(response.json())
```
    message="Create a Google Sheet with income statement data for AAPL, MSFT, and GOOGL for 2024."
)
```

### 3. Web Interface (Gradio)

For a user-friendly web interface, you can use the Gradio app:

```bash
# Run the Gradio web interface
python app.py
```

This will start a web server at `http://localhost:7860` where you can:

- 💬 Chat with the Finance Analyst agent
- 🚀 Use quick action buttons for common tasks
- 📊 Analyze Google Sheets with one click
- 📈 Get income statements for multiple companies
- 📝 Create financial reports automatically
- 🧮 Run benchmarking and ratio analysis

The web interface provides an intuitive way to interact with all the agent's capabilities without writing code.

### 4. Advanced Usage with Datasets

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
finance-ai-analyst/
├── agents/                     # Agent implementations
│   ├── __init__.py
│   └── finance_analyst.py      # Finance Analyst agent
├── tools/                      # Utility tools
│   ├── __init__.py
│   ├── workspace.py           # Google Workspace utilities
│   └── sheet.py               # Financial data management
├── config.py                  # Configuration management
├── config.json.example        # Configuration template
├── requirements.txt           # Python dependencies
├── README.md                  # Main documentation
└── LICENSE                    # MIT License
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

#### SheetUtils

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
