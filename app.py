"""
streamlit run app.py
💰🎁🍯⏱️🧮⚖️⏳🏆🏅
"""
import streamlit as st
from methods.app_utils import wishlist_maker, date_range_maker, rewinded_events_maker
from methods.utils import night_day, heatmapper, bar_grouped, events_maker, eq_tabs, center_header, suggested_rewarder
from proj_consts.consts import SCORE_DCT, CALENDARS_DCT, UNITS_DCT, BY_DCT, AGG_DCT, DEMO

center_header(1, "🗓️ CalTally")
center_header(7,"💲 Monetize your time  ⏳ Stay accountable 📈 Track Performance")
center_header(7,"")
with st.sidebar:
    night_day(st.session_state)
    selected_calendars = st.multiselect("Select calendars", CALENDARS_DCT.keys(), default=SCORE_DCT.keys())
    refresh = st.button("Refresh")
    # rolling = st.radio("***Period calculation", ["🛞 Rolling", "🗓️ Calendar"], horizontal=True)#TODO: add functionality

    selected_date, download_dates, agg_frq = date_range_maker()
    review_by = st.radio("Review by", UNITS_DCT.keys(),horizontal=True)
    monthly_budget = st.number_input(label=f"Monthly Reward Budget ({UNITS_DCT['Reward']})", min_value=0, max_value=None, value=1000, step=100, help="Maximum reward to possibly achieve")

if selected_calendars:
    events, events_score_dct = events_maker(selected_calendars, download_dates, refresh, DEMO)
    sugg_reward = suggested_rewarder(monthly_budget, events)
    cph = st.sidebar.number_input(f"Reward per point ({UNITS_DCT['Reward']})", value=sugg_reward, min_value=0.0, max_value=None, step=0.1,help=f"**Suggested Reward:** {sugg_reward:,.1f} {UNITS_DCT['Reward']}")
    events["reward"] = events["score"] * cph
    by = BY_DCT[review_by]
    sel_events, delta_score, periodical_budget = rewinded_events_maker(selected_date, events,
                                                                        by, monthly_budget, cph)
else:
    st.error("Please select at least one calendar")


metrics_cols = st.columns([1,3])
metrics_cols[0].metric(f"Periodical {review_by}" ,
         f'{sel_events[by].sum():,.0f} {UNITS_DCT[review_by]}' ,
         delta = f'{delta_score:,.0f} {UNITS_DCT[review_by]}')
if by != "hours":
    metrics_cols[1].progress(value=min(sel_events[by].sum()/periodical_budget,1.0), text=f'{sel_events[by].sum():,.0f} of {periodical_budget:,.0f} {UNITS_DCT[review_by]}')
eq_tabs()
tabs = st.tabs(["📊 Bar Chart", "🗓️ Heatmap", "🎁 Wishlist"])

with tabs[0]:
    bar_grouped(sel_events, review_by, frq=agg_frq)
    with st.expander("Events Score Dictionary"):
        st.dataframe(events_score_dct, hide_index=True)
    with st.expander("Events"):
        st.dataframe(sel_events, hide_index=True)
with tabs[1]: 
    heatmapper(sel_events, selected_date)
with tabs[2]:
    wishlist_maker(sel_events)


# center_header(7,"This is a demo version of CalTally. Some features are not available in this version.")
# center_header(7,"For google calendar integration review the docs in the repo.")
st.markdown("**:material/reviews:** This is a Demo version of CalTally, Some features are not available in this version.")
st.markdown("**:material/calendar_month:** For **Google Calendar** integration review the docs in the repo.")
cols = st.columns(3)
cols[1].markdown("###### :material/raven: [𝕏 (twitter)](https://x.com/CalTallyApp)")
