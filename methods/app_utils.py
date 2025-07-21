import streamlit as st
import pandas as pd
import numpy as np
import os
import time
import datetime

from proj_consts.consts import WISH_COL_CONFIG, AGG_DCT
from proj_consts.paths import wishlist_path


def rewinded_events_maker(selected_date, events, by, monthly_budget, cph):
    """ calculate the delta score of the events in the selected date range """
    # Move selected_date one period backwards
    date_range = (selected_date[1] - selected_date[0]).days
    rewinded_selected_date = (
        selected_date[0] - datetime.timedelta(days=date_range + 1),
        selected_date[1] - datetime.timedelta(days=date_range + 1)
    )
    rewinded_events = events.query("start >= @rewinded_selected_date[0] and start <= @rewinded_selected_date[1]")
    sel_events = events.query("start >= @selected_date[0] and start <= @selected_date[1]")
    delta_score = 0 if rewinded_events.empty else sel_events[by].sum() - rewinded_events[by].sum()
    periodical_budget = (monthly_budget * date_range) / 30  if by == "reward" else (monthly_budget* date_range) / (cph * 30) 
    return sel_events, delta_score, periodical_budget


def date_range_maker():
    TODAY = datetime.datetime(2025,7,12).date()
    last_week_start = TODAY - datetime.timedelta(days=7)
    last_month_start = TODAY - datetime.timedelta(days=30)
    yearly_start = TODAY.replace(day=1, month=TODAY.month) - datetime.timedelta(days=180)#365)
    
    date_range = st.segmented_control("Select date",
                            options= list(AGG_DCT.keys()) + ["Custom"],
                            default="Week")
    if date_range == "Week":
        selected_date = [last_week_start, TODAY]
    elif date_range == "Month":
        selected_date = [last_month_start, TODAY]
    elif date_range == "6 Months":
        selected_date =  [yearly_start, TODAY]
    elif date_range == "Custom":
        selected_date = st.date_input("Select date",
                                    value=[last_week_start, TODAY], min_value=None, max_value=None,
                                    format="DD/MM/YYYY")
        # Handle the case where selected_date might be a single date or tuple
        if isinstance(selected_date, tuple) and len(selected_date) == 2:
            custom_duration = (selected_date[1] - selected_date[0]).days
        else:
            # If it's a single date, use it as both start and end
            selected_date = [selected_date, selected_date]
            custom_duration = 0
        date_range = "Week" if custom_duration <= 7 else "Month" if custom_duration <= 30 else "6 Months"
    else:
        date_range = "Week"
        selected_date = [last_week_start, TODAY]
        
    agg_frq = AGG_DCT[date_range]
    return selected_date, [yearly_start, TODAY], agg_frq

def progress_maker(sel_events, wishlist,rolling=False):
    if rolling:
        wishlist = wishlist.sort_values(by="priority")
        expanding_sum = sel_events["reward"].sum() - wishlist["price"].cumsum().shift(1)
        expanding_sum = expanding_sum.where(expanding_sum > 0, expanding_sum.iloc[-1])
        expanding_sum.iloc[0] = sel_events["reward"].sum()
        # st.metric("Left/Missing to spend",expanding_sum.iloc[-1])
        # st.write(expanding_sum)
        time.sleep(1)
        return np.minimum(100, np.maximum(0,100*expanding_sum/wishlist["price"])).astype(int)
    else:
        return np.minimum(100, np.maximum(0 ,100*sel_events["reward"].sum()/wishlist["price"])).astype(int)

@st.fragment()
def wishlist_maker(sel_events):
    rolling = st.toggle("Rolling", value=True)

    if not os.path.exists(wishlist_path):
        wishlist = pd.DataFrame({
            "purchased": [False],
            "priority": [1],
            "name": ["Ledger Nano X™"], 
            "price": [511],
            "progress": [None],
            "link": ["https://www.ledger.com/products/ledger-nano-x"]
        })
        wishlist["progress"] = progress_maker(sel_events, wishlist,rolling=rolling)
        wishlist["purchase_date"] = np.nan#datetime.date(2030,1,1)
        wishlist.to_csv(wishlist_path, index=False)
    
    wishlist = pd.read_csv(wishlist_path)
    wishlist["purchase_date"] = pd.to_datetime(wishlist["purchase_date"],format="%Y-%m-%d")
    wishlist.sort_values(by="priority",inplace=True)
    edited_wishlist = st.data_editor(wishlist, 
    column_config=WISH_COL_CONFIG,
    column_order=list(WISH_COL_CONFIG.keys()),
    disabled=("Progress"),
    num_rows="dynamic", 
    hide_index=True, 
    )
    if st.button("💾 Save and Refresh 🔁",type="primary"):
        # edited_wishlist.columns = syntaxer(edited_wishlist.columns)
        edited_wishlist["progress"] = progress_maker(sel_events, edited_wishlist ,rolling=rolling)
        edited_wishlist.loc[~edited_wishlist["purchased"]& wishlist["purchased"]& edited_wishlist["purchase_date"].notna(), "purchase_date"] = np.nan
        edited_wishlist["purchased"] = edited_wishlist["purchased"] | edited_wishlist["purchase_date"].notna()
        edited_wishlist.loc[edited_wishlist["purchased"] & edited_wishlist["purchase_date"].isna(), "purchase_date"] = pd.Timestamp.now().date().strftime("%Y-%m-%d")
        edited_wishlist.to_csv(wishlist_path, index=False)
        st.rerun()
