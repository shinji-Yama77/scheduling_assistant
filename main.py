from agents import set_default_openai_key, Agent, Runner, RunContextWrapper, handoff, ItemHelpers
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from dataclasses import dataclass
from typing import Optional
import os
import asyncio
import sys
from rich.console import Console
from rich.panel import Panel
from rich import print as rprint
from datetime import datetime
from utils import schedule_meeting, get_user_info
import time
import threading
from server.autho_code_server import run_server, get_auth_code
from azure.identity import AuthorizationCodeCredential
from msgraph import GraphServiceClient
from test import wait_for_auth_code
import requests



load_dotenv()


api_key = os.getenv("OPENAI_KEY")
set_default_openai_key(api_key)
CLIENT_ID = os.getenv("CLIENT_ID")
TENANT_ID = "common"
SCOPES = ["User.Read"]
REDIRECT_URI = "http://localhost:8000/callback"
AUTHORITY = f"https://login.microsoftonline.com/common"


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


class ScheduleMeetingOutput(BaseModel):
    """Class for structuring the meeting event output created"""
    id: str
    subject: str
    start: str = Field(description="ISO 8601 start time")
    end: str = Field(description="ISO 8601 end time")
    web_link: Optional[str] = Field(description="Link to join the meeting")
    
class CurrentTime(BaseModel):
    current_time: str 


def dynamic_instructions(
        context: RunContextWrapper[CurrentTime], agent: Agent[CurrentTime]) -> str:
    now = context.context.current_time
    return f"""
    The current time is {now}.

    You are a helpful scheduling assistant that creates meetings in the future in Outlook calendars.
    Always use current or future dates (never before today).

    Extract the meeting details from the user's request, including:
    1. Meeting subject/title
    2. Start date and time
    3. End date and time
    4. Time zone
    5. Meeting attendees (if specified)
    6. Meeting location (if specified)
    7. Meeting description (if specified)

    Convert dates and times to ISO 8601 format (YYYY-MM-DDThh:mm:ss).
    For time zones, use Microsoft Graph compatible Windows time zones like:
    - Pacific Standard Time
    - Eastern Standard Time
    - UTC

    If time zone is not specified, default to "Pacific Standard Time".
    If a meeting description is not provided, leave it empty. If the user wants to schedule a meeting, handoff to the scheduling agent 
    """

Scheduler_Agent = Agent(
    name="Scheduling Agent",
    instructions="Call the neccessary tools to schedule a meeting",
    tools=[
        schedule_meeting
    ]
)


IntentParser_Agent = Agent[CurrentTime](
    name="Intent Parser Agent",
    instructions=dynamic_instructions,
    output_type=IntentParserOutput
)


async def process_user_request(user_input):
    """Process the user's natural language request using the agentic framework"""
    console = Console()
    
    with console.status("[bold green]Processing your request..."):
        # Run the agent to understand the request
        context_obj = CurrentTime(current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        result = await Runner.run(starting_agent=IntentParser_Agent, 
                                  input=user_input,
                                  context=context_obj)
        meeting_details = result.final_output_as(IntentParserOutput)

        
    # # Show the extracted meeting details
    # console.print("\n[bold]Meeting Details Extracted:[/bold]")
    # console.print(f"Subject: {meeting_details.subject}")
    # console.print(f"Start: {meeting_details.start_date_time} ({meeting_details.start_time_zone})")
    # console.print(f"End: {meeting_details.end_date_time} ({meeting_details.end_time_zone})")
    
    # if meeting_details.attendees:
    #     console.print(f"Attendees: {', '.join(meeting_details.attendees)}")
    # if meeting_details.location:
    #     console.print(f"Location: {meeting_details.location}")
    # if meeting_details.description:
    #     console.print(f"Description: {meeting_details.description}")
    
    # # Confirm before scheduling
    # console.print("\nDo you want to schedule this meeting? [y/n]: ", end="")
    # response = input().lower()
    
    # if response != 'y':
    #     console.print("[yellow]Meeting scheduling cancelled.[/yellow]")
    #     return
    
    # # Schedule the meeting using Microsoft Graph
    # with console.status("[bold green]Scheduling the meeting..."):
    #     try:
    #         # Get user info
    #         user_info = await graph.get_user_info()
    #         console.print(f"\nScheduling as: {user_info['display_name']} ({user_info['email']})")
            
    #         # Schedule meeting
    #         event = await graph.schedule_meeting(
    #             subject=meeting_details.subject,
    #             start_date_time=meeting_details.start_date_time,
    #             start_time_zone=meeting_details.start_time_zone,
    #             end_date_time=meeting_details.end_date_time,
    #             end_time_zone=meeting_details.end_time_zone,
    #             attendees=meeting_details.attendees,
    #             description=meeting_details.description,
    #             location=meeting_details.location
    #         )
            
    #         # Success message
    #         console.print(Panel.fit(
    #             f"[bold green]✓ Meeting scheduled successfully![/bold green]\n\n"
    #             f"[bold]Subject:[/bold] {event['subject']}\n"
    #             f"[bold]When:[/bold] {event['start']} to {event['end']}\n"
    #             f"[bold]Link:[/bold] {event['web_link']}",
    #             title="Meeting Scheduled",
    #             border_style="green"
    #         ))
            
    #     except Exception as e:
    #         console.print(f"[bold red]Error scheduling meeting:[/bold red] {str(e)}")


def show_help():
    """Show help information about the assistant capabilities"""
    rprint(Panel.fit(
        "[bold]Scheduling Assistant Capabilities:[/bold]\n\n"
        "This AI assistant can understand natural language requests to schedule meetings.\n\n"
        "[bold]Examples of what you can say:[/bold]\n"
        "- \"Schedule a team meeting tomorrow at 2pm\"\n"
        "- \"Create a product review with marketing team on Friday from 10-11am\"\n"
        "- \"Set up a 1:1 with John (john@example.com) next Monday at 3pm in Conference Room A\"\n"
        "- \"Schedule a weekly standup every Monday at 9am starting next week\"\n\n"
        "[bold]The assistant will extract:[/bold]\n"
        "- Meeting subject/title\n"
        "- Start and end times\n"
        "- Attendee email addresses\n"
        "- Location (if specified)\n"
        "- Description/agenda (if specified)\n\n"
        "[bold]Commands:[/bold]\n"
        "- Type 'help' to see this information again\n"
        "- Type 'exit' to quit the application",
        title="AI Meeting Scheduling Assistant",
        border_style="blue"
    ))


# async def authenticate_user():
#     """Authenticate the user with Microsoft Graph API"""
#     console = Console()
    
#     console.print(Panel.fit(
#         "This application requires access to your Microsoft account to schedule meetings.\n"
#         "A browser window will open for you to sign in.",
#         title="Authentication Required",
#         border_style="yellow"
#     ))
    
#     try:
#         with console.status("[bold yellow]Authenticating with Microsoft Graph..."):
#             # This will trigger the browser authentication flow
#             user_info = await get_user_info()
        
#         console.print(Panel.fit(
#             f"Successfully authenticated as:\n[bold]{user_info['display_name']}[/bold] ({user_info['email']})",
#             title="Authentication Successful",
#             border_style="green"
#         ))
#         return True
#     except Exception as e:
#         console.print(Panel.fit(
#             f"Authentication failed: {str(e)}\n\nPlease restart the application and try again.",
#             title="Authentication Error",
#             border_style="red"
#         ))
#         return False


# async def main():
#     """Main application function"""
#     console = Console()
    
#     # First ensure user is authenticated
#     is_authenticated = await authenticate_user()
#     if not is_authenticated:
#         return
    
#     # Show welcome message
#     rprint(Panel.fit(
#         "This AI assistant can help schedule meetings using natural language.\n"
#         "Simply describe the meeting you want to schedule, and the assistant will do the rest.\n"
#         "Type 'help' to see example commands or 'exit' to quit.",
#         title="Meeting Scheduling Assistant",
#         border_style="green"
#     ))
    
#     # Interactive session
#     while True:
#         console.print("\n[bold blue]What can I help you schedule? >[/bold blue] ", end="")
#         user_input = input()
        
#         if not user_input.strip():
#             continue
        
#         if user_input.lower() == "exit":
#             console.print("[yellow]Thank you for using the Meeting Scheduling Assistant. Goodbye![/yellow]")
#             break
#         elif user_input.lower() == "help":
#             show_help()
#         else:
#             # Process the user's request using the agent
#             return await process_user_request(user_input)

async def test():
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

    context_obj = CurrentTime(current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    result = await Runner.run(starting_agent=IntentParser_Agent, 
                              input="I want to schedule a meeting next thursday 12PM to 12:30PM pst with alice about Japanese tutoring class",
                              context=context_obj)
    meeting_details = result.final_output
    
    return await schedule_meeting(client, meeting_details)


    


if __name__ == "__main__":

    print(asyncio.run(test()))

    # try:
    #     asyncio.run(main())
    # except KeyboardInterrupt:
    #     print("\nExiting...")
    #     sys.exit(0)

