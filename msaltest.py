from msal import PublicClientApplication
from dotenv import load_dotenv
import os
import requests
import asyncio
from azure.core.credentials import AccessToken
from datetime import datetime, timedelta
from msgraph import GraphServiceClient
from azure.identity import AuthorizationCodeCredential
from azure.identity import DeviceCodeCredential, InteractiveBrowserCredential
import webbrowser
load_dotenv()

class MSALCredentialShim:
    def __init__(self, access_token: str, expires_in: int = 3600):
        # Store the access token
        self._access_token = access_token

        # Set when the token expires (current time + 1 hour by default)
        self._expires_on = datetime.utcnow() + timedelta(seconds=expires_in)

    def get_token(self, *scopes):
        # Return an Azure-compatible AccessToken object
        return AccessToken(
            self._access_token,
            int(self._expires_on.timestamp())  # expires_on needs to be a UNIX timestamp
        )


TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
scopes = ["User.Read", "Calendars.Read"]

authority = f"https://login.microsoftonline.com/{TENANT_ID}"

client_instance = PublicClientApplication(
    client_id=CLIENT_ID,
    authority=authority
)

# authorization_request_url = client_instance.get_authorization_request_url(scopes)
# print(authorization_request_url)
# webbrowser.open(authorization_request_url, new=True)

credentials = DeviceCodeCredential(
    client_id=CLIENT_ID,
    TENANT_ID=TENANT_ID,
    redirect_uri="http://localhost:8400"
)


# credentials = InteractiveBrowserCredential(
#     client_id=CLIENT_ID,
#     tenant_id=TENANT_ID,
#     redirect_uri="http://localhost:8400"
# )


# credential = AuthorizationCodeCredential(
#     tenant_id=TENANT_ID,
#     client_id=CLIENT_ID,
#     authorization_code=authorization_code,
#     redirect_uri="http://localhost:8400"
# )


# result = app.acquire_token_interactive(scopes=scopes)
# access_token = result["access_token"]
# # cred = MSALCredentialShim(access_token)
# headers = {
#     "Authorization": f"Bearer {access_token}",
#     "Content-Type": "application/json"
# }



# response = requests.get("https://graph.microsoft.com/v1.0/me/events", headers=headers)
client = GraphServiceClient(credentials=credentials, scopes=scopes)

async def get_user():
     me = await client.me.get()
     if me:
        print(me.user_principal_name)



async def get_events():
    results = await client.me.calendar.get()
    print(results)

asyncio.run(get_user())



