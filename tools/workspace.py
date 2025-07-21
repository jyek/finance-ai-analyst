"""
Google Workspace Utilities

Provides functions for creating, reading, and updating Google Docs and Google Sheets
for financial analysis workflows.
"""

import os
import pandas as pd
from typing import Annotated, Dict, Any, List, Optional
from functools import wraps
import gspread
from google.oauth2.credentials import Credentials as OAuthCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle
from datetime import datetime

# OAuth2 scopes for Google Workspace
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/presentations'
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

class WorkspaceUtils:
    """Utilities for Google Workspace operations"""
    
    @staticmethod
    @init_google_workspace
    def create_google_doc(
        title: Annotated[str, "title of the Google Doc"],
        content: Annotated[str, "content to add to the document"],
        folder_id: Annotated[Optional[str], "Google Drive folder ID where to create the doc"] = None
    ) -> str:
        """
        Create a new Google Doc with the specified title and content.
        
        Args:
            title: Title for the Google Doc
            content: Content to add to the document (plain text or markdown)
            folder_id: Optional Google Drive folder ID
            
        Returns:
            URL of the created Google Doc
        """
        
        try:
            # Create the document
            document = {
                'title': title
            }
            
            doc = docs_service.documents().create(body=document).execute()
            document_id = doc.get('documentId')
            
            # Simple text insertion (no formatting conversion)
            requests = [
                {
                    'insertText': {
                        'location': {
                            'index': 1
                        },
                        'text': content
                    }
                }
            ]
            
            docs_service.documents().batchUpdate(
                documentId=document_id,
                body={'requests': requests}
            ).execute()
            
            # Move to folder if specified
            if folder_id:
                file = drive_service.files().get(fileId=document_id, fields='parents').execute()
                previous_parents = ",".join(file.get('parents', []))
                
                drive_service.files().update(
                    fileId=document_id,
                    addParents=folder_id,
                    removeParents=previous_parents,
                    fields='id, parents'
                ).execute()
            
            doc_url = f"https://docs.google.com/document/d/{document_id}"
            return f"Google Doc created: {doc_url}"
            
        except HttpError as error:
            return f"Error creating Google Doc: {error}"
    
    @staticmethod
    @init_google_workspace
    def read_google_doc(
        doc_url: Annotated[str, "URL of the Google Doc"]
    ) -> str:
        """
        Read content from a Google Doc.
        
        Args:
            doc_url: URL of the Google Doc
            
        Returns:
            Content of the document
        """
        
        try:
            # Extract document ID from URL
            import re
            doc_id_match = re.search(r'/document/d/([a-zA-Z0-9-_]+)', doc_url)
            if not doc_id_match:
                return "Error: Invalid Google Doc URL"
            
            doc_id = doc_id_match.group(1)
            
            # Get document content
            document = docs_service.documents().get(documentId=doc_id).execute()
            content = document.get('body', {}).get('content', [])
            
            # Extract text
            text = ""
            for element in content:
                if 'paragraph' in element:
                    for para_element in element['paragraph']['elements']:
                        if 'textRun' in para_element:
                            text += para_element['textRun']['content']
            
            return text.strip()
            
        except Exception as e:
            return f"Error reading Google Doc: {e}"
    
    @staticmethod
    @init_google_workspace
    def update_google_doc(
        doc_url: Annotated[str, "URL of the Google Doc"],
        content: Annotated[str, "new content to add to the document"]
    ) -> str:
        """
        Update a Google Doc with new content.
        
        Args:
            doc_url: URL of the Google Doc
            content: New content to add
            
        Returns:
            Success message
        """
        
        try:
            # Extract document ID from URL
            import re
            doc_id_match = re.search(r'/document/d/([a-zA-Z0-9-_]+)', doc_url)
            if not doc_id_match:
                return "Error: Invalid Google Doc URL"
            
            doc_id = doc_id_match.group(1)
            
            # Insert new content
            requests = [
                {
                    'insertText': {
                        'location': {
                            'index': 1
                        },
                        'text': content + "\n"
                    }
                }
            ]
            
            docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': requests}
            ).execute()
            
            return f"Successfully updated Google Doc: {doc_url}"
            
        except Exception as e:
            return f"Error updating Google Doc: {e}"
    
    @staticmethod
    @init_google_workspace
    def update_doc_variables(
        doc_url: Annotated[str, "URL of the Google Doc"],
        variables: Annotated[Dict[str, str], "dictionary of variable names and values"]
    ) -> str:
        """
        Update variables in a Google Doc by replacing placeholders like {{variable}}.
        
        Args:
            doc_url: URL of the Google Doc
            variables: Dictionary of variable names and their new values
            
        Returns:
            Success message with number of replacements
        """
        
        try:
            # Extract document ID from URL
            import re
            doc_id_match = re.search(r'/document/d/([a-zA-Z0-9-_]+)', doc_url)
            if not doc_id_match:
                return "Error: Invalid Google Doc URL"
            
            doc_id = doc_id_match.group(1)
            
            # Get document content
            document = docs_service.documents().get(documentId=doc_id).execute()
            content = document.get('body', {}).get('content', [])
            
            # Extract text
            text = ""
            for element in content:
                if 'paragraph' in element:
                    for para_element in element['paragraph']['elements']:
                        if 'textRun' in para_element:
                            text += para_element['textRun']['content']
            
            # Create batch update requests
            requests = []
            replacements = 0
            
            for var_name, var_value in variables.items():
                placeholder = f"{{{{{var_name}}}}}"
                if placeholder in text:
                    requests.append({
                        'replaceAllText': {
                            'containsText': {
                                'text': placeholder
                            },
                            'replaceText': str(var_value)
                        }
                    })
                    replacements += 1
            
            if requests:
                docs_service.documents().batchUpdate(
                    documentId=doc_id,
                    body={'requests': requests}
                ).execute()
                
                return f"Successfully replaced {replacements} variables in Google Doc: {doc_url}"
            else:
                return f"No variables found to replace in Google Doc: {doc_url}"
            
        except Exception as e:
            return f"Error updating variables in Google Doc: {e}"
    
    @staticmethod
    @init_google_workspace
    def list_my_sheets(
        max_results: Annotated[int, "maximum number of sheets to return"] = 10
    ) -> str:
        """
        List Google Sheets accessible to the user.
        
        Args:
            max_results: Maximum number of sheets to return
            
        Returns:
            List of accessible Google Sheets
        """
        
        try:
            # Get list of files from Google Drive
            results = drive_service.files().list(
                q="mimeType='application/vnd.google-apps.spreadsheet'",
                pageSize=max_results,
                fields="files(id, name, webViewLink, createdTime)"
            ).execute()
            
            files = results.get('files', [])
            
            if not files:
                return "No Google Sheets found."
            
            result = f"Found {len(files)} Google Sheets:\n"
            result += "=" * 50 + "\n"
            
            for file in files:
                result += f"📊 {file['name']}\n"
                result += f"   🔗 {file['webViewLink']}\n"
                result += f"   📅 Created: {file['createdTime'][:10]}\n"
                result += f"   🆔 ID: {file['id']}\n\n"
            
            return result
            
        except Exception as e:
            return f"Error listing Google Sheets: {e}"
    
    @staticmethod
    @init_google_workspace
    def read_worksheet(
        sheet_name: Annotated[str, "name of the Google Sheet"],
        worksheet_name: Annotated[str, "name of the worksheet (optional)"] = None
    ) -> str:
        """
        Read data from a specific worksheet in a Google Sheet.
        
        Args:
            sheet_name: Name of the Google Sheet
            worksheet_name: Optional specific worksheet name (defaults to first worksheet)
            
        Returns:
            Formatted data from the worksheet
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
            print(f"✅ Successfully retrieved {len(all_values)} rows of data")
            
            if not all_values:
                return f"No data found in {sheet_name}"
            
            # Convert to pandas DataFrame
            headers = all_values[0]
            data_rows = all_values[1:] if len(all_values) > 1 else []
            
            df = pd.DataFrame(data_rows, columns=headers)
            
            # Convert numeric columns where possible
            for col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col].replace('', pd.NA), errors='ignore')
                except:
                    pass
            
            print(f"✅ Successfully created DataFrame with shape: {df.shape}")
            print(f"✅ DataFrame columns: {list(df.columns)}")
            
            # Return DataFrame info and first few rows as string
            result = f"DataFrame from {sheet_name}:\n"
            result += f"Shape: {df.shape}\n"
            result += f"Columns: {list(df.columns)}\n\n"
            result += "First 10 rows:\n"
            result += df.head(10).to_string(index=False)
            
            if len(df) > 10:
                result += f"\n\n... and {len(df) - 10} more rows"
            
            return result
            
        except Exception as e:
            return f"Error reading sheet data: {e}"
    
    @staticmethod
    @init_google_workspace
    def read_all_worksheets(
        sheet_name: Annotated[str, "name of the Google Sheet"]
    ) -> str:
        """
        Read all worksheets from a Google Sheet and return as DataFrames.
        
        Args:
            sheet_name: Name of the Google Sheet
            
        Returns:
            Analysis of all worksheets
        """
        
        try:
            import pandas as pd
            
            # Open the sheet
            sheet = gc.open(sheet_name)
            print(f"✅ Successfully opened sheet: {sheet_name}")
            
            # Get all worksheets
            worksheets = sheet.worksheets()
            print(f"✅ Found {len(worksheets)} worksheets in the sheet")
            
            if not worksheets:
                return []
            
            # Extract each worksheet as DataFrame
            worksheet_data = []
            
            for worksheet in worksheets:
                try:
                    # Get worksheet data
                    all_values = worksheet.get_all_values()
                    
                    if not all_values:
                        # Empty worksheet
                        worksheet_data.append({
                            "worksheet_name": worksheet.title,
                            "dataframe": pd.DataFrame(),
                            "shape": (0, 0),
                            "columns": [],
                            "status": "empty"
                        })
                        continue
                    
                    # Create DataFrame
                    headers = all_values[0]
                    data_rows = all_values[1:] if len(all_values) > 1 else []
                    
                    df = pd.DataFrame(data_rows, columns=headers)
                    
                    # Convert numeric columns where possible
                    for col in df.columns:
                        try:
                            df[col] = pd.to_numeric(df[col].replace('', pd.NA), errors='ignore')
                        except:
                            pass
                    
                    worksheet_data.append({
                        "worksheet_name": worksheet.title,
                        "dataframe": df,
                        "shape": df.shape,
                        "columns": list(df.columns),
                        "status": "success"
                    })
                    
                except Exception as e:
                    worksheet_data.append({
                        "worksheet_name": worksheet.title,
                        "dataframe": pd.DataFrame(),
                        "shape": (0, 0),
                        "columns": [],
                        "status": f"error: {str(e)}"
                    })
            
            # Create analysis report
            result = f"📊 Analysis of Google Sheet: {sheet_name}\n"
            result += "=" * 60 + "\n\n"
            
            successful = sum(1 for ws in worksheet_data if ws['status'] == 'success')
            empty = sum(1 for ws in worksheet_data if ws['status'] == 'empty')
            errors = sum(1 for ws in worksheet_data if ws['status'].startswith('error'))
            
            result += f"📋 Summary:\n"
            result += f"   Total worksheets: {len(worksheets)}\n"
            result += f"   Successful extractions: {successful}\n"
            result += f"   Empty worksheets: {empty}\n"
            result += f"   Errors: {errors}\n\n"
            
            result += "📄 Worksheet Details:\n"
            for ws_data in worksheet_data:
                result += f"   📊 {ws_data['worksheet_name']}:\n"
                result += f"      Status: {ws_data['status']}\n"
                result += f"      Shape: {ws_data['shape']}\n"
                result += f"      Columns: {len(ws_data['columns'])}\n"
                if ws_data['columns']:
                    result += f"      Sample columns: {ws_data['columns'][:5]}{'...' if len(ws_data['columns']) > 5 else ''}\n"
                result += "\n"
            
            return result
            
        except Exception as e:
            return f"Error analyzing sheet: {e}"
    
    @staticmethod
    @init_google_workspace
    def analyze_dataframes(
        worksheet_data: Annotated[List[Dict], "list of worksheet data from read_all_worksheets"]
    ) -> str:
        """
        Analyze DataFrames from worksheet data.
        
        Args:
            worksheet_data: List of worksheet data from read_all_worksheets
            
        Returns:
            Analysis report
        """
        
        try:
            result = "📊 DataFrame Analysis Report\n"
            result += "=" * 40 + "\n\n"
            
            for ws_data in worksheet_data:
                if ws_data['status'] == 'success' and not ws_data['dataframe'].empty:
                    df = ws_data['dataframe']
                    worksheet_name = ws_data['worksheet_name']
                    
                    result += f"📋 Worksheet: {worksheet_name}\n"
                    result += f"   Shape: {df.shape}\n"
                    result += f"   Memory usage: {df.memory_usage(deep=True).sum() / 1024:.2f} KB\n"
                    
                    # Data types
                    result += f"   Data types:\n"
                    for dtype, count in df.dtypes.value_counts().items():
                        result += f"     {dtype}: {count} columns\n"
                    
                    # Numeric columns analysis
                    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                    if numeric_cols:
                        result += f"   Numeric columns: {len(numeric_cols)}\n"
                        result += f"     Sample: {numeric_cols[:5]}{'...' if len(numeric_cols) > 5 else ''}\n"
                        
                        # Basic statistics for first few numeric columns
                        for col in numeric_cols[:3]:
                            try:
                                stats = df[col].describe()
                                result += f"     {col}: mean={stats['mean']:.2f}, std={stats['std']:.2f}\n"
                            except:
                                pass
                    
                    # Missing values
                    missing = df.isnull().sum()
                    if missing.sum() > 0:
                        result += f"   Missing values: {missing.sum()} total\n"
                        for col, count in missing[missing > 0].head(3).items():
                            result += f"     {col}: {count} missing\n"
                    
                    result += "\n"
            
            return result
            
        except Exception as e:
            return f"Error analyzing DataFrames: {e}"
    
    @staticmethod
    @init_google_workspace
    def suggest_chart_columns(
        sheet_name: Annotated[str, "name of the Google Sheet"],
        target_metric: Annotated[str, "metric to look for (e.g., 'revenue', 'customers')"]
    ) -> str:
        """
        Suggest chart columns based on a target metric.
        
        Args:
            sheet_name: Name of the Google Sheet
            target_metric: Metric to look for
            
        Returns:
            Suggested columns for charting
        """
        
        try:
            # Get all worksheets
            sheet = gc.open(sheet_name)
            worksheets = sheet.worksheets()
            
            suggestions = []
            
            for worksheet in worksheets:
                try:
                    all_values = worksheet.get_all_values()
                    if not all_values:
                        continue
                    
                    headers = all_values[0]
                    
                    # Look for columns containing the target metric
                    matching_cols = [col for col in headers if target_metric.lower() in col.lower()]
                    
                    if matching_cols:
                        suggestions.append({
                            'worksheet': worksheet.title,
                            'columns': matching_cols,
                            'all_columns': headers
                        })
                        
                except Exception as e:
                    continue
            
            if not suggestions:
                return f"No columns found matching '{target_metric}' in any worksheet."
            
            result = f"📊 Chart Column Suggestions for '{target_metric}':\n"
            result += "=" * 50 + "\n\n"
            
            for suggestion in suggestions:
                result += f"📋 Worksheet: {suggestion['worksheet']}\n"
                result += f"   Matching columns: {suggestion['columns']}\n"
                result += f"   All columns: {suggestion['all_columns'][:10]}{'...' if len(suggestion['all_columns']) > 10 else ''}\n\n"
            
            return result
            
        except Exception as e:
            return f"Error suggesting chart columns: {e}"
    
    @staticmethod
    @init_google_workspace
    def create_chart(
        sheet_name: Annotated[str, "name of the Google Sheet"],
        worksheet_name: Annotated[str, "name of the worksheet"],
        chart_type: Annotated[str, "type of chart (line, bar, pie, etc.)"],
        x_column: Annotated[str, "column name for x-axis"],
        y_column: Annotated[str, "column name for y-axis"],
        chart_title: Annotated[str, "title for the chart"]
    ) -> str:
        """
        Create a chart from Google Sheets data.
        
        Args:
            sheet_name: Name of the Google Sheet
            worksheet_name: Name of the worksheet
            chart_type: Type of chart
            x_column: Column name for x-axis
            y_column: Column name for y-axis
            chart_title: Title for the chart
            
        Returns:
            Success message with chart details
        """
        
        try:
            # Get worksheet data
            sheet = gc.open(sheet_name)
            worksheet = sheet.worksheet(worksheet_name)
            all_values = worksheet.get_all_values()
            
            if not all_values:
                return f"No data found in worksheet {worksheet_name}"
            
            headers = all_values[0]
            data_rows = all_values[1:]
            
            # Find column indices
            try:
                x_col_idx = headers.index(x_column)
                y_col_idx = headers.index(y_column)
            except ValueError:
                return f"Column not found. Available columns: {headers}"
            
            # Create DataFrame
            df = pd.DataFrame(data_rows, columns=headers)
            
            # Convert to numeric
            try:
                df[x_column] = pd.to_numeric(df[x_column], errors='coerce')
                df[y_column] = pd.to_numeric(df[y_column], errors='coerce')
            except:
                pass
            
            # Remove NaN values
            df = df.dropna(subset=[x_column, y_column])
            
            if df.empty:
                return "No valid data points found for charting"
            
            # Create chart using matplotlib
            import matplotlib.pyplot as plt
            
            plt.figure(figsize=(10, 6))
            
            if chart_type.lower() == 'line':
                plt.plot(df[x_column], df[y_column], marker='o')
            elif chart_type.lower() == 'bar':
                plt.bar(df[x_column], df[y_column])
            elif chart_type.lower() == 'scatter':
                plt.scatter(df[x_column], df[y_column])
            else:
                plt.plot(df[x_column], df[y_column], marker='o')  # Default to line
            
            plt.title(chart_title)
            plt.xlabel(x_column)
            plt.ylabel(y_column)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Save chart
            chart_filename = f"{sheet_name}_{worksheet_name}_{chart_type}_chart.png"
            plt.savefig(chart_filename, dpi=300, bbox_inches='tight')
            plt.close()
            
            return f"✅ Chart created successfully!\n📊 Chart saved as: {chart_filename}\n📈 Type: {chart_type}\n📋 Data points: {len(df)}"
            
        except Exception as e:
            return f"Error creating chart: {e}"
    
    @staticmethod
    @init_google_workspace
    def export_sheet_as_csv(
        sheet_name: Annotated[str, "name of the Google Sheet"],
        worksheet_name: Annotated[str, "name of the worksheet (optional)"] = None,
        output_filename: Annotated[str, "name for the CSV file"] = None
    ) -> str:
        """
        Export a Google Sheet worksheet as CSV.
        
        Args:
            sheet_name: Name of the Google Sheet
            worksheet_name: Optional specific worksheet name
            output_filename: Name for the CSV file
            
        Returns:
            Success message with file details
        """
        
        try:
            # Open the sheet
            sheet = gc.open(sheet_name)
            
            # Get worksheet
            if worksheet_name:
                worksheet = sheet.worksheet(worksheet_name)
            else:
                worksheet = sheet.get_worksheet(0)
            
            if not worksheet:
                return f"No worksheet found in {sheet_name}"
            
            # Get all values
            all_values = worksheet.get_all_values()
            
            if not all_values:
                return f"No data found in {sheet_name}"
            
            # Create DataFrame
            headers = all_values[0]
            data_rows = all_values[1:] if len(all_values) > 1 else []
            df = pd.DataFrame(data_rows, columns=headers)
            
            # Generate filename if not provided
            if not output_filename:
                output_filename = f"{sheet_name}_{worksheet.title}.csv"
            
            # Export to CSV
            df.to_csv(output_filename, index=False)
            
            return f"✅ CSV exported successfully!\n📄 File: {output_filename}\n📊 Rows: {len(df)}\n📋 Columns: {len(df.columns)}"
            
        except Exception as e:
            return f"Error exporting CSV: {e}"
    
    @staticmethod
    @init_google_workspace
    def search_sheets_by_content(
        search_term: Annotated[str, "term to search for in sheets"],
        max_results: Annotated[int, "maximum number of results"] = 10
    ) -> str:
        """
        Search Google Sheets by content.
        
        Args:
            search_term: Term to search for
            max_results: Maximum number of results
            
        Returns:
            Search results
        """
        
        try:
            # Search for files containing the term
            results = drive_service.files().list(
                q=f"mimeType='application/vnd.google-apps.spreadsheet' and fullText contains '{search_term}'",
                pageSize=max_results,
                fields="files(id, name, webViewLink, modifiedTime)"
            ).execute()
            
            files = results.get('files', [])
            
            if not files:
                return f"No Google Sheets found containing '{search_term}'"
            
            result = f"🔍 Search Results for '{search_term}':\n"
            result += "=" * 50 + "\n\n"
            
            for file in files:
                result += f"📊 {file['name']}\n"
                result += f"   🔗 {file['webViewLink']}\n"
                result += f"   📅 Modified: {file['modifiedTime'][:10]}\n"
                result += f"   🆔 ID: {file['id']}\n\n"
            
            return result
            
        except Exception as e:
            return f"Error searching sheets: {e}" 