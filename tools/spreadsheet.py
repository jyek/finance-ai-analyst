"""
Google Sheets Utilities for Financial Data

Provides functions for creating, managing, and analyzing financial data in Google Sheets.
"""

import os
import pandas as pd
from typing import Annotated, Dict, Any, List, Optional, Union
from functools import wraps
import gspread
from google.oauth2.credentials import Credentials as OAuthCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
from datetime import datetime

# OAuth2 scopes
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/presentations'
]

def init_google_sheets(func):
    """Decorator to initialize Google Sheets client"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        global gc
        # Try to get OAuth credentials from config or environment variable
        oauth_credentials_json = None
        
        # First try to get from config
        try:
            from config import get_config
            config = get_config("config.json")  # Explicitly load config file
            oauth_credentials_json = config.google_oauth_credentials_json
        except:
            pass
        
        # Fall back to environment variable
        if not oauth_credentials_json:
            oauth_credentials_json = os.environ.get("GOOGLE_OAUTH_CREDENTIALS_JSON")
        
        if oauth_credentials_json:
            # Use OAuth2 authentication
            print("🔐 Using Google OAuth2 authentication...")
            creds = get_oauth_credentials_from_json(oauth_credentials_json)
        else:
            print("❌ Please add GOOGLE_OAUTH_CREDENTIALS_JSON to your environment variables or config file.")
            return None
        
        if creds:
            # Authorize the client
            gc = gspread.authorize(creds)
            print("✅ Google Sheets client initialized")
            return func(*args, **kwargs)
        else:
            print("❌ Failed to initialize Google Sheets client")
            return None

    return wrapper

def get_oauth_credentials_from_json(credentials_json):
    """Get OAuth2 credentials for user authentication from JSON string"""
    creds = None
    token_path = 'token.pickle'
    
    # Load existing token
    if os.path.exists(token_path):
        try:
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
            print("✅ Loaded existing OAuth token")
        except Exception as e:
            print(f"⚠️ Could not load existing token: {e}")
            creds = None
    
    # If no valid credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired OAuth token...")
            try:
                creds.refresh(Request())
                print("✅ Token refreshed successfully")
            except Exception as e:
                print(f"❌ Failed to refresh token: {e}")
                creds = None
        
        # If still no valid credentials, prompt for new authorization
        if not creds or not creds.valid:
            print("🔐 Starting OAuth2 authentication...")
            try:
                # Handle credentials - could be string or dict
                if isinstance(credentials_json, str):
                    import json
                    creds_dict = json.loads(credentials_json)
                else:
                    creds_dict = credentials_json
                
                # Create flow from credentials dict
                flow = InstalledAppFlow.from_client_config(creds_dict, SCOPES)
                creds = flow.run_local_server(port=0)
                print("✅ OAuth2 authentication completed")
            except Exception as e:
                print(f"❌ OAuth2 authentication failed: {e}")
                print(f"Credentials type: {type(credentials_json)}")
                print(f"Credentials content: {credentials_json}")
                return None
        
        # Save the credentials for the next run
        try:
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
            print("💾 OAuth token saved for future use")
        except Exception as e:
            print(f"⚠️ Could not save token: {e}")
    
    return creds

class SpreadsheetUtils:
    """Utilities for Google Sheets operations"""
    
    @staticmethod
    @init_google_sheets
    def create_empty_sheet(
        sheet_name: Annotated[str, "name of the Google Sheet to create"],
        folder_id: Annotated[Optional[str], "Google Drive folder ID where to create the sheet"] = None,
        make_public: Annotated[bool, "make the sheet publicly accessible"] = False,
        share_with: Annotated[Optional[str], "email address to share the sheet with"] = None
    ) -> str:
        """
        Create a new empty Google Sheet.
        
        Args:
            sheet_name: Name for the Google Sheet
            folder_id: Optional Google Drive folder ID
            make_public: Whether to make the sheet publicly accessible
            share_with: Optional email address to share with
            
        Returns:
            URL of the created Google Sheet
        """
        
        try:
            # Check if sheet already exists
            try:
                sheet = gc.open(sheet_name)
                print(f"Opening existing sheet: {sheet_name}")
            except gspread.SpreadsheetNotFound:
                # Create new sheet
                if folder_id:
                    sheet = gc.create(sheet_name, folder_id=folder_id)
                else:
                    sheet = gc.create(sheet_name)
                print(f"Created new empty sheet: {sheet_name}")
            
            # Get the first worksheet
            worksheet = sheet.get_worksheet(0)
            if worksheet is None:
                worksheet = sheet.add_worksheet(title="Sheet1", rows=100, cols=20)
            
            # Clear any existing content
            worksheet.clear()
            
            # Add a simple header
            header_data = [
                [f"Empty Sheet: {sheet_name}"],
                [f"Created on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]
            ]
            
            # Update the worksheet with properly formatted data
            worksheet.update('A1', header_data)
            
            # Format header
            worksheet.format('A1:A2', {
                'textFormat': {'bold': True, 'fontSize': 12}
            })
            
            # Configure access rights
            if make_public:
                # Make the sheet publicly accessible with edit permissions
                sheet.share('', perm_type='anyone', role='writer')
                print("Sheet made publicly accessible with edit permissions")
            
            if share_with:
                # Share with specific email with edit permissions
                sheet.share(share_with, perm_type='user', role='writer')
                print(f"Sheet shared with edit access: {share_with}")
            
            sheet_url = sheet.url
            return f"Google Sheet created: {sheet_url}"
            
        except Exception as e:
            return f"Error creating Google Sheet: {e}"
    
    @staticmethod
    @init_google_sheets
    def get_income_stmt_to_sheet(
        tickers: Annotated[List[str], "list of ticker symbols"],
        fyear: Annotated[str, "fiscal year for the data"] = "2024",
        folder_id: Annotated[Optional[str], "Google Drive folder ID where to create the sheet"] = None
    ) -> str:
        """
        Get income statement data for multiple tickers and save to Google Sheets.
        
        Args:
            tickers: List of ticker symbols
            fyear: Fiscal year for the data
            folder_id: Optional Google Drive folder ID
            
        Returns:
            URL of the created Google Sheet
        """
        
        try:
            # Create sheet name
            sheet_name = f"{'_'.join(tickers)}_{fyear}_Income_Statements"
            
            # Check if sheet already exists
            try:
                sheet = gc.open(sheet_name)
                print(f"Opening existing sheet: {sheet_name}")
            except gspread.SpreadsheetNotFound:
                # Create new sheet
                if folder_id:
                    sheet = gc.create(sheet_name, folder_id=folder_id)
                else:
                    sheet = gc.create(sheet_name)
                print(f"Created new sheet: {sheet_name}")
            
            # Create summary worksheet
            summary_worksheet = sheet.get_worksheet(0)
            if summary_worksheet is None:
                summary_worksheet = sheet.add_worksheet(title="Summary", rows=50, cols=10)
            else:
                summary_worksheet.clear()
                summary_worksheet.update_title("Summary")
            
            # Add summary information
            summary_data = [
                [f"Income Statements - {fyear}"],
                [f"Generated on: {datetime.now().strftime('%Y-%m-%d')}"],
                [],
                ["Available Ticker Worksheets:"]
            ]
            
            for ticker in tickers:
                summary_data.append([f"• {ticker.upper()}"])
            
            summary_worksheet.update('A1', summary_data)
            summary_worksheet.format('A1:A2', {
                'textFormat': {'bold': True, 'fontSize': 14}
            })
            
            # Process each ticker
            for ticker in tickers:
                print(f"Processing {ticker.upper()}...")
                
                try:
                    # Get income statement data using yfinance
                    import yfinance as yf
                    
                    # Get the stock info
                    stock = yf.Ticker(ticker)
                    income_stmt = stock.financials
                    
                    if income_stmt is None or income_stmt.empty:
                        print(f"⚠️ No income statement data available for {ticker.upper()}")
                        continue
                    
                    # Flip the order of rows and columns
                    income_stmt = income_stmt.iloc[::-1]  # Reverse rows
                    income_stmt = income_stmt.iloc[:, ::-1]  # Reverse columns
                    
                    # Create worksheet for this ticker
                    worksheet_name = ticker.upper()
                    
                    # Check if worksheet exists, if not create it
                    try:
                        worksheet = sheet.worksheet(worksheet_name)
                        worksheet.clear()
                    except gspread.WorksheetNotFound:
                        worksheet = sheet.add_worksheet(title=worksheet_name, rows=100, cols=20)
                    
                    # Prepare data for this worksheet
                    sheet_data = []
                    
                    # Add header
                    sheet_data.append([f"{ticker.upper()} {fyear} Income Statement"])
                    sheet_data.append([f"Generated on: {datetime.now().strftime('%Y-%m-%d')}"])
                    sheet_data.append([])  # Empty row
                    
                    # Add income statement data
                    sheet_data.append(["Income Statement Data"])
                    
                    # Add column headers
                    column_headers = []
                    for col in income_stmt.columns:
                        if hasattr(col, 'strftime'):  # Timestamp or datetime
                            column_headers.append(col.strftime('%Y-%m-%d'))
                        else:
                            column_headers.append(str(col))
                    sheet_data.append([''] + column_headers)
                    
                    # Add data rows
                    for index, row in income_stmt.iterrows():
                        row_values = []
                        for value in row.values:
                            # Format numbers with comma separation and no decimal places
                            if pd.notna(value) and isinstance(value, (int, float)):
                                formatted_value = f"{int(value):,}"
                            else:
                                formatted_value = str(value)
                            row_values.append(formatted_value)
                        sheet_data.append([str(index)] + row_values)
                    
                    # Update the worksheet
                    worksheet.update('A1', sheet_data)
                    
                    # Auto-resize columns
                    worksheet.columns_auto_resize(0, len(sheet_data[0]) if sheet_data else 1)
                    
                    # Apply formatting
                    worksheet.format('A1:A3', {
                        'textFormat': {'bold': True, 'fontSize': 14}
                    })
                    
                    print(f"✅ {ticker.upper()} worksheet created successfully")
                    
                except Exception as e:
                    print(f"❌ Error processing {ticker.upper()}: {e}")
                    continue
            
            sheet_url = sheet.url
            return f"Google Sheet created: {sheet_url}"
            
        except Exception as e:
            return f"Error creating income statement sheet: {e}"
    
    @staticmethod
    @init_google_sheets
    def run_benchmarking(
        sheet_name: Annotated[str, "name of the existing Google Sheet"],
        years: Annotated[list, "list of years to benchmark"] = ['2022', '2023', '2024']
    ) -> str:
        """
        Add a benchmarking worksheet to an existing Google Sheet.
        Computes gross profit margins for all companies in the sheet.
        
        Args:
            sheet_name: Name of the existing Google Sheet
            
        Returns:
            URL of the updated Google Sheet
        """
        
        try:
            # Open the existing sheet
            try:
                sheet = gc.open(sheet_name)
                print(f"Opening existing sheet: {sheet_name}")
            except gspread.SpreadsheetNotFound:
                return f"Error: Sheet '{sheet_name}' not found"
            
            # Get all worksheets to find ticker worksheets
            worksheets = sheet.worksheets()
            ticker_worksheets = []
            
            # Find all ticker worksheets (exclude Summary and Benchmarking)
            for worksheet in worksheets:
                title = worksheet.title
                if title not in ['Summary', 'Benchmarking'] and len(title) <= 5:  # Likely ticker symbols
                    ticker_worksheets.append(title)
            
            if not ticker_worksheets:
                return f"Error: No ticker worksheets found in sheet '{sheet_name}'"
            
            print(f"Found {len(ticker_worksheets)} ticker worksheets: {', '.join(ticker_worksheets)}")
            
            # Create or update benchmarking worksheet
            try:
                benchmarking_worksheet = sheet.worksheet("Benchmarking")
                benchmarking_worksheet.clear()
            except gspread.WorksheetNotFound:
                benchmarking_worksheet = sheet.add_worksheet(title="Benchmarking", rows=50, cols=10)
            
            # Create benchmarking worksheet content
            benchmarking_data = [
                [f"Gross Profit Margin Benchmarking"],
                [f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"],
                [],
                ["Company"] + years,  # Header row with years
            ]
            
            # Collect data for each ticker
            all_data = []
            for ticker in ticker_worksheets:
                print(f"Processing {ticker} for benchmarking...")
                
                try:
                    # Get the ticker worksheet data
                    ticker_worksheet = sheet.worksheet(ticker)
                    ticker_data = ticker_worksheet.get_all_values()
                    
                    # Find the data section (skip headers)
                    data_start_row = None
                    for i, row in enumerate(ticker_data):
                        if row and 'Income Statement Data' in row[0]:
                            data_start_row = i + 2  # Skip "Income Statement Data" and empty row
                            break
                    
                    if data_start_row is None or data_start_row >= len(ticker_data):
                        print(f"⚠️ Could not find data section for {ticker}")
                        continue
                    
                    # Extract column headers (dates) and data
                    header_row = ticker_data[data_start_row]
                    data_rows = ticker_data[data_start_row + 1:]
                    
                    # Find Gross Profit and Total Revenue rows
                    gross_profit_row = None
                    total_revenue_row = None
                    
                    for row in data_rows:
                        if row and 'Gross Profit' in row[0]:
                            gross_profit_row = row
                        elif row and 'Total Revenue' in row[0]:
                            total_revenue_row = row
                    
                    if gross_profit_row and total_revenue_row:
                        company_data = {
                            'ticker': ticker,
                            'gross_profit_row': gross_profit_row,
                            'total_revenue_row': total_revenue_row,
                            'header_row': header_row
                        }
                        all_data.append(company_data)
                        print(f"✅ {ticker} data prepared for benchmarking")
                    else:
                        print(f"⚠️ Could not find Gross Profit or Total Revenue for {ticker}")
                        
                except Exception as e:
                    print(f"❌ Error processing {ticker}: {e}")
                    continue
            
            # Add data rows with formulas
            for i, company_data in enumerate(all_data):
                ticker = company_data['ticker']
                row = [ticker]
                
                # Create formulas for each year
                for j, year in enumerate(years):
                    # Find the row numbers for Gross Profit and Total Revenue in the ticker worksheet
                    ticker_worksheet = sheet.worksheet(ticker)
                    ticker_data = ticker_worksheet.get_all_values()
                    
                    # Find data section
                    data_start_row = None
                    for k, row_data in enumerate(ticker_data):
                        if row_data and 'Income Statement Data' in row_data[0]:
                            data_start_row = k + 2
                            break
                    
                    if data_start_row is not None:
                        # Find Gross Profit and Total Revenue rows
                        gross_profit_row_num = None
                        total_revenue_row_num = None
                        
                        for k, row_data in enumerate(ticker_data[data_start_row + 1:], data_start_row + 1):
                            if row_data and 'Gross Profit' in row_data[0]:
                                gross_profit_row_num = k + 1  # +1 because Google Sheets is 1-indexed
                            elif row_data and 'Total Revenue' in row_data[0]:
                                total_revenue_row_num = k + 1
                        
                        if gross_profit_row_num and total_revenue_row_num:
                            # Create formula: =(Gross Profit / Total Revenue) (removed *100 for percentage formatting)
                            year_col = chr(66 + j)  # B, C, D, etc.
                            formula = f'=IF({ticker}!{year_col}{total_revenue_row_num}<>0,({ticker}!{year_col}{gross_profit_row_num}/{ticker}!{year_col}{total_revenue_row_num}),"N/A")'
                            row.append(formula)
                        else:
                            row.append("N/A")
                    else:
                        row.append("N/A")
                
                benchmarking_data.append(row)
            
            # Update the entire benchmarking worksheet at once
            benchmarking_worksheet.update('A1', benchmarking_data, value_input_option='USER_ENTERED')
            
            # Format the worksheet
            benchmarking_worksheet.format('A1:A2', {
                'textFormat': {'bold': True, 'fontSize': 14}
            })
            
            # Auto-resize columns
            benchmarking_worksheet.columns_auto_resize(0, len(benchmarking_data[0]) if benchmarking_data else 1)
            
            sheet_url = sheet.url
            return f"Benchmarking added to Google Sheet: {sheet_url}"
            
        except Exception as e:
            return f"Error running benchmarking: {e}"
    
    @staticmethod
    @init_google_sheets
    def compute_financial_ratios(
        sheet_name: Annotated[str, "name of the existing Google Sheet"],
        ratio_name: Annotated[str, "name of the ratio to compute (e.g., 'Net Profit Margin', 'Revenue Growth')"],
        numerator_metric: Annotated[str, "numerator metric to find in the data (e.g., 'Net Income', 'Total Revenue')"],
        denominator_metric: Annotated[str, "denominator metric to find in the data (e.g., 'Total Revenue', 'Previous Year Revenue')"],
        years: Annotated[list, "list of years to analyze"] = ['2022', '2023', '2024'],
        output_format: Annotated[str, "output format: 'percentage', 'decimal', or 'ratio'"] = 'percentage'
    ) -> str:
        """
        Compute financial ratios for all companies in a Google Sheet.
        
        Args:
            sheet_name: Name of the existing Google Sheet
            ratio_name: Name of the ratio to compute
            numerator_metric: Numerator metric to find in the data
            denominator_metric: Denominator metric to find in the data
            years: List of years to analyze
            output_format: Output format for the ratio
            
        Returns:
            URL of the updated Google Sheet
        """
        
        try:
            # Open the existing sheet
            try:
                sheet = gc.open(sheet_name)
                print(f"Opening existing sheet: {sheet_name}")
            except gspread.SpreadsheetNotFound:
                return f"Error: Sheet '{sheet_name}' not found"
            
            # Get all worksheets to find ticker worksheets
            worksheets = sheet.worksheets()
            ticker_worksheets = []
            
            # Find all ticker worksheets (exclude Summary and analysis worksheets)
            for worksheet in worksheets:
                title = worksheet.title
                if title not in ['Summary', 'Benchmarking'] and len(title) <= 5:  # Likely ticker symbols
                    ticker_worksheets.append(title)
            
            if not ticker_worksheets:
                return f"Error: No ticker worksheets found in sheet '{sheet_name}'"
            
            print(f"Found {len(ticker_worksheets)} ticker worksheets: {', '.join(ticker_worksheets)}")
            
            # Create analysis worksheet name
            analysis_name = ratio_name.replace(' ', '_').replace('/', '_')
            
            # Create or update analysis worksheet
            try:
                analysis_worksheet = sheet.worksheet(analysis_name)
                analysis_worksheet.clear()
            except gspread.WorksheetNotFound:
                analysis_worksheet = sheet.add_worksheet(title=analysis_name, rows=50, cols=10)
            
            # Create analysis worksheet content
            analysis_data = [
                [f"{ratio_name} Analysis"],
                [f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"],
                [],
                ["Company"] + years,  # Header row with years
            ]
            
            # Collect data and create formulas for each ticker
            for ticker in ticker_worksheets:
                print(f"Processing {ticker} for {ratio_name}...")
                
                try:
                    # Get the ticker worksheet data
                    ticker_worksheet = sheet.worksheet(ticker)
                    ticker_data = ticker_worksheet.get_all_values()
                    
                    # Find the data section
                    data_start_row = None
                    for i, row in enumerate(ticker_data):
                        if row and 'Income Statement Data' in row[0]:
                            data_start_row = i + 2
                            break
                    
                    if data_start_row is None or data_start_row >= len(ticker_data):
                        print(f"⚠️ Could not find data section for {ticker}")
                        continue
                    
                    # Extract column headers and data
                    header_row = ticker_data[data_start_row]
                    data_rows = ticker_data[data_start_row + 1:]
                    
                    # Find numerator and denominator rows
                    numerator_row_num = None
                    denominator_row_num = None
                    
                    for k, row_data in enumerate(data_rows, data_start_row + 1):
                        if row_data and numerator_metric in row_data[0]:
                            numerator_row_num = k + 1  # +1 because Google Sheets is 1-indexed
                        elif row_data and denominator_metric in row_data[0]:
                            denominator_row_num = k + 1
                    
                    if numerator_row_num and denominator_row_num:
                        row = [ticker]
                        
                        # Create formulas for each year
                        for j, year in enumerate(years):
                            year_col = chr(66 + j)  # B, C, D, etc.
                            
                            if output_format == 'percentage':
                                formula = f'=IF({ticker}!{year_col}{denominator_row_num}<>0,({ticker}!{year_col}{numerator_row_num}/{ticker}!{year_col}{denominator_row_num}),"N/A")'
                            elif output_format == 'decimal':
                                formula = f'=IF({ticker}!{year_col}{denominator_row_num}<>0,({ticker}!{year_col}{numerator_row_num}/{ticker}!{year_col}{denominator_row_num}),"N/A")'
                            else:  # ratio
                                formula = f'=IF({ticker}!{year_col}{denominator_row_num}<>0,{ticker}!{year_col}{numerator_row_num}&"/"&{ticker}!{year_col}{denominator_row_num},"N/A")'
                            
                            row.append(formula)
                        
                        analysis_data.append(row)
                        print(f"✅ {ticker} {ratio_name} formulas created")
                    else:
                        print(f"⚠️ Could not find {numerator_metric} or {denominator_metric} for {ticker}")
                        
                except Exception as e:
                    print(f"❌ Error processing {ticker}: {e}")
                    continue
            
            if len(analysis_data) <= 4:
                return "Error: No valid data found for analysis"
            
            # Update the entire analysis worksheet at once
            analysis_worksheet.update('A1', analysis_data, value_input_option='USER_ENTERED')
            
            # Format the worksheet
            analysis_worksheet.format('A1:A2', {
                'textFormat': {'bold': True, 'fontSize': 14}
            })
            
            # Auto-resize columns
            analysis_worksheet.columns_auto_resize(0, len(analysis_data[0]) if analysis_data else 1)
            
            sheet_url = sheet.url
            return f"Financial ratio analysis added to Google Sheet: {sheet_url}"
            
        except Exception as e:
            return f"Error computing financial ratios: {e}" 