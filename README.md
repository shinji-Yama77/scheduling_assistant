# scheduling_assistant
Teams Scheduling Assistant

## Overview
The Teams Scheduling Assistant is a Python-based application designed to streamline the process of scheduling meetings. It leverages the OpenAI Agent SDK to extract intent from user inputs and utilizes the Agentic Framework to interact with Microsoft Outlook via the Microsoft Graph API. The assistant automates the creation of meetings with other users, making scheduling efficient and seamless.

### Key Features
- **Intent Extraction**: Uses OpenAI Agent SDK to understand user requests and extract scheduling-related intents.
- **Microsoft Graph Integration**: Accesses Outlook calendars and contacts to retrieve availability and schedule meetings.
- **Automated Meeting Creation**: Creates and sends meeting invitations programmatically using Python.
- **Agentic Framework**: Provides a structured approach to managing interactions with external APIs.

## High-Level Architecture
```mermaid
graph TD
    UserInput["User Input (Natural Language)"]
    OpenAIAgent["OpenAI Agent SDK (Intent Extraction)"]
    AgenticFramework["Agentic Framework"]
    MicrosoftGraph["Microsoft Graph API"]
    Outlook["Outlook (Calendar & Contacts)"]
    MeetingCreation["Meeting Creation (Python)"]

    UserInput --> OpenAIAgent
    OpenAIAgent --> AgenticFramework
    AgenticFramework --> MicrosoftGraph
    MicrosoftGraph --> Outlook
    AgenticFramework --> MeetingCreation
    MeetingCreation --> MicrosoftGraph