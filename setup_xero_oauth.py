"""
Setup script for Xero OAuth authentication.
"""

import json
import webbrowser
import http.server
import socketserver
import urllib.parse
from urllib.parse import urlparse, parse_qs
import requests
from connectors.xero_connector import XeroConnector


class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    """HTTP server to handle OAuth callback."""
    
    def __init__(self, *args, **kwargs):
        self.auth_code = None
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET request from OAuth callback."""
        # Parse the authorization code from the callback URL
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        
        if 'code' in query_params:
            self.auth_code = query_params['code'][0]
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            response = """
            <html>
            <body>
                <h2>Authentication Successful!</h2>
                <p>You can close this window and return to the terminal.</p>
            </body>
            </html>
            """
            self.wfile.write(response.encode())
        else:
            # Send error response
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            response = """
            <html>
            <body>
                <h2>Authentication Failed!</h2>
                <p>Please try again.</p>
            </body>
            </html>
            """
            self.wfile.write(response.encode())


def setup_xero_oauth():
    """Set up Xero OAuth authentication."""
    
    # Load configuration
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("config.json not found. Please create it first.")
        return False
    
    xero_config = config.get('xero', {})
    if not xero_config:
        print("Xero configuration not found in config.json")
        return False
    
    client_id = xero_config.get('client_id')
    client_secret = xero_config.get('client_secret')
    redirect_uri = xero_config.get('redirect_uri', 'http://localhost:8080/callback')
    
    if not client_id or not client_secret:
        print("Missing Xero client_id or client_secret in config.json")
        return False
    
    # Step 1: Generate authorization URL
    auth_url = (
        "https://login.xero.com/identity/connect/authorize?"
        f"response_type=code&"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        "scope=offline_access accounting.transactions accounting.settings accounting.contacts"
    )
    
    print("Opening browser for Xero authentication...")
    print(f"Authorization URL: {auth_url}")
    
    # Open browser for user to authorize
    webbrowser.open(auth_url)
    
    # Step 2: Start local server to receive callback
    print("Starting local server to receive callback...")
    
    # Create a custom handler that can store the auth code
    handler = type('CustomHandler', (OAuthCallbackHandler,), {})
    handler.auth_code = None
    
    with socketserver.TCPServer(("", 8080), handler) as httpd:
        print("Waiting for OAuth callback...")
        httpd.handle_request()  # Handle one request then stop
    
    auth_code = handler.auth_code
    if not auth_code:
        print("Failed to receive authorization code")
        return False
    
    # Step 3: Exchange authorization code for access token
    print("Exchanging authorization code for access token...")
    
    token_url = "https://identity.xero.com/connect/token"
    token_data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    try:
        response = requests.post(token_url, data=token_data)
        response.raise_for_status()
        
        token_response = response.json()
        
        # Add expiration timestamp
        import time
        token_response["expires_at"] = time.time() + token_response.get("expires_in", 1800)
        
        # Save token to file
        with open("xero_token.json", "w") as f:
            json.dump(token_response, f, indent=2)
        
        print("✅ Xero OAuth setup completed successfully!")
        print(f"Access token expires at: {token_response.get('expires_at')}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"Failed to exchange authorization code: {e}")
        return False


if __name__ == "__main__":
    setup_xero_oauth() 