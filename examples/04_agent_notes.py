#!/usr/bin/env python3
"""
Example 5: Notes Management

This example demonstrates the agent's ability to create, read, and write to a local notes.md file
for storing information and maintaining memory across sessions.
"""

import os
import sys
import autogen

# Add the parent directory to the path so we can import local modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.finance_analyst import FinanceAnalystAgent
from config import get_config
from tools.workspace import WorkspaceUtils

def main():
    """Main example function for notes management"""
    
    # Load configuration
    config = get_config("config.json")
    
    print("🤖 Finance AI Analyst - Notes Management Example")
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
    
    # Step 1: Create notes file
    print("📝 Step 1: Creating Notes File")
    print("-" * 40)
    
    result = WorkspaceUtils.create_notes("Finance AI Analyst Notes")
    print(result)
    print()
    
    # Step 2: List drive files
    print("📁 Step 2: Listing Drive Files")
    print("-" * 40)
    
    result = WorkspaceUtils.list_drive_files()
    print(result)
    print()
    
    # Step 3: Read notes file
    print("📖 Step 3: Reading Notes File")
    print("-" * 40)
    
    result = WorkspaceUtils.read_notes()
    print(result)
    print()
    
    # Step 4: Add some notes
    print("✏️ Step 4: Adding Notes")
    print("-" * 40)
    
    # Add general notes
    result = WorkspaceUtils.update_notes("Notes", "Initial setup completed. Agent is ready for financial analysis tasks.")
    print(result)
    print()
    
    # Add analysis note
    result = WorkspaceUtils.update_notes("Analysis History", "**Income Statement Analysis**\nSuccessfully analyzed Sample Income Statement sheet. Found monthly data for 2018 with revenue streams and cost structure.")
    print(result)
    print()
    
    # Add important finding
    result = WorkspaceUtils.update_notes("Important Findings", "Total Net Revenue for 2018: $9,325.0M with healthy gross profit margins")
    print(result)
    print()
    
    # Add todo item
    result = WorkspaceUtils.update_notes("To-Do Items", "- [ ] Analyze quarterly trends in the income statement data")
    print(result)
    print()
    
    # Step 5: Read updated notes
    print("📖 Step 5: Reading Updated Notes")
    print("-" * 40)
    
    result = WorkspaceUtils.read_notes()
    print(result)
    print()
    
    print("🎉 Notes Management Example completed successfully!")
    print("\n📋 Summary:")
    print("   ✅ Created notes.md file in drive folder")
    print("   ✅ Added structured notes with timestamps")
    print("   ✅ Demonstrated different note types (general, analysis, findings, todos)")
    print("   ✅ Showed file listing and reading capabilities")
    
    print("\n💡 Next Steps:")
    print("   - Use notes.md to track analysis sessions")
    print("   - Store important findings for future reference")
    print("   - Maintain to-do lists for follow-up tasks")
    print("   - Integrate notes with other analysis workflows")

if __name__ == "__main__":
    main() 