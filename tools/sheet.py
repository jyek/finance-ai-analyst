"""
Google Sheets Utilities for Financial Data

Provides functions for creating, managing, and analyzing financial data in Google Sheets.
Includes structured analysis capabilities for financial statements.
"""

import os
import pandas as pd
import numpy as np
from typing import Annotated, Dict, Any, List, Optional, Union, Tuple
from functools import wraps
import gspread
from google.oauth2.credentials import Credentials as OAuthCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
from datetime import datetime
import re

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

class SheetAnalyzer:
    """Structured analyzer for Google Sheets with financial data"""
    
    def __init__(self, credentials: OAuthCredentials):
        """Initialize with Google credentials"""
        self.gc = gspread.authorize(credentials)
        self.sheets_service = build('sheets', 'v4', credentials=credentials)
    
    @staticmethod
    @init_google_sheets
    def identify_sheet_header(
        sheet_name: Annotated[str, "name of the Google Sheet"],
        worksheet_name: Annotated[str, "name of the worksheet"]
    ) -> str:
        """
        Step 1: Identify the header row containing periods (monthly, quarterly, yearly)
        
        Args:
            sheet_name: Name of the Google Sheet
            worksheet_name: Name of the worksheet
            
        Returns:
            Header information and period details
        """
        
        try:
            # Get OAuth credentials
            oauth_credentials_json = None
            try:
                from config import get_config
                config = get_config("config.json")
                oauth_credentials_json = config.google_oauth_credentials_json
            except:
                oauth_credentials_json = os.environ.get("GOOGLE_OAUTH_CREDENTIALS_JSON")
            
            if not oauth_credentials_json:
                return "❌ OAuth credentials not found in config or environment variables."
            
            creds = get_oauth_credentials_from_json(oauth_credentials_json)
            sheet_analyzer = SheetAnalyzer(creds)
            
            # Identify header
            header_info = sheet_analyzer.identify_header_row(sheet_name, worksheet_name)
            
            if 'error' in header_info:
                return f"❌ Error: {header_info['error']}"
            
            result = f"✅ Header Analysis Complete!\n\n"
            result += f"📊 Sheet: {sheet_name}\n"
            result += f"📋 Worksheet: {worksheet_name}\n"
            result += f"📍 Header Row Index: {header_info['header_row_index']}\n"
            result += f"📅 Period Type: {header_info['period_type']}\n"
            result += f"📅 Year: {header_info['year']}\n"
            result += f"📅 Periods Found: {len(header_info['periods'])}\n"
            result += f"📊 Total Rows: {header_info['total_rows']}\n"
            result += f"📊 Total Columns: {header_info['total_columns']}\n\n"
            
            if header_info['periods']:
                result += f"📅 Identified Periods:\n"
                for period in header_info['periods']:
                    result += f"   - {period}\n"
            
            return result
            
        except Exception as e:
            return f"❌ Error identifying header: {str(e)}"
    
    @staticmethod
    @init_google_sheets
    def extract_structured_data(
        sheet_name: Annotated[str, "name of the Google Sheet"],
        worksheet_name: Annotated[str, "name of the worksheet"],
        header_row_index: Annotated[int, "index of the header row (from identify_sheet_header)"]
    ) -> str:
        """
        Step 2: Extract clean DataFrame with identified header
        
        Args:
            sheet_name: Name of the Google Sheet
            worksheet_name: Name of the worksheet
            header_row_index: Index of the header row
            
        Returns:
            Cleaned DataFrame information
        """
        
        try:
            # Get OAuth credentials
            oauth_credentials_json = None
            try:
                from config import get_config
                config = get_config("config.json")
                oauth_credentials_json = config.google_oauth_credentials_json
            except:
                oauth_credentials_json = os.environ.get("GOOGLE_OAUTH_CREDENTIALS_JSON")
            
            if not oauth_credentials_json:
                return "❌ OAuth credentials not found in config or environment variables."
            
            creds = get_oauth_credentials_from_json(oauth_credentials_json)
            sheet_analyzer = SheetAnalyzer(creds)
            
            # Create header info structure
            header_info = {
                'header_row_index': header_row_index,
                'header_row': [],
                'periods': [],
                'period_type': 'unknown',
                'year': None
            }
            
            # Extract DataFrame
            df = sheet_analyzer.extract_dataframe(sheet_name, worksheet_name, header_info)
            
            if df.empty:
                return "❌ Error: Could not extract DataFrame"
            
            result = f"✅ DataFrame Extracted Successfully!\n\n"
            result += f"📊 Shape: {df.shape}\n"
            result += f"📋 Columns: {list(df.columns)}\n\n"
            result += f"📋 First 5 Rows:\n"
            result += df.head().to_string()
            
            return result
            
        except Exception as e:
            return f"❌ Error extracting DataFrame: {str(e)}"
    
    @staticmethod
    @init_google_sheets
    def identify_important_metrics(
        sheet_name: Annotated[str, "name of the Google Sheet"],
        worksheet_name: Annotated[str, "name of the worksheet"],
        header_row_index: Annotated[int, "index of the header row"]
    ) -> str:
        """
        Step 3: Identify important financial rows for analysis
        
        Args:
            sheet_name: Name of the Google Sheet
            worksheet_name: Name of the worksheet
            header_row_index: Index of the header row
            
        Returns:
            List of important financial metrics
        """
        
        try:
            # Get OAuth credentials
            oauth_credentials_json = None
            try:
                from config import get_config
                config = get_config("config.json")
                oauth_credentials_json = config.google_oauth_credentials_json
            except:
                oauth_credentials_json = os.environ.get("GOOGLE_OAUTH_CREDENTIALS_JSON")
            
            if not oauth_credentials_json:
                return "❌ OAuth credentials not found in config or environment variables."
            
            creds = get_oauth_credentials_from_json(oauth_credentials_json)
            sheet_analyzer = SheetAnalyzer(creds)
            
            # Create header info structure
            header_info = {
                'header_row_index': header_row_index,
                'header_row': [],
                'periods': [],
                'period_type': 'unknown',
                'year': None
            }
            
            # Extract DataFrame
            df = sheet_analyzer.extract_dataframe(sheet_name, worksheet_name, header_info)
            
            if df.empty:
                return "❌ Error: Could not extract DataFrame"
            
            # Identify important rows
            important_rows = sheet_analyzer.identify_important_rows(df)
            
            result = f"✅ Important Metrics Identified!\n\n"
            result += f"📊 Found {len(important_rows)} important financial metrics:\n\n"
            
            for i, row in enumerate(important_rows):
                result += f"{i+1}. {row['name']}\n"
                result += f"   📊 Type: {row['type']}\n"
                result += f"   📊 Total: {row['total']:.2f}\n"
                result += f"   📊 Average: {row['avg']:.2f}\n"
                result += f"   📊 Row Index: {row['index']}\n\n"
            
            return result
            
        except Exception as e:
            return f"❌ Error identifying important metrics: {str(e)}"
    
    @staticmethod
    @init_google_sheets
    def analyze_dataframe(
        sheet_name: Annotated[str, "name of the Google Sheet"],
        worksheet_name: Annotated[str, "name of the worksheet"],
        header_row_index: Annotated[int, "index of the header row"]
    ) -> str:
        """
        Step 4: Analyze DataFrame by identifying important metrics, generating commentary, and creating charts
        
        Args:
            sheet_name: Name of the Google Sheet
            worksheet_name: Name of the worksheet
            header_row_index: Index of the header row
            
        Returns:
            Complete analysis with commentary and charts
        """
        
        try:
            # Get OAuth credentials
            oauth_credentials_json = None
            try:
                from config import get_config
                config = get_config("config.json")
                oauth_credentials_json = config.google_oauth_credentials_json
            except:
                oauth_credentials_json = os.environ.get("GOOGLE_OAUTH_CREDENTIALS_JSON")
            
            if not oauth_credentials_json:
                return "❌ OAuth credentials not found in config or environment variables."
            
            creds = get_oauth_credentials_from_json(oauth_credentials_json)
            sheet_analyzer = SheetAnalyzer(creds)
            
            # Create header info structure
            header_info = {
                'header_row_index': header_row_index,
                'header_row': [],
                'periods': [],
                'period_type': 'unknown',
                'year': None
            }
            
            # Extract DataFrame
            df = sheet_analyzer.extract_dataframe(sheet_name, worksheet_name, header_info)
            
            if df.empty:
                return "❌ Error: Could not extract DataFrame"
            
            # Step 1: Identify important metrics
            important_metrics_result = SheetAnalyzer.identify_important_metrics(sheet_name, worksheet_name, header_row_index)
            
            if "❌ Error" in important_metrics_result:
                return f"❌ Failed to identify important metrics: {important_metrics_result}"
            
            # Extract important row indices from the result
            import re
            row_indices = []
            for line in important_metrics_result.split('\n'):
                match = re.search(r'Row Index: (\d+)', line)
                if match:
                    row_indices.append(int(match.group(1)))
            
            if not row_indices:
                return "❌ No important metrics found to analyze"
            
            # Step 2: Generate commentary for each important metric
            commentaries = []
            for row_idx in row_indices:
                commentary = sheet_analyzer._generate_commentary_for_row(df, row_idx)
                commentaries.append(commentary)
            
            # Step 3: Create charts for each important metric
            charts = []
            chart_paths = []
            for row_idx in row_indices:
                chart_data = sheet_analyzer._create_chart_for_row(df, row_idx)
                charts.append(chart_data)
                
                # Extract chart paths from the result (now multiple charts per metric)
                import re
                path_matches = re.findall(r'📄 \w+ chart: (.+\.png)', chart_data)
                chart_paths.extend(path_matches)
            
            # Combine results
            result = f"📊 Complete DataFrame Analysis for {sheet_name}"
            if worksheet_name:
                result += f" - {worksheet_name}"
            result += "\n\n"
            result += "=" * 80 + "\n"
            result += "STEP 1: Important Metrics Identification\n"
            result += "=" * 80 + "\n"
            result += important_metrics_result + "\n\n"
            
            result += "=" * 80 + "\n"
            result += "STEP 2: Commentary for Each Metric\n"
            result += "=" * 80 + "\n"
            for i, commentary in enumerate(commentaries):
                result += f"📝 Metric {i+1}:\n{commentary}\n\n"
            
            result += "=" * 80 + "\n"
            result += "STEP 3: Charts Created\n"
            result += "=" * 80 + "\n"
            for i, chart_data in enumerate(charts):
                result += f"📈 Chart {i+1}:\n{chart_data}\n\n"
            
            # Add chart paths to the result for the agent to use
            result += "\n\n" + "=" * 80 + "\n"
            result += "CHART PATHS FOR DOCUMENT INSERTION\n"
            result += "=" * 80 + "\n"
            result += f"📁 Chart files created: {len(chart_paths)}\n"
            for i, path in enumerate(chart_paths, 1):
                result += f"   {i}. {path}\n"
            
            return result
            
        except Exception as e:
            return f"❌ Error analyzing DataFrame: {str(e)}"
    
    def _generate_commentary_for_row(self, df: pd.DataFrame, row_idx: int) -> str:
        """
        Generate commentary for a specific row in the DataFrame
        
        Args:
            df: DataFrame to analyze
            row_idx: Index of the row to analyze
            
        Returns:
            Commentary for the row
        """
        try:
            if row_idx >= len(df):
                return f"❌ Row index {row_idx} is out of bounds (DataFrame has {len(df)} rows)"
            
            row_name = df.iloc[row_idx, 0]  # First column is usually the row name
            row_data = df.iloc[row_idx, 1:]  # Skip the first column (row name)
            
            # Convert to numeric, ignoring errors
            numeric_data = pd.to_numeric(row_data, errors='coerce')
            
            if numeric_data.isna().all():
                return f"📝 {row_name}: No numeric data available for analysis"
            
            # Calculate basic statistics
            total = numeric_data.sum()
            avg = numeric_data.mean()
            min_val = numeric_data.min()
            max_val = numeric_data.max()
            
            # Calculate trends
            movements = self._calculate_movements(numeric_data)
            
            # Generate commentary
            commentary = f"📝 {row_name}:\n"
            commentary += f"   📊 Total: {total:.2f}\n"
            commentary += f"   📊 Average: {avg:.2f}\n"
            commentary += f"   📊 Range: {min_val:.2f} to {max_val:.2f}\n"
            commentary += f"   📈 Trend: {movements['trend']}\n"
            commentary += f"   📈 Average Change: {movements['avg_change']:.2f}\n"
            commentary += f"   📈 Total Change: {movements['total_change']:.2f}\n"
            
            # Add insights based on the data
            if movements['trend'] == 'increasing':
                commentary += f"   💡 This metric shows a positive trend with consistent growth.\n"
            elif movements['trend'] == 'decreasing':
                commentary += f"   💡 This metric shows a declining trend that may need attention.\n"
            else:
                commentary += f"   💡 This metric shows a stable pattern with minimal variation.\n"
            
            return commentary
            
        except Exception as e:
            return f"❌ Error generating commentary for row {row_idx}: {str(e)}"
    
    def _create_chart_for_row(self, df: pd.DataFrame, row_idx: int) -> str:
        """
        Create a chart for a specific row in the DataFrame, separating different period types
        
        Args:
            df: DataFrame to analyze
            row_idx: Index of the row to create chart for
            
        Returns:
            Chart creation result
        """
        try:
            if row_idx >= len(df):
                return f"❌ Row index {row_idx} is out of bounds (DataFrame has {len(df)} rows)"
            
            row_name = df.iloc[row_idx, 0]  # First column is usually the row name
            row_data = df.iloc[row_idx, 1:]  # Skip the first column (row name)
            
            # Convert to numeric, ignoring errors
            numeric_data = pd.to_numeric(row_data, errors='coerce')
            
            if numeric_data.isna().all():
                return f"📈 {row_name}: No numeric data available for charting"
            
            # Get column names (periods)
            periods = df.columns[1:].tolist()
            
            # Separate periods by type
            monthly_periods = []
            quarterly_periods = []
            annual_periods = []
            other_periods = []
            
            monthly_data = []
            quarterly_data = []
            annual_data = []
            other_data = []
            
            for i, period in enumerate(periods):
                period_lower = str(period).lower()
                
                # Check for monthly periods (JAN, FEB, MAR, etc.)
                if any(month in period_lower for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                                                          'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
                    monthly_periods.append(period)
                    monthly_data.append(numeric_data.iloc[i])
                # Check for quarterly periods (Q1, Q2, Q3, Q4)
                elif any(q in period_lower for q in ['q1', 'q2', 'q3', 'q4', 'quarter']):
                    quarterly_periods.append(period)
                    quarterly_data.append(numeric_data.iloc[i])
                # Check for annual periods (Full Year, Annual, Year)
                elif any(annual in period_lower for annual in ['full year', 'annual', 'year']):
                    annual_periods.append(period)
                    annual_data.append(numeric_data.iloc[i])
                else:
                    other_periods.append(period)
                    other_data.append(numeric_data.iloc[i])
            
            # Create drive folder if it doesn't exist
            import os
            drive_folder = "drive"
            os.makedirs(drive_folder, exist_ok=True)
            
            chart_paths = []
            total_charts = 0
            
            # Create separate charts for each period type
            import matplotlib
            matplotlib.use('Agg')  # Use non-interactive backend
            import matplotlib.pyplot as plt
            
            # Monthly chart
            if monthly_periods and len(monthly_periods) >= 2:
                plt.figure(figsize=(12, 6))
                plt.bar(range(len(monthly_periods)), monthly_data, color='skyblue', alpha=0.7)
                plt.title(f'{row_name} - Monthly Analysis', fontsize=14, fontweight='bold')
                plt.xlabel('Months', fontsize=12)
                plt.ylabel('Value', fontsize=12)
                plt.xticks(range(len(monthly_periods)), monthly_periods, rotation=45, ha='right')
                
                # Add value labels on bars
                for i, v in enumerate(monthly_data):
                    if not pd.isna(v):
                        plt.text(i, v, f'{v:.1f}', ha='center', va='bottom', fontsize=10)
                
                plt.grid(axis='y', alpha=0.3)
                plt.tight_layout()
                
                chart_filename = f"{row_name.replace(' ', '_').replace('/', '_')}_monthly_chart.png"
                chart_path = os.path.join(drive_folder, chart_filename)
                plt.savefig(chart_path, dpi=300, bbox_inches='tight')
                plt.close()
                chart_paths.append(chart_path)
                total_charts += 1
            
            # Quarterly chart
            if quarterly_periods and len(quarterly_periods) >= 2:
                plt.figure(figsize=(10, 6))
                plt.bar(range(len(quarterly_periods)), quarterly_data, color='lightgreen', alpha=0.7)
                plt.title(f'{row_name} - Quarterly Analysis', fontsize=14, fontweight='bold')
                plt.xlabel('Quarters', fontsize=12)
                plt.ylabel('Value', fontsize=12)
                plt.xticks(range(len(quarterly_periods)), quarterly_periods, rotation=45, ha='right')
                
                # Add value labels on bars
                for i, v in enumerate(quarterly_data):
                    if not pd.isna(v):
                        plt.text(i, v, f'{v:.1f}', ha='center', va='bottom', fontsize=10)
                
                plt.grid(axis='y', alpha=0.3)
                plt.tight_layout()
                
                chart_filename = f"{row_name.replace(' ', '_').replace('/', '_')}_quarterly_chart.png"
                chart_path = os.path.join(drive_folder, chart_filename)
                plt.savefig(chart_path, dpi=300, bbox_inches='tight')
                plt.close()
                chart_paths.append(chart_path)
                total_charts += 1
            
            # Annual chart
            if annual_periods and len(annual_periods) >= 1:
                plt.figure(figsize=(8, 6))
                plt.bar(range(len(annual_periods)), annual_data, color='orange', alpha=0.7)
                plt.title(f'{row_name} - Annual Analysis', fontsize=14, fontweight='bold')
                plt.xlabel('Years', fontsize=12)
                plt.ylabel('Value', fontsize=12)
                plt.xticks(range(len(annual_periods)), annual_periods, rotation=45, ha='right')
                
                # Add value labels on bars
                for i, v in enumerate(annual_data):
                    if not pd.isna(v):
                        plt.text(i, v, f'{v:.1f}', ha='center', va='bottom', fontsize=10)
                
                plt.grid(axis='y', alpha=0.3)
                plt.tight_layout()
                
                chart_filename = f"{row_name.replace(' ', '_').replace('/', '_')}_annual_chart.png"
                chart_path = os.path.join(drive_folder, chart_filename)
                plt.savefig(chart_path, dpi=300, bbox_inches='tight')
                plt.close()
                chart_paths.append(chart_path)
                total_charts += 1
            
            # Other periods chart (if any)
            if other_periods and len(other_periods) >= 2:
                plt.figure(figsize=(10, 6))
                plt.bar(range(len(other_periods)), other_data, color='lightcoral', alpha=0.7)
                plt.title(f'{row_name} - Other Periods Analysis', fontsize=14, fontweight='bold')
                plt.xlabel('Periods', fontsize=12)
                plt.ylabel('Value', fontsize=12)
                plt.xticks(range(len(other_periods)), other_periods, rotation=45, ha='right')
                
                # Add value labels on bars
                for i, v in enumerate(other_data):
                    if not pd.isna(v):
                        plt.text(i, v, f'{v:.1f}', ha='center', va='bottom', fontsize=10)
                
                plt.grid(axis='y', alpha=0.3)
                plt.tight_layout()
                
                chart_filename = f"{row_name.replace(' ', '_').replace('/', '_')}_other_chart.png"
                chart_path = os.path.join(drive_folder, chart_filename)
                plt.savefig(chart_path, dpi=300, bbox_inches='tight')
                plt.close()
                chart_paths.append(chart_path)
                total_charts += 1
            
            if total_charts == 0:
                return f"📈 {row_name}: No valid period groups found for charting"
            
            # Return results
            result = f"📈 Charts created for {row_name}:\n"
            for i, chart_path in enumerate(chart_paths):
                period_type = ["monthly", "quarterly", "annual", "other"][i] if i < 4 else "mixed"
                result += f"   📄 {period_type.capitalize()} chart: {chart_path}\n"
            result += f"   📊 Total charts: {total_charts}\n"
            result += f"   📈 Chart types: Bar charts"
            
            return result
            
        except Exception as e:
            return f"❌ Error creating chart for row {row_idx}: {str(e)}"
    
    @staticmethod
    @init_google_sheets
    def read_worksheet(
        sheet_name: Annotated[str, "name of the Google Sheet"],
        worksheet_name: Annotated[str, "name of the worksheet (optional)"] = "Sheet1"
    ) -> str:
        """
        Read data from a specific worksheet using structured analysis.
        This method runs identify_sheet_header and extract_structured_data in sequence.
        
        Args:
            sheet_name: Name of the Google Sheet
            worksheet_name: Optional specific worksheet name (defaults to Sheet1)
            
        Returns:
            Structured analysis results from the worksheet
        """
        
        try:
            # Get OAuth credentials
            oauth_credentials_json = None
            try:
                from config import get_config
                config = get_config("config.json")
                oauth_credentials_json = config.google_oauth_credentials_json
            except:
                oauth_credentials_json = os.environ.get("GOOGLE_OAUTH_CREDENTIALS_JSON")
            
            if not oauth_credentials_json:
                return "❌ OAuth credentials not found in config or environment variables."
            
            creds = get_oauth_credentials_from_json(oauth_credentials_json)
            sheet_analyzer = SheetAnalyzer(creds)
            
            # Step 1: Identify header
            header_result = SheetAnalyzer.identify_sheet_header(sheet_name, worksheet_name)
            
            if "❌ Error" in header_result:
                return f"❌ Failed to identify header: {header_result}"
            
            # Extract header row index from the result
            # Look for "Header Row Index: X" in the result
            import re
            header_match = re.search(r"Header Row Index: (\d+)", header_result)
            if not header_match:
                return f"❌ Could not extract header row index from: {header_result}"
            
            header_row_index = int(header_match.group(1))
            
            # Step 2: Extract structured data
            data_result = SheetAnalyzer.extract_structured_data(sheet_name, worksheet_name, header_row_index)
            
            if "❌ Error" in data_result:
                return f"❌ Failed to extract data: {data_result}"
            
            # Combine results
            result = f"📊 Read worksheet {worksheet_name} in sheet {sheet_name}"
            result += "\n\n"
            result += "=" * 60 + "\n"
            result += "STEP 1: Header Identification\n"
            result += "=" * 60 + "\n"
            result += header_result + "\n\n"
            result += "=" * 60 + "\n"
            result += "STEP 2: Data Extraction\n"
            result += "=" * 60 + "\n"
            result += data_result
            
            return result
            
        except Exception as e:
            return f"❌ Error in structured worksheet reading: {str(e)}"
    
    @staticmethod
    @init_google_sheets
    def read_all_worksheets(
        sheet_name: Annotated[str, "name of the Google Sheet"]
    ) -> str:
        """
        Read all worksheets from a Google Sheet using structured analysis.
        This method runs identify_sheet_header and extract_structured_data for each worksheet.
        
        Args:
            sheet_name: Name of the Google Sheet
            
        Returns:
            Structured analysis results from all worksheets
        """
        
        try:
            # Get OAuth credentials
            oauth_credentials_json = None
            try:
                from config import get_config
                config = get_config("config.json")
                oauth_credentials_json = config.google_oauth_credentials_json
            except:
                oauth_credentials_json = os.environ.get("GOOGLE_OAUTH_CREDENTIALS_JSON")
            
            if not oauth_credentials_json:
                return "❌ OAuth credentials not found in config or environment variables."
            
            creds = get_oauth_credentials_from_json(oauth_credentials_json)
            sheet_analyzer = SheetAnalyzer(creds)
            
            # Open the sheet to get all worksheets
            sheet = sheet_analyzer.gc.open(sheet_name)
            worksheets = sheet.worksheets()
            
            if not worksheets:
                return f"❌ No worksheets found in {sheet_name}"
            
            result = f"📊 Read all worksheets in {sheet_name}\n"
            result += "=" * 80 + "\n\n"
            result += f"📋 Found {len(worksheets)} worksheets\n\n"
            
            successful = 0
            errors = 0
            
            for i, worksheet in enumerate(worksheets, 1):
                worksheet_name = worksheet.title
                result += f"📄 Worksheet {i}/{len(worksheets)}: {worksheet_name}\n"
                result += "-" * 50 + "\n"
                
                try:
                    # Run structured analysis for this worksheet
                    worksheet_result = SheetAnalyzer.read_worksheet(sheet_name, worksheet_name)
                    
                    if "❌ Error" in worksheet_result:
                        result += f"❌ Failed to analyze {worksheet_name}: {worksheet_result}\n"
                        errors += 1
                    else:
                        result += f"✅ Successfully analyzed {worksheet_name}\n"
                        successful += 1
                    
                    result += worksheet_result + "\n\n"
                    
                except Exception as e:
                    result += f"❌ Error analyzing {worksheet_name}: {str(e)}\n\n"
                    errors += 1
            
            # Summary
            result += "=" * 80 + "\n"
            result += "📊 SUMMARY\n"
            result += "=" * 80 + "\n"
            result += f"Total worksheets: {len(worksheets)}\n"
            result += f"Successful analyses: {successful}\n"
            result += f"Errors: {errors}\n"
            
            return result
            
        except Exception as e:
            return f"❌ Error in structured all-worksheets reading: {str(e)}"
    
    def identify_header_row(self, sheet_name: str, worksheet_name: str) -> Dict[str, Any]:
        """
        Step 1: Identify the header row containing periods (monthly, quarterly, yearly)
        
        Args:
            sheet_name: Name of the Google Sheet
            worksheet_name: Name of the worksheet
            
        Returns:
            Dict containing header information and period details
        """
        try:
            # Open the sheet and worksheet
            sheet = self.gc.open(sheet_name)
            worksheet = sheet.worksheet(worksheet_name)
            
            # Get all values
            all_values = worksheet.get_all_values()
            
            # Analyze each row to find the header
            header_info = self._analyze_header_candidates(all_values)
            
            return {
                'header_row_index': header_info['row_index'],
                'header_row': header_info['header_row'],
                'periods': header_info['periods'],
                'period_type': header_info['period_type'],
                'year': header_info['year'],
                'total_rows': len(all_values),
                'total_columns': len(all_values[0]) if all_values else 0
            }
            
        except Exception as e:
            return {
                'error': f"Error identifying header: {str(e)}",
                'header_row_index': None,
                'header_row': None,
                'periods': None,
                'period_type': None
            }
    
    def _analyze_header_candidates(self, all_values: List[List[str]]) -> Dict[str, Any]:
        """Analyze potential header rows to find the one with periods, including multi-row headers"""
        
        # First, try to find single-row headers with multiple periods and years
        for row_index, row in enumerate(all_values):
            if not row or all(cell.strip() == '' for cell in row):
                continue
                
            # Check if this row contains period information
            period_info = self._extract_periods_from_row(row)
            
            # Only consider it a valid single-row header if it has multiple periods and a year
            if period_info['is_period_header'] and len(period_info['periods']) >= 3 and period_info['year']:
                return {
                    'row_index': row_index,
                    'header_row': row,
                    'periods': period_info['periods'],
                    'period_type': period_info['period_type'],
                    'year': period_info['year']
                }
        
        # Check for multi-row headers: rows with only months/quarters and adjacent rows with only years
        for row_index in range(len(all_values) - 1):
            current_row = all_values[row_index]
            next_row = all_values[row_index + 1]
            
            if not current_row or not next_row:
                continue
            
            # Check if current row contains only years and next row contains only months/quarters
            current_analysis = self._analyze_row_content(current_row)
            next_analysis = self._analyze_row_content(next_row)
            
            if (current_analysis['has_only_years'] and next_analysis['has_only_periods'] and 
                next_analysis['period_count'] >= 3):
                
                # Combine the headers
                combined_header = self._combine_multi_row_header(current_row, next_row, current_analysis['year'])
                
                return {
                    'row_index': row_index + 1,  # Return the second row index (periods row)
                    'header_row': combined_header,
                    'periods': combined_header[1:],  # Skip the first column (metric names)
                    'period_type': next_analysis['period_type'],
                    'year': current_analysis['year']
                }
            
            # Also check the reverse: current row has periods, next row has years
            if (next_analysis['has_only_years'] and current_analysis['has_only_periods'] and 
                current_analysis['period_count'] >= 3):
                
                # Combine the headers
                combined_header = self._combine_multi_row_header(next_row, current_row, next_analysis['year'])
                
                return {
                    'row_index': row_index,  # Return the first row index (periods row)
                    'header_row': combined_header,
                    'periods': combined_header[1:],  # Skip the first column (metric names)
                    'period_type': current_analysis['period_type'],
                    'year': next_analysis['year']
                }
        
        # If no clear period header found, return the first non-empty row
        for row_index, row in enumerate(all_values):
            if row and any(cell.strip() != '' for cell in row):
                return {
                    'row_index': row_index,
                    'header_row': row,
                    'periods': [],
                    'period_type': 'unknown',
                    'year': None
                }
        
        return {
            'row_index': 0,
            'header_row': [],
            'periods': [],
            'period_type': 'unknown',
            'year': None
        }
    
    def _extract_periods_from_row(self, row: List[str]) -> Dict[str, Any]:
        """Extract period information from a row"""
        
        periods = []
        period_type = 'unknown'
        year = None
        
        # Common period patterns
        month_patterns = [
            r'jan|january', r'feb|february', r'mar|march', r'apr|april',
            r'may', r'jun|june', r'jul|july', r'aug|august',
            r'sep|september', r'oct|october', r'nov|november', r'dec|december'
        ]
        
        quarter_patterns = [r'q[1-4]', r'quarter\s*[1-4]']
        year_patterns = [r'20\d{2}', r'19\d{2}']
        
        for cell in row:
            cell_lower = str(cell).lower().strip()
            
            # Check for months
            for pattern in month_patterns:
                if re.search(pattern, cell_lower):
                    periods.append(cell)
                    period_type = 'monthly'
                    break
            
            # Check for quarters
            for pattern in quarter_patterns:
                if re.search(pattern, cell_lower):
                    periods.append(cell)
                    period_type = 'quarterly'
                    break
            
            # Check for years
            for pattern in year_patterns:
                match = re.search(pattern, cell_lower)
                if match:
                    year = match.group()
                    if cell not in periods:
                        periods.append(cell)
                    break
        
        # Determine if this is a period header
        is_period_header = len(periods) >= 2 or (len(periods) == 1 and year)
        
        return {
            'is_period_header': is_period_header,
            'periods': periods,
            'period_type': period_type,
            'year': year
        }
    
    def _analyze_row_content(self, row: List[str]) -> Dict[str, Any]:
        """Analyze the content of a row to determine if it contains only years, only periods, or mixed content"""
        
        year_count = 0
        period_count = 0
        total_cells = 0
        year = None
        period_type = 'unknown'
        
        # Common period patterns
        month_patterns = [
            r'jan|january', r'feb|february', r'mar|march', r'apr|april',
            r'may', r'jun|june', r'jul|july', r'aug|august',
            r'sep|september', r'oct|october', r'nov|november', r'dec|december'
        ]
        
        quarter_patterns = [r'q[1-4]', r'quarter\s*[1-4]']
        year_patterns = [r'20\d{2}', r'19\d{2}']
        
        for cell in row:
            cell_str = str(cell).strip()
            if cell_str == '':
                continue
                
            total_cells += 1
            
            # Check for years
            for pattern in year_patterns:
                if re.search(pattern, cell_str):
                    year_count += 1
                    if not year:
                        year = re.search(pattern, cell_str).group()
                    break
            
            # Check for months
            for pattern in month_patterns:
                if re.search(pattern, cell_str.lower()):
                    period_count += 1
                    period_type = 'monthly'
                    break
            
            # Check for quarters
            for pattern in quarter_patterns:
                if re.search(pattern, cell_str.lower()):
                    period_count += 1
                    period_type = 'quarterly'
                    break
        
        # Determine if row contains only years or only periods
        has_only_years = year_count > 0 and period_count == 0 and year_count >= total_cells * 0.5
        has_only_periods = period_count > 0 and year_count == 0 and period_count >= total_cells * 0.5
        
        return {
            'has_only_years': has_only_years,
            'has_only_periods': has_only_periods,
            'year_count': year_count,
            'period_count': period_count,
            'total_cells': total_cells,
            'year': year,
            'period_type': period_type
        }
    
    def _combine_multi_row_header(self, year_row: List[str], period_row: List[str], year: str) -> List[str]:
        """Combine year row and period row into a single header row"""
        
        # Ensure both rows have the same length
        max_length = max(len(year_row), len(period_row))
        year_row_padded = year_row + [''] * (max_length - len(year_row))
        period_row_padded = period_row + [''] * (max_length - len(period_row))
        
        combined_header = []
        
        for i, (year_cell, period_cell) in enumerate(zip(year_row_padded, period_row_padded)):
            year_cell = str(year_cell).strip()
            period_cell = str(period_cell).strip()
            
            if i == 0:  # First column (metric names)
                combined_header.append(year_cell if year_cell else period_cell)
            elif period_cell and period_cell.lower() in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                                                       'jul', 'aug', 'sep', 'oct', 'nov', 'dec', 'full year']:
                # Combine period with year
                if period_cell.lower() == 'full year':
                    combined_header.append(f"Full Year {year}")
                else:
                    combined_header.append(f"{period_cell.upper()} {year}")
            else:
                # Keep the year cell if period cell is empty
                combined_header.append(year_cell if year_cell else period_cell)
        
        return combined_header
    
    def extract_dataframe(self, sheet_name: str, worksheet_name: str, header_info: Dict[str, Any]) -> pd.DataFrame:
        """
        Step 2: Extract dataframe with identified header and data rows
        
        Args:
            sheet_name: Name of the Google Sheet
            worksheet_name: Name of the worksheet
            header_info: Header information from step 1
            
        Returns:
            Cleaned pandas DataFrame
        """
        try:
            sheet = self.gc.open(sheet_name)
            worksheet = sheet.worksheet(worksheet_name)
            
            # Get all values
            all_values = worksheet.get_all_values()
            
            if not all_values:
                return pd.DataFrame()
            
            header_row_index = header_info['header_row_index']
            
            # Use the combined header if available, otherwise extract from sheet
            if 'header_row' in header_info and header_info['header_row']:
                header = header_info['header_row']
                data_rows = all_values[header_row_index + 1:]
            else:
                # Extract header and data
                header = all_values[header_row_index]
                data_rows = all_values[header_row_index + 1:]
            
            # Create DataFrame
            df = pd.DataFrame(data_rows, columns=header)
            
            # Clean the DataFrame
            df = self._clean_dataframe(df)
            
            return df
            
        except Exception as e:
            print(f"Error extracting dataframe: {str(e)}")
            return pd.DataFrame()
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean the extracted DataFrame"""
        
        # Remove completely empty rows
        df = df.dropna(how='all')
        
        # Remove completely empty columns
        df = df.dropna(axis=1, how='all')
        
        # Clean column names
        df.columns = [str(col).strip() for col in df.columns]
        
        # Convert numeric columns
        for col in df.columns:
            if col and col.strip():
                try:
                    df[col] = pd.to_numeric(df[col].replace(['', 'nan', 'NaN'], np.nan))
                except (ValueError, TypeError):
                    # Keep as object type if conversion fails
                    pass
        
        return df
    
    def identify_important_rows(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Step 3: Identify important rows for analysis and charting
        
        Args:
            df: The cleaned DataFrame
            
        Returns:
            List of important rows with their details
        """
        important_rows = []
        
        # Common important financial metrics
        important_keywords = [
            'revenue', 'sales', 'income', 'profit', 'margin', 'cost', 'expense',
            'gross', 'operating', 'net', 'ebitda', 'ebit', 'cash', 'flow',
            'assets', 'liabilities', 'equity', 'debt', 'capital'
        ]
        
        for index, row in df.iterrows():
            # Check if the first column contains important keywords
            first_col = str(row.iloc[0]).lower()
            
            is_important = any(keyword in first_col for keyword in important_keywords)
            
            # Check if row has significant numeric values
            numeric_values = pd.to_numeric(row.iloc[1:], errors='coerce').dropna()
            has_significant_values = len(numeric_values) > 0 and numeric_values.abs().sum() > 0
            
            if is_important and has_significant_values:
                important_rows.append({
                    'index': index,
                    'name': row.iloc[0],
                    'values': numeric_values.tolist(),
                    'total': numeric_values.sum(),
                    'avg': numeric_values.mean(),
                    'type': self._categorize_row(row.iloc[0])
                })
        
        return important_rows
    
    def _categorize_row(self, row_name: str) -> str:
        """Categorize a row based on its name"""
        name_lower = str(row_name).lower()
        
        if any(word in name_lower for word in ['revenue', 'sales', 'income']):
            return 'revenue'
        elif any(word in name_lower for word in ['cost', 'expense', 'cogs']):
            return 'expense'
        elif any(word in name_lower for word in ['profit', 'margin', 'ebit']):
            return 'profit'
        elif any(word in name_lower for word in ['asset', 'liability', 'equity']):
            return 'balance_sheet'
        else:
            return 'other'
    
    def analyze_movements(self, df: pd.DataFrame, selected_rows: List[int]) -> Dict[str, Any]:
        """
        Step 4: Analyze year-over-year and period-over-period movements
        
        Args:
            df: The cleaned DataFrame
            selected_rows: List of row indices to analyze
            
        Returns:
            Analysis results with movements and commentary
        """
        analysis_results = {}
        
        for row_index in selected_rows:
            if row_index >= len(df):
                continue
                
            row_name = df.iloc[row_index, 0]
            row_data = pd.to_numeric(df.iloc[row_index, 1:], errors='coerce').dropna()
            
            if len(row_data) < 2:
                continue
            
            # Calculate movements
            movements = self._calculate_movements(row_data)
            
            analysis_results[row_name] = {
                'data': row_data.tolist(),
                'movements': movements,
                'commentary': self._generate_commentary(row_name, movements)
            }
        
        return analysis_results
    
    def _calculate_movements(self, data: pd.Series) -> Dict[str, Any]:
        """Calculate period-over-period movements"""
        
        movements = {
            'absolute_changes': [],
            'percentage_changes': [],
            'total_change': 0,
            'avg_change': 0,
            'trend': 'stable'
        }
        
        for i in range(1, len(data)):
            current = data.iloc[i]
            previous = data.iloc[i-1]
            
            if pd.notna(current) and pd.notna(previous) and previous != 0:
                abs_change = current - previous
                pct_change = (abs_change / previous) * 100
                
                movements['absolute_changes'].append(abs_change)
                movements['percentage_changes'].append(pct_change)
        
        if movements['absolute_changes']:
            movements['total_change'] = sum(movements['absolute_changes'])
            movements['avg_change'] = np.mean(movements['absolute_changes'])
            
            # Determine trend
            if movements['avg_change'] > 0:
                movements['trend'] = 'increasing'
            elif movements['avg_change'] < 0:
                movements['trend'] = 'decreasing'
        
        return movements
    
    def _generate_commentary(self, row_name: str, movements: Dict[str, Any]) -> str:
        """Generate commentary based on movements"""
        
        if not movements['absolute_changes']:
            return f"No significant changes observed for {row_name}."
        
        trend = movements['trend']
        avg_change = movements['avg_change']
        total_change = movements['total_change']
        
        commentary = f"Analysis for {row_name}:\n"
        
        if trend == 'increasing':
            commentary += f"- Shows an {trend} trend with average change of {avg_change:.2f}\n"
        elif trend == 'decreasing':
            commentary += f"- Shows a {trend} trend with average change of {avg_change:.2f}\n"
        else:
            commentary += f"- Shows a {trend} trend with minimal changes\n"
        
        commentary += f"- Total change across all periods: {total_change:.2f}\n"
        
        # Add specific insights
        if abs(avg_change) > 10:
            commentary += "- Significant volatility observed\n"
        elif abs(avg_change) > 5:
            commentary += "- Moderate changes observed\n"
        else:
            commentary += "- Relatively stable performance\n"
        
        return commentary
    
    def create_charts(self, df: pd.DataFrame, selected_rows: List[int], chart_type: str = 'stacked_bar') -> Dict[str, Any]:
        """
        Step 5: Create charts for selected rows
        
        Args:
            df: The cleaned DataFrame
            selected_rows: List of row indices to chart
            chart_type: Type of chart to create
            
        Returns:
            Chart configuration and data
        """
        chart_data = {
            'chart_type': chart_type,
            'series': [],
            'categories': [],
            'title': 'Financial Performance Analysis'
        }
        
        # Get period categories (column headers)
        chart_data['categories'] = df.columns[1:].tolist()
        
        # Add data series for each selected row
        for row_index in selected_rows:
            if row_index >= len(df):
                continue
                
            row_name = df.iloc[row_index, 0]
            row_data = pd.to_numeric(df.iloc[row_index, 1:], errors='coerce').fillna(0)
            
            chart_data['series'].append({
                'name': row_name,
                'data': row_data.tolist(),
                'type': self._categorize_row(row_name)
            })
        
        return chart_data

class SheetUtils:
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