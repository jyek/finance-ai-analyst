"""
Xero API connector for pulling chart of accounts and financial statements.
"""

import requests
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, date
from .base_connector import BaseConnector


class XeroConnector(BaseConnector):
    """Connector for Xero API integration."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Xero connector.
        
        Args:
            config: Configuration containing Xero API credentials
        """
        super().__init__(config)
        self.base_url = "https://api.xero.com/api.xro/2.0"
        self.access_token = None
        self.tenant_id = None
        
        # Required config keys
        self.client_id = self.get_config_value("client_id")
        self.client_secret = self.get_config_value("client_secret")
        self.redirect_uri = self.get_config_value("redirect_uri")
        
    def authenticate(self) -> bool:
        """
        Authenticate with Xero using OAuth2.
        
        Returns:
            bool: True if authentication successful
        """
        try:
            # Check if we have a stored access token
            token_file = "xero_token.json"
            if os.path.exists(token_file):
                with open(token_file, 'r') as f:
                    token_data = json.load(f)
                    if self._is_token_valid(token_data):
                        self.access_token = token_data.get("access_token")
                        self.authenticated = True
                        return True
            
            # If no valid token, need to refresh or re-authenticate
            refresh_token = self.get_config_value("refresh_token")
            if refresh_token:
                return self._refresh_token(refresh_token)
            
            # If no refresh token, need to start OAuth flow
            print("No valid Xero token found. Please run the OAuth setup first.")
            return False
            
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False
    
    def _is_token_valid(self, token_data: Dict[str, Any]) -> bool:
        """Check if the stored token is still valid."""
        expires_at = token_data.get("expires_at")
        if not expires_at:
            return False
        
        # Add some buffer time (5 minutes)
        buffer_time = 300
        return datetime.now().timestamp() < (expires_at - buffer_time)
    
    def _refresh_token(self, refresh_token: str) -> bool:
        """Refresh the access token using refresh token."""
        try:
            url = "https://identity.xero.com/connect/token"
            data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
            
            response = requests.post(url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            token_data["expires_at"] = datetime.now().timestamp() + token_data.get("expires_in", 1800)
            
            # Save the new token
            with open("xero_token.json", 'w') as f:
                json.dump(token_data, f, indent=2)
            
            self.access_token = token_data.get("access_token")
            self.authenticated = True
            return True
            
        except Exception as e:
            print(f"Token refresh failed: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test the connection to Xero API.
        
        Returns:
            bool: True if connection successful
        """
        if not self.authenticated:
            if not self.authenticate():
                return False
        
        try:
            # Test with a simple API call
            response = self._make_request("GET", "/Organisations")
            return response.status_code == 200
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    
    def get_tenants(self) -> List[Dict[str, Any]]:
        """
        Get list of Xero tenants (organizations).
        
        Returns:
            List of tenant information
        """
        if not self.authenticated:
            self.authenticate()
        
        response = self._make_request("GET", "/Organisations")
        if response.status_code == 200:
            data = response.json()
            return data.get("Organisations", [])
        else:
            raise Exception(f"Failed to get tenants: {response.text}")
    
    def set_tenant(self, tenant_id: str = None) -> bool:
        """
        Set the active tenant ID.
        
        Args:
            tenant_id: Tenant ID to set. If None, uses first available tenant.
            
        Returns:
            bool: True if tenant set successfully
        """
        if not tenant_id:
            tenants = self.get_tenants()
            if tenants:
                tenant_id = tenants[0]["OrganisationID"]
            else:
                raise Exception("No tenants found")
        
        self.tenant_id = tenant_id
        return True
    
    def get_chart_of_accounts(self) -> List[Dict[str, Any]]:
        """
        Get the chart of accounts from Xero.
        
        Returns:
            List of account information
        """
        if not self.tenant_id:
            self.set_tenant()
        
        response = self._make_request("GET", "/Accounts")
        if response.status_code == 200:
            data = response.json()
            accounts = data.get("Accounts", [])
            
            # Save to drive
            filename = f"xero_chart_of_accounts_{self.tenant_id}.json"
            self.save_to_drive(accounts, filename, "xero")
            
            return accounts
        else:
            raise Exception(f"Failed to get chart of accounts: {response.text}")
    
    def get_financial_statements(self, date_from: str = None, date_to: str = None) -> Dict[str, Any]:
        """
        Get financial statements from Xero.
        
        Args:
            date_from: Start date (YYYY-MM-DD format)
            date_to: End date (YYYY-MM-DD format)
            
        Returns:
            Dictionary containing financial statements
        """
        if not self.tenant_id:
            self.set_tenant()
        
        # Default to current year if no dates provided
        if not date_from:
            date_from = f"{datetime.now().year}-01-01"
        if not date_to:
            date_to = datetime.now().strftime("%Y-%m-%d")
        
        statements = {}
        
        # Get Profit & Loss
        pl_url = f"/Reports/ProfitAndLoss?fromDate={date_from}&toDate={date_to}"
        pl_response = self._make_request("GET", pl_url)
        if pl_response.status_code == 200:
            statements["profit_and_loss"] = pl_response.json()
        
        # Get Balance Sheet
        bs_url = f"/Reports/BalanceSheet?date={date_to}"
        bs_response = self._make_request("GET", bs_url)
        if bs_response.status_code == 200:
            statements["balance_sheet"] = bs_response.json()
        
        # Get Cash Flow
        cf_url = f"/Reports/CashFlow?fromDate={date_from}&toDate={date_to}"
        cf_response = self._make_request("GET", cf_url)
        if cf_response.status_code == 200:
            statements["cash_flow"] = cf_response.json()
        
        # Save to drive
        filename = f"xero_financial_statements_{date_from}_to_{date_to}.json"
        self.save_to_drive(statements, filename, "xero")
        
        return statements
    
    def get_balance_sheet(self, date: str = None) -> Dict[str, Any]:
        """
        Get balance sheet for a specific date.
        
        Args:
            date: Date for balance sheet (YYYY-MM-DD format)
            
        Returns:
            Balance sheet data
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        if not self.tenant_id:
            self.set_tenant()
        
        url = f"/Reports/BalanceSheet?date={date}"
        response = self._make_request("GET", url)
        
        if response.status_code == 200:
            data = response.json()
            
            # Save to drive
            filename = f"xero_balance_sheet_{date}.json"
            self.save_to_drive(data, filename, "xero")
            
            return data
        else:
            raise Exception(f"Failed to get balance sheet: {response.text}")
    
    def get_profit_and_loss(self, date_from: str = None, date_to: str = None) -> Dict[str, Any]:
        """
        Get profit and loss statement for a date range.
        
        Args:
            date_from: Start date (YYYY-MM-DD format)
            date_to: End date (YYYY-MM-DD format)
            
        Returns:
            Profit and loss data
        """
        if not date_from:
            date_from = f"{datetime.now().year}-01-01"
        if not date_to:
            date_to = datetime.now().strftime("%Y-%m-%d")
        
        if not self.tenant_id:
            self.set_tenant()
        
        url = f"/Reports/ProfitAndLoss?fromDate={date_from}&toDate={date_to}"
        response = self._make_request("GET", url)
        
        if response.status_code == 200:
            data = response.json()
            
            # Save to drive
            filename = f"xero_profit_and_loss_{date_from}_to_{date_to}.json"
            self.save_to_drive(data, filename, "xero")
            
            return data
        else:
            raise Exception(f"Failed to get profit and loss: {response.text}")
    
    def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None) -> requests.Response:
        """
        Make an authenticated request to Xero API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request data for POST requests
            
        Returns:
            requests.Response object
        """
        if not self.access_token:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if self.tenant_id:
            headers["Xero-tenant-id"] = self.tenant_id
        
        url = f"{self.base_url}{endpoint}"
        
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        return response 