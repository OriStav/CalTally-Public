import pandas as pd
import datetime
import streamlit as st
import plotly.express as px
import os

from streamlit_echarts import st_echarts
from proj_consts.consts import COL_CONFIG
from proj_consts import paths
from proj_consts.consts import SCORE_DCT, CALENDARS_DCT, UNITS_DCT, BY_DCT, TICK_DICT

# from methods.g_cal import get_calendar_events
get_calendar_events = None # Placeholder for the actual import or function definition

def st_columns(df: pd.DataFrame, write: bool = True):
    """st_writes columns appropriately"""
    columns_as_string = '","'.join(df.columns.dropna())  # Joins with "," between
    if write:
        st.write(f'"{columns_as_string}"')
    return columns_as_string

def events_maker(selected_calendars, selected_date, refresh=False, DEMO=False):
    events = pd.DataFrame()
    if DEMO:
        if os.path.exists(paths.demo_cache_file):
            try:
                cached_events = pd.read_csv(paths.demo_cache_file)

                if not cached_events.empty:
                    # Convert date columns back to datetime
                    cached_events['start'] = pd.to_datetime(cached_events['start'],format="%Y-%m-%d %H:%M:%S", errors='coerce')
                    cached_events['end'] = pd.to_datetime(cached_events['end'],format="%Y-%m-%d %H:%M:%S", errors='coerce')

                    cached_events['cache_timestamp'] = pd.to_datetime(cached_events['cache_timestamp'])
                    cached_events["calendar"] = cached_events["calendar_id"]
                    events = cached_events.copy()
            except Exception as e:
                print(f"Error loading DEMO cache: {e}")
                events = pd.DataFrame()

    else:
        for calendar in selected_calendars:
            cal_events = get_calendar_events(selected_date[0], selected_date[1], CALENDARS_DCT[calendar], refresh)
            cal_events["calendar"] = calendar
            events = pd.concat([events, cal_events])
    # st.write(cached_events)

    events.set_index("id", inplace=True)
    events["duration"] = events["end"] - events["start"]
    events.sort_values(by="start", inplace=True)    
    events["hours"] = events["duration"].dt.total_seconds() / 3600
    events["hours"] = events["hours"].mask(events["hours"] >= 24, 1)
    events["score_per_hour"] = events["calendar"].map(SCORE_DCT)
    events["score"] = events["hours"] * events["score_per_hour"]
    events_score_dct = events.groupby(["summary","calendar"]).agg({"score_per_hour": "first"}).reset_index()
    return events, events_score_dct

def line_grouped(hourly, by = "hours", frq="D"):  
    """"
    Samples of selection:
    {"selection":{"points":[],"point_indices":[],"box":[],"lasso":[{"xref":"x","yref":"y","x":[0.9408602150537635,1,1.075268817204301],"y":[26.01169590643275,26.573099415204677,27.695906432748536]}]}}
    {"selection":{"points":[{"curve_number":0,"point_number":0,"point_index":0,"x":"South Korea","y":24,"label":"South Korea","value":24,"legendgroup":"gold"},{"curve_number":1,"point_number":0,"point_index":0,"x":"South Korea","y":37,"label":"South Korea","value":37,"legendgroup":"silver"}],"point_indices":[0],"box":[{"xref":"x","yref":"y","x":[0.6720430107526881,-0.010752688172043012],"y":[41.35672514619883,22.64327485380117]}],"lasso":[]}}
    """
    # grouped = hourly.groupby([pd.Grouper(key="start", freq="D"),"calendar"]
    #                         ).agg({by: "sum"}).reset_index()
    daily_events = hourly.groupby(pd.Grouper(key="start", freq=frq)).agg({by: "sum"}).reset_index()
    # Add day of week column
    # grouped_df['day_of_week'] = grouped_df['start'].dt.day_name()
    
    # Create a bar plot with plotly
    fig = px.line(
        daily_events, 
        markers=True,
        x="start", 
        y=by, 
        # color="calendar",
        title=f"{titler(by)} Timeline"
    )
    
    # Update layout for better readability
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title=titler(by),
        xaxis=dict(
            tickformat='%a - %d/%m',  # Format to show year-month-day and day of week
            tickmode='auto'
        ),
            yaxis=dict(
                tickmode='auto'
                # dtick=3  # Set y-axis tick interval to 1
            )
    )
    
    # Display the plot
    st.plotly_chart(fig, 
                    on_select='rerun',
                    key="line_grouped",
                    use_container_width=True)

def suggested_rewarder(monthly_budget, sel_events):
    monthly_events = sel_events.groupby([pd.Grouper(key="start", freq="MS")]
                            ).agg({"score": "sum"}).reset_index()
    up_rounded_max = round(1.1*monthly_events["score"].max(),0)
    sugg_reward = monthly_budget/up_rounded_max
    # st.sidebar.markdown(f"**Suggested Reward:** {monthly_budget/up_rounded_max:,.1f} {UNITS_DCT['Reward']}")
    return sugg_reward

@st.fragment
def bar_grouped(hourly, review_by = "Time", frq="D"):  
    """"
    Samples of selection:
    {"selection":{"points":[],"point_indices":[],"box":[],"lasso":[{"xref":"x","yref":"y","x":[0.9408602150537635,1,1.075268817204301],"y":[26.01169590643275,26.573099415204677,27.695906432748536]}]}}
    {"selection":{"points":[{"curve_number":0,"point_number":0,"point_index":0,"x":"South Korea","y":24,"label":"South Korea","value":24,"legendgroup":"gold"},{"curve_number":1,"point_number":0,"point_index":0,"x":"South Korea","y":37,"label":"South Korea","value":37,"legendgroup":"silver"}],"point_indices":[0],"box":[{"xref":"x","yref":"y","x":[0.6720430107526881,-0.010752688172043012],"y":[41.35672514619883,22.64327485380117]}],"lasso":[]}}
    """
    by = BY_DCT[review_by]
    grouped = hourly.groupby([pd.Grouper(key="start", freq=frq),"calendar"]
                            ).agg({by: "sum"}).reset_index()
    daily_events = hourly.groupby(pd.Grouper(key="start", freq=frq)).agg({by: "sum"}).reset_index()
    tick_format = TICK_DICT[frq]

    # Create a bar plot with plotly
    fig = px.bar(
        grouped, 
        x="start", 
        y=by, 
        color="calendar",
        title=f"{titler(by)} by Date and Calendar",
        opacity=0.5,  # Make bars more transparent
        pattern_shape="calendar",  # Add different patterns for each calendar
        pattern_shape_sequence=["", "/", "\\", "x", "+", "|", "-"]  # Pattern sequence for different shapes
    )
    
    # Add line with markers for daily events - make it more prominent
    fig.add_scatter(
        x=daily_events["start"],
        y=daily_events[by],
        mode="lines+markers",
        name="Total",
        line=dict(color="grey", width=3, dash="solid"),  # Thicker, solid line
        opacity=0.9,  # Higher opacity for the line
        marker=dict(size=12, symbol="diamond", color="white", line=dict(width=3, color="black")),  # Larger, more prominent markers
        showlegend=True
    )
    
    # Update layout for better readability
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title=titler(by),
        barmode='relative',  # Group bars by calendar
        # legend=dict(
        #     yanchor="top",
        #     y=1.15,
        #     xanchor="left",
        #     x=0.01,
        #     orientation="h",
        #     bgcolor="rgba(255, 255, 255, 0)",
        #     title=None
        # ),
        xaxis=dict(
            tickformat=tick_format,
            tickmode='auto'
        ),
        yaxis=dict(
            tickmode='auto'
        ),
        legend=dict(
        orientation="v",
        yanchor="top",
        y=1,
        xanchor="left",
        title=None,

        x=1.02  # Position legend just outside the plot area on the right
    )
        # plot_bgcolor='rgba(0,0,0,0)',  # Clean background
        # paper_bgcolor='rgba(0,0,0,0)'
    )
    fig.add_hline(y=0, line_width=3, line_color="black", line_dash="solid", opacity=0.5)

    # Display the plot
    st.plotly_chart(fig, 
                    on_select='rerun',
                    key="bar_grouped",
                    use_container_width=True)

    if st.session_state.bar_grouped.selection.points:
        day = st.session_state.bar_grouped.selection.points[0]["x"]
        day_datetime = pd.to_datetime(day,format="%Y-%m-%d")
        day_events = hourly[hourly["start"].dt.date == day_datetime.date()]
        st.dataframe(day_events,
                    column_order=COL_CONFIG.keys(),
                    column_config=COL_CONFIG,
                    hide_index=True)

    else:
        pass
        # st.warning(f"Select a day to see its {review_by.lower()}")

def heatmapper(events, selected_date):
    # Calendar heatmap visualization
    calendar_data = get_calendar_data(events)
    options = get_calendar_options(selected_date[0], selected_date[1], calendar_data)
    # st.subheader("Calendar Heatmap")
    st_echarts(options=options, height="400px")

def get_calendar_data(events_df):
    if events_df.empty:
        return []
    
    # Group events by date and count them
    daily_counts = events_df.groupby(events_df['end'].dt.date)['score'].sum().reset_index()
    
    # Convert to the format expected by ECharts
    data = [[date.strftime('%Y-%m-%d'), count] for date, count in zip(daily_counts["end"], daily_counts["score"])]
    
    return data

def get_calendar_options(start_date, end_date, calendar_data):
    date_range = (end_date - start_date).days
    
    # Determine the appropriate view based on the date range
    if date_range <= 7:  # Week view
        # For week view, use the month that contains most of the week
        range_str = start_date.strftime('%Y-%m')
        title_text = "Weekly Calendar Events Score"
        cell_size = [40, 40]  # Width, Height for vertical layout
        is_vertical = True
    elif date_range <= 31:  # Month view
        range_str = start_date.strftime('%Y-%m')  # Use month for month view
        title_text = "Monthly Calendar Events Score"
        cell_size = [40, 40]  # Square cells for month view
        is_vertical = True
    else:  # Year view
        range_str = str(start_date.year)  # Use year for year view
        title_text = "Yearly Calendar Events Score"
        cell_size = [20, 20]  # Horizontal layout for year view
        is_vertical = False
    
    # Calculate max value for color scale
    max_events = max([count for _, count in calendar_data]) if calendar_data else 10
    
    options = {
        "title": {
            "top": 30,
            "left": "center",
            "text": title_text
        },
        "tooltip": {
            "formatter": "{b} events on {c}"
        },
        "visualMap": {
            "min": 0,
            "max": max_events,
            "type": "continuous",
            "orient": "horizontal",
            "left": "center",
            "top": 65
        },
        "calendar": {
            "top": 120,
            "left": "center" if is_vertical else 60,
            "right": 30 if not is_vertical else None,
            "orient": "vertical" if is_vertical else "horizontal",
            "cellSize": cell_size,
            "range": range_str,
            "itemStyle": {
                "borderWidth": 0.5
            },
            "yearLabel": {"show": True},
            "dayLabel": {
                "firstDay": 0,  # 0= Start week on Sunday, 1= Start week on Monday
                "nameMap": ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
                "position": "top" if is_vertical else "left",
                "color": "#808080"
            },
            "monthLabel": {
                "show": True,
                "position": "left" if is_vertical else "top"
            }
        },
        "series": {
            "type": "heatmap",
            "coordinateSystem": "calendar",
            "data": calendar_data,
            # "label": {
            #     "show": date_range > 1,  # Show labels only in week view
            #     "formatter": "{c}"
            # }
        }
    }
    
    return options

def night_day(ms):
    """ Simplistic option which sometimes work...
    if st.toggle("Dark Mode", value=True) is False:
          st._config.set_option(f'theme.base', "light")
    else:
          st._config.set_option(f'theme.base', "dark")
    if st.button("Refresh"):
          st.rerun()
    """
    if "themes" not in ms: 
        ms.themes = {"current_theme": "light",
                        "refreshed": True,
                        
                        "light": {"theme.base": "dark",
                                #   "theme.backgroundColor": "black",
                                #   "theme.primaryColor": "#c98bdb",
                                #   "theme.secondaryBackgroundColor": "#5591f5",
                                #   "theme.textColor": "white",
                                #   "theme.textColor": "white",
                                "button_face": "🌜"},

                        "dark":  {"theme.base": "light",
                                #   "theme.backgroundColor": "white",
                                #   "theme.primaryColor": "#5591f5",
                                #   "theme.secondaryBackgroundColor": "#82E1D7",
                                #   "theme.textColor": "#0a1464",
                                "button_face": "🌞"},
                        }
    

    def ChangeTheme():
        previous_theme = ms.themes["current_theme"]
        tdict = ms.themes["light"] if ms.themes["current_theme"] == "light" else ms.themes["dark"]
        for vkey, vval in tdict.items(): 
            if vkey.startswith("theme"): st._config.set_option(vkey, vval)

        ms.themes["refreshed"] = False
        if previous_theme == "dark": ms.themes["current_theme"] = "light"
        elif previous_theme == "light": ms.themes["current_theme"] = "dark"


    btn_face = ms.themes["light"]["button_face"] if ms.themes["current_theme"] == "light" else ms.themes["dark"]["button_face"]
    st.button(btn_face, on_click=ChangeTheme)

    if ms.themes["refreshed"] == False:
        ms.themes["refreshed"] = True
        st.rerun()

def titler(series):
    if type(series) == str:
        ret = series.replace("_"," ").title()
    elif type(series) == list or type(series) == pd.Index:
        ret = [i.replace("_"," ").title() for i in series]
    return ret


def center_header(level=1, text="📚 ספרייה קהילתית 🌳"):
    st.markdown(f"<h{level} style='text-align: center;'>{text}</h{level}>", unsafe_allow_html=True)

def eq_tabs():
    """ Make the tab labels spread equally along the width"""

    st.markdown(
    """
    <style>
    /* Make the tab labels spread equally along the width */
    .stTabs [data-baseweb="tab-list"] {
        display: flex !important;
        justify-content: stretch !important;
        width: 100% !important;
        gap: 0 !important;
    }
    .stTabs [data-baseweb="tab"] {
        flex: 1 1 0 !important;
        text-align: center !important;
        padding-left: 2.5rem !important;
        padding-right: 2.5rem !important;
        min-width: 0 !important;
        font-size: 1.2rem !important;
        max-width: 100% !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def syntaxer(series):
    if type(series) == str:
        ret = series.replace(" ","_").lower()
    elif type(series) == list or type(series) == pd.Index:
        ret = [i.replace(" ","_").lower() for i in series]
    return ret