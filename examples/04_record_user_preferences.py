#!/usr/bin/env python3
"""
Example 4: Record User Preferences

This example demonstrates the agent's ability to:
1. Read existing user preferences from notes.md
2. Set user preferences for analysis customization
3. Use preferences to guide analysis approach
4. Update preferences based on user feedback
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
    """Main example function for user preferences management"""
    
    # Load configuration
    config = get_config("config.json")
    
    print("🤖 Finance AI Analyst - User Preferences Example")
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
    
    # Step 1: Check if notes file exists
    print("📝 Step 1: Checking Notes File")
    print("-" * 40)
    
    result = WorkspaceUtils.read_notes()
    print(result)
    print()
    
    # Step 2: Set user preferences
    print("⚙️ Step 2: Setting User Preferences")
    print("-" * 40)
    
    preferences = """• Focus on profitability ratios (ROE, ROA, profit margins) and use percentage format
• Prioritize revenue growth, profit margins, and cash flow analysis
• Prefer stacked charts for summary rows and monthly charts over quarterly
• Focus on trend analysis and variance analysis
• Prefer HTML reports with detailed commentary
• Use color-coded charts for better visualization
• Include year-over-year comparisons in analysis"""
    
    result = WorkspaceUtils.update_notes("User Preferences", preferences)
    print(result)
    print()
    
    # Step 3: Read notes again to see preferences
    print("📖 Step 3: Reading Notes with Preferences")
    print("-" * 40)
    
    result = WorkspaceUtils.read_notes()
    print(result)
    print()
    
    # Step 4: Update preferences
    print("✏️ Step 4: Updating User Preferences")
    print("-" * 40)
    
    updated_preferences = """• Focus on profitability ratios (ROE, ROA, profit margins) and use percentage format
• Prioritize revenue growth, profit margins, and cash flow analysis
• Prefer stacked charts for summary rows and monthly charts over quarterly
• Focus on trend analysis and variance analysis
• Prefer HTML reports with detailed commentary
• Use color-coded charts for better visualization
• Include year-over-year comparisons in analysis
• Add benchmarking against industry averages
• Include sensitivity analysis for key metrics"""
    
    result = WorkspaceUtils.update_notes("User Preferences", updated_preferences)
    print(result)
    print()
    
    print("🎉 User Preferences Example completed successfully!")
    print("\n📋 Summary:")
    print("   ✅ Created notes.md file for storing preferences")
    print("   ✅ Set user preferences for analysis customization")
    print("   ✅ Updated preferences with additional requirements")
    print("   ✅ Demonstrated preference reading and updating")
    
    print("\n💡 Next Steps:")
    print("   - Use preferences to customize analysis approach")
    print("   - Update preferences based on analysis feedback")
    print("   - Apply preferences to ratio calculations and charting")
    print("   - Integrate preferences with other analysis workflows")

if __name__ == "__main__":
    main() 