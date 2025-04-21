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


# load environment variables from .env or set them directly here

load_dotenv()

TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")

credentials = InteractiveBrowserCredential(
    client_id=CLIENT_ID,
    tenant_id=TENANT_ID
)


scopes = ["User.Read", "User.Read.All", "Calendars.ReadWrite"]
client = GraphServiceClient(credentials=credentials, scopes=scopes)


async def me():
    me = await client.me.get()
    if me:
        return me
    
# Fetch users
async def list_users():
    users = await client.users.get()
    for user in users.value:
        print(user.display_name, "-", user.user_principal_name)
        
async def get_user_info():
    """Get current user information"""
    user = await me()
    return {
        "display_name": user.display_name,
        "email": user.mail or user.user_principal_name
    }

async def schedule_meeting(subject, start_date_time, start_time_zone, 
                          end_date_time, end_time_zone, 
                          attendees=None, description=None, location=None):
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
    # Create event object
    event = Event()
    event.subject = subject
    
    # Set body/description
    if description:
        body = ItemBody()
        body.content = description
        body.content_type = BodyType.TEXT
        event.body = body
    
    # Set start and end times
    start = DateTimeTimeZone()
    start.date_time = start_date_time
    start.time_zone = start_time_zone
    event.start = start
    
    end = DateTimeTimeZone()
    end.date_time = end_date_time
    end.time_zone = end_time_zone
    event.end = end
    
    # Set location if provided
    if location:
        event_location = Location()
        event_location.display_name = location
        event.location = event_location
    
    # Add attendees if provided
    if attendees:
        event.attendees = []
        for email in attendees:
            attendee = Attendee()
            email_address = EmailAddress()
            email_address.address = email
            attendee.email_address = email_address
            event.attendees.append(attendee)
    
    # Create the event
    created_event = await client.me.events.post(event)
    
    # Return event details
    return {
        "id": created_event.id,
        "subject": created_event.subject,
        "start": created_event.start.date_time,
        "end": created_event.end.date_time,
        "web_link": created_event.web_link
    }

# For testing the module directly
if __name__ == "__main__":

    asyncio.run(list_users())