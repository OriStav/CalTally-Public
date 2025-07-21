# CalTally - Quick Reference Guide

## Essential Functions

### 🗓️ Calendar Data

```python
# Get calendar events
from methods.g_cal import get_calendar_events
events = get_calendar_events(start_date, end_date, calendar_id='primary', refresh=False)

# Get all available calendars
from methods.g_cal import get_all_calendar_names
calendars = get_all_calendar_names()
```

### 📊 Data Processing

```python
# Process events with scoring
from methods.utils import events_maker
events_df, score_summary = events_maker(
    selected_calendars=['Work', 'Personal'], 
    selected_date=(start_date, end_date),
    refresh=False
)
```

### 📈 Visualizations

```python
# Interactive bar chart
from methods.utils import bar_grouped
bar_grouped(events_df, review_by='Score')  # 'Time', 'Score', 'Reward'

# Timeline chart
from methods.utils import line_grouped
line_grouped(events_df, by='score')  # 'duration_hours', 'score', 'monetized'

# Calendar heatmap
from methods.utils import heatmapper
heatmapper(events_df, selected_date)
```

### 🎨 UI Components

```python
# Theme toggle
from methods.utils import night_day
night_day(st.session_state)

# Text formatting
from methods.utils import titler
formatted_text = titler("duration_hours")  # Returns "Duration Hours"
```

## Configuration Constants

```python
from proj_consts.consts import SCORE_DCT, CALENDARS_DCT, UNITS_DCT, BY_DCT

# Calendar scoring weights
SCORE_DCT = {
    "Work": 2,
    "Personal": 1,
    "Break": -1
}

# Review mode mappings
BY_DCT = {
    "Time": "duration_hours",
    "Score": "score", 
    "Reward": "monetized"
}
```

## Data Schema

### Events DataFrame
| Column | Type | Description |
|--------|------|-------------|
| `start` | datetime | Event start time |
| `end` | datetime | Event end time |
| `summary` | str | Event title |
| `duration_hours` | float | Duration (max 24h) |
| `score` | float | Calculated score |
| `monetized` | float | Monetary value |

## Common Patterns

### Date Range Setup
```python
import datetime
today = datetime.date.today()
week_ago = today - datetime.timedelta(days=7)
date_range = (week_ago, today)
```

### Basic Analysis
```python
# Get and process events
events, _ = events_maker(['Work'], date_range)

# Calculate metrics
total_hours = events['duration_hours'].sum()
total_score = events['score'].sum()
productivity = total_score / total_hours if total_hours > 0 else 0
```

### Streamlit Integration
```python
import streamlit as st

# Sidebar controls
with st.sidebar:
    night_day(st.session_state)
    calendars = st.multiselect("Calendars", CALENDARS_DCT.keys())
    dates = st.date_input("Date Range", value=[start, end])

# Main content
if calendars and len(dates) == 2:
    events, _ = events_maker(calendars, dates)
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["Bar Chart", "Heatmap", "Timeline"])
    with tab1:
        bar_grouped(events, "Score")
    with tab2:
        heatmapper(events, dates)
    with tab3:
        line_grouped(events, "score")
```

## Error Handling

```python
try:
    events = get_calendar_events(start_date, end_date, calendar_id)
    if events.empty:
        st.warning("No events found in date range")
    else:
        # Process events
        pass
except Exception as e:
    st.error(f"Error loading calendar data: {e}")
    events = pd.DataFrame()  # Fallback to empty
```

## Performance Tips

- Use smaller date ranges for faster loading
- Enable caching with `refresh=False` (default)
- Limit calendar selection to relevant ones
- Clear cache with `refresh=True` when needed

## File Paths

```python
from proj_consts.paths import token, client_secret
# token = "files/token.json"
# client_secret = "files/client_secret.json"
```

## Dependencies

Key packages used:
- `streamlit` - Web framework
- `pandas` - Data manipulation  
- `plotly` - Interactive charts
- `google-api-python-client` - Calendar API
- `streamlit-echarts` - Calendar heatmaps

---

*For complete documentation, see [`API_DOCUMENTATION.md`](API_DOCUMENTATION.md)*