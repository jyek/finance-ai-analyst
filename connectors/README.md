# Connectors

This package provides integrations with external software systems to pull financial data and save it to the drive folder.

## Available Connectors

### Xero Connector

The Xero connector allows you to pull chart of accounts and financial statements from Xero via their API.

#### Features

- **Chart of Accounts**: Retrieve complete chart of accounts with account codes, names, and types
- **Financial Statements**: Pull profit & loss, balance sheet, and cash flow statements
- **OAuth2 Authentication**: Secure authentication with automatic token refresh
- **Data Persistence**: Automatically saves retrieved data to `drive/xero/` folder with timestamps

#### Setup

1. **Create Xero App**
   - Go to [Xero Developer Portal](https://developer.xero.com/)
   - Create a new app
   - Note down your `client_id` and `client_secret`
   - Set redirect URI to `http://localhost:8080/callback`

2. **Update Configuration**
   Add Xero credentials to your `config.json`:
   ```json
   {
     "xero": {
       "client_id": "your-xero-client-id",
       "client_secret": "your-xero-client-secret",
       "redirect_uri": "http://localhost:8080/callback"
     }
   }
   ```

3. **Run OAuth Setup**
   ```bash
   python setup_xero_oauth.py
   ```
   This will open your browser for authentication and save the access token.

#### Usage

```python
from connectors.xero_connector import XeroConnector
import json

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)

# Initialize connector
xero = XeroConnector(config['xero'])

# Test connection
if xero.test_connection():
    print("Connected to Xero!")
    
    # Get chart of accounts
    accounts = xero.get_chart_of_accounts()
    print(f"Retrieved {len(accounts)} accounts")
    
    # Get financial statements
    statements = xero.get_financial_statements("2024-01-01", "2024-12-31")
    print("Retrieved financial statements")
    
    # Get specific reports
    balance_sheet = xero.get_balance_sheet("2024-12-31")
    profit_loss = xero.get_profit_and_loss("2024-01-01", "2024-12-31")
```

#### Example

Run the example script to see the connector in action:
```bash
python examples/06_xero_integration.py
```

#### Data Storage

All retrieved data is automatically saved to the `drive/xero/` folder with timestamps:
- `xero_chart_of_accounts_[tenant_id]_[timestamp].json`
- `xero_financial_statements_[date_from]_to_[date_to]_[timestamp].json`
- `xero_balance_sheet_[date]_[timestamp].json`
- `xero_profit_and_loss_[date_from]_to_[date_to]_[timestamp].json`

## Adding New Connectors

To add a new connector:

1. Create a new file in the `connectors/` folder (e.g., `quickbooks_connector.py`)
2. Inherit from `BaseConnector` class
3. Implement required methods:
   - `authenticate()`: Handle authentication
   - `test_connection()`: Test API connectivity
4. Add any connector-specific methods for data retrieval
5. Update `connectors/__init__.py` to export the new connector

Example structure:
```python
from .base_connector import BaseConnector

class QuickBooksConnector(BaseConnector):
    def __init__(self, config):
        super().__init__(config)
        # Initialize QuickBooks-specific settings
    
    def authenticate(self) -> bool:
        # Implement QuickBooks authentication
        pass
    
    def test_connection(self) -> bool:
        # Test QuickBooks API connection
        pass
    
    def get_chart_of_accounts(self):
        # Implement QuickBooks chart of accounts retrieval
        pass
```

## Base Connector Features

The `BaseConnector` class provides common functionality:

- **Configuration Management**: Safe access to configuration values
- **Data Persistence**: Automatic saving to drive folder with timestamps
- **Error Handling**: Common error handling patterns
- **Authentication State**: Track authentication status

## Security Notes

- Access tokens are stored locally in JSON files
- Tokens automatically refresh when expired
- Never commit sensitive credentials to version control
- Use environment variables for production deployments 