#!/usr/bin/env python3
"""
Example 3: Analyze Income Statement

This example demonstrates how to use the Finance AI Analyst to:
1. Analyze detailed income statements from Google Sheets
2. Create comprehensive financial analysis reports
3. Identify key drivers of profitability
4. Generate insights and recommendations
5. Create professional financial documents
"""

import os
import sys
import autogen

# Add the parent directory to the path so we can import local modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.finance_analyst import FinanceAnalystAgent
from config import get_config

def main():
    """Main example function for income statement analysis"""
    
    # Load configuration
    config = get_config("config.json")
    
    print("🤖 Finance AI Analyst - Income Statement Analysis Example")
    print("=" * 60)
    
    # Validate configuration
    if not config.validate():
        print("\n💡 To set up your configuration:")
        print("   1. Copy config.json.example to config.json")
        print("   2. Add your API keys to config.json")
        print("   3. Or set environment variables directly")
        return
    
    # Show configuration status
    config.print_status()
    print()
    
    # Get LLM configuration from config
    llm_config = config.llm_config
    
    # Create a user proxy first
    user_proxy = FinanceAnalystAgent.create_user_proxy()
    
    # Create the Finance Analyst agent
    finance_agent = FinanceAnalystAgent.create_agent(
        llm_config=llm_config,
        human_input_mode="NEVER",
        user_proxy=user_proxy
    )
    
    print("✅ Agent created successfully!")
    
    # Example: Read and analyze Income Statement Sample sheet
    print("\n📊 Example: Read Income Statement Sample Sheet")
    print("-" * 40)
    
    task = """
    Read and analyze the "Sample Income Statement" Google Sheet, specifically the "Profit and Loss (Monthly)" tab:
    
    1. Read the Data:
       - Read all data from the "Profit and Loss (Monthly)" worksheet
       - Identify the structure and columns in the data
       - Understand the time periods and financial metrics included
    
    2. Data Analysis:
       - Analyze the monthly income statement data
       - Identify key revenue and expense categories
       - Calculate monthly trends and patterns
       - Identify any seasonal variations or trends
    
    3. Create Analysis:
       - Generate a summary of the income statement structure
       - Create charts showing monthly trends
       - Identify the main revenue drivers and cost centers
       - Calculate key financial ratios and metrics
    
    4. Create a detailed analysis document with insights about the data
    """
    
    print("Executing analysis...")
    result = user_proxy.initiate_chat(
        finance_agent,
        message=task
    )
    
    print("\n🎉 Income Statement Analysis completed successfully!")
    print("\n📋 Summary:")
    print("   ✅ Read and analyzed the Income Statement Sample sheet")
    print("   ✅ Created comprehensive analysis of the Profile and Loss (Monthly) data")
    print("   ✅ Generated charts and insights from the monthly data")
    print("   ✅ Created detailed analysis document with findings")
    
    print("\n💡 Next Steps:")
    print("   - Review the generated analysis document")
    print("   - Check the charts and visualizations created")
    print("   - Use the insights for financial decision making")
    print("   - Customize the analysis for other income statement data")

if __name__ == "__main__":
    main() 