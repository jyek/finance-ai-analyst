"""
Finance Analyst Agent

A comprehensive agent for managing financial data through Google Workspace APIs.
"""

import autogen
from typing import Dict, Any, List
from textwrap import dedent
from tools.workspace import WorkspaceUtils
from tools.spreadsheet import SpreadsheetUtils
from tools.dataset_manager import DatasetManager

class FinanceAnalystAgent:
    """Finance Analyst Agent for Google Workspace operations"""
    
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
            Primary Responsibility: Managing Google Sheets, Google Docs, and Google Slides for Financial Analysis

            Role Description:
            As a Finance Analyst, you are an expert in managing and analyzing financial data through Google's collaborative tools. You can create, read, and update Google Sheets and Google Docs, making you invaluable for financial analysis workflows. You can access existing Google Sheets, read their data, and provide insights based on the content. You can also create comprehensive financial reports as Google Docs and manage multiple ticker income statements in Google Sheets.

            Key Capabilities:

            Google Sheets Management:
            - Save financial analysis data to Google Sheets with proper formatting
            - Create and manage multiple ticker income statements in a single sheet
            - Read and analyze existing Google Sheets data
            - Search across all accessible sheets for specific content
            - Get comprehensive summaries of sheet structure and data
            - Save datasets from Google Sheets for reuse across documents
            - Manage structured data with field names and periods

            Google Docs Integration:
            - Create professional financial reports as Google Docs
            - Read and extract content from existing Google Docs
            - Update Google Docs with new analysis or findings
            - Format reports with proper structure and metadata
            - Insert and refresh datapoints from datasets in Google Docs
            - Manage dynamic content with dataset placeholders

            Financial Data Analysis:
            - Read and analyze financial data from existing Google Sheets
            - Format financial data with proper number formatting
            - Create benchmarking analyses across multiple companies
            - Generate insights from financial data in sheets

            Dataset Management:
            - Save datasets from Google Sheets for consistent data access
            - Insert and refresh datapoints in documents for dynamic reporting
            - Manage structured data with field names and periods
            - Create reusable data sources for financial analysis

            Collaboration Features:
            - Share sheets and docs with team members
            - Organize files in Google Drive folders
            - Maintain version control and access permissions
            - Provide URLs for easy access to created documents

            Key Objectives:
            - Read and analyze financial data from existing Google Sheets
            - Save financial analysis data to Google Sheets with proper formatting
            - Create and manage multiple ticker income statements efficiently
            - Provide clear, actionable insights from sheet data
            - Create professional, well-formatted financial reports
            - Enable collaborative financial analysis workflows
            - Maintain data integrity and proper formatting
            - Save and manage datasets for consistent data access
            - Insert and refresh datapoints in documents for dynamic reporting
            
            Important Instructions:
            - When using get_income_stmt_to_sheet for multiple tickers, always pass ticker as a list: ticker=['TICKER1', 'TICKER2']
            - Do not pass tickers as a comma-separated string
            - This ensures separate worksheets are created for each ticker
            
            Financial Ratio Analysis:
            - Use compute_financial_ratios to create flexible ratio comparisons across all tickers
            - You can analyze any ratio by specifying numerator and denominator metrics
            - Common ratios: Net Profit Margin (Net Income/Total Revenue), Gross Profit Margin (Gross Profit/Total Revenue), 
              Revenue Growth (Current Revenue/Previous Revenue), Operating Margin (Operating Income/Total Revenue)
            - Output formats: 'percentage' for margins, 'decimal' for ratios, 'ratio' for fraction display
            - All formulas are traceable back to source data for auditability

            Dataset Management:
            - Use save_dataset_from_sheet to create reusable datasets from Google Sheets
            - Use insert_datapoint_into_doc to add dynamic data to Google Docs
            - Use refresh_datapoints_in_doc to update all datapoints in a document
            - Datasets are stored locally and can be reused across multiple documents
            - Use placeholder format "{{dataset.field.period}}" for datapoints

            Performance Indicators:
            Success is measured by the quality and accessibility of financial data management, the clarity of insights provided from sheet analysis, and the professional presentation of financial reports. The agent should enable seamless collaboration and provide valuable financial insights through Google Workspace tools.

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
        
        # Register all the toolkit functions
        if user_proxy:
            FinanceAnalystAgent._register_toolkits(agent, user_proxy)
        
        return agent
    
    @staticmethod
    def _register_toolkits(agent: autogen.AssistantAgent, user_proxy: autogen.UserProxyAgent):
        """Register all toolkit functions with the agent"""
        
        # Workspace utilities
        autogen.register_function(
            WorkspaceUtils.create_google_doc,
            caller=agent,
            executor=user_proxy,
            name="create_google_doc",
            description="Create a new Google Doc with specified title and content"
        )
        
        autogen.register_function(
            WorkspaceUtils.read_google_doc,
            caller=agent,
            executor=user_proxy,
            name="read_google_doc",
            description="Read content from a Google Doc"
        )
        
        autogen.register_function(
            WorkspaceUtils.update_google_doc,
            caller=agent,
            executor=user_proxy,
            name="update_google_doc",
            description="Update a Google Doc with new content"
        )
        
        autogen.register_function(
            WorkspaceUtils.update_doc_variables,
            caller=agent,
            executor=user_proxy,
            name="update_doc_variables",
            description="Update variables in a Google Doc by replacing placeholders"
        )
        
        autogen.register_function(
            WorkspaceUtils.list_my_sheets,
            caller=agent,
            executor=user_proxy,
            name="list_my_sheets",
            description="List Google Sheets accessible to the user"
        )
        
        autogen.register_function(
            WorkspaceUtils.read_worksheet,
            caller=agent,
            name="read_worksheet",
            description="Read data from a specific worksheet in a Google Sheet",
            executor=user_proxy
        )
        
        autogen.register_function(
            WorkspaceUtils.read_all_worksheets,
            caller=agent,
            name="read_all_worksheets",
            description="Read all worksheets from a Google Sheet and return as DataFrames",
            executor=user_proxy
        )
        
        autogen.register_function(
            WorkspaceUtils.analyze_dataframes,
            caller=agent,
            name="analyze_dataframes",
            description="Analyze DataFrames from worksheet data",
            executor=user_proxy
        )
        
        autogen.register_function(
            WorkspaceUtils.suggest_chart_columns,
            caller=agent,
            name="suggest_chart_columns",
            description="Suggest chart columns based on a target metric",
            executor=user_proxy
        )
        
        autogen.register_function(
            WorkspaceUtils.create_chart,
            caller=agent,
            name="create_chart",
            description="Create a chart from Google Sheets data",
            executor=user_proxy
        )
        
        autogen.register_function(
            WorkspaceUtils.export_sheet_as_csv,
            caller=agent,
            name="export_sheet_as_csv",
            description="Export a Google Sheet worksheet as CSV",
            executor=user_proxy
        )
        
        autogen.register_function(
            WorkspaceUtils.search_sheets_by_content,
            caller=agent,
            name="search_sheets_by_content",
            description="Search Google Sheets by content",
            executor=user_proxy
        )
        
        # Spreadsheet utilities
        autogen.register_function(
            SpreadsheetUtils.create_empty_sheet,
            caller=agent,
            name="create_empty_sheet",
            description="Create a new empty Google Sheet",
            executor=user_proxy
        )
        
        autogen.register_function(
            SpreadsheetUtils.get_income_stmt_to_sheet,
            caller=agent,
            name="get_income_stmt_to_sheet",
            description="Get income statement data for multiple tickers and save to Google Sheets",
            executor=user_proxy
        )
        
        autogen.register_function(
            SpreadsheetUtils.run_benchmarking,
            caller=agent,
            name="run_benchmarking",
            description="Add a benchmarking worksheet to an existing Google Sheet",
            executor=user_proxy
        )
        
        autogen.register_function(
            SpreadsheetUtils.compute_financial_ratios,
            caller=agent,
            name="compute_financial_ratios",
            description="Compute financial ratios for all companies in a Google Sheet",
            executor=user_proxy
        )
        
        # Dataset management utilities
        autogen.register_function(
            DatasetManager.save_dataset_from_sheet,
            caller=agent,
            name="save_dataset_from_sheet",
            description="Save a dataset from a Google Sheet",
            executor=user_proxy
        )
        
        autogen.register_function(
            DatasetManager.insert_datapoint_into_doc,
            caller=agent,
            name="insert_datapoint_into_doc",
            description="Insert a datapoint into a Google Doc using a placeholder",
            executor=user_proxy
        )
        
        autogen.register_function(
            DatasetManager.refresh_datapoints_in_doc,
            caller=agent,
            name="refresh_datapoints_in_doc",
            description="Refresh all datapoints in a Google Doc by replacing placeholders with current values",
            executor=user_proxy
        )
        
        autogen.register_function(
            DatasetManager.list_datasets,
            caller=agent,
            name="list_datasets",
            description="List all available datasets",
            executor=user_proxy
        )
        
        autogen.register_function(
            DatasetManager.get_datapoint,
            caller=agent,
            name="get_datapoint",
            description="Get a specific datapoint value",
            executor=user_proxy
        )
    
    @staticmethod
    def create_user_proxy(
        name: str = "User",
        human_input_mode: str = "NEVER",
        max_consecutive_auto_reply: int = 5,
        **kwargs
    ) -> autogen.UserProxyAgent:
        """
        Create a user proxy agent for the Finance Analyst.
        
        Args:
            name: Name for the user proxy
            human_input_mode: Human input mode
            max_consecutive_auto_reply: Maximum consecutive auto replies
            **kwargs: Additional arguments for UserProxyAgent
            
        Returns:
            Configured user proxy agent
        """
        
        return autogen.UserProxyAgent(
            name=name,
            human_input_mode=human_input_mode,
            max_consecutive_auto_reply=max_consecutive_auto_reply,
            is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").strip().endswith("TERMINATE"),
            code_execution_config={"use_docker": False},
            **kwargs
        ) 