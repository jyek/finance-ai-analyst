#!/usr/bin/env python3
"""
Configuration Setup Script

This script helps you set up your configuration file with API keys and settings.
"""

import os
import json
from config import get_config

def setup_config():
    """Interactive configuration setup"""
    print("🔧 Finance Workspace Agent - Configuration Setup")
    print("=" * 50)
    
    config_data = {}
    
    print("\n📝 Please provide your API keys and configuration:")
    
    # OpenAI API Key
    openai_key = input("\n🔑 OpenAI API Key (or press Enter to skip): ").strip()
    if openai_key:
        config_data["OPENAI_API_KEY"] = openai_key
    
    # Google Workspace Credentials JSON
    workspace_creds = input("\n🔐 Google Workspace Credentials JSON (or press Enter to skip): ").strip()
    if workspace_creds:
        config_data["GOOGLE_WORKSPACE_CREDENTIALS_JSON"] = workspace_creds
    
    # LLM Configuration
    print("\n🤖 LLM Configuration:")
    model = input("   Model (default: gpt-4): ").strip() or "gpt-4"
    temperature = input("   Temperature (default: 0.1): ").strip() or "0.1"
    timeout = input("   Timeout (default: 120): ").strip() or "120"
    
    config_data.update({
        "LLM_MODEL": model,
        "LLM_TEMPERATURE": float(temperature),
        "LLM_TIMEOUT": int(timeout)
    })
    
    # Save configuration
    if config_data:
        config_file = "config.json"
        
        # Check if file already exists
        if os.path.exists(config_file):
            overwrite = input(f"\n⚠️ {config_file} already exists. Overwrite? (y/N): ").strip().lower()
            if overwrite != 'y':
                print("❌ Configuration setup cancelled.")
                return
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            print(f"\n✅ Configuration saved to {config_file}")
            
            # Test the configuration
            print("\n🧪 Testing configuration...")
            test_config = get_config(config_file)
            test_config.print_status()
            
            if test_config.validate():
                print("\n🎉 Configuration is valid and ready to use!")
            else:
                print("\n⚠️ Configuration is missing some required values.")
                
        except Exception as e:
            print(f"\n❌ Error saving configuration: {e}")
    else:
        print("\n❌ No configuration provided.")

def check_current_config():
    """Check current configuration status"""
    print("🔍 Current Configuration Status:")
    print("=" * 40)
    
    config = get_config()
    config.print_status()
    
    if config.validate():
        print("\n✅ Configuration is valid!")
    else:
        print("\n❌ Configuration is missing required values.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        check_current_config()
    else:
        setup_config() 