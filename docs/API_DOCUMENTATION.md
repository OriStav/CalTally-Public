# CalTally - API Documentation

## Overview

CalTally is a Streamlit web application designed to track, analyze, and visualize Google Calendar events with customizable scoring systems. It provides interactive charts, heatmaps, and metrics to help users understand their calendar activity patterns and productivity.

## Features

- 📅 Google Calendar integration with multi-calendar support
- 📊 Interactive bar charts, line charts, and calendar heatmaps
- 🏆 Customizable scoring system for different calendar types
- 💰 Reward/monetization tracking
- 🌙 Dark/light theme toggle
- 📝 Event caching for improved performance
- 🔄 Real-time data refresh capabilities

## Installation

### Prerequisites

- Python 3.8+
- Google Cloud Console project with Calendar API enabled
- OAuth 2.0 credentials (`client_secret.json`)

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up Google Calendar API:
   - Create a project in Google Cloud Console
   - Enable the Calendar API
   - Create OAuth 2.0 credentials
   - Download `client_secret.json` and place in `files/` directory

3. Run the application:
```bash
streamlit run app.py
```

## Project Structure

```
CalTally/
├── app.py                 # Main Streamlit application
├── methods/
│   ├── utils.py          # Utility functions for data processing and visualization
│   └── g_cal.py          # Google Calendar API integration
├── proj_consts/
│   ├── consts.py         # Project constants and configurations
│   └── paths.py          # File path configurations
├── files/
│   ├── cache.csv         # Event cache storage
│   ├── token.json        # OAuth tokens (auto-generated)
│   └── client_secret.json # Google API credentials
└── requirements.txt       # Python dependencies
```

## Core API Reference

### Main Application (`app.py`)

The main Streamlit application that orchestrates the UI and data flow.

**Key Features:**
- Multi-calendar selection
- Date range picker
- Review mode selection (Time/Score/Reward)
- Interactive visualizations
- Metrics display

**Configuration Constants:**
- `SCORE_DCT`: Calendar scoring weights
- `CALENDARS_DCT`: Available calendars mapping
- `UNITS_DCT`: Display units for different modes
- `BY_DCT`: Data aggregation field mapping

---

### Calendar Integration (`methods/g_cal.py`)

#### `get_calendar_events(start_date, end_date, calendar_id='primary', refresh=False)`

Fetches calendar events with intelligent caching support.

**Parameters:**
- `start_date` (datetime.date): Start date for event retrieval (inclusive)
- `end_date` (datetime.date): End date for event retrieval (inclusive)
- `calendar_id` (str): Google Calendar ID ('primary' for default calendar)
- `refresh` (bool): Force refresh cache if True

**Returns:**
- `pd.DataFrame`: DataFrame with columns: `['id', 'start', 'end', 'summary', 'location']`

**Example:**
```python
from methods.g_cal import get_calendar_events
import datetime

# Get events for the last week
today = datetime.date.today()
start_date = today - datetime.timedelta(days=7)
end_date = today

events = get_calendar_events(start_date, end_date, 'primary')
print(f"Found {len(events)} events")
```

**Caching Behavior:**
- Cache duration: 24 hours
- Cache file: `files/cache.csv`
- Automatic cache invalidation for overlapping date ranges
- Per-calendar caching support

#### `download_calendar_events(start_date, end_date, calendar_id='primary')`

Direct calendar data download without caching (used internally).

**Parameters:**
- Same as `get_calendar_events` (minus refresh parameter)

**Returns:**
- `pd.DataFrame`: Fresh calendar data

**Rate Limiting:**
- Maximum 2500 events per request
- Automatic pagination warning

#### `get_all_calendar_names()`

Retrieves all available calendars for the authenticated user.

**Returns:**
- `dict`: Mapping of calendar names to calendar IDs

**Example:**
```python
calendars = get_all_calendar_names()
print("Available calendars:")
for name, cal_id in calendars.items():
    print(f"  {name}: {cal_id}")
```

---

### Data Processing & Visualization (`methods/utils.py`)

#### `events_maker(selected_calendars, selected_date, refresh=False)`

Processes calendar events and calculates scores for multiple calendars.

**Parameters:**
- `selected_calendars` (list): List of calendar names to include
- `selected_date` (tuple): (start_date, end_date) tuple
- `refresh` (bool): Force cache refresh

**Returns:**
- `tuple`: (processed_events_df, events_score_summary_df)

**Processing Steps:**
1. Fetches events from selected calendars
2. Calculates event duration in hours (capped at 24h for all-day events)
3. Applies scoring based on calendar type
4. Adds monetization column

**Example:**
```python
from methods.utils import events_maker
import datetime

calendars = ["Work", "Personal"]
date_range = (
    datetime.date(2024, 1, 1),
    datetime.date(2024, 1, 7)
)

events, score_summary = events_maker(calendars, date_range)
print(f"Total score: {events['score'].sum()}")
```

#### `bar_grouped(events_df, review_by='Time')`

Creates interactive grouped bar chart visualization.

**Parameters:**
- `events_df` (pd.DataFrame): Processed events data
- `review_by` (str): Aggregation mode ('Time', 'Score', 'Reward')

**Features:**
- Daily aggregation by calendar
- Interactive selection with metrics
- Combined bar and line chart
- Streamlit session state integration

**Streamlit Component:**
```python
# Used within Streamlit app
bar_grouped(events, "Score")
```

#### `line_grouped(events_df, by='duration_hours')`

Generates timeline visualization with daily aggregation.

**Parameters:**
- `events_df` (pd.DataFrame): Events data
- `by` (str): Column to aggregate ('duration_hours', 'score', 'monetized')

**Features:**
- Daily trend analysis
- Marker-based line chart
- Interactive plotting with Plotly

#### `heatmapper(events_df, selected_date)`

Creates calendar heatmap visualization using ECharts.

**Parameters:**
- `events_df` (pd.DataFrame): Events data
- `selected_date` (tuple): Date range for display optimization

**Features:**
- Adaptive view (week/month/year)
- Score-based color mapping
- Interactive calendar grid

**View Logic:**
- ≤7 days: Week view with vertical layout
- ≤31 days: Month view with square cells
- >31 days: Year view with horizontal layout

#### `night_day(session_state)`

Implements theme switching functionality.

**Parameters:**
- `session_state`: Streamlit session state object

**Features:**
- Light/dark theme toggle
- Persistent theme state
- Dynamic UI refresh

**Usage:**
```python
# In Streamlit sidebar
with st.sidebar:
    night_day(st.session_state)
```

#### `titler(text)`

Utility function for text formatting.

**Parameters:**
- `text` (str/list/pd.Index): Text to format

**Returns:**
- Formatted text with title case and underscore replacement

---

### Configuration (`proj_consts/`)

#### Constants (`proj_consts/consts.py`)

**`SCORE_DCT`**: Calendar scoring weights
```python
SCORE_DCT = {
    "Datomotive": 2,
    "Finance": 2,
    "Neutral": 0,
    "+ Raise": 2,
    "- Spend": -3,
}
```

**`CALENDARS_DCT`**: Dynamic calendar mapping (populated from Google Calendar)

**`UNITS_DCT`**: Display units for different review modes
```python
UNITS_DCT = {
    "Reward": "₪",
    "Score": "points", 
    "Time": "hours",
}
```

**`BY_DCT`**: Data aggregation field mapping
```python
BY_DCT = {
    "Time": "duration_hours",
    "Score": "score", 
    "Reward": "monetized"
}
```

#### Paths (`proj_consts/paths.py`)

**File path constants:**
- `token`: OAuth token storage path
- `client_secret`: Google API credentials path

---

## Data Models

### Event DataFrame Schema

| Column | Type | Description |
|--------|------|-------------|
| `id` | str | Unique event identifier (index) |
| `start` | datetime | Event start time |
| `end` | datetime | Event end time |
| `summary` | str | Event title/summary |
| `location` | str | Event location |
| `calendar` | str | Source calendar name |
| `duration` | timedelta | Event duration |
| `duration_hours` | float | Duration in hours (capped at 24) |
| `score_per_hour` | float | Scoring rate from calendar mapping |
| `score` | float | Total event score |
| `monetized` | float | Monetary value (score × reward rate) |

### Cache DataFrame Schema

Additional columns for caching:
- `cache_timestamp`: When data was cached
- `calendar_id`: Google Calendar ID

---

## Usage Examples

### Basic Calendar Analysis

```python
import datetime
from methods.g_cal import get_calendar_events
from methods.utils import events_maker

# Set date range
today = datetime.date.today()
week_start = today - datetime.timedelta(days=7)

# Get events and analyze
events, summary = events_maker(["Work", "Personal"], (week_start, today))

# Calculate productivity metrics
total_hours = events['duration_hours'].sum()
total_score = events['score'].sum()
avg_score_per_hour = total_score / total_hours if total_hours > 0 else 0

print(f"Week Summary:")
print(f"  Total Hours: {total_hours:.1f}")
print(f"  Total Score: {total_score:.1f}")
print(f"  Productivity: {avg_score_per_hour:.2f} points/hour")
```

### Custom Scoring System

```python
# Modify scoring in proj_consts/consts.py
CUSTOM_SCORES = {
    "Deep Work": 5.0,
    "Meetings": 1.0,
    "Admin": 0.5,
    "Breaks": -0.5
}

# Apply to your calendar mapping
# This would require updating SCORE_DCT in consts.py
```

### Data Export

```python
# Export processed events
events, _ = events_maker(selected_calendars, date_range)
events.to_csv('calendar_analysis.csv', index=True)

# Export daily summaries
daily_summary = events.groupby(events['start'].dt.date).agg({
    'duration_hours': 'sum',
    'score': 'sum',
    'monetized': 'sum'
}).round(2)
daily_summary.to_csv('daily_summary.csv')
```

## Authentication & Security

### Google OAuth Setup
methods/g_cal.py
1. **Google Cloud Console Configuration:**
   - Enable Calendar API
   - Create OAuth 2.0 Client ID
   - Add authorized redirect URIs for local development

2. **Credentials File (`client_secret.json`):**
```json
{
  "installed": {
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    ...
  }
}
```

3. **Scopes:**
   - `https://www.googleapis.com/auth/calendar.readonly`

### Token Management

- Tokens auto-refresh when expired
- Stored in `files/token.json`
- First-time authentication opens browser for consent

## Performance Optimization

### Caching Strategy

- **Cache Duration:** 24 hours per calendar
- **Cache Invalidation:** Automatic for overlapping date ranges
- **Cache File:** `files/cache.csv`
- **Benefits:** Reduces API calls, improves load times

### Best Practices

1. **Date Range Selection:**
   - Smaller ranges load faster
   - Use refresh sparingly for recent data

2. **Calendar Selection:**
   - Limit to relevant calendars
   - High-volume calendars may slow performance

3. **Data Processing:**
   - Events are processed client-side
   - Large datasets may impact browser performance

## Error Handling

### Common Issues

1. **Authentication Errors:**
   - Check `client_secret.json` file presence
   - Verify Google Cloud Console configuration
   - Clear `token.json` and re-authenticate

2. **API Rate Limits:**
   - Automatic retry with exponential backoff
   - 2500 events per request limit

3. **Cache Issues:**
   - Use refresh button to force cache update
   - Delete `files/cache.csv` to reset cache

### Error Recovery

```python
try:
    events = get_calendar_events(start_date, end_date, calendar_id)
except Exception as e:
    print(f"Error fetching events: {e}")
    # Fallback to cached data or empty DataFrame
    events = pd.DataFrame()
```

## Future Enhancements

Based on `TODO` file:

- [ ] **Reward Suggestions:** Monthly reward target recommendations
- [ ] **Time-frame Aggregations:** Weekly, monthly, quarterly views
- [ ] **Points Integration:** `points.csv` integration for custom scoring
- [ ] **Code-words:** Pattern-based calendar reading
- [ ] **Category Settings:** Enhanced event categorization
- [x] **Refresh Button:** Manual cache refresh (implemented)

## Contributing

### Development Setup

1. Clone repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up Google Calendar API credentials
4. Run: `streamlit run app.py`

### Code Style

- Follow PEP 8 conventions
- Add docstrings for public functions
- Include type hints where applicable
- Write descriptive commit messages

## License

[Add license information here]

## Support

For issues and questions:
1. Check error logs in Streamlit interface
2. Verify Google Calendar API setup
3. Review authentication configuration
4. Check cache file permissions

---

*This documentation covers CalTally v1.0 - Last updated: 2024*