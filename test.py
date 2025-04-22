import asyncio
import requests
import time
import threading
from server.autho_code_server import run_server, get_auth_code
from azure.identity import AuthorizationCodeCredential
from msgraph import GraphServiceClient
import os
from dotenv import load_dotenv
from models import IntentParserOutput

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
TENANT_ID = "common"
SCOPES = ["User.Read"]
REDIRECT_URI = "http://localhost:8000/callback"
AUTHORITY = f"https://login.microsoftonline.com/common"




async def wait_for_auth_code(timeout=120):
    print("🔁 Waiting for user to authenticate and for code to arrive...")

    start_time = time.time()
    while True:
        code = get_auth_code()
        if code:
            print("✅ Received auth code!")
            return code
        if time.time() - start_time > timeout:
            raise TimeoutError("❌ Timed out waiting for auth code.")
        await asyncio.sleep(2)

async def main():
    # Run the Flask server in a background thread
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()

    # Trigger the auth URL
    requests.get("http://localhost:8000")

    # Wait for the user to log in and capture the code
    code = await wait_for_auth_code()
    
    credential = AuthorizationCodeCredential(
        client_id=CLIENT_ID,
        tenant_id=TENANT_ID,
        authorization_code=code,
        redirect_uri=REDIRECT_URI
    )
    
    client = GraphServiceClient(credentials=credential, scopes=SCOPES)
    results = await client.me.events.get()
    return results

if __name__ == "__main__":
    print(asyncio.run(main()))