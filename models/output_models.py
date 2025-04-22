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
