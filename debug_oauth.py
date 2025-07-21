#!/usr/bin/env python3
"""Debug OAuth credentials loading"""

import os
import sys

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_config_loading():
    print("Testing config loading...")
    
    # Test 1: Direct config import
    try:
        from config import get_config
        config = get_config("config.json")
        print(f"✅ Config loaded successfully")
        print(f"OAuth credentials: {'✅ Set' if config.google_oauth_credentials_json else '❌ Missing'}")
        if config.google_oauth_credentials_json:
            print(f"Type: {type(config.google_oauth_credentials_json)}")
            print(f"Keys: {list(config.google_oauth_credentials_json.keys())}")
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
    
    # Test 2: Environment variable
    env_creds = os.environ.get("GOOGLE_OAUTH_CREDENTIALS_JSON")
    print(f"\nEnvironment variable: {'✅ Set' if env_creds else '❌ Missing'}")
    if env_creds:
        print(f"Type: {type(env_creds)}")
        print(f"Content: {env_creds[:100]}...")
    
    # Test 3: Simulate tool loading
    print("\nSimulating tool loading...")
    try:
        from config import get_config
        config = get_config("config.json")  # Explicitly load config file
        oauth_credentials_json = config.google_oauth_credentials_json
        print(f"Tool config loading: {'✅ Success' if oauth_credentials_json else '❌ Failed'}")
        if oauth_credentials_json:
            print(f"Tool credentials type: {type(oauth_credentials_json)}")
    except Exception as e:
        print(f"❌ Tool config loading failed: {e}")

if __name__ == "__main__":
    test_config_loading() 