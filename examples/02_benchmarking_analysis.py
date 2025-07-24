#!/usr/bin/env python3
"""
Example 2: Perform Benchmarking Analysis

This example demonstrates how to use the Finance AI Analyst to:
1. Analyze existing Google Sheets with financial data
2. Run benchmarking analysis across companies
3. Compute financial ratios and metrics
4. Create comparison charts and visualizations
"""

import os
import sys
import autogen

# Add the parent directory to the path so we can import local modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.finance_analyst import FinanceAnalystAgent
from config import get_config

def main():
    """Main example function for benchmarking analysis"""
    
    # Load configuration
    config = get_config("config.json")
    
    print("🤖 Finance AI Analyst - Benchmarking Analysis Example")
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
    
    # Example: Benchmark tech companies
    print("\n📊 Example: Tech Companies Benchmarking")
    print("-" * 40)
    
    task = """
    Analyze the Google Sheet "Tech_Companies_Income_Statements_2024" and:
    1. Run comprehensive benchmarking analysis for 2022-2024
    2. Compute key financial ratios:
       - Net Profit Margin
       - Gross Profit Margin
       - Operating Margin
       - Revenue Growth Rate
    3. Create comparison charts for each metric
    4. Generate a summary document with insights
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
    
    print("\n🎉 Benchmarking Analysis completed successfully!")
    print("\n📋 Summary:")
    print("   ✅ Performed tech companies benchmarking analysis")
    print("   ✅ Computed key financial ratios and metrics")
    print("   ✅ Created comparison charts and visualizations")
    print("   ✅ Generated summary document with insights")
    
    print("\n💡 Next Steps:")
    print("   - Review the generated analysis document")
    print("   - Check the charts and visualizations created")
    print("   - Run the income statement analysis example next")
    print("   - Customize the analysis parameters as needed")

if __name__ == "__main__":
    main() 