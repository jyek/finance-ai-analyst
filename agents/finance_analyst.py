"""
Finance Analyst Agent

A comprehensive agent for managing financial data through Google Workspace APIs.
"""

import autogen
from typing import Dict, Any, List
from textwrap import dedent
from tools.workspace import WorkspaceUtils
from tools.sheet import SheetUtils, SheetAnalyzer
from tools.research import ResearchUtils
import os
import pickle
from google.oauth2.credentials import Credentials as OAuthCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import gspread

# OAuth2 scopes for Google Workspace
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/presentations'
]

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
            print("✅ OAuth token saved for future use")
        except Exception as e:
            print(f"⚠️ Could not save token: {e}")
    
    return creds

class FinanceAnalystAgent:
    """Finance Analyst for analyzing spreadsheet trends"""
    
    # Global OAuth credentials - initialized once and reused
    _oauth_creds = None
    _gc = None
    
    @classmethod
    def initialize_oauth(cls):
        """Initialize OAuth credentials once for the entire agent session"""
        if cls._oauth_creds is None:
            print("🔐 Initializing OAuth credentials for Finance Analyst...")
            
            # Get OAuth credentials
            oauth_credentials_json = None
            try:
                from config import get_config
                config = get_config("config.json")
                oauth_credentials_json = config.google_oauth_credentials_json
            except:
                oauth_credentials_json = os.environ.get("GOOGLE_OAUTH_CREDENTIALS_JSON")
            
            if not oauth_credentials_json:
                print("❌ OAuth credentials not found in config or environment variables.")
                return False
            
            cls._oauth_creds = get_oauth_credentials_from_json(oauth_credentials_json)
            if cls._oauth_creds:
                cls._gc = gspread.authorize(cls._oauth_creds)
                print("✅ Google Sheets client initialized for Finance Analyst")
                return True
            else:
                print("❌ Failed to initialize OAuth credentials")
                return False
        
        return True
        
    @staticmethod
    def get_tools():
        """Get the list of tools for the Finance Analyst agent"""
        return [
            # Workspace utilities
            (WorkspaceUtils.create_google_doc, "create_google_doc", "Create a new Google Doc with specified title and content"),
            (WorkspaceUtils.create_google_doc_with_images, "create_google_doc_with_images", "Create a new Google Doc with specified title, content, and embedded images"),
            (WorkspaceUtils.read_google_doc, "read_google_doc", "Read content from a Google Doc"),
            (WorkspaceUtils.update_google_doc, "update_google_doc", "Update a Google Doc with new content"),
            (WorkspaceUtils.list_my_sheets, "list_my_sheets", "List Google Sheets accessible to the user"),
            (WorkspaceUtils.search_sheets_by_content, "search_sheets_by_content", "Search Google Sheets by content"),
            
            # Notes management
            (WorkspaceUtils.read_notes, "read_notes", "Read the contents of notes.md file"),
            (WorkspaceUtils.update_notes, "update_notes", "Write content to a specific section of the notes.md file"),
            (WorkspaceUtils.list_files, "list_files", "List all files in the files folder"),
            (WorkspaceUtils.save_dataframe, "save_dataframe", "Save a dataframe to the files folder in CSV or JSON format"),
            
            # Sheet utilities
            (SheetUtils.create_empty_sheet, "create_empty_sheet", "Create a new empty Google Sheet"),
            (SheetUtils.get_income_stmt_to_sheet, "get_income_stmt_to_sheet", "Get income statement data for multiple tickers and save to Google Sheets"),
            (SheetUtils.run_benchmarking, "run_benchmarking", "Add a benchmarking worksheet to an existing Google Sheet"),
            (SheetUtils.compute_financial_ratios, "compute_financial_ratios", "Compute financial ratios for all companies in a Google Sheet"),
            
            # Sheet analysis
            (SheetAnalyzer.read_worksheet, "read_worksheet", "Read data from a specific worksheet using structured analysis (runs header identification and data extraction)"),
            (SheetAnalyzer.read_all_worksheets, "read_all_worksheets", "Read all worksheets from a Google Sheet using structured analysis for each worksheet"),
            (SheetAnalyzer.analyze_dataframe, "analyze_dataframe", "Analyze DataFrame by identifying important metrics, generating commentary, and creating charts"),

            # Research and document download 
            (ResearchUtils.get_filings_from_company_website, "get_filings_from_company_website", "Search and download financial documents from a company's investor relations website. REQUIRES: company_name (string) AND search_criteria (dict with document_types list, optional keywords, max_documents, prioritize_latest)"),
            (ResearchUtils.list_downloaded_filings, "list_downloaded_filings", "List all downloaded financial filings in the drive folder"),    
        ]
    
    @staticmethod
    def create_agent(
        name: str = "Finance_Analyst",
        llm_config: Dict[str, Any] = None,
        human_input_mode: str = "NEVER",
        max_consecutive_auto_reply: int = 5,
        user_proxy: autogen.UserProxyAgent = None,
        **kwargs
    ) -> autogen.AssistantAgent:
        """
        Create a Finance Analyst agent with all Google Workspace capabilities.
        
        Args:
            name: Name for the agent
            llm_config: LLM configuration
            human_input_mode: Human input mode
            max_consecutive_auto_reply: Maximum consecutive auto replies
            **kwargs: Additional arguments for AssistantAgent
            
        Returns:
            Configured Finance Analyst agent
        """
        
        # Define the agent profile
        profile = dedent(
            f"""
            Role: Finance Analyst
            Department: Financial Planning and Analysis
            Primary Responsibility: Help a company understand its financial performance, make better decisions, and plan for the future

            Role Description:
            As a Finance Analyst, you are an expert in analyzing financial data through structured workflows. You can identify important metrics, generate insightful commentary, and create visual charts from spreadsheet data. You can also manage Google Sheets and Google Docs for comprehensive financial analysis workflows.

            Key Capabilities:

            Automated Financial Analysis:
            - Identify sheet headers and extract structured data from Google Sheets
            - Automatically identify important financial metrics for analysis
            - Generate comprehensive commentary with trends and insights
            - Create visual charts for each important metric
            - Analyze individual worksheets or entire spreadsheets
            - Provide step-by-step analysis with clear resultsts

            Google Sheets Management:
            - Create and manage Google Sheets with proper formatting
            - Import income statement data for multiple tickers
            - Run benchmarking analyses across companies
            - Compute financial ratios with flexible configurations
            - Search and list accessible sheets
            - Organize files in Google Drive folders

            Research and Document Download:
            - Search for company investor relations pages
            - Download financial documents (annual reports, presentations, filings)
            - Search and download specific documents based on criteria
            - List and manage downloaded financial documents
            - Use browser automation to bypass anti-bot measures
            
            Document Search Intelligence:
            - ALWAYS interpret user requests intelligently and infer document types from natural language
            - "investor presentation" = document_type: ["presentation"]
            - "annual report" = document_type: ["annual_report"]
            - "quarterly report" = document_type: ["quarterly_report", "presentation"]
            - "financial filings" = document_type: ["filing"]
            - "latest" = prioritize_latest: True
            - "recent" = prioritize_latest: True
            - "2024" = keywords: ["2024"]
            - "Q4" = keywords: ["q4", "quarterly"]
            - DO NOT ask for clarification when the document type is clear from the request
            - Automatically set reasonable defaults: max_documents=5, prioritize_latest=True
            - Use keywords to improve search relevance based on the request context
            - IMPORTANT: ALWAYS provide BOTH company_name AND search_criteria parameters to get_filings_from_company_website
            - search_criteria should be a dictionary with at least document_types (list) and optionally keywords, max_documents, prioritize_latest
            - Example: {{"document_types": ["presentation"], "prioritize_latest": true}}
            - ONLY use the registered tools (get_filings_from_company_website, list_downloaded_filings)
            - DO NOT try to execute browser automation code directly
            - DO NOT try to import or use Playwright, requests, or other libraries directly
            - All browser automation is handled internally by the registered tools

            Collaboration Features:
            - Share sheets and docs with team members
            - Organize files in Google Drive folders
            - Maintain version control and access permissions
            - Provide URLs for easy access to created documents

            Key Objectives:
            - Identify and analyze important financial metrics automatically
            - Generate insightful commentary with trends and statistics
            - Create visual charts for better data understanding
            - Provide clear, actionable insights from sheet data
            - Create professional, well-formatted financial reports
            - Enable collaborative financial analysis workflows
            - Maintain data integrity and proper formatting
            
            Important Instructions:
            - When using get_income_stmt_to_sheet for multiple tickers, always pass ticker as a list: ticker=['TICKER1', 'TICKER2']
            - Do not pass tickers as a comma-separated string
            - This ensures separate worksheets are created for each ticker
            
            Sheet Analysis Workflow:
            - Use read_worksheet for single worksheet analysis
            - Use read_all_worksheets for multiple worksheet analysis
            - Use analyze_dataframe to automatically identify metrics, generate commentary, create charts, and create a report
            - Workflow: Header Identification → Data Extraction → Metric Identification → Commentary → Charts → HTML Report Generation
            
            Note-Taking Workflow:
            - Always use read_notes before starting any analysis to consider user preferences
            - Apply user preferences to tool calls and analysis
            - Use update_notes to store user preferences in bullet points
            
            Financial Ratio Analysis:
            - Use compute_financial_ratios to create flexible ratio comparisons across all tickers
            - You can analyze any ratio by specifying numerator and denominator metrics
            - Common ratios: Net Profit Margin (Net Income/Total Revenue), Gross Profit Margin (Gross Profit/Total Revenue), 
              Revenue Growth (Current Revenue/Previous Revenue), Operating Margin (Operating Income/Total Revenue)
            - Output formats: 'percentage' for margins, 'decimal' for ratios, 'ratio' for fraction display
            - All formulas are traceable back to source data for auditability

            Performance Indicators:
            Success is measured by the quality of structured financial analysis, the clarity of insights provided from automated metric identification, the usefulness of generated commentary and charts, and the professional presentation of financial reports. The agent should provide valuable financial insights through automated analysis workflows and enable seamless collaboration through Google Workspace tools.

            Reply TERMINATE when the task is completed successfully.
            """
        )
        
        # Remove user_proxy from kwargs to avoid passing it to AssistantAgent
        agent_kwargs = kwargs.copy()
        if 'user_proxy' in agent_kwargs:
            del agent_kwargs['user_proxy']
        
        # Create the agent
        agent = autogen.AssistantAgent(
            name=name,
            system_message=profile,
            llm_config=llm_config,
            human_input_mode=human_input_mode,
            max_consecutive_auto_reply=max_consecutive_auto_reply,
            **agent_kwargs
        )
        
        # Initialize OAuth credentials once for the entire agent session
        FinanceAnalystAgent.initialize_oauth()
        
        # Register all the toolkit functions
        if user_proxy:
            FinanceAnalystAgent._register_toolkits(agent, user_proxy)
        
        return agent
    
    @staticmethod
    def _register_toolkits(agent: autogen.AssistantAgent, user_proxy: autogen.UserProxyAgent = None):
        """Register all toolkit functions with the agent"""
        
        # Register all tools from the get_tools method
        for func, name, description in FinanceAnalystAgent.get_tools():
            autogen.register_function(
                func,
                caller=agent,
                executor=user_proxy,
                name=name,
                description=description
            )
    
    @staticmethod
    def create_code_executor_agent(
        name: str = "Code_Executor",
        llm_config: Dict[str, Any] = None,
        human_input_mode: str = "NEVER",
        max_consecutive_auto_reply: int = 5,
        **kwargs
    ) -> autogen.UserProxyAgent:
        """
        Create a code executor agent for the Finance Analyst.
        
        Args:
            name: Name for the code executor
            human_input_mode: Human input mode
            max_consecutive_auto_reply: Maximum consecutive auto replies
            **kwargs: Additional arguments for UserProxyAgent
            
        Returns:
            Configured code executor agent
        """
        
        return autogen.UserProxyAgent(
            name=name,
            llm_config=llm_config,
            human_input_mode=human_input_mode,
            max_consecutive_auto_reply=max_consecutive_auto_reply,
            is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").strip().endswith("TERMINATE"),
            code_execution_config={"use_docker": False},
            **kwargs
        )