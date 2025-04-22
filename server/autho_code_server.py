import os
from flask import Flask, request
from msal import PublicClientApplication
from dotenv import load_dotenv
import webbrowser
from azure.identity import AuthorizationCodeCredential
from msgraph import GraphServiceClient

load_dotenv()

app = Flask(__name__)

CLIENT_ID = os.getenv("CLIENT_ID")
TENANT_ID = os.getenv("TENANT_ID")
SCOPES = ["User.Read"]
REDIRECT_URI = "http://localhost:8000/callback"
AUTHORITY = f"https://login.microsoftonline.com/common"
# Shared variable to store the code
auth_code_holder = {"code": None}

# Create MSAL client
msal_app = PublicClientApplication(client_id=CLIENT_ID, authority=AUTHORITY)

# Step 1: Generate auth URL and open in browser
@app.route("/")
def auth():
    auth_url = msal_app.get_authorization_request_url(SCOPES, redirect_uri=REDIRECT_URI)
    webbrowser.open(auth_url)
    return "Opening Microsoft login page..."



@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "Authorization code not found."
    
    # Store the code globally
    auth_code_holder["code"] = code
    return "✅ Authorization complete! You may return to your app."

def get_auth_code():
    return auth_code_holder["code"]

def run_server():
    app.run(port=8000)

if __name__ == "__main__":
    app.run(port=8000)