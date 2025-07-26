#!/usr/bin/env python3
"""
AI Finance Analyst - Terminal Interface

An interactive terminal application to chat with the AI Finance Analyst.
"""

import sys
import os
import autogen
from agents.finance_analyst import FinanceAnalystAgent
from config import get_config

class SimplePromptUserProxy(autogen.UserProxyAgent):
    """Custom UserProxyAgent with simplified prompt"""
    
    def get_human_input(self, prompt: str) -> str:
        """Override to use simple '>' prompt instead of default"""
        return input("> ")

def main():
    """Main function to start the interactive Finance Analyst agent."""
    
    print("🤖 Finance AI Analyst - Terminal Interface")
    print("=" * 50)
    
    try:
        # Load configuration
        print("📋 Loading configuration...")
        config = get_config("config.json")
        print("✅ Configuration loaded successfully")
        
        # Create a code executor agent for tool execution
        print("🔧 Creating code executor agent...")
        code_executor = FinanceAnalystAgent.create_code_executor_agent(
            llm_config=config.llm_config
        )
        print("✅ Code executor agent created")
        
        # Create the Finance Analyst agent
        print("🧠 Initializing Finance Analyst agent...")
        finance_agent = FinanceAnalystAgent.create_agent(
            llm_config=config.llm_config,
            human_input_mode="NEVER",  # Run tools automatically without asking
            max_consecutive_auto_reply=10,  # Allow multiple auto-replies
            user_proxy=code_executor  # Use code executor for tool execution
        )
        print("✅ Finance Analyst agent initialized")
        
        # Create a user proxy for conversation
        print("👤 Creating user proxy for conversation...")
        user_proxy = SimplePromptUserProxy(
            name="user",
            human_input_mode="ALWAYS",  # Always ask for your input when it's your turn
            max_consecutive_auto_reply=0,  # Never auto-reply - wait for your input
            code_execution_config=False  # Disable code execution
        )
        print("✅ User proxy created")
        
        # Create a group chat where Finance_Analyst can talk to Code_Executor
        print("🤝 Setting up group chat...")
        groupchat = autogen.GroupChat(
            agents=[user_proxy, finance_agent, code_executor],
            messages=[],
            max_round=50
        )
        manager = autogen.GroupChatManager(
            groupchat=groupchat,
            llm_config=config.llm_config
        )
        print("✅ Group chat configured")
        
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
            manager,
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