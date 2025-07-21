"""
Dataset Manager for Google Workspace

Provides functions for managing datasets from Google Sheets and datapoints in Google Docs.
"""

import os
import pandas as pd
import json
from typing import Annotated, Dict, Any, List, Optional, Union
from functools import wraps
import gspread
from google.oauth2.credentials import Credentials as OAuthCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle
from datetime import datetime
import re

# OAuth2 scopes for Google Workspace
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/documents'
]

def init_google_workspace(func):
    """Decorator to initialize Google Workspace clients"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        global gc, docs_service, drive_service
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
            # Authorize the clients
            gc = gspread.authorize(creds)
            docs_service = build('docs', 'v1', credentials=creds)
            drive_service = build('drive', 'v3', credentials=creds)
            print("✅ Google Workspace clients initialized")
            return func(*args, **kwargs)
        else:
            print("❌ Failed to initialize Google Workspace clients")
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
            return creds
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
                # Parse JSON credentials
                import json
                if isinstance(credentials_json, str):
                    creds_dict = json.loads(credentials_json)
                else:
                    creds_dict = credentials_json
                
                # Create flow from credentials dict
                flow = InstalledAppFlow.from_client_config(creds_dict, SCOPES)
                creds = flow.run_local_server(port=0)
                print("✅ OAuth2 authentication completed")
            except Exception as e:
                print(f"❌ OAuth2 authentication failed: {e}")
                return None
        
        # Save the credentials for the next run
        try:
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
            print("💾 OAuth token saved for future use")
        except Exception as e:
            print(f"⚠️ Could not save token: {e}")
    
    return creds

class DatasetManager:
    """Manages datasets from Google Sheets and datapoints in Google Docs"""
    
    def __init__(self):
        self.datasets_file = "datasets_registry.json"
        self.datasets = self._load_datasets()
    
    def _load_datasets(self) -> Dict[str, Any]:
        """Load datasets from registry file"""
        try:
            if os.path.exists(self.datasets_file):
                with open(self.datasets_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"⚠️ Error loading datasets: {e}")
            return {}
    
    def _save_datasets(self):
        """Save datasets to registry file"""
        try:
            with open(self.datasets_file, 'w') as f:
                json.dump(self.datasets, f, indent=2)
            print("💾 Datasets registry saved")
        except Exception as e:
            print(f"❌ Error saving datasets: {e}")
    
    @staticmethod
    @init_google_workspace
    def save_dataset_from_sheet(
        dataset_name: Annotated[str, "name for the dataset"],
        sheet_name: Annotated[str, "name of the Google Sheet"],
        worksheet_name: Annotated[str, "name of the worksheet (optional)"] = None,
        field_column: Annotated[str, "column name containing field names (default: first column)"] = None,
        period_columns: Annotated[List[str], "list of column names for periods (default: all except field column)"] = None
    ) -> str:
        """
        Save a dataset from a Google Sheet.
        
        Args:
            dataset_name: Name for the dataset
            sheet_name: Name of the Google Sheet
            worksheet_name: Optional specific worksheet name
            field_column: Column containing field names (defaults to first column)
            period_columns: List of column names for periods (defaults to all except field column)
            
        Returns:
            Success message with dataset details
        """
        
        try:
            # Open the sheet
            sheet = gc.open(sheet_name)
            print(f"✅ Successfully opened sheet: {sheet_name}")
            
            # Get worksheet
            if worksheet_name:
                worksheet = sheet.worksheet(worksheet_name)
                print(f"✅ Successfully opened worksheet: {worksheet_name}")
            else:
                worksheet = sheet.get_worksheet(0)
                print(f"✅ Successfully opened first worksheet: {worksheet.title}")
            
            if not worksheet:
                return f"No worksheet found in {sheet_name}"
            
            # Get all values
            all_values = worksheet.get_all_values()
            if not all_values:
                return f"No data found in {sheet_name}"
            
            # Convert to DataFrame
            headers = all_values[0]
            data_rows = all_values[1:] if len(all_values) > 1 else []
            df = pd.DataFrame(data_rows, columns=headers)
            
            # Determine field column and period columns
            if field_column is None:
                field_column = headers[0]  # Use first column as field column
            
            if period_columns is None:
                period_columns = [col for col in headers if col != field_column]
            
            # Validate columns exist
            if field_column not in headers:
                return f"Error: Field column '{field_column}' not found in sheet. Available columns: {headers}"
            
            missing_periods = [col for col in period_columns if col not in headers]
            if missing_periods:
                return f"Error: Period columns {missing_periods} not found in sheet. Available columns: {headers}"
            
            # Create dataset structure
            dataset = {
                "name": dataset_name,
                "sheet_name": sheet_name,
                "worksheet_name": worksheet.title,
                "field_column": field_column,
                "period_columns": period_columns,
                "fields": df[field_column].tolist(),
                "periods": period_columns,
                "data": {},
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
            
            # Extract data for each field and period
            for _, row in df.iterrows():
                field_name = str(row[field_column])
                for period in period_columns:
                    value = row[period]
                    # Convert to numeric if possible
                    try:
                        if pd.notna(value) and str(value).strip():
                            # Remove commas and convert to float
                            clean_value = str(value).replace(',', '')
                            numeric_value = float(clean_value)
                            dataset["data"][f"{field_name}|{period}"] = numeric_value
                        else:
                            dataset["data"][f"{field_name}|{period}"] = None
                    except (ValueError, TypeError):
                        dataset["data"][f"{field_name}|{period}"] = str(value)
            
            # Save to registry
            manager = DatasetManager()
            manager.datasets[dataset_name] = dataset
            manager._save_datasets()
            
            # Create summary
            total_datapoints = len([v for v in dataset["data"].values() if v is not None])
            summary = f"✅ Dataset '{dataset_name}' saved successfully!\n"
            summary += f"📊 Sheet: {sheet_name}\n"
            summary += f"📋 Worksheet: {worksheet.title}\n"
            summary += f"📝 Fields: {len(dataset['fields'])} (e.g., {', '.join(dataset['fields'][:3])}{'...' if len(dataset['fields']) > 3 else ''})\n"
            summary += f"📅 Periods: {len(dataset['periods'])} (e.g., {', '.join(dataset['periods'][:3])}{'...' if len(dataset['periods']) > 3 else ''})\n"
            summary += f"🔢 Total datapoints: {total_datapoints}\n"
            summary += f"💾 Registry updated: {manager.datasets_file}"
            
            return summary
            
        except Exception as e:
            return f"Error saving dataset: {e}"
    
    @staticmethod
    @init_google_workspace
    def insert_datapoint_into_doc(
        doc_url: Annotated[str, "URL of the Google Doc"],
        dataset_name: Annotated[str, "name of the dataset"],
        field_name: Annotated[str, "name of the field"],
        period: Annotated[str, "period (column name)"],
        placeholder_format: Annotated[str, "format for placeholder (default: {{dataset.field.period}})"] = "{{dataset.field.period}}"
    ) -> str:
        """
        Insert a datapoint into a Google Doc using a placeholder.
        
        Args:
            doc_url: URL of the Google Doc
            dataset_name: Name of the dataset
            field_name: Name of the field
            period: Period (column name)
            placeholder_format: Format for the placeholder
            
        Returns:
            Success message with insertion details
        """
        
        try:
            # Load datasets
            manager = DatasetManager()
            if dataset_name not in manager.datasets:
                return f"Error: Dataset '{dataset_name}' not found. Available datasets: {list(manager.datasets.keys())}"
            
            dataset = manager.datasets[dataset_name]
            
            # Get the datapoint value
            datapoint_key = f"{field_name}|{period}"
            if datapoint_key not in dataset["data"]:
                return f"Error: Datapoint '{field_name}' for period '{period}' not found in dataset '{dataset_name}'"
            
            value = dataset["data"][datapoint_key]
            if value is None:
                return f"Warning: Datapoint '{field_name}' for period '{period}' is empty in dataset '{dataset_name}'"
            
            # Extract document ID from URL
            doc_id_match = re.search(r'/document/d/([a-zA-Z0-9-_]+)', doc_url)
            if not doc_id_match:
                return "Error: Invalid Google Doc URL"
            
            doc_id = doc_id_match.group(1)
            
            # Create placeholder
            placeholder = placeholder_format.replace("{{dataset}}", dataset_name).replace("{{field}}", field_name).replace("{{period}}", period)
            
            # Insert placeholder into document
            requests = [
                {
                    'insertText': {
                        'location': {
                            'index': 1
                        },
                        'text': f"{placeholder}\n"
                    }
                }
            ]
            
            docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': requests}
            ).execute()
            
            result = f"✅ Datapoint placeholder inserted successfully!\n"
            result += f"📄 Document: {doc_url}\n"
            result += f"📊 Dataset: {dataset_name}\n"
            result += f"📝 Field: {field_name}\n"
            result += f"📅 Period: {period}\n"
            result += f"🔢 Value: {value}\n"
            result += f"🏷️ Placeholder: {placeholder}"
            
            return result
            
        except Exception as e:
            return f"Error inserting datapoint: {e}"
    
    @staticmethod
    @init_google_workspace
    def refresh_datapoints_in_doc(
        doc_url: Annotated[str, "URL of the Google Doc"],
        placeholder_format: Annotated[str, "format for placeholder (default: {{dataset.field.period}})"] = "{{dataset.field.period}}"
    ) -> str:
        """
        Refresh all datapoints in a Google Doc by replacing placeholders with current values.
        
        Args:
            doc_url: URL of the Google Doc
            placeholder_format: Format for the placeholder
            
        Returns:
            Success message with refresh details
        """
        
        try:
            # Load datasets
            manager = DatasetManager()
            
            # Extract document ID from URL
            doc_id_match = re.search(r'/document/d/([a-zA-Z0-9-_]+)', doc_url)
            if not doc_id_match:
                return "Error: Invalid Google Doc URL"
            
            doc_id = doc_id_match.group(1)
            
            # Get document content
            document = docs_service.documents().get(documentId=doc_id).execute()
            content = document.get('body', {}).get('content', [])
            
            # Extract text and find placeholders
            text = ""
            for element in content:
                if 'paragraph' in element:
                    for para_element in element['paragraph']['elements']:
                        if 'textRun' in para_element:
                            text += para_element['textRun']['content']
            
            # Find all placeholders
            placeholder_pattern = placeholder_format.replace("{{dataset}}", r"([a-zA-Z0-9_-]+)").replace("{{field}}", r"([a-zA-Z0-9_\s-]+)").replace("{{period}}", r"([a-zA-Z0-9_\s-]+)")
            matches = re.findall(placeholder_pattern, text)
            
            if not matches:
                return f"No datapoint placeholders found in document using format: {placeholder_format}"
            
            # Process each placeholder
            replacements = []
            for match in matches:
                dataset_name, field_name, period = match
                
                if dataset_name not in manager.datasets:
                    print(f"⚠️ Dataset '{dataset_name}' not found, skipping placeholder")
                    continue
                
                dataset = manager.datasets[dataset_name]
                datapoint_key = f"{field_name}|{period}"
                
                if datapoint_key not in dataset["data"]:
                    print(f"⚠️ Datapoint '{field_name}' for period '{period}' not found in dataset '{dataset_name}', skipping")
                    continue
                
                value = dataset["data"][datapoint_key]
                if value is None:
                    print(f"⚠️ Datapoint '{field_name}' for period '{period}' is empty in dataset '{dataset_name}', skipping")
                    continue
                
                placeholder = placeholder_format.replace("{{dataset}}", dataset_name).replace("{{field}}", field_name).replace("{{period}}", period)
                replacements.append({
                    'placeholder': placeholder,
                    'value': str(value)
                })
            
            if not replacements:
                return "No valid datapoints found to refresh"
            
            # Create batch update requests
            requests = []
            for replacement in replacements:
                # Find and replace each placeholder
                requests.append({
                    'replaceAllText': {
                        'containsText': {
                            'text': replacement['placeholder']
                        },
                        'replaceText': replacement['value']
                    }
                })
            
            # Execute batch update
            docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': requests}
            ).execute()
            
            result = f"✅ Refreshed {len(replacements)} datapoints successfully!\n"
            result += f"📄 Document: {doc_url}\n"
            result += f"🔄 Placeholders replaced: {len(replacements)}\n"
            
            for i, replacement in enumerate(replacements[:5]):  # Show first 5
                result += f"  {i+1}. {replacement['placeholder']} → {replacement['value']}\n"
            
            if len(replacements) > 5:
                result += f"  ... and {len(replacements) - 5} more\n"
            
            return result
            
        except Exception as e:
            return f"Error refreshing datapoints: {e}"
    
    @staticmethod
    def list_datasets() -> str:
        """
        List all available datasets.
        
        Returns:
            Formatted list of datasets
        """
        
        try:
            manager = DatasetManager()
            
            if not manager.datasets:
                return "No datasets found. Use save_dataset_from_sheet() to create your first dataset."
            
            result = f"📊 Available Datasets ({len(manager.datasets)}):\n"
            result += "=" * 50 + "\n"
            
            for name, dataset in manager.datasets.items():
                total_datapoints = len([v for v in dataset["data"].values() if v is not None])
                result += f"📋 Dataset: {name}\n"
                result += f"   📄 Sheet: {dataset['sheet_name']}\n"
                result += f"   📝 Fields: {len(dataset['fields'])}\n"
                result += f"   📅 Periods: {len(dataset['periods'])}\n"
                result += f"   🔢 Datapoints: {total_datapoints}\n"
                result += f"   📅 Created: {dataset['created_at'][:10]}\n"
                result += f"   🔄 Updated: {dataset['last_updated'][:10]}\n"
                result += "\n"
            
            return result
            
        except Exception as e:
            return f"Error listing datasets: {e}"
    
    @staticmethod
    def get_datapoint(
        dataset_name: Annotated[str, "name of the dataset"],
        field_name: Annotated[str, "name of the field"],
        period: Annotated[str, "period (column name)"]
    ) -> str:
        """
        Get a specific datapoint value.
        
        Args:
            dataset_name: Name of the dataset
            field_name: Name of the field
            period: Period (column name)
            
        Returns:
            Datapoint value or error message
        """
        
        try:
            manager = DatasetManager()
            
            if dataset_name not in manager.datasets:
                return f"Error: Dataset '{dataset_name}' not found. Available datasets: {list(manager.datasets.keys())}"
            
            dataset = manager.datasets[dataset_name]
            datapoint_key = f"{field_name}|{period}"
            
            if datapoint_key not in dataset["data"]:
                return f"Error: Datapoint '{field_name}' for period '{period}' not found in dataset '{dataset_name}'"
            
            value = dataset["data"][datapoint_key]
            
            if value is None:
                return f"Datapoint '{field_name}' for period '{period}' is empty in dataset '{dataset_name}'"
            
            result = f"📊 Datapoint Retrieved:\n"
            result += f"📋 Dataset: {dataset_name}\n"
            result += f"📝 Field: {field_name}\n"
            result += f"📅 Period: {period}\n"
            result += f"🔢 Value: {value}\n"
            result += f"📄 Source: {dataset['sheet_name']} ({dataset['worksheet_name']})"
            
            return result
            
        except Exception as e:
            return f"Error getting datapoint: {e}" 