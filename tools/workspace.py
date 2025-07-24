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
    def create_google_doc_with_images(
        title: Annotated[str, "title of the Google Doc"],
        content: Annotated[str, "content to add to the document"],
        image_paths: Annotated[List[str], "list of image file paths to insert"] = None,
        folder_id: Annotated[Optional[str], "Google Drive folder ID where to create the doc"] = None
    ) -> str:
        """
        Create a new Google Doc with the specified title, content, and embedded images.
        
        Args:
            title: Title for the Google Doc
            content: Content to add to the document (plain text or markdown)
            image_paths: List of image file paths to insert into the document
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
            
            # Prepare batch update requests
            requests = []
            current_index = 1
            
            # Insert content first
            if content:
                requests.append({
                    'insertText': {
                        'location': {
                            'index': current_index
                        },
                        'text': content
                    }
                })
                current_index += len(content)
            
            # Insert images if provided
            if image_paths:
                for image_path in image_paths:
                    if os.path.exists(image_path):
                        # Upload image to Drive first
                        file_metadata = {
                            'name': os.path.basename(image_path),
                            'parents': [folder_id] if folder_id else [],
                            'role': 'reader',
                            'type': 'anyone'
                        }
                        
                        media = drive_service.files().create(
                            body=file_metadata,
                            media_body=image_path,
                            fields='id'
                        ).execute()
                        
                        image_id = media.get('id')
                        
                        # Make the image publicly accessible
                        drive_service.permissions().create(
                            fileId=image_id,
                            body={
                                'role': 'reader',
                                'type': 'anyone'
                            }
                        ).execute()
                        
                        # Insert image into document
                        requests.append({
                            'insertText': {
                                'location': {
                                    'index': current_index
                                },
                                'text': '\n'
                            }
                        })
                        current_index += 1
                        
                        requests.append({
                            'insertInlineImage': {
                                'location': {
                                    'index': current_index
                                },
                                'uri': f'https://drive.google.com/uc?id={image_id}',
                                'objectSize': {
                                    'height': {
                                        'magnitude': 300,
                                        'unit': 'PT'
                                    },
                                    'width': {
                                        'magnitude': 400,
                                        'unit': 'PT'
                                    }
                                }
                            }
                        })
                        current_index += 1
                        
                        requests.append({
                            'insertText': {
                                'location': {
                                    'index': current_index
                                },
                                'text': '\n'
                            }
                        })
                        current_index += 1
            
            # Execute batch update
            if requests:
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
            return f"Google Doc created with images: {doc_url}"
            
        except HttpError as error:
            return f"Error creating Google Doc with images: {error}"
        except Exception as e:
            return f"Error creating Google Doc with images: {str(e)}"
    
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
    

    
    # ============================================================================
    # LOCAL FILE MANAGEMENT FUNCTIONS
    # ============================================================================
    
    @staticmethod
    def create_notes(
        title: Annotated[str, "title for the notes file"] = "Agent Notes"
    ) -> str:
        """
        Create a notes.md file in the drive folder for the agent to store information
        
        Args:
            title: Title for the notes file
            
        Returns:
            Success message with file details
        """
        
        try:
            # Ensure drive folder exists
            drive_path = os.path.join(os.getcwd(), 'drive')
            os.makedirs(drive_path, exist_ok=True)
            
            # Create notes.md file path
            notes_file_path = os.path.join(drive_path, 'notes.md')
            
            # Check if file already exists
            if os.path.exists(notes_file_path):
                return f"✅ Notes file already exists at: {notes_file_path}"
            
            # Create the notes file with initial content
            initial_content = f"""# {title}

Created on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Notes

<!-- Add your notes here -->

## Analysis History

<!-- Track analysis sessions and findings -->

## Important Findings

<!-- Key insights and observations -->

## To-Do Items

<!-- Tasks and follow-ups -->

---
*This file is automatically managed by the Finance AI Analyst agent.*
"""
            
            with open(notes_file_path, 'w', encoding='utf-8') as f:
                f.write(initial_content)
            
            return f"✅ Notes file created successfully!\n📄 File: {notes_file_path}\n📝 Title: {title}"
            
        except Exception as e:
            return f"❌ Error creating notes file: {str(e)}"
    
    @staticmethod
    def read_notes() -> str:
        """
        Read the contents of notes.md file
        
        Returns:
            Contents of the notes file or error message
        """
        
        try:
            # Get notes file path
            drive_path = os.path.join(os.getcwd(), 'drive')
            notes_file_path = os.path.join(drive_path, 'notes.md')
            
            # Check if file exists
            if not os.path.exists(notes_file_path):
                return "❌ Notes file does not exist. Use create_notes_file() to create it first."
            
            # Read the file
            with open(notes_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return f"✅ Notes file read successfully!\n\n📄 Content:\n{content}"
            
        except Exception as e:
            return f"❌ Error reading notes file: {str(e)}"
    
    @staticmethod
    def update_notes(
        section: Annotated[str, "section to write to (e.g., 'Notes', 'Analysis History', 'Important Findings', 'To-Do Items')"],
        content: Annotated[str, "content to add to the section"]
    ) -> str:
        """
        Write content to a specific section of the notes.md file
        
        Args:
            section: Section name to write to
            content: Content to add
            
        Returns:
            Success message or error
        """
        
        try:
            # Get notes file path
            drive_path = os.path.join(os.getcwd(), 'drive')
            notes_file_path = os.path.join(drive_path, 'notes.md')
            
            # Check if file exists
            if not os.path.exists(notes_file_path):
                return "❌ Notes file does not exist. Use create_notes_file() to create it first."
            
            # Read current content
            with open(notes_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Find the section and add content
            section_found = False
            new_lines = []
            
            for line in lines:
                new_lines.append(line)
                
                # Check if this is the target section
                if line.strip().startswith(f"## {section}"):
                    section_found = True
                    # Add timestamp and content
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    new_lines.append(f"\n### {timestamp}\n")
                    new_lines.append(f"{content}\n\n")
            
            if not section_found:
                return f"❌ Section '{section}' not found in notes file. Available sections: Notes, Analysis History, Important Findings, To-Do Items"
            
            # Write back to file
            with open(notes_file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            return f"✅ Content written to '{section}' section successfully!\n📝 Added: {content[:100]}{'...' if len(content) > 100 else ''}"
            
        except Exception as e:
            return f"❌ Error writing to notes: {str(e)}"
    
    @staticmethod
    def list_drive_files() -> str:
        """
        List all files in the drive folder
        
        Returns:
            List of files in the drive folder
        """
        
        try:
            # Get drive folder path
            drive_path = os.path.join(os.getcwd(), 'drive')
            
            # Check if drive folder exists
            if not os.path.exists(drive_path):
                return "❌ Drive folder does not exist."
            
            # List files
            files = os.listdir(drive_path)
            
            if not files:
                return "📁 Drive folder is empty."
            
            result = "📁 Files in drive folder:\n"
            for file in files:
                file_path = os.path.join(drive_path, file)
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path)
                    modified = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
                    result += f"   📄 {file} ({size} bytes, modified: {modified})\n"
                else:
                    result += f"   📁 {file}/\n"
            
            return result
            
        except Exception as e:
            return f"❌ Error listing drive files: {str(e)}"
    
    @staticmethod
    def save_dataframe_to_drive(
        dataframe_name: Annotated[str, "name for the saved dataframe file"],
        dataframe_data: Annotated[str, "dataframe data in CSV format or JSON format"],
        file_format: Annotated[str, "format to save as: 'csv' or 'json'"] = "csv"
    ) -> str:
        """
        Save a dataframe to the drive folder
        
        Args:
            dataframe_name: Name for the saved dataframe file
            dataframe_data: Dataframe data in CSV or JSON format
            file_format: Format to save as (csv or json)
            
        Returns:
            Success message with file details
        """
        
        try:
            import pandas as pd
            import json
            
            # Ensure drive folder exists
            drive_path = os.path.join(os.getcwd(), 'drive')
            os.makedirs(drive_path, exist_ok=True)
            
            # Generate filename
            if not dataframe_name.endswith(f'.{file_format}'):
                dataframe_name = f"{dataframe_name}.{file_format}"
            
            file_path = os.path.join(drive_path, dataframe_name)
            
            # Check if file already exists
            if os.path.exists(file_path):
                return f"⚠️ File already exists: {file_path}"
            
            # Parse and save the dataframe
            if file_format.lower() == 'csv':
                # For CSV, assume the data is already in CSV format
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(dataframe_data)
                
                # Try to read it back to get info
                try:
                    df = pd.read_csv(file_path)
                    rows, cols = df.shape
                    result = f"✅ DataFrame saved as CSV successfully!\n"
                    result += f"📄 File: {file_path}\n"
                    result += f"📊 Shape: {rows} rows, {cols} columns\n"
                    result += f"📋 Columns: {list(df.columns)}\n"
                except Exception as e:
                    result = f"✅ DataFrame saved as CSV successfully!\n"
                    result += f"📄 File: {file_path}\n"
                    result += f"⚠️ Could not read back for details: {str(e)}"
                
            elif file_format.lower() == 'json':
                # For JSON, try to parse and save
                try:
                    if isinstance(dataframe_data, str):
                        data = json.loads(dataframe_data)
                    else:
                        data = dataframe_data
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    
                    result = f"✅ DataFrame saved as JSON successfully!\n"
                    result += f"📄 File: {file_path}\n"
                    result += f"📊 Data type: {type(data).__name__}\n"
                    
                except Exception as e:
                    return f"❌ Error saving JSON: {str(e)}"
            else:
                return f"❌ Unsupported format: {file_format}. Use 'csv' or 'json'."
            
            return result
            
        except Exception as e:
            return f"❌ Error saving dataframe: {str(e)}" 