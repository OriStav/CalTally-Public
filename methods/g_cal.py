#%%
import datetime
import os.path
import pandas as pd
import streamlit as st
from proj_consts import paths
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

def get_calendar_events(start_date: datetime.date, end_date: datetime.date,
                        calendar_id: str = 'primary', refresh: bool = False):
    """
    Fetches calendar events with caching support. Checks cache first, then downloads if needed.
    
    Args:
        start_date (datetime.date): The start date for fetching events (inclusive).
        end_date (datetime.date): The end date for fetching events (inclusive).
        calendar_id (str): The ID of the calendar to query. Use 'primary' for the user's default calendar.
    
    Returns:
        pd.DataFrame: DataFrame containing calendar events for the specified date range.
    """

    cache_file = paths.cache_file
    cache_max_age_hours = 24  # Cache expires after 24 hours
    
    # Ensure cache directory exists
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    
    # Load existing cache
    cached_events = pd.DataFrame()
    if os.path.exists(cache_file) and not refresh:
        try:
            cached_events = pd.read_csv(cache_file)
            if not cached_events.empty:
                # Convert date columns back to datetime
                cached_events['start'] = pd.to_datetime(cached_events['start'])
                cached_events['end'] = pd.to_datetime(cached_events['end'])
                cached_events['cache_timestamp'] = pd.to_datetime(cached_events['cache_timestamp'])
        except Exception as e:
            print(f"Error loading cache: {e}")
            cached_events = pd.DataFrame()
    
    # Check if we have cached data for this calendar and date range
    if not cached_events.empty:
        # Filter for this calendar
        calendar_cache = cached_events[cached_events['calendar_id'] == calendar_id].copy()
        
        if not calendar_cache.empty:
            # Check cache age
            latest_cache_time = calendar_cache['cache_timestamp'].max()
            cache_age = datetime.datetime.now() - latest_cache_time
            
            if cache_age.total_seconds() < cache_max_age_hours * 3600:  # Cache is still fresh
                # Check if requested date range is fully covered by cache
                cache_start = calendar_cache['start'].min().date()
                cache_end = calendar_cache['end'].max().date()
                ## TODO: fix this
                temp_cond = 1
                # st.write(cache_start, cache_end)
                # st.write(start_date, end_date)

                if temp_cond: #start_date >= cache_start and end_date <= cache_end:
                    # Requested range is fully covered by cache
                    # Convert to date for comparison
                    calendar_cache_start_dates = calendar_cache['start'].dt.date
                    calendar_cache_end_dates = calendar_cache['end'].dt.date
                    mask = (calendar_cache_start_dates >= start_date) & (calendar_cache_end_dates <= end_date)
                    result = calendar_cache[mask].copy()
                    if not result.empty:
                        print(f"Using cached data for {calendar_id} ({start_date} to {end_date})")
                        # Remove cache-specific columns before returning
                        result = result.drop(['cache_timestamp', 'calendar_id'], axis=1)
                        return result
    
    # Cache miss or stale - need to download data
    print(f"Downloading fresh data for {calendar_id} ({start_date} to {end_date})")
    new_events = download_calendar_events(start_date, end_date, calendar_id)
    
    if not new_events.empty:
        # Add cache metadata
        new_events['cache_timestamp'] = datetime.datetime.now()
        new_events['calendar_id'] = calendar_id
        
        # Merge with existing cache
        if not cached_events.empty:
            # Remove any overlapping data for this calendar and date range
            other_calendars = cached_events[cached_events['calendar_id'] != calendar_id]
            same_calendar = cached_events[cached_events['calendar_id'] == calendar_id]
            
            # Remove overlapping date ranges for this calendar
            if not same_calendar.empty:
                same_calendar_start_dates = same_calendar['start'].dt.date
                same_calendar_end_dates = same_calendar['end'].dt.date
                overlap_mask = ~((same_calendar_start_dates >= start_date) & (same_calendar_end_dates <= end_date))
                non_overlapping = same_calendar[overlap_mask]
                
                # Combine non-overlapping cached data with new data
                updated_cache = pd.concat([other_calendars, non_overlapping, new_events], ignore_index=True)
            else:
                updated_cache = pd.concat([cached_events, new_events], ignore_index=True)
        else:
            updated_cache = new_events
        
        # Save updated cache
        try:
            updated_cache.to_csv(cache_file, index=False)
            print(f"Cache updated with {len(new_events)} new events")
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    # Return the new events (without cache metadata)
    if not new_events.empty:
        return new_events.drop(['cache_timestamp', 'calendar_id'], axis=1)
    else:
        return new_events

def download_calendar_events(start_date: datetime.date, end_date: datetime.date, calendar_id: str = 'primary'):
    """
        Fetches events from a specified Google Calendar within a given date range.

        Args:
            start_date (datetime.date): The start date for fetching events (inclusive).
            end_date (datetime.date): The end date for fetching events (inclusive).
            calendar_id (str): The ID of the calendar to query. Use 'primary' for the user's default calendar.
                            You can find other calendar IDs in your Google Calendar settings.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(paths.token):
        creds = Credentials.from_authorized_user_file(paths.token, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                paths.client_secret, SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(paths.token, "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)

        # Convert date objects to RFC3339 format for the API
        # timeMin should be the beginning of the start_date
        time_min = datetime.datetime.combine(start_date, datetime.time.min).isoformat() + 'Z'
        # timeMax should be the end of the end_date
        time_max = datetime.datetime.combine(end_date, datetime.time.max).isoformat() + 'Z'

        events_result = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
                maxResults=2500, # Set max results to 2500
            )
            .execute()
        )
        events = events_result.get("items", [])

        if not events:
            print("No events found in this range.")
            return pd.DataFrame()  # Return empty DataFrame instead of None

        if len(events) >= 2499: # Check if we hit or are very close to the limit
            print("\n!!! ALERT: You retrieved 2499 or more events. There might be more events to fetch beyond this limit. Consider implementing pagination if you need all events. !!!\n")

        # Create a list to store event data
        event_data = []
        for event in events:
            # Get start and end times, defaulting to date if dateTime not available
            start = event["start"].get("dateTime", event["start"].get("date"))
            end = event["end"].get("dateTime", event["end"].get("date"))
            
            # Handle all-day events (date) vs timed events (dateTime)
            if 'T' not in start:  # All-day event
                start = datetime.datetime.strptime(start, '%Y-%m-%d')
                end = datetime.datetime.strptime(end, '%Y-%m-%d')
            else:  # Timed event
                # Remove the 'Z' if it exists and parse with timezone info
                start = start.rstrip('Z')
                end = end.rstrip('Z')
                start = datetime.datetime.fromisoformat(start)
                end = datetime.datetime.fromisoformat(end)
            
            # Get other fields, using empty string if not available
            # import streamlit as st
            # st.write(event)
            summary = event.get("summary", "")
            location = event.get("location", "")
            event_id = event.get("id", "")
            
            event_data.append({
                "start": start,
                "end": end, 
                "summary": summary,
                "location": location,
                "id": event_id
            })
        # Convert to DataFrame
        events_df = pd.DataFrame(event_data)
        
        # Convert timezone-aware datetimes to timezone-naive if they have timezone info
        if not events_df.empty:
            if hasattr(events_df['start'].iloc[0], 'tzinfo'):
                events_df['start'] = events_df['start'].apply(lambda x: x.replace(tzinfo=None))
            if hasattr(events_df['end'].iloc[0], 'tzinfo'):
                events_df['end'] = events_df['end'].apply(lambda x: x.replace(tzinfo=None))
                
        return events_df
    except HttpError as error:
        print(f"An error occurred: {error}")
        return pd.DataFrame()  # Return empty DataFrame on error

def get_all_calendar_names():
    """
    Authenticates with Google Calendar API and prints the names (summary)
    and IDs of all calendars in the authenticated user's account.
    """
    creds = None
    if os.path.exists(paths.token):
        creds = Credentials.from_authorized_user_file(paths.token, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                flow = InstalledAppFlow.from_client_secrets_file(
                    paths.client_secret, SCOPES
                )
                creds = flow.run_local_server(port=0)

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                paths.client_secret, SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(paths.token, "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)

        # Use the calendarList().list() method to get all calendars
        # The 'calendarList' service represents the user's list of calendars
        # https://developers.google.com/calendar/api/guides/calendar-list
        calendar_list_result = service.calendarList().list().execute()
        
        calendars = calendar_list_result.get("items", [])

        if not calendars:
            print("No calendars found in your account.")
            return {}

        calendars_dict = {calendar['summary']: calendar['id'] for calendar in calendars}
        return calendars_dict
        
    except HttpError as error:
        print(f"An error occurred: {error}")
        return {}
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {}

#%%
if __name__ == "__main__":
    # --- Example Usage ---
    # 1. 
    calendars = get_all_calendar_names()

    # 2. Get events for last week (from 7 days ago to yesterday)
    print("--- Getting events for Last Week ---")
    today = datetime.datetime.now().date()
    last_week_start = today - datetime.timedelta(days=7)
    last_week_end = today - datetime.timedelta(days=1)
    
    if calendars and "Datomotive" in calendars:
        events = get_calendar_events(last_week_start, last_week_end, calendar_id=calendars["Datomotive"])
        print(events)
    else:
        print("Calendar 'Datomotive' not found or no calendars available")
        # Try with primary calendar instead
        events = get_calendar_events(last_week_start, last_week_end, calendar_id='primary')
        print(events)

# %%
