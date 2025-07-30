"""
Example: Xero integration - Pull chart of accounts and financial statements.
"""

import json
import sys
import os
from datetime import datetime, date

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from connectors.xero_connector import XeroConnector


def main():
    """Main function to demonstrate Xero integration."""
    
    print("🔗 Xero Integration Example")
    print("=" * 50)
    
    # Load configuration
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ config.json not found. Please create it first.")
        return
    
    xero_config = config.get('xero', {})
    if not xero_config:
        print("❌ Xero configuration not found in config.json")
        print("Please add Xero configuration to your config.json:")
        print("""
        {
            "xero": {
                "client_id": "YOUR_XERO_CLIENT_ID",
                "client_secret": "YOUR_XERO_CLIENT_SECRET",
                "redirect_uri": "http://localhost:8080/callback"
            }
        }
        """)
        return
    
    # Initialize Xero connector
    print("📡 Initializing Xero connector...")
    xero = XeroConnector(xero_config)
    
    # Test connection
    print("🔍 Testing connection...")
    if not xero.test_connection():
        print("❌ Connection test failed. Please run setup_xero_oauth.py first.")
        return
    
    print("✅ Connection successful!")
    
    # Get available tenants
    print("\n🏢 Getting available tenants...")
    try:
        tenants = xero.get_tenants()
        print(f"Found {len(tenants)} tenant(s):")
        for tenant in tenants:
            print(f"  - {tenant.get('Name', 'Unknown')} (ID: {tenant.get('OrganisationID', 'Unknown')})")
        
        # Set the first tenant as active
        if tenants:
            xero.set_tenant(tenants[0]["OrganisationID"])
            print(f"✅ Set active tenant: {tenants[0]['Name']}")
    except Exception as e:
        print(f"❌ Failed to get tenants: {e}")
        return
    
    # Get chart of accounts
    print("\n📊 Getting chart of accounts...")
    try:
        accounts = xero.get_chart_of_accounts()
        print(f"✅ Retrieved {len(accounts)} accounts")
        
        # Display some account details
        print("\nSample accounts:")
        for i, account in enumerate(accounts[:5]):  # Show first 5 accounts
            print(f"  {i+1}. {account.get('Name', 'Unknown')} - {account.get('Type', 'Unknown')} - {account.get('Code', 'No Code')}")
        
        if len(accounts) > 5:
            print(f"  ... and {len(accounts) - 5} more accounts")
            
    except Exception as e:
        print(f"❌ Failed to get chart of accounts: {e}")
    
    # Get financial statements
    print("\n📈 Getting financial statements...")
    try:
        # Get current year statements
        current_year = datetime.now().year
        date_from = f"{current_year}-01-01"
        date_to = datetime.now().strftime("%Y-%m-%d")
        
        statements = xero.get_financial_statements(date_from, date_to)
        
        print(f"✅ Retrieved financial statements for {date_from} to {date_to}")
        
        # Display what was retrieved
        if "profit_and_loss" in statements:
            print("  ✅ Profit & Loss Statement")
        if "balance_sheet" in statements:
            print("  ✅ Balance Sheet")
        if "cash_flow" in statements:
            print("  ✅ Cash Flow Statement")
            
    except Exception as e:
        print(f"❌ Failed to get financial statements: {e}")
    
    # Get specific balance sheet
    print("\n💰 Getting current balance sheet...")
    try:
        balance_sheet = xero.get_balance_sheet()
        print("✅ Retrieved current balance sheet")
        
        # Display some balance sheet info if available
        if balance_sheet and "Reports" in balance_sheet:
            report = balance_sheet["Reports"][0] if balance_sheet["Reports"] else {}
            print(f"  Report Title: {report.get('ReportTitle', 'Unknown')}")
            print(f"  Report Date: {report.get('ReportDate', 'Unknown')}")
            
    except Exception as e:
        print(f"❌ Failed to get balance sheet: {e}")
    
    # Get specific profit and loss
    print("\n📊 Getting current year profit and loss...")
    try:
        profit_loss = xero.get_profit_and_loss()
        print("✅ Retrieved profit and loss statement")
        
        # Display some P&L info if available
        if profit_loss and "Reports" in profit_loss:
            report = profit_loss["Reports"][0] if profit_loss["Reports"] else {}
            print(f"  Report Title: {report.get('ReportTitle', 'Unknown')}")
            print(f"  From Date: {report.get('FromDate', 'Unknown')}")
            print(f"  To Date: {report.get('ToDate', 'Unknown')}")
            
    except Exception as e:
        print(f"❌ Failed to get profit and loss: {e}")
    
    print("\n🎉 Xero integration example completed!")
    print("📁 Check the 'drive/xero/' folder for saved data files.")


if __name__ == "__main__":
    main() 