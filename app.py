#!/usr/bin/env python3
"""
Finance AI Analyst - Terminal Interface

An interactive terminal application to chat with the Finance AI Analyst agent.
The agent will ask for human input and never auto-reply.
"""

import sys
import os
import autogen
from agents.finance_analyst import FinanceAnalystAgent
from config import get_config

def main():
    """Main function to start the interactive Finance Analyst agent."""
    
    print("🤖 Finance AI Analyst - Terminal Interface")
    print("=" * 50)
    
    try:
        # Load configuration
        print("📋 Loading configuration...")
        config = get_config("config.json")
        print("✅ Configuration loaded successfully")
        
        # Create the Finance Analyst agent with direct tool execution
        print("🧠 Initializing Finance Analyst agent...")
        finance_agent = FinanceAnalystAgent.create_agent(
            llm_config=config.llm_config,
            human_input_mode="NEVER",  # Run tools automatically without asking
            max_consecutive_auto_reply=10,  # Allow multiple auto-replies
            code_execution_config={"use_docker": False}  # Enable code execution without Docker
        )
        print("✅ Finance Analyst agent initialized")
        
        # Create a simple user proxy for conversation only
        print("👤 Creating user proxy for conversation...")
        user_proxy = autogen.UserProxyAgent(
            name="user",
            human_input_mode="ALWAYS",  # Always ask for your input when it's your turn
            max_consecutive_auto_reply=0,  # Never auto-reply - wait for your input
            code_execution_config=False  # Disable code execution
        )
        print("✅ User proxy created")
        
        print("\n" + "=" * 50)
        print("🎯 Ready to chat! Type 'quit' or 'exit' to end the session.")
        print("💡 Example requests:")
        print("   - 'List the sheets in my Google Drive'")
        print("   - 'Analyze the income statement in my Google Sheet'")
        print("   - 'Get income statements for AAPL and GOOGL'")
        print("   - 'Run benchmarking analysis for 2022-2024 in my Google Sheet'")
        print("=" * 50 + "\n")
        
        # Start the chat with the Finance Analyst initiating
        finance_agent.initiate_chat(
            user_proxy,
            message="Hello! I'm ready to help you with financial analysis. What would you like me to do?"
        )
        
    except FileNotFoundError:
        print("❌ Error: config.json not found!")
        print("📝 Please copy config.json.example to config.json and add your credentials.")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Error initializing agent: {e}")
        print("🔧 Please check your configuration and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main() 