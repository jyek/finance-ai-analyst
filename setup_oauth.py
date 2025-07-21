#!/usr/bin/env python3
"""
OAuth2 Setup Script for Finance AI Analyst

This script helps you set up Google OAuth2 credentials for the Finance AI Analyst.
It will guide you through the process of creating OAuth2 credentials and testing them.
"""

import os
import json
import webbrowser
from pathlib import Path

def print_header():
    """Print the setup header"""
    print("🔐 Finance AI Analyst - OAuth2 Setup")
    print("=" * 50)
    print("This script will help you set up Google OAuth2 credentials.")
    print("You'll need to create OAuth2 credentials in Google Cloud Console.\n")

def get_oauth_credentials():
    """Get OAuth2 credentials from user input"""
    print("📋 Please provide your OAuth2 credentials:")
    print("(You can get these from Google Cloud Console > Credentials > OAuth 2.0 Client IDs)")
    print()
    
    client_id = input("Client ID: ").strip()
    if not client_id:
        print("❌ Client ID is required")
        return None
    
    project_id = input("Project ID: ").strip()
    if not project_id:
        print("❌ Project ID is required")
        return None
    
    client_secret = input("Client Secret: ").strip()
    if not client_secret:
        print("❌ Client Secret is required")
        return None
    
    return {
        "installed": {
            "client_id": client_id,
            "project_id": project_id,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": client_secret,
            "redirect_uris": ["http://localhost"]
        }
    }

def save_config(oauth_creds, openai_key=None):
    """Save configuration to config.json"""
    config = {
        "OPENAI_API_KEY": openai_key or "your-openai-api-key-here",
        "GOOGLE_OAUTH_CREDENTIALS_JSON": oauth_creds,
        "LLM_MODEL": "gpt-4",
        "LLM_TEMPERATURE": 0.1,
        "LLM_TIMEOUT": 120
    }
    
    config_path = Path("config.json")
    
    # Check if config already exists
    if config_path.exists():
        overwrite = input(f"\n⚠️  {config_path} already exists. Overwrite? (y/N): ").strip().lower()
        if overwrite != 'y':
            print("❌ Setup cancelled")
            return False
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✅ Configuration saved to {config_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to save configuration: {e}")
        return False

def test_oauth_credentials():
    """Test the OAuth2 credentials"""
    print("\n🧪 Testing OAuth2 credentials...")
    
    try:
        from config import get_config
        config = get_config("config.json")
        
        if not config.validate():
            print("❌ Configuration validation failed")
            return False
        
        print("✅ Configuration is valid!")
        
        # Try to initialize Google Workspace
        print("🔐 Testing Google Workspace connection...")
        from tools.workspace import WorkspaceUtils
        
        # This will trigger OAuth2 flow if needed
        result = WorkspaceUtils.list_my_sheets(1)
        
        if result:
            print("✅ Google Workspace connection successful!")
            print("🎉 OAuth2 setup is complete!")
            return True
        else:
            print("❌ Failed to connect to Google Workspace")
            return False
            
    except Exception as e:
        print(f"❌ Error testing credentials: {e}")
        return False

def print_instructions():
    """Print setup instructions"""
    print("\n📖 OAuth2 Setup Instructions:")
    print("=" * 40)
    print("1. Go to Google Cloud Console: https://console.cloud.google.com/")
    print("2. Create a new project or select an existing one")
    print("3. Enable these APIs:")
    print("   - Google Sheets API")
    print("   - Google Docs API")
    print("   - Google Drive API")
    print("4. Go to 'Credentials' → 'Create Credentials' → 'OAuth 2.0 Client IDs'")
    print("5. Choose 'Desktop application' as the application type")
    print("6. Download the JSON file")
    print("7. Use the values from the JSON file in this setup\n")

def main():
    """Main setup function"""
    print_header()
    
    # Check if user wants instructions
    show_instructions = input("Would you like to see OAuth2 setup instructions? (Y/n): ").strip().lower()
    if show_instructions != 'n':
        print_instructions()
    
    # Get OpenAI API key
    print("🔑 OpenAI API Key Setup:")
    openai_key = input("Enter your OpenAI API key (or press Enter to skip for now): ").strip()
    if not openai_key:
        openai_key = "your-openai-api-key-here"
        print("⚠️  You'll need to add your OpenAI API key later")
    
    # Get OAuth2 credentials
    oauth_creds = get_oauth_credentials()
    if not oauth_creds:
        print("❌ Setup cancelled")
        return
    
    # Save configuration
    if not save_config(oauth_creds, openai_key):
        return
    
    # Test credentials
    test_credentials = input("\nWould you like to test the OAuth2 credentials now? (Y/n): ").strip().lower()
    if test_credentials != 'n':
        test_oauth_credentials()
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Add your OpenAI API key to config.json if you haven't already")
    print("2. Run the example: python examples/basic_usage.py")
    print("3. The first time you run it, you'll be prompted to authenticate with Google")

if __name__ == "__main__":
    main() 