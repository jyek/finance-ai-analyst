#!/usr/bin/env python3
"""Test configuration loading"""

from config import get_config

def main():
    config = get_config("config.json")
    
    print("Configuration test:")
    print(f"OpenAI API Key: {'✅ Set' if config.openai_api_key else '❌ Missing'}")
    print(f"OAuth Credentials: {'✅ Set' if config.google_oauth_credentials_json else '❌ Missing'}")
    
    if config.google_oauth_credentials_json:
        print(f"OAuth Credentials type: {type(config.google_oauth_credentials_json)}")
        print(f"OAuth Credentials content: {config.google_oauth_credentials_json}")
    
    # Check environment variable
    import os
    env_creds = os.environ.get("GOOGLE_OAUTH_CREDENTIALS_JSON")
    print(f"Environment variable: {'✅ Set' if env_creds else '❌ Missing'}")
    if env_creds:
        print(f"Env var type: {type(env_creds)}")
        print(f"Env var content: {env_creds}")

if __name__ == "__main__":
    main() 