"""
Finance AI Analyst

A Python package for managing financial data through Google Workspace APIs.
Provides agents that can create, read, and update Google Sheets and Google Docs
for financial analysis workflows.

Author: Your Name
License: MIT
Version: 1.0.0
"""

from agents.finance_analyst import FinanceAnalystAgent
from tools.workspace import WorkspaceUtils
from tools.spreadsheet import SpreadsheetUtils
from tools.dataset_manager import DatasetManager

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

__all__ = [
    "FinanceAnalystAgent",
    "WorkspaceUtils", 
    "SpreadsheetUtils",
    "DatasetManager"
] 