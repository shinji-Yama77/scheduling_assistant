import asyncio
from dotenv import load_dotenv
import os
from azure.identity.aio import ClientSecretCredential
from azure.identity import DeviceCodeCredential, InteractiveBrowserCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.date_time_time_zone import DateTimeTimeZone
from msgraph.generated.models.event import Event
from msgraph.generated.models.item_body import ItemBody
from msgraph.generated.models.body_type import BodyType
from msgraph.generated.models.location import Location
from msgraph.generated.models.attendee import Attendee
from msgraph.generated.models.email_address import EmailAddress
from msgraph.generated.models.online_meeting_provider_type import OnlineMeetingProviderType
from msgraph.generated.users.users_request_builder import UsersRequestBuilder
from msgraph.generated.users.item.events.events_request_builder import EventsRequestBuilder
from kiota_abstractions.base_request_configuration import RequestConfiguration
from agents import function_tool
from datetime import datetime, timedelta
from pprint import pprint
import requests
from msal import PublicClientApplication

from pydantic import BaseModel, Field



class IntentParserOutput(BaseModel):
    """Class for structuring the output to parse the intent of a meeting through teams by using Microsoft Graph api"""
    subject: str = Field(description="Meeting subject/title")
    start_date_time: str = Field(description="Start time in ISO 8601 format")
    start_time_zone: str = Field(description="Microsoft Graph compatible windows time zone")
    end_date_time: str = Field(description="End time in ISO 8601 format")
    end_time_zone: str = Field(description="Microsoft Graph compatible windows time zone")
    attendees: list[str] = Field(description="List of attendee names")
    description: str = Field(description="Meeting description/body")
    location: str = Field(description="Meeting location")

# load environment variables from .env or set them directly here

load_dotenv()





# TENANT_ID = os.getenv("TENANT_ID")
# CLIENT_ID = os.getenv("CLIENT_ID")

# authority = f"https://login.microsoftonline.com/{TENANT_ID}"

# credentials = InteractiveBrowserCredential(
#     client_id=CLIENT_ID,
#     tenant_id=TENANT_ID,
#     redirect_uri="http://localhost:8400"
# )


# permissions that needs to be configured
# scopes = ["User.Read", "User.ReadBasic.All", "Calendars.Read"]
# client = GraphServiceClient(credentials=credentials, scopes=scopes)

# token = credentials.get_token("https://graph.microsoft.com/.default")
# access_token = token.token
# print(token)


# # get logged in user information
# async def me():
#     cred = InteractiveBrowserCredential(client_id=CLIENT_ID, tenant_id=TENANT_ID)
#     token = cred.get_token("https://graph.microsoft.com/.default")
#     print(token)
#     me = await client.me.get()
#     if me:
#         print(me.user_principal_name)
    
# # Fetch users
# async def list_users():
#     users = await client.users.get()
#     for user in users.value:
#         print(user.given_name, "-", user.user_principal_name)
        
# get user information
async def get_user_info():
    """Get current user information"""
    user = await me()
    return {
        "display_name": user.display_name,
        "email": user.mail or user.user_principal_name
    }

async def get_events():
    # query_params = EventsRequestBuilder.EventsRequestBuilderGetQueryParameters(
	# 	select = ["subject","body","bodyPreview","organizer","attendees","start","end","location"],
    # )

    # request_configuration = RequestConfiguration(
    # query_parameters = query_params,
    # )
    headers = {
    "Authorization": f"Bearer {access_token}"
    }
    response = requests.get("https://graph.microsoft.com/v1.0/me/calendars", headers=headers)
    print(response.status_code)


# resolves the user's email based on the givenName
async def resolve_email_by_name(client: GraphServiceClient, name: str):
    try:
        query_params = UsersRequestBuilder.UsersRequestBuilderGetQueryParameters(
            filter=f"startswith(givenName, '{name}') eq true",
        )
        request_configuration = RequestConfiguration(query_parameters=query_params)
        result = await client.users.get(request_configuration=request_configuration)

        if result.value and len(result.value) > 0:
            user = result.value[0]
            return user.mail or user.user_principal_name
        else:
            print("No match found")
            return None
    except Exception as e:
        print(f"error searching for '{name}'")
        return None

# resolves a list of user's names based on the structured output
async def resolve_emails_by_names(client: GraphServiceClient, names: list[str]):
    tasks =[resolve_email_by_name(client, name) for name in names]
    results = await asyncio.gather(*tasks)
    return [email for email in results if email]

# schedules a meeting
async def schedule_meeting(client: GraphServiceClient, details: IntentParserOutput):
    """
    Schedule a meeting using Microsoft Graph API
    
    Args:
        subject (str): Meeting subject
        start_date_time (str): Start time in ISO 8601 format
        start_time_zone (str): Microsoft Graph compatible time zone
        end_date_time (str): End time in ISO 8601 format
        end_time_zone (str): Microsoft Graph compatible time zone
        attendees (list, optional): List of attendee email addresses
        description (str, optional): Meeting description
        location (str, optional): Meeting location
        
    Returns:
        dict: Created event details
    """

    # extract fields from the structured output
    subject = details.subject
    start_date_time = details.start_date_time
    start_time_zone = details.start_time_zone
    end_date_time = details.end_date_time
    end_time_zone = details.end_time_zone
    attendees = details.attendees
    description = details.description
    location = details.location

    # Resolve attendee names → emails
    resolved_emails = await resolve_emails_by_names(client, attendees or [])

    # Build the event
    event = Event(subject=subject)

    if description:
        event.body = ItemBody(content=description, content_type=BodyType.Text)

    event.start = DateTimeTimeZone(date_time=start_date_time, time_zone=start_time_zone)
    event.end = DateTimeTimeZone(date_time=end_date_time, time_zone=end_time_zone)

    if location:
        event.location = Location(display_name=location)

    if resolved_emails:
        event.attendees = [
            Attendee(email_address=EmailAddress(address=email)) for email in resolved_emails
        ]

    event.allow_new_time_proposals = True
    event.is_online_meeting = True
    event.online_meeting_provider = OnlineMeetingProviderType.TeamsForBusiness

    # Call Graph API
    created_event = await client.me.events.post(event)

    return {
        "id": created_event.id,
        "subject": created_event.subject,
        "start": created_event.start.date_time,
        "end": created_event.end.date_time,
        "web_link": created_event.web_link
    }


# For testing the module directly
if __name__ == "__main__":
    names = ["alice", "shinji"]
    # #asyncio.run(list_users())
    # emails = asyncio.run(resolve_emails_by_names(client, names))
    # for name, email in zip(names, emails):
    #     print(f"{name} → {email}")

    # TENANT_ID = os.getenv("TENANT_ID")
    # CLIENT_ID = os.getenv("CLIENT_ID")

    # credentials = InteractiveBrowserCredential(
    #     client_id=CLIENT_ID,
    #     tenant_id=TENANT_ID
    # )

    # # token = await credentials.get_token("https://graph.microsoft.com/.default")
    # # print("\n🔐 ACCESS TOKEN:")
    # # print(token.token)      

    # # permissions that needs to be configured
    # scopes = ["User.Read", "User.Read.All", "Calendars.ReadWrite", "User.ReadBasic.All", "VirtualAppointment.ReadWrite", "OnlineMeetings.ReadWrite"]
    # client = GraphServiceClient(credentials=credentials, scopes=scopes)

    asyncio.run(get_events())

    

    
