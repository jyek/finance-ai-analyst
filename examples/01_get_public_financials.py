#!/usr/bin/env python3
"""
Example 1: Get Public Company Financials into Google Sheet

This example demonstrates how to use the Finance AI Analyst to:
1. Pull financial data from Yahoo Finance for public companies
2. Create Google Sheets with income statement data
3. Organize data with separate worksheets for each company
"""

import os
import sys
import autogen

# # Add the parent directory to the path so we can import local modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.finance_analyst import FinanceAnalystAgent
from config import get_config

def main():
    """Main example function for getting public financials"""
    
    # Load configuration
    config = get_config("config.json")
    
    print("🤖 Finance AI Analyst - Public Financials Example")
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
    
    # Create a code executor agent for tool execution
    code_executor = FinanceAnalystAgent.create_code_executor_agent(
        llm_config=llm_config
    )
    
    # Create the Finance Analyst agent
    finance_agent = FinanceAnalystAgent.create_agent(
        llm_config=llm_config,
        human_input_mode="NEVER",
        user_proxy=code_executor
    )
    
    # Create a user proxy for conversation
    user_proxy = autogen.UserProxyAgent(
        name="user",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=2,
        code_execution_config=False
    )
    
    print("✅ Agents created successfully!")
    
    # Example: Get financial data for tech companies
    print("\n📊 Example: Tech Companies Financial Data")
    print("-" * 40)
    
    task = """
    Create a Google Sheet with income statement data for the following companies:
    - Apple (AAPL)
    - Microsoft (MSFT)
    - Google (GOOGL)
    
    Use the year 2024 and create separate worksheets for each company.
    Name the sheet "Tech_Companies_Income_Statements_2024".
    Include key metrics like Total Revenue, Gross Profit, Operating Income, and Net Income.
    """
    
    print("Executing analysis...")
    # Create a group chat where Finance_Analyst can talk to Code_Executor
    groupchat = autogen.GroupChat(
        agents=[user_proxy, finance_agent, code_executor],
        messages=[],
        max_round=50
    )
    manager = autogen.GroupChatManager(
        groupchat=groupchat,
        llm_config=llm_config
    )
    
    result = user_proxy.initiate_chat(
        manager,
        message=task
    )
    
    print("\n🎉 Public Financials Analysis completed successfully!")
    print("\n📋 Summary:")
    print("   ✅ Created Google Sheet with tech company financial data")
    print("   ✅ Pulled income statement data for Apple, Microsoft, and Google")
    print("   ✅ Organized data with separate worksheets for each company")
    print("   ✅ Included key financial metrics and ratios")
    
    print("\n💡 Next Steps:")
    print("   - Check your Google Drive for the created file")
    print("   - Review the financial data and structure")
    print("   - Run the benchmarking analysis example next")
    print("   - Customize the companies and time periods as needed")

if __name__ == "__main__":
    main() 